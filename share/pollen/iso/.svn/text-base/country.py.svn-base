"""
ISO country information.
"""

import codecs
from pkg_resources import resource_filename



class CountryCodes(object):
    """
    A list of all ISO country codes.

    The information is available as two collections:
    
      - A list of items, in alphabetical order (sorted by the country name).
      - A dictionary of items, keyed by the country code.

    Each item is a dict containing the following keys:

      - name :: the short country name
      - code :: the alpha-2 code
    """

    _all = None
    _allByCode = None


    def getAll(self):
        if self._all is None:
            self._all = self._loadFromResource()
        return self._all

    all = property(getAll)


    def getAllByCode(self):
        if self._allByCode is None:
            self._allByCode = dict((c['code'],c) for c in self.all)
        return self._allByCode

    allByCode = property(getAllByCode)


    def getCountryName(self, code):
        """
        Return the name of the country with the give ISO code.
        """
        return self.allByCode[code]['name']


    def _loadFromResource(self):
        # Work out the filename
        filename = resource_filename(self.__class__.__module__,
                'countrycodes.txt')
        f = file(filename)
        try:
            # Open the file as a UTF-8 stream
            stream = codecs.getreader('utf-8')(f)
            # Strip the lines
            stream = (l.strip() for l in stream)
            # Remove empty lines
            stream = (l for l in stream if l)
            # Split the lines at the ';'
            stream = (l.strip().split(';') for l in stream)
            # Create a dict for each line
            stream = (dict(zip(['name','code'], l)) for l in stream)
            # Return the final list
            return list(stream)
        finally:
            f.close()



countryCodes = CountryCodes()

