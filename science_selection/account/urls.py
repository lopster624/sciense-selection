from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from .views import RegistrationView, ActivationView, HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('activation/<str:token>/', ActivationView.as_view(), name='activation'),

]
