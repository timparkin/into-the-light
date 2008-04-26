# This module will allows the public tub site to access content from
# the cms database.

from cms.contentitem import ContentManager
from cms.systemservices import Assets
from nevow import rend, url

from crux import icrux
from tub import itub, category

class CMSService(object):

    def getContentManager(self, avatar):
         return ContentManager(avatar, None)

    def getCategoriesManager(self, avatar, sess):
         return category.CategoryManager(avatar, sess)

    def loadCategories(self, sess, avatar, name):
        return self.getCategoriesManager(avatar, sess).loadCategories(name)

    def getItem(self, sess, avatar, id=None, name=None, type=None, category=None):
        if id:
            if name or type or category:
                raise 'Can only specify id'
            return self._getItemById(sess, avatar, id)

        def gotItems(items):
            # Return the first one or None.
            if len(items):
                return items[0]
            else:
                return None

        d = self.getItems(sess, avatar, name, type, category)
        d.addCallback(gotItems) 
        return d

    def _getItemById(self, sess, avatar, id):
        return self.getContentManager(avatar).publicFindById(sess, id)

    def getItems(self, sess, avatar, name=None, type=None, category=None):

        if not name and not type and not category:
            raise 'Must specify one of name, type or category'

        def gotItems(items):
            if len(items):
                return items
            else:
                return []

        # Build the where and params. The where clause is built in parts and
        # then AND'd together at the end.
        where = []
        params = {}
        if name:
            where.append("name=%(name)s")
            params['name'] = name
        if category is not None:
            where.append("categories <@ %(category)s")
            params['category'] = category
        # Make final where
        where = ' and '.join(where)
        if not where:
            where = None

        d = self.getContentManager(avatar).publicFindManyContentItems(sess,
                where=where, params=params, itemType=type)
        d.addCallback(gotItems) 
        return d

    def getItemsByIds(self, sess, avatar, ids):

        def gotItems(items):
            if len(items):
                return items
            else:
                return []

        where = []
        params = {}

        for id in ids:
            key = 'id%s'%id
            where.append( '%%(%s)s'%key )
            params[key] = id

        where = ','.join(where)
        where = ' id in (%s) '%where

        d = self.getContentManager(avatar).publicFindManyContentItems(sess,
                where=where, params=params)
        d.addCallback(gotItems) 
        return d


class NullApplication(object):

    def __init__(self):
        self._cm = None

    def getContentManager(self, avatar):
        return ContentManager(avatar, None)

class AssetsService(rend.Page):
    """This is a hook into the imaging service in cms.
    """

    def __init__(self, cachedir):
        self.assets = Assets(cachedir)
        self.assets.setURL(url.root.child('system').child('assets'))
        self.assets.setApplication(NullApplication())
        self.cachedir = cachedir

    def locateChild(self, ctx, segments):
        avatar = icrux.IAvatar(ctx)
        ctx.remember(avatar, itub.IAvatar)
        return self.assets.locateChild(ctx, segments)

