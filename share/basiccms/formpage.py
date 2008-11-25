import csv
from cStringIO import StringIO
from twisted.internet import defer
from poop import objstore
import formal as forms
from cms.contentitem import Attribute, PagishBase, PagishPluginBase
from cms.contentindex import IndexDefinition
from cms.widgets import richtextarea
from pollen import csvutil
from basiccms import fragment, news
parsers = [('markdown','MarkDown'),('xhtml','XHTML'),('plain','Plain Text')]


FORMPAGE_PLUGIN_ID = 'cms/form-page'



class FormPage(PagishBase):

    attributes = [
        Attribute('title', forms.String(required=True)),
        Attribute('shortDescription', forms.String(required=True),
            widgetFactory=forms.TextArea),
        Attribute('body', forms.RichTextType(required=True),
            widgetFactory=forms.widgetFactory(richtextarea.RichTextArea, parsers=parsers,itemTypes=[fragment.Fragment,news.NewsItem]),
            classes=['imagepicker','preview','itemselector'],
            ),
        Attribute('formDefinition', forms.String(required=True),
            widgetFactory=forms.TextArea),
        Attribute('sendToEmail', forms.String()),
        Attribute('submitterEmailFieldName', forms.String(strip=True)),
        Attribute('storeData', forms.Boolean()),
        Attribute('humanCheck', forms.Boolean()),
        Attribute('submittedBody', forms.RichTextType(required=True),
            widgetFactory=forms.widgetFactory(richtextarea.RichTextArea, parsers=parsers,itemTypes=[fragment.Fragment,news.NewsItem]),
            classes=['imagepicker','preview','itemselector'],
            ),
        ]

    contentIndex = IndexDefinition('title', 'shortDescription', 'body')

    capabilityObjectId = FORMPAGE_PLUGIN_ID

    resourceIds = (FORMPAGE_PLUGIN_ID,)

            
    def getParsedFormDefinition(self):
        stream = StringIO(self.formDefinition.encode("utf-8"))
        dialect = csvutil.guessCSVDialect(stream, numCols=6)
        reader = csv.reader(stream, dialect=dialect)
        reader = csvutil.decodeFilter(reader)
        formDefinition = []
        for row in reader:
            name,label,type,widget,required,options = row
            options = self.parseOptions(options)
            formDefinition.append({
                    'name':name, 
                    'label':label,
                    'type':type,
                    'widget':widget,
                    'required':required,
                    'options':options,
                })
        return formDefinition


    def parseOptions(self, options):
        if ':' in options:
            options = options.split(':')
            values = []
            for option in options:
                try:
                    k,v = option.split('=', 1)
                except ValueError:
                    print "Failed to split %r as an option" % (option,)
                    continue
                values.append( (k,v) )
            return values
        else:
            return options


    def storeSubmittedData(self, storeSession, data):
        return storeSession.createItem(SubmittedFormData, form=self, data=data)



class SubmittedFormData(objstore.Item):

    __typename__ = 'cms/form_data'
    __table__ = 'cms_form_data'
    formId = objstore.column('form_id')
    formVersion = objstore.column('form_version')

    def __init__(self, *a, **k):
        form = k.pop('form')
        data = k.pop('data')
        super(SubmittedFormData, self).__init__(*a, **k)
        self.formId = form.id
        self.formVersion = form.version
        self.data = data



class FormPagePlugin(PagishPluginBase):

    name = 'Form Page'
    contentItemClass = FormPage
    description = 'Form Page'
    id = FORMPAGE_PLUGIN_ID    

