def strip(s):
    """Equivalent of str.strip() that copes with None"""
    if s is not None:
        s = s.strip()
    return s

def htmltoplain(data):

    from HTMLParser import HTMLParser
    import htmlentitydefs

    class Parser(HTMLParser):

        def __init__(self):
            HTMLParser.__init__(self)
            self._content = []

        def handle_data(self, data):
            self._content.append(data.decode('utf-8'))

        def handle_rawdata(self, data):
            self._content.append(data.decode('utf-8'))

        def handle_charref(self, name):
            self._content.append(chr(int(name)))

        def handle_entityref(self, name):
            self._content.append(htmlentitydefs.entitydefs[name].decode('iso-8859-1'))

        def _getContent(self):
            return ''.join(self._content)

        content = property(_getContent)

    parser = Parser()
    parser.feed(data)
    return parser.content

