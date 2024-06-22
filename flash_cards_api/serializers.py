from time import sleep

from selenium.webdriver.common.by import By

from flash_cards_api import models
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
        for field_value in fields:
            field = field_value.pop('field')
            if field.xpath:
                options = Options()
                options.add_argument('--headless')
                driver = webdriver.Firefox(options=options)
                driver.get(field.data_format.url.format(**field_dict))
                sleep(3)
                value = driver.find_element(By.XPATH, field.xpath).get_attribute('outerHTML')
                css = '\n'.join([tag.get_attribute('outerHTML') for tag in driver.find_elements(By.XPATH, '//style')] +
                                [tag.get_attribute('outerHTML') for tag in driver.find_elements(By.XPATH, '//link[@rel="stylesheet"]')])
                field_value['value'] = f'{css}\n{value}'
                driver.close()
            serializer = FieldValueSerializer(
                data={
                    'parent': instance.id,
                    'field': field.id,
                    **field_value
                },
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
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
                    field_obj = models.Field.objects.get(parent=instance, field=field['field'])
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


class CardFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CardFormat
        fields = '__all__'


class DataFormatSerializer(serializers.ModelSerializer):
    field_set = FieldSerializer(many=True, partial=True)

    class Meta:
        model = models.DataFormat
        fields = '__all__'

    def validate(self, data):
        order_nums = [field['order'] for field in data.get('field_set', [])]
        if self.instance:
            order_nums.extend(field.order for field in
                              models.Field.objects.filter(data_format=self.instance)
                              .exclude(id__in=[field.get('id') for field in data['field_set']]))
        if len(order_nums) != len(set(order_nums)):
            raise serializers.ValidationError('Duplicate field orders found')
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
    class Meta:
        model = models.Deck
        fields = '__all__'


class DeckDetailSerializer(serializers.ModelSerializer):
    card_set = CardSerializer(many=True)

    class Meta:
        model = models.Deck
        fields = '__all__'
