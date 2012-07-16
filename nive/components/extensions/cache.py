#----------------------------------------------------------------------
# Nive CMS
# Copyright (C) 2012  Arndt Droullier, DV Electric, info@dvelectric.com
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

from time import time
import thread

from nive.definitions import ICache, implements


class ContainerCache:
    """
    Object caching support
    
    Caches loaded objects including data as attributes. Subsequent lookups
    won't access the database to load the object.
    
    Options ::
    
        useCache =   enable or disable caching
        cacheTypes = a list of pool_types to be cached. not matching types 
                     are not cached
        expires =    objs are reloaded or purged after this many seconds. 
                     0 = never expires 
                     
    The cache is currently not *edit* aware and only recommended for readonly
    pages.
    """
    implements(ICache)
    useCache = True
    cacheTypes = None
    expires = 0 

    def Cache(self, obj, id):
        """
        """
        if not self.useCache:
            return True
        try:
            t = obj.GetTypeID()
            if self.cacheTypes and not t in self.cacheTypes:
                return False
        except:
            if self.cacheTypes:
                return False
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            setattr(self, self._Cachename(id), (obj, time()))
            if lock.locked():
                lock.release()
        except:
            if lock and lock.locked():
                lock.release()
            return False
        return True

    def GetFromCache(self, id=0):
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
            return True
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
        return True

    def _Cachename(self, id):
        return "__c__" + str(id)
