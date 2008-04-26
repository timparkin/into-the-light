import urlparse
from sets import Set
import urllib
import re
import os
import zope.interface as zi
from twisted.internet import defer
from twisted.web import http
from nevow import appserver, inevow, url, vhost, static

class SeeThroughWrapper(object):
    """
    Resource wrapper base class that forwards any get/set attrs to the wrapped
    resource to make the the wrapper as transparent as possible.
    """

    def __init__(self, wrapped):
        self.__dict__['wrapped'] = wrapped

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def __setattr__(self, name, value):
        return setattr(self.wrapped, name, value)


class VHostWrapper(SeeThroughWrapper):
    """
    Wrapper that provides a VHostMonsterResource as the 'vhost' segment and
    passes any other segments to the wrapped resource.
    """
    zi.implements(inevow.IResource)

    _vhost = None

    def locateChild(self, ctx, segments):
        if segments[0] == 'vhost':
            # Lazily create the vhost resource instance. Reference the class
            # explicitly so we don't trip over the SeeThroughWrapper's
            # __setattr__ magic.
            if VHostWrapper._vhost is None:
                VHostWrapper._vhost = vhost.VHostMonsterResource()
            return VHostWrapper._vhost, segments[1:]
        return self.wrapped, segments

    def renderHTTP(self, ctx):
        return self.wrapped.renderHTTP(ctx)


class CanonicalDomainNameWrapper(SeeThroughWrapper):
    """
    Resource wrapper that forces a 301 redirect to a canonical domain name.

    This is mostly useful for ensuring that a web site can only be reached at
    one domain name, i.e. when your logs must contain only one domain name in or
    when you're running SSL and don't have a wildcard certificate.

    The wrapper uses a map of canonical domain names to list of domain names to
    canononicalise.

    Example use:

        canonicalMappings = {
            'www.pollenation.net': [
                'pollenation.net',
                ],
            }
        root = MyRealRootResource()
        root = CanonicalDomainNameWrapper(root, canonicalMappings)
    """

    zi.implements(inevow.IResource)

    def __init__(self, wrapped, mappings):
        SeeThroughWrapper.__init__(self, wrapped)
        # Reverse the mappings for fast lookups
        self.mappings = {}
        for canonical, domains in mappings.iteritems():
            for domain in domains:
                self.mappings[domain] = canonical

    def locateChild(self, ctx, segments):
        redirectURL = self.canonicalRedirectURL(ctx)
        if redirectURL is not None:
            return RedirectResource(redirectURL, http.MOVED_PERMANENTLY), ()
        return self.wrapped.locateChild(ctx, segments)

    def renderHTTP(Self, ctx):
        redirectURL = self.canonicalRedirectURL(ctx)
        if redirectURL is not None:
            return RedirectResource(redirectURL, http.MOVED_PERMANENTLY)
        return self.wrapped.renderHTTP(ctx)

    def canonicalRedirectURL(self, ctx):
        """Search the mappings for a canonical domain name and return a new
        URL or None, as necessary.
        """
        # Get the current URL
        u = url.URL.fromContext(ctx)
        # Split the authentication stuff from the netloc
        if '@' in u.netloc:
            userpass, host = u.netloc.split('@', 1)
        else:
            userpass, host = None, u.netloc
        if ':' in host:
            host, port = host.split(':', 1)
        else:
            host, port = host, None
        # See if there is a canonical mapping for this domain
        canonical = self.mappings.get(host)
        if canonical is None:
            return None
        # Construct a new netloc
        netloc = ''
        if userpass is not None:
            netloc += userpass
            netloc += '@'
        netloc += canonical
        if port is not None:
            netloc += ':'
            netloc += port
        u.netloc = netloc
        # Add on any remaining segments
        for segment in inevow.IRemainingSegments(ctx):
            u = u.child(segment)
        return u


