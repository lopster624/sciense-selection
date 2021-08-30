from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.views.generic.list import ListView

from .models import Direction, Application


class DirectionView(LoginRequiredMixin, ListView):
    model = Direction

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test'] = 'test'
        return context


class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application


class CompetenceEditView(LoginRequiredMixin, View):
    def get(self, request):
        pass
