# -*- coding: utf8 -*-
import os.path
from twisted.internet import defer, utils, threads
from twisted.python import log
from nevow import appserver, inevow, static
import PIL.Image

from zope.interface import implements

# Binaries
IDENTIFY = '/usr/bin/identify'
CONVERT = '/usr/bin/convert'

class ImageResource(object):
    implements( inevow.IResource )
    
    def __init__(self, path):
        self.path = path
    
    def locateChild(self, ctx, segments):
        return appserver.NotFound
        
    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)
        nocache = ctx.arg('nocache')
        if nocache:
            request.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
            request.setHeader('Pragma', 'no-cache')            
        size = ctx.arg('size')
        if size is None:
            return static.File(self.path)
        sharpen = ctx.arg('sharpen')
        quality = ctx.arg('quality')
        invert = ctx.arg('invert')
        if size is not None:
            size = tuple( [int(s) for s in size.split('x')] )
        d = imagingService.getImageThumbnail(self.path, size, sharpen=sharpen, quality=quality, invert=invert)
        d.addCallback(static.File)
        return d

class ImagingService(object):

    _cache = {}

    def __init__( self, cachedir ):
        self.cachedir = cachedir
    
    def _getFileCache(self, path):
        cache = self._cache.setdefault(path, {})
        mtime = os.path.getmtime(path)
        if cache.get('mtime') != mtime:
            cache.clear()
            cache['mtime'] = mtime
        return cache

    def getImageSize(self, path):
        cache = self._getFileCache(path)
        size = cache.get('size')
        if size is not None:
            return defer.succeed(size)
        d = utils.getProcessOutput(IDENTIFY, [path])
        d.addCallback(self._cbGotImageSize, path)
        return d
        
    def _cbGotImageSize(self, out, path):
        size = tuple( [int(s) for s in out.split()[2].split('x')] )
        cache = self._getFileCache(path)
        cache['size'] = size
        return size
        
    def getImageThumbnail(self, path, maxSize,sharpen=None,quality=None, invert=None):
        
        maxSize = tuple(maxSize)
        
        cache = self._getFileCache(path)
        thumbnailCache = cache.setdefault('thumbnails', {})
        
        # Construct the thumbnail filename
        thumbnail = os.path.join(self.cachedir, os.path.split(path)[1])
        thumbnail, ext = os.path.splitext(thumbnail)
        if ext == '.jpe':
            ext = '.jpg'
        if maxSize is not None:
            params = '-%sx%s'%maxSize
        else:
            params = ''
        if sharpen is not None:
            params = params + '-s%s'%sharpen
        if quality is not None:
            params = params + '-q%s'%quality            
        if invert is not None:
            params = params + '-i%s'%invert
        
        thumbnail = thumbnail + params + ext
        exists = os.path.isfile(thumbnail)
        #log.msg('does %s exist ... %s'%(thumbnail,exists))
        
        # Return immediately if cached and the file still exists
        t = thumbnailCache.get(params)
        if t is not None and exists:
            return defer.succeed(t)
            
        # If the file exists and it's new enough then cache and return it 
        if exists and os.path.getmtime(thumbnail) >= cache['mtime']:
            thumbnailCache[params] = thumbnail
            return defer.succeed(thumbnail)
            
        def gotImageSize(size, path, thumbnail, maxSize, sharpen=None, quality=None, invert=None):
            return resizeImage(path, thumbnail, maxSize, sharpen=sharpen, quality=quality, size=size, invert=invert)
            
        # OK, we need to convert it then
        d = self.getImageSize(path)
        d.addCallback(gotImageSize,path, thumbnail, maxSize, sharpen=sharpen, quality=quality, invert=invert)
        d.addCallback(self._cbImageThumbnailed, path, thumbnail, params)
        return d
        
    def _cbImageThumbnailed(self, r, path, thumbnail, params):
        cache = self._getFileCache(path)
        thumbnailCache = cache.setdefault('thumbnails', {})
        thumbnailCache[params] = thumbnail
        return thumbnail

        