class HttpRedirectWrapper(SeeThroughWrapper):
    """
    Resource wrapper that allows arbitrary redirecting of urls

    Allows the supply of a set of urls to map and a type of http redirect (301
    typically but 302's for moving a site to a new domain name and keeping
    existing google rank)

    TODO: currently maps from paths with get parameters but not to paths with
    get parameters. It should really check for parameters that have been
    'mapped' and leave all remaining alone.

    Example use:

        urlMappings = [
            ['/about.html', '/about.html'],
            ['/contact.asp', '/enquiry'],
            ['/contact.asp?id=2', '/enquiry'],
            ]
        root = MyRealRootResource()
        root = HttpRedirectWrapper(root, urlMappings, http.MOVED_PERMANENTLY)

    we also need to process the following to skip the category.

        urlMappings = [
            ["\/products\/[\/A-Za-z0-9_]*\/([0-9-]+)","/products/\1","pattern"],
            ["\/products([\/A-Za-z0-9_])*1220-660-4561","/products\11220-660-4562","pattern"],
            ]
            
    the first replaces any category prefixed product with a link to the root product
    the second points an old product to a replacement
            
    note the use of an extra variable at the end to indicate something special is happening.
    """

    zi.implements(inevow.IResource)

    def __init__(self, wrapped, urlMappings, httpRedirectCode = http.FOUND):
        SeeThroughWrapper.__init__(self, wrapped)
        self.urlMappings = [self.prepare(*mapping) for mapping in urlMappings]
        self.httpRedirectCode = httpRedirectCode
        
    def prepare(self, old, new, type='string'):
        if type == 'pattern':
            old = re.compile(old)
        return (old, new, type)
        
    def locateChild(self, ctx, segments):
        redirectURL = self.redirectURL(ctx,segments)
        if redirectURL is not None:
            return RedirectResource(redirectURL, self.httpRedirectCode), ()
        return self.wrapped.locateChild(ctx, segments)

    def renderHTTP(Self, ctx):
        redirectURL = self.redirectURL(ctx)
        if redirectURL is not None:
            return RedirectResource(redirectURL, httpRedirectCode)
        return self.wrapped.renderHTTP(ctx)

    def redirectURL(self, ctx, segments=[]):
        """Search the mappings for a url and return a new
        URL or None, as necessary.
        """
        # get the requested path as a nevow url
        requestUrlString = inevow.IRequest(ctx).uri
        requestUrl = url.URL.fromString( requestUrlString )
        requestQuerySet = Set( requestUrl.queryList() )

        # function to see if url matches. If it does it returns the 

        # for each mapping, get the query set
        redirectSet = None
        toUrl = None
        for fromUrlString, toUrlString, type in self.urlMappings:
            # get the set of k,v tuples for the from url
            if type == 'string':
                fromUrl = url.URL.fromString( fromUrlString )
                if fromUrl.path == requestUrl.path:
                    # get the set of query parameters for both request and from
                    fromQuerySet = Set( fromUrl.queryList() )
                    if fromQuerySet.issubset(requestQuerySet):
                        remainsQuerySet = requestQuerySet.difference(fromQuerySet)
                        toUrl = url.URL.fromString( toUrlString )
                        toQuerySet = Set( toUrl.queryList() )
                        redirectSet = toQuerySet.union(remainsQuerySet)
                        break

            elif type=='pattern':
                # fromUrlString is actually a compiled regexp at this point
                p = fromUrlString
                m = p.match(requestUrl.path) 
                if m:
                    toUrlPath = p.sub(toUrlString,requestUrl.path)
                    toUrl = url.URL.fromString( toUrlString ).click('/%s'%toUrlPath)
                    break

        # See if there is a url mapping for this path
        if toUrl is not None:
            if redirectSet is not None:
                queryArgs = redirectSet
            else:
                queryArgs = requestQuerySet
            redirectUrl = urlparse.urlunsplit( (requestUrl.scheme, requestUrl.netloc, '/%s'%toUrl.path, '&'.join( ['%s=%s'%(urllib.quote_plus(k[0]),urllib.quote_plus(k[1])) for k in queryArgs] ), requestUrl.fragment) )
            return url.URL.fromString(redirectUrl)


class FinalResourceWrapper(SeeThroughWrapper):
    """
    A resource wrapper that fires either the success or error callback method at
    the end of the request.
    """
    zi.implements(inevow.IResource)

    def __init__(self, wrapped, *args, **kwargs):
        # I really need an IResource to work
        wrapped = inevow.IResource(wrapped)
        super(FinalResourceWrapper, self).__init__(wrapped)
        self.__dict__['args'] = args
        self.__dict__['kwargs'] = kwargs
        
    def locateChild(self, ctx, segments):
        
        def waitForResource(result):
            resource, segments = result
            if isinstance(resource, defer.Deferred):
                d = resource
            else:
                d = defer.succeed(resource)
            d.addCallback(lambda resource: (resource, segments))
            return d
            
        def childLocated(result):
            if result == appserver.NotFound or result[0] is None:
                d = defer.maybeDeferred(self.notFound, ctx)
                d.addCallback(lambda ignore: result)
                return d
            newResource, newSegments = result
            return self.__class__(newResource, *self.args,
                    **self.kwargs), newSegments
            
        d = defer.maybeDeferred(self.wrapped.locateChild, ctx, segments)
        d.addCallback(waitForResource)
        d.addCallback(childLocated)
        d.addErrback(self.error, ctx)
        return d

    def renderHTTP(self, ctx):
        def rendered(result):
            # The result can be a string or a resource. If it's a resource then
            # we should wrap that too. Unfortunately, Nevow provides an adapter
            # from str to IResource so we need to type check first.
            if not isinstance(result, str):
                resource = inevow.IResource(result, None)
                if resource is not None:
                    return self.__class__(resource, *self.args, **self.kwargs)
            return self.success(result, ctx)
        d = defer.maybeDeferred(self.wrapped.renderHTTP, ctx)
        d.addCallbacks(rendered, self.error, errbackArgs=(ctx,))
        return d
        
    def success(self, result, ctx):
        return result
            
    def error(self, failure, ctx):
        return failure

    def notFound(self, ctx):
        pass



