from poop import objstore

from tub import capabilities


class TubStoreSession(objstore.ObjectStoreSession):
    """
    Extension of Poop's object store session that adds capabilities support.
    """

    # Flag used to force a rollback of the entire session. Defaults to False.
    forceRollback = False

    # Capaibility context. Must be initialised early on in the session.
    capCtx = None

    def initCapCtx(self, avatar):
        """
        Initialise the capability context for the avatar.
        """
        if self.capCtx is None:
            self.capCtx = capabilities.NullCapabilityContext(self,
                    avatar.id)


class TubStore(objstore.ObjectStore):
    """
    Database storage for a Tub application.
    """

    sessionFactory = TubStoreSession
