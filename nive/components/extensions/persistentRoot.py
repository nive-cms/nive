
import json
from datetime import datetime

from nive.definitions import Conf, IConf 
from nive.definitions import Interface, implements
from nive.helper import DumpJSONConf, LoadJSONConf

        
class IPersistentRoot(Interface):
    """
    """
    
class Persistent(object):
    """
    Extension for nive root objects to store values
    
    Persistent values are can be accessed via `root.data` and `root.meta`.
    Use `Update()` or `Commit()` to store values. 
    Functions are compatible to nive objects.
    
    Meta and data values are stored as a single dict `root values` in 
    pool_sys table.
    
    Root configuration needs a list of data field definitions configuration.data.
    
    Requires: Events
    """
    implements(IPersistentRoot)
    storagekey = u"root storage"
    notifyAllRoots = True

    def Init(self):
        self.LoadStoredValues()
    
    def LoadStoredValues(self):
        """
        Load values
        
        Event: - dataloaded()
        """
        values = self.app.LoadSysValue(self.storagekey)
        if values:
            values = LoadJSONConf(values, default=Conf)
            if isinstance(values, dict) or IConf.providedBy(values):
                data, meta, files = self.SplitData(values)
                self.data.update(data)
                self.meta.update(meta)
                if not hasattr(self, "files"):
                    self.files = {}
                self.files.update(files)
        self.Signal("dataloaded")
    
    def Commit(self, user):
        """
        Commit data values
        """
        self.CommitInternal(user)
           
    def CommitInternal(self, user):
        values = {}
        if hasattr(self, "files"):
            values.update(self.files)
        values.update(self.data)
        values.update(self.meta)
        values[u"pool_change"] = datetime.now()
        values[u"pool_changedby"] = str(user)
        vstr = DumpJSONConf(values)
        self.app.StoreSysValue(self.storagekey, vstr)
        if self.notifyAllRoots:
            # call Init for other persistent roots to update values
            for root in self.app.GetRoots():
                if root.idhash == self.idhash:
                    continue
                if IPersistentRoot.providedBy(root):
                    root.LoadStoredValues()

    def Update(self, values, user):
        """
        Update and store data values
        """
        data, meta, files = self.SplitData(values)
        self.data.update(data)
        self.meta.update(meta)
        self.files.update(files)
        self.Commit(user)
        
    def SplitData(self, sourceData):
        """
        Split sourceData dictionary in data, meta and file based on this objects
        configuration. Unused fields in source data are ignored.
        
        returns data, meta, files (each as dictionary)
        """
        data = {}
        meta = {}
        files = {}
        if self.configuration.get("data"):
            for f in self.configuration.get("data"):
                id = f["id"]
                if sourceData.has_key(id):
                    if f["datatype"]=="file":
                        files[id] = sourceData[id]
                    else:
                        data[id] = sourceData[id]
        for f in self.GetApp()._meta:
            id = f["id"]
            if sourceData.has_key(id):
                meta[id] = sourceData[id]
        return data, meta, files
        
        
