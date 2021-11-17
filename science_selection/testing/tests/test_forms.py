from django.contrib.auth.models import User
from django.test import TestCase

from account.models import Member, Role
from application.models import Direction
from testing.forms import TestCreateForm, QuestionForm, AnswerForm
from testing.models import TypeOfTest, Test, Question
from utils.constants import MASTER_ROLE_NAME


class TestCreateFormTest(TestCase):

    def setUp(self) -> None:
        type1 = TypeOfTest.objects.create(name='Type1')
        self.direction1 = Direction.objects.create(name='Направление1', description='desc')
        self.direction2 = Direction.objects.create(name='Направление2', description='desc2')
        self.form_data = {
            'name': 'Test1',
            'time_limit': 10,
            'description': 'Help text',
            'type': type1,
            'directions': [self.direction1, self.direction2]
        }

    def test_time_limit_min_value(self):
        """ Проверка минимального значения лимита времени """
        self.form_data['time_limit'] = -20
        form = TestCreateForm(data=self.form_data, directions=[self.direction1.pk])
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['time_limit'][0].message, "Значение времени не может быть меньше 1 минуты")

    def test_clean_directions(self):
        """ Проверка выбора незакрепленных направлений за пользователем """
        form = TestCreateForm(data=self.form_data, directions=[self.direction1.pk])
        self.assertFalse(form.is_valid())

    def test_valid_data(self):
        form = TestCreateForm(data=self.form_data, directions=[self.direction1.pk, self.direction2.pk])
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        """ Проверка обязательных параметров формы """
        for field, value in self.form_data.items():
            if field in ['description', 'directions']:
                continue
            new_form = self.form_data.copy()
            new_form.pop(field)
            form = TestCreateForm(data=new_form, directions=[self.direction1.pk, self.direction2.pk])
            self.assertFalse(form.is_valid())


class TestQuestionFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        master_role = Role.objects.create(role_name=MASTER_ROLE_NAME)
        master = User.objects.create_user(username=f'master', password='master')
        Member.objects.create(user=master, role=master_role, phone='89998887766')

    def setUp(self) -> None:
        type1 = TypeOfTest.objects.create(name='Type1')
        direction1 = Direction.objects.create(name='Направление1', description='desc')
        direction2 = Direction.objects.create(name='Направление2', description='desc2')
        master = User.objects.get(username='master')
        member = Member.objects.get(user=master)
        self.form_data = {
            'wording': 'Test1',
            'question_type': Question.type_of_question[0][0],
            'image': None,
        }
        test = Test.objects.create(name='Test1', time_limit=10, description='Help text', type=type1, creator=member)
        test.directions.set([direction1, direction2])

    def test_valid_data(self):
        form = QuestionForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        """ Проверка обязательных параметров формы """
        for field, value in self.form_data.items():
            if field in ['image']:
                continue
            new_form = self.form_data.copy()
            new_form.pop(field)
            form = QuestionForm(data=new_form,)
            self.assertFalse(form.is_valid())


class AnswerFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        master_role = Role.objects.create(role_name=MASTER_ROLE_NAME)
        master = User.objects.create_user(username=f'master', password='master')
        Member.objects.create(user=master, role=master_role, phone='89998887766')

    def setUp(self) -> None:
        type1 = TypeOfTest.objects.create(name='Type1')
        direction1 = Direction.objects.create(name='Направление1', description='desc')
        direction2 = Direction.objects.create(name='Направление2', description='desc2')
        master = User.objects.get(username='master')
        member = Member.objects.get(user=master)
        test = Test.objects.create(name='Test1', time_limit=10, description='Help text', type=type1, creator=member)
        test.directions.set([direction1, direction2])
        Question.objects.create(test=test, wording='Test1', question_type=Question.type_of_question[0][0])
        self.form_data = {
            'meaning': 'bla bla bla',
        }

    def test_valid_data(self):
        form = AnswerForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        """ Проверка обязательных параметров формы """
        for field, value in self.form_data.items():
            new_form = self.form_data.copy()
            new_form.pop(field)
            form = AnswerForm(data=new_form,)
            self.assertFalse(form.is_valid())
