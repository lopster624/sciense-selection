import datetime
from django.test import TestCase
from django.contrib.auth.models import User

from account.models import Affiliation
from application.forms import FilterForm
from application.models import Direction
from utils.calculations import get_current_draft_year


class FilterFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create(username='test', email='test@test.ru')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)

    def setUp(self) -> None:
        master_affiliations = Affiliation.objects.all()
        self.directions_set = [(aff.direction.id, aff.direction.name) for aff in master_affiliations]
        self.in_wishlist_set = [(affiliation.id, affiliation) for affiliation in master_affiliations]
        current_year, current_season = get_current_draft_year()
        self.draft_year_set = [(2020, 2020), (2021, 2021)]
        self.form_data = {
            'ordering': 'member__user__last_name',
            'directions': [str(self.directions_set[0][0]), ],
            'affiliation': [str(self.in_wishlist_set[0][0]), ],
            'in_wishlist': [str(self.in_wishlist_set[0][0]), ],
            'draft_season': [str(current_season[0]), ],
            'draft_year': ['2020'],
        }
        self.initial_data = {'draft_year': 2021,
                             'draft_season': current_season,
                             }

    def test_valid_form(self):
        form = FilterForm(initial=self.initial_data, data=self.form_data,
                          directions_set=self.directions_set,
                          in_wishlist_set=self.in_wishlist_set,
                          draft_year_set=self.draft_year_set, chosen_affiliation_set=self.in_wishlist_set)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = FilterForm(initial=self.initial_data, data={'draft_year': ['2920']},
                          directions_set=self.directions_set,
                          in_wishlist_set=self.in_wishlist_set,
                          draft_year_set=self.draft_year_set, chosen_affiliation_set=self.in_wishlist_set)
        self.assertFalse(form.is_valid())

    def test_initial_value(self):
        form = FilterForm(initial=self.initial_data, data=self.form_data,
                          directions_set=self.directions_set,
                          in_wishlist_set=self.in_wishlist_set,
                          draft_year_set=self.draft_year_set, chosen_affiliation_set=self.in_wishlist_set)
        self.assertEqual(form['draft_year'].initial, 2021)

