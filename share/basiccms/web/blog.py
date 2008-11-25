from twisted.internet import defer
from twisted.python.components import registerAdapter
from twisted.python import log
from nevow import inevow, static, url, context, appserver, tags as T
from tub.public.web import pages as tub_pages
from tub.public.web import common as tubcommon
from tub.public.web import wrappers
from crux import skin, icrux
import formal
from pollen.mail import mailutil
import email.Utils
from basiccms.web import common, rssfeed
from basiccms import blogentry
from notification import inotification
import markdown
from comments import icomments

from datetime import *; from dateutil.relativedelta import *
from zope.interface import implements


class HumanCheckValidator(object):
    """
    A pointless example that checks a specific word, 'silly', is entered.
    """
    implements(formal.iformal.IValidator)

    word = u'ward'

    def validate(self, field, value):
        if value is None:
            return
        if value.lower() != self.word.lower():
            raise formal.FieldValidationError(u'You must enter \'%s\''%self.word)



def filter_by_month_year(month_year):
    month,year = month_year.split('-')
    month = int(month)
    year = int(year)
    def filter(items):
        return [item for item in items if item.date.month == month and item.date.year == year]
    return filter
    
def filter_last_n(last):
    last = int(last)
    def filter(items):
        return items[:int(last)]
    return filter

    
def filter_default():
    def filter(items):
        return items
    return filter
    
def get_filter_function(ctx):
    try:
        month_year = ctx.arg('month_year',None)
        if month_year is not None: 
            return filter_by_month_year(month_year)
        last = ctx.arg('last',None)
        if last is not None:
            return filter_last_n(last)
    except:
        pass

    return filter_default()
    
class BlogRSSSource():
    
    def __init__(self,blogitems):
        self.blogitems = blogitems[:10]
        self.blogitems.reverse()
        
    def title(self, ctx):
        return 'David Ward - Into The Light'

    def description(self, ctx):
        return 'Some of my images and some of my ramblings about the art of landscape photography...'

    def link(self, ctx):
        u = url.URL.fromContext(ctx)
        u = u.clear()
        return str(u)

    def items(self, ctx):
        items = []
        for item in self.blogitems:
            items.append( RSSItem(item) )
        return items

    def rssLink(self, ctx):
        u = url.URL.fromContext(ctx).child('rss')
        u = u.clear()
        return str(u)

class CommentRSSSource():
    
    def __init__(self,commentItems):
        self.commentItems = commentItems[:40]
        self.commentItems.reverse()
        
    def title(self, ctx):
        return 'David Ward - Into The Light - Comments'

    def description(self, ctx):
        return 'Comments Feed for David Ward\'s Blog'

    def link(self, ctx):
        u = url.URL.fromContext(ctx)
        u = u.clear()
        return str(u)

    def items(self, ctx):
        items = []
        for item in self.commentItems:
            items.append( CommentRSSItem(item) )
        return items

    def rssLink(self, ctx):
        u = url.URL.fromContext(ctx).child('commentrss')
        u = u.clear()
        return str(u)    
    
class RSSItem():
    
    def __init__(self,item):
        self.item = item
        
    def shortTitle(self, ctx):
        return self.item.title['en']

    def description(self, ctx):
        try:
            return self.item.shortdescription['en']
        except:
            return self.item.shortDescription['en']
            #return '-no description-'

    def link(self, ctx):
        u = url.URL.fromContext(ctx).child('blog').child(self.item.name)
        u = u.clear()
        return str(u)
    
    def pubDate(self, ctx):
        return self.item.date

class CommentRSSItem():
    
    def __init__(self,item):
        self.item = item
        
    def shortTitle(self, ctx):
        return '%s - %s' %(self.item.relatedToSummary,self.item.authorName)
        

    def description(self, ctx):
        return self.item.comment

    def link(self, ctx):
        u = url.URL.fromContext(ctx).child('blog').child(self.item.relatedToName)
        u = u.clear()
        return '%s#%s'%(str(u),'comment-%s'%self.item.id)
    
    def pubDate(self, ctx):
        return self.item.posted
    
    
def getItems(ctx,self=None):
    def gotItems(items):
        items = list(items)
        for item in items:
            item.date = datetime.fromordinal( item.date.toordinal() )
        items.sort(lambda x,y: -cmp(x.date,y.date))
        if self is not None:
            self.items = items
        return items
        
    if self is not None and hasattr(self,'items'):
        return defer.succeed(self.items)
    avatar = icrux.IAvatar(ctx)
    storeSession = tubcommon.getStoreSession(ctx)        
    d = storeSession.getItems(itemType=blogentry.BlogEntry)
    d.addCallback(gotItems)
    return d    
   
