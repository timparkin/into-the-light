import csv
from decimal import Decimal, InvalidOperation
from cStringIO import StringIO


class OptionException(Exception):
    pass



class OptionManager(object):

    REQUIRED_COLUMNS=('code','price')

    def processFile(self, currentOptions, f):

        if currentOptions is None:
            currentOptions = []
        currentOptionsMap = dict( [(o['code'], o) for o in currentOptions] )
        newOptions = self._getOptionsFromFile(f)

        return newOptions


    def _getOptionsFromFile(self, f):

        reader = csv.reader(f)

        headers = reader.next()
        self._checkHeaders(headers)


        def code(option, header, value):
            if not value:
                raise OptionException('No code specified')
            if value in codes:
                raise OptionException('Duplicate code: %s'%value)
            if value.find('.') != -1:
                raise OptionException("Invalid code: %s (cannot contain '.' characters)"%value)
            codes.add(value)
            option[header] = value


        def price(option, header, value):
            if not value:
                raise OptionException('No price specified')
            try:
                option[header] = Decimal(value)
            except InvalidOperation:
                raise OptionException('Invalid price: %s'%value)


        def cat(option, header, value):
            if not value:
                raise OptionException('Must have a value for: %s'%header)
            option['cats'].append( {'cat':header, 'value':value} )



        codes = set()
        rv = []
        for row in reader:
            
            row = [i.decode('latin_1') for i in row]

            if not row:
                # Skip blank lines.
                continue

            option = {'cats': []}
            for i in range(len(headers)):
                header = headers[i]
                try:
                    value = row[i]
                except IndexError:
                    raise OptionException('incomplete row: %s'%', '.join(row))
                    

                value = value.strip()

                {
                    'code': code,
                    'price': price,
                }.get(header, cat)(option, header, value)

            self._checkOption(option)
            rv.append(option)

        return rv


    def _checkHeaders(self, headers):
        for col in self.REQUIRED_COLUMNS:
            if col not in headers:
                raise OptionException('Missing column: %s'%col)
        tmpHeaders = set()
        for header in headers:
            if header in tmpHeaders:
                raise OptionException('Duplicate column: %s'%header)
            tmpHeaders.add(header)


    def _checkOption(self, row):
        pass


    def exportOptions(self, options):

        def writeHeaders(writer, option):
            headers = [h for h in self.REQUIRED_COLUMNS]
            cats = option['cats']
            for cat in cats:
                headers.append( cat['cat'] )
            writer.writerow(headers)


        def writeRow(writer, option):
            row = [option[h] for h in self.REQUIRED_COLUMNS]
            cats = option['cats']
            for cat in cats:
                row.append( cat['value'] )
            row = [unicode(i).encode('latin_1') for i in row ]
            writer.writerow(row)


        data = StringIO()
        writer = csv.writer(data)

        headersWritten = False

        for option in options:
            if not headersWritten:
                # Write the headers
                writeHeaders(writer, option)
                headersWritten = True

            writeRow(writer, option)

        return data.getvalue()



def getMinimumPrice(options):
    minPrice = options[0]
    for option in options:
        if option['price']<minPrice:
            minPrice = option['price']
    return minPrice



def getPrice(option):
    return option['price']
        


def inStock(options):
    return getInStockOptions(options) != []



def getInStockOptions(options):
    rv = []
    for option in options:
        if option['_stockLevel'] > 0:
            rv.append(option)
    return rv



def hasPriceRange(options):
    prices = set()
    for option in options:
        prices.add(option['price'])
    return len(prices) > 1



def getOptionsAndValues(options):
    rv = []
    map = {}

    for option in options:
        for cat in option['cats']:
            catRecord = map.get(cat['cat'])
            if catRecord is None:
                catRecord = {'cat': cat['cat'], 'values': [] }
                rv.append(catRecord)
                map[cat['cat']] = catRecord

            if cat['value'] not in catRecord['values']:
                catRecord['values'].append(cat['value'])

    return rv



def findOption(options, key):
    # key is a sequence of {cat, value} dictionaries

    def genKey(cats):
        return [(o['cat'], o['value']) for o in cats]

    rv = []
    for option in options:
        optionCats = set(genKey(option['cats']))
        keyCats = set(genKey(key))
        if keyCats.issubset(optionCats):
            rv.append(option)

    return rv

    
    
