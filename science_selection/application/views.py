import json
import os

from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.encoding import escape_uri_path
from django.views import View
from django.views.generic import CreateView
from django.views.generic.list import ListView

from account.models import Member, Affiliation, Booking, BookingType
from application.forms import CreateCompetenceForm, FilterForm
from utils.constants import BOOKED, IN_WISHLIST, MASTER_ROLE_NAME, SLAVE_ROLE_NAME, PATH_TO_INTERVIEW_LIST, \
    PATH_TO_CANDIDATES_LIST, PATH_TO_RATING_LIST
from .forms import ApplicationCreateForm, EducationFormSet, ApplicationMasterForm
from .mixins import OnlySlaveAccessMixin, OnlyMasterAccessMixin, DataApplicationMixin, MasterDataMixin
from .models import Direction, Application, Education, Competence, ApplicationCompetencies, File, ApplicationNote, \
    Universities
from .utils import pick_competence, delete_competence, get_context, \
    check_permission_decorator, WordTemplate, check_booking_our, check_role, get_filtered_sorted_queryset, \
    get_application_note


class ChooseDirectionInAppView(LoginRequiredMixin, View):
    @check_permission_decorator(MASTER_ROLE_NAME)
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        context = {'direction_active': True, 'app_id': app_id}
        if user_app:
            if request.user.member.role.role_name == MASTER_ROLE_NAME or user_app.is_final:
                context.update({'blocked': True})
            directions = Direction.objects.all()
            selected_directions = [_.id for _ in user_app.directions.all()]
            context.update({'directions': directions, 'selected_directions': selected_directions})
        else:
            context.update({'msg': 'Создайте заявку', 'name': 'create_application'})
        return render(request, 'application/application_direction_choose.html', context=context)

    @check_permission_decorator()
    def post(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        if user_app.is_final:
            return redirect(request.path_info)
        selected_directions = request.POST.getlist('direction')
        user_app.directions.clear()
        if selected_directions:
            directions = Direction.objects.filter(pk__in=selected_directions)
            user_app.directions.add(*list(directions))
        user_app.save()
        directions = Direction.objects.all()
        context = {'directions': directions, 'selected_directions': list(map(int, selected_directions)),
                   'direction_active': True, 'app_id': app_id}
        return render(request, 'application/application_direction_choose.html', context=context)


class CreateApplicationView(LoginRequiredMixin, OnlySlaveAccessMixin, View):
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


class ApplicationView(LoginRequiredMixin, View):
    @check_permission_decorator(role_name=MASTER_ROLE_NAME)
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_education = user_app.education.order_by('end_year').all()
        context = {'user_app': user_app, 'app_id': app_id, 'user_education': user_education, 'app_active': True}
        return render(request, 'application/application_detail.html', context=context)


class EditApplicationView(LoginRequiredMixin, View):
    @check_permission_decorator(MASTER_ROLE_NAME)
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        if user_app.is_final and check_role(request.user, SLAVE_ROLE_NAME):
            raise PermissionDenied('Редактирование анкеты недоступно.')
        user_education = user_app.education.order_by('end_year').all()
        app_form = ApplicationCreateForm(instance=user_app) if check_role(request.user,
                                                                          SLAVE_ROLE_NAME) else ApplicationMasterForm(
            instance=user_app)
        education_formset = EducationFormSet(queryset=user_education)
        context = {'app_form': app_form, 'app_id': app_id, 'education_formset': education_formset, 'app_active': True}
        return render(request, 'application/application_edit.html', context=context)

    @check_permission_decorator(MASTER_ROLE_NAME)
    def post(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        user_role = request.user.member.role.role_name
        if user_app.is_final and user_role == SLAVE_ROLE_NAME:
            raise PermissionDenied('Редактирование анкеты недоступно.')
        user_education = user_app.education.all()
        app_form = ApplicationCreateForm(request.POST,
                                         instance=user_app) if user_role == SLAVE_ROLE_NAME else ApplicationMasterForm(
            request.POST, instance=user_app)
        education_formset = EducationFormSet(request.POST, queryset=user_education)
        if app_form.is_valid() and education_formset.is_valid():
            new_app = app_form.save()
            user_app.education.all().delete()
            for form in education_formset:
                if form.cleaned_data:
                    user_education = form.save(commit=False)
                    user_education.application = new_app
                    user_education.save()
            return redirect('application', app_id=new_app.pk)
        else:
            msg = 'Некорректные данные в заявке'
        context = {'app_form': app_form, 'app_id': app_id, 'education_formset': education_formset, 'app_active': True,
                   'msg': msg}
        return render(request, 'application/application_edit.html', context=context)


class DocumentsInAppView(LoginRequiredMixin, View):
    @check_permission_decorator(MASTER_ROLE_NAME)
    def get(self, request, app_id):
        file_templates = File.objects.filter(is_template=True).all()
        app = Application.objects.filter(pk=app_id).first()
        user_files = File.objects.filter(member=app.member).all()
        context = {'file_templates': file_templates, 'user_files': user_files, 'document_active': True,
                   'app_id': app_id}
        return render(request, 'application/application_documents.html', context=context)

    @check_permission_decorator()
    def post(self, request, app_id):
        new_files = request.FILES.getlist('downloaded_files')
        for file in new_files:
            file_name = os.path.splitext(os.path.basename(file.name))[0]
            new_file = File(member=request.user.member, file_path=file, file_name=file_name, is_template=False)
            new_file.save()
        return redirect(request.path_info)


class CreateWordAppView(LoginRequiredMixin, View):
    @check_permission_decorator(MASTER_ROLE_NAME)
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        filename = f"Анкета_{user_app.member.user.last_name}.docx"
        word_template = WordTemplate(request, PATH_TO_INTERVIEW_LIST)
        context = word_template.create_context_to_interview_list(app_id)
        user_docx = word_template.create_word_in_buffer(context)
        response = HttpResponse(user_docx, content_type='application/docx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(filename) + '"'
        return response


class AddCompetencesView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    def post(self, request, direction_id):
        direction = Direction.objects.get(id=direction_id)
        chosen_competences = request.POST.getlist('chosen_competences')
        chosen_competences_id = [int(competence_id) for competence_id in chosen_competences]
        for competence_id in chosen_competences_id:
            pick_competence(competence_id, direction)
        return redirect(reverse('competence_list') + f'?direction={direction_id}')


class DeleteCompetenceView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    def get(self, request, competence_id, direction_id):
        master_direction_id = Affiliation.objects.filter(member=request.user.member).values_list('direction__id',
                                                                                                 flat=True)
        if direction_id not in master_direction_id:
            return PermissionDenied('Невозможно удалить компетенцию из чужого направления.')
        direction = Direction.objects.get(id=direction_id)
        delete_competence(competence_id, direction)
        return redirect(reverse('competence_list') + f'?direction={direction_id}')


class CreateCompetenceView(MasterDataMixin, CreateView):
    """ Показывает список всех компетенций. Создает новую компетенцию. """
    template_name = 'application/create_competence.html'
    form_class = CreateCompetenceForm
    success_url = reverse_lazy('create_competence')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'competence_active': True})
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'current_user': self.request.user})
        return kwargs