def getCommentItems(ctx,self=None):

    @defer.inlineCallbacks
    def gotComments(comments):
        comments = list(comments)
        commentMap = {}
        for comment in comments:
            commentMap[ comment.id ] = comment
        for comment in comments:
            if comment.relatesToCommentId is not None:
                comment.relatesToComment = commentMap[comment.relatesToCommentId]
            else:
                comment.relatesToComment = None
            followUpComments = []
            for c in comments:
                if comment.id == c.relatesToCommentId:
                    followUpComments.append( c )
            comment.followUpComments = followUpComments
            relatedTo = yield storeSession.getItemById(comment.relatesToId)
            relatedToSummary = icomments.IRelatedToSummarizer(relatedTo).getTitle()
            comment.relatedToSummary = relatedToSummary
            comment.relatedToName = relatedTo.name

        defer.returnValue( [c for c in comments if c.approved is True] )
    
    
    avatar = icrux.IAvatar(ctx)
    storeSession = tubcommon.getStoreSession(ctx)        
    d = avatar.realm.commentsService.getComments(storeSession,  order='DESCENDING')
    d.addCallback(gotComments)        
    return d
    
def BlogRSS(ctx):
    def gotItems(items):
        return rssfeed.getRSSFeed( ctx, BlogRSSSource(items) )
    d = getItems(ctx)
    d.addCallback(gotItems)
    return d

def CommentRSS(ctx):
    def gotItems(items):
        return rssfeed.getRSSFeed( ctx, CommentRSSSource(items) )
    d = getCommentItems(ctx)
    d.addCallback(gotItems)
    return d
    
    
def formatAgo(ago):
    if ago.years > 0:
        return 'last year'
    if ago.months > 1:
        return '%s months ago'%ago.months
    if ago.months > 0:
        return 'last month'
    if ago.days > 28:
        return '4 weeks ago'
    if ago.days > 21:
        return '3 weeks ago'
    if ago.days > 14:
        return '2 weeks ago'
    if ago.days > 7:
        return 'last week'
    if ago.days >1:
        return '%s days ago'%ago.days
    if ago.days >0:
        return 'yesterday'
    if ago.hours>0:
        return '%s hours ago'%ago.hours
    if ago.minutes>0:
        return '%s minutes ago'%ago.minutes
    if ago.seconds>0:
        return '%s seconds ago'%ago.seconds
    return ''

class Blog(common.PagingMixin,common.Page):

    docFactory = skin.loader("Blog.html")
 
    def getItems(self,ctx):
        items = getItems(ctx,self=self)       
        return items
        
        
       
    def data_blogentries(self, ctx, data):
        def gotItems(items):
            filter = get_filter_function(ctx)
            return filter(items)
        d = self.getItems(ctx)
        d.addCallback(gotItems)
        return d

    def render_months(self,ctx,data):
        def gotItems(items):
            from sets import Set
            last_month_year = None
            ordered_set_month_year = []
            for item in items:
                month_year = '%s-%s'%(item.date.month,item.date.year)
                if month_year != last_month_year:
                    ordered_set_month_year.append( {'id':month_year,'label': item.date.strftime('%b \'%y'), 'count':1} )
                    last_month_year = month_year
                else:
                    ordered_set_month_year[-1]['count'] += 1
                    
            blog_month_menu = T.ul(id='blogmonths')
            month_year_args = ctx.arg('month_year',None)
            for month_year in ordered_set_month_year:
                if month_year_args == month_year['id']:

                    blog_month_menu[ T.li[ T.strong[ T.a(href='?month_year=%s'%month_year['id'])[ month_year['label'], T.em[' (%s)'%month_year['count'] ] ] ] ] ]
                else:
                    blog_month_menu[ T.li[ T.a(href='?month_year=%s'%month_year['id'])[ month_year['label'], T.em[' (%s)'%month_year['count'] ] ] ] ]
            return blog_month_menu

        d = self.getItems(ctx)
        d.addCallback(gotItems)
        return d
            
    
    def render_blogentry(self, ctx, item):
        
        def gotComments(comments):
            
            comments = list(comments)
            try:
                lastComment = comments[-1].posted
                ago = relativedelta(datetime.now(),lastComment)
            except IndexError:
                lastComment = None
                ago = None
                
            tag = ctx.tag
            itemDate = item.getAttributeValue("date", "en")
            try:
                itemDate = itemDate['en']
            except:
                pass

            d = itemDate.day
            if 4 <= d <= 20 or 24 <= d <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][d % 10 - 1]
                

                
            m = itemDate.strftime('%B')
            y = itemDate.strftime('%Y')
            day = itemDate.strftime('%A')
            itemDate = '%s%s %s %s'%(d,suffix,m,y)   

            tag.fillSlots("url", url.here.child(item.name))
            tag.fillSlots("date", itemDate)
            if lastComment is not None:
                tag.fillSlots("lastComment", lastComment.strftime('%d %b %y %H:%M'))
                tag.fillSlots("ago", formatAgo(ago))
            else:
                tag.fillSlots("lastComment", '-')
                tag.fillSlots("ago", '-')
                
            tag.fillSlots("day", day)
            tag.fillSlots("title", item.getAttributeValue("title", "en"))
            tag.fillSlots("body", item.getAttributeValue("body", "en"))
            tag.fillSlots("sidebar", item.getAttributeValue("sidebar", "en"))
            comments = list(comments)
            commentcount = len(comments)
            if commentcount == 0:
                tag.fillSlots("comments", 'No Comments')
            elif commentcount == 1:
                tag.fillSlots("comments", '1 Comment')
            else:
                tag.fillSlots("comments", '%s Comments'%commentcount)
                
            return tag
            
        storeSession = tubcommon.getStoreSession(ctx) 
        d = self.avatar.realm.commentsService.getCommentsForItem(storeSession, item)        
        d.addCallback(gotComments)
        return d
    
    def childFactory(self, ctx, name):
        
        try:
            blogname = name
        except ValueError:
            return None
            
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        return storeSession.getOneItem(where='name=%(name)s',params={'name':blogname},itemType=blogentry.BlogEntry).addCallback(
                lambda blogentry: BlogEntryResource(storeSession, avatar, blogentry))
    

