import json
import os

from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, BadRequest
from django.db import transaction
from django.db.models import F, Q, Count, OuterRef, Subquery, Prefetch, Case, When, Value
from django.http import FileResponse
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.encoding import escape_uri_path
from django.views import View
from django.views.generic import CreateView, DetailView
from django.views.generic.list import ListView

from account.models import Member, Affiliation, Booking, BookingType
from application.forms import CreateCompetenceForm, FilterAppListForm, CreateWorkGroupForm, FilterWorkGroupForm, \
    ChooseWorkGroupForm
from engine.settings import MEDIA_DIR
from testing.models import TestResult, Test
from utils import constants as const
from utils.calculations import get_current_draft_year
from utils.exceptions import MasterHasNoDirectionsException
from .forms import ApplicationCreateForm, EducationFormSet, ApplicationMasterForm
from .mixins import OnlySlaveAccessMixin, OnlyMasterAccessMixin, MasterDataMixin, DataApplicationMixin
from .models import Direction, Application, Education, Competence, ApplicationCompetencies, File, ApplicationNote, \
    Universities, AdditionFieldApp, AdditionField, Specialization, MilitaryCommissariat, WorkGroup
from .utils import check_permission_decorator, WordTemplate, check_booking_our_or_exception, check_final_decorator, \
    add_additional_fields, get_cleared_query_string_of_page, get_sorted_queryset


class ChooseDirectionInAppView(DataApplicationMixin, LoginRequiredMixin, View):
    """ Показывает список имеющихся направлений. Сохраняет список выбранных направлений в заявке. """

    @check_permission_decorator(const.MASTER_ROLE_NAME)
    def get(self, request, pk):
        user_app = get_object_or_404(Application.objects.only('is_final'), pk=pk)
        selected_directions = [_.id for _ in user_app.directions.all()]
        context = {'direction_active': True, 'pk': pk, 'directions': self.get_all_directions(),
                   'selected_directions': selected_directions}
        if request.user.member.is_master() or user_app.is_final:
            context.update({'blocked': True})
        return render(request, 'application/application_direction_choose.html', context=context)

    @check_final_decorator
    @check_permission_decorator()
    def post(self, request, pk):
        user_app = get_object_or_404(Application, pk=pk)
        selected_directions = request.POST.getlist('direction')
        context = {}
        if len(selected_directions) <= const.MAX_APP_DIRECTIONS:
            if selected_directions:
                directions = Direction.objects.filter(pk__in=selected_directions)
                user_app.directions.set(list(directions))
            else:
                user_app.directions.clear()
            user_app.update_scores(update_fields=['fullness', 'final_score'])
        else:
            selected_directions = [_.id for _ in user_app.directions.all()]
            context['error_msg'] = 'Выбранное количество направлений должно быть не больше 4'
        context.update(
            {'directions': self.get_all_directions(), 'selected_directions': list(map(int, selected_directions)),
             'direction_active': True, 'pk': pk})
        return render(request, 'application/application_direction_choose.html', context=context)


class CreateApplicationView(LoginRequiredMixin, OnlySlaveAccessMixin, View):
    """ Показывает создание новой заявки пользователя """

    def get(self, request):
        user_app = Application.objects.filter(member=request.user.member).first()
        if user_app:
            return redirect('application', pk=user_app.id)
        app_form = ApplicationCreateForm()
        education_formset = EducationFormSet(queryset=Education.objects.none())
        additional_fields = AdditionField.objects.all()
        context = {'app_form': app_form, 'app_active': True, 'education_formset': education_formset,
                   'additional_fields': additional_fields, 'user_additional_fields': {}}
        return render(request, 'application/application_create.html', context=context)

    def post(self, request):
        app_form = ApplicationCreateForm(request.POST)
        education_formset = EducationFormSet(request.POST)
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
                new_app.update_scores(update_fields=['fullness', 'final_score'])
                add_additional_fields(request, new_app)
                return redirect('application', pk=new_app.pk)
            else:
                context = {'app_active': True, 'msg': 'Некорректные данные в заявке', 'app_form': app_form,
                           'education_formset': education_formset}
                return render(request, 'application/application_create.html', context=context, status=400)
        else:
            return redirect('application', pk=Application.objects.filter(member=request.user.member).first().id)


