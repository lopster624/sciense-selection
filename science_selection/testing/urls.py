from django.urls import path
from . import views

urlpatterns = [
    path('', views.CreateTestView.as_view(), name='create_test'),
    path('list/',  views.TestListView.as_view(), name='test_list'),
    path('results/',  views.TestResultsView.as_view(), name='test_results'),
    path('add/<int:direction_id>/', views.AddTestInDirectionView.as_view(), name='add_test'),
    path('exclude/<int:test_id>/<int:direction_id>/', views.ExcludeTestInDirectionView.as_view(), name='exclude_test'),
    path('<int:pk>/',  views.DetailTestView.as_view(), name='test'),
    path('<int:pk>/question/',  views.AddQuestionToTestView.as_view(), name='add_question_to_test'),
    path('<int:pk>/question/<int:question_id>/',  views.UpdateQuestionView.as_view(), name='update_question'),
    path('<int:pk>/question/<int:question_id>/delete/',  views.DeleteQuestionView.as_view(), name='delete_question'),
    path('<int:pk>/edit/',  views.EditTestView.as_view(), name='edit_test'),
    path('<int:pk>/delete/', views.DeleteTestView.as_view(), name='delete_test'),
    path('<int:pk>/result/', views.AddTestResultView.as_view(), name='add_test_result'),
    path('<int:pk>/result/<int:result_id>/', views.TestResultView.as_view(), name='test_result'),
    path('<int:pk>/result/<int:result_id>/word/', views.TestResultInWordView.as_view(), name='test_result_in_word'),
]
