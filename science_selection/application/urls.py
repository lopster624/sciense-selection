from django.urls import path
from . import views

urlpatterns = [
    path('application/', views.CreateApplicationView.as_view(), name='create_application'),

    path('application/<int:pk>/', views.ApplicationView.as_view(), name='application'),
    path('application/<int:pk>/edit/', views.EditApplicationView.as_view(), name='edit_application'),
    path('application/<int:pk>/direction/', views.ChooseDirectionInAppView.as_view(), name='choose_app_direction'),
    path('application/<int:pk>/competence/', views.ChooseCompetenceInAppView.as_view(), name='choose_app_competence'),
    path('application/<int:pk>/documents/', views.DocumentsInAppView.as_view(), name='app_documents'),
    path('application/<int:pk>/word/', views.CreateWordAppView.as_view(), name='create_word_app'),
    path('application/<int:pk>/add_note/', views.EditApplicationNote.as_view(), name='add_application_note'),
    path('application/list/', views.ApplicationListView.as_view(), name='application_list'),
    path('application/<int:pk>/finished/', views.ChangeAppFinishedView.as_view(), name='change_finished'),
    path('application/list/service-document/', views.CreateServiceDocumentView.as_view(), name='create_word_service_document'),

    path('competence/add/<int:direction_id>/', views.AddCompetencesView.as_view(), name='add_competences'),
    path('competence/list/', views.CompetenceListView.as_view(), name='competence_list'),
    path('competence/delete/<int:competence_id>/<int:direction_id>/', views.DeleteCompetenceView.as_view(),
         name='delete_competence'),
    path('competence/create/', views.CreateCompetenceView.as_view(), name='create_competence'),
    path('documents/templates/delete/<int:file_id>/', views.DeleteFileView.as_view(), name='delete_file'),
    path('documents/templates/', views.MasterFileTemplatesView.as_view(), name='documents_templates'),
    path('booking/<int:pk>/', views.BookMemberView.as_view(), name='book_member'),
    path('booking/delete/<int:pk>/<int:aff_id>/', views.UnBookMemberView.as_view(), name='un-book_member'),
    path('wishlist/add/<int:pk>/', views.AddInWishlistView.as_view(), name='add_in_wishlist'),
    path('wishlist/delete/<int:pk>/', views.DeleteFromWishlistView.as_view(), name='delete_from_wishlist'),

    path('search/universities/', views.ajax_search_universities, name='ajax_search_universities'),
    path('search/competencies/', views.CompetenceAutocomplete.as_view(), name='search_competencies',),
]