class ApplicationView(LoginRequiredMixin, DataApplicationMixin, View):
    """ Показывает заявку пользователя в режиме просмотра """

    @check_permission_decorator(const.MASTER_ROLE_NAME)
    def get(self, request, pk):
        context = {}
        user_application = self.get_user_application(pk)
        user_education = user_application.education.order_by('end_year').all()
        context['master_directions_affiliations'] = self.get_master_direction_affiliations(
            self.get_master_affiliations())
        context['master_affiliations'] = self.get_master_affiliations()
        context.update(
            {'app': user_application, 'pk': user_application.id, 'user_education': user_education, 'app_active': True})
        return render(request, 'application/application_detail.html', context=context)

    def get_user_application(self, pk):
        wishlist_affiliations = Booking.objects.filter(affiliation__in=self.get_master_affiliations(),
                                                       booking_type__name=const.IN_WISHLIST).select_related(
            'affiliation').only('affiliation', 'slave')

        booked_member_affiliation = Booking.objects.filter(slave=OuterRef('member'), booking_type__name=const.BOOKED)
        app = Application.objects.filter(pk=pk).select_related('member', 'member__user').prefetch_related(
            Prefetch('member__candidate', queryset=wishlist_affiliations),
            Prefetch('directions', queryset=self.get_master_directions().only('id'), to_attr='aval_dir'),
        ).only('id', 'member', 'directions', 'birth_day', 'birth_place', 'draft_year', 'draft_season', 'final_score',
               'fullness', 'member__user__id', 'member__user__first_name', 'member__user__last_name',
               'member__father_name').annotate(
            is_booked=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.BOOKED),
                distinct=True
            ),
            company=Subquery(booked_member_affiliation.values('affiliation__company')),
            platoon=Subquery(booked_member_affiliation.values('affiliation__platoon')),
            booked_id=Subquery(booked_member_affiliation.values('affiliation__id')),
            is_booked_our=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.BOOKED,
                         member__candidate__affiliation__in=self.get_master_affiliations()),
                distinct=True
            ),
            can_unbook=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.BOOKED,
                         member__candidate__affiliation__in=self.get_master_affiliations(),
                         member__candidate__master=self.request.user.member),
                distinct=True
            ),
            wishlist_len=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.IN_WISHLIST),
                distinct=True
            ),
            is_in_wishlist=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.IN_WISHLIST,
                         member__candidate__affiliation__in=self.get_master_affiliations()),
                distinct=True
            ),
            our_direction_count=Count(
                F('directions'),
                filter=Q(directions__id__in=self.get_master_directions_id()),
                distinct=True
            ),
            our_direction=Case(
                When(our_direction_count__gt=0, then=Value(True)),
                default=Value(False),
            ),
        ).first()
        return app


class EditApplicationView(LoginRequiredMixin, View):
    """ Показывает форму для редактирования заявки. Сохраняет отредактированную заявку. """

    @check_permission_decorator(const.MASTER_ROLE_NAME)
    def get(self, request, pk):
        user_app = get_object_or_404(Application, pk=pk)
        if user_app.is_final and request.user.member.is_slave():
            raise PermissionDenied('Редактирование анкеты недоступно.')
        user_education = user_app.education.order_by('end_year').all()
        app_form = ApplicationCreateForm(
            instance=user_app) if request.user.member.is_slave() else ApplicationMasterForm(instance=user_app)
        education_formset = EducationFormSet(queryset=user_education)
        additional_fields = AdditionField.objects.all()
        user_additional_fields = {f.addition_field_id: f.value for f in
                                  AdditionFieldApp.objects.filter(application=user_app)}
        context = {'app_form': app_form, 'pk': pk, 'education_formset': education_formset, 'app_active': True,
                   'additional_fields': additional_fields, 'user_additional_fields': user_additional_fields}
        return render(request, 'application/application_edit.html', context=context)

    @check_permission_decorator(const.MASTER_ROLE_NAME)
    def post(self, request, pk):
        user_app = get_object_or_404(Application, pk=pk)
        if user_app.is_final and request.user.member.is_slave():
            raise PermissionDenied('Редактирование анкеты недоступно.')
        user_education = user_app.education.all()
        app_form = ApplicationCreateForm(request.POST, instance=user_app) if request.user.member.is_slave() \
            else ApplicationMasterForm(request.POST, instance=user_app)
        education_formset = EducationFormSet(request.POST, queryset=user_education)
        if app_form.is_valid() and education_formset.is_valid():
            new_app = app_form.save()
            user_app.education.all().delete()
            for form in education_formset:
                if form.cleaned_data:
                    user_education = form.save(commit=False)
                    user_education.application = new_app
                    user_education.save()
            new_app.update_scores(update_fields=['fullness', 'final_score'])
            add_additional_fields(request, user_app)
            return redirect('application', pk=new_app.pk)
        else:
            context = {'app_form': app_form, 'pk': pk, 'education_formset': education_formset, 'app_active': True,
                       'msg': 'Некорректные данные в заявке'}
            return render(request, 'application/application_edit.html', context=context, status=400)


class DocumentsInAppView(LoginRequiredMixin, View):
    """ Показывает список загруженных файлов и имеюищхся шаблонов. Сохраняет загруженные файлы в заявке """

    @check_permission_decorator(const.MASTER_ROLE_NAME)
    def get(self, request, pk):
        file_templates = File.objects.filter(is_template=True).all()
        app = get_object_or_404(Application, pk=pk)
        user_files = File.objects.filter(member=app.member).all()
        context = {'file_templates': file_templates, 'user_files': user_files, 'document_active': True, 'pk': pk}
        if request.user.member.is_master():
            context.update({'blocked': True})
        return render(request, 'application/application_documents.html', context=context)

    @check_permission_decorator()
    def post(self, request, pk):
        new_files = request.FILES.getlist('downloaded_files')
        for file in new_files:
            file_name = os.path.basename(file.name)
            new_file = File(member=request.user.member, file_path=file, file_name=file_name, is_template=False)
            new_file.save()
        return redirect(request.path_info)


