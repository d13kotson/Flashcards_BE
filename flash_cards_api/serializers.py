from flash_cards_api import models
from flash_cards_api.helpers.selenium import get_value
from rest_framework import serializers

from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class FieldSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    data_format = serializers.PrimaryKeyRelatedField(queryset=models.DataFormat.objects.all(), required=False)

    class Meta:
        model = models.Field
        fields = '__all__'
        validators = []


class FieldValueSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    parent = serializers.PrimaryKeyRelatedField(queryset=models.Data.objects.all(), required=False)

    class Meta:
        model = models.FieldValue
        fields = '__all__'
        validators = []


class CardSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    question = serializers.CharField()
    answer = serializers.CharField()

    def get_name(self, instance):
        return str(instance)

    class Meta:
        model = models.Card
        fields = '__all__'

    def validate(self, data):
        data = super().validate(data)
        if data.get('format') and data['format'].data_format_id != data['data'].format_id:
            raise serializers.ValidationError('Card Format and Data Format do not match.')
        return data


class CardFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CardFormat
        fields = '__all__'


class CardQuizSerializer(CardSerializer):
    format = CardFormatSerializer()


class DataSerializer(serializers.ModelSerializer):
    field_value_set = FieldValueSerializer(many=True, partial=True)

    class Meta:
        model = models.Data
        fields = '__all__'

    def validate(self, data):
        field_ids = [field_value['field'] for field_value in data.get('field_value_set', [])]
        if self.instance:
            field_ids.extend(field_value.field_id for field_value in
                             models.FieldValue.objects.filter(parent=self.instance)
                             .exclude(id__in=[field_value.get('id') for field_value in data['field_value_set']]))
        if len(field_ids) != len(set(field_ids)):
            raise serializers.ValidationError('Duplicate field ids found')
        return super().validate(data)

    def create(self, validated_data):
        fields = validated_data.pop('field_value_set', [])
        field_dict = {
            field['field'].name: field['value']
            for field in fields
        }
        instance = super().create(validated_data)
        for field in instance.format.field_set.filter(xpath=''):
            value = field_dict.get(field.name)
            serializer = FieldValueSerializer(
                data={
                    'parent': instance.id,
                    'field': field.id,
                    'value': value
                },
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        if instance.format.url:
            options = Options()
            options.add_argument('--headless')
            driver = webdriver.Firefox(options=options)
            driver.get(instance.format.url.format(**field_dict))
            for field in instance.format.field_set.filter(xpath__isnull=False).exclude(xpath=''):
                value = get_value(driver, field.xpath)
                serializer = FieldValueSerializer(
                    data={
                        'parent': instance.id,
                        'field': field.id,
                        'value': value
                    },
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            driver.close()
        return instance

    def update(self, instance, validated_data):
        fields = validated_data.pop('field_value_set', [])
        for field in fields:
            if 'id' in field:
                field_obj = models.Field.objects.get(id=field['id'])
                serializer = FieldSerializer(
                    field_obj,
                    data={
                        'parent': instance.id,
                        **field
                    },
                    partial=True
                )
            else:
                try:
                    field_obj = field['field']
                    serializer = FieldSerializer(
                        field_obj,
                        data={
                            'parent': instance.id,
                            **field
                        },
                        partial=True
                    )
                except models.Field.DoesNotExist:
                    serializer = FieldSerializer(
                        data={
                            'parent': instance.id,
                            **field
                        },
                        partial=True
                    )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return super().update(instance, validated_data)


class DataFormatSerializer(serializers.ModelSerializer):
    field_set = FieldSerializer(many=True, partial=True)

    class Meta:
        model = models.DataFormat
        fields = '__all__'

    def validate(self, data):
        return super().validate(data)

    def create(self, validated_data):
        fields = validated_data.pop('field_set', [])
        instance = super().create(validated_data)
        for field in fields:
            serializer = FieldSerializer(
                data={
                    'data_format': instance.id,
                    **field
                },
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return instance

    def update(self, instance, validated_data):
        fields = validated_data.pop('field_set', [])
        for field in fields:
            if 'id' in field:
                field_obj = models.Field.objects.get(id=field['id'])
                serializer = FieldSerializer(
                    field_obj,
                    data={
                        'data_format': instance.id,
                        **field
                    },
                    partial=True
                )
            else:
                serializer = FieldSerializer(
                    data={
                        'data_format': instance.id,
                        **field
                    },
                    partial=True
                )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return super().update(instance, validated_data)


class DeckSerializer(serializers.ModelSerializer):
    num_due = serializers.SerializerMethodField(required=False)

    def get_num_due(self, instance):
        return instance.due_cards.count()

    class Meta:
        model = models.Deck
        fields = '__all__'


class DeckDetailSerializer(serializers.ModelSerializer):
    card_set = CardSerializer(many=True)

    class Meta:
        model = models.Deck
        fields = '__all__'
