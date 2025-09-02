from django.contrib import admin
from django.urls import path, include
from .views import index, react

urlpatterns = [
    path('', index),
    path('react/', react),
    path('admin/', admin.site.urls),
    path('api/', include('flash_cards_api.urls')),
    path('app/', include('flash_cards_app.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
