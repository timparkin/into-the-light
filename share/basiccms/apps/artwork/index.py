from zope.interface import Interface, implements
from twisted.internet import defer
from twisted.python import log


class IArtworkIndexer(Interface):

    def add(artwork, storeSession):
        """Add a artwork to the index"""

    def update(artwork, storeSession):
        """Update the artwork in the index"""

    def remove(id):
        """Remove a artwork from the index"""

    def getMatchingIds(keyWords):
        """Return either None or a sequence (possibly empty) of artwork ids that match the keyWords"""

class NullArtworkIndexer(object):
    implements(IArtworkIndexer)

    def __init__(self, *a, **kw):
        pass

    def add(self, artwork, storeSession):
        return defer.succeed(artwork)

    def update(self, artwork, storeSession):
        return defer.succeed(artwork)

    def remove(self, id):
        return defer.succeed(id)

    def getMatchingIds(self, keyWords):
        return defer.succeed(None)

try:
    import hype

    class AdminArtworkIndexer(object):
        implements(IArtworkIndexer)

        """Indexer for the admin site artwork index."""

        def __init__(self, path):
            self.path = path

        def add(self, artwork, storeSession):
            def gotDoc(doc):
                db = self._openDatabase()
                try:
                    db.put_doc(doc)
                finally:
                    self._closeDatabase(db)

            d = self._toHypeDocument(artwork, storeSession)
            d.addCallback(gotDoc)
            d.addCallback(lambda ignore: artwork)
            return d


        def update(self, artwork, storeSession):
            def gotDoc(doc):
                db = self._openDatabase()
                try:
                    try:
                        orig_doc = db.get_doc_by_uri(doc['@uri'])
                        if orig_doc is not None:
                            db.remove(orig_doc)
                    except hype.DBRemoveError, e:
                        print e

                    db.put_doc(doc)
                finally:
                    self._closeDatabase(db)

            d = self._toHypeDocument(artwork, storeSession)
            d.addCallback(gotDoc)
            d.addCallback(lambda ignore: artwork)
            return d


        def remove(self, id):
            db = self._openDatabase()
            try:
                doc = hype.Document()
                doc['@uri'] = unicode(id)

                try:
                    doc = db.get_doc_by_uri(doc['@uri'])
                    if doc is not None:
                        db.remove(doc)
                except hype.DBRemoveError, e:
                    print e
            finally:
                self._closeDatabase(db)

            return defer.succeed(id)

        def _toHypeDocument(self, artwork, storeSession):


            doc = hype.Document()
            doc['@uri'] = unicode(artwork.id)

            for attr in ('shortDescription', 'description', 'material', 'title', 'metaKeywords'):
                value = getattr(artwork, attr, '')
                doc.add_text(unicode(value))
            # Need to map artist and categories

            d = self._getCategories(artwork, storeSession, doc)
            d.addCallback(lambda ignore: self._getArtistTitle(artwork, storeSession, doc))
            d.addCallback(lambda ignore: doc)
            return d


        def _getCategories(self, artwork, storeSession, doc):

            if not artwork.categories:
                return defer.succeed(None)

            where = ["%s" for i in range(len(artwork.categories))]
            params = [c for c in artwork.categories]

            sql = """select label from categories where path in (""" + ', '.join(where) + """)"""

            def gotRows(rows):
                for r in rows:
                    doc.add_text(unicode(r[0]))

            d = storeSession.curs.execute(sql, tuple(params))
            d.addCallback(lambda ignore: storeSession.curs.fetchall())
            d.addCallback(gotRows)
            return d

        
        def _getArtistTitle(self, artwork, storeSession, doc):

            attrNames = ['id', 'version', 'type', 'ctime', 'mtime', 'olcount', 'attrs']

            def gotItem(row):
                if not row:
                    return defer.succeed(None)

                id, version, type, ctime, mtime, olcount, attrs = row

                item = storeSession.reconstituteItem(dict(zip(attrNames,
                                  [id, version, type, ctime, mtime, olcount, attrs])))
                title = item.title
                for k, v in title.iteritems():
                    doc.add_text(unicode(v))

            sql = """
                select %(attrs)s
                from item 
                where
                    id = %(artist_id)s
                    and version = 
                        (select max(version) from item where id = %(artist_id)s)"""

            params = {'attrs':', '.join(attrNames), 'artist_id': artwork.artist}

            d =  storeSession.curs.execute(sql%params)
            d.addCallback(lambda ignore: storeSession.curs.fetchone())
            d.addCallback(gotItem)
            return d
            

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

            return defer.succeed(rv)

        def _queryDatabase(self, keyWords):
            rv = []
            db = self._openDatabase()
            try:
                res = db.search(unicode(keyWords), simple=True)
                rv = [int(d['@uri']) for d in res]
            finally:
                self._closeDatabase(db)

            return rv

    class PublicArtworkIndexer(AdminArtworkIndexer):

        """Specialization of the Admin site artwork indexer for the
           public site."""

        def update(self, artwork, storeSession):
            def gotDoc(doc):
                db = self._openDatabase()
                try:

                    try:
                        orig_doc = db.get_doc_by_uri(doc['@uri'])
                        if orig_doc is not None:
                            db.remove(orig_doc)
                    except hype.DBRemoveError, e:
                        print e

                    if artwork.show:
                        db.put_doc(doc)
                finally:
                    self._closeDatabase(db)

            d = self._toHypeDocument(artwork, storeSession)
            d.addCallback(gotDoc)
            d.addCallback(lambda ignore: artwork)
            return d

except ImportError:

    class AdminArtworkIndexer(NullArtworkIndexer):
        pass

    class PublicArtworkIndexer(NullArtworkIndexer):
        pass


class ArtworkIndexer(object):
    implements(IArtworkIndexer)

    """This wraps the indexers for both the admin artwork index and
       public artwork index, it forwards method calls to the individual 
       indexers."""

    def __init__(self, adminPath, publicPath):
        self.admin = AdminArtworkIndexer(adminPath)
        self.public = PublicArtworkIndexer(publicPath)

    def setApplication(self, application):
        self.application = application

    def add(self, artwork, storeSession):
        d = self.admin.add(artwork, storeSession)
        d.addCallback(self.public.add, storeSession)
        return d

    def update(self, artwork, storeSession):
        d = self.admin.update(artwork, storeSession)
        d.addCallback(self.public.update, storeSession)
        return d

    def remove(self, id):
        d = self.admin.remove(id)
        d.addCallback(self.public.remove)
        return d

    def getMatchingIds(self, keyWords):
        return self.admin.getMatchingIds(keyWords)