class CreateWordAppView(LoginRequiredMixin, View):
    """ Генерирует анкету в формате docx на основе заявки """

    @check_permission_decorator(const.MASTER_ROLE_NAME)
    def get(self, request, pk):
        user_app = get_object_or_404(Application.objects.only('member'), pk=pk)
        filename = f"Анкета_{user_app.member.user.last_name}.docx"
        word_template = WordTemplate(request, const.PATH_TO_INTERVIEW_LIST)
        context = word_template.create_context_to_interview_list(pk)
        user_docx = word_template.create_word_in_buffer(context)
        response = HttpResponse(user_docx, content_type='application/docx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(filename) + '"'
        return response


class AddCompetencesView(MasterDataMixin, View):
    """Добавляет все выбранные компетенции в направление, id которого = direction_id"""

    def post(self, request, direction_id):
        chosen_competences = request.POST.getlist('chosen_competences')
        with transaction.atomic():
            for competence in Competence.objects.filter(id__in=chosen_competences).only('id'):
                competence.directions.add(direction_id)
        return redirect(reverse('competence_list') + f'?direction={direction_id}')


class DeleteCompetenceView(MasterDataMixin, View):
    """Рекурсивно удаляет компетенцию с competence_id и все ее дочерние из направления с direction_id"""

    def get(self, request, competence_id, direction_id):
        if direction_id not in self.get_master_directions_id():
            raise PermissionDenied('Невозможно удалить компетенцию из чужого направления.')
        self.delete_competence(competence_id, direction_id)
        return redirect(reverse('competence_list') + f'?direction={direction_id}')

    def delete_competence(self, competence_id, direction_id):
        """Todo: перевести на mptt и сделать get_descendants(include_self=False)"""
        competence = Competence.objects.prefetch_related(
            Prefetch('directions', queryset=Direction.objects.filter(id=direction_id)),
            Prefetch('child__directions', queryset=Direction.objects.filter(id=direction_id)),
            Prefetch('child__child__directions', queryset=Direction.objects.filter(id=direction_id)),
        ).get(id=competence_id)
        all_competences = []
        if competence.directions.all().exists():
            all_competences.append(competence)
        for comp in competence.child.all():
            if comp.directions.all().exists():
                all_competences.append(comp)
            for comp2 in comp.child.all():
                if comp2.directions.all().exists():
                    all_competences.append(comp2)
        with transaction.atomic():
            for comp in all_competences:
                comp.directions.remove(direction_id)


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
    """ Показывает список имеющихся компетенций по выбранным направлениям.
    Сохраняет список выбранных компетенций и их уровень в заявке. """

    @check_permission_decorator(const.MASTER_ROLE_NAME)
    def get(self, request, pk):
        user_app = get_object_or_404(Application, pk=pk)
        context = {'competence_active': True, 'pk': pk}
        if request.user.member.is_master() or user_app.is_final:
            context.update({'blocked': True})
        user_directions = user_app.directions.all()
        if user_directions:
            user_competencies = ApplicationCompetencies.objects.select_related('competence').filter(
                application=user_app)
            selected_competencies = {_.competence.id: _.level for _ in user_competencies}
            competencies = Competence.objects.filter(parent_node__isnull=True,
                                                     directions__in=user_directions).prefetch_related('child',
                                                                                                      'child__child',
                                                                                                      'directions').distinct()
            competence_levels = ApplicationCompetencies.competence_levels
            context.update({'levels': competence_levels, 'selected_competencies': selected_competencies,
                            'competencies': competencies, 'selected_directions': user_directions})
        else:
            msg = 'Направления не выбраны' if request.user.member.is_master() else 'Заполните направления'
            context.update({'msg': msg, 'name': 'choose_app_direction'})
        return render(request, 'application/application_competence_choose.html', context=context)

    @check_final_decorator
    @check_permission_decorator()
    def post(self, request, pk):
        user_app = get_object_or_404(Application, pk=pk)
        user_directions = user_app.directions.all()
        competencies_of_direction = Competence.objects.filter(directions__in=user_directions).distinct()
        level_competence = [ApplicationCompetencies(application=user_app,
                                                    competence=competence,
                                                    level=request.POST.get(str(competence.id), 0))
                            for competence in competencies_of_direction]
        ApplicationCompetencies.objects.filter(application=user_app, competence__in=competencies_of_direction).delete()
        ApplicationCompetencies.objects.bulk_create(level_competence)

        user_app.update_scores(update_fields=['fullness', 'final_score'])
        user_competencies = ApplicationCompetencies.objects.select_related('competence').filter(application=user_app)
        selected_competencies = {_.competence.id: _.level for _ in user_competencies}
        competencies = Competence.objects.filter(parent_node__isnull=True,
                                                 directions__in=user_directions).prefetch_related('child',
                                                                                                  'child__child',
                                                                                                  'directions').distinct()

        context = {'competencies': competencies, 'levels': ApplicationCompetencies.competence_levels,
                   'selected_competencies': selected_competencies, 'pk': pk, 'competence_active': True,
                   'selected_directions': user_directions}
        return render(request, 'application/application_competence_choose.html', context=context)


class MasterFileTemplatesView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """Показывает список уже загруженных файлов на сервер и позволяет загрузить новые"""

    def get(self, request):
        files = File.objects.filter(is_template=True).all().only('file_path', 'file_name', 'is_template')
        return render(request, 'application/documents.html', context={'file_list': files, 'document_active': True})

    def post(self, request):
        new_files = request.FILES.getlist('downloaded_files')
        for file in new_files:
            file_name = os.path.basename(file.name)
            new_file = File(member=request.user.member, file_path=file, is_template=True, file_name=file_name)
            new_file.save()
        return redirect(request.path_info)


class DeleteFileView(LoginRequiredMixin, View):
    """Удаляет файл по file_id"""

    def get(self, request, file_id):
        file = File.objects.get(id=file_id)
        if file.member != request.user.member:
            raise PermissionDenied('Только загрузивший пользователь может удалить файл.')
        os.remove(os.path.join(MEDIA_DIR, str(file.file_path)))
        file.delete()
        if request.user.member.is_slave():
            request.user.member.application.update_scores(update_fields=['fullness', 'final_score'])
        return redirect(request.META.get('HTTP_REFERER'))


class DownloadFileView(LoginRequiredMixin, View):
    """ Скачивает файлы по file_id """

    def get(self, request, file_id):
        file = get_object_or_404(File, pk=file_id)
        member = request.user.member
        if member.is_slave() and member != file.member and not file.is_template:
            raise PermissionDenied('Недостаточно прав для скачивания файла')
        file_path = os.path.join(MEDIA_DIR, str(file.file_path))
        response = FileResponse(open(file_path, 'rb'), filename=file.file_name, as_attachment=True)
        return response


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
    paginate_by = 50

    def get_queryset(self):
        wishlist_affiliations = Booking.objects.filter(affiliation__in=self.get_master_affiliations(),
                                                       booking_type__name=const.IN_WISHLIST).select_related(
            'affiliation').only('affiliation', 'slave')

        booked_member_affiliation = Booking.objects.filter(slave=OuterRef('member'), booking_type__name=const.BOOKED)
        apps = Application.objects.all().select_related('member', 'member__user').prefetch_related(
            Prefetch('member__candidate', queryset=wishlist_affiliations),
            Prefetch('directions', queryset=self.get_master_directions().only('id'), to_attr='aval_dir'),
        ).only('id', 'member', 'directions', 'birth_day', 'birth_place', 'draft_year', 'draft_season', 'final_score',
               'fullness', 'member__user__id', 'member__user__first_name', 'member__user__last_name',
               'member__father_name')
        apps = self.get_filtered_sorted_queryset(apps)
        apps = apps.annotate(
            is_booked=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.BOOKED),
                distinct=True
            ),
            company=Subquery(booked_member_affiliation.values('affiliation__company')),
            platoon=Subquery(booked_member_affiliation.values('affiliation__platoon')),
            booked_id=Subquery(booked_member_affiliation.values('affiliation__id')),
            is_booked_our=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.BOOKED,
                         member__candidate__affiliation__in=self.get_master_affiliations()),
                distinct=True
            ),
            can_unbook=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.BOOKED,
                         member__candidate__affiliation__in=self.get_master_affiliations(),
                         member__candidate__master=self.request.user.member),
                distinct=True
            ),
            wishlist_len=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.IN_WISHLIST),
                distinct=True
            ),
            is_in_wishlist=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.IN_WISHLIST,
                         member__candidate__affiliation__in=self.get_master_affiliations()),
                distinct=True
            ),
            university=Subquery(Education.objects.filter(application=OuterRef('pk')).order_by('-end_year').values(
                'university')[:1]),
            avg_score=Subquery(Education.objects.filter(application=OuterRef('pk')).order_by('-end_year').values(
                'avg_score')[:1]),
            education_type=Subquery(Education.objects.filter(application=OuterRef('pk')).order_by('-end_year').values(
                'education_type')[:1]),
            our_direction_count=Count(
                F('directions'),
                filter=Q(directions__id__in=self.get_master_directions_id()),
                distinct=True
            ),
            our_direction=Case(
                When(our_direction_count__gt=0, then=Value(True)),
                default=Value(False),
            ),
            author_note=Subquery(
                ApplicationNote.objects.filter(application=OuterRef('pk'), author=self.request.user.member,
                                               affiliations__in=self.get_master_affiliations(),
                                               ).values('text')[:1]),
            note=Subquery(
                ApplicationNote.objects.filter(application=OuterRef('pk'),
                                               affiliations__in=self.get_master_affiliations(),
                                               ).values('text')[:1]),
        )
        apps = get_sorted_queryset(apps, self.request.GET.get('ordering', None))
        return apps

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        master_affiliations = self.get_master_affiliations().select_related('direction').defer('direction__description',
                                                                                               'direction__image')
        current_year, current_season = get_current_draft_year()
        initial = {'draft_year': current_year,
                   'draft_season': current_season,
                   }
        data = self.request.GET if self.request.GET else None
        context['form'] = FilterAppListForm(initial=initial, data=data, master_affiliations=master_affiliations)
        context['reset_filters'] = bool(self.request.GET)
        context['application_active'] = True
        context['master_affiliations'] = master_affiliations
        context['master_directions_affiliations'] = self.get_master_direction_affiliations(master_affiliations)
        context['cleaned_query_string'] = get_cleared_query_string_of_page(self.request.META['QUERY_STRING'])
        return context

    def get_filtered_sorted_queryset(self, apps):
        """Возвращает отфильтрованный  список анкет. Если в self.request.GET пусто, то
        фильтрует по текущему году и сезону призыва"""
        args = dict(self.request.GET)
        if args:
            args.pop('page', None)
        if not args:
            current_year, current_season = get_current_draft_year()
            return apps.filter(draft_year=current_year, draft_season=current_season[0]).distinct()
        # тут производится вся сортировка и фильтрация
        # фильтрация по направлениям
        chosen_directions = self.request.GET.getlist('directions', None)
        if chosen_directions:
            apps = apps.filter(directions__in=chosen_directions).distinct()

        # фильтрация по бронированию
        chosen_affiliation = self.request.GET.getlist('affiliation', None)
        if chosen_affiliation:
            booked_members = Booking.objects.filter(affiliation__in=chosen_affiliation,
                                                    booking_type__name=const.BOOKED).values_list('slave', flat=True)
            apps = apps.filter(member__id__in=booked_members).distinct()

        # фильтрация по вишлисту
        chosen_affiliation_wishlist = self.request.GET.getlist('in_wishlist', None)
        if chosen_affiliation_wishlist:
            booked_members = Booking.objects.filter(affiliation__in=chosen_affiliation_wishlist,
                                                    booking_type__name=const.IN_WISHLIST).values_list('slave',
                                                                                                      flat=True)
            apps = apps.filter(member__id__in=booked_members).distinct()

        # фильтрация по сезону
        draft_season = self.request.GET.getlist('draft_season', None)
        if draft_season:
            apps = apps.filter(draft_season__in=draft_season).distinct()

        # фильтрация по году призыва
        draft_year = self.request.GET.getlist('draft_year', None)
        if draft_year:
            apps = apps.filter(draft_year__in=draft_year).distinct()
        return apps


