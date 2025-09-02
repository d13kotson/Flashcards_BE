from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template.response import TemplateResponse

from flash_cards_api import models, serializers


@login_required
def decks(request):
    return render(request, 'deck/list.html', {})


@login_required
def deck_create(request):
    return render(request, 'deck/create_edit.html', context={
        'name': '',
        'id': None,
        'action': 'Create'
    })


@login_required
def deck_edit(request, deck_id):
    deck = get_object_or_404(models.Deck, pk=deck_id)
    serializer = serializers.DeckSerializer(deck)
    return render(request, 'deck/create_edit.html', context={**serializer.data, 'action': 'Edit'})


@login_required
def deck_quiz(request, deck_id):
    deck = get_object_or_404(models.Deck, pk=deck_id)
    serializer = serializers.DeckSerializer(deck)
    if deck.due_cards.count() > 0:
        return render(request, 'deck/quiz.html', context=serializer.data)
    else:
        return redirect('/app/decks')


@login_required
def deck_study(request, deck_id):
    deck = get_object_or_404(models.Deck, pk=deck_id)
    serializer = serializers.DeckSerializer(deck)
    return render(request, 'deck/study.html', context=serializer.data)


@login_required
def data_formats(request):
    return render(request, 'data_format/list.html', {})


@login_required
def data_format_create(request):
    return render(request, 'data_format/create_edit.html', context={
        'name': '',
        'id': None,
        'action': 'Create'
    })


@login_required
def data_format_edit(request, data_format_id):
    data_format = get_object_or_404(models.DataFormat, pk=data_format_id)
    serializer = serializers.DataFormatSerializer(data_format)
    return render(request, 'data_format/create_edit.html', context={**serializer.data, 'action': 'Edit'})


@login_required
def card_formats(request):
    return render(request, 'card_format/list.html', {})


@login_required
def card_format_create(request):
    return render(request, 'card_format/create_edit.html', context={
        'name': '',
        'id': None,
        'default_deck': 0,
        'data_format': 0,
        'action': 'Create'
    })


@login_required
def card_format_edit(request, card_format_id):
    card_format = get_object_or_404(models.CardFormat, pk=card_format_id)
    serializer = serializers.CardFormatSerializer(card_format)
    return render(request, 'card_format/create_edit.html', context={**serializer.data, 'action': 'Edit'})


@login_required
def card_front(request, card_id):
    card = get_object_or_404(models.Card, pk=card_id)
    serializer = serializers.CardSerializer(card)
    response = TemplateResponse(request, 'card/front.html', context=serializer.data)
    return response


@login_required
def card_back(request, card_id):
    card = get_object_or_404(models.Card, pk=card_id)
    serializer = serializers.CardSerializer(card)
    response = TemplateResponse(request, 'card/back.html', context=serializer.data)
    return response


@login_required
def data(request):
    return render(request, 'data/list.html', {})


@login_required
def data_create(request):
    return render(request, 'data/create_edit.html', context={
        'name': '',
        'id': None,
        'format': 0,
        'action': 'Create'
    })


@login_required
def data_edit(request, data_id):
    data = get_object_or_404(models.Data, pk=data_id)
    serializer = serializers.DataSerializer(data)
    print(serializer.data)
    return render(request, 'data/create_edit.html', context={**serializer.data, 'action': 'Edit'})
