from cStringIO import StringIO
import syck
import email.Utils
from zope.interface import Interface
from twisted.internet import defer
from nevow import inevow, url, tags as T, flat, stan
from crux import skin, icrux
import formal
from notification import inotification
from tub.public.web import common as tubcommon
from tub.web import util
from cms.widgets.itemselection import ItemSelection
from cms import fragment, fragmenttype
from basiccms import formpage, news, page, gallery
from basiccms.web import common, rest
import yamlRegistry as Y
from twisted.internet.defer import returnValue
from random import shuffle

def parseTemplateString(template):
    """
    Parse the template string returning a list of positional args and a
    dict of keyword args.

    The string is assumed to be something vaguely like that used when
    calling a Python function, only this is more lenient and less powerful.
    """
    # Short-circuit if nothing useful passed in
    if template is None:
        return [], {}
    # Convenience function
    stripper = lambda s: s.strip()
    # Split on comma and remove whitespace
    template = map(stripper, template.split(","))
    # Extract the args
    args = [part for part in template if "=" not in part]
    # Extract the kwargs
    kwargs = [part for part in template if "=" in part]
    kwargs = [part.split("=", 1) for part in kwargs]
    kwargs = [map(stripper, part) for part in kwargs]
    kwargs = dict(kwargs)
    # Return the final result
    return args, kwargs