class CompetenceListView(MasterDataMixin, View):
    def get(self, request):
        """Показывает список выбранных компетенций и невыбранных компетенций для данного направления"""
        chosen_direction = self.get_chosen_direction()
        if chosen_direction is None:
            raise MasterHasNoDirectionsException(
                'У вас нет ни одного направления, по которому вы можете осуществлять отбор.')
        competences_list, picking_competences = self.get_competences_lists(self.get_root_competences(),
                                                                           chosen_direction)
        picked_competences = Competence.objects.alias(
            picked=Count(F'directions', filter=Q(directions=chosen_direction))
        ).filter(picked__gt=0)
        context = {'competences_list': competences_list, 'picked_competences': picked_competences,
                   'picking_competences': picking_competences,
                   'selected_direction': chosen_direction, 'directions': self.get_master_directions(),
                   'competence_active': True}
        return render(request, 'application/competence_list.html', context=context)

    def get_chosen_direction(self):
        """Возвращает выбранное направление, если оно было получено через GET, первое направление,
         закрепленное за пользователем или None, если первых двух нет"""
        selected_direction_id = self.request.GET.get('direction')
        if selected_direction_id:
            return Direction.objects.get(id=int(selected_direction_id))
        return self.get_first_master_direction_or_exception()

    def get_competences_lists(self, roots, selected_direction):
        """
        Возвращает кортеж листов доступных корневых компетенций для выбора и уже выбранных
        :param roots: Корни всех компетенций
        :param selected_direction: Выбранное направлени
        :return: кортеж <корни всех выбранных компетенций> <корни всех доступных компетенций>
        """
        if selected_direction is None:
            return [], roots
        exsist_coms = roots.filter(parent_node__isnull=True).alias(
            lvl1=Count(F('directions'), filter=Q(directions=selected_direction), distinct=True),
            lvl2=Count(F('child'), filter=Q(child__directions=selected_direction), distinct=True),
            lvl3=Count(F('child__child'), filter=Q(child__child__directions=selected_direction), distinct=True),
            lvl2all=Count(F('child'), distinct=True),
            lvl3all=Count(F('child__child'), distinct=True),
        ).annotate(exist_competences=F('lvl1') + F('lvl2') + F('lvl3'),
                   not_exist_competences=F('lvl2all') - F('lvl2') + F('lvl3all') - F('lvl3') + 1 - F('lvl1'),
                   ).prefetch_related('child', 'child__child')
        chosen_competences_list = exsist_coms.filter(exist_competences__gt=0)
        for_pick_competences_list = exsist_coms.filter(not_exist_competences__gt=0)
        return chosen_competences_list, for_pick_competences_list


