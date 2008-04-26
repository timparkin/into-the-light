import sys
from pkg_resources import require
from twisted.python.components import registerAdapter


from twisted.application import internet, service
from crux import guard, icrux, skin
from tub import store
# import rest to get it to register the correct rich text flattener
from basiccms.web import rest
from basiccms import app
import purepg.adbapi
from formal import RichText
from nevow.flat import registerFlattener
from pollen.richtext import converterRegistry
from basiccms.web.common import RichTextFragment
from basiccms import richtext

def richTextRenderer(richText,ctx):
    converter = converterRegistry.converter(richText.type, 'xhtml')
    out = converter(richText.value).encode('utf8')
    return RichTextFragment(out)

registerFlattener(richTextRenderer, RichText)

# Load configuration
import syck
config = syck.load(file('config.yaml'), implicit_typing=False)


from pollen.nevow import imaging
imaging.initialiseService(config['cmsAssetsService']['cachedir'])

application = service.Application('brunswick-tcf')
connectionPool = purepg.adbapi.ConnectionPool(**config['database']['args'])
store = store.TubStore(connectionPool.connect)

realm = app.Realm(application, config, store, None)

skin = skin.FileSystemSkin(config['skin']['dir'])
icrux.IWebSite(realm).install(config['public']['http']['strport'],
        logPath=config['public']['log'], skin=skin,
        sessionManager=guard.SessionManager(sessionLifetime=7200))

