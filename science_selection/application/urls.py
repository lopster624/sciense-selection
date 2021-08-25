from django.urls import path

from .views import DirectionView


urlpatterns = [
    path('direction/', DirectionView.as_view(), name='direction')
]