class BlogEntryResource(formal.ResourceMixin, common.Page):
    
    
    docFactory = skin.loader("BlogEntry.html")
    commentPostedSkin = skin.loader("CommentPostedFragment.html", ignoreDocType=True)
    
    
    COMMENT_POSTED = 'comment_posted'
    
    
    def __init__(self, storeSession, avatar, blogentry):
        super(BlogEntryResource, self).__init__()
        self.storeSession = storeSession
        self.avatar = avatar
        self.original = blogentry
        
        
    def renderHTTP(self, ctx):
        if ctx.arg(self.COMMENT_POSTED):
            return ResponseReturnPage(url.here.clear(), self.commentPostedSkin)
        return super(BlogEntryResource, self).renderHTTP(ctx)

    def render_blogentry(self, ctx, item):
        
        def gotComments(comments):
            
            comments = list(comments)
            try:
                lastComment = comments[-1].posted
                ago = relativedelta(datetime.now(),lastComment)
            except IndexError:
                lastComment = None
                ago = None
                
            tag = ctx.tag
            itemDate = item.getAttributeValue("date", "en")
            try:
                itemDate = itemDate['en']
            except:
                pass
            d = itemDate.day
            if 4 <= d <= 20 or 24 <= d <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][d % 10 - 1]
                

                
            m = itemDate.strftime('%B')
            y = itemDate.strftime('%Y')
            day = itemDate.strftime('%A')
            itemDate = '%s%s %s %s'%(d,suffix,m,y)   

            
            tag.fillSlots("url", url.here.child(item.name))
            tag.fillSlots("date", itemDate)
            if lastComment is not None:
                tag.fillSlots("lastComment", lastComment.strftime('%d %b %y %H:%M'))
                tag.fillSlots("ago", formatAgo(ago))
            else:
                tag.fillSlots("lastComment", '-')
                tag.fillSlots("ago", '-')
            tag.fillSlots("day", day)
            tag.fillSlots("title", item.getAttributeValue("title", "en"))
            tag.fillSlots("body", item.getAttributeValue("body", "en"))
            tag.fillSlots("sidebar", item.getAttributeValue("sidebar", "en"))
            comments = list(comments)
            commentcount = len(comments)
            if commentcount == 0:
                tag.fillSlots("comments", 'No Comments')
            elif commentcount == 1:
                tag.fillSlots("comments", '1 Comment')
            else:
                tag.fillSlots("comments", '%s Comments'%commentcount)
                
            return tag
            
        storeSession = tubcommon.getStoreSession(ctx) 
        d = self.avatar.realm.commentsService.getCommentsForItem(storeSession, item)        
        d.addCallback(gotComments)
        return d
            

    
    def data_comments(self, ctx, data):
        """
        Return the list of comments for the object.
        """
        def gotComments(comments):
            comments = list(comments)
            commentMap = {}
            for comment in comments:
                commentMap[ comment.id ] = comment
            for comment in comments:
                if comment.relatesToCommentId is not None:
                    comment.relatesToComment = commentMap[comment.relatesToCommentId]
                else:
                    comment.relatesToComment = None
                followUpComments = []
                for c in comments:
                    if comment.id == c.relatesToCommentId:
                        followUpComments.append( c )
                comment.followUpComments = followUpComments
            return comments
        
        d =  self.avatar.realm.commentsService.getCommentsForItem(self.storeSession, self.original)
        d.addCallback(gotComments)        
        return d
        
    def render_comment(self, ctx, comment):
        tag = ctx.tag
        tag.fillSlots("id", comment.id)
        tag.fillSlots("posted", comment.posted)
        tag.fillSlots("authorName", comment.authorName)
        if comment.authorName == 'David Ward':
            tag.fillSlots("isOwner", 'owner')
        else:
            tag.fillSlots("isOwner", '')
        tag.fillSlots("authorEmail", comment.authorEmail)
        tag.fillSlots("comment", T.xml(markdown.markdown(comment.comment)))
        tag.fillSlots("relatesToCommentId",comment.relatesToCommentId)
        if hasattr(comment, 'relatesToComment') and comment.relatesToComment is not None:
            tag.fillSlots("relatesToCommentName",comment.relatesToComment.authorName)
        else:
            tag.fillSlots("relatesToCommentName",'main blog entry')
        if hasattr(comment,'followUpComments') and comment.followUpComments is not None:
            fTag = T.span(class_='followUps')
            for f in comment.followUpComments:
                fTag[ T.a(href="#comment-%s"%f.id,rel='inspires')[ f.authorName ],', ' ]
            tag.fillSlots("followUpComments",fTag)
        else:
            tag.fillSlots("followUpComments",'None')
            
        return tag
        

        
    def form_comment(self, ctx):
        form = formal.Form()
        form.addField('authorName', formal.String(required=True), label="Name")
        form.addField('authorEmail', formal.String(required=True), label="Email")
        form.addField('comment', formal.String(required=True), widgetFactory=formal.TextArea)
        form.addField('humanCheck', formal.String(required=True,validators=[HumanCheckValidator()]), description="Enter David's Surname")
        form.addField('relatesToCommentId', formal.Integer(),widgetFactory=formal.Hidden)
        form.addAction(self.postComment)
        return form
        
        
    def postComment(self, ctx, form, data):
        def sendCommentNotification(data, ctx, title):
            def getEmailText():
                emailPage = CommentNotificationEmail(data,title)
                emailPage.remember(icrux.ISkin(ctx), icrux.ISkin)
                return emailPage.renderSynchronously()

            fromAddress = self.avatar.realm.config['mailService']['fromEmail']
            toAddress = [self.avatar.realm.config['mailService']['fromEmail']]
            htmlemail = getEmailText()
            msg = mailutil.createhtmlmail(fromAddress, toAddress, 'Comment Posted by %s'%data.authorName, htmlemail)
            return self.avatar.realm.mailService.sendMessage(toAddress, fromAddress, msg)
        
        d = self.avatar.realm.commentsService.postComment(self.storeSession, relatesTo=self.original, **data)
        d.addCallback(lambda item: sendCommentNotification(item,ctx,self.original.title))
        d.addCallback(lambda ignore: url.here.add(self.COMMENT_POSTED, 1))
        return d

    def childFactory(self, ctx, name):
        
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        return storeSession.getOneItem(where='name=%(name)s',params={'name':self.original.name},itemType=blogentry.BlogEntry).addCallback(
                lambda blogentry: BlogEntryResource(storeSession, avatar, blogentry))    
        
        
