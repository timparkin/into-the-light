"""Utilities for parsing isoformat strings into datetime types.
"""

from datetime import datetime, date, time

def datetimefromisoformat(s):
    """Parse an isoformat string into a datetime.datetime object.
    """
    date, time = s.split()
    year, month, day = _parsedate(date)
    hour, minute, second, microsecond = _parsetime(time)
    return datetime(year, month, day, hour, minute, second, microsecond)

def datefromisoformat(s):
    """Parse an isoformat date string into a datetime.date object.
    """
    year, month, day = _parsedate(s)
    return date(year, month, day)

def timefromisoformat(s):
    """Parse an isoformat time string into a datetime.time object.
    """
    hour, minute, second, microsecond = _parsetime(s)
    return time(hour, minute, second, microsecond)

def _parsedate(s):
    """Parse an isoformat date string into a (year, month, day) tuple.
    """
    return [int(i) for i in s.split('-')]

def _parsetime(s):
    """Parse an isoformat time string into a (hour, minute, second,
    microsecond) tuple.
    """

    # The microseond is optional
    if '.' in s:
        time, microsecond = s.split('.')
        microsecond = int(microsecond)
    else:
        time, microsecond = s, 0

    hour, minute, second = [int(i) for i in time.split(':')]
    
    return hour, minute, second, microsecond

if __name__ == '__main__':

    import unittest

    now = datetime.now()
    today = date.today()
    midnight = time()
    
    class Tests(unittest.TestCase):
        
        datetimeTests = [
            [str(now), str(now)],
            [str(now.replace(microsecond=0)), str(now.replace(microsecond=0))],
            [str(now.replace(second=0, microsecond=0)), str(now.replace(second=0, microsecond=0))],
            [str(now.replace(second=0)), str(now.replace(second=0))],
            ]

        dateTests = [
            [str(today), str(today)],
            ]

        timeTests = [
            [str(time(0,0,0)),'00:00:00'],
            [str(time(1,2,3)),'01:02:03'],
            [str(time(1,2,3,4)),'01:02:03.000004'],
            ]

        def test_datetime(self):
            for test,expected in self.datetimeTests:
                result = str(datetimefromisoformat(test))
                self.assertEqual(expected, result)

        def test_date(self):
            for test,expected in self.dateTests:
                result = str(datefromisoformat(test))
                self.assertEqual(expected, result)

        def test_time(self):
            for test,expected in self.timeTests:
                result = str(timefromisoformat(test))
                self.assertEqual(expected, result)

    unittest.main()
