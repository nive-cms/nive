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
import time

from nive.definitions import Interface, implements
from nive.definitions import ModuleConf, Conf
from nive.userdb.root import UserFound


"""
Session user cache
------------------
Caches simplified user objects and attaches them to request objects
as request.authenticated_userobj.

Setup:
- adds SessionUserCache object to usedb.app as userdb.usercache
- 
- listens to root *getuser* events
- listens to user *login*, *logout*, *commit*, *delete*
- listens to new request


"""

class ISessionUser(Interface):
    """ """


class SessionUserCache(object):
    """
    User caching support. Caches users including data as attributes. 
    
    Options: ::

        expires = objs are reloaded or purged after this many seconds. 0 = never expires 

    """
    expires = 20*60 

    def __init__(self, expires=None):
        if expires != None:
            self.expires = expires

    def Add(self, obj, id):
        """
        """
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            setattr(self, self._Cachename(id), (obj, time.time()))
            if lock.locked():
                lock.release()
        except Exception, e:
            if lock and lock.locked():
                lock.release()

    def Get(self, id):
        """
        """
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

    def GetAll(self):
        """
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

    def Invalidate(self, id):
        """
        """
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

    def Purge(self):
        """
        """
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            tt = time.time()
            for v in self.__dict__.keys():
                if v[:5] == "__c__" and getattr(self, v)[1]+self.expires < tt:
                    delattr(self, v)
            if lock.locked():
                lock.release()
        except:
            if lock and lock.locked():
                lock.release()

    def _Cachename(self, id):
        return "__c__" + str(hash(str(id)))


class RootListener(object):
    
    def Init(self):
        self.Listen("getuser", self.LookupCache)
        pass
    
    def LookupCache(self, ident=None, activeOnly=None):
        user = self.app.usercache.Get(ident)
        if user:
            raise UserFound, user
        
        
class UserListener(object):

    def Init(self):
        self.Listen("commit", self.InvalidateCache)
        self.Listen("logout", self.InvalidateCache)
        self.Listen("login", self.AddToCache)
    
    def AddToCache(self):
        sessionuser = self.SessionUserFactory(self.identity, self)
        self.app.usercache.Add(sessionuser, self.identity)
        
    def InvalidateCache(self):
        self.app.usercache.Invalidate(self.identity)

    def SessionUserFactory(self, ident, user):
        fields = ("name", "email", "surname", "lastname", "groups", "notify", "lastlogin")
        data = {}
        for f in fields:
            data[f] = user.data.get(f)
        su = SessionUser(ident, Conf(**data))
        return su
    

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
        self.lastlogin = data.get(u"lastlogin")
        self.currentlogin = time.time()
    
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
    
    
    
# session user module definition

def SetupRootAndUser(app, pyramidConfig):
    # get all roots and user and add Listeners
    def add(confs, extension):
        for c in confs:
            e = c.extensions
            if e == None:
                e = []
            elif extension in e:
                continue
            if isinstance(e, tuple):
                e = list(e)
            e.append(extension)
            c.unlock()
            c.extensions = tuple(e)
            c.lock()
    
    rootextension = "nive.userdb.sessionuser.RootListener"
    add(app.GetAllRootConfs(), rootextension)
    userextension = "nive.userdb.sessionuser.UserListener"
    add([app.GetObjectConf("user",skipRoot=True)], userextension)
    # add usercache to app
    app.usercache = SessionUserCache()


configuration = ModuleConf(
    id = "sessionuser",
    name = u"Session user cache",
    events = (Conf(event="startRegistration", callback=SetupRootAndUser),),

)

