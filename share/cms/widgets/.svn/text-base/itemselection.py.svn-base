from datetime import date
import zope.interface as zi
from twisted.cred import portal
from twisted.internet import defer
from twisted.python import components, reflect
from nevow import appserver, inevow, rend, tags as T
from cms import icms
from tub import itub
from tub.web import categorieswidget, util
import formal as forms
from formal import converters, types
from formal import iformal as iforms
from formal.util import keytocssid
from crux import icrux


TYPES_SEP='!'

def loader(filename):
    """
    Load a template from this package's templates directory.
    """
    return util.PackageTemplate('cms.templates',
            filename, ignoreDocType=True)

class IItemSelection(zi.Interface):
    """Item selection interface.
    """
    type = zi.Attribute('Type of Item')
    categories = zi.Attribute('List of categories to filter items')
    maxPublishedAge = zi.Attribute('Maximum age of published items in days')
    maxItems = zi.Attribute('Maximum number of items to display')
    order = zi.Attribute('List of (attribute, direction) tuples to sort on')
    template = zi.Attribute('An indication of how to render the items')
    paging = zi.Attribute('Number of items per page')
    name = zi.Attribute('Identifies a single item to select by name')
    id = zi.Attribute('Identifies a single item to select; type, categories, maxPublishedAge, maxItems are ignored')



def encodeTypes(types):
    return TYPES_SEP.join([t.__typename__ for t in types])



def decodeTypes(types):
    return types.split(TYPES_SEP)



def encodeDate(v):
    if v is None:
        return ''
    return v.isoformat()


def decodeDate(v):
    if not v:
        return None
    return date(*map(int, v.split('-')))


_codecs = {
    'type':            (lambda v: v,           lambda v: v),
    'categories':      (lambda v: ','.join(v), lambda v: v.split(',')),
    'maxPublishedAge': (lambda v: str(v),      lambda v: int(v)),
    'maxItems':        (lambda v: str(v),      lambda v: int(v)),
    'order':           (lambda v: v,           lambda v: v),
    'template':        (lambda v: v,           lambda v: v),
    'paging':          (lambda v: str(v),      lambda v: int(v)),
    'id':              (lambda v: str(v),      lambda v: int(v)),
    'name':            (lambda v: v,      lambda v: v),
    }


class ItemSelection(object):
    """Item selection type.
    """
    zi.implements(IItemSelection)

    def __init__(self, type=None, categories=None, maxPublishedAge=None, order=None, 
        maxItems=None, template=None, paging=None, id=None, name=None):

        self.type = type
        if categories is not None:
            self.categories = categories
        else:
            self.categories = []
        self.maxPublishedAge = maxPublishedAge
        self.maxItems = maxItems
        self.order = order
        self.template = template
        self.paging = paging
        self.id = id
        self.name = name

    def toString(self):
        result = []
        for name, value in self.__dict__.iteritems():
            if value is None:
                continue
            result.append('%s=%s'%(name,_codecs[name][0](value)))
        return ';'.join(result)

    @classmethod
    def fromString(cls, s):
        s = s.strip()
        if not s:
            return cls()
        kw = {}
        for name, value in [kv.split('=') for kv in s.split(';')]:
            kw[name] = _codecs[name][1](value)
        return cls(**kw)


class ItemSelectionType(forms.types.Type):
    pass


class ItemSelectionWidget(object):
    zi.implements(iforms.IWidget)

    def __init__(self, original, types=None):
        self.original = original
        if types is None:
            self.types = ""
        else:
            self.types = TYPES_SEP.join([t.__typename__ for t in types])
        

    def render(self, ctx, key, args, errors):
        if errors:
            value = args.get(key, [''])[0]
            itemsel = ItemSelection.fromString(value)
        else:
            itemsel = args.get(key)
            if itemsel is not None:
                value = itemsel.toString()
            else:
                value = ''
        return T.div[
            T.div(id="%s-description"%keytocssid(ctx.key))[self.renderDescriptiveText(itemsel)],
            T.input(type='hidden', name=key, id=keytocssid(ctx.key), value=value),
            T.button(onclick='return Cms.Forms.ItemSelection.popup("%s","%s")'%(keytocssid(ctx.key),self.types))['Choose items ...']
            ]


    def renderImmutable(self, ctx, key, args, errors):
        if errors:
            value = args.get(key, [''])[0]
            itemsel = ItemSelection.fromString(value)
        else:
            itemsel = args.get(key)
            if itemsel is not None:
                value = itemsel.toString()
            else:
                value = ''
        return T.div(id="%s-description"%keytocssid(ctx.key))[
            self.renderDescriptiveText(itemsel)
            ]


    def renderDescriptiveText(self, itemsel):
        if itemsel is None:
            return ''
        return inevow.IRenderer(itemsel)


    def processInput(self, ctx, key, args):
        value = args.get(key, [None])[0] or None
        if value is not None:
            value = ItemSelection.fromString(value)
        return self.original.validate(value)



class ItemSelectionRenderer(object):
    zi.implements(inevow.IRenderer)

    def __init__(self, itemsel):
        self.itemsel = itemsel

    def rend(self, ctx, data):
        itemsel = self.itemsel
        if itemsel.type is not None:
            yield T.strong['Type: ']
            yield itemsel.type.split('.')[-1]
            yield T.br
        if itemsel.categories and itemsel.categories is not None:
            yield T.strong['Categories: ']
            categories = [[category, ', '] for category in itemsel.categories]
            del categories[-1][1]
            yield categories
            #type=None, categories=None, maxPublishedAge=None, order=None, maxItems=None


