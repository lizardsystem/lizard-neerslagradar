"""Tests for layers.py"""

from django.test import TestCase

from lizard_neerslagradar import layers


class TestMinutesSince2000ToUtc(TestCase):
    def test_1_day(self):
        day = 24 * 60  # minutes
        utc = layers.minutes_since_2000_to_utc(day)

        self.assertEquals(utc.year, 2000)
        self.assertEquals(utc.month, 1)
        self.assertEquals(utc.day, 2)
        self.assertEquals(utc.hour, 0)
        self.assertEquals(utc.minute, 0)