class BookMemberView(MasterDataMixin, View):
    """Бронирует анкету с id=pk текущим пользователем на направление, полученное из post"""

    def post(self, request, pk):
        affiliation_id = request.POST.get('affiliation', None)
        slave_member = get_object_or_404(Member.objects.only('id'), application__id=pk)
        booking_type = BookingType.objects.only('id').get(name=const.BOOKED)
        affiliation = get_object_or_404(Affiliation.objects.select_related('direction').only('id', 'direction_id'),
                                        id=affiliation_id)
        slave_directions_id = Member.objects.prefetch_related(
            'application__directions__id').only('application__directions__id').values_list(
            'application__directions__id', flat=True).distinct().filter(application__id=pk)

        if not Booking.objects.filter(booking_type=booking_type, slave=slave_member).exists() \
                and affiliation.direction_id in self.get_master_directions_id() \
                and affiliation.direction_id in slave_directions_id:
            Booking(booking_type=booking_type, master=request.user.member, slave=slave_member,
                    affiliation=affiliation).save()
        else:
            raise PermissionDenied('Бронирование на неверное направление.')
        return self.get_redirect_on_previous_page(request)


class UnBookMemberView(MasterDataMixin, View):
    """Удаляет из бронирования анкету с id=pk текущим пользователем с направления id=aff_id"""

    def post(self, request, pk, aff_id):
        slave_member = get_object_or_404(Member.objects.select_related('application__work_group'), application__id=pk)
        booking = Booking.objects.filter(master=request.user.member, slave=slave_member,
                                         booking_type__name=const.BOOKED,
                                         affiliation__id=aff_id)
        if booking:
            if slave_member.application.work_group:
                slave_member.application.work_group = None
                slave_member.application.save(update_fields=["work_group"])
            booking.delete()
            return self.get_redirect_on_previous_page(request)
        booking = Booking.objects.filter(slave=slave_member, booking_type__name=const.BOOKED,
                                         affiliation__id=aff_id).first()
        master_name = booking.master if booking else ""
        raise PermissionDenied(f'Отказано в запросе на удаление. Удалять может только {master_name}, отобравший '
                               'кандидатуру.')


