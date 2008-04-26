from zope.interface import implements
from twisted.internet import defer
from cms.contentitem import DefaultContentEditor, populateFormFromPlugin
from cms import icms
import formal as forms
from formal import iformal as iforms
from tub.web import util

def storeFile(sess, fileId, id, version, name, fileTuple):

    def addNewFile():
        d = sess.curs.execute("""
            insert into file
                (id, version, name, mime_type, file_name, data)
            values
                (%s, %s, %s, %s, %s, %s)""",
            (id, version, name, fileTuple[0], fileTuple[2], buffer(fileTuple[1])))
        d.addCallback(lambda ignore: getId())
        return d

    def getId():
        def gotRow(row):
            return row[0]

        d = sess.curs.execute("""
            select currval('file_id_sequence')
            """)
        d.addCallback(lambda ignore: sess.curs.fetchone())
        d.addCallback(gotRow)
        return d

    def updateExistingFile():
        def orInsert(row):
            if sess.curs.rowcount != 1:
                return addNewFile()
            else:
                return defer.succeed(fileId)

        d = sess.curs.execute("""
            update file
                set id=%s, version=%s, name=%s, mime_type=%s, file_name=%s, data=%s
            where file_id=%s and version=%s""",
            (id, version, name, fileTuple[0], fileTuple[2], buffer(fileTuple[1]), fileId, version))
        d.addCallback(orInsert)
        return d
        
    if fileId:
        d = updateExistingFile()
        return d
    else:
        d = addNewFile()
        return d



def deleteFile(sess, id, version, name):
    d = sess.curs.execute("""
        delete from file where id = %s and version = %s and name=%s
        """,
        (id, version, name))
    return d



def getFile(sess, fileId):

    def gotFile(row):
        return (row[1], str(row[2]), row[0])

    d = sess.curs.execute("""
        select 
            file_name, mime_type, data
        from file
        where 
            file_id = %s""",
        (fileId, ))
    d.addCallback(lambda ignore: sess.curs.fetchone())
    d.addCallback(gotFile)
    return d


class KeyToFileConverter( object ):
    implements( iforms.IFileConvertible )

    def __init__(self, original=None):
        pass

    def fromType( self, value, context = None ):
        pass

    def toType( self, value ):

        if value == None:
            return None

        data = value[1].read()
        return ( value[0], data, value[2] )

class ContentEditor( DefaultContentEditor ):
    implements( icms.IContentEditor )

    assetNames = []

    def getForm(self, ctx, language, plugin, immutable):

        form = DefaultContentEditor.getForm(self, ctx, language, plugin, immutable)
        self.updateFormAssets(plugin, form)
        return form

    def updateFormAssets(self, plugin, form):
        def addSize(u):
            u = u.add('size', '160x120')
            u = u.add('nocache', 1)
            return u

        # Map to a key for the file upload widget
        # Make a URL for the asset preview, no bigger than 160x120
        targetUrlWithVersion = plugin.application.services.getService(plugin.assetServiceName).getURLForAsset(self.original)

        for assetName in self.assetNames:
            form.data[assetName] = addSize(targetUrlWithVersion.child(assetName))

    @defer.deferredGenerator
    def saveAttributes(self, ctx, form, data, language):

        # Copy the original file back if no new file is specified
        for assetName in self.assetNames:
            fileId = getattr(self.original, assetName, None)
            if data.get(assetName) is None:
                data[assetName] = fileId
            else:
                # Store data in external table
                storeSession = util.getStoreSession(ctx)
                d = storeFile(storeSession, fileId, 
                    self.original.id, self.original.version, 
                    assetName, data[assetName])
                d = defer.waitForDeferred(d)
                yield d
                fileId = d.getResult()
                data[assetName] = fileId

        d = DefaultContentEditor.saveAttributes(self, ctx, form, data, language)
        d = defer.waitForDeferred(d)
        yield d
        yield d.getResult()

class AssetDataProvider(object):
    """
    Adapter that allows the imaging service to look inside to get the default
    asset.
    """
    implements(icms.IAssetDataProvider)

    defaultAssetName = None

    def __init__(self, original):
        self.original = original

    def provideData(self, avatar, storeSession, assetName, langs):
        # Get data from external table
        assetName = assetName or self.defaultAssetName
        if assetName is None:
            raise KeyError()
        attrs = self.original.getAttributeValues(langs[0], langs[1:])
        fileId = attrs[assetName] 
        if not fileId:
            raise KeyError()
        d = getFile(storeSession, fileId)
        d.addCallback(lambda data: data[:2])
        return d
