from datetime import datetime

from django.db.models import Prefetch, Count, Q
from rest_framework.decorators import action
from rest_framework.response import Response

from flash_cards_api import models, serializers
from rest_framework import viewsets

from flash_cards_api.helpers.submit import submit


minimum_accuracy = 0.1


class UserCreateViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)


class DeckViewSet(UserCreateViewSet):
    serializer_class = serializers.DeckSerializer

    def get_queryset(self):
        return models.Deck.objects.filter(user=self.request.user).annotate(num_due=Count('card', filter=(Q(card__last_correct__lt=datetime.now()) | Q(card__last_correct__isnull=True))))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.DeckDetailSerializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def quiz(self, request, *args, **kwargs):
        instance = self.get_object()
        cards = instance.due_cards
        if cards.count() > 0:
            serializer = serializers.CardQuizSerializer(cards.first())
            return Response(serializer.data)
        else:
            return Response('', status=204)

    @action(detail=True, methods=['get'])
    def study(self, request, *args, **kwargs):
        instance = self.get_object()
        card = instance.card_set.order_by('last_correct').first()
        serializer = serializers.CardQuizSerializer(card)
        return Response(serializer.data)


class DataFormatViewSet(UserCreateViewSet):
    serializer_class = serializers.DataFormatSerializer

    def get_queryset(self):
        return models.DataFormat.objects.filter(user=self.request.user).prefetch_related(
            Prefetch('field_set', queryset=models.Field.objects.all())
        )


class CardFormatViewSet(UserCreateViewSet):
    serializer_class = serializers.CardFormatSerializer

    def get_queryset(self):
        return models.CardFormat.objects.filter(user=self.request.user)


class DataViewSet(UserCreateViewSet):
    serializer_class = serializers.DataSerializer

    def get_queryset(self):
        return models.Data.objects.filter(user=self.request.user).prefetch_related(
            Prefetch('field_value_set',
                     queryset=models.FieldValue.objects.select_related('field'))
        )


class CardViewSet(UserCreateViewSet):
    serializer_class = serializers.CardSerializer

    def get_queryset(self):
        return models.Card.objects.filter(user=self.request.user) \
            .select_related('data').select_related('format') \
            .prefetch_related(Prefetch('data__field_value_set',
                                       queryset=models.FieldValue.objects.select_related('field')))

    @action(detail=True, methods=['post'])
    def correct(self, request, *args, **kwargs):
        instance = self.get_object()
        now = datetime.now()
        instance.last_seen = now
        instance.last_correct = now
        if request.data.get('study'):
            instance.total_correct += 1
            instance.current_streak += 1
            instance.calculate_next_due()
        instance.save()
        return Response(self.serializer_class(instance).data)

    @action(detail=True, methods=['post'])
    def incorrect(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.last_seen = datetime.now()
        if request.data.get('study'):
            instance.total_wrong += 1
            instance.current_streak = 0
            instance.calculate_next_due()
        instance.save()
        return Response(self.serializer_class(instance).data)

    @action(detail=True, methods=['post'])
    def check_written(self, request, *args, **kwargs):
        instance = self.get_object()
        image = request.data.get('image')
        data = submit(image)
        response = {
            'data': data,
            'correct': True
        }
        if len(data) != len(instance.answer_text):
            response['correct'] = False
        else:
            for i, char in enumerate(instance.answer_text):
                if char not in data[i]['labels']:
                    response['correct'] = False
                else:
                    index = data[i]['labels'].index(char)
                    if data[i]['accuracy'][index] < minimum_accuracy:
                        response['correct'] = False
        return Response(response)

    @action(detail=True, methods=['post'])
    def check_typed(self, request, *args, **kwargs):
        instance = self.get_object()
        answer = request.data.get('answer')
        data = {
            'correct': answer == instance.answer_text,
            'answer': answer
        }
        return Response(data)