class PageResource(common.PagingMixin,common.CMSResource):

    docFactory = skin.loader("Page.html")

    def __init__(self, *a, **k):
        super(PageResource, self).__init__(*a, **k)
        self.setTemplate(*parseTemplateString(getattr(self.original, "template", None)))

    def renderHTTP(self,ctx):
        args, kwargs = self.getExtraData(ctx)['template']
        if len(args) == 0:
            self.docFactory = skin.loader("Page.html")
        else:
            self.docFactory = skin.loader("Page-%s.html" % (args[0],))
        return super(PageResource,self).renderHTTP(ctx)

    def setTemplate(self, args, kwargs):
        if args:
            self.docFactory = skin.loader("Page-%s.html" % (args[0],))

    def render_admin(self,ctx,data):
        if common.isAdminOn(ctx):
            return T.div(id='admin')[ T.a(href=url.URL.fromString('http://admin.dw.timparkin.co.uk:8131/Pages/%s'%self.original.id))[ 'Click here to edit page content' ] ]
        else:
            return ''

    def childFactory(self, ctx, name):
        # Handle the case when this is a news page and am asked
        # to resolve a news Item.
        try:
            id = int(name)
        except ValueError:
            return None

        def gotItem(item):
            if not item:
                return None
            try:
                return inevow.IResource(item)
            except:
                return None

        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        d = avatar.realm.cmsService.getItem(storeSession, avatar, id=id)
        d.addCallback(gotItem)
        return d

    @defer.inlineCallbacks
    def data_products(self,ctx,data):
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        items = yield avatar.realm.cmsService.getItems(storeSession, avatar, type=gallery.GalleryItem)
        products = yield avatar.getProducts(storeSession, categorisationFilters=[('flags','homepage')])
        shuffle(products)
        for cnt,p in enumerate(products):
            setattr(p,'cnt',cnt)
            setattr(p,'modcnt',cnt%3)
            setattr(p,'divcnt',cnt//3)
        defer.returnValue(products[:3])
        
        
    def render_product(self,ctx,data):
        def getUrlForImage(image):
            categories = image.categories
            galleryCategories = [gallery for gallery in categories if gallery.startswith('gallery.')]
            if len(galleryCategories) == 0:
                return '#'
            firstCategory = galleryCategories[0].split('.')[1]
            return '/gallery/%s/%s'%(firstCategory,image.code)
            
        name=data.code
        title = data.title
        shortDescription = data.summary
        imgsrc='/system/ecommerce/%s/mainImage?size=300x383&sharpen=1.0x0.5%%2b0.8%%2b0.1'%data.id
        
        ctx.tag.fillSlots('url',url.URL.fromString(getUrlForImage(data)))
        ctx.tag.fillSlots('title',data.title)
        ctx.tag.fillSlots('shortDescription',shortDescription)
        ctx.tag.fillSlots('imgsrc',imgsrc)
        ctx.tag.fillSlots('cnt',data.cnt)
        ctx.tag.fillSlots('modcnt',data.modcnt)
        ctx.tag.fillSlots('divcnt',data.divcnt)        
        return ctx.tag   
    
    def render_extraData(self, param):
        
        def renderer(self, ctx, data):
            extraData = self.getExtraData(ctx)
            if not extraData:
                return ''
            value = extraData.get(param,'')
            return value

        return renderer


    def _parseYAML(self, yaml):
        f = StringIO(yaml.encode('utf8'))
        rv = syck.load(f,Loader=Y.Loader,implicit_typing=False)
        return rv


class FormPageResource(formal.ResourceMixin, common.CMSResource):

    docFactory = skin.loader("FormPage.html")


    def __init__(self, *a, **k):
        super(FormPageResource, self).__init__(*a, **k)
        self.setTemplate(*parseTemplateString(getattr(self.original, "template", None)))


    def setTemplate(self, args, kwargs):
        if args:
            self.docFactory = skin.loader("FormPage-%s.html" % (args[0],))


    def render_view(self, ctx, data):
        """
        Choose the form or submitted view, depending on the state of the
        resource.
        """
        if ctx.arg("submitted"):
            pattern = "submitted"
        else:
            pattern = "form"
        return ctx.tag.onePattern(pattern)


    def form_form(self,ctx):
        form = formal.Form()
        for field in self.original.getParsedFormDefinition():

            # Parse the required
            if field['required'] == 'True':
                required = True
            else:
                required = False
                
            # Map the field's type to a formal type.
            try:
                fieldType = field['type']
                if fieldType.startswith('Sequence/'):
                    fieldType = fieldType.split('/',1)[1]
                    fieldType = formal.Sequence(getattr(formal, fieldType)(), required=required)
                else:
                    fieldType = getattr(formal, fieldType)(required=required)
            except AttributeError:
                fieldType = None

            # Skip if we don't know the type or widget.
            if not fieldType or not hasattr(formal,field['widget']):
                continue

            # Build the widget
            if field['widget'] == 'Checkbox':
                form.addField(field['name'], fieldType, label=field['options'],widgetFactory=getattr(formal,field['widget']))
            elif not field['widget'].startswith('Select') and not field['widget'].startswith('Radio') and field['widget'] != 'CheckboxMultiChoice':
                form.addField(field['name'], fieldType, label=field['label'], widgetFactory=getattr(formal,field['widget']))
            else:
                form.addField(field['name'], fieldType, label=field['label'], widgetFactory=formal.widgetFactory(getattr(formal,field['widget']),options=field['options']))
            if field['widget'] == 'Hidden':
                form.data[field['name']] = field['options']
        form.addAction(self._submit)
        return form          
 

    def _submit(self,ctx,form,data):

        def handleErrors(ignore):
            # Report a likely error
            log.err(ignore)
            raise formal.FormError('There was an error with the email addresses')

        def sendToEmail():
            emails = self.original.sendToEmail
            if not emails:
                return defer.succeed(None)
            toAddresses = [e.strip() for e in emails.split(",")]
            return self.sendFormResults(toAddresses, subject, data, formDefinition)

        def sendToSubmitter():
            emailFieldName = self.original.submitterEmailFieldName
            if not emailFieldName:
                return defer.succeed(None)
            email = data.get(emailFieldName, None)
            if not email:
                return defer.succeed(None)
            return self.sendFormResults([email], subject, data, formDefinition)

        def store():
            if not self.original.storeData:
                return defer.succeed(None)
            storeSession = tubcommon.getStoreSession(ctx)
            return self.original.storeSubmittedData(storeSession, data)

        formDefinition = self.original.getParsedFormDefinition()
        subject = self.original.title

        # Convert sequences to comma-delimited string
        for field in self.original.getParsedFormDefinition():
            if field['type'].startswith('Sequence/'):
                data[field['name']] = ', '.join(data.get(field['name']) or [])

        d = defer.succeed(None)
        d.addCallback(lambda ignore: sendToEmail())
        d.addCallback(lambda ignore: sendToSubmitter())
        d.addCallback(lambda ignore: store())
        d.addCallback(lambda ignore: url.URL.fromContext(ctx).add('submitted', 1) )
        return d


    def sendFormResults(self, toAddresses, subject, formData, formDefinition):
        # get notificaton service
        notificationService = inotification.INotificationService(self.avatar.realm)
        # Build Args
        args = {'data':[]}
        for field in self.original.getParsedFormDefinition():
            fieldvalue = formData.get(field['name'], None)
            args['data'].append( {'key':field['name'],'value':fieldvalue} )           

        # Build the email message
        headers = {
                "To": ','.join(toAddresses),
                "Subject": subject,
                "Date": email.Utils.formatdate(),
                }
        msg = notificationService.buildEmailFromTemplate(
                "FormPage", args, headers)

        # Send it off
        return notificationService.sendEmail(toAddresses, msg)



class NewsItemResource(common.CMSResource):

    docFactory = skin.loader("NewsItem.html")


    def __init__(self, *a, **k):
        super(NewsItemResource, self).__init__(*a, **k)
        self.setTemplate(*parseTemplateString(getattr(self.original, "template", None)))


    def setTemplate(self, args, kwargs):
        if len(args) > 0:
            self.docFactory = skin.loader("NewsItem-%s.html" % (args[0],))




class FragmentResource(common.CMSResource):

    docFactory = skin.loader("Fragment.html")




    def render_extraData(self, param):
        
        def renderer(self, ctx, data):
            extraData = self.original.getExtraDataAttributeValue('extraData', 'en')
            if not extraData:
                return ''
            value = self._parseYAML(extraData).get(param,'')
            return value

        return renderer


    def _parseYAML(self, yaml):
        f = StringIO(yaml.encode('utf8'))
        rv = syck.load(f,Loader=Y.Loader,implicit_typing=False)
        return rv
    
    @defer.inlineCallbacks
    def render_fragmentTemplate(self,ctx,data):
        sess = util.getStoreSession(ctx)
        items = yield sess.getItems(fragmenttype.FragmentType)
        for item in items:
            if item.name == self.original.protectedObject.type:
                fragmentType = item
                break
        template = fragmentType.template
        from genshi.template import NewTextTemplate as TextTemplate
        tmpl = TextTemplate(fragmentType.template)
        output = tmpl.generate(**self.original.protectedObject.data)
        returnValue(T.xml(output.render('text')))
  

#
# Flatteners adaption for different item types
#

def RestFlattener(original,ctx):
    return rest.str2ReSTFragment(original)

def HtmlFlattener(original,ctx):
    return T.xml(original)

def CmsItemSelFlattener(original,ctx):
    def gotData(data, ctx):
        if hasattr(data, 'sort'):
            data.sort(key=lambda i: i.date, reverse=True)
        resource = inevow.IResource(data)
        #if itemsel.template is not None and hasattr(resource, 'setTemplate'): 
            #resource.setTemplate(*parseTemplateString(itemsel.template))
        return resource

    itemsel = ItemSelection.fromString(str(original))
    d = inevow.IGettable(itemsel).get(ctx)
    d.addCallback(gotData, ctx)
    return d

def CmsFragmentFlattener(original,ctx):
    def gotData(data, ctx):
        if hasattr(data, 'sort'):
            data.sort(key=lambda i: i.date, reverse=True)
        resource = inevow.IResource(data)
        #if itemsel.template is not None and hasattr(resource, 'setTemplate'): 
            #resource.setTemplate(*parseTemplateString(itemsel.template))
        return resource

    itemsel = ItemSelection.fromString(str(original))
    d = inevow.IGettable(itemsel).get(ctx)
    d.addCallback(gotData, ctx)
    return d

flat.registerFlattener(RestFlattener,         Y.rest)
flat.registerFlattener(HtmlFlattener,         Y.html)
flat.registerFlattener(CmsItemSelFlattener,         Y.cmsitemsel)
