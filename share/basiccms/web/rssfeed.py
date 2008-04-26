
from nevow import static, url
from basiccms.web import RSS


def getRSSFeed(ctx, rssSource):

    def createChannel(rssSource):
        fields = {
            (RSS.ns.rss10, "title"): rssSource.title(ctx),
            (RSS.ns.rss10, "description"): rssSource.description(ctx),
            (RSS.ns.rss10, "link"): rssSource.link(ctx)
        }

        return RSS.CollectionChannel( {(RSS.ns.rss10, "channel"): fields} )

    def createRSSItem(item):
        rv = { (RSS.ns.rss10, 'title'): item.shortTitle(ctx), 
                     (RSS.ns.rss10, 'description'): item.description(ctx),
                     (RSS.ns.rss10, 'link'): item.link(ctx),
                     (RSS.ns.rss10, 'pubDate'): _formatPubDate(item.pubDate(ctx)),
        }
        return rv

    def _formatPubDate(pd):
        return pd.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def createResourceFromChannel(channel):
        return static.Data(str(channel), 'text/xml')

    channel = createChannel(rssSource)

    for item in rssSource.items(ctx):
        channel.addItem(createRSSItem(item))
    return createResourceFromChannel(channel)

    


