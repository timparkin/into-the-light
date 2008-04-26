from nevow import inevow



def neverCache(request):
    """
    Set response headers on the request to ensure that the content is not
    cached.
    """
    request = inevow.IRequest(request)
    request.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
    request.setHeader('Pragma', 'no-cache')



def setDownload(request, filename):
    """
    Set the request headers so the client sees a file download.
    """
    request = inevow.IRequest(request)
    request.setHeader('Content-Disposition', 'attachment; filename=%s' % (filename,))

