from tub.web import wrappers

        
class TransactionalResourceWrapper(wrappers.TransactionalResourceWrapper):

    def notFound(self, ctx):
        # Replace tub's version of notFound with a noop because tub closes the
        # store session and we don't to here.
        pass
