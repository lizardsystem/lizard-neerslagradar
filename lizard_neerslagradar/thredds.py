"""Functions for communicating with thredds."""

import datetime
import pandas
from pydap import client

from lizard_neerslagradar import dates

DATASET_URL = 'http://gmdb.lizard.net/thredds/dodsC/radar/radar.nc'


class Timeseries(object):
    """Class copied from the in-progress lizard-datasource. Should be
    imported from somewhere later."""
    def __init__(
        self,
        timeseries_dict=None,
        timeseries_pandas=None,
        timeseries_times=None, timeseries_values=None):
        """
        Can be called with either:

        timeseries_dict, a dict with UTC datetimes as keys and floats
        as values.

        timeseries_pandas, a pandas timeseries.

        timeseries_times and timeseries_values, two iterables of equal
        length containing the times (UTC datetimes) and values of the
        timeseries."""
        if timeseries_dict is not None:
            self.timeseries = pandas.Series(timeseries_dict)
        elif timeseries_pandas is not None:
            self.timeseries = timeseries_pandas.copy()
        elif timeseries_times is not None and timeseries_values is not None:
            self.timeseries = pandas.Series(
                index=timeseries_times, data=timeseries_values)
        else:
            raise ValueError("Timeseries.__init__ called incorrectly.")

    def dates(self):
        return self.timeseries.keys()

    def values(self):
        return list(self.timeseries)

    def iter_items(self):
        return ((k, self.timeseries[k]) for k in self.timeseries.keys())


def get_thredds_url(step, datatype, start_dt):
    """Step is a datetime.timedelta object of 5 minutes, 1 hour or 1
    day.  Datatype is 'R' for realtime data, 'N' for near-realtime
    data, or 'A' for... ? data."""

    thredds_server = (
        'http://p-fews-ws-d1.external-nens.local:8080/thredds/catalog/radar')

    if step == datetime.timedelta(days=1):
        url = (
            ('{thredds_server}/TF_2400_{datatype}/{year}/{month:02}/{day:02}/'
             'RAD_TF2400_{datatype}_{year}{month:02}{day:02}080000.h5')
            .format(
                thredds_server=thredds_server,
                datatype=datatype,
                year=start_dt.year,
                month=start_dt.month,
                day=start_dt.day))
    elif step == datetime.timedelta(hours=1):
        url = (
            ('{thredds_server}/TF0100_{datatype}/{year}/{month:02}/{day:02}/'
             'RAD_TF0100_{datatype}_{year}{month:02}{day:02}000000.h5')
            .format(
                thredds_server=thredds_server,
                datatype=datatype,
                year=start_dt.year,
                month=start_dt.month,
                day=start_dt.day))
    else:
        url = (
            ('{thredds_server}/TF0005_{datatype}/{year}/{month:02}/{day:02}/'
             'RAD_TF0005_{datatype}_{year}{month:02}{day:02}{hour:02}0000.h5')
            .format(
                thredds_server=thredds_server,
                datatype=datatype,
                year=start_dt.year,
                month=start_dt.month,
                day=start_dt.day,
                hour=start_dt.hour))
    return url


class ThreddsDataset(object):
    def __init__(self, url, start_dt, end_dt, step):
        """
        A thredds dataset is defined by four things:
        - An URL

        - A start and end datetime (must have UTC timezone). The end
          datetime is _exclusive_, e.g. if there is one dataset per
          hour, then a dataset might be from 2013-01-07 10:00 to
          2013-01-07 11:00; it will contain the 10:00 data but not the
          11:00 data.

        - A step (it's either 5 minute, 60 minute or 24 hour
          data). datetime.timedelta object.
        """

        self.url = url
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.step = step
        self._dataset = None

    @property
    def dataset(self):
        if not self._dataset:
            self._dataset = client.open_url(self.url)
        return self._dataset

    def get(self, x, y, start_dt, end_dt):
        """Get data from this dataset between start_dt and
        end_dt (both inclusive). The data returned is a list of
        (datetime, value) tuples.

        x, y is a coordinate in dataset coordinates."""

        if ((end_dt < start_dt) or
            (start_dt >= self.end_dt) or
            (end_dt < self.start_dt)):
            # No data
            return []

        # The following verbose bit of code is a crude way to get a
        # list of datetimes we need to deliver data for, and the
        # corresponding min and max index in thredds. Could be made a
        # lot more Pythonic...
        index = 0
        dt = self.start_dt
        minindex = None
        maxindex = None
        dts = []

        while dt < self.end_dt:
            if start_dt <= dt <= end_dt:
                dts.append(dt)
                if minindex is None:
                    minindex = index
                maxindex = index
            index += 1
            dt = dt + self.step

        # Fetch the data
        data = (
            self.dataset['precipitation']['precipitation']
            [x, y, minindex:(maxindex + 1)])

        # Return as datetime, value tuples
        return zip(dts, data)


def get_timeseries(start_date, end_date, identifier):
    pixel_x, pixel_y = identifier['identifier']

    start_minutes_since_2000 = dates.utc_to_minutes_since_2000(start_date)
    end_minutes_since_2000 = dates.utc_to_minutes_since_2000(end_date)

    dataset = client.open_url(DATASET_URL)

    selected_dates = ((dataset.time >= start_minutes_since_2000) &
                      (dataset.time <= end_minutes_since_2000))

    if not any(selected_dates):
        return None

    alldates = [dates.minutes_since_2000_to_utc(d)
                for d in dataset['time'][selected_dates]]

    series = [max(s, 0)
              for s in
              dataset['rain']['rain'][selected_dates, pixel_x, pixel_y]]

    return Timeseries(timeseries_times=alldates, timeseries_values=series)
