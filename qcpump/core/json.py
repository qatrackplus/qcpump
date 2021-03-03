import datetime
import decimal
from json import JSONEncoder
import uuid

import numpy as np

# JSON Encoders ripped from Django & QATrack+

NP_INT_TYPES = (
    np.int_,
    np.intc,
    np.intp,
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64,
)

NP_FLOAT_TYPES = (
    np.float_,
    np.float16,
    np.float32,
    np.float64,
)

serializing_methods = [
    'tolist',  # np.array,
    'to_list',
    'to_dict',  # pd.DataFrame,
]


def _get_duration_components(duration):
    days = duration.days
    seconds = duration.seconds
    microseconds = duration.microseconds

    minutes = seconds // 60
    seconds = seconds % 60

    hours = minutes // 60
    minutes = minutes % 60

    return days, hours, minutes, seconds, microseconds


def duration_iso_string(duration):
    if duration < datetime.timedelta(0):
        sign = '-'
        duration *= -1
    else:
        sign = ''

    days, hours, minutes, seconds, microseconds = _get_duration_components(duration)
    ms = '.{:06d}'.format(microseconds) if microseconds else ""
    return '{}P{}DT{:02d}H{:02d}M{:02d}{}S'.format(sign, days, hours, minutes, seconds, ms)


def is_aware(value):
    """
    Determine if a given datetime.datetime is aware.

    The concept is defined in Python's docs:
    https://docs.python.org/library/datetime.html#datetime.tzinfo

    Assuming value.tzinfo is either None or a proper datetime.tzinfo,
    value.utcoffset() implements the appropriate logic.
    """
    return value.utcoffset() is not None


class DjangoJSONEncoder(JSONEncoder):

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.time):

            if is_aware(o):  # pragma: nocover
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:  # pragma: nocover
                r = r[:12]
            return r
        elif isinstance(o, datetime.timedelta):
            return duration_iso_string(o)
        elif isinstance(o, (decimal.Decimal, uuid.UUID)):
            return str(o)
        else:  # pragma: nocover
            return super().default(o)


class QCPumpJSONEncoder(DjangoJSONEncoder):
    # inspired by https://github.com/illagrenan/django-numpy-json-encoder

    def default(self, o):
        if isinstance(o, NP_INT_TYPES):
            return int(o)
        elif isinstance(o, NP_FLOAT_TYPES):
            return float(o)
        elif isinstance(o, (range, zip, set,)):
            return list(o)

        for m in serializing_methods:
            method = getattr(o, m, None)
            if callable(method):
                return method()

        if isinstance(o, datetime.datetime):
            r = o.strftime("%Y-%m-%d %H:%M:%S")
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith('+00:00'):  # pragma: nocover
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, datetime.date):
            return o.strftime("%Y-%m-%d")

        return super().default(o)
