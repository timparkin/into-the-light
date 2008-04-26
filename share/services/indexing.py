from zope.interface import implements
from twisted.python import components, log
from twisted.internet import defer
from nevow import inevow, appserver

from ecommerce.product import index, manager

import hype

class AdminProductIndexer(object):
    implements(index.IProductIndexer)

    """Indexer for the admin ste product index."""

    def __init__(self, path):
        self.path = path


    def add(self, product):
        db = self._openDatabase()
        try:
            doc = self._toHypeDocument(product)
            db.put_doc(doc)
        finally:
            self._closeDatabase(db)

        return defer.succeed(product)


    def update(self, product):
        db = self._openDatabase()
        try:
            doc = self._toHypeDocument(product)

            try:
                docUri = doc['@uri']
                orig_doc = db.get_doc_by_uri(docUri)
                if orig_doc is not None:
                    db.remove(orig_doc)
            except hype.DBRemoveError, e:
                print e

            db.put_doc(doc)
        finally:
            self._closeDatabase(db)

        return defer.succeed(product)


    def remove(self, id):
        db = self._openDatabase()
        try:
            doc = hype.Document(unicode(id))
            #doc['@uri'] = unicode(id)

            try:
                doc = db.get_doc_by_uri(doc['@uri'])
                if doc is not None:
                    db.remove(doc)
            except hype.DBRemoveError, e:
                print e
        finally:
            self._closeDatabase(db)

        return defer.succeed(id)


    def _toHypeDocument(self, product):
        doc = hype.Document(unicode(product.id))
        summary = getattr(product, 'summary', None)
        description = getattr(product, 'description', None)
        metaKeywords = getattr(product, 'metaKeywords', '')
        title = getattr(product, 'title', '')

        if summary:
            doc.add_text(unicode(getattr(summary,'value','')))
        if description:
            doc.add_text(unicode(getattr(description,'value','')))
        doc.add_text(unicode(metaKeywords))
        doc.add_text(unicode(title))

        return doc


    def _openDatabase(self):
        return hype.Database(self.path)


    def _closeDatabase(self, db):
        db.close()


    def getMatchingIds(self, keyWords):

        if keyWords is None:
            return defer.succeed(None)
        keyWords = keyWords.strip()
        if keyWords == '':
            return defer.succeed(None)

        try:
            rv = self._queryDatabase(keyWords)
        except:
            import sys
            log.err('Error searching hype database')
            log.err(sys.exc_info()[1])
            rv = None
        #print rv
        return defer.succeed(rv)

    def _queryDatabase(self, keyWords):
        rv = []
        db = self._openDatabase()
        try:
            res = db.search(unicode(keyWords), simple=False)
            rv = [int(d['@uri']) for d in res]
        finally:
            self._closeDatabase(db)

        return rv



class PublicProductIndexer(AdminProductIndexer):

    """Specialization of the Admin site product indexer for the
       public site."""

    def __init__(self, path, dontIndexCategory):
        super(PublicProductIndexer, self).__init__(path)
        self.dontIndexCategory = dontIndexCategory

    def update(self, product):
        db = self._openDatabase()
        try:
            doc = self._toHypeDocument(product)

            try:
                docUri = doc['@uri']
                orig_doc = db.get_doc_by_uri(docUri)
                if orig_doc is not None:
                    db.remove(orig_doc)
            except hype.DBRemoveError, e:
                print e

            if product.show and self.dontIndexCategory not in product.categories:
                db.put_doc(doc)
        finally:
            self._closeDatabase(db)

        return defer.succeed(product)



class ProductIndexer(object):
    implements(index.IProductIndexer)

    """This wraps the indexers for both the admin product index and
       public product index, it forwards method calls to the individual 
       indexers."""

    def __init__(self, adminPath, publicPath, dontIndexCategory):
        self.admin = AdminProductIndexer(adminPath)
        self.public = PublicProductIndexer(publicPath, dontIndexCategory)

    def setApplication(self, application):
        self.application = application

    def add(self, product):
        d = self.admin.add(product)
        d.addCallback(self.public.add)
        return d

    def update(self, product):
        d = self.admin.update(product)
        d.addCallback(self.public.update)
        return d

    def remove(self, id):
        d = self.admin.remove(id)
        d.addCallback(self.public.remove)
        return d

    def getMatchingIds(self, keyWords):
        return self.admin.getMatchingIds(keyWords)



