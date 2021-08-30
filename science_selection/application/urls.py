from django.urls import path

from .views import DirectionView, ApplicationListView, ApplicationView

urlpatterns = [
    path('direction/', DirectionView.as_view(), name='direction'),
    path('application_list/', ApplicationListView.as_view(), name='application'),
    path('application_list/<int:app_id>/', ApplicationView.as_view(), name='application')
]
