try:
    import wingdbstub
except:
    pass
import re
import os.path
import shutil
import hype
import urllib
import urlparse
from nevow import url as n_url
from twisted.internet import defer
from twisted.web.client import HTTPClientFactory
from twisted.web import error
from BeautifulSoup import BeautifulSoup, Tag, NavigableString



def my_parse(url, defaultPort=None):
    parsed = urlparse.urlparse(url)
    scheme = parsed[0]
    path = urlparse.urlunparse(('','')+parsed[2:])
    if defaultPort is None:
        if scheme == 'https':
            defaultPort = 443
        else:
            defaultPort = 80
    host, port = parsed[1], defaultPort
    if ':' in host:
        host, port = host.split(':')
        port = int(port)
    return scheme, host, port, path



def switchDirectories(real, new, tmp):
    """Switch between the new and existing index directories, using the tmp as required"""
    try:
        #print 'Renaming %s to %s'%(real, tmp)
        if os.path.exists(real):
            os.rename(real, tmp)
    except:         
        raise

    try:
        #print 'Renaming %s to %s'%(new, real)
        os.rename(new, real)
    except:
        try:
            if os.path.exists(tmp):
                os.rename(tmp, real)
        except:
            raise
        raise

    if os.path.exists(tmp):
        #print 'Deleting %s'%tmp
        shutil.rmtree(tmp)



def getPage(url, contextFactory=None, *args, **kwargs):
    """Download a web page as a string.

    Download a page. Return a deferred, which will callback with a
    page (as a string) or errback with a description of the error.

    See HTTPClientFactory to see what extra args can be passed.

    A copy of the twisted web version but returns the factory
    rather than a deferred
    """
    scheme, host, port, path = my_parse(url)
    factory = HTTPClientFactory(url, *args, **kwargs)
    if scheme == 'https':
        from twisted.internet import ssl
        if contextFactory is None:
            contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(host, port, factory, contextFactory)
    else:
        reactor.connectTCP(host, port, factory)
    return factory

def processString(s):
    try:
        return unicode(s)
    except:
        pass
 
    try:
        return s.decode('utf8')
    except:
        pass

    try:
        return unicode(s.decode('utf8'))
    except:
        pass

    try:
        return s
    except:
        pass

    #print repr(s)
    import sys
    sys.exit()


class HypeIndex(object):

    def __init__(self, path):
        self.path = path


    def _toHypeDocument(self, key, title, section, summary, content):
        doc = hype.Document(unicode(key))
        #doc['@uri'] = unicode(key)
        doc['@title'] =processString(title)

        doc['@section'] = processString(section)
        doc['@summary'] = processString(summary)
        doc['@content'] = processString(content)

        tmp = []
        for c in content:
            try:
                unicode(c)
                tmp.append(c)
            except UnicodeDecodeError:
                pass
        content = "".join(tmp)

        doc.add_text(unicode(content))
        return doc


    def addDocument(self, key, title, section, summary, content):
        doc = self._toHypeDocument(key, title, section, summary, content)

        db = self._openDatabase()
        try:
            db.put_doc(doc)
        finally:
            self._closeDatabase(db)


    def _openDatabase(self):
        return hype.Database(self.path)


    def _closeDatabase(self, db):
        db.close()


def shouldSkipPath(path, pathREs):

    if not pathREs:
        pathREs = []

    for re in pathREs:
        if re.match(path):
            return True

    return False



@defer.deferredGenerator
def index(indexPath, url, matchingDomains=None, skipPaths=None, id=None):

    hypeIndex = HypeIndex(indexPath)

    domains=[]
    if matchingDomains is not None:
        domains = matchingDomains[:]

    scheme, host, port, path = my_parse(url)

    domains.append(host)
    domains.append('')

    visited = set()

    urlsToVisit = set()
    urlsToVisit.add(url)

    def newURLs(data, origURL):
        actualPath, newPaths = data

        args =  n_url.URL.fromString(origURL).queryList()
        query = ''
        for arg in args: 
            if arg[0] in ['page']:
                query = '?page=%s'%arg[1]

        origPath = '/' + '/'.join( n_url.URL.fromString(origURL).pathList() )
        origPath = origPath.lower() + query

        actualPath = actualPath.lower()
        #print '** Visited', actualPath, origPath
        visited.add(actualPath)
        visited.add(origPath)

        for newPath in newPaths:
            if shouldSkipPath(newPath, skipPaths):
                continue

            #print '** Test', newPath.lower(), visited
            if newPath.lower() not in visited:
                newURL = '%s://%s:%s%s'%(scheme, host, port, newPath)
                urlsToVisit.add(newURL)
                #print '** Adding', newURL
        

    while True:
        #print 'urls',urlsToVisit
        if len(urlsToVisit) == 0:
            break
        url = urlsToVisit.pop()
        #print 'visiting', url
        d = processURL(hypeIndex, url, domains, id)
        d.addCallback(newURLs, url)
        d = defer.waitForDeferred(d); yield d
        try:
            d.getResult()
        except error.Error, e:
            if e.status == '404' or e.status == '500':
#                print '** 404 **', url
                url = '/' + '/'.join( n_url.URL.fromString(url).pathList() )
                visited.add(url)
                continue
            raise e


entityRE = re.compile('&[a-z]+;', re.I)


