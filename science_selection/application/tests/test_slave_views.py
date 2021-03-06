import datetime
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from account.models import Role, Member
from application.models import Direction, Education, Application, AdditionField, Competence, ApplicationCompetencies, \
    Universities, MilitaryCommissariat, Specialization
from utils.constants import SLAVE_ROLE_NAME, MASTER_ROLE_NAME


class CreateApplicationViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        AdditionField.objects.create(name='Тестовое поле')

    def setUp(self) -> None:
        self.user_master = User.objects.create_user(username='admin', password='admin', is_superuser=True)
        self.user_officer = User.objects.create_user(username='officer', password='officer')
        officer_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        Member.objects.create(user=self.user_officer, role=officer_role, phone='89998881111')
        self.user = User.objects.create(username='test_user', password='test_user')
        self.user.set_password('test_user')
        self.user.save()
        Member.objects.create(user=self.user, role=slave_role, phone='1111111111')
        self.form_data = {
            'birth_day': '10.10.2000',
            'birth_place': 'Тест',
            'nationality': 'РФ',
            'military_commissariat': 'Йо',
            'group_of_health': 'А1',
            'draft_year': datetime.datetime.today().year,
            'draft_season': 1,
        }
        self.education_form_data = {
            'form-0-university': 'МЭИ',
            'form-0-specialization': 'ИВТ',
            'form-0-avg_score': 5,
            'form-0-end_year': 2019,
            'form-0-theme_of_diploma': 'БД',
            'form-0-name_of_education_doc': 'Вышка',
            'form-0-is_ended': True,
            'form-0-education_type': 'b',
        }

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('create_application'))
        self.assertRedirects(resp, '/accounts/login/?next=/app/application/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('create_application'))
        self.assertEqual(str(resp.context['user']), 'test_user')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'application/application_create.html')

    def test_master_access(self):
        """ Проверяет, что у постоянного состава нет доступа к странице  """
        self.client.login(username='officer', password='officer')
        resp = self.client.get(reverse('create_application'))
        self.assertEqual(resp.status_code, 403)

    def test_create_app_when_exists(self):
        """ Проверяет, что пользователь уже имеет созданную заявку """
        member = Member.objects.get(user=self.user)
        app = Application.objects.create(member=member, birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                         birth_place=f'Test', nationality='РФ',
                                         military_commissariat='Йо',
                                         group_of_health='А1', draft_year='2021', draft_season=1)
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('create_application'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application', kwargs={'pk': app.id}))

    def test_context(self):
        """ Проверяет контекст страницы """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('create_application'))
        self.assertTrue(resp.context['app_active'])
        ad_fields = AdditionField.objects.all()
        self.assertEqual(list(resp.context['additional_fields']), list(ad_fields))

    def test_create_app(self):
        """ Проверяет корректное создание заявки без образования """
        self.client.login(username='test_user', password='test_user')
        self.form_data.update({
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0
        })
        resp = self.client.post(reverse('create_application'), data=self.form_data)
        self.assertEqual(resp.status_code, 302)

    def test_invalid_birth_date(self):
        """ Проверяет, что при создании заявки валидируются данные формы """
        self.client.login(username='test_user', password='test_user')
        self.form_data.update({
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'draft_year': datetime.datetime.today().year - 1,
        })
        resp = self.client.post(reverse('create_application'), data=self.form_data)
        self.assertEqual(resp.status_code, 400)

    def test_main_required_fields(self):
        """ Проверяет, что при создании заявки есть обязательные поля """
        self.client.login(username='test_user', password='test_user')
        new_data = self.form_data.copy()
        for key, v in self.form_data.items():
            new_data.pop(key)
            new_data.update({
                'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': 0,
            })
            resp = self.client.post(reverse('create_application'), data=new_data)
            self.assertEqual(resp.status_code, 400)

    def test_create_app_with_education(self):
        """ Проверяет корректное создание заявки с образованием """
        self.client.login(username='test_user', password='test_user')
        self.education_form_data.update({
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
        })
        resp = self.client.post(reverse('create_application'), data={**self.form_data, **self.education_form_data})
        self.assertEqual(resp.status_code, 302)

    def test_education_invalid_data(self):
        """ Проверяет, что при создании заявки с образованием валидируются поля """
        self.client.login(username='test_user', password='test_user')
        self.education_form_data.update({
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-0-avg_score': 5.1,
            'form-0-education_type': 't'
        })
        resp = self.client.post(reverse('create_application'), data={**self.form_data, **self.education_form_data})
        self.assertEqual(resp.status_code, 400)

    def test_education_required_fields(self):
        """ Проверяет, что при создании заявки с образованием есть обязательные поля """
        self.client.login(username='test_user', password='test_user')
        new_data = self.education_form_data.copy()
        for key, v in self.education_form_data.items():
            if key not in ['form-0-name_of_education_doc', 'form-0-avg_score', 'form-0-is_ended']:
                new_data.pop(key)
                new_data.update({
                    'form-TOTAL_FORMS': 2,
                    'form-INITIAL_FORMS': 0,
                })
                resp = self.client.post(reverse('create_application'), data={**self.form_data, **new_data})
                self.assertEqual(resp.status_code, 400)


class ApplicationViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        AdditionField.objects.create(name='Тестовое поле')

    def setUp(self) -> None:
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        self.user = User.objects.create(username='test_user', password='test_user')
        self.user.set_password('test_user')
        self.user.save()
        member = Member.objects.create(user=self.user, role=slave_role, phone='1111111111')
        self.form_data = {
            'birth_day': datetime.datetime.strptime('18/09/19', '%d/%m/%y').date(),
            'birth_place': 'Тест',
            'nationality': 'РФ',
            'military_commissariat': 'Йо',
            'group_of_health': 'А1',
            'draft_year': datetime.datetime.today().year,
            'draft_season': 1,
        }
        self.education_form_data = {
            'university': 'МЭИ',
            'specialization': 'ИВТ',
            'avg_score': 5.0,
            'end_year': 2019,
            'theme_of_diploma': 'БД',
            'name_of_education_doc': 'Вышка',
            'is_ended': True,
            'education_type': 'b',
        }
        self.app = Application.objects.create(member=member, **self.form_data)
        Education.objects.create(application=self.app, **self.education_form_data)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('application', kwargs={'pk': self.app.id}))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/application/{self.app.id}/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('application', kwargs={'pk': self.app.id}))
        self.assertEqual(str(resp.context['user']), 'test_user')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'application/application_detail.html')

    def test_context(self):
        """ Проверяет контекст просмотра созданной заявки """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('application', kwargs={'pk': self.app.id}))
        user_app = resp.context['app'].__dict__
        for k, v in self.form_data.items():
            self.assertEqual(user_app[k], v)
        user_ed = resp.context['user_education'].values()[0]
        user_ed.pop('id')
        user_ed.pop('application_id')
        self.assertEqual(user_ed, self.education_form_data)
        self.assertTrue(resp.context['app_active'])


class EditApplicationViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        AdditionField.objects.create(name='Тестовое поле')

    def setUp(self) -> None:
        self.user_master = User.objects.create_user(username='admin', password='admin', is_superuser=True)
        self.user_officer = User.objects.create_user(username='officer', password='officer')
        officer_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        Member.objects.create(user=self.user_officer, role=officer_role, phone='89998881111')
        self.user = User.objects.create(username='test_user', password='test_user')
        self.user.set_password('test_user')
        self.user.save()
        member = Member.objects.create(user=self.user, role=slave_role, phone='1111111111')
        self.form_data = {
            'birth_day': datetime.datetime.strptime('18/09/19', '%d/%m/%y').date(),
            'birth_place': 'Тест',
            'nationality': 'РФ',
            'military_commissariat': 'Йо',
            'group_of_health': 'А1',
            'draft_year': datetime.datetime.today().year,
            'draft_season': 1,
        }
        self.new_form_data = {
            'birth_place': 'Тест2',
            'nationality': 'РФ2',
            'military_commissariat': 'Йо2',
            'group_of_health': 'А2',
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
        }
        self.app = Application.objects.create(member=member, **self.form_data)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('edit_application', kwargs={'pk': self.app.id}))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/application/{self.app.id}/edit/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('edit_application', kwargs={'pk': self.app.id}))
        self.assertEqual(str(resp.context['user']), 'test_user')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'application/application_edit.html')

    def test_get_context(self):
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('edit_application', kwargs={'pk': self.app.id}))
        self.assertEqual(resp.status_code, 200)

        self.client.login(username='officer', password='officer')
        resp = self.client.get(reverse('edit_application', kwargs={'pk': self.app.id}))
        self.assertEqual(resp.status_code, 200)

    def test_get_is_final_app(self):
        """ Проверяет, что закрытии заявки, пользователь не сможет ее редактировать """
        Application.objects.filter(id=self.app.id).update(is_final=True)
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('edit_application', kwargs={'pk': self.app.id}))
        self.assertEqual(resp.status_code, 403)

    def test_update_app(self):
        """ Проверяка на обновление полей заявки """
        self.form_data.update(self.new_form_data)
        self.client.login(username='test_user', password='test_user')
        resp = self.client.post(reverse('edit_application', kwargs={'pk': self.app.id}), data=self.form_data)
        self.assertEqual(resp.status_code, 302)
        resp = self.client.get(reverse('application', kwargs={'pk': self.app.id}))
        user_app = resp.context['app'].__dict__
        for k, v in self.form_data.items():
            if k not in ['form-TOTAL_FORMS', 'form-INITIAL_FORMS']:
                self.assertEqual(user_app[k], v)


class ChooseDirectionInAppViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        AdditionField.objects.create(name='Тестовое поле')

    def setUp(self) -> None:
        self.user_master = User.objects.create_user(username='admin', password='admin', is_superuser=True)
        self.user_officer = User.objects.create_user(username='officer', password='officer')
        officer_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        Member.objects.create(user=self.user_officer, role=officer_role, phone='89998881111')
        self.user = User.objects.create(username='test_user', password='test_user')
        self.user.set_password('test_user')
        self.user.save()
        member = Member.objects.create(user=self.user, role=slave_role, phone='1111111111')
        self.form_data = {
            'birth_day': datetime.datetime.strptime('18/09/19', '%d/%m/%y').date(),
            'birth_place': 'Тест',
            'nationality': 'РФ',
            'military_commissariat': 'Йо',
            'group_of_health': 'А1',
            'draft_year': datetime.datetime.today().year,
            'draft_season': 1,
        }
        self.app = Application.objects.create(member=member, **self.form_data)
        for i in range(3):
            direction = Direction.objects.create(name=f'test{i}')
            self.app.directions.add(direction)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('choose_app_direction', kwargs={'pk': self.app.id}))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/application/{self.app.id}/direction/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('choose_app_direction', kwargs={'pk': self.app.id}))
        self.assertEqual(str(resp.context['user']), 'test_user')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'application/application_direction_choose.html')

    def test_without_app(self):
        """ Проверяет, что нет возможности выбрать направления без созданной заявки """
        app_id = self.app.id
        self.app.delete()
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('choose_app_direction', kwargs={'pk': app_id}))
        self.assertEqual(resp.status_code, 403)

    def test_master_permission(self):
        """ Проверка на блокирование направлений для постоянного состава """
        self.client.login(username='officer', password='officer')
        resp = self.client.get(reverse('choose_app_direction', kwargs={'pk': self.app.id}))
        self.assertTrue(resp.context['blocked'])

    def test_direction_context(self):
        """ Проверяет, что выбранные направления появляются в контексте """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('choose_app_direction', kwargs={'pk': self.app.id}))
        directions = Direction.objects.all()
        self.assertEqual(list(resp.context['selected_directions']), [d.id for d in directions])

    def test_update_directions(self):
        """ Проверяка на обновление списка выбранных компетенций """
        first_direction = Direction.objects.get(pk=1)
        self.client.login(username='test_user', password='test_user')
        resp = self.client.post(reverse('choose_app_direction', kwargs={'pk': self.app.id}),
                                data={'direction': [first_direction.id]})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context['selected_directions']), [first_direction.id])

    def test_max_selected_directions(self):
        """ Проверяет, что максимальное количество компетенций <= 4 """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.post(reverse('choose_app_direction', kwargs={'pk': self.app.id}),
                                data={'direction': [1, 2, 3, 4, 5]})
        self.assertEqual(resp.context['error_msg'], 'Выбранное количество направлений должно быть не больше 4')

    def test_update_directions_with_officer_permission(self):
        """ Проверяет, что постоянный состав не может обновлять направления в заявке """
        self.client.login(username='officer', password='officer')
        resp = self.client.post(reverse('choose_app_direction', kwargs={'pk': self.app.id}),
                                data={'direction': [1]})
        self.assertEqual(resp.status_code, 403)


class ChooseCompetenceInAppViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        AdditionField.objects.create(name='Тестовое поле')

    def setUp(self) -> None:
        self.user_master = User.objects.create_user(username='admin', password='admin', is_superuser=True)
        self.user_officer = User.objects.create_user(username='officer', password='officer')
        officer_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        Member.objects.create(user=self.user_officer, role=officer_role, phone='89998881111')
        self.user = User.objects.create(username='test_user', password='test_user')
        self.user.set_password('test_user')
        self.user.save()
        member = Member.objects.create(user=self.user, role=slave_role, phone='1111111111')
        self.form_data = {
            'birth_day': datetime.datetime.strptime('18/09/19', '%d/%m/%y').date(),
            'birth_place': 'Тест',
            'nationality': 'РФ',
            'military_commissariat': 'Йо',
            'group_of_health': 'А1',
            'draft_year': datetime.datetime.today().year,
            'draft_season': 1,
        }
        self.app = Application.objects.create(member=member, **self.form_data)
        for i in range(3):
            direction = Direction.objects.create(name=f'test{i}', )
            self.app.directions.add(direction)
            comp1 = Competence.objects.create(name=f'parent comp {i}')
            comp1.directions.add(direction)
            comp2 = Competence.objects.create(parent_node=comp1, name=f'comp {i}', is_estimated=True)
            comp2.directions.add(direction)
            ApplicationCompetencies.objects.create(application=self.app, competence=comp2, level=i)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('choose_app_competence', kwargs={'pk': self.app.id}))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/application/{self.app.id}/competence/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('choose_app_competence', kwargs={'pk': self.app.id}))
        self.assertEqual(str(resp.context['user']), 'test_user')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'application/application_competence_choose.html')

    def test_without_app(self):
        """ Проверяет, что нет возможности выбрать компетенции без созданной заявки """
        app_id = self.app.id
        self.app.delete()
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('choose_app_competence', kwargs={'pk': app_id}))
        self.assertEqual(resp.status_code, 403)

    def test_master_permission(self):
        """ Проверка на блокирование компетенций для постоянного состава """
        self.client.login(username='officer', password='officer')
        resp = self.client.get(reverse('choose_app_competence', kwargs={'pk': self.app.id}))
        self.assertTrue(resp.context['blocked'])

    def test_without_directions(self):
        """ Проверка на вывод ошибки при выборе компетенций без выбранных направлений """
        self.app.directions.clear()
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('choose_app_competence', kwargs={'pk': self.app.id}))
        self.assertEqual(resp.context['msg'], 'Заполните направления')

    def test_update_competencies(self):
        """ Проверка на корректное обновлений компетенций """
        comp2 = Competence.objects.get(name='comp 1')
        self.client.login(username='test_user', password='test_user')
        resp = self.client.post(reverse('choose_app_competence', kwargs={'pk': self.app.id}),
                                data={str(comp2.id): int(3)})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['selected_competencies'][comp2.id], 3)

    def test_update_competencies_with_officer_permission(self):
        """ Проверяет, что постоянный состав не может обновлять компетенции в заявке """
        self.client.login(username='officer', password='officer')
        resp = self.client.post(reverse('choose_app_competence', kwargs={'pk': self.app.id}),
                                data={'1': 3})
        self.assertEqual(resp.status_code, 403)


class DocumentsInAppViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        AdditionField.objects.create(name='Тестовое поле')

    def setUp(self) -> None:
        self.user_master = User.objects.create_user(username='admin', password='admin', is_superuser=True)
        self.user_officer = User.objects.create_user(username='officer', password='officer')
        officer_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        Member.objects.create(user=self.user_officer, role=officer_role, phone='89998881111')
        self.user = User.objects.create(username='test_user', password='test_user')
        self.user.set_password('test_user')
        self.user.save()
        member = Member.objects.create(user=self.user, role=slave_role, phone='1111111111')
        self.form_data = {
            'birth_day': datetime.datetime.strptime('18/09/19', '%d/%m/%y').date(),
            'birth_place': 'Тест',
            'nationality': 'РФ',
            'military_commissariat': 'Йо',
            'group_of_health': 'А1',
            'draft_year': datetime.datetime.today().year,
            'draft_season': 1,
        }
        self.app = Application.objects.create(member=member, **self.form_data)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('app_documents', kwargs={'pk': self.app.id}))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/application/{self.app.id}/documents/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('app_documents', kwargs={'pk': self.app.id}))
        self.assertEqual(str(resp.context['user']), 'test_user')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'application/application_documents.html')

    def test_master_permission(self):
        """ Проверка на блокирование вложений для постоянного состава """
        self.client.login(username='officer', password='officer')
        resp = self.client.get(reverse('app_documents', kwargs={'pk': self.app.id}))
        self.assertTrue(resp.context['blocked'])

    def test_add_files_without_permission(self):
        """ Проверяет, что постоянный состав не может добавлять вложения к заявке """
        self.client.login(username='officer', password='officer')
        resp = self.client.post(reverse('app_documents', kwargs={'pk': self.app.id}), data={'downloaded_files': b'asd'})
        self.assertEqual(resp.status_code, 403)


class CreateWordAppViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        AdditionField.objects.create(name='Тестовое поле')

    def setUp(self) -> None:
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        self.user = User.objects.create(username='test_user', password='test_user')
        self.user.set_password('test_user')
        self.user.save()
        member = Member.objects.create(user=self.user, role=slave_role, phone='1111111111')
        self.form_data = {
            'birth_day': datetime.datetime.strptime('18/09/19', '%d/%m/%y').date(),
            'birth_place': 'Тест',
            'nationality': 'РФ',
            'military_commissariat': 'Йо',
            'group_of_health': 'А1',
            'draft_year': datetime.datetime.today().year,
            'draft_season': 1,
        }
        self.app = Application.objects.create(member=member, **self.form_data)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('create_word_app', kwargs={'pk': self.app.id}))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/application/{self.app.id}/word/')

    def test_without_app(self):
        """ Проверяет, что нет возможности создать word документ-анкету без созданной заявки """
        app_id = self.app.id
        self.app.delete()
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('create_word_app', kwargs={'pk': app_id}))
        self.assertEqual(resp.status_code, 403)

    def test_create_file(self):
        """ Проверяет, что создается word документ-анкета для выбранной заявки """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('create_word_app', kwargs={'pk': self.app.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers['Content-Type'], 'application/docx')
        self.assertIsNotNone(resp.content)


class CreateServiceDocumentViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        AdditionField.objects.create(name='Тестовое поле')

    def setUp(self) -> None:
        self.user_officer = User.objects.create_user(username='officer', password='officer')
        officer_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        Member.objects.create(user=self.user_officer, role=officer_role, phone='89998881111')
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        self.user = User.objects.create(username='test_user', password='test_user')
        self.user.set_password('test_user')
        self.user.save()
        member = Member.objects.create(user=self.user, role=slave_role, phone='1111111111')
        self.form_data = {
            'birth_day': datetime.datetime.strptime('18/09/19', '%d/%m/%y').date(),
            'birth_place': 'Тест',
            'nationality': 'РФ',
            'military_commissariat': 'Йо',
            'group_of_health': 'А1',
            'draft_year': datetime.datetime.today().year,
            'draft_season': 1,
        }
        self.app = Application.objects.create(member=member, **self.form_data)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('create_word_service_document', ))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/application/list/service-document/')

    def test_bad_query_params(self):
        """ Проверяет, что значение query параметра не подходит """
        self.client.login(username='officer', password='officer')
        resp = self.client.get(reverse('create_word_service_document') + '?doc=test')
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get(reverse('create_word_service_document') + '?docs=rating&directions=t')
        self.assertEqual(resp.status_code, 400)

    def test_not_exists(self):
        """ Проверяет, что не существует такой страницы """
        self.client.login(username='officer', password='officer')
        resp = self.client.get(reverse('create_word_service_document') + 'd=test')
        self.assertEqual(resp.status_code, 404)

    def test_create_files(self):
        """ Проверяет, что успешно создаются файлы """
        self.client.login(username='officer', password='officer')
        for query in ['candidates', 'rating', 'evaluation-statement']:
            resp = self.client.get(reverse('create_word_service_document') + '?doc=' + query)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers['Content-Type'], 'application/docx')
            self.assertIsNotNone(resp.content)

    def test_slave_access(self):
        """ Проверка, что обычный пользователь не имеет доступа к созданию документов """
        self.client.login(username='test_user', password='test_user')
        for query in ['candidates', 'rating', 'evaluation-statement']:
            resp = self.client.get(reverse('create_word_service_document') + '?doc=' + query)
            self.assertEqual(resp.status_code, 403)


class CompetenceAutocompleteTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Competence.objects.create(name='Информатика')
        Competence.objects.create(name='Информатика и вычислительная техника')
        Competence.objects.create(name='Техническое зрение')
        Competence.objects.create(name='Радиофизика')

    def setUp(self) -> None:
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        self.user = User.objects.create(username='test_user', password='test_user')
        self.user.set_password('test_user')
        self.user.save()
        Member.objects.create(user=self.user, role=slave_role, phone='1111111111')

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('search_competencies', ))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/search/competencies/')

    def test_correct_autocomplete(self):
        """ Проверка, что корректно выполняется автокомплит """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('search_competencies') + '?q=Ин')
        self.assertEqual(resp.status_code, 200)
        result = {res['selected_text'] for res in json.loads(resp.content)['results']}
        self.assertEqual(result - {'Информатика', 'Информатика и вычислительная техника'}, set())

    def test_incorrect_query_param(self):
        """ Проверка, что при неправильном query не будет выполняться запрос """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('create_word_service_document') + '?term=Ин')
        self.assertEqual(resp.status_code, 403)


class AjaxSearchInfoInDbTablesTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Universities.objects.create(name='НИУ "МЭИ"')
        Universities.objects.create(name='МГУ')
        Universities.objects.create(name='НИУ "МФТИ"')
        Specialization.objects.create(name='Информатика и вычислительная техника')
        Specialization.objects.create(name='Информационные технологии')
        Specialization.objects.create(name='Медицина')
        MilitaryCommissariat.objects.create(name='Военный комиссариат РМЭ', subject='Республика Марий Эл', city='Йо')
        MilitaryCommissariat.objects.create(name='Военный комиссариат Татарстана', subject='Республика Татарстан',
                                            city='Казань')
        MilitaryCommissariat.objects.create(name='Военный комиссариат г.Москвы', subject='г.Москва', city='г.Москва')
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        user = User.objects.create(username='test_user', password='test_user')
        user.set_password('test_user')
        user.save()
        Member.objects.create(user=user, role=slave_role, phone='1111111111')

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('ajax_search_universities', ))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/search/universities/')

    def test_ajax_uni(self):
        """ Проверят правильность автодополнения из списка университетов по шаблону """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('ajax_search_universities') + '?term=НИУ')
        result = {row['value'] for row in json.loads(resp.content)}
        self.assertEqual(result - {'НИУ "МЭИ"', 'НИУ "МФТИ"'}, set())

    def test_ajax_military_commissariat(self):
        """ Проверят правильность автодополнения из списка военных комиссариатов по шаблону """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('ajax_search_commissariat') + '?term=Моск')
        result = {row['value'] for row in json.loads(resp.content)}
        self.assertEqual(result - {'Военный комиссариат г.Москвы'}, set())

    def test_ajax_specialization(self):
        """ Проверят правильность автодополнения из списка специальностей по шаблону """
        self.client.login(username='test_user', password='test_user')
        resp = self.client.get(reverse('ajax_search_specialization') + '?term=Инф')
        result = {row['value'] for row in json.loads(resp.content)}
        self.assertEqual(result - {'Информатика и вычислительная техника', 'Информационные технологии'}, set())
