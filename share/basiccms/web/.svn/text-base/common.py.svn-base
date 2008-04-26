from sets import Set
from nevow import inevow, tags as T, flat, loaders, rend
from tub.public.web import common as tubcommon
from crux import web, icrux, skin
from navigation import NestedListNavigationFragment
from pollen.nevow import renderers

from basiccms.paging import ListPagingData, PagingControlsFragment

from cms.widgets.itemselection import ItemSelection


def distinct(l):
    """
    Return a list of distinct items.
    """
    return list(set(l))

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



def data_cmsitemselection(encodedItemsel):

    def data(ctx, data):

        def gotData(data, ctx):
            if hasattr(data, 'sort'):
                try:
                    data.sort(key=lambda i: i.date, reverse=True)
                except AttributeError:
                    data.sort(key=lambda i: i.name, reverse=True)
                    
            return data

        itemsel = ItemSelection.fromString(str(encodedItemsel))
        d = inevow.IGettable(itemsel).get(ctx)
        d.addCallback(gotData, ctx)
        return d

    return data


def render_cmsitemselection(encodedItemsel):
    itemsel = ItemSelection.fromString(str(encodedItemsel))

    def renderer(ctx, data):
        from basiccms.web import cmsresources
        resource = inevow.IResource(data)
        if itemsel.template is not None and hasattr(resource, 'setTemplate'): 
            resource.setTemplate(*cmsresources.parseTemplateString(itemsel.template))
        return resource

    return renderer

class NavigationMixin(object):
    """
    Mixin the navigation renderer.
    """

    def render_navigation(self, *render_args):
        def f(ctx, data):
            args = []
            kwargs = {}
            for arg in render_args:
                if "=" in arg:
                    key, value = arg.split('=', 1)
                    kwargs[str(key)] = value
                else:
                    args.append(arg)
            return NestedListNavigationFragment(*args, **kwargs)
        return f



class SiteMixin(object):
    """
    Mixin the site layout and templating renderers.
    """


    def getExtraData(self, ctx):
        """
        Load the site data.
        """
        avatar = icrux.IAvatar(ctx)
        return avatar.realm.staticData.parseYAML('site') or {}


    def render_logotext(self,ctx,data):
        logotext = self.getExtraData(ctx).get('logotext')
        if logotext is not None:
            return T.xml(logotext)
        return ctx.tag


    def render_footer(self,ctx,data):
        footer = self.getExtraData(ctx).get('footer')
        if footer is not None:
            return T.xml(footer)
        return ctx.tag


    def render_yuiid(self,ctx,data):
        yuiid = self.getExtraData(ctx).get('yuiid')
        if yuiid is not None:
            return T.xml(yuiid)
        return 'doc3'
    

    def render_sidebar(self,ctx,data):
        sidebar = self.getExtraData(ctx).get('sidebar')
        if sidebar is not None:
            return  T.div(id='sidebar')[sidebar]
        else:
            return ''

    def render_admin(self,ctx,data):
        return ''

    def render_bodyclass(self,ctx,data):
        classes = self.getExtraData(ctx).get('template',[None,{}])[1].get('classes',None)
        if classes:
            return ' '.join(classes)
        else:
            return ''


    def render_yuiclass(self,ctx,data):
        yuiclass = self.getExtraData(ctx).get('yuiclass')
        if yuiclass is not None:
            return T.xml(yuiclass)
        return 'yui-t1'
    
    def render_backgroundswapper(self,ctx,data):
        if isInverted(ctx) == True:
            if ctx.arg('q'):
                return T.a(href="?invert=False&amp;q=%s"%ctx.arg('q'),class_="backgroundswapper")[ T.img(src="/skin/images/swapbackground-invert.gif") ]
            else:
                return T.a(href="?invert=False",class_="backgroundswapper")[ T.img(src="/skin/images/swapbackground-invert.gif") ]
        else:
            if ctx.arg('q'):
                return T.a(href="?invert=True&amp;q=%s"%ctx.arg('q'),class_="backgroundswapper")[ T.img(src="/skin/images/swapbackground.gif") ]
            else:
                return T.a(href="?invert=True",class_="backgroundswapper")[ T.img(src="/skin/images/swapbackground.gif") ]
            
    def render_adminswapper(self,ctx,data):
        if isAdminOn(ctx) == True:
            if ctx.arg('q'):
                return T.a(href="?admin=False&amp;q=%s"%ctx.arg('q'),class_="adminswapper")[ T.img(src="/skin/images/swapadmin.gif") ]
            else:
                return T.a(href="?admin=False",class_="adminswapper")[ T.img(src="/skin/images/swapadmin.gif") ]
        else:
            if ctx.arg('q'):
                return T.a(href="?admin=True&amp;q=%s"%ctx.arg('q'),class_="adminswapper")[ T.img(src="/skin/images/swapadmin.gif") ]
            else:
                return T.a(href="?admin=True",class_="adminswapper")[ T.img(src="/skin/images/swapadmin.gif") ]
        
                