def resizeImageConvert(sourcePath, targetPath, maxSize, sharpen=None, quality=None, size=None, invert=None):
    """Resize image to max size using ImageMagic's convert. Debian's convert
    does not have the -thumbnail option though :(.
    # convert -font Helvetica -gravity South -background black -fill grey -splice 0x18 -draw "text 0,2 '© Copyright David Ward 1980-2007 - tel: +44 113 2252500 email: info@into-the-light.com web: www.into-the-light.com' address: David Ward, 3 Landsdowne Place, Leeds, United Kingdom LS17 6QR" 1.jpg out.jpg
    '-font','Helvetica','-gravity','South','-background','black','-fill','grey','-splice','0x18','-draw','"text 0,2 '© Copyright David Ward 1980-2007 - tel: +44 113 2252500 email: info@into-the-light.com web: www.into-the-light.com' address: David Ward, 3 Landsdowne Place, Leeds, United Kingdom LS17 6QR"',
    """

    if size is not None:
        width = size[0]
        height= size[1]
        
        
    
    if quality is None:
        quality='70'
        
    if invert=='inverted':
        foreback=['white','black']
        fill = '#555555'
    else:
        foreback=['black','white']
        fill = '#888888'
        
        
    args= [ '-bordercolor','black','-crop','%sx%s+0+0'%(width,height+24)] 
    profile = ['-profile','/home/into-the-light/site/live/public/icc/srgb.icm']

    border = None

    if maxSize is None:
        border=32
        points=12
        label = ['-pointsize','%s'%points,'-font','Helvetica','-gravity','South','-background',foreback[0],'-fill',fill,'-splice','0x%s'%border,'-draw',"text 0,2 '© David Ward 1980-2008 - tel: +44 1432 830781 email: david@into-the-light.com web: www.into-the-light.com address: Rowley Cottage, Westhope, UK. HR4 8BU'"] 
    else:
        if not (maxSize[0] == 601 and maxSize[1] == 631) and (maxSize[0] > 500 or maxSize[1] > 500):
            border=64
            points=24
            label = ['-pointsize','%s'%points,'-font','Helvetica','-gravity','South','-background',foreback[0],'-fill',fill,'-splice','0x%s'%border,'-draw',"text 0,2 '© David Ward 1980-2008, email: info@into-the-light.com web: www.into-the-light.com"] 
        if not(maxSize[0] == 1199 and maxSize[1] == 1200) and (maxSize[0] > 800 or maxSize[1] > 800):
            border=32
            points=12
            quality='95'
            sharpen='0.8x0.4+0.5+0.1'
            label = ['-pointsize','%s'%points,'-font','Helvetica','-gravity','South','-background',foreback[0],'-fill',fill,'-splice','0x%s'%border,'-draw',"text 0,2 '© David Ward 1980-2008 - tel: +44 1432 830781 email: david@into-the-light.com web: www.into-the-light.com address: Rowley Cottage, Westhope, UK. HR4 8B'"]
        if maxSize[0] == 1199 and maxSize[1] == 1200:
            quality='95'
            border = None
            label = ''
        
        


    if border is not None:
        args= [ '-bordercolor','black','-crop','%sx%s+0+0'%(width,height+border)] 
        args.extend( label )

    args.extend( profile )


    args.extend( ['-thumbnail', '%sx%s'%maxSize, '-quality', quality] )

    if sharpen is not None:
        args.extend( ['-unsharp',sharpen] )
    else:
        args.extend( ['-unsharp', '1.0x0.5+0.7+0.1'] )
    args.extend( [sourcePath, targetPath] )
    
    #log.msg('ImagingService(IM): thumbnailing %r to %r max'%(targetPath,maxSize))
    log.msg('ImagingService(IM): convert %s'% ' '.join(args))
    return utils.getProcessOutput(CONVERT, args)
        
        

def resizeImagePIL(sourcePath, targetPath, maxSize, neverGrow=False): #data, size, neverGrow=False):
    """Resize image to max size using PIL.
    """
    
    #log.msg('ImagingService(PIL): thumbnailing %r to %r max'%(targetPath,maxSize))
    
    def resizer():
    
        # PIL likes tuples
        size = tuple(maxSize)
    
        origImg = PIL.Image.open(sourcePath)
        if origImg.size <= maxSize and neverGrow:
            return data
    
        try:
            # Work in RGB for conversion ops
            img = origImg.convert('RGB')
            
            # Make the thumbnail
            img.thumbnail(maxSize, PIL.Image.ANTIALIAS)
            
            # Convert to a palletted image if there was one originally
            if origImg.palette:
                img = img.convert('P', palette=PIL.Image.ADAPTIVE, colors=255, dither=PIL.Image.NONE)
            
            # Save the image to a string
            img.save(targetPath, quality=70)
        except:
            import traceback; traceback.print_exc()
            
    return threads.deferToThread(resizer)
        
        
# Choose PIL, choose threads, choose small sizes, choose ... oh, I'm so bored!
resizeImage = resizeImageConvert
imagingService = None

def initialiseService( cachedir ):        
    global imagingService
    if imagingService is None:
        imagingService = ImagingService( cachedir )

