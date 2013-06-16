#----------------------------------------------------------------------
# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#----------------------------------------------------------------------

import hashlib
import thread

from nive.definitions import Interface, implements


class SessionUserCache(object):
    """
    User caching support. Caches users including data as attributes. 
    
    Options: ::

        useCache = enable or disable caching
        cacheTypes = a list of pool_types to be cached. not matching types are not cached
        expires = objs are reloaded or purged after this many seconds. 0 = never expires 
    """
    useCache = True
    expires = 20*60 

    def Cache(self, obj, id):
        """
        """
        if not self.useCache:
            return 
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            setattr(self, self._Cachename(id), (obj, time()))
            if lock.locked():
                lock.release()
        except:
            if lock and lock.locked():
                lock.release()

    def GetFromCache(self, id):
        """
        returns the cached object
        """
        if not self.useCache:
            return None
        n = self._Cachename(id)
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            if hasattr(self, n):
                o = getattr(self, n)
                if lock.locked():
                    lock.release()
                return o[0]
        except:
            if lock and lock.locked():
                lock.release()
        return None

    def GetAllFromCache(self):
        """
        returns all cached objects
        """
        objs = []
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            for v in self.__dict__.keys():
                if v[:5] == "__c__":
                    objs.append(getattr(self, v)[0])
            if lock.locked():
                lock.release()
        except:
            if lock and lock.locked():
                lock.release()
        return objs

    def RemoveCache(self, id):
        """
        """
        if not self.useCache:
            return 
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            try:
                delattr(self, self._Cachename(id))
            except:
                pass
            if lock.locked():
                lock.release()
        except:
            if lock and lock.locked():
                lock.release()

    def _Cachename(self, id):
        return "__c__" + str(hash(str(id)))




class UserCacheExtension(object):
    def AddToCache(self):
        sessionuser = self.SessionFactory(self.id, self)
        self.app.Cache(sessionuser, self.id)
        
    def RemoveFromCache(self):
        self.app.RemoveCache(self.id)


    def SessionFactory(self, ident, user):
        fields = ("name", "email", "surname", "lastname", "groups", "notify", "lastlogin")
        data = {}
        for f in fields:
            data[f] = user.data.get(f)
        su = SessionUser(ident, Conf(**data))
        su.currentlogin = time.time()
        return su
    

class ISessionUser(Interface):
    """ """

class SessionUser(object):
    """
    The session user is created on login by the _real_ database user and cached on app
    level. In subsequent requests the session user is loaded from cache and attached to 
    the request. 
    
    All functions are readonly. The Session User is not connected to the database or 
    application. 
    
    Lifecycle: Login adds the user to the cache. Logout removes the user from the cache.
    Updates of user values also removes the user from cache.
     
    Default data values: name, email, surname, lastname, groups
    """
    implements(ISessionUser)    
    
    def __init__(self, ident, data):
        self.ident = ident
        self.data = data
        self.lastlogin = lastlogin
        self.currentlogin = currentlogin
    
    def GetGroups(self, context=None):
        """
        Returns the users gloabal groups as tuple.
        Local assignments are not supported, `context` is currently unused.
        """
        return self.data.groups

    def InGroups(self, groups):
        """
        check if user has one of these groups
        """
        if isinstance(groups, basestring):
            return groups in self.data.groups
        for g in groups:
            if g in self.data.groups:
                return True
        return False
    
