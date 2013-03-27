import datetime

from django.test import TestCase
import mock

from lizard_neerslagradar import views


class TestAnimationDatetimes(TestCase):

    def test_returned_datetimes(self):
        start_date = datetime.datetime(
            year=2013,
            month=1,
            day=2,
            hour=15,
            minute=17)

        datetimes = list(views.animation_datetimes(
                start_date,
                hours_before_now=24))

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
