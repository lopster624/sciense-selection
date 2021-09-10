import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic.list import ListView

from account.models import Member, Affiliation, Booking, BookingType
from application.forms import CreateCompetenceForm, FilterForm
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
        user_app = get_object_or_404(Application, pk=app_id)
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
        context = {'app_form': app_form, 'app_active': True, 'education_formset': education_formset}
        return render(request, 'application/application_create.html', context=context)

    def post(self, request):
        app_form = ApplicationCreateForm(request.POST)
        education_formset = EducationFormSet(request.POST)
        context = {'app_active': True, 'msg': ''}
        if not Application.objects.filter(member=request.user.member):
            if app_form.is_valid() and education_formset.is_valid():
                new_app = app_form.save(commit=False)
                new_app.member = request.user.member
                new_app.save()
                for ed_form in education_formset:
                    if ed_form.cleaned_data:
                        user_education = ed_form.save(commit=False)
                        user_education.application = new_app
                        user_education.save()
                return redirect('application', app_id=new_app.pk)
            else:
                msg = 'Некорректные данные в заявке'
        else:
            msg = 'Заявка пользователя уже существует'
        context.update({'msg': msg, 'app_form': app_form, 'education_formset': education_formset})
        return render(request, 'application/application_create.html', context=context)


class CompetenceEditView(LoginRequiredMixin, View):
    def get(self, request):
        pass


class ApplicationView(LoginRequiredMixin, View):
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_education = Education.objects.filter(application=user_app).order_by('end_year').all()
        context = {'user_app': user_app, 'app_id': app_id, 'user_education': user_education, 'app_active': True}
        return render(request, 'application/application_detail.html', context=context)


