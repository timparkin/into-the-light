"""
A collection of CSV-related utilities.
"""


from cStringIO import StringIO
import csv



def parseRow(s):
    """
    Utility function to parse a single "row" of text.
    """
    return csv.reader(StringIO(s)).next()



def decodeFilter(reader, encoding="utf-8"):
    """
    Decodes the cells of a row as they are parsed from the CSV.
    """
    for row in reader:
        yield [cell.decode(encoding) for cell in row]



def encodeFilter(rows, encoding="utf-8"):
    """
    Encode the cells of a row on the way to being written to a CSV.
    """
    for row in rows:
        yield [cell.encode(encoding) for cell in row]



def encodeDictFilter(rows, encoding="utf-8"):
    """
    Encode the values of a dictionary row on the way to being written to a CSV.
    """
    for row in rows:
        yield dict( [(k,v.encode(encoding)) for k,v in row.iteritems()])



def guessCSVDialect(csvIO, numCols=None, default=csv.excel, maxSampleSize=1024):
    """
    Try to guess the dialect of a CSV file.
    
    If possible, provide the number of columns in the CSV, it gives this
    function a much better chance of guessing correctly because it can actually
    test the dialect against the CSV.

    csvIO -- a file-like object containing CSV data
    numCols -- the expected number of columns in the CSV
    default -- the default to use, if all else fails
    maxSampleSize -- the maximum size of the sample passed to the csv Sniffer
    """
    pos = csvIO.tell()
    try:
        csvIO.seek(0)
        return _guessCSVDialect(csvIO, numCols, default, maxSampleSize)
    finally:
        csvIO.seek(pos)



def _guessCSVDialect(csvIO, numCols, default, maxSampleSize):

    # Read some sample data from the stream.
    sampleData = csvIO.read(maxSampleSize)
    if not sampleData:
        return default

    # See if the csv module can sniff the dialect (it's not hugely reliable
    # though).
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(sampleData, delimiters='\t;, ')

    # Try creating a reader, sometimes this fails with the sniffed dialect.
    try:
        csvIO.seek(0)
        reader = csv.reader(csvIO, dialect)
    except TypeError:
        dialect = default

    # If we don't know how many cols to expect then that's the best we can do
    if numCols is None:
        return dialect

    # Test the number of cols using the dialect from above and then a list of
    # common dialects to try after.
    dialects = [dialect, csv.excel, csv.excel_tab]
    for dialect in dialects:
        csvIO.seek(0)
        reader = csv.reader(csvIO, dialect)
        try:
            if len(reader.next()) == numCols:
                return dialect
        except csv.Error:
            pass

    # Oh well, you can't say I didn't try
    return default