class ChooseCompetenceInAppView(LoginRequiredMixin, View):
    @check_permission_decorator(MASTER_ROLE_NAME)
    def get(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        context = {'competence_active': True, 'app_id': app_id}
        if user_app:
            if request.user.member.role.role_name == MASTER_ROLE_NAME or user_app.is_final:
                context.update({'blocked': True})
            user_directions = user_app.directions.all()
            if user_directions:
                user_competencies = ApplicationCompetencies.objects.filter(application=user_app)
                competencies = Competence.objects.filter(directions__in=user_directions,
                                                         parent_node__isnull=True).distinct()
                selected_competencies = {_.competence.id: _.level for _ in user_competencies}
                competence_levels = ApplicationCompetencies.competence_levels
                context.update({'levels': competence_levels, 'selected_competencies': selected_competencies,
                                'competencies': competencies, 'selected_directions': user_directions})
            else:
                context.update({'msg': 'Заполните направления', 'name': 'choose_app_direction'})
        else:
            context.update({'msg': 'Создайте заявку', 'name': 'create_application'})
        return render(request, 'application/application_competence_choose.html', context=context)

    @check_permission_decorator()
    def post(self, request, app_id):
        user_app = get_object_or_404(Application, pk=app_id)
        if user_app.is_final:
            return redirect(request.path_info)
        user_directions = user_app.directions.all()
        competence_direction_ids = [_.id for _ in Competence.objects.filter(directions__in=user_directions).distinct()]
        user_app.competencies.clear()
        for comp_id in competence_direction_ids:
            level_competence = int(request.POST.get(str(comp_id), 0))
            if level_competence and level_competence != 0:
                competence = Competence.objects.filter(pk=comp_id).first()
                ApplicationCompetencies.objects.create(application=user_app, competence=competence,
                                                       level=level_competence)
        user_app.save()
        user_competencies = ApplicationCompetencies.objects.filter(application=user_app)
        selected_competencies = {_.competence.id: _.level for _ in user_competencies}
        competencies = Competence.objects.filter(directions__in=user_directions, parent_node__isnull=True).distinct()

        context = {'competencies': competencies, 'levels': ApplicationCompetencies.competence_levels,
                   'selected_competencies': selected_competencies, 'app_id': app_id, 'competence_active': True,
                   'selected_directions': user_directions}
        return render(request, 'application/application_competence_choose.html', context=context)


class MasterFileTemplatesView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    def get(self, request):
        files = File.objects.filter(is_template=True).all()
        # показывает список уже загруженных файлов на сервер и позволяет загрузить новые
        return render(request, 'application/documents.html', context={'file_list': files})

    def post(self, request):
        new_files = request.FILES.getlist('downloaded_files')
        for file in new_files:
            new_file = File(member=request.user.member, file_path=file, is_template=True)
            new_file.save()
            new_file.file_name = new_file.file_path.name.split('/')[-1]  # отделяется название от пути загрузки
            new_file.save()
        return redirect(request.path_info)


class DeleteFileView(LoginRequiredMixin, View):
    def get(self, request, file_id):
        file = File.objects.get(id=file_id)
        if file.member != request.user.member:
            return PermissionDenied('Только загрузивший пользователь может удалить файл.')
        file.delete()
        request.user.member.application.save()
        return redirect(request.META.get('HTTP_REFERER'))


class ApplicationListView(MasterDataMixin, ListView):
    """
    Класс отображения списка заявок.

    Среди заявок предусмотрена сортировка по следующим параметрам: ФИО, город, итог. балл, заполненность
    Среди заявок предусмотрен следующий список фильтров:
    Направления заявки: список направлений заявки
    Отобран в: список принадлежностей мастера
    В избранном в: список принадлежностей мастера
    Сезон призыва (весна/осень)
    Год призыва

    Заявки отображаются по следующим правилам:
    Если человек подавал на одно из направлений отбирающего, то анкета этого человека показывается белым цветом, если
    не подавал - серым.
    Забронированные на направление отбирающего показываются зеленым цветом.
    """
    model = Application

    def get_queryset(self):
        apps = Application.objects.all()
        self.master_affiliations = self.get_master_affiliations()
        master_direction_id = self.master_affiliations.values_list('direction__id', flat=True)
        if self.request.GET:
            apps = get_filtered_sorted_queryset(apps, self.request)
        for app in apps:
            app.last_education = app.get_last_education()

            booking = Booking.objects.filter(slave=app.member, booking_type__name=BOOKED)
            if booking:
                app.is_booked = True  # данный человек в принципе забронирован
                app.affiliation = booking.first().affiliation
                if booking.filter(affiliation__in=self.master_affiliations):
                    app.is_booked_our = True
                    if booking.filter(affiliation__in=self.master_affiliations, master=self.request.user.member):
                        app.can_unbook = True

            in_wishlist = Booking.objects.filter(slave=app.member, booking_type__name=IN_WISHLIST)
            if in_wishlist:
                app.wishlist_len = len(in_wishlist)
                wishlist_affiliations = Booking.objects.filter(slave=app.member, booking_type__name=IN_WISHLIST,
                                                               affiliation__in=self.master_affiliations).values_list(
                    'affiliation',
                    flat=True)
                if wishlist_affiliations:
                    app.wishlist_affiliations = Affiliation.objects.filter(id__in=wishlist_affiliations)
                    app.is_in_wishlist = True  # данный человек находится в вишлисте мастера

            slave_directions = app.directions.all()
            available_directions = slave_directions.filter(id__in=master_direction_id)
            app.our_direction = True if available_directions else False
            app.available_affiliations = self.master_affiliations.filter(direction__in=slave_directions)
            app.note = get_application_note(self.request.user.member, self.master_affiliations, app)
        return apps

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        directions_set = [(aff.direction.id, aff.direction) for aff in self.master_affiliations]
        in_wishlist_set = [(affiliation.id, affiliation) for affiliation in self.master_affiliations]
        draft_year_set = Application.objects.order_by('draft_year').distinct().values_list('draft_year', 'draft_year')
        filter_form = FilterForm(self.request.GET, directions_set=directions_set, in_wishlist_set=in_wishlist_set,
                                 draft_year_set=draft_year_set, chosen_affiliation_set=in_wishlist_set)
        context['form'] = filter_form
        context['reset_filters'] = True if self.request.GET else False
        context['application_active'] = True
        return context


class CompetenceListView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    def get(self, request):
        context = get_context(self)
        return render(request, 'application/competence_list.html', context=context)

    def post(self, request):
        context = get_context(self)
        return render(request, 'application/competence_list.html', context=context)


class BookMemberView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    def post(self, request, app_id):
        affiliation_id = request.POST.get('affiliation', None)
        slave_member = Member.objects.get(application__id=app_id)
        booking_type = BookingType.objects.get(name=BOOKED)
        affiliation = Affiliation.objects.get(id=affiliation_id)
        Booking(booking_type=booking_type, master=request.user.member, slave=slave_member,
                affiliation=affiliation).save()
        return redirect('application_list')


class UnBookMemberView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    def post(self, request, app_id, aff_id):
        slave_member = Member.objects.get(application__id=app_id)
        booking = Booking.objects.filter(master=request.user.member, slave=slave_member, booking_type__name=BOOKED,
                                         affiliation__id=aff_id)
        if booking:
            booking.delete()
            return redirect('application_list')
        booking = Booking.objects.filter(slave=slave_member, booking_type__name=BOOKED,
                                         affiliation__id=aff_id).first()
        master_name = booking.master if booking else ""
        return render(request, 'access_error.html',
                      context={
                          'error': f'Отказано в запросе на удаление. Удалять может только {master_name}, отобравший '
                                   'кандидатуру.'})


class AddInWishlistView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    def post(self, request, app_id):
        affiliations_id = request.POST.getlist('affiliations', None)
        slave_member = Member.objects.get(application__id=app_id)
        booking_type = BookingType.objects.get(name=IN_WISHLIST)
        for affiliation_id in affiliations_id:
            affiliation = Affiliation.objects.get(id=affiliation_id)
            Booking(booking_type=booking_type, master=request.user.member, slave=slave_member,
                    affiliation=affiliation).save()
        return redirect('application_list')


class DeleteFromWishlistView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    def post(self, request, app_id):
        affiliations_id = request.POST.getlist('affiliations', None)
        slave_member = Member.objects.get(application__id=app_id)
        for affiliation_id in affiliations_id:
            current_booking = Booking.objects.filter(booking_type__name=IN_WISHLIST, master=request.user.member,
                                                     slave=slave_member, affiliation__id=affiliation_id)
            if current_booking:
                current_booking.first().delete()
        return redirect('application_list')


@login_required
def ajax_search_universities(request):
    result = []
    if request.is_ajax():
        term = request.GET.get('term', '')
        universities = Universities.objects.filter(name__icontains=term)
        result = [{'id': university.id,
                   'value': university.name,
                   'label': university.name} for university in universities]
        result = json.dumps(result)
    return HttpResponse(result)


class EditApplicationNote(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    def post(self, request, app_id):
        text = request.POST.get('note_text', '')
        master_affiliations = Affiliation.objects.filter(member=request.user.member)
        app_note = ApplicationNote.objects.filter(application=app_id, affiliations__in=master_affiliations,
                                                  author=request.user.member).distinct().first()
        if app_note:
            if text == '':
                app_note.delete()
            else:
                app_note.text = text
                app_note.affiliations.add(*list(master_affiliations))
                app_note.save()
        else:
            application = get_object_or_404(Application, pk=app_id)
            new_note = ApplicationNote(text=text, application=application, author=request.user.member)
            new_note.save()
            new_note.affiliations.add(*list(master_affiliations))
            new_note.save()
        return redirect('application', app_id=app_id)


class CompetenceAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        return Competence.objects.filter(name__istartswith=self.q) if self.q else Competence.objects.all()


class ChangeAppFinishedView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """ Обработка post запроса на блокирование редактирования анкеты пользователя"""

    def post(self, request, app_id):
        is_final = True if request.POST.get('is_final', None) == 'on' else False
        if check_booking_our(app_id=app_id, user=request.user):
            application = get_object_or_404(Application, pk=app_id)
            application.is_final = is_final
            application.save()
            return redirect('application', app_id=app_id)
        raise PermissionDenied('Данный пользователь не отобран на ваше направление.')


class CreateRatingListView(LoginRequiredMixin, View):
    def get(self, request):
        filename = "Рейтинговый список призыва.docx"
        word_template = WordTemplate(request, PATH_TO_RATING_LIST)
        context = word_template.create_context_to_rating_list()
        user_docx = word_template.create_word_in_buffer(context)
        response = HttpResponse(user_docx, content_type='application/docx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(filename) + '"'
        return response


class CreateCandidatesListView(LoginRequiredMixin, View):
    def get(self, request):
        filename = "Итоговый список кандидатов.docx"
        word_template = WordTemplate(request, PATH_TO_CANDIDATES_LIST)
        context = word_template.create_context_to_rating_list()
        user_docx = word_template.create_word_in_buffer(context)
        response = HttpResponse(user_docx, content_type='application/docx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(filename) + '"'
        return response
