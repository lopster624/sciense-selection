from django.urls import path

from .views import DirectionView, ApplicationListView, ApplicationView, ApplicationCreateView

urlpatterns = [
    path('direction/', DirectionView.as_view(), name='direction'),
    path('application', ApplicationCreateView.as_view(), name='create_application'),
    path('application_list/', ApplicationListView.as_view(), name='application'),
    path('application_list/<int:app_id>/', ApplicationView.as_view(), name='application')
]
