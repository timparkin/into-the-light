from twisted.python import components


class IFTPShell(components.Interface):
    
    # Directory operations
    
    def currentDirectory(self):
        """Get the current directory.
        
        @return current directory
        @rtype str
        """
        
    def changeDirectory(self, path):
        """Change directory.
        
        @param path: path to change to, may be absolute or relative or None
        """
        
    def makeDirectory(self, path):
        """Create a new directory."""
        
    def deleteDirectory(self, path):
        """Delete a directory."""
        
    # File/directory operations
        
    def list(self, path):
        '''List the contents of the directory specified by path or the current
        directory if path is None.
        
        Returns a list of (stat, thing, user, group, size, mtime, name) tuples.
        '''
        
    # File operations
        
    def getFile(self, path):
        """Retrieve a file."""
        
    def getFileSize(self, path):
        """Get the size of a file."""
        
    def getFileModificationTime(self, path):
        """Retrieve the file timestamp from the server."""
        
    def putFile(self, path):
        """Store a file on the server.
        
        @return: an object that implement the IFinishableConsumer object to
                 accept the uploaded data.
        """
        
    def deleteFile(self, path):
        """Delete a file from the server."""

