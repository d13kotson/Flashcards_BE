from django.shortcuts import redirect, render


def index(request):
    return redirect('/app/decks', permanent=True)


def react(request):
    return render(request, 'index.html', {})
