#!/usr/bin/python

#
# This now uses pysvn to get the sql files from svn.
# The psql commands are executed using a sudo to postgres so may need to provide
# a password to a sudo password prompt.
#

import sys, os, re
from optparse import OptionParser

# Create a constants directory with appropriate values for your installation
# 
# For example
#    C = {
#       'ltree':'/usr/share/postgresql/7.4/contrib/ltree.sql',
#       'db':'brunswicktesting',
#       'user':'brunswicktesting',
#    }
#
# You should also check the getFilesFromSvn section which sets up 'sqlFiles'
#

C = {
        'ltree': '/usr/share/postgresql/contrib/ltree.sql',
        }

sqlfiles = []
tempDirName = None


def getFilesFromSvn():
    import pysvn
    import tempfile
    import os.path

    if C.has_key('svnusername'):
        svn = 'svn+ssh://%(svnusername)s@pollenation.net/svn'%C
    else:
        svn = 'svn+ssh://pollenation.net/svn'
        
    pollen = svn+'/pollen'
    tub = pollen+'/pollen/tub/trunk/src'
    basic_cms = pollen+'/pollen/basic_cms/trunk/lib/sql'

    filesToGet = [
        ('oltree', 'ordered-ltree-api.sql', 
            pollen+'/pollen/ltree/ordered-ltree-api.sql'),
        (None, 'objstore.sql', 
            pollen+'/poop/trunk/poop/objstore.sql'),
        (None, 'categories.sql',
            tub+'/tub/apps/categories/db/categories.sql'),
        (None, 'users.sql',
            tub+'/tub/apps/users/db/users.sql'),
        (None, 'files.sql',
            tub+'/cms/db/files.sql'),
        (None, 'contentitem.sql',
            tub+'/cms/db/contentitem.sql'),
        (None, 'sitemap.sql',
            tub+'/sitemap/db/sitemap.sql'),
        (None, 'basic_cms_model.sql',
            basic_cms+'/model.sql'),
	(None, 'product-type.sql',
	    pollen+'/pollen/ecommerce/trunk/ecommerce/product/sql/product-type.sql'),
	(None, 'customer.sql',
	    pollen+'/pollen/ecommerce/trunk/ecommerce/customer/sql/customer.sql'),
	(None, 'salesorder.sql',
	    pollen+'/pollen/ecommerce/trunk/ecommerce/salesorder/sql/salesorder.sql'),
    ]



    global tempDirName
    tempDirName = tempfile.mkdtemp()
    os.chmod(tempDirName, 0755)

    global sqlfiles
    sqlfiles = []

    def get_login( realm, username, may_save ):
        return retcode, C['svnusername'], C['svnpassword'], True

    client = pysvn.Client()

    client.callback_get_login = get_login    
    for file in filesToGet:
        key, fileName, svnPath = file
        if key:
            # Only get files that haven't been specified already
            if C.has_key(key):
                continue
        if C['verbose'] > 0:
            print '# Getting %s from svn'%fileName
        filePath = os.path.join( tempDirName , fileName)
        f = open(filePath, 'wb')
        f.write(client.cat(svnPath))
        f.close()
        if key:
            C[key] = filePath
        else:
            sqlfiles.append(filePath)


def tidyUp():
    import shutil
    global tempDirName
    #if tempDirName:
        #shutil.rmtree(tempDirName)


def escapequote(s):
    s = s.replace(r'\"', r'\\\"')
    s = re.sub(r'([^\\]|^)"', r'\1\"', s)
    return s


def command(command,message):
    message = message%C
    command = command%C
    if C['verbose'] == 1:
        print '# %s'%(message)
    if C['verbose'] > 1:
        print '>%s'%command

    command = escapequote(command)
    command='sudo su postgres -c "%s"'%command

    tochild, fromchild, childerror = os.popen3(command, 'r')
    err = '\n'.join(childerror.readlines())
    if len(err) > 0 :
        if 'NOTICE' not in err and C['verbose'] > 0:
            print err
    if C['verbose'] > 1:
        print '\n'.join(fromchild.readlines())
    

def createdb():
    command('dropdb %(db)s',"Dropping database %(db)s")
    if C['dropuser']:
        command('dropuser %(user)s', "Dropping user %(user)s")
    command('createdb %(db)s -Eutf8',"Creating database %(db)s")
    command('createuser %(user)s -A -D',"creating user %(user)s")        
    command('createlang --dbname=%(db)s plpythonu',"Creating plpythonu")

    command('cat %(ltree)s | psql %(db)s',"Creating ltree contrib")
    command('cat %(oltree)s | psql %(db)s',"Creating ordered ltree")

    for f in sqlfiles:
        C['sqlfile'] = f
        command('cat %(sqlfile)s | psql %(db)s',"Applying %(sqlfile)s to db")
        lines = open(f).readlines()
        for line in lines:
            if line.startswith('---<ADDUSERNAME>'):
                sql = line[17:].replace('<USERNAME>',C['user']).strip()
                C['sql'] = escapequote(sql)
                command('echo "%(sql)s" | psql %(db)s',"Applying grants from %(sqlfile)s")
                

def main(options, args):

    if len(args) == 1:
        C['db'] = args[0]
    else:
        print 'no database specified'
        sys.exit(0)
    if options.user:
        C['user'] = options.user
    C['dropuser'] = options.dropuser
    if options.ltree:
        C['ltree'] = options.ltree
    if options.oltree:
        C['oltree'] = options.oltree
    if options.objstore:
        C['objstore'] = options.objstore
    if options.svnusername:
        C['svnusername'] = options.svnusername
    C['verbose'] = options.verbose
    try:
        getFilesFromSvn()
        createdb()
    finally:
        tidyUp()


def parseOptions():
    parser = OptionParser()
    parser.add_option("-U", "--user", dest="user",
        help="user to create",
        metavar="USER")
    parser.add_option("-D", "--drop-user", dest="dropuser",
        action="store_const", default=False, const=True,
        help="drop user before create",
        metavar="DROPUSER")
    parser.add_option("-L", "--ltree", dest="ltree",
        help="path to ltree sql, usually in /usr/share/postgresql/7.4/contrib/ltree.sql",
        metavar="LTREE")
    parser.add_option("-l", "--oltree", dest="oltree",
        help="path to oltree sql, svn+ssh://pollenation.net/svn/pollen/pollen/ltree/ordered-ltree-api.sql",
        metavar="LTREE")
    parser.add_option("-o", "--objstore", dest="objstore",
        help="path to objstore sql, svn+ssh://pollenation.net/svn/pollen/poop/trunk/poop/objstore.sql",
        metavar="LTREE")
    parser.add_option("-u", "--svnusername", dest="svnusername",
        help="usename to use for subversion checkouts",
        metavar="SVNUSERNAME")
    parser.add_option("-v", "--verbose", action="store_const",
        dest="verbose", default=0, const=1,
        help="print status messages to stdout")
    parser.add_option("-V", "--veryverbose", action="store_const",
        dest="verbose", default=0, const=2,
        help="print status messages and commands to stdout")
    (options, args) = parser.parse_args()
    main(options, args)

if __name__ == "__main__":
    parseOptions()