class AddInWishlistView(MasterDataMixin, View):
    """Добавляет в список желания на направления, полученные из post заявку с id=pk"""

    def post(self, request, pk):
        affiliations_id = list(map(int, request.POST.getlist('affiliations', None)))
        self.check_master_has_affiliation(affiliations_id,
                                          "Невозможно добавить заявку в избранное на чужое направление.")
        slave_member = Member.objects.get(application__id=pk)
        booking_type = BookingType.objects.get(name=const.IN_WISHLIST)
        for affiliation_id in affiliations_id:
            affiliation = Affiliation.objects.get(id=affiliation_id)
            if not Booking.objects.filter(booking_type=booking_type, slave=slave_member,
                                          affiliation=affiliation).exists():
                Booking(booking_type=booking_type, master=request.user.member, slave=slave_member,
                        affiliation=affiliation).save()
        return self.get_redirect_on_previous_page(request)


class DeleteFromWishlistView(MasterDataMixin, View):
    """Удаляет из списка желаемых заявку с id=pk с направлений, полученных с post"""

    def post(self, request, pk):
        affiliations_id = request.POST.getlist('affiliations', None)
        slave_member = Member.objects.get(application__id=pk)
        for affiliation_id in affiliations_id:
            current_booking = Booking.objects.filter(booking_type__name=const.IN_WISHLIST, master=request.user.member,
                                                     slave=slave_member, affiliation__id=affiliation_id)
            if current_booking:
                current_booking.first().delete()
        return self.get_redirect_on_previous_page(request)


@login_required
def ajax_search_info_in_db_tables(request):
    term = request.GET.get('term', '')
    db_table_name = {
        'universities': Universities,
        'specialization': Specialization,
        'commissariat': MilitaryCommissariat,
    }
    db_table = db_table_name[request.path.split('/')[-2]]
    filtered_table = db_table.objects.filter(name__icontains=term)
    result = [{'id': record.id,
               'value': record.name,
               'label': record.name} for record in filtered_table]
    return HttpResponse(json.dumps(result))


class EditApplicationNote(MasterDataMixin, View):

    def post(self, request, pk):
        """
        Редактирует существующую заметку и добавляет к ней список взводов автора.
        Удаляет заметку, если она пустая и создает новую, если заметка отсутствует
        """
        text = request.POST.get('note_text', '')
        master_affiliations = self.get_master_affiliations()
        app_note = ApplicationNote.objects.filter(application=pk, affiliations__in=master_affiliations,
                                                  author=request.user.member).distinct().first()
        if app_note:
            if text == '':
                app_note.delete()
            else:
                app_note.text = text
                app_note.affiliations.add(*list(master_affiliations))
                app_note.save()
        else:
            application = get_object_or_404(Application, pk=pk)
            new_note = ApplicationNote(text=text, application=application, author=request.user.member)
            new_note.save()
            new_note.affiliations.add(*list(master_affiliations))
            new_note.save()
        return redirect('application', pk=pk)


class CompetenceAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Показывает список компетенций, которые подходят по шаблону (автодополнение)
    query params:
        q: string - строка шаблон, по которой фильтруются компетенции
    """

    def get_queryset(self):
        return Competence.objects.filter(name__istartswith=self.q) if self.q else Competence.objects.all()


class ChangeAppFinishedView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """ Обработка post запроса на блокирование редактирования анкеты пользователя"""

    def post(self, request, pk):
        """Меняет поле is_final анкеты с id=pk в зависимости от переключателя is_final"""
        is_final = request.POST.get('is_final', None) == 'on'
        check_booking_our_or_exception(pk=pk, user=request.user)
        application = get_object_or_404(Application, pk=pk)
        application.is_final = is_final
        application.save()
        return redirect('application', pk=pk)


class CreateServiceDocumentView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """
    Генерирует служебные файлы формата docx на основе отобранных анкет
    query params:
        doc: string - обозначает какой из файлов необходимо сгенерировать
            candidates - для итогового списка кандидатов
            rating - для рейтингового списка призыва
            evaluation-statement - для итогового списка кандидатов
        directions: True/False - делать выборку по всем направлениям/по направлениям закрепленными за пользователем
    """

    def get(self, request):
        service_document = request.GET.get('doc', '')
        all_directions = bool(request.GET.get('directions', None))
        path_to_file, filename = const.TYPE_SERVICE_DOCUMENT.get(service_document, (None, None))
        if path_to_file:
            word_template = WordTemplate(request, path_to_file)
            context = word_template.create_context_to_word_files(path_to_file, all_directions)
            user_docx = word_template.create_word_in_buffer(context)
            response = HttpResponse(user_docx, content_type='application/docx')
            response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(filename) + '"'
            return response
        raise BadRequest('Плохой query параметр')


class WorkGroupsListView(MasterDataMixin, CreateView):
    """ Показывает список всех рабочих групп. Создает новую рабочую группу. """
    template_name = 'application/create_work_group.html'
    form_class = CreateWorkGroupForm
    success_url = reverse_lazy('work_group_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        affiliations_with_groups = self.get_master_affiliations(). \
            prefetch_related('work_group')
        context.update({'work_groups_active': True, 'affiliations_with_groups': affiliations_with_groups})
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        master_affiliations = self.get_master_affiliations()
        if not master_affiliations:
            raise MasterHasNoDirectionsException(
                'У вас нет ни одного направления, по которому вы можете осуществлять отбор.')
        kwargs.update({'master_affiliations': master_affiliations})
        return kwargs


class DeleteWorkGroupView(MasterDataMixin, View):

    def get(self, request, group_id):
        """Удаляет рабочую группу с group_id"""
        group = get_object_or_404(WorkGroup, pk=group_id)
        self.check_master_has_affiliation(group.affiliation.id,
                                          'Невозможно удалить чужую рабочую группу.')
        group.delete()
        return redirect('work_group_list')


class WorkGroupView(MasterDataMixin, DetailView):
    """ Показывает рабочую группу"""
    model = WorkGroup
    template_name = 'application/work_group_detail.html'

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        current_year, current_season = get_current_draft_year()
        group = get_object_or_404(WorkGroup.objects.prefetch_related(
            Prefetch('application', queryset=Application.objects.filter(draft_year=current_year,
                                                                        draft_season=current_season[0]))),
            pk=pk)
        self.check_master_has_affiliation(group.affiliation.id,
                                          'Данная рабочая группа не принадлежит вашим направлениям!')
        return group


class RemoveApplicationWorkGroupView(MasterDataMixin, View):
    def get(self, request, app_id, group_id):
        """Удаляет заявку с app_id из рабочей группы с group_id"""
        group = get_object_or_404(WorkGroup, pk=group_id)
        application = get_object_or_404(Application, pk=app_id)
        self.check_master_has_affiliation(group.affiliation.id,
                                          'Данная рабочая группа не принадлежит вашим направлениям!')
        if application.work_group:
            application.work_group = None
            application.save(update_fields=['work_group'])
        return self.get_redirect_on_previous_page(request)


class WorkingListView(MasterDataMixin, ListView):
    """
    Показывает список заявок по одному из направлений мастера.
    В таблице показываются все компетенции кандидатов, сгруппированные по уровню владению.
    Также показываются результаты тестов.
    Каждого забронированного кандидата можно добавить в рабочую группу
    Фильтр сбоку: забронированные, в избранном, выбранное направление
    """
    model = Application
    template_name = 'application/working_list.html'

    def get_queryset(self):
        self.chosen_affiliation_id = self.get_chosen_affiliation_id()
        chosen_direction = Direction.objects.get(affiliation__id=self.chosen_affiliation_id)
        wishlist_affiliations = Booking.objects.filter(affiliation__in=self.get_master_affiliations(),
                                                       booking_type__name=const.IN_WISHLIST).select_related(
            'affiliation').only('affiliation', 'slave')

        booked_member_affiliation = Booking.objects.filter(slave=OuterRef('member'),
                                                           booking_type__name=const.BOOKED)
        apps = Application.objects.all().select_related('member', 'member__user', 'work_group').prefetch_related(
            Prefetch('member__candidate', queryset=wishlist_affiliations),
            Prefetch('directions', queryset=self.get_master_directions().only('id'), to_attr='aval_dir'),
            Prefetch('app_competence',
                     queryset=ApplicationCompetencies.objects.filter(
                         competence__directions=chosen_direction, level__in=[1, 2, 3]).select_related('competence')),
            Prefetch('member__test_result',
                     queryset=TestResult.objects.filter(test__directions=chosen_direction,
                                                        status=TestResult.test_statuses[2][0]).select_related('test'),
                     to_attr='test_results')
        ).only('id', 'member', 'directions', 'birth_day', 'birth_place', 'draft_year', 'draft_season',
               'final_score', 'work_group',
               'fullness', 'member__user__id', 'member__user__first_name', 'member__user__last_name',
               'member__father_name')
        apps = self.get_filtered_sorted_queryset(apps, self.chosen_affiliation_id)
        apps = apps.annotate(
            is_booked=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.BOOKED),
                distinct=True
            ),
            company=Subquery(booked_member_affiliation.values('affiliation__company')),
            platoon=Subquery(booked_member_affiliation.values('affiliation__platoon')),
            booked_id=Subquery(booked_member_affiliation.values('affiliation__id')),
            is_booked_our=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.BOOKED,
                         member__candidate__affiliation__in=self.get_master_affiliations()),
                distinct=True
            ),
            can_unbook=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.BOOKED,
                         member__candidate__affiliation__in=self.get_master_affiliations(),
                         member__candidate__master=self.request.user.member),
                distinct=True
            ),
            wishlist_len=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.IN_WISHLIST),
                distinct=True
            ),
            our_direction_count=Count(
                F('directions'),
                filter=Q(directions__id__in=self.get_master_directions_id()),
                distinct=True
            ),
            our_direction=Case(
                When(our_direction_count__gt=0, then=Value(True)),
                default=Value(False),
            ),
            is_in_wishlist=Count(
                F('member__candidate'),
                filter=Q(member__candidate__booking_type__name=const.IN_WISHLIST,
                         member__candidate__affiliation__in=self.get_master_affiliations()),
                distinct=True
            ),
            author_note=Subquery(
                ApplicationNote.objects.filter(application=OuterRef('pk'), author=self.request.user.member,
                                               affiliations__in=self.get_master_affiliations(),
                                               ).values('text')[:1]),
            note=Subquery(
                ApplicationNote.objects.filter(application=OuterRef('pk'),
                                               affiliations__in=self.get_master_affiliations(),
                                               ).values('text')[:1]),
        )

        return apps

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booked_type_id = BookingType.objects.only('id').get(name=const.BOOKED)
        master_affiliations = self.get_master_affiliations().select_related('direction').defer('direction__description',
                                                                                               'direction__image')
        initial = {'affiliation': self.get_first_master_affiliation_or_exception(),
                   'booking_type': booked_type_id.id,
                   }
        data = self.request.GET if self.request.GET else None
        affiliation_set = [(affiliation.id, affiliation) for affiliation in master_affiliations]
        filter_form = FilterWorkGroupForm(initial=initial, data=data, affiliation_set=affiliation_set)
        group_set = WorkGroup.objects.filter(affiliation__id=self.chosen_affiliation_id)
        work_group_select = ChooseWorkGroupForm(group_set=group_set)
        context['group_form'] = work_group_select
        context['form'] = filter_form
        context['reset_filters'] = bool(self.request.GET)
        context['work_list_active'] = True
        context['master_directions_affiliations'] = self.get_master_direction_affiliations(master_affiliations)
        chosen_affiliation = get_object_or_404(Affiliation.objects.select_related('direction'),
                                               pk=self.chosen_affiliation_id)
        context['chosen_company'] = chosen_affiliation.company
        context['chosen_platoon'] = chosen_affiliation.platoon
        context['direction_tests'] = Test.objects.filter(directions=chosen_affiliation.direction)
        return context

    def get_chosen_affiliation_id(self):
        """Возвращает выбранную принадлежность из get или первую принадлежность мастера"""
        chosen_competence = self.request.GET.get('affiliation', None)
        return chosen_competence if chosen_competence else self.get_first_master_affiliation_or_exception().id

    def get_filtered_sorted_queryset(self, apps, chosen_affiliation_id):
        """
        Возвращает отфильтрованный и отсортированный список анкет.
        Если в self.request.GET пусто, то фильтрует по первой принадлежности, забронированным участникам, текущему году.
        :param apps: queryset заявок
        :param chosen_affiliation_id: id выбранной принадлежности
        :return: отфильтрованный queryset
        """
        booked_members = Booking.objects.filter(affiliation__id=chosen_affiliation_id,
                                                booking_type__name=const.BOOKED).values_list('slave', flat=True)
        if not self.request.GET:
            current_year, current_season = get_current_draft_year()
            return apps.filter(draft_year=current_year, draft_season=current_season[0],
                               directions__affiliation__id=chosen_affiliation_id,
                               member__id__in=booked_members).distinct()

        # тут производится вся сортировка и фильтрация
        # фильтрация по принадлежностям
        chosen_affiliation = self.request.GET.get('affiliation', None)
        apps = apps.filter(directions__affiliation__id=chosen_affiliation)
        booking_type_id = self.request.GET.getlist('booking_type', None)
        if not booking_type_id or 'all' in booking_type_id:
            return apps
        booked_members = Booking.objects.filter(affiliation__in=chosen_affiliation,
                                                booking_type__id__in=booking_type_id).values_list('slave', flat=True)
        return apps.filter(member__id__in=booked_members)


class ChangeWorkGroupView(MasterDataMixin, View):
    """Используется для смены рабочей группы у заявки."""

    def post(self, request, app_id):
        """Меняет рабочую группу в заявке с id=app_id на отправленную в форме. Редиректит на предыдущую страницу"""
        check_booking_our_or_exception(app_id, request.user)
        application = get_object_or_404(Application, pk=app_id)
        group_id = request.POST.get('work_group', None)
        if group_id:
            group = get_object_or_404(WorkGroup, pk=group_id)
            self.check_master_has_affiliation(group.affiliation.id,
                                              'Данная рабочая группа не принадлежит вашим направлениям!')

            booking_type_booked = BookingType.objects.only('id').get(name=const.BOOKED)
            if not Booking.objects.filter(booking_type=booking_type_booked, slave=application.member,
                                          affiliation=group.affiliation).exists():
                raise PermissionDenied('Невозможно назначить данному кандидату рабочую группу другого взвода!')
        work_group_select = ChooseWorkGroupForm(data=request.POST, instance=application)
        if work_group_select.is_valid():
            work_group_select.save()
        return self.get_redirect_on_previous_page(request)
