from tub.web import page
from nevow import inevow, url, tags as T
from crux import skin
import formal
import markdown
from comments import icomments, model, service



class CommentsPage(page.Page):


    componentContent = skin.loader('comments/Comments.html')


    def __init__(self, commentsService, storeSession, avatar):
        self.commentsService = commentsService
        self.storeSession = storeSession
        self.avatar = avatar
        
        
    def childFactory(self, ctx, name):
        try:
            commentId = int(name)
        except ValueError:
            return None
        d = self.storeSession.getItemById(commentId, itemType=model.Comment)
        d.addCallback(lambda comment: ReviewCommentPage(self.storeSession, comment))
        return d
        
        
    def data_comments(self, ctx, data):
        return self.commentsService.getComments(self.storeSession, approved=False, order=service.CommentsService.DESCENDING)
        
        
    def render_comment(self, ctx, comment):
        
        def gotRelatedToItem(relatedTo):
            tag = ctx.tag
            tag.fillSlots("url", url.here.child(comment.id))
            tag.fillSlots("posted", comment.posted.strftime('%c'))
            tag.fillSlots("authorName", comment.authorName)
            tag.fillSlots("authorEmail", comment.authorEmail)
            tag.fillSlots("comment", T.xml(markdown.markdown(comment.comment)))
            tag.fillSlots("relatedTo", icomments.IRelatedToSummarizer(relatedTo).getTitle())
            return tag
        
        d = self.storeSession.getItemById(comment.relatesToId)
        d.addCallback(gotRelatedToItem)
        return d

    def data_approved(self, ctx, data):
        return self.commentsService.getComments(self.storeSession, approved=True, order=service.CommentsService.DESCENDING)
        
        
    def render_approvedcomment(self, ctx, comment):
        
        def gotRelatedToItem(relatedTo):
            tag = ctx.tag
            tag.fillSlots("url", url.here.child(comment.id))
            tag.fillSlots("posted", comment.posted.strftime('%c'))
            tag.fillSlots("authorName", comment.authorName)
            tag.fillSlots("authorEmail", comment.authorEmail)
            tag.fillSlots("comment", T.xml(markdown.markdown('%s ...'%comment.comment[:50])))
            tag.fillSlots("relatedTo", icomments.IRelatedToSummarizer(relatedTo).getTitle())
            return tag
        
        d = self.storeSession.getItemById(comment.relatesToId)
        d.addCallback(gotRelatedToItem)
        return d

        
        
class ReviewCommentPage(formal.ResourceMixin, page.Page):


    componentContent = skin.loader('comments/ReviewComment.html')


    def __init__(self, storeSession, comment):
        super(ReviewCommentPage, self).__init__()
        self.storeSession = storeSession
        self.comment = comment


    def form_comment(self, ctx):
        form = formal.Form()
        form.addField('authorName', formal.String(required=True), label="Name")
        form.addField('authorEmail', formal.String(required=True), label="Email")
        form.addField('comment', formal.String(required=True), widgetFactory=formal.TextArea)
        form.addField('posted', formal.Date(required=True, immutable=True))
        form.addAction(self.updateComment, 'update')
        form.addAction(self.approveComment, 'approve')
        form.addAction(self.deleteComment, 'delete')
        form.data = {
            'authorName': self.comment.authorName,
            'authorEmail': self.comment.authorEmail,
            'comment': self.comment.comment,
            'posted': self.comment.posted,
            }
        return form
        
        
    def updateComment(self, ctx, form, data):
        self.updateCommentAttrs(data)
        return url.here.up()
        
        
    def approveComment(self, ctx, form, data):
        self.updateCommentAttrs(data)
        self.comment.approved = True
        return url.here.up()
        
        
    def deleteComment(self, ctx, form, data):
        d = self.storeSession.removeItem(self.comment.id)
        d.addCallback(lambda ignore: url.here.up())
        return d
        
        
    def updateCommentAttrs(self, data):
        self.comment.touch()
        self.comment.authorName = data['authorName']
        self.comment.authorEmail = data['authorEmail']
        self.comment.comment = data['comment']

