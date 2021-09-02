from django.urls import path

from .views import DirectionView, ApplicationListView, ApplicationView, ApplicationCreateView, CompetenceChooseView, \
    AddCompetencesView, ChosenCompetenceView, DeleteCompetenceView, DirectionChooseView

urlpatterns = [
    path('direction/', DirectionView.as_view(), name='direction'),
    path('application/', ApplicationCreateView.as_view(), name='create_application'),
    path('application/direction/', DirectionChooseView.as_view(), name='choose_direction'),
    path('application/list/', ApplicationListView.as_view(), name='application'),
    path('application/<int:app_id>/', ApplicationView.as_view(), name='application'),
    path('competence/choose/add/<int:direction_id>/', AddCompetencesView.as_view(), name='add_competences'),
    path('competence/choose/', CompetenceChooseView.as_view(), name='competence_choose'),
    path('competence/chosen/<int:direction_id>/', ChosenCompetenceView.as_view(), name='chosen_competence'),
    path('competence/chosen/', ChosenCompetenceView.as_view(), name='chosen_competence'),
    path('competence/delete/<int:competence_id>/<int:direction_id>/', DeleteCompetenceView.as_view(),
         name='delete_competence'),

]
