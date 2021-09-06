from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic.list import ListView

from application.forms import CreateCompetenceForm
from account.models import Member, Affiliation, Booking
from utils.constants import BOOKED, IN_WISHLIST
from .forms import ApplicationCreateForm, EducationFormSet
from .models import Direction, Application, Education, Competence, ApplicationCompetencies, File
from .utils import pick_competence, delete_competence, get_context


class DirectionView(LoginRequiredMixin, ListView):
    model = Direction

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test'] = 'test'
        return context


class ChooseDirectionInAppView(LoginRequiredMixin, View):
    def get(self, request, app_id):
        # TODO: сначала проверка на существование заявки?
        user_app = get_object_or_404(Application, pk=app_id)
        # user_app = Application.objects.filter(pk=app_id).first()
        context = {'direction_active': True, 'app_id': app_id}
        if user_app:
            directions = Direction.objects.all()
            selected_directions = [_.id for _ in user_app.directions.all()]
            context.update({'directions': directions, 'selected_directions': selected_directions})
        else:
            context.update({'msg': 'Создайте заявку', 'name': 'create_application'})
        return render(request, 'application/application_direction_choose.html', context=context)

    def post(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        # user_app = Application.objects.filter(member=request.user.member).first()
        if user_app:
            selected_directions = request.POST.getlist('direction')
            user_app.directions.clear()
            if selected_directions:
                directions = Direction.objects.filter(pk__in=selected_directions)
                user_app.directions.add(*list(directions))
        directions = Direction.objects.all()
        context = {'directions': directions, 'selected_directions': list(map(int, selected_directions)),
                   'direction_active': True, 'app_id': app_id}
        return render(request, 'application/application_direction_choose.html', context=context)


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


class CreateApplicationView(LoginRequiredMixin, View):
    def get(self, request):
        user_app = Application.objects.filter(member=request.user.member).first()
        if user_app:
            return redirect('application', app_id=user_app.id)
        app_form = ApplicationCreateForm()
        education_formset = EducationFormSet(queryset=Education.objects.none())
        return render(request, 'application/application_create.html',
                      context={'app_form': app_form, 'education_formset': education_formset, 'app_active': True})

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
        return render(request, 'application/application_create.html',
                      context={'app_form': app_form, 'education_formset': education_formset, 'app_active': True,
                               'msg': msg})


class CompetenceEditView(LoginRequiredMixin, View):
    def get(self, request):
        pass


class ApplicationView(LoginRequiredMixin, View):
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_education = Education.objects.filter(application=user_app)
        return render(request, 'application/application_detail.html',
                      context={'user_app': user_app, 'app_id': app_id, 'user_education': user_education, 'app_active': True})


class EditApplicationView(LoginRequiredMixin, View):
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_education = Education.objects.filter(application=user_app)
        app_form = ApplicationCreateForm(instance=user_app)
        education_formset = EducationFormSet(queryset=user_education)
        return render(request, 'application/application_edit.html',
                      context={'app_form': app_form, 'app_id': app_id, 'education_formset': education_formset, 'app_active': True})

    def post(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        app_form = ApplicationCreateForm(request.POST, instance=user_app)
        user_education = Education.objects.filter(application=user_app).all()
        education_formset = EducationFormSet(request.POST, queryset=user_education)
        if app_form.is_valid() and education_formset.is_valid():
            new_app = app_form.save()
            for form in education_formset:
                if form.cleaned_data:
                    user_education = form.save(commit=False)
                    user_education.application = new_app
                    user_education.save()
            return redirect('application', app_id=new_app.pk)
        return render(request, 'application/application_edit.html',
                      context={'app_form': app_form, 'app_id': app_id, 'education_formset': education_formset, 'app_active': True})


class AddCompetencesView(LoginRequiredMixin, View):
    def post(self, request, direction_id):
        # TODO: возможно нужно сделать автоматический выбор дочерних элементов при выборе родительских
        direction = Direction.objects.get(id=direction_id)
        chosen_competences = request.POST.getlist('chosen_competences')
        chosen_competences_id = [int(competence_id) for competence_id in chosen_competences]
        for competence_id in chosen_competences_id:
            pick_competence(competence_id, direction)
        return redirect(reverse('competence_list') + f'?direction={direction_id}')


class DeleteCompetenceView(LoginRequiredMixin, View):
    def get(self, request, competence_id, direction_id):
        direction = Direction.objects.get(id=direction_id)
        delete_competence(competence_id, direction)
        return redirect(reverse('competence_list') + f'?direction={direction_id}')


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
            return render(request, 'application/create_competence.html',
                          context={'form': bound_form, 'competence_active': True, 'competence_list': competence_list})
        bound_form.save(commit=True)
        return redirect(request.path_info)


class ChooseCompetenceInAppView(LoginRequiredMixin, View):
    def get(self, request, app_id):
        #TODO: сначала проверка на существование заявки?
        user_app = get_object_or_404(Application, pk=app_id)
        context = {'competence_active': True, 'app_id': app_id}
        if user_app:
            user_directions = user_app.directions.all()
            if user_directions:
                user_competencies = ApplicationCompetencies.objects.filter(application=user_app)
                competencies = Competence.objects.filter(directions__in=user_directions).all()
                selected_competencies = {_.competence.id: _.level for _ in user_competencies} if user_app else {}
                competence_level = ApplicationCompetencies.competence_level
                context.update({'competencies': competencies, 'levels': competence_level, 'selected_competencies': selected_competencies})
            else:
                context.update({'msg': 'Заполните направления', 'name': 'choose_app_direction'})
        else:
            context.update({'msg': 'Создайте заявку', 'name': 'create_application'})
        return render(request, 'application/application_competence_choose.html', context=context)

    def post(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_directions = user_app.directions.all()
        competencies = Competence.objects.filter(directions__in=user_directions).all()
        competence_ids = [_.id for _ in competencies]
        user_app.competencies.clear()
        for key in competence_ids:
            level_competence = int(request.POST.get(str(key), 0))
            if level_competence and level_competence != 0:
                competence = Competence.objects.filter(id=key).first()
                ApplicationCompetencies.objects.create(application=user_app, competence=competence,
                                                       level=level_competence)
        user_competencies = ApplicationCompetencies.objects.filter(application=user_app)
        selected_competencies = {_.competence.id: _.level for _ in user_competencies} if user_app else {}
        competence_level = ApplicationCompetencies.competence_level
        context = {'competencies': competencies, 'levels': competence_level, 'selected_competencies': selected_competencies,
                   'app_id': app_id, 'competence_active': True}
        return render(request, 'application/application_competence_choose.html', context=context)


class MasterFileTemplatesView(LoginRequiredMixin, View):
    def get(self, request):
        files = File.objects.all()
        # показывает список уже загруженных файлов на сервер и позволяет загрузить новые
        return render(request, 'application/documents.html', context={'file_list': files})

    def post(self, request):
        new_files = request.FILES.getlist('downloaded_files')
        member = Member.objects.get(user=request.user)
        for file in new_files:
            new_file = File(member=member, file_path=file, is_template=True)
            new_file.save()
            new_file.file_name = new_file.file_path.name.split('/')[-1]  # отделяется название от пути загрузки
            new_file.save()
        return redirect(request.path_info)


class DeleteFileView(LoginRequiredMixin, View):
    def get(self, request, file_id):
        file = File.objects.get(id=file_id)
        file.delete()
        return redirect('documents_templates')


class ApplicationListView(LoginRequiredMixin, ListView):
    """
    Класс отображения списка заявок.

    Среди заявок предусмотрена сортировка по следующим параметрам: ФИО, Ср. балл, итог. балл, заполненность
    Среди заявок предусмотрен следующий список фильтров:
    Направления заявки: список направлений заявки
    Отобран в: список принадлежностей мастера
    В вишлисте в: список принадлежностей мастера

    Заявки отображаются по следующим правилам:
    Если человек подавал на одно из направлений отбирающего, то анкета этого человека показывается

    Заметки:
    Возможно нужно добавить поле для бронирования и добавление в избранное, где в избранном будет показываться звездочка и кол-во человек, которое добавили в избранное
    Возможные способы пометок: шрифт: жирный/нет, цвет рамки, цвет бекграунда
    Жирным шрифтом помечаются забронированные, также у них отображается, куда(рота, взвод) они были забронированы.
    Цвет рамки зеленый - если заявка была подана на направление, на которое отбирает отбирающий.

    """
    model = Application

    def get_queryset(self):
        apps = Application.objects.all()
        master_member = Member.objects.get(user=self.request.user)
        master_affiliations = Affiliation.objects.filter(member=master_member)
        master_directions = [aff.direction for aff in master_affiliations]
        for app in apps:
            educations = Education.objects.filter(application__exact=app).order_by('-end_year')
            if educations:
                app.university = educations[0].university
                app.avg_score = educations[0].avg_score
            app.draft_time = app.get_draft_time()
            booking = Booking.objects.filter(slave=app.member, booking_type__name=BOOKED)
            if booking:
                app.is_booked = True  # данный человек в принципе забронирован
                app.affiliation = booking.first().affiliation
                if booking.filter(affiliation__in=master_affiliations):
                    app.is_booked_our = True
            in_wishlist = Booking.objects.filter(slave=app.member, booking_type__name=IN_WISHLIST)
            if in_wishlist:
                app.wishlist_len = len(in_wishlist)
                if Booking.objects.filter(slave=app.member, booking_type__name=IN_WISHLIST,
                                          affiliation__in=master_affiliations):
                    app.is_in_wishlist = True  # данный человек находится в вишлисте мастера
        return apps

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application_active'] = True
        return context


class CompetenceListView(LoginRequiredMixin, View):
    def get(self, request):
        context = get_context(self)
        return render(request, 'application/competence_list.html', context=context)

    def post(self, request):
        context = get_context(self)
        return render(request, 'application/competence_list.html', context=context)
