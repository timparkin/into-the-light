from comments import model


class CommentsService(object):


    # Ordering
    ASCENDING = 'ASCENDING'
    DESCENDING = 'DESCENDING'


    def postComment(self, storeSession, **k):
        """
        Post a new comment, passing all keyword args to the Comment initializer.
        """
        return storeSession.createItem(model.Comment, **k)


    def getCommentsForItem(self, storeSession, relatesTo, approved=True,
            order=ASCENDING, offset=None, limit=None):
        """
        Get a sequence of comments relating to the given item.
        """

        # Basic where clause and params
        where = "relates_to_id=%(relates_to_id)s"
        params = {'relates_to_id': relatesTo.id, 'relates_to_version': relatesTo.version}

        # Add approval
        if approved is not None:
            where = where + " and approved=%(approved)s"
            params['approved'] = approved

        # Add ordering
        if order is CommentsService.ASCENDING:
            orderBy = "posted asc"
        elif order is CommentsService.ASCENDING:
            orderBy = "posted desc"
        else:
            raise Exception("Unknown ordering %r" % order)

        return storeSession.getItems(model.Comment, where=where, params=params,
                orderBy=orderBy, offset=offset, limit=limit)

                
    def getComments(self, storeSession, approved=None, order=ASCENDING,
            offset=None, limit=None):
        """
        Get a sequence of all comments in the system.
        """

        # Add approval
        if approved is not None:
            where = "approved=%(approved)s"
            params = {'approved': approved}
        else:
            where = None
            params = None

        # Add ordering
        if order == CommentsService.ASCENDING:
            orderBy = "posted asc"
        elif order == CommentsService.DESCENDING:
            orderBy = "posted desc"
        else:
            raise Exception("Unknown ordering %r" % order)

        return storeSession.getItems(model.Comment, where=where, params=params,
                orderBy=orderBy, offset=offset, limit=limit)
                
