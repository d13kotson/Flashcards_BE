from django.shortcuts import render, get_object_or_404

from flash_cards_api import models, serializers


def decks(request):
    return render(request, 'deck/list.html', {})


def deck_create(request):
    return render(request, 'deck/create_edit.html', context={
        'name': '',
        'id': None,
        'action': 'Create'
    })


def deck_edit(request, deck_id):
    deck = get_object_or_404(models.Deck, pk=deck_id)
    serializer = serializers.DeckSerializer(deck)
    return render(request, 'deck/create_edit.html', context={**serializer.data, 'action': 'Edit'})


def data_formats(request):
    return render(request, 'data_format/list.html', {})


def data_format_create(request):
    return render(request, 'data_format/create_edit.html', context={
        'name': '',
        'id': None,
        'action': 'Create'
    })


def data_format_edit(request, data_format_id):
    data_format = get_object_or_404(models.DataFormat, pk=data_format_id)
    serializer = serializers.DataFormatSerializer(data_format)
    return render(request, 'data_format/create_edit.html', context={**serializer.data, 'action': 'Edit'})


def card_formats(request):
    return render(request, 'card_format/list.html', {})


def card_format_create(request):
    return render(request, 'card_format/create_edit.html', context={
        'name': '',
        'id': None,
        'default_deck': 0,
        'data_format': 0,
        'action': 'Create'
    })


def card_format_edit(request, card_format_id):
    card_format = get_object_or_404(models.CardFormat, pk=card_format_id)
    serializer = serializers.CardFormatSerializer(card_format)
    return render(request, 'card_format/create_edit.html', context={**serializer.data, 'action': 'Edit'})


def data(request):
    return render(request, 'data/list.html', {})


def data_create(request):
    return render(request, 'data/create_edit.html', context={
        'name': '',
        'id': None,
        'format': 0,
        'action': 'Create'
    })


def data_edit(request, data_id):
    data = get_object_or_404(models.Data, pk=data_id)
    serializer = serializers.DataSerializer(data)
    return render(request, 'data/create_edit.html', context={**serializer.data, 'action': 'Edit'})
