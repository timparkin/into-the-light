from zope.interface import Interface
import sys
from exceptions import ImportError
import cPickle
import datetime

from zope.interface import implements

class IndexDefinition(object):
    def __init__(self, title, shortDescription, *a):
        self.title = title
        self.shortDescription = shortDescription
        self.others = a

class IContentIndex( Interface ):
    def indexItem( self, item ):
        pass

    def removeItem( self, item ):
        pass

    def query( self, query ):
        pass

def getContentIndex( realm ):
    return _indexFactory( realm )

class NullContentIndex( object ):
    implements( IContentIndex )

    def __init__( self ):
        pass

    def checkedIndexItem(self, item, now=None):
        pass
        
    def indexItem( self, item ):
        pass

    def removeItem( self, item ):
        pass

    def query( self, query, language=None ):
        return []

class XapwrapContentIndex( object ):

    implements( IContentIndex )

    def __init__( self, directory, languages ):
        self.directory = directory
        self.languages = languages

    def checkedIndexItem(self, item, now=None):
        """Check that the item should be seen on the public site before indexing it"""
        from cms.types.base import ContentItem
        if not now:
            now = datetime.datetime.utcnow().date()

        if item.workflowStatus == ContentItem.WORKFLOW_STATUS_APPROVED:
            if item.publicationDate:
                if now < item.publicationDate:
                    return False
            if item.expirationDate:
                if now > item.expirationDate:
                    return False
            self.indexItem(item)
            return True
        return False 

    def indexItem(self, item):
        index = xapwrap.SmartIndex(self.directory, True)

        self._removeItem(index, item.id)

        if not hasattr(item, 'contentIndex'):
            # No idea what to index
            return 

        for language in self.languages:
            self._indexLanguage(index, language.code, item)

        index.close()

    def _indexLanguage(self, index, language, item):
        attributes = item.getAttributeValues(language)
        textFields = []
        for k in self._getAttributeNamesToIndex(item):
            v = attributes.get(k, None)
            if not isinstance(v, str) and not isinstance(v, unicode):
                v = str(v)
            if v is None or v == '':
                continue
            textFields.append(xapwrap.TextField(k, v))

        title = self._getTitle(item, attributes)
        shortDescription = self._getShortDescription(item, attributes)
        keywords = xapwrap.Keyword('poopid', str(item.id))

        data = IndexData(item.id, title, language, shortDescription)

        print 'adding document id', item.id, 'language', language
        doc = xapwrap.Document(textFields=textFields, keywords=keywords, data=data)
        index.index(doc)

    def _getAttributeNamesToIndex(self, item):
        rv = []
        rv.append(item.contentIndex.title)
        if item.contentIndex.shortDescription:
            rv.append(item.contentIndex.shortDescription)
        rv = rv + list(item.contentIndex.others)
        return rv

    def _getTitle(self, item, attributes):
        return attributes.get(item.contentIndex.title, None)

    def _getShortDescription(self, item, attributes):
        rv = None
        if not item.contentIndex.shortDescription:
            return rv
        rv = attributes.get(item.contentIndex.shortDescription, None)
        if rv is not None and len(rv) > 100:
            rv = rv[:100] + '...'

        return rv

    def removeItem(self, id):
        index = xapwrap.SmartIndex(self.directory, True)
        self._removeItem(index, id)
        index.close()

    def _removeItem(self, index, id):
        res = index.search( 'POOPID' + str(id) )
        if res is not None :
            for obj in res:
                uid = obj['uid']
                print 'deleting document id', id
                index.delete_document( uid )

    def query(self, queryStr, language=None):
        index = xapwrap.SmartReadOnlyIndex(self.directory)

        rv = []

        queryStr = queryStr.lower()

        res = index.search(ANDQuery(queryStr))
        for obj in res:
            doc = index.get_document(obj['uid'])
            data = cPickle.loads(doc.get_data())
            # Should really put the language into the query
            if language and data.language != language:
                continue
            rv.append(data)

        index.close()
    
        return rv
        

class IndexData(object):
    def __init__(self, id, title, language, shortDescription):
        self.id = id
        self.title = title
        self.language = language
        self.shortDescription = shortDescription

    def __repr__(self):
        return "IndexData(%s, '%r', '%s', '%s')" % (self.id, self.title, self.language, self.shortDescription)

try:

    import xapian
    import xapwrap

    _indexFactory = XapwrapContentIndex

    class ANDQuery( xapwrap.Query ):
        def __init__(self, queryStr):
            self._words = queryStr.split()

        def prepare( self, queryParser ):
            rv = None

            for word in self._words:
                newTerm = xapian.Query(word.encode('utf8'))
                if rv is None:
                    rv = newTerm
                else:
                    rv = xapian.Query(xapian.Query.OP_AND, rv, newTerm)
            return rv

except ImportError:
    print '******** xapwrap not found, indexing disabled *******'
    _indexFactory = NullContentIndex
