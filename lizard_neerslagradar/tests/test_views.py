import datetime

from django.test import TestCase
import mock

from lizard_neerslagradar import views


def standard_start_date():
    return datetime.datetime(
        year=2013,
        month=1,
        day=2,
        hour=15,
        minute=17)


class TestAnimationDatetimes(TestCase):

    @mock.patch('lizard_neerslagradar.views.utc_now',
                standard_start_date)
    def test_returned_datetimes(self):

        datetimes = list(views.animation_datetimes(24))

        self.assertEquals(len(datetimes), 24 * 12)
        self.assertEquals(
            datetimes[0],
            datetime.datetime(
                year=2013,
                month=1,
                day=1,
                hour=15,
                minute=20))
        self.assertEquals(
            datetimes[-1],
            datetime.datetime(
                year=2013,
                month=1,
                day=2,
                hour=15,
                minute=15))

    @mock.patch('lizard_neerslagradar.views.DefaultView.user_logged_in',
                lambda self: False)
    def test_number_of_hours1(self):
        view = views.DefaultView()
        self.assertEquals(view.number_of_hours, 3)

    @mock.patch('lizard_neerslagradar.views.DefaultView.user_logged_in',
                lambda self: True)
    def test_number_of_hours2(self):
        view = views.DefaultView()
        self.assertEquals(view.number_of_hours, 24)

    @mock.patch('lizard_neerslagradar.views.DefaultView.user_logged_in',
                lambda self: False)
    def test_content_actions1(self):
        view = views.DefaultView()
        klasses = [action.klass for action in view.content_actions]
        self.assertFalse('popup-date-range' in klasses)

    @mock.patch('lizard_neerslagradar.views.DefaultView.user_logged_in',
                lambda self: True)
    def test_content_actions2(self):
        view = views.DefaultView()
        klasses = [action.klass for action in view.content_actions]
        self.assertTrue('popup-date-range' in klasses)
