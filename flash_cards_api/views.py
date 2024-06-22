import base64
import json
from datetime import datetime

from django.db.models import Prefetch
from django.http import HttpResponse
from django.views.generic import View
from rest_framework.decorators import action
from rest_framework.response import Response

from flash_cards_api import models, serializers
from rest_framework import viewsets

import cv2
import numpy as np

from flash_cards_api.helpers.labels import get_label_encoder
from flash_cards_api.helpers.model import load_model

default_num_results = 20


class UserCreateViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)


class DeckViewSet(UserCreateViewSet):
    serializer_class = serializers.DeckSerializer

    def get_queryset(self):
        return models.Deck.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.DeckDetailSerializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def study(self, request, *args, **kwargs):
        instance = self.get_object()
        cards = instance.card_set.order_by('last_correct').all()[:10]
        serializer = serializers.CardSerializer(cards, many=True)
        return Response(serializer.data)


class DataFormatViewSet(UserCreateViewSet):
    serializer_class = serializers.DataFormatSerializer

    def get_queryset(self):
        return models.DataFormat.objects.filter(user=self.request.user).prefetch_related(
            Prefetch('field_set', queryset=models.Field.objects.order_by('order'))
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
                     queryset=models.FieldValue.objects.select_related('field').order_by('field__order'))
        )


class CardViewSet(UserCreateViewSet):
    serializer_class = serializers.CardSerializer

    def get_queryset(self):
        return models.Card.objects.filter(user=self.request.user) \
            .select_related('data').select_related('format') \
            .prefetch_related(Prefetch('data__field_value_set',
                                       queryset=models.FieldValue.objects.select_related('field').order_by(
                                           'field__order')))

    @action(detail=True, methods=['get'])
    def question(self, request, *args, **kwargs):
        instance = self.get_object()
        return HttpResponse(instance.question)

    @action(detail=True, methods=['get'])
    def answer(self, request, *args, **kwargs):
        instance = self.get_object()
        return HttpResponse(instance.answer)

    @action(detail=True, methods=['post'])
    def correct(self, request, *args, **kwargs):
        instance = self.get_object()
        now = datetime.now()
        instance.last_seen = now
        instance.last_correct = now
        instance.total_correct += 1
        instance.save()
        return Response(self.serializer_class(instance).data)

    @action(detail=True, methods=['post'])
    def incorrect(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.last_seen = datetime.now()
        instance.total_wrong += 1
        instance.save()
        return Response(self.serializer_class(instance).data)


class SubmitView(View):
    def post(self, request, *args, **kwargs):
        data = request.POST['file']
        image = cv2.imdecode(np.asarray(bytearray(base64.b64decode(bytes(data[22:], 'utf-8'))), dtype=np.uint8),
                             cv2.IMREAD_UNCHANGED)

        edged = cv2.Canny(image, 30, 150)
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bounding_boxes = [cv2.boundingRect(c) for c in cnts[0]]
        reduce = True
        while reduce:
            reduce = False
            for box in bounding_boxes:
                for sub in bounding_boxes:
                    if box != sub:
                        if box[0] <= sub[0]:
                            left = box
                            right = sub
                        else:
                            left = sub
                            right = box
                        if box[1] <= sub[1]:
                            top = box
                            bottom = sub
                        else:
                            top = sub
                            bottom = box
                        if (left[0] <= right[0] <= left[0] + max(left[2], left[3])) and (
                                top[1] <= bottom[1] <= top[1] + max(top[2], top[3])):
                            reduce = True
                            bounding_boxes.remove(sub)
                            bounding_boxes.remove(box)
                            min_x = min(box[0], sub[0])
                            max_x = max(box[0] + box[2], sub[0] + sub[2])
                            min_y = min(box[1], sub[1])
                            max_y = max(box[1] + box[3], sub[1] + sub[3])
                            new_width = max_x - min_x
                            new_height = max_y - min_y
                            bounding_boxes.append((min_x, min_y, new_width, new_height))
                            break
                if reduce:
                    break
        if bounding_boxes:
            cnts, bounding_boxes = zip(*sorted(zip(cnts, bounding_boxes), key=lambda b: b[1][0]))

            chars = []

            for box in bounding_boxes:
                x, y, w, h = box
                x -= 1
                y -= 1
                w += 2
                h += 2
                if (w >= 5) and (h >= 15):
                    roi = image[y:y + h, x:x + w]
                    padded = cv2.resize(roi, (64, 64))
                    padded = padded.astype('float32') / 255.0
                    padded = np.expand_dims(padded, axis=-1)

                    chars.append((padded, (x, y, w, h)))

            chars = np.array([c[0] for c in chars], dtype='float32')

            model = load_model()
            le = get_label_encoder()
            prediction = model.predict(
                np.array([[[(pix[3][0], pix[3][0], pix[3][0]) for pix in row] for row in char] for char in chars]))
            results = dict()
            for i, row in enumerate(prediction):
                max_values, max_indices = zip(*sorted(zip(row, range(len(row))), key=lambda b: -b[0]))
                predicted_labels = le.inverse_transform(max_indices[:default_num_results])
                predicted_labels = [chr(int(label)) for label in predicted_labels]
                results[i] = {
                    'labels': predicted_labels,
                    'accuracy': [float(value) for value in max_values[:default_num_results]]
                }

            return HttpResponse(json.dumps({
                'value': ''.join([row['labels'][0] for row in results.values()]),
                'results': results
            }))
        return HttpResponse('{}', status=200)