def isInverted(ctx):
    request = inevow.IRequest(ctx)
    if ctx.arg('invert',None) == 'True':
        request.addCookie('invert', 'True', expires=None, path='/')
        return True
    elif ctx.arg('invert',None) == 'False':
        request.addCookie('invert', 'False', expires=None, path='/')
        return False
    request = inevow.IRequest(ctx)
    cookie = request.getCookie('invert')
    if cookie is None or cookie == 'False':
        return False
    else:
        return True

def isAdminOn(ctx):
    request = inevow.IRequest(ctx)
    if ctx.arg('admin',None) == 'True':
        request.addCookie('admin', 'True', expires=None, path='/')
        return True
    elif ctx.arg('admin',None) == 'False':
        request.addCookie('admin', 'False', expires=None, path='/')
        return False
    request = inevow.IRequest(ctx)
    cookie = request.getCookie('admin')
    if cookie is None or cookie == 'False':
        return False
    else:
        return True

def getInverted(ctx):
    i = isInverted(ctx)
    if i is True:
        return '-inverted'
    else:
        return ''

class Page(SiteMixin, NavigationMixin, renderers.RenderersMixin, web.Page):
    """
    Base class for "ordinary" pages.
    """


    def render_title_tag(self, ctx, data):
        return ctx.tag


    def render_meta_description(self, ctx, data):
        return ctx.tag


    def render_meta_keywords(self, ctx, data):
        return ctx.tag
    
    def render_invert(self,ctx,data):
        i = isInverted(ctx)
        if i is True:
            return '-inverted'
        else:
            return ''
        
    def render_invertstyles(self,ctx,data):
        i = isInverted(ctx)
        if i is True:
            return T.link(rel='stylesheet',type='text/css',href='/skin/css/styles-inverted.css')
        else:
            return ''
        
    def render_ifinverted(self,ctx,data):
        return render_if(ctx,isInverted(ctx))
        
    def render_if(self,ctx,data):
        return render_if(ctx,data)

    def data_cmsitemselection(self, encodedItemsel):
        return data_cmsitemselection(encodedItemsel)
    def render_cmsitemselection(self, encodedItemsel):
        return render_cmsitemselection(encodedItemsel)

