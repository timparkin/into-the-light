import unittest
from nevow import context, url
from pollen.nevow.wrappers import CanonicalDomainNameWrapper


class FakeRequest(object):
    
    def __init__(self, u):
        self.u = url.URL.fromString(u)
        
    def URLPath(self):
        return self.u
        
    uri = property(lambda self: self.u.path)


class TestCanonicalDomainNameWrapper(unittest.TestCase):
    
    skip = 'Test are broken'
    
    def fakeUriContext(self, url):
        request = FakeRequest(url)
        return context.RequestContext(tag=request)
    
    def test_it(self):
        
        mappings = {
            'www.pollenation.net': ['pollenation.net', 'pollenation.co.uk'],
            'www.example.com': ['example.com'],
            }
        wrapper = CanonicalDomainNameWrapper(None, mappings)
        
        tests = [
            ['http://pollenation.net/', 'http://www.pollenation.net/'],
            ['http://pollenation.co.uk/', 'http://www.pollenation.net/'],
            ['http://www.pollenation.net/', 'http://www.pollenation.net/'],
            ['http://example.com/', 'http://www.example.com/'],
            ['http://foo.com/', 'http://foo.com/'],
            ]
        
        for domain, canonicalised in tests:
            print '*', domain, canonicalised
            ctx = self.fakeUriContext(domain)
            self.assertEquals(wrapper.canonicalRedirectURL(ctx), url.URL.fromString(canonicalised))
            
