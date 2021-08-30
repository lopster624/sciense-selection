from django.urls import path

from .views import DirectionView, ApplicationListView

urlpatterns = [
    path('direction/', DirectionView.as_view(), name='direction'),
    path('application_list/', ApplicationListView.as_view(), mame='application')
]
