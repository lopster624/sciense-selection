from django.shortcuts import render
from django.views.generic.list import ListView

from .models import Direction


class DirectionView(ListView):
    model = Direction

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test'] = 'test'
        return context
