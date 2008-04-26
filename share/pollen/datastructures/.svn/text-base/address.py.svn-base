"""
Address data structures and utilities.

The following ISO codes are not currently supported by the utility functions:

    BV, HM, FK, YT, RS, NF, KP, TK, TF, NR, PN, NU, PM, GS, EH, AF, CC, IR, AQ,
    CX, IM, IO, AX, CU, ME, MM, KM, ST, UM, SJ, SH, SO, SD

"""

import pkg_resources
import csv
import re

from pollen.iso.country import countryCodes



class Address(object):
    """
    Basic address structure.

    Address makes no assumptions about how it is used, only really defining
    common names for the various parts of an address. However, some methods may
    only work if the address is in a specific format, i.e. county is an ISO
    country code.

    The decision to split the street address into address1-3 is difficult. Some
    places require the address split out; some like the street address in one
    string with newlines.
    
    It's always easy to join but it's not as easy to split text, at least not
    in a way that makes sense. It's therefore probably best to ask the person
    entering an address to do so in a way that makes most sense.
    """


    def __init__(self, streetAddress1=None, streetAddress2=None,
            streetAddress3=None, townOrCity=None, postalCode=None,
            stateOrProvince=None, country=None):
        self.streetAddress1 = streetAddress1
        self.streetAddress2 = streetAddress2
        self.streetAddress3 = streetAddress3
        self.townOrCity = townOrCity
        self.postalCode = postalCode
        self.stateOrProvince = stateOrProvince
        self.country = country


    def addressLines(self):
        """
        Return a sequence of lines for the address in the correct format for
        the country (if present).

        If country is present it *must* be a country code. The country in the
        returned sequence will be represented by its full name.
        """
        if self.country is not None:
            info = addressFormat(self.country)
        else:
            info = addressFormat("GB")
        parts = []
        for i in info:
            attr = i['attr']
            required = i['required']
            if attr == 'country':
                part = countryCodes.getCountryName(self.country)
            else:
                part = getattr(self, attr)
            if part:
                parts.append(part)
        return parts


    def toString(self):
        return '\n'.join(self.addressLines())



def addressFormat(countryCode):
    """
    Return a list of dicts describing the order in which the attribute of an
    address for the given country code should be presented, which of those
    attributes are required a (optional) label.
    """

    addressFormat = addressInfo.forCountry(countryCode)['AddressFormat']
    if not addressFormat:
        return None

    # The street address parts are not configured in the address info because
    # they're always returned and the first is required.
    r = [('streetAddress1', True, None), ('streetAddress2', False, None),
            ('streetAddress3', False, None)]

    # Add the fields specified in the address info. A field that starts with a
    # "!" is required.
    for part in addressFormat.split(','):
        part = part.strip()
        if part[0] == '!':
            required = True
            part = part[1:]
        else:
            required = False
        if '=' in part:
            attr, label = part.split('=', 1)
        else:
            attr, label = part, None
        r.append((attr, required, label))

    # List street address, the country is always added and is required.
    r.append(('country', True, None))

    return [dict(zip(['attr', 'required', 'label'], i)) for i in r]



def isPostalCodeValid(postalCode, countryCode, onUnknown=True):
    """
    Validate the postal code matches the format for the given country.  If
    either the country code or the postal code pattern is unknown then return
    onUnknown (defaults to True).
    """

    try:
        info = addressInfo.forCountry(countryCode)
    except ValueError:
        return onUnknown

    pattern = info['PostalCodePattern']

    if not pattern:
        return onUnknown

    pattern = _completePostalCodeRegex(pattern)
    return re.match(pattern, postalCode) is not None



def _completePostalCodeRegex(pattern):
    """
    Complete the partial regex stored in the address info database by adding
    start and end matches.
    """
    return '^%s$' % (pattern,)



class AddressInfo(object):

    data = None


    def forCountry(self, countryCode):
        if self.data is None:
            self._loadData()
        try:
            return self.data[countryCode]
        except KeyError:
            raise ValueError("Unknown country code %r" % (countryCode,))


    def statesForCountry(self, countryCode):
        """
        Return a sequence of states/provinces for the given country or None if
        the list is not available.

        Each item in the sequence is a dictionary containing the following
        keys:

            * StateCode -- code used to identify the state.
            * StateName -- English name of the state.

        Note: if there is no code used in the country then code will be the
        same as the name.
        """
        f = pkg_resources.resource_stream("pollen.datastructures", "states.csv")
        try:
            states = [row for row in csv.DictReader(f) if row['CountryCode'] == countryCode]
        finally:
            f.close()
        if not states:
            states = None
        return states


    def _loadData(self):
        f = pkg_resources.resource_stream("pollen.datastructures", "address.csv")
        try:
            data = {}
            for row in csv.DictReader(f):
                countryCode = row.pop('CountryCode')
                data[countryCode] = row
            self.data = data
        finally:
            f.close()



