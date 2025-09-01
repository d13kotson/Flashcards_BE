import math
from datetime import datetime, timedelta
from html.parser import HTMLParser

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import Template, Context
from django.contrib.auth.models import User


class UserPref(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pref')
    learning_rate = models.FloatField(default=0.03)


class Deck(models.Model):
    # A deck is a collection of cards.
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def due_cards(self):
        return Card.objects.filter(Q(next_due__lte=datetime.now()) | Q(next_due__isnull=True), deck=self)

    def __str__(self):
        return self.name


class DataFormat(models.Model):
    # A data format is a collection of fields which define what is available to display on a card.
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=512, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class CardFormat(models.Model):
    # A card format defines the layout of a card.
    name = models.CharField(max_length=100)
    question_html = models.TextField()
    answer_html = models.TextField()
    validation_mode = models.CharField(max_length=20, default='NONE')
    data_format = models.ForeignKey(DataFormat, on_delete=models.CASCADE)
    default_deck = models.ForeignKey(Deck, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Data(models.Model):
    # A data is the information to display on a card.
    name = models.CharField(max_length=100)
    format = models.ForeignKey(DataFormat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Card(models.Model):
    # A card is a flash card with a question side and an answer side.
    deck = models.ForeignKey(Deck, on_delete=models.SET_NULL, null=True, blank=True)
    format = models.ForeignKey(CardFormat, on_delete=models.CASCADE)
    data = models.ForeignKey(Data, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(null=True, blank=True)
    last_correct = models.DateTimeField(null=True, blank=True)
    next_due = models.DateField(null=True, blank=True)
    total_correct = models.IntegerField(default=0)
    total_wrong = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def field_data(self):
        return {
            value.field.name: value.value for value in self.data.field_value_set.all()
        }

    @property
    def question(self):
        return Template(f'{{% autoescape off %}}{self.format.question_html}{{% endautoescape %}}').render(Context(self.field_data))

    @property
    def answer(self):
        return Template(f'{{% autoescape off %}}{self.format.answer_html}{{% endautoescape %}}').render(Context(self.field_data))

    @property
    def answer_text(self):
        class HTMLFilter(HTMLParser):
            text = ''
            def handle_data(self, data):
                self.text += data
        f = HTMLFilter()
        f.feed(self.answer)
        return f.text

    def calculate_next_due(self):
        learning_rate = self.user.pref.learning_rate
        days = math.floor(learning_rate * self.current_streak ** 2 + 0.9)
        self.next_due = (self.last_seen + timedelta(days=days)).date()

    def __str__(self):
        return f'{self.format}: {self.data}'


class Field(models.Model):
    # A field is a container which defines a piece of information in a format.
    name = models.CharField(max_length=100)
    data_format = models.ForeignKey(DataFormat, on_delete=models.CASCADE)
    xpath = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class FieldValue(models.Model):
    # A field value is the actual value of a field for a certain card.
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    parent = models.ForeignKey(Data, on_delete=models.CASCADE, related_name='field_value_set')
    value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.field.name}: {self.value}'

    class Meta:
        unique_together = ('field', 'parent')


@receiver(post_save, sender=Data)
def data_post_save(sender, instance, created, *args, **kwargs):
    if created:
        card_formats = instance.format.cardformat_set.all()
        for card_format in card_formats:
            Card.objects.create(
                format=card_format,
                data=instance,
                deck=card_format.default_deck,
                user=instance.user,
            )


@receiver(post_save, sender=CardFormat)
def card_format_post_save(sender, instance, created, *args, **kwargs):
    if created:
        data_set = instance.data_format.data_set.all()
        for data in data_set:
            Card.objects.create(
                format=instance,
                data=data,
                deck=instance.default_deck,
                user=instance.user,
            )