def processURL(hypeIndex, urlToGet, domains, id):

    def isExtensionOkay(u):

        if u.endswith('.htm') or u.endswith('.html'):
            return True
        else:
            return False


    def getIndexableContent(soup):
        contents = []

        allTags = soup.findAll(id='body')
        soup = BeautifulSoup(str(allTags[0]))
        allTags = soup.findAll()

        # Try and find the indexable contents
        for tag in allTags:
            for item in tag.contents:
                # Looking for leaf nodes
                if not hasattr(item, 'contents'):
                    if item.__class__ == NavigableString:
                        content = str(item).strip()
                        if content:
                            contents.append(content)

        contents = " ".join([str(s) for s in contents])
        contents = re.sub(entityRE, "", contents)
        return contents


    def getTitle(soup):
        title = soup.find('title')
        if title:
            return title.string
        else:
            return ''


    def getLinkedPages(soup, u, domains):
        newPaths = []
        anchors = soup.findAll('a')
        for a in anchors:
            try:
                href = a['href']
            except KeyError:
                continue

            scheme, host, port, path = my_parse(href)

            if scheme in ('http', 'https', '') and host in domains:
                if path == '' or path[0] != '/':
                    # relative path
                    pathList = u.pathList()[:-1] 
                    currpath = '/'.join(pathList) 
                    if currpath:
                        currpath = '/' + currpath
                    path = currpath + '/' + path
                    path = n_url.normURLPath(path)

                args = n_url.URL.fromString(path).queryList()
                path = '/'+'/'.join(n_url.URL.fromString(path).pathList())
                query = ''
                for arg in args: 
                    if arg[0] in ['page']:
                       query = '?page=%s'%arg[1]
                path = path.encode('ascii')
                path = urllib.quote(path)+query.encode('ascii')
                newPaths.append(path)
            else:
#                print '** Ignore', href
                pass

        return newPaths


    def getSectionAndSummary(soup):
        if id is None:
            return 'any', ''
        summary = soup.findAll('div', attrs={'id':id})
        text = summary[0].findAll(lambda tag: hasattr(tag,'string') and tag.string is not None)
        #for t in text:
            #if t.name in ['h1','h2','h3','h4','strong']:
                #print '***',t.string
            #else:
                #print '---',t.string
            
                    
        if text:
            summary = ' .'.join( [t.string for t in text] )
            section = 'any'
            summary = re.sub( '\s+', ' ', summary)
            #print 'storing', section, ',',summary
            return section, summary[:300]

        return 'any', ''


    def gotPage(page, factory):

        u = n_url.URL.fromString(factory.url)

        if not page.startswith('<!DOCTYPE'):
            # Don't like the look of this url so I won't try and process it
            return factory.url, []
        soup = BeautifulSoup(page)
        title = getTitle(soup)
        content = getIndexableContent(soup)
        newPaths = getLinkedPages(soup, u, domains)
        section, summary = getSectionAndSummary(soup)

        #print '****'
        #print '>> URL', factory.url
        #print '>> content', content

        args = u.queryList()
        query = ''
        for arg in args: 
            if arg[0] in ['page']:
                query = '?page=%s'%arg[1]
        key = '/' + '/'.join(u.pathList()) + query

        if query == '':
            hypeIndex.addDocument(key, title, section, summary, content)

        return key, newPaths
                


    urlparse.clear_cache()
    factory = getPage(urlToGet)
    d = factory.deferred
    d.addCallback(gotPage, factory)
    return d


def debug(r):
    print '>>DEBUG', r
    return r


def buildOptionParser():
    from optparse import OptionParser

    parser = OptionParser()

    parser.add_option("-s", "--site", dest="site", 
        help="site to index e.g: http://horse-riding-guide.com")
    parser.add_option("-n", "--skip", dest="skip", 
        help="comma separated list of url reg exs not to index e.g. /products/*,/basket/*")
    parser.add_option("-o", "--output", dest="output", 
        help="Directory to write the generated index, this is rebuilt.")
    parser.add_option("-a", "--alias", dest="alias", 
        help="comma separated list of host alias")
    parser.add_option("-i", "--id", dest="id", 
        help="id that holds the section and summary")

    return parser


def buildSkipPathREs(param):
    import re
    urls = param.split(',')
    rv = []
    for url in urls:
        rv.append(re.compile(url))

    return rv



if __name__ == '__main__':
    import sys
    from twisted.internet import reactor

    parser = buildOptionParser()

    (options, args) = parser.parse_args()

    #print options
    #print args

    if options.site is None or options.output is None :
        print 'Must specify both an output directory and a site to index'
        sys.exit(1)

    indexDir = options.output
    newIndexDir = indexDir + '.new'
    tmpIndexDir = indexDir + '.tmp'

    if os.path.exists(newIndexDir) or os.path.exists(tmpIndexDir):
        print '%s or %s directories already exists'%(newIndexDir, tmpIndexDir)
        sys.exit(1)

    os.makedirs(newIndexDir)

    def cleanup(failure):
        shutil.rmtree(newIndexDir)
        return failure

    alias=None
    if options.alias:
        alias = options.alias.split(',')

    skipPaths=None
    if options.skip:
        skipPaths= buildSkipPathREs(options.skip)

    d = index(newIndexDir, options.site, alias, skipPaths, options.id)
    d.addCallback(lambda ignore: switchDirectories(indexDir, newIndexDir, tmpIndexDir))
    d.addErrback(cleanup)
    d.addBoth(debug)
    d.addBoth(lambda ignore: reactor.stop())

    reactor.run()
