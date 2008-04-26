"""
Telephone related data structures, formatters and parsers.
"""


import csv
import re
import pkg_resources



PHONE_NUMBER_RE = re.compile(
    """
    ^\+(?P<countryCode>[0-9]+)              # Country Code
    \s
    (?P<areaCode>[0-9]+)                    # Area Code
    \s
    (?P<number>[0-9]+)                      # Number
    (\sext\.\s(?P<extension>[0-9]+))?$      # Extension (optional)
    """,
    re.VERBOSE)



class PhoneNumber(object):
    """
    A phone number according to the ITU standard notation (ish).

    http://www.itu.int/rec/T-REC-E.123-200102-I/E
    """


    def __init__(self, countryCode, areaCode, number, extension=None):
        self.countryCode = countryCode
        self.areaCode = areaCode
        self.number = number
        self.extension = extension


    def toString(self):
        s = "+%s %s %s" % (self.countryCode, self.areaCode, self.number)
        if self.extension is not None:
            s += " ext. %s" % (self.extension,)
        return s


    def fromString(cls, s):
        match = PHONE_NUMBER_RE.match(s)
        if not match:
            raise ValueError("Unrecognisable phone number %r" % (s,))
        return cls(**match.groupdict())

    fromString = classmethod(fromString)


    __str__ = toString
    __repr__ = __str__




def countryCodes():
    """
    Return a mapping of ISO country code to international dialling code.
    """
    reader = csv.reader(pkg_resources.resource_stream('pollen.datastructures',
        'telephone-country-codes.csv'))
    return dict(reader)


if __name__ == '__main__':

    import unittest

    class TestPhoneNumber(unittest.TestCase):

        def test_init(self):
            PhoneNumber(1, 2, 3)
            PhoneNumber(1, 2, 3, extension=4)
            self.assertRaises(TypeError, PhoneNumber, 1, 2)

        def test_toString(self):
            self.assertEquals(PhoneNumber('44', '113', '1234567').toString(), '+44 113 1234567')
            self.assertEquals(PhoneNumber('44', '113', '1234567', extension='890').toString(), '+44 113 1234567 ext. 890')

        def test_fromString(self):
            tests = ['+44 113 1234567', '+44 113 1234567 ext. 890']
            for test in tests:
                self.assertEquals(str(PhoneNumber.fromString(test)), test)


    class TestCountryCodes(unittest.TestCase):

        def test_countryCodes(self):
            self.assertEquals(countryCodes().get('GB'), '44')
            self.assertEquals(countryCodes().get('US'), '1')
            self.assertEquals(countryCodes().get('TL'), None)


    unittest.main()

