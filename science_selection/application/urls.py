from django.urls import path

from .views import DirectionView, ApplicationListView, ApplicationView, ApplicationCreateView, CompetenceChooseView, DirectionChooseView

urlpatterns = [
    path('direction/', DirectionView.as_view(), name='direction'),
    path('application/', ApplicationCreateView.as_view(), name='create_application'),
    path('application/direction/', DirectionChooseView.as_view(), name='choose_direction'),
    path('application/list/', ApplicationListView.as_view(), name='application'),
    path('application/<int:app_id>/', ApplicationView.as_view(), name='application'),
    path('competence/choose/', CompetenceChooseView.as_view(), name='competence_choose'),
]