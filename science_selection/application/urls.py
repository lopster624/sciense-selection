from django.urls import path
from . import views

urlpatterns = [
    path('application/', views.CreateApplicationView.as_view(), name='create_application'),

    path('application/<int:app_id>/', views.ApplicationView.as_view(), name='application'),
    path('application/<int:app_id>/edit/', views.EditApplicationView.as_view(), name='edit_application'),
    path('application/<int:app_id>/direction/', views.ChooseDirectionInAppView.as_view(), name='choose_app_direction'),
    path('application/<int:app_id>/competence/', views.ChooseCompetenceInAppView.as_view(), name='choose_app_competence'),
    path('application/<int:app_id>/documents/', views.DocumentsInAppView.as_view(), name='app_documents'),
    path('application/<int:app_id>/word/', views.CreateWordAppView.as_view(), name='create_word_app'),
    path('application/<int:app_id>/add_note/', views.EditApplicationNote.as_view(), name='add_application_note'),
    path('application/list/', views.ApplicationListView.as_view(), name='application_list'),
    path('application/<int:app_id>/finished/', views.ChangeAppFinishedView.as_view(), name='change_finished'),
    path('application/list/rating-list/', views.CreateRatingListView.as_view(), name='create_rating_list_word'),
    path('application/list/candidates-list/', views.CreateCandidatesListView.as_view(), name='create_candidates_list_word'),

    path('competence/add/<int:direction_id>/', views.AddCompetencesView.as_view(), name='add_competences'),
    path('competence/list/', views.CompetenceListView.as_view(), name='competence_list'),
    path('competence/delete/<int:competence_id>/<int:direction_id>/', views.DeleteCompetenceView.as_view(),
         name='delete_competence'),
    path('competence/create/', views.CreateCompetenceView.as_view(), name='create_competence'),
    path('documents/templates/delete/<int:file_id>/', views.DeleteFileView.as_view(), name='delete_file'),
    path('documents/templates/', views.MasterFileTemplatesView.as_view(), name='documents_templates'),
    path('booking/<int:app_id>/', views.BookMemberView.as_view(), name='book_member'),
    path('booking/delete/<int:app_id>/<int:aff_id>/', views.UnBookMemberView.as_view(), name='un-book_member'),
    path('wishlist/add/<int:app_id>/', views.AddInWishlistView.as_view(), name='add_in_wishlist'),
    path('wishlist/delete/<int:app_id>/', views.DeleteFromWishlistView.as_view(), name='delete_from_wishlist'),

    path('search/universities/', views.ajax_search_universities, name='ajax_search_universities'),
    path('search/competencies/', views.CompetenceAutocomplete.as_view(), name='search_competencies',),
]
