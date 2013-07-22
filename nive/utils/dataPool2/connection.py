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

import threading
from time import time

# The following is used in *ConnectionRequest* classes to cahed the current db connection
# for the time of a request. if pyramid is not available the thread local stack is used
# as fallback
try:
    from pyramid.threadlocal import get_current_request
except:
    def get_current_request():
        return None

from nive.definitions import OperationalError



class Connection(object):
    """
    Base database connection class. Parameter depend on database version.

    configuration (usage depends on database type):
    user = database user
    pass = password user
    host = host server
    port = port server
    dbName = database name
    """
    
    placeholder = u"%s"

    def __init__(self, config = None, connectNow = True):
        self.configuration=config
        self.db = None
        self._vtime = time()
        if connectNow:
            self.connect()

    def __del__(self):
        self.close()

    # dbapi like functions --------------------------------------------------------------

    def cursor(self):
        db = self._get()
        if not db:
            raise OperationalError, "Database is closed"
        return db.cursor()
    
    def begin(self):
        """ Calls commit on the current transaction, if supported """
        return

    def rollback(self):
        """ Calls rollback on the current transaction, if supported """
        db = self._get()
        db.rollback()

    def commit(self):
        """ Calls commit on the current transaction, if supported """
        db = self._get()
        db.commit()

    def connect(self):
        """ Close and connect to server """
        # "use a subclassed connection"

    def close(self):
        """ Close database connection """
        db = self._get()
        if db:
            db.close()
            self._set(None)
    
    def ping(self):
        """ ping database server """
        db = self._get()
        return db.ping()


    def IsConnected(self):
        """ Check if database is connected """
        try:
            db = self._get()
            return db.cursor()!=None
        except:
            return False

    def VerifyConnection(self):
        """ 
        reconnects if not connected. If revalidate is larger than 0 IsConnected() will only be called 
        after `revalidate` time
        """
        db = self._get()
        if not db:
            return self.connect()
        conf = self.configuration
        if not conf.verifyConnection:
            return True
        if conf.revalidate > 0:
            if self._getvtime()+conf.revalidate > time():
                return True
        if not self.IsConnected():
            return self.connect()
        self._setvtime()
        return True
    
    @property
    def dbapi(self):
        """ returns the dbapi database connection """
        return self._get() or self.connect()

    def PrivateConnection(self):
        """ """
        return None

    
    def FmtParam(self, param):
        """ 
        Format a parameter for sql queries like literal for db. This function is not
        secure for any values. 
        """
        if isinstance(param, (int, long, float)):
            return unicode(param)
        d = unicode(param)
        if d.find(u'"')!=-1:
            d = d.replace(u'"',u'\\"')
        return u'"%s"'%d


    def GetDBManager(self):
        """ returns the database manager obj """
        raise TypeError, "please use a subclassed connection"


    def _get(self):
        # get stored database connection
        return self.db
        
    def _set(self, dbconn):
        # locally store database connection
        self.db = dbconn

    def _getvtime(self):
        # get stored database connection
        return self._vtime
        
    def _setvtime(self):
        # locally store database connection
        self._vtime = time()


class ConnectionThreadLocal(Connection):
    """
    Caches database connections as thread local values.
    """

    def __init__(self, config = None, connectNow = True):
        self.local = threading.local()
        Connection.__init__(self, config, False)
        
    def _get(self):
        # get stored database connection
        if not hasattr(self.local, "db"):
            return None
        return self.local.db
        
    def _set(self, dbconn):
        # locally store database connection
        self.local.db = dbconn
        
    def _getvtime(self):
        if not hasattr(self.local, "_vtime"):
            self._setvtime()
        return self.local._vtime
        
    def _setvtime(self):
        self.local._vtime = time()


class ConnectionCache(object):
    """
    Supports caching of multiple different database connection
    """
    def __init__(self):
        self.connections = {}

    def __setitem__(self, key, conn):
        self.connections[key] = conn
    
    def __getitem__(self, key):
        return self.connections[key]
    
    def close(self):
        for key, conn in self.connections.iteritems():
            conn.close()

class ConnectionRequest(Connection):
    """
    Caches database connections as webob request values. Uses thread local stack as fallback (e.g testing).
    """

    def __init__(self, config = None, connectNow = True):
        self.local = threading.local()
        Connection.__init__(self, config, False)

    def VerifyConnection(self):
        """ 
        Connection is verified when added to the request. Failures during requests are not to be 
        expected.
        """
        req = get_current_request()
        if req:
            # connect moved to _get()
            return True
        # fallback if no request available
        db = self._get()
        if not db:
            return self.connect()
        conf = self.configuration
        if not conf.verifyConnection:
            return True
        if conf.revalidate > 0:
            if self._getvtime()+conf.revalidate > time():
                return True
        if not self.IsConnected():
            return self.connect()
        return True
    
    
    def _get(self):
        # get stored database connection
        req = get_current_request()
        if not req:
            # use thread local stack as fallback
            if not hasattr(self.local, "db"):
                return None
            return self.local.db
        try:
            return req.__nive_db__[self.configuration.dbName] or  self.connect()
        except (AttributeError, KeyError):
            return self.connect()
        
    def _set(self, dbconn):
        # store database connection
        req = get_current_request()
        if not req:
            # use thread local stack as fallback
            self.local.db = dbconn
            return
        if not hasattr(req, "__nive_db__"):
            req.__nive_db__ = ConnectionCache()
        req.__nive_db__[self.configuration.dbName] = dbconn

        def CloseDatabase(request):
            try:
                request.__nive_db__.close()
                request.__nive_db__ = None
            except AttributeError:
                pass
        req.add_finished_callback(CloseDatabase)
        
    def _getvtime(self):
        if not hasattr(self.local, "_vtime"):
            self._setvtime()
        return self.local._vtime
        
    def _setvtime(self):
        self.local._vtime = time()