addressInfo = AddressInfo()



if __name__ == '__main__':

    import unittest

    class TestUtilities(unittest.TestCase):

        def testAddressFormat(self):
            self.assertEquals(addressFormat('GB'), [
                {'attr': 'streetAddress1', 'required': True, 'label': None},
                {'attr': 'streetAddress2', 'required': False, 'label': None},
                {'attr': 'streetAddress3', 'required': False, 'label': None},
                {'attr': 'townOrCity', 'required': True, 'label': None},
                {'attr': 'stateOrProvince', 'required': False, 'label': 'County'},
                {'attr': 'postalCode', 'required': True, 'label': None},
                {'attr': 'country', 'required': True, 'label': None},
                ])
            self.assertEquals(addressFormat('IE'), [
                {'attr': 'streetAddress1', 'required': True, 'label': None},
                {'attr': 'streetAddress2', 'required': False, 'label': None},
                {'attr': 'streetAddress3', 'required': False, 'label': None},
                {'attr': 'townOrCity', 'required': True, 'label': None},
                {'attr': 'stateOrProvince', 'required': True, 'label': 'County'},
                {'attr': 'country', 'required': True, 'label': None},
                ])
            self.assertEquals(addressFormat('FR'), [
                {'attr': 'streetAddress1', 'required': True, 'label': None},
                {'attr': 'streetAddress2', 'required': False, 'label': None},
                {'attr': 'streetAddress3', 'required': False, 'label': None},
                {'attr': 'postalCode', 'required': True, 'label': None},
                {'attr': 'townOrCity', 'required': True, 'label': None},
                {'attr': 'stateOrProvince', 'required': False, 'label': None},
                {'attr': 'country', 'required': True, 'label': None},
                ])
            self.assertEquals(addressFormat('US'), [
                {'attr': 'streetAddress1', 'required': True, 'label': None},
                {'attr': 'streetAddress2', 'required': False, 'label': None},
                {'attr': 'streetAddress3', 'required': False, 'label': None},
                {'attr': 'townOrCity', 'required': True, 'label': None},
                {'attr': 'stateOrProvince', 'required': True, 'label': 'State'},
                {'attr': 'postalCode', 'required': True, 'label': 'ZIP Code'},
                {'attr': 'country', 'required': True, 'label': None},
                ])
            self.assertRaises(ValueError, addressFormat, None)

        def testValidatePostalCode(self):
            self.assertTrue(isPostalCodeValid('LS17 6QR', countryCode='GB'))
            self.assertFalse(isPostalCodeValid('123', countryCode='GB'))
            self.assertTrue(isPostalCodeValid('LS17 6QR', countryCode='GB'))
            self.assertTrue(isPostalCodeValid('12345', countryCode='US'))
            self.assertFalse(isPostalCodeValid('12345-12345', countryCode='US'))

        def testValidatePostalCodeUnknown(self):
            self.assertTrue(isPostalCodeValid('12345-12345', countryCode='unknown'))
            self.assertTrue(isPostalCodeValid('12345-12345', countryCode='unknown', onUnknown=True))
            self.assertFalse(isPostalCodeValid('12345-12345', countryCode='unknown', onUnknown=False))

        def test_addressLines(self):
            a = Address(streetAddress1="237 Lidgett Lane", townOrCity="Leeds", stateOrProvince="West Yorkshire", postalCode="LS17 6QR", country="GB")
            self.assertEquals(a.addressLines(), ["237 Lidgett Lane", "Leeds", "West Yorkshire", "LS17 6QR", "UNITED KINGDOM"])
            a = Address(streetAddress1="18, Avenue Suffren", townOrCity="Paris", postalCode="75015", country="FR")
            self.assertEquals(a.addressLines(), ["18, Avenue Suffren", "75015", "Paris", "FRANCE"])

        def test_states(self):
            self.assertEquals(len(addressInfo.statesForCountry('US')), 50)
            self.assertTrue(addressInfo.statesForCountry('GB') is None)

    unittest.main()

