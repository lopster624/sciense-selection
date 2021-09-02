from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic.list import ListView

from account.forms import CreateCompetenceForm
from account.models import Member, Affiliation
from .forms import ApplicationCreateForm, EducationFormSet
from .models import Direction, Application, Education, Competence
from .utils import pick_competence, put_direction_in_context, delete_competence


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
                    if form.cleaned_data:
                        user_education = form.save(commit=False)
                        user_education.application = new_app
                        user_education.save()
                return redirect('application', app_id=new_app.pk)
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
        selected_direction_id = self.request.GET.get('direction')
        member = Member.objects.get(user=self.request.user)
        affiliations = Affiliation.objects.filter(member=member)
        directions = [aff.direction for aff in affiliations]
        all_competences = Competence.objects.all().filter(parent_node__isnull=True)
        if selected_direction_id:
            selected_direction_id = int(selected_direction_id)
            chosen_direction = Direction.objects.get(id=selected_direction_id)
            competences = all_competences.exclude(directions=chosen_direction)
        elif directions:
            competences = all_competences.exclude(directions=directions[0])
        else:
            competences = []
        return competences

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['competence_active'] = True
        selected_direction_id = self.request.GET.get('direction')
        context = put_direction_in_context(self, context, selected_direction_id)
        return context


class AddCompetencesView(LoginRequiredMixin, View):
    def post(self, request, direction_id):
        direction = Direction.objects.get(id=direction_id)
        chosen_competences = request.POST.getlist('chosen_competences')
        chosen_competences_id = [int(competence_id) for competence_id in chosen_competences]
        for competence_id in chosen_competences_id:
            pick_competence(competence_id, direction)
        return redirect('chosen_competence', direction_id)


class ChosenCompetenceView(LoginRequiredMixin, ListView):
    model = Competence

    def get_queryset(self):
        try:
            selected_direction_id = self.kwargs['direction_id']
        except KeyError:
            selected_direction_id = self.request.GET.get('direction')
        member = Member.objects.get(user=self.request.user)
        affiliations = Affiliation.objects.filter(member=member)
        directions = [aff.direction for aff in affiliations]
        all_competences = Competence.objects.all().filter(parent_node__isnull=True)
        if selected_direction_id:
            selected_direction_id = int(selected_direction_id)
            chosen_direction = Direction.objects.get(id=selected_direction_id)
            competences = all_competences.filter(directions=chosen_direction)
        elif directions:
            competences = all_competences.filter(directions=directions[0])
        else:
            competences = []
        return competences

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['competence_active'] = True
        try:
            selected_direction_id = self.kwargs['direction_id']
        except KeyError:
            selected_direction_id = self.request.GET.get('direction')
        context = put_direction_in_context(self, context, selected_direction_id)
        return context


class DeleteCompetenceView(LoginRequiredMixin, View):
    def get(self, request, competence_id, direction_id):
        direction = Direction.objects.get(id=direction_id)
        delete_competence(competence_id, direction)
        return redirect('chosen_competence', direction_id)


class CreateCompetenceView(LoginRequiredMixin, View):
    def get(self, request):
        form = CreateCompetenceForm(current_user=request.user)
        competence_list = Competence.objects.filter(parent_node__isnull=True)
        return render(request, 'application/create_competence.html',
                      context={'form': form, 'competence_active': True, 'competence_list': competence_list})

    def post(self, request):
        bound_form = CreateCompetenceForm(request.POST, current_user=request.user)
        competence_list = Competence.objects.filter(parent_node__isnull=True)
        if not bound_form.is_valid():
            print('error')
            return render(request, 'application/create_competence.html',
                          context={'form': bound_form, 'competence_active': True, 'competence_list': competence_list})
        bound_form.save(commit=True)
        print('all right')
        return redirect(request.path_info)
