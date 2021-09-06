from django.urls import path

from .views import DirectionView, ApplicationListView, ApplicationView, CreateApplicationView, \
    AddCompetencesView, DeleteCompetenceView, CreateCompetenceView, \
    ChooseDirectionInAppView, ChooseCompetenceInAppView, EditApplicationView, CompetenceListView, MasterFileTemplatesView, DeleteFileView

urlpatterns = [
    path('direction/', DirectionView.as_view(), name='direction'),
    path('application/', CreateApplicationView.as_view(), name='create_application'),

    path('application/<int:app_id>/', ApplicationView.as_view(), name='application'),
    path('application/<int:app_id>/edit', EditApplicationView.as_view(), name='edit_application'),
    path('application/<int:app_id>/direction/', ChooseDirectionInAppView.as_view(), name='choose_app_direction'),
    path('application/<int:app_id>/competence/', ChooseCompetenceInAppView.as_view(), name='choose_app_competence'),

    path('application/list/', ApplicationListView.as_view(), name='application_list'),

    path('competence/add/<int:direction_id>/', AddCompetencesView.as_view(), name='add_competences'),
    path('competence/list/', CompetenceListView.as_view(), name='competence_list'),
    path('competence/delete/<int:competence_id>/<int:direction_id>/', DeleteCompetenceView.as_view(),
         name='delete_competence'),
    path('competence/create/', CreateCompetenceView.as_view(), name='create_competence'),
    path('documents/templates/delete/<int:file_id>/', DeleteFileView.as_view(), name='delete_file'),
    path('documents/templates/', MasterFileTemplatesView.as_view(), name='documents_templates'),
]
