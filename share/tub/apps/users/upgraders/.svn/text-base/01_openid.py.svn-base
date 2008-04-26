from purepg import adbapi
from poop import objstore, upgrade
from tub import user


def connectionFactory():
    return adbapi.connect(**vars)


store = objstore.ObjectStore(connectionFactory)

upgrader = upgrade.Upgrader()
store.registerType(user.User)

upgrader.add(upgrade.addAttribute, 'tub.user.User', ('openid', None), ('normalizedOpenid', None))

upgrader.add(upgrade.commit)

