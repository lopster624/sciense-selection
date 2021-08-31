from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.views.generic.list import ListView

from .forms import ApplicationCreateForm, EducationFormSet
from .models import Direction, Application, Education


class DirectionView(LoginRequiredMixin, ListView):
    model = Direction

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test'] = 'test'
        return context


class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application

    def get_queryset(self):
        apps = Application.objects.all()
        for app in apps:
            try:
                educations = Education.objects.filter(application__exact=app).order_by('-end_year')
                app.university = educations[0].university
                app.avg_score = educations[0].avg_score
            except IndexError:
                app.university = ''
                app.avg_score = ''
        return apps

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['now'] =
        return context


class ApplicationCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form_app = ApplicationCreateForm()
        form_factory = EducationFormSet(queryset=Education.objects.none())
        return render(request, 'application_create.html', context={'form_app': form_app, 'form_factory': form_factory})

    def post(self, request):
        form = ApplicationCreateForm(request.POST)

        if form.is_valid():
            b = form.cleaned_data
            print(b)
        return render(request, 'application_create.html', context={'form': form})


class CompetenceEditView(LoginRequiredMixin, View):
    def get(self, request):
        pass


class ApplicationView(LoginRequiredMixin, View):
    def get(self, request, app_id):
        pass
