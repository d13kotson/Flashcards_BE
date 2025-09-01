from django.urls import include, path
from flash_cards_api import views
from rest_framework import routers


router = routers.DefaultRouter()
router.register('decks', views.DeckViewSet, basename='deck')
router.register('data-formats', views.DataFormatViewSet, basename='dataformat')
router.register('card-formats', views.CardFormatViewSet, basename='cardformat')
router.register('data', views.DataViewSet, basename='data')
router.register('cards', views.CardViewSet, basename='card')

urlpatterns = [
    path('', include(router.urls)),
]
