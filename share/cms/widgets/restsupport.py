from nevow import tags as T, flat, url

from docutils.writers.html4css1 import Writer, HTMLTranslator
from docutils import nodes
from docutils.parsers.rst import directives

from cms.widgets.itemselection import ItemSelection

class CMSReST2HTMLTranslator(HTMLTranslator):

    systemURL = url.URL.fromString('/').child('content').child('system')
    
    def visit_cmslink_node(self, node):

        tag = T.a(href=node.attributes['href'])[node.attributes['body']]
        if node.attributes['title']:
            tag = tag(title=node.attributes['title'])
        if node.attributes['cssclass']:
            tag = tag(class_=node.attributes['cssclass'])

        html = flat.flatten(tag)

        self.body.append(html)

    def depart_cmslink_node(self, node):
        pass
    
    def visit_cmsimage_node(self, node):
        maxwidth=node.attributes['maxwidth']
        maxheight=node.attributes['maxheight']
            
        if maxwidth is None or maxheight is None:
            tag = T.img(src=self.systemURL.child('assets').child( node.attributes['id'] ))
        else:
            tag = T.img(src=self.systemURL.child('assets').child( node.attributes['id'] ).add('size','%sx%s'%(maxwidth,maxheight)))
        
        if node.attributes['alt']:
            tag = tag(alt=node.attributes['alt'])
        if node.attributes['title']:
            tag = tag(title=node.attributes['title'])
        if node.attributes['cssclass']:
            tag = tag(class_=node.attributes['cssclass'])
        if node.attributes['href']:
            tag = T.a(href=node.attributes['href'])[ tag ]
            
        if node.attributes['caption']:
            tag = T.div(class_='cmsimage')[tag,T.p[node.attributes['caption']]]
        else:
            tag = T.div(class_='cmsimage')[tag]
        html = flat.flatten(tag)

        self.body.append(html)

    def depart_cmsimage_node(self, node):
        pass    

    def visit_cmsitemselection_node(self, node):
        itemsel = ItemSelection.fromString(str(node.attributes['itemsel']))
        tag = T.div(class_="cmsitemselection")[
            "Items matching:", T.br,
            T.strong["Type:"], itemsel.type or '', T.br,
            T.strong["Categories:"], itemsel.categories or '', T.br,
            T.strong["Max Publish Age:"], itemsel.maxPublishedAge or '', T.br,
            T.strong["Max Items:"], itemsel.maxItems or '', T.br,
            T.strong["Template:"], itemsel.template or '', T.br,
            "will be inserted here"
        ]
        html = flat.flatten(tag)
        self.body.append(html)


    def depart_cmsitemselection_node(self, node):
        pass

class CMSReST2HTMLTranslatorPublic(CMSReST2HTMLTranslator):
    systemURL = url.URL.fromString('/').child('system')

cmsReSTWriter = Writer()
cmsReSTWriter.translator_class = CMSReST2HTMLTranslator

publicCmsReSTWriter = Writer()
publicCmsReSTWriter.translator_class = CMSReST2HTMLTranslatorPublic


class cmslink_node(nodes.General, nodes.Inline, nodes.TextElement):
    pass

def cmslink(name, arguments, options, content, lineno,
                 content_offset, block_text, state, state_machine):
    return [cmslink_node('', href=arguments[0], body=options.get('alt', None), title=options.get('title', None), cssclass=options.get('cssclass', None))]

cmslink.arguments = (1, 0, 1)
cmslink.options = { 'title': directives.unchanged,
                    'cssclass': directives.unchanged }

class cmsimage_node(nodes.General, nodes.Inline, nodes.TextElement):
    pass

def cmsimage(name, arguments, options, content, lineno,
                 content_offset, block_text, state, state_machine):
    return [cmsimage_node('', id=arguments[0], alt=options.get('alt', None), title=options.get('title', None), cssclass=options.get('cssclass', None), href=options.get('href', None), caption=options.get('caption', None), maxheight=options.get('maxheight', None), maxwidth=options.get('maxwidth', None))]

cmsimage.arguments = (1, 0, 1)
cmsimage.options = { 'title': directives.unchanged,
                     'cssclass': directives.unchanged,
                     'alt': directives.unchanged,
                     'href': directives.unchanged,
                     'caption': directives.unchanged,
                     'maxwidth': directives.unchanged,
                     'maxheight': directives.unchanged,
                     }


class cmsitemselection_node(nodes.General, nodes.Inline, nodes.TextElement):
    pass

def cmsitemselection(name, arguments, options, content, lineno,
                 content_offset, block_text, state, state_machine):
    return [cmsitemselection_node('', itemsel=arguments[0])]

cmsitemselection.arguments = (1, 0, 1)
cmsitemselection.options = { }

from docutils.parsers.rst import directives
directives.register_directive('cmslink', cmslink)
directives.register_directive('cmsimage', cmsimage)
directives.register_directive('cmsitemselection', cmsitemselection)

def htmlFragment(input_string, writer=None, writer_name=None):
    from docutils.core import publish_parts

    overrides = {'input_encoding': 'utf8',
                 'doctitle_xform': 0,
                 'initial_header_level': 1}
    parts = publish_parts(
        source=input_string,
        writer_name=writer_name, writer=writer, settings_overrides=overrides)
    fragment = parts['fragment']
    return fragment.encode('utf8')