class CMSResource(tubcommon.CMSMixin, Page):
    """
    Base class for CMS item pages.
    """

    def getExtraData(self,ctx):

        # Get the extra data from the super class and the extra data from the item.
        extraData = SiteMixin.getExtraData(self, ctx)
        itemExtraData = self.original.getExtraDataAttributeValue('extraData', 'en') or {}

        # XXX itemExtraData is a unicode instance and yet the rest of the code
        # is expecting a dict. Did this thing ever work (even before my
        # changes) or were the exception handlers masking the problems?
        # For now, because I'd really like to achieve something today, I'm
        # going to just set itemExtraData to an empty dict.
        itemExtraData = {}

        # ... from the item
        templateName = getattr(self.original.getProtectedObject(), "template", None)
        templateString = ''
        templates = getattr(self.original.plugin,'templates',[])
        if templates is not None:
            for pluginTemplate in templates:
                if pluginTemplate is not None and pluginTemplate[0] == templateName:
                    templateString = pluginTemplate[2]
                    break
        args,kwargs = parseTemplateString(templateString)
        classes = kwargs.get('classes','').split()
        # ... from the super class's extra data
        edargs,edkwargs = parseTemplateString(extraData.get('template'))
        if len(edargs)>1:
            args = edargs
        classes.extend( edkwargs.get('classes','').split() )
        kwargs.update(edkwargs)
        # ... from the item's extra data
        iargs, ikwargs = parseTemplateString(itemExtraData.get('template'))
        if len(iargs)>1:
            args = iargs
        classes.extend( ikwargs.get('classes','').split() )
        kwargs.update(ikwargs)

        # Overlay the item's extra data on the "normal" extra data
        extraData.update(itemExtraData)

        # Replace the templates with out aggregated version
        kwargs['classes'] = classes
        extraData['template'] = (distinct(args),kwargs)

        # Hurray! We finally got there!
        return extraData

    def data_cmsitemselection(self, encodedItemsel):
        from basiccms.web import rest
        # This returns a list of objects
        return rest.data_cmsitemselection(encodedItemsel)
    
    def render_cmsitemselection(self, encodedItemsel):
        # This is expecting to render a single object
        from basiccms.web import rest
        return rest.render_cmsitemselection(encodedItemsel)

    def render_invert(self,ctx,data):
        i = isInverted(ctx)
        if i is True:
            return '-inverted'
        else:
            return ''
 
    def render_ifinverted(self,ctx,data):
        return render_if(ctx,isInverted(ctx))
        
    def render_if(self,ctx,data):
        return render_if(ctx,data)
    
    def render_invertstyles(self,ctx,data):
        i = isInverted(ctx)
        if i is True:
            return T.link(rel='stylesheet',type='text/css',href='/skin/css/styles-inverted.css')
        else:
            return ''   
        
    def render_title_tag(self, ctx, data):
        titleTag = getattr(self.original.getProtectedObject(), 'title', None)
        if titleTag:
            ctx.tag.clear()
            ctx.tag[titleTag]
        return ctx.tag
        
        

def render_if(ctx, data):

    # Look for (optional) patterns.
    truePatterns = ctx.tag.allPatterns('True')
    falsePatterns = ctx.tag.allPatterns('False')

    # Render the data. If we found patterns use them, otherwise return the tag
    # or nothing.
    if data:
        if truePatterns:
            return truePatterns
        else:
            return ctx.tag
    else:
        if falsePatterns:
            return falsePatterns
        else:
            return ''



class PagingMixin(object):


    def render_paging(self, paging, grouping=None):

        paging = int(paging)
        if grouping is not None:
            grouping = int(grouping)

        def render(ctx, data):

            def gotPage(ignore, pageData):
                def emptyString():
                    return ''
                tag = inevow.IQ(ctx).patternGenerator('item')
                if grouping is not None:
                    try:
                        septag = inevow.IQ(ctx).patternGenerator('seperator')
                    except:
                        septag = emptyString

                for cnt,item in enumerate(pageData.data):
                    yield tag(data=item)
                    if grouping is not None and (cnt+1)%grouping == 0:
                        yield septag()

            pageData = ListPagingData(ctx, list(data), paging)
            d = pageData.runQuery()
            d.addCallback(gotPage, pageData)

            return d

        return render


    def fragment_paging_controls(self, ctx, data):
        return PagingControlsFragment('PagingControlsFragment.html')





class RichTextFragment(rend.Fragment, PagingMixin, skin.SkinRenderersMixin):

    XML_TEMPLATE = """<!DOCTYPE html
      PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
      <div xmlns:n="http://nevow.com/ns/nevow/0.1" >%s</div>"""


    def __init__(self,xml):
        rend.Fragment.__init__(self, docFactory=loaders.xmlstr(self.XML_TEMPLATE%xml, ignoreDocType=True))
    
    def data_cmsitemselection(self, encodedItemsel):
        return data_cmsitemselection(encodedItemsel)
    def render_cmsitemselection(self, encodedItemsel):
        return render_cmsitemselection(encodedItemsel)
    