import datetime

from django.test import TestCase

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
