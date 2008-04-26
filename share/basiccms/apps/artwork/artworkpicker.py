from zope.interface import implements
from twisted.internet import defer

from nevow import tags as T
from nevow import url

from pollen.nevow import imaging

from formal import iforms
from formal.util import keytocssid


from cms.assetbrowser import AssetBrowser, IImageFactory, ListModel
from basiccms.apps.artwork.manager import ArtworkManager
from basiccms.apps.artwork.web import loader



class ArtworkBrowser(AssetBrowser):
    implements(IImageFactory)

    docFactory = loader('ArtworkBrowser.html')

    name = "artworkbrowser"

    def __init__(self, application):
        super(ArtworkBrowser, self).__init__(application, self)

    def getURL(self, avatar, storeSession, image, name):
        imgURL=url.URL.fromString('/artwork/system/assets/%s'%image.id)
        if name:
            imgURL = imgURL.child(name)
        return defer.succeed(imgURL)


    def getSize(self, avatar, storeSession, image, name):
        defaultLanguage = avatar.realm.defaultLanguage

        d = self.application.getServices().getService('assets').getPathForAsset(avatar, storeSession, image, name, defaultLanguage)
        d.addCallback(imaging.imagingService.getImageSize)
        return d


    def getImages(self, avatar, storeSession, query):

        manager = ArtworkManager()

        where = [ " categories ~ '%s' "%cat for cat in query if cat ]

        if where:
            where = ["(" + " or ".join( where ) + ")" ]
        else:
            where = None

        d = manager.findMany(storeSession, where=where)
        d.addCallback(lambda artworks: ListModel([ (a, 'mainImage') for a in artworks]))
        return d


    def getAltStr(self, image):
        return image.shortDescription


class ArtworkPickerWidget(object):
    implements(iforms.IWidget)


    def __init__(self, original):
        self.original = original

    def _parseValue(self, value):
        if not value:
            return []
        rv = []
        for line in value.splitlines():
            line = line.strip()
            if line:
                rv.append(line)

        return rv
        

    def render(self, ctx, key, args, errors):

        if errors:
            images = args.get(key, [''])[0]
            images = self._parseValue(images)
        else:
            images = iforms.ISequenceConvertible(self.original).fromType(args.get(key))
            if images is None:
                images = []

        imgs = T.ul(id="artwork_list_"+keytocssid(ctx.key))

        for image in images:
            imgs[ T.li(id='item_%s'%image)[
                T.img(src='/artwork/system/assets/%s/mainImage?size=100x100'%image , class_="preview"),
                T.a(onClick='delete_item(%s);'%image)['delete']
            ] ]

        return T.div()[
            imgs, T.br(),
            T.textarea(name=key, id=keytocssid(ctx.key))['\n'.join(images)], T.br(),
            T.button(onclick="return ArtworkPicker('%s')"%keytocssid(ctx.key))['Choose artwork ...'],
            T.script(type="text/javascript")[
            T.xml("""
            function ArtworkPicker(elementId, type) {
                var url = '/artwork/system/assets/artworkbrowser';
                url = url + '?searchOwningId='+elementId+'&searchType='+type;
                var popup = window.open(url, 'ArtworkPicker', 'height=500,width=900,resizable,scrollbars');
                popup.focus();
                return false;
            }
            function imageListChanged(sortable) {
              var items = MochiKit.Sortable.Sortable.serialize(sortable).split('&');
              var newOrder=[];
              for(i=0;i<items.length;i++){
                var item = items[i];
                var id = item.split('=')[1];
                newOrder.push(id);
              }
              var ta=document.getElementById('%(key)s');
              ta.value='';
              for(i=0;i<newOrder.length;i++) {
                ta.value=ta.value+'\\n'+newOrder[i];
              }
            }

            function itemAdded() {
              MochiKit.Sortable.Sortable.create('artwork_list_%(key)s',{onUpdate:imageListChanged});
            }

            function delete_item(delete_id) {
              var element=document.getElementById('item_'+delete_id);
              removeElement(element);
              var ta=document.getElementById('%(key)s');
              var ids = ta.value.split('\\n');

              ta.value='';
              for(i=0;i<ids.length;i++) {
                id = ids[i];
                if(delete_id==id) {
                  continue;
                } 
                ta.value=ta.value+'\\n'+id;
              }
            }
            function setup() {
                connect('artwork_list_%(key)s', 'itemAdded', itemAdded); 
                signal('artwork_list_%(key)s', 'itemAdded');
            }
            setup();
            """%{'key': keytocssid(ctx.key)})
            ]
            ]

    def renderImmutable(self, ctx, key, args, errors):
        if errors:
            images = args.get(key, [''])[0]
            images = self._parseValue(images)
        else:
            images = iforms.ISequenceConvertible(self.original).fromType(args.get(key))
            if images is None:
                images = []

        imgs = T.invisible()

        for image in images:
            imgs[ T.img(src='/artwork/system/assets/%s/mainImage?size=100x100'%image , class_="preview") ]

        return T.div()[
            imgs, T.br(),
            T.textarea(class_="readonly", readonly="readonly", name=key, id=keytocssid(ctx.key))['\n'.join(images)],
            ]

    def processInput(self, ctx, key, args):
        value = args.get(key, [None])[0] or None
        value = self._parseValue(value)
        return self.original.validate(value)

