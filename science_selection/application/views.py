from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic.list import ListView

from account.models import Member, Affiliation
from .forms import ApplicationCreateForm, EducationFormSet
from .models import Direction, Application, Education, Competence


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
        context['application_active'] = True
        return context


class ApplicationCreateView(LoginRequiredMixin, View):
    def get(self, request):
        app_form = ApplicationCreateForm()
        education_formset = EducationFormSet(queryset=Education.objects.none())
        return render(request, 'application_create.html',
                      context={'app_form': app_form, 'education_formset': education_formset})

    def post(self, request):
        app_form = ApplicationCreateForm(request.POST)
        education_formset = EducationFormSet(request.POST)
        msg = ''
        if not Application.objects.filter(member=request.user.member):
            if app_form.is_valid() and education_formset.is_valid():
                new_app = app_form.save(commit=False)
                new_app.member = request.user.member
                new_app.save()
                for form in education_formset:
                    user_education = form.save(commit=False)
                    user_education.application = new_app
                    user_education.save()
        else:
            msg = 'Заявка пользователя уже существует'
        return render(request, 'application_create.html',
                      context={'app_form': app_form, 'education_formset': education_formset,
                               'msg': msg})


class CompetenceEditView(LoginRequiredMixin, View):
    def get(self, request):
        pass


class ApplicationView(LoginRequiredMixin, View):
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_education = Education.objects.filter(application=user_app)
        return render(request, 'application_detail.html',
                      context={'user_app': user_app, 'user_education': user_education})


class CompetenceChooseView(LoginRequiredMixin, ListView):
    model = Competence
    template_name = 'application/competence_choose.html'

    def get_queryset(self):

        member = Member.objects.get(user=self.request.user)
        affiliations = Affiliation.objects.filter(member=member)
        directions = [aff.direction for aff in affiliations]
        if directions:
            competences = Competence.objects.all().filter(parent_node__isnull=True).exclude(directions=directions[0])
        else:
            competences = Competence.objects.all().filter(parent_node__isnull=True)
        return competences

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = Member.objects.get(user=self.request.user)
        affiliations = Affiliation.objects.filter(member=member)
        context['directions'] = [aff.direction for aff in affiliations]
        context['competence_active'] = True
        return context
