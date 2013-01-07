"""Date utility functions."""

import datetime
import pytz

UTC = pytz.utc
UTC_2000 = UTC.localize(datetime.datetime(2000, 1, 1))


def minutes_since_2000_to_utc(minutes_since_2000):
    return UTC_2000 + datetime.timedelta(minutes=minutes_since_2000)


def utc_to_minutes_since_2000(utc_datetime):
    return int((utc_datetime - UTC_2000).total_seconds() / 60)


def to_utc(datetime_object):
    """If datetime is naive, assume it is UTC and turn it into a UTC
    date. If it has an associated timezone, translate to UTC."""

    if datetime_object.utcoffset() is None:
        return UTC.localize(datetime_object)
    else:
        return datetime_object.astimezone(UTC)
