import hype
print hype.__file__
print

from twisted.application import service
from crux import icrux, skin, openidconsumer
import purepg.adbapi

from tub import app, store
from basiccms import richtext
from cms import app as cmsapp, asset, systemservices
from pollen.nevow import imaging

from sitemap import app as sitemapapp

from ecommerce import app as ecommerce_app
from ecommerce.customer import app as customer_app, manager as customer_manager
from ecommerce.salesorder import app as salesorder_app, manager as salesorder_manager
from ecommerce.product import app as product_app, basicstock, optionmanager

import syck
config = syck.load(file('../public/config.yaml'), implicit_typing=False)


from comments.tub import app as commentsapp

from basiccms.apps.artwork import app as artwork_app
from basiccms.apps.registeredusers import app as registeredusers_app
from basiccms.apps import assets

application = service.Application(config['applicationLabel'])

# Create a connection pool
connectionPool = purepg.adbapi.ConnectionPool(**config['database']['args'])
purepg.adbapi.ConnectionPoolService(connectionPool).setServiceParent(
        application)

# Create a realm (kind of a service, really)
realm = app.Realm(application, config['applicationLabel'],
        store.TubStore(connectionPool.connect),config=config)

# Add the sitemap application
sitemapApplication = sitemapapp.SiteMapApplication()
sitemapApplication.addReservedNodes(['system', 'assets'])
sitemapApplication.setNavigationLevels( ( (1,'Primary'),(2,'Secondary') ) )

# Add the content management application
contentApplication = cmsapp.ContentApplication(sitemapApplication.getManager)
realm.applications.addApplication(contentApplication)

# Configure the imaging service and the asset CMS type
imaging.initialiseService('cache/cms/assets')
contentApplication.addService('assets', systemservices.AdminAssets('cache/cms/assets'))
contentApplication.addContentType(asset.AssetPlugin('assets'))





# Add common CMS types
from basiccms import formpage, news, page, gallery, blogentry
from cms import fragment, fragmenttype
contentApplication.addContentType(formpage.FormPagePlugin())
contentApplication.addContentType(page.PagePlugin())
contentApplication.addContentType(news.NewsItemPlugin())
contentApplication.addContentType(gallery.GalleryPlugin())
contentApplication.addContentType(blogentry.BlogEntryPlugin())
contentApplication.addContentType(fragment.FragmentPlugin())
contentApplication.addContentType(fragmenttype.FragmentTypePlugin())

# Add the sitemap application
sitemapApplication = sitemapapp.SiteMapApplication()
sitemapApplication.addReservedNodes(['system', 'assets'])
sitemapApplication.setNavigationLevels( ( (1,'Primary'),(2,'Secondary') ) )

#registerAdapter contentApplication to navigation content source
from cms import cmssitemap
sitemapApplication.addContentSource(contentApplication)



#realm.applications.addApplication(sitemapApplication)
realm.applications.addApplication(commentsapp.CommentsApplication())

#
try:
    from services import indexing as indexing_service
    indexer = indexing_service.ProductIndexer('indexes/product', '../public/indexes/product',None)
except ImportError, e:
    print '** Indexing service failed to load, indexing disabled **/n%s'%e
    indexer = None


# Add the ecommerce application
ecommerceApp = ecommerce_app.ECommerceApplication()
ecommerceApp.addService('assets', ecommerce_app.ECommerceAssets('cache/cms/assets'))




ecommerceApp.addApplication(customer_app.CustomerApplication())
ecommerceApp.addApplication(salesorder_app.SalesOrderApplication(
    {'sales_order': {'order_num_pattern': 'DW-%(sales_order_id)s',
                     'sales_order_processed_email_template': 'skin/SalesOrderProcessedEmail.html'
                    },
     'mailService': { 'smtpServer': 'localhost',
                      'fromEmail': 'tim@pollenation.net',
                      'orderProcessedEmailCategory': 'email.order_processed'
                    }
    },
    htmlEmailFactory=None
    )
)
ecommerceApp.addApplication(product_app.ProductApplication('assets', indexer, optionManager=optionmanager.OptionManager()))
realm.applications.addApplication(ecommerceApp)

realm.applications.addApplication(registeredusers_app.RegisteredUsersApplication())




# Add the Static Data application
from static_data import app as static_data_app
staticDataApplication = static_data_app.StaticDataApplication(static_data_app.StaticData('../public/%s'%config['staticData']['baseDir'], site=config['staticData']['files']['site']))
realm.applications.addApplication(staticDataApplication)


# Add CMS Form Data download
from basiccms.apps.form_data import app as form_data_app
realm.applications.addApplication(form_data_app.FormDataApplication())


# Configure OpenID consumer
openidconsumer.config({'filestore_dir': 'data/openid'})

# Run a web site
icrux.IWebSite(realm).install(config['admin']['http']['strport'], logPath=config['admin']['log'],
        checkers=(app.CredentialsChecker(realm),app.OpenIDCredentialsChecker(realm))
        )
