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

__doc__ = """
Extension modules to store configuration values edited through the web interface.
Several backends are supported.

The functions only stores and loads the values passed to ``Save(values)``, not all configuration values.
Remaining values are loaded from python and configuration files in the file system.

For configuration storage and reference ``configuration.uid()`` is used as key.  
"""
import pickle
import time

from nive.definitions import implements, IPersistent, ModuleConf, Conf, IModuleConf
from nive.definitions import OperationalError, ProgrammingError





class PersistentConf(object):
    """
    configuration persistence base class ---------------------------------------
    """
    implements(IPersistent)
    
    def __init__(self, app, configuration):
        self.app = app
        self.conf = configuration
        
    def Load(self):
        """
        Load configuration values from backend and map to configuration.
        """
        raise TypeError, "subclass"
        
    def Save(self, values):
        """
        Store configuration values in backend.
        """
        raise TypeError, "subclass"
        
    def Changed(self):
        """
        Validate configuration and backend timestamp and check if 
        values have changed.
        """
        return False
        
    def _GetUid(self):
        return self.conf.uid()



        
def LoadStoredConfValues(app, pyramidConfig):
    # lookup persistent manager for configuration
    storage = app.Factory(IModuleConf, "persistence")
    if not storage:
        return
        # adapters
    for conf in app.registry.registeredAdapters():
        storage(app=app, configuration=conf.factory).Load()
    for conf in app.registry.registeredUtilities():
        storage(app=app, configuration=conf.component).Load()
    
    

class DbPersistence(PersistentConf):
    """
    Stores configuration values in the configured databases' pool_sys table.
    """

    def Load(self):
        """
        Load configuration values from backend and map to configuration.
        """
        try:
            db = self.app.NewDBConnection()
            sql = """select value,ts from pool_sys where uid=%s""" % (db.GetPlaceholder())
            c=db.cursor()
            c.execute(sql, (self._GetUid(),))
            data = c.fetchall()
            c.close()
        except OperationalError:
            data = None
            db.rollback()
        except ProgrammingError: 
            data = None
            db.rollback()
        db.close()
        if data:
            values = pickle.loads(data[0][0])
            lock = 0
            if self.conf.locked:
                lock = 1
                self.conf.unlock()
            self.conf.timestamp = data[0][1]
            #opt
            #for f in values.items():
            #    self.conf[f[0]] = f[1]
            self.conf.update(values)
            if lock:
                self.conf.lock()
            return values
        return None
        
    def Save(self, values):
        """
        Store configuration values in backend.
        """
        ts = time.time()
        try:
            db = self.app.NewDBConnection()
            sql = """select ts from pool_sys where uid=%s""" % (db.GetPlaceholder())
            c=db.cursor()
            c.execute(sql, (self._GetUid(),))
            r = c.fetchall()
            c.close()
            data = pickle.dumps(values)
            if len(r):
                db.UpdateFields("pool_sys", r[0][0], {"value":data,"ts":ts})
            else:
                db.InsertFields("pool_sys", {"value":data,"ts":ts, "uid":self._GetUid()})
            db.commit()
        except OperationalError: 
            data = None
            db.rollback()
        except ProgrammingError: 
            data = None
            db.rollback()
        db.close()
        lock = 0
        if self.conf.locked:
            lock = 1
            self.conf.unlock()
        self.conf.timestamp = ts
        #for f in values.items():
        #    self.conf[f[0]] = f[1]
        self.conf.update(values)
        if lock:
            self.conf.lock()
        return True
        
    def Changed(self):
        """
        Validate configuration timestamp and backend timestamp and check if 
        updates have occured.
        """
        return False


dbPersistenceConfiguration = ModuleConf(
    id = "persistence",
    name = u"Configuration persistence extension",
    context = DbPersistence,
    events = (Conf(event="finishRegistration", callback=LoadStoredConfValues),),
)

