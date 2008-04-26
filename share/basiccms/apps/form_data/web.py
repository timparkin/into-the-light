import csv
import mimetypes
from cStringIO import StringIO
import pkg_resources

from zope.interface import implements
from twisted.internet import defer
from nevow import loaders, url

from pollen.nevow.tabular import cellrenderers, itabular, tabular
from pollen import csvutil

from tub.web import page, util

from basiccms import formpage



def loader(filename):
    return loaders.xmlfile(util.resource_filename('basiccms.apps.form_data.templates',
        filename), ignoreDocType=True)



class FormDataPage(page.Page):
    """Page used for editing base delivery charges"""

    componentContent = loader('FormData.html')


    def __init__(self, application, storeSession):
        super(FormDataPage, self).__init__()
        self.application = application
        self.storeSession = storeSession


    def data_forms(self, ctx, data):

        def formsFactory():
            def _(**kw):
                return self.storeSession.getItems(itemType=formpage.FormPage)
            return _

        return FormsModel(formsFactory())


    def render_forms(self, ctx, model):
        """
        Create a tabular view of the forms.
        """
        # Create a link renderer to click to the Sale instance.
        linkRenderer = cellrenderers.LinkRenderer(url.here, 'id')
        # Create the view
        view = tabular.TabularView('forms', model, 20)
        view.columns.append(tabular.Column('name', 'name', linkRenderer))
        return view


    def childFactory(self, ctx, name):


        def getForm(id):
            return self.storeSession.getItemById(id)

        def getFormData(item):
            return self.storeSession.getItems(where="""
                id in (select id from cms_form_data
                    where form_id = %(form_id)s)
                """,
                params = {'form_id':item.id},
                orderBy="ctime" )

        def buildCSV(formItem, items):

            items = list(items)
            keys = set()
            map(lambda item: keys.update(item.data.keys()), items)
            keys = ['ctime'] + list(keys)
            
            def genRows():

                # Headers
                yield dict([(k,k) for k in keys])

                # Answer set
                for item in items:
                    rv = {}
                    rv.update( dict([(key,item.data.get(key,'') or '') for key in keys]) )
                    rv['ctime'] = str(item.ctime)
                    yield rv

            buf = StringIO()
            writer = csv.DictWriter(buf, keys)
            writer.writerows(csvutil.encodeDictFilter(genRows()))
            buf.flush()

            from nevow import inevow, static
            filename=str('%s_data.csv'%formItem.name)
            inevow.IRequest(ctx).setHeader('Cache-Control',
                    'no-cache, must-revalidate, no-store')
            inevow.IRequest(ctx).setHeader('Content-disposition',
                    'attachement ; filename=%s'%filename)
            return static.Data(buf.getvalue(), mimetypes.guess_type(filename)[0])
            

        try:
            id = int(name)
        except:
            return None

        d = defer.succeed(id)
        d.addCallback(getForm)
        d.addCallback(lambda formItem: getFormData(formItem).addCallback(
            lambda items: buildCSV(formItem, items)))
        return d


    def generateAnswersCSV(self, ctx, name):

        def gotAnswers(answers):

            questionnaire, questions = csvpack.parse(self.questionnaire._CSVPackDir())
            keys = [n[-1].fullKey for n in questionnaire.walk() if n[-1].isQuestion()]

            def genRows():

                # Headers
                yield dict([(k,k) for k in keys])

                # Answer set
                for answer in answers:
                    yield dict([(key,answer.answers.get(key,'') or '') for key in keys])

            buf = StringIO()
            writer = csv.DictWriter(buf, keys)
            writer.writerows(csvutil.encodeDictFilter(genRows()))
            buf.flush()

            from nevow import inevow, static
            inevow.IRequest(ctx).setHeader('Cache-Control',
                    'no-cache, must-revalidate, no-store')
            return static.Data(buf.getvalue(), mimetypes.guess_type(name)[0])

        d = self.questionnaire.getAnswers()
        d.addCallback(gotAnswers)
        return d




class FormsModel(object):

    implements(itabular.IModel)

    attributes = {
        'id': tabular.Attribute(),
        'name': tabular.Attribute(),
        }


    def __init__(self, itemsFactory):
        self.itemsFactory = itemsFactory
        self._cache = None


    def setOrder(self, attribute, direction):
        raise NotImplemented()


    def getItemCount(self):
        d = self._getItems()
        d.addCallback(lambda items: len(items))
        return d


    def getItems(self, start, end):
        d = self._getItems()
        d.addCallback(lambda items: items[start:end])
        return d


    def _getItems(self):
        if self._cache is not None:
            return defer.succeed(self._cache)

        def itemToDict(item):

            data = {
                'id': item.id,
                'name': item.name,
                }
            return data

        def cacheAndReturn(items):
            self._cache = map(itemToDict, items)
            return self._cache

        d = self.itemsFactory()
        d.addCallback(cacheAndReturn)
        return d

