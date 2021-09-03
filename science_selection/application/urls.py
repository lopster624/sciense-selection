from django.conf.urls.static import static
from django.urls import path

from engine import settings
from .views import DirectionView, ApplicationListView, ApplicationView, ApplicationCreateView, \
    AddCompetencesView, DeleteCompetenceView, CreateCompetenceView, \
    ApplicationCompetenceChooseView, ApplicationDirectionChooseView, MasterFileTemplatesView, DeleteFileView, \
    CompetenceListView

urlpatterns = [
                  path('direction/', DirectionView.as_view(), name='direction'),
                  path('application/', ApplicationCreateView.as_view(), name='create_application'),
                  path('application/direction/', ApplicationDirectionChooseView.as_view(), name='choose_app_direction'),
                  path('application/competence/', ApplicationCompetenceChooseView.as_view(),
                       name='choose_app_competence'),
                  path('application/list/', ApplicationListView.as_view(), name='application'),
                  path('application/<int:app_id>/', ApplicationView.as_view(), name='application'),
                  path('application/', ApplicationCreateView.as_view(), name='create_application'),
                  path('competence/add/<int:direction_id>/', AddCompetencesView.as_view(), name='add_competences'),
                  path('competence/list/', CompetenceListView.as_view(), name='competence_list'),
                  path('competence/delete/<int:competence_id>/<int:direction_id>/', DeleteCompetenceView.as_view(),
                       name='delete_competence'),
                  path('competence/create/', CreateCompetenceView.as_view(), name='create_competence'),
                  path('documents/templates/delete/<int:file_id>/', DeleteFileView.as_view(), name='delete_file'),
                  path('documents/templates/', MasterFileTemplatesView.as_view(), name='documents_templates'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
