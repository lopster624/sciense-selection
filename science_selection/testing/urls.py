from django.urls import path
from . import views

urlpatterns = [
    path('', views.CreateTestView.as_view(), name='create_test'),
    path('list/',  views.TestListView.as_view(), name='test_list'),
    path('list/results/',  views.TestResultsView.as_view(), name='test_results'),
    path('<int:pk>/',  views.DetailTestView.as_view(), name='test'),
    path('<int:pk>/edit/',  views.EditTestView.as_view(), name='edit_test'),
    path('<int:pk>/delete/', views.DeleteTestView.as_view(), name='delete_test'),
    path('<int:pk>/result/', views.AddTestResultView.as_view(), name='add_test_result'),
]