class ResponseReturnPage(common.Page):
    

    docFactory = skin.loader("ResponseReturn.html", ignoreDocType=True)
    
    
    def __init__(self, returnURL, messageFragment=None):
        super(ResponseReturnPage, self).__init__()
        self.messageFragment = messageFragment
        self.returnURL = returnURL
        
        
    def render_returnURL(self, ctx, data):
        ctx.tag.fillSlots("url", self.returnURL)
        ctx.tag.fillSlots("title", self.returnURL)
        return ctx.tag
        
        
    def fragment_message(self, ctx, data):
        return self.messageFragment

class CommentNotificationEmail(common.Page):
    docFactory = skin.loader('CommentNotificationEmail.html')

    def __init__(self, data,title):
        super(CommentNotificationEmail, self).__init__()
        self.data = data
        self.relatedToTitle = title

    def render_authorName(self,ctx,data):
        return self.data.authorName

    def render_authorEmail(self,ctx,data):
        return self.data.authorEmail
    
    def render_comment(self,ctx,data):
        return T.xml(markdown.markdown(self.data.comment))
    
    def render_relatedToTitle(self,ctx,data):
        return self.relatedToTitle.get('en','')
    
    
    def render_commentadmin(self,ctx,data):
        return T.a(href='http://admin.into-the-light.com/comments/%s'%self.data.id)['Click here for comment admin']
        
    
registerAdapter(BlogEntryResource, blogentry.BlogEntry, inevow.IResource)    
    

