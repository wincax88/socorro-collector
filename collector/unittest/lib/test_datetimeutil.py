# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_, ok_
import datetime

from collector.lib import datetimeutil


UTC = datetimeutil.UTC


def test_utc_now():
    """
    Test datetimeutil.utc_now()
    """
    res = datetimeutil.utc_now()
    eq_(res.strftime('%Z'), 'UTC')
    eq_(res.strftime('%z'), '+0000')
    ok_(res.tzinfo)


def test_string_to_datetime():
    """
    Test datetimeutil.string_to_datetime()
    """
    # Empty date
    date = ""
    try:
        res = datetimeutil.string_to_datetime(date)
        raise AssertionError("expect this to raise ValueError")
    except ValueError:
        pass

    # already a date
    date = datetime.datetime.utcnow()
    res = datetimeutil.string_to_datetime(date)

    eq_(res, date.replace(tzinfo=UTC))
    eq_(res.strftime('%Z'), 'UTC')
    eq_(res.strftime('%z'), '+0000')

    # YY-mm-dd date
    date = "2001-11-03"
    res = datetimeutil.string_to_datetime(date)
    eq_(res, datetime.datetime(2001, 11, 3, tzinfo=UTC))
    eq_(res.strftime('%Z'), 'UTC')  # timezone aware

    # and naughty YY-m-d date
    date = "2001-1-3"
    res = datetimeutil.string_to_datetime(date)
    eq_(res, datetime.datetime(2001, 1, 3, tzinfo=UTC))
    eq_(res.strftime('%Z'), 'UTC')  # timezone aware

    # Commented out because I don't thing `YY-mm-dd+HH:ii:ss` is a
    # valid date format.
    ## YY-mm-dd+HH:ii:ss date
    #date = "2001-11-30+12:34:56"
    #try:
    #    res = datetimeutil.string_to_datetime(date)
    #except ValueError:
    #    res = None
    #expected = datetime(2001, 11, 30, 12, 34, 56)
    #assert res == expected, "Date is %s, %s expected." % (date, expected)

    # YY-mm-dd HH:ii:ss.S date
    date = "2001-11-30 12:34:56.123456"
    res = datetimeutil.string_to_datetime(date)
    eq_(res, datetime.datetime(2001, 11, 30, 12, 34, 56, 123456, tzinfo=UTC))

    # Separated date
    date = ["2001-11-30", "12:34:56"]
    res = datetimeutil.string_to_datetime(date)
    eq_(res, datetime.datetime(2001, 11, 30, 12, 34, 56, tzinfo=UTC))

    # Invalid date
    date = "2001-11-32"
    try:
        res = datetimeutil.string_to_datetime(date)
        raise AssertionError("should have raise a ValueError")
    except ValueError:
        pass


def test_string_datetime_with_timezone():
    date = "2001-11-30T12:34:56Z"
    res = datetimeutil.string_to_datetime(date)
    eq_(res, datetime.datetime(2001, 11, 30, 12, 34, 56, tzinfo=UTC))
    eq_(res.strftime('%H'), '12')
    # because it's a timezone aware datetime
    ok_(res.tzname())
    eq_(res.strftime('%Z'), 'UTC')
    eq_(res.strftime('%z'), '+0000')

    # plus 3 hours east of Zulu means minus 3 hours on UTC
    date = "2001-11-30T12:10:56+03:00"
    res = datetimeutil.string_to_datetime(date)
    expected = datetime.datetime(2001, 11, 30, 12 - 3, 10, 56, tzinfo=UTC)
    eq_(res, expected)

    # similar example
    date = "2001-11-30T12:10:56-01:30"
    res = datetimeutil.string_to_datetime(date)
    eq_(res, datetime.datetime(2001, 11, 30, 12 + 1, 10 + 30, 56, tzinfo=UTC))

    # YY-mm-dd+HH:ii:ss.S date
    date = "2001-11-30 12:34:56.123456Z"
    res = datetimeutil.string_to_datetime(date)
    eq_(res, datetime.datetime(2001, 11, 30, 12, 34, 56, 123456, tzinfo=UTC))

    docstring = """
        * 2012-01-10T12:13:14
        * 2012-01-10T12:13:14.98765
        * 2012-01-10T12:13:14.98765+03:00
        * 2012-01-10T12:13:14.98765Z
        * 2012-01-10 12:13:14
        * 2012-01-10 12:13:14.98765
        * 2012-01-10 12:13:14.98765+03:00
        * 2012-01-10 12:13:14.98765Z
    """.strip().splitlines()
    examples = [x.replace('*', '').strip() for x in docstring]
    for example in examples:
        res = datetimeutil.string_to_datetime(example)
        ok_(res.tzinfo)
        ok_(isinstance(res, datetime.datetime))
