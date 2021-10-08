import datetime

from django.test import TestCase

from application.models import Direction, Competence, Education, Application
from application.forms import CreateCompetenceForm, EducationCreateForm, ApplicationMasterForm


class CreateCompetenceFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        direction = Direction.objects.create(name='ИВТ', description='программирование и роботы')
        competence = Competence.objects.create(name='ЯП')
        competence.directions.set([direction])

    def setUp(self) -> None:
        self.form_data = {
            'name': 'Python',
            'directions': [1],
            'parent_node': 1
        }

    def test_directions_not_exists(self):
        self.form_data['directions'] = [99]
        form = CreateCompetenceForm(data=self.form_data)
        self.assertFalse(form.is_valid())

    def test_parent_node_not_exists(self):
        self.form_data['parent_node'] = 99
        form = CreateCompetenceForm(data=self.form_data)
        self.assertFalse(form.is_valid())

    def test_valid_data(self):
        form = CreateCompetenceForm(data=self.form_data)
        self.assertTrue(form.is_valid())


class EducationCreateFormTest(TestCase):

    def setUp(self) -> None:
        self.form_data = {
            'university': 'МЭИ',
            'specialization': 'ИВТ',
            'avg_score': 4.5,
            'end_year': 2020,
            'theme_of_diploma': 'БД',
            'name_of_education_doc': 'Документ о высшем образовании',
            'is_ended': True,
            'education_type': 'b',
        }

    def test_education_type_not_exists(self):
        self.form_data['education_type'] = 'baccalaureate'
        form = EducationCreateForm(data=self.form_data)
        self.assertFalse(form.is_valid())

    def test_high_avg_score(self):
        self.form_data['avg_score'] = 5.5
        form = EducationCreateForm(data=self.form_data)
        self.assertFalse(form.is_valid())

    def test_low_avg_score(self):
        self.form_data['avg_score'] = 1.9
        form = EducationCreateForm(data=self.form_data)
        self.assertFalse(form.is_valid())

    def test_required_fields(self):
        for field, value in self.form_data.items():
            if field not in ['name_of_education_doc', 'avg_score', 'is_ended']:
                new_form = self.form_data.copy()
                new_form.pop(field)
                form = EducationCreateForm(data=new_form)
                self.assertFalse(form.is_valid())

    def test_valid_data(self):
        for program in Education.education_program:
            self.form_data['education_type'] = program[0]
            form = EducationCreateForm(data=self.form_data)
            self.assertTrue(form.is_valid())


class ApplicationMasterFormTest(TestCase):

    def setUp(self) -> None:
        self.form_data = {
            'birth_day': datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
            'birth_place': 'ЙО',
            'nationality': 'РФ',
            'military_commissariat': 'ВК ЙО',
            'group_of_health': 'A1',
            'draft_year': datetime.datetime.today().year,
            'draft_season': 1,
        }

    def test_validate_birth_day_template(self):
        self.form_data['birth_day'] = '22-09-2003'
        form = ApplicationMasterForm(data=self.form_data)
        self.assertFalse(form.is_valid())

        self.form_data['birth_day'] = '22 09 2003'
        form = ApplicationMasterForm(data=self.form_data)
        self.assertFalse(form.is_valid())

    def test_max_value_birth_day(self):
        self.form_data['birth_day'] = datetime.datetime.today() + datetime.timedelta(days=1)
        form = ApplicationMasterForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['birth_day'][0].message, 'Дата рождения не может быть больше текущей')

    def test_min_value_draft_year(self):
        self.form_data['draft_year'] = self.form_data['draft_year'] - 1
        form = ApplicationMasterForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['draft_year'][0].message,
                         ApplicationMasterForm.declared_fields['draft_year'].error_messages['min_value'])

    def test_valid_draft_year(self):
        self.form_data['draft_year'] = self.form_data['draft_year'] + 1
        form = ApplicationMasterForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        for field, value in self.form_data.items():
            new_form = self.form_data.copy()
            new_form.pop(field)
            form = ApplicationMasterForm(data=new_form)
            self.assertFalse(form.is_valid())

    def test_valid_data(self):
        for season in Application.season:
            self.form_data['draft_season'] = season[0]
            form = ApplicationMasterForm(data=self.form_data)
            self.assertTrue(form.is_valid())