components.registerAdapter(ItemSelectionRenderer, ItemSelection, inevow.IRenderer)



class ItemSelectionResource(forms.ResourceMixin, rend.Page):
    """Main item selection popup (the page with the form).

    I present a form for the user to fill in and, once the form is valid, I
    send the selection back to the calling page using a ItemWidgetUpdateResource
    resource.
    """

    docFactory = loader('ItemSelectionPopup.html')

    def __init__(self, application):
        rend.Page.__init__(self)
        forms.ResourceMixin.__init__(self)
        self.application = application


    def form_itemSelection(self, ctx):

        # Get the element id of the field to update from the request params.
        # We'll store it in a hidden field for the POST to use.
        elementId = ctx.arg("element_id")

        # Set up the form
        f = forms.Form(self._submit)

        f.addField('type', forms.String(), forms.widgetFactory(forms.SelectChoice, noneOption=None, options=self.data_types))
        f.addField('name', forms.String())
        f.addField('categories', forms.Sequence(forms.Integer()), forms.widgetFactory(categorieswidget.CheckboxTreeMultichoice))
        f.addField('maxPublishedAge', forms.Integer())
        f.addField('maxItems', forms.Integer())
        f.addField('paging', forms.Integer(), label="Items per page")
        f.addField('template', forms.String(), forms.widgetFactory(forms.SelectChoice, noneOption=None, options=[]))
        f.addField('elementId', forms.String(), widgetFactory=forms.Hidden)

        f.addAction(self._submit)
        # If we have a value request parameter then decode it and set the
        # form's initial values.
        value = inevow.IRequest(ctx).args.get('value', [None])[0]
        f.data = {"elementId": elementId}
        if value is not None:
            itemsel = ItemSelection.fromString(value)
            f.data['type'] = itemsel.type
            f.data['name'] = itemsel.name
            f.data['categories'] = itemsel.categories
            f.data['maxPublishedAge'] = itemsel.maxPublishedAge
            f.data['maxItems'] = itemsel.maxItems
            f.data['template'] = itemsel.template
            f.data['paging'] = itemsel.paging
        return f


    def _typesList(self,ctx):
        types = ctx.arg("types")

        # Restrict types in the list to the specified types
        if types is None:
            typesToList = [p for p in self.application.contentTypes if p.listable]
        else:
            types = decodeTypes(types)
            typesToList = [p for p in self.application.contentTypes if p.contentItemClass.__typename__ in types]

        return typesToList


    def data_types(self, ctx, data):
        
        for plugin in self._typesList(ctx):
            yield plugin.contentItemClass.__typename__, plugin.description
            

    def _submit(self, ctx, form, data):
        # The submit button is javascripted away.
        # It is the javascript that updates that opening form.
        pass

    
    def render_item_template_js(self, ctx, data):
        html = T.script(type="text/javascript", language="javascript" )

        js = """function getTemplates(plugin) {
                %(pluginTemplates)s
            }
            """

        fragment = """ if(plugin == "%(plugin)s") {
                return new Array(%(templates)s);
            }
            """

        fragments = []

        for plugin in self._typesList(ctx):
            templates = ','.join( ['["%s","%s"]'%(t[0],t[1]) for t in plugin.listTemplates])
            fragments.append(fragment%{'plugin':plugin.contentItemClass.__typename__,
                'templates':templates})

        fragments.append( """ { return new Array(); } """)

        pluginTemplates = ' else '.join(fragments)
        js = js%{'pluginTemplates': pluginTemplates}
        return html[T.xml(js)]
        


components.registerAdapter(ItemSelectionWidget, ItemSelectionType, iforms.IWidget)



class ItemSelectionGettable(object):
    """
    Adapter to convert ItemSelection instances left in the stan tree into a
    list of items.
    """
    zi.implements(inevow.IGettable)

    def __init__(self, original):
        self.original = original

    def get(self, ctx):
        # Get bits we need from the context
        avatar = ctx.locate(icrux.IAvatar)
        sess = util.getStoreSession(ctx)

        # Is this for a single item?
        if self.original.id:
            return avatar.realm.cmsService.getContentManager(avatar).publicFindById(sess, self.original.id)

        # Determine the item type we are retrieving
        itemType = self.original.type
        if itemType is not None:
            itemType = sess.store.registry.typeWithName(itemType)
        where = []
        params = {}
        # Add categories to where, if any
        categories = [c for c in self.original.categories if c]
        if categories is not None:
            for i, category in enumerate(categories):
                marker = 'cat%s'%i
                where.append('categories <@ %%(%s)s'%marker)
                params[marker] = category
        if self.original.name:
            where.append('name=%(name)s')
            params['name'] = self.original.name
        if where:
            where = ' and '.join(where)
        else:
            where = None
        return avatar.realm.cmsService.getContentManager(avatar).publicFindManyContentItems(sess, itemType=itemType, where=where, params=params)


components.registerAdapter(ItemSelectionGettable, ItemSelection, inevow.IGettable)


