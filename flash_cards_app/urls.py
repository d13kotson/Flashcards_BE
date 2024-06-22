from django.urls import path
from flash_cards_app import views


urlpatterns = [
    path('decks/', views.decks),
    path('decks/create/', views.deck_create),
    path('decks/<int:deck_id>/', views.deck_edit),
    path('data-formats/', views.data_formats),
    path('data-formats/create/', views.data_format_create),
    path('data-formats/<int:data_format_id>/', views.data_format_edit),
    path('card-formats/', views.card_formats),
    path('card-formats/create/', views.card_format_create),
    path('card-formats/<int:card_format_id>/', views.card_format_edit),
    path('data/', views.data),
    path('data/create/', views.data_create),
    path('data/<int:data_id>/', views.data_edit),
]