class OverlayWrapper(SeeThroughWrapper):
    """
    Resource wrapper that intercepts the wrapped resource's locateChild(),
    allowing it to run only if a list of locateChild-style callables fail to
    provide a resource.
    """


    zi.implements(inevow.IResource)


    def __init__(self, wrapped, handlers):
        """
        wrapped -- the resource to wrap
        handlers -- a list of locateChild-style callables
        """
        super(OverlayWrapper, self).__init__(wrapped)
        self.__dict__['handlers'] = handlers


    def locateChild(self, ctx, segments):
        def processResult(result):
            if result != appserver.NotFound:
                return result
            return self.wrapped.locateChild(ctx, segments)
        handlers = self.__dict__['handlers']
        d = _firstLocateChildHandlerResult(handlers, ctx, segments)
        d.addCallback(processResult)
        return d



def _firstLocateChildHandlerResult(handlers, ctx, segments):
    """
    Call each handler in sequence returning either NotFound or the result of
    the first handler that does not return NotFound.
    """

    def next():
        try:
            handler = handlers.next()
        except StopIteration:
            return defer.succeed(appserver.NotFound)
        d = defer.maybeDeferred(handler, ctx, segments)
        d.addCallback(_undeferLocateChildResult)
        d.addCallback(checkResult)
        return d

    def checkResult(result):
        if result != appserver.NotFound:
            return result
        return next()

    handlers = iter(handlers)
    return next()



def _undeferLocateChildResult((resource, segments)):
    """
    Helper function to callback only when the actual resource from a
    locateChild call is known.
    """
    if isinstance(resource, defer.Deferred):
        return resource.addCallback(lambda resource: (resource, segments))
    return (resource, segments)



class RedirectResource(object):
    zi.implements(inevow.IResource)

    def __init__(self, url, httpRedirectCode):
        self.url = url
        self.httpRedirectCode = httpRedirectCode

    def locateChild(self, ctx, segments):
        raise NotImplementedError, 'RedirectResource instances can never have children'

    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)
        request.setResponseCode(self.httpRedirectCode)
        request.setHeader('Location', str(self.url))
        request.write('')
        return ''



class NotFoundWrapper(SeeThroughWrapper):
    """
    Catch not found errors and display a nice page.
    """


    def __init__(self, wrapped, resourceFactory):
        SeeThroughWrapper.__init__(self, wrapped)
        self.resourceFactory = resourceFactory


    def locateChild(self, ctx, segments):
        ctx.remember(self, inevow.ICanHandleNotFound)
        return self.wrapped.locateChild(ctx, segments)


    def renderHTTP_notFound(self, ctx):
        return self.resourceFactory(ctx)



class FileSystemTemplateHandler(object):
    """
    An underlay/overlay handler for mapping URLs to "static" resources on the
    file system in the given path.

    By default, a static.File resource is returned but an application-specified
    resource type can be created by setting the resourceFactory. The
    resourceFactory callable is expected to take two arguments: a Nevow context
    and the path to the template.

    The handler tries to avoid the use of file extensions in the hope that, one
    day, these resources will become dynamic. A the path maps to a directory
    then the a file, index.html, in the directory is returned.  Otherwise, if
    the path doen not aready have an '.html' extension then it is automatically
    appended before looking on the file system.
    """


    resourceFactory = static.File


    def __init__(self, baseDir, resourceFactory=None):
        self.baseDir = baseDir
        if resourceFactory is not None:
            self.resourceFactory = resourceFactory


    def __call__(self, ctx, segments):

        baseDir = tuple(self.baseDir.split('/'))
        currentSegments = inevow.ICurrentSegments(ctx)

        # Build a full path to what may be some static content
        path = os.path.join(*(baseDir + currentSegments + segments))

        if os.path.isdir(path):
            # Path is a directory, append default file name
            path = os.path.join(path, 'index.html')
        else:
            # Path is a file. Append '.html' if it doesn't already have an
            # extension.
            if not os.path.splitext(path)[1]:
                path += '.html'

        # return the file if it exists
        if os .path.isfile(path):
            return self.resourceFactory(path), ()

        # Dunno what it is, mate.
        return appserver.NotFound



# Create a default handler to match the previous version. Perhaps this should
# be deprecated?
locateStaticChild = FileSystemTemplateHandler('static')

