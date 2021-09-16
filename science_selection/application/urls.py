from django.urls import path

from .views import ApplicationListView, ApplicationView, CreateApplicationView, \
    AddCompetencesView, DeleteCompetenceView, CreateCompetenceView, \
    BookMemberView, UnBookMemberView, AddInWishlistView, DeleteFromWishlistView, \
    ChooseDirectionInAppView, ChooseCompetenceInAppView, EditApplicationView, CompetenceListView, \
    MasterFileTemplatesView, DeleteFileView, DocumentsInAppView, CreateWordAppView, EditApplicationNoteView, \
    ChangeAppFinishedView

urlpatterns = [
    path('application/', CreateApplicationView.as_view(), name='create_application'),

    path('application/<int:app_id>/', ApplicationView.as_view(), name='application'),
    path('application/<int:app_id>/edit/', EditApplicationView.as_view(), name='edit_application'),
    path('application/<int:app_id>/direction/', ChooseDirectionInAppView.as_view(), name='choose_app_direction'),
    path('application/<int:app_id>/competence/', ChooseCompetenceInAppView.as_view(), name='choose_app_competence'),
    path('application/<int:app_id>/documents/', DocumentsInAppView.as_view(), name='app_documents'),
    path('application/<int:app_id>/word/', CreateWordAppView.as_view(), name='create_word_app'),
    path('application/<int:app_id>/add_note/', EditApplicationNoteView.as_view(), name='add_application_note'),
    path('application/list/', ApplicationListView.as_view(), name='application_list'),
    path('application/<int:app_id>/finished/', ChangeAppFinishedView.as_view(), name='change_finished'),

    path('competence/add/<int:direction_id>/', AddCompetencesView.as_view(), name='add_competences'),
    path('competence/list/', CompetenceListView.as_view(), name='competence_list'),
    path('competence/delete/<int:competence_id>/<int:direction_id>/', DeleteCompetenceView.as_view(),
         name='delete_competence'),
    path('competence/create/', CreateCompetenceView.as_view(), name='create_competence'),
    path('documents/templates/delete/<int:file_id>/', DeleteFileView.as_view(), name='delete_file'),
    path('documents/templates/', MasterFileTemplatesView.as_view(), name='documents_templates'),
    path('booking/<int:app_id>/', BookMemberView.as_view(), name='book_member'),
    path('booking/delete/<int:app_id>/<int:aff_id>/', UnBookMemberView.as_view(), name='un-book_member'),
    path('wishlist/add/<int:app_id>/', AddInWishlistView.as_view(), name='add_in_wishlist'),
    path('wishlist/delete/<int:app_id>/', DeleteFromWishlistView.as_view(), name='delete_from_wishlist'),

]