class EditApplicationView(LoginRequiredMixin, View):
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_education = Education.objects.filter(application=user_app).order_by('end_year').all()
        app_form = ApplicationCreateForm(instance=user_app)
        education_formset = EducationFormSet(queryset=user_education)
        context = {'app_form': app_form, 'app_id': app_id, 'education_formset': education_formset, 'app_active': True}
        return render(request, 'application/application_edit.html', context=context)

    def post(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_education = Education.objects.filter(application=user_app).all()
        app_form = ApplicationCreateForm(request.POST, instance=user_app)
        education_formset = EducationFormSet(request.POST, queryset=user_education)
        if app_form.is_valid() and education_formset.is_valid():
            new_app = app_form.save()
            for form in education_formset:
                if not form.cleaned_data.get('DELETE') and form.cleaned_data:
                    user_education = form.save(commit=False)
                    user_education.application = new_app
                    user_education.save()
                elif form.cleaned_data.get('DELETE'):
                    educ = get_object_or_404(Education, id=form.cleaned_data['id'].id)
                    educ.delete()
            return redirect('application', app_id=new_app.pk)
        else:
            msg = 'Некорректные данные в заявке'
        context = {'app_form': app_form, 'app_id': app_id, 'education_formset': education_formset, 'app_active': True,
                   'msg': msg}
        return render(request, 'application/application_edit.html', context=context)


class DocumentsInAppView(LoginRequiredMixin, View):
    def get(self, request, app_id):
        file_templates = File.objects.filter(is_template=True).all()
        app = Application.objects.filter(pk=app_id).first()
        user_files = File.objects.filter(member=app.member).all()
        context = {'file_templates': file_templates, 'user_files': user_files, 'document_active': True,
                   'app_id': app_id}
        return render(request, 'application/application_documents.html', context=context)

    def post(self, request, app_id):
        new_files = request.FILES.getlist('downloaded_files')
        for file in new_files:
            file_name = os.path.splitext(os.path.basename(file.name))[0]
            new_file = File(member=request.user.member, file_path=file, file_name=file_name, is_template=False)
            new_file.save()
        return redirect(request.path_info)


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
        user_app = get_object_or_404(Application, pk=app_id)
        context = {'competence_active': True, 'app_id': app_id}
        if user_app:
            user_directions = user_app.directions.all()
            if user_directions:
                user_competencies = ApplicationCompetencies.objects.filter(application=user_app)
                competencies = Competence.objects.filter(directions__in=user_directions, parent_node__isnull=True).all()
                selected_competencies = {_.competence.id: _.level for _ in user_competencies}
                competence_levels = ApplicationCompetencies.competence_levels
                context.update({'levels': competence_levels, 'selected_competencies': selected_competencies,
                                'competencies': competencies})
            else:
                context.update({'msg': 'Заполните направления', 'name': 'choose_app_direction'})
        else:
            context.update({'msg': 'Создайте заявку', 'name': 'create_application'})
        return render(request, 'application/application_competence_choose.html', context=context)

    def post(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_directions = user_app.directions.all()
        competence_direction_ids = [_.id for _ in Competence.objects.filter(directions__in=user_directions).all()]
        user_app.competencies.clear()
        for comp_id in competence_direction_ids:
            level_competence = int(request.POST.get(str(comp_id), 0))
            if level_competence and level_competence != 0:
                competence = Competence.objects.filter(pk=comp_id).first()
                ApplicationCompetencies.objects.create(application=user_app, competence=competence,
                                                       level=level_competence)
        user_competencies = ApplicationCompetencies.objects.filter(application=user_app)
        selected_competencies = {_.competence.id: _.level for _ in user_competencies}
        competencies = Competence.objects.filter(directions__in=user_directions, parent_node__isnull=True).all()

        context = {'competencies': competencies, 'levels': ApplicationCompetencies.competence_levels,
                   'selected_competencies': selected_competencies, 'app_id': app_id, 'competence_active': True}
        return render(request, 'application/application_competence_choose.html', context=context)


class MasterFileTemplatesView(LoginRequiredMixin, View):
    def get(self, request):
        files = File.objects.filter(is_template=True).all()
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
        return redirect(request.META.get('HTTP_REFERER'))


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
        master_direction_id = master_affiliations.values_list('direction__id', flat=True)
        if self.request.GET:
            # тут производится вся сортировка и фильтрация
            # фильтрация по направлениям
            chosen_directions = self.request.GET.getlist('directions', None)
            if chosen_directions:
                apps = apps.filter(directions__in=chosen_directions).distinct()

            # фильтрация по бронированию
            chosen_affiliation = self.request.GET.getlist('affiliation', None)
            if chosen_affiliation:
                booked_members = Booking.objects.filter(affiliation__in=chosen_affiliation,
                                                        booking_type__name=BOOKED).values_list('slave', flat=True)
                apps = apps.filter(member__id__in=booked_members).distinct()

            # фильтрация по вишлисту
            chosen_affiliation_wishlist = self.request.GET.getlist('in_wishlist', None)
            if chosen_affiliation_wishlist:
                booked_members = Booking.objects.filter(affiliation__in=chosen_affiliation_wishlist,
                                                        booking_type__name=IN_WISHLIST).values_list('slave', flat=True)
                apps = apps.filter(member__id__in=booked_members).distinct()

            # фильтрация по сезону
            draft_season = self.request.GET.getlist('draft_season', None)
            if draft_season:
                apps = apps.filter(draft_season__in=draft_season).distinct()

            # фильтрация по году призыва
            draft_year = self.request.GET.getlist('draft_year', None)
            if draft_year:
                apps = apps.filter(draft_year__in=draft_year).distinct()

            # сортировка
            ordering = self.request.GET.get('ordering', None)
            if ordering:
                apps = apps.order_by(ordering)

        for app in apps:
            educations = Education.objects.filter(application__exact=app).order_by('-end_year')
            if educations:
                app.university = educations[0].university
                app.avg_score = educations[0].avg_score
                app.education_type = educations[0].get_education_type_display()
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
                wishlist = Booking.objects.filter(slave=app.member, booking_type__name=IN_WISHLIST,
                                                  affiliation__in=master_affiliations).values_list('affiliation',
                                                                                                   flat=True)
                if wishlist:
                    app.wishlist_affiliations = Affiliation.objects.filter(id__in=wishlist)
                    app.is_in_wishlist = True  # данный человек находится в вишлисте мастера

            slave_directions = app.directions.all()
            available_directions = slave_directions.filter(id__in=master_direction_id)
            if available_directions:
                app.our_direction = True
                app.available_affiliations = master_affiliations.filter(direction__in=slave_directions)

            else:
                app.our_direction = False

        return apps

    def get_context_data(self, **kwargs):
        master_member = Member.objects.get(user=self.request.user)
        master_affiliations = Affiliation.objects.filter(member=master_member)
        context = super().get_context_data(**kwargs)
        directions_set = [(aff.direction.id, aff.direction) for aff in master_affiliations]
        in_wishlist_set = [(affiliation.id, affiliation) for affiliation in master_affiliations]
        draft_year_set = Application.objects.order_by(
            'draft_year').distinct().values_list('draft_year', 'draft_year')
        filter_form = FilterForm(self.request.GET, directions_set=directions_set, in_wishlist_set=in_wishlist_set,
                                 draft_year_set=draft_year_set,
                                 chosen_affiliation_set=in_wishlist_set, )
        context['form'] = filter_form
        if self.request.GET:
            context['reset_filters'] = True
        context['application_active'] = True
        context['master_affiliations'] = master_affiliations
        return context


class CompetenceListView(LoginRequiredMixin, View):
    def get(self, request):
        context = get_context(self)
        return render(request, 'application/competence_list.html', context=context)

    def post(self, request):
        context = get_context(self)
        return render(request, 'application/competence_list.html', context=context)


class BookMemberView(LoginRequiredMixin, View):
    def post(self, request, app_id):
        # todo: спросить, может ли отбирающий с этого же направления удалять людей из бронирования
        #  или только тот, кто бронировал
        affiliation_id = request.POST.get('affiliation', None)
        master_member = Member.objects.get(user=request.user)
        slave_member = Member.objects.get(application__id=app_id)
        booking_type = BookingType.objects.get(name=BOOKED)
        affiliation = Affiliation.objects.get(id=affiliation_id)
        Booking(booking_type=booking_type, master=master_member, slave=slave_member, affiliation=affiliation).save()
        return redirect('application_list')


class UnBookMemberView(LoginRequiredMixin, View):
    def post(self, request, app_id, aff_id):
        master_member = Member.objects.get(user=request.user)
        slave_member = Member.objects.get(application__id=app_id)
        booking = Booking.objects.filter(master=master_member, slave=slave_member, booking_type__name=BOOKED,
                                         affiliation__id=aff_id)
        if booking:
            booking.delete()
            return redirect('application_list')
        return render(request, 'access_error.html',
                      context={'error': 'Отказано в запросе на удаление. Удалять может только пользователь, отобравший '
                                        'кандидатуру.'})


class AddInWishlist(LoginRequiredMixin, View):
    def post(self, request, app_id):
        affiliations_id = request.POST.getlist('affiliations', None)
        master_member = Member.objects.get(user=request.user)
        slave_member = Member.objects.get(application__id=app_id)
        booking_type = BookingType.objects.get(name=IN_WISHLIST)
        for affiliation_id in affiliations_id:
            affiliation = Affiliation.objects.get(id=affiliation_id)
            Booking(booking_type=booking_type, master=master_member, slave=slave_member,
                    affiliation=affiliation).save()
        return redirect('application_list')


class DeleteFromWishlist(LoginRequiredMixin, View):
    def post(self, request, app_id):
        affiliations_id = request.POST.getlist('affiliations', None)
        master_member = Member.objects.get(user=request.user)
        slave_member = Member.objects.get(application__id=app_id)
        for affiliation_id in affiliations_id:
            current_booking = Booking.objects.filter(booking_type__name=IN_WISHLIST, master=master_member,
                                                     slave=slave_member, affiliation__id=affiliation_id)
            if current_booking:
                current_booking.first().delete()
        return redirect('application_list')
