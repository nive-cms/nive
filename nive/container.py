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
This file provides *container* functionality for :term:`objects` and :term:`roots`. The different components
are separated into classes by functionality. 

See :py:mod:`nive.components.objects.base` for subclassing containers.
"""

from time import time

from nive.definitions import StagContainer, StagPageElement, MetaTbl
from nive.definitions import IContainer, ICache, IObject, IConf 
from nive.definitions import ContainmentError, ConfigurationError
from nive.workflow import WorkflowNotAllowed
from nive.helper import ResolveName, ClassFactory


class Container(object):
    """
    Container implementation with read access for subobjects used for objects and roots.

    Requires: ContainerFactory
    """

    def obj(self, id, **kw):
        """ shortcut for GetObj """
        return self.GetObj(id, **kw)

    def __getitem__(self, id):
        id = id.split(".")[0]
        o = self.GetObj(id)
        if o:
            return o
        raise KeyError, id


    # Container functions ----------------------------------------------------

    def GetObj(self, id, **kw):
        """
        Get the subobject by id. ::
        
            id = object id as number
            **kw = load information
            returns the object or None
        
        Events:
        - loadObj(obj)
        """
        try:
            id = long(id)
        except:
            return None
        if not id:
            return None
        obj = self._GetObj(id, **kw)
        self.Signal("loadObj", obj)
        return obj


    def GetObjs(self, parameter = None, operators = None, **kw):
        """
        Search for subobjects based on parameter and operators. ::
        
            parameter = dict. see nive.Search
            operators = dict. see nive.Search
            kw.sort = sort objects. if None container default sort is used
            kw.batch = load subobjects as batch
            **kw = see Container.GetObj()
            returns all matching subobjects as list
    
        see :class:`nive.Search` for parameter/operators description
        
        Events
        - loadObj(obj)
        """
        if parameter==None:
            parameter = {}
        if operators==None:
            operators = {}
        parameter[u"pool_unitref"] = self.id
        sort = kw.get("sort", self.GetSort())
        fields = [u"id",u"pool_datatbl",u"pool_dataref",u"pool_type",u"pool_state"]
        root = self.root()
        if kw.get("queryRestraints")!=False:
            parameter,operators = root.ObjQueryRestraints(self, parameter, operators)
        objects = root.SelectDict(parameter=parameter, fields=fields, operators=operators, sort = sort)
        useBatch = kw.get("batch", True)
        if useBatch:
            ids = [c["id"] for c in objects]
            kw["meta"] = objects
            kw["sort"] = sort
            objs = self._GetObjBatch(ids, queryRestraint=False, **kw)
            return objs
        objs = []
        for c in objects:
            try:
                kw[u"pool_datatbl"] = c[u"pool_datatbl"]
                kw[u"pool_dataref"] = c[u"pool_dataref"]
                obj = self._GetObj(c[u"id"], queryRestraints=False, **kw)
                if obj:
                    objs.append(obj)
            except:
                pass
        self.Signal("loadObj", objs)
        return objs


    def GetObjsList(self, fields = None, parameter = None, operators = None, pool_type = None, **kw):
        """
        Search for subobjects based on parameter and operators. This function performs a sql query based on parameters and
        does not load any object. ::
        
            fields = list. see nive.Search
            parameter = dict. see nive.Search
            operators = dict. see nive.Search
            kw.sort = sort objects. if None container default sort is used
            kw.batch = load subobjects as batch
            returns dictionary list
    
        see :class:`nive.Search` for parameter/operators description
        """
        if parameter==None:
            parameter = {}
        if operators==None:
            operators = {}
        parameter[u"pool_unitref"] = self.id
        sort = kw.get("sort", self.GetSort())
        if not fields:
            fields = [u"id", u"title", u"pool_filename", u"pool_type", u"pool_state", u"pool_sort", u"pool_stag", u"pool_wfa"]
        root = self.root()
        parameter,operators = root.ObjQueryRestraints(self, parameter, operators)
        if pool_type:
            objects = root.SelectDict(pool_type=pool_type, parameter=parameter, fields=fields, operators=operators, sort = sort)
        else:
            objects = root.SelectDict(parameter=parameter, fields=fields, operators=operators, sort = sort)
        return objects
    
        
    def GetObjsBatch(self, ids, **kw):
        """
        Tries to load the objects with as few sql queries as possible. ::
        
            ids = list of object ids as number
            **kw = see Container.GetObj()
            returns all matching sub objects as list

        Events
        - loadObj(objs)
        """
        sort = kw.get("sort", self.GetSort())
        fields = [u"id",u"pool_datatbl",u"pool_dataref"]
        parameter,operators = {}, {}
        parameter[u"id"] = ids
        parameter[u"pool_unitref"] = self.id
        operators[u"id"] = "IN"
        root = self.root()
        parameter,operators = root.ObjQueryRestraints(self, parameter, operators)
        objects = root.SelectDict(parameter=parameter, fields=fields, operators=operators, sort = sort)
        ids = [c["id"] for c in objects]
        kw["meta"] = objects
        objs = self._GetObjBatch(ids, **kw)
        self.Signal("loadObj", objs)
        return objs
    
        
    def GetContainers(self, parameter = None, operators = None, **kw):
        """
        Loads all subobjects with container functionality. Uses select tag range `nive.definitions.StagContainer` to 
        `nive.definitions.StagPageElement - 1`.  ::
        
            kw.batch = load subobjects as batch and not as single object
            parameter = see pool Search
            operators = see pool Search
            **kw = see Container.GetObj()
            returns all matching sub objects as list

        see :class:`nive.Search` for parameter/operators description

        Events
        - loadObj(objs)
        """
        if parameter==None:
            parameter = {}
        if operators==None:
            operators = {}
        parameter[u"pool_stag"] = (StagContainer, StagPageElement-1)
        operators[u"pool_stag"] = u"BETWEEN"
        objs = self.GetObjs(parameter, operators, **kw)        
        return objs

        
    def GetContainerList(self, fields = None, parameter = None, operators = None, **kw):
        """
        Lists all subobjects with container functionality. Uses select tag range `nive.definitions.StagContainer` to 
        `nive.definitions.StagPageElement - 1`. This function performs a sql query based on parameters and
        does not load any object. ::

            fields = list. see nive.Search
            parameter = see pool Search
            operators = see pool Search
            kw.batch = load subobjects as batch
            **kw = see Container.GetObj()
            returns dictionary list

        see :class:`nive.Search` for parameter/operators description
        """
        if parameter==None:
            parameter = {}
        if operators==None:
            operators = {}
        parameter[u"pool_stag"] = (StagContainer, StagPageElement-1)
        operators[u"pool_stag"] = u"BETWEEN"
        return self.GetObjsList(fields, parameter, operators, **kw)
    
        
    def GetContainedIDs(self, sort=None):
        """
        Returns the ids of all contained objects including subfolders sorted by *sort*. Default is *GetSort()*.

        returns list
        """
        if not sort:
            sort = self.GetSort()
        db = self.app.db
        ids = db.GetContainedIDs(sort=sort, base=self.id)
        return ids


    def GetSort(self):
        """
        The default sort order field name.
        
        returns the field id as string
        """
        return u"title"


    def IsContainer(self):
        """ """
        return IContainer.providedBy(self)


class ContainerEdit:
    """
    Container with add and delete functionality for subobjects.

    Requires: Container
    """

    def Create(self, type, data, user, **kw):
        """
        Creates a new sub object. ::
        
            type = object type id as string or object configuration
            data = dictionary containing data for the new object
            user = the currently active user
            **kw = version information
            returns the new object or None
            
        Events
        
        - beforeCreate(data=data, type=type, kw) called for the container
        - create(kw) called for the new object
        
        Workflow actions
        
        - add (called in context of the container)
        - create (called in context of the new object)
        """
        app = self.GetApp()
        typedef = app.GetObjectConf(type)
        if not typedef:
            raise ConfigurationError, "Type not found (%s)" % (str(type))

        # allow subobject
        if not self.IsTypeAllowed(type, user):
            raise ContainmentError, "Add type not allowed here (%s)" % (str(type))

        if not self.WfAllow("add", user=user):
            raise WorkflowNotAllowed, "Not allowed in current workflow state (add)"

        self.Signal("beforeCreate", data=data, type=type, **kw)
        db = app.db
        dbEntry = None
        try:
            dbEntry = db.CreateEntry(pool_datatbl=typedef["dbparam"], user=user, **kw)
            obj = self._GetObj(dbEntry.GetID(), dbEntry = dbEntry, parentObj = self, configuration = typedef, **kw)
            obj.CreateSelf(data, user=user, **kw)
            self.WfAction("add", user=user)
            obj.Signal("create", **kw)
            if app.configuration.autocommit:
                obj.CommitInternal(user=user)
        except Exception, e:
            if dbEntry:
                id = dbEntry.GetID()
                db.DeleteEntry(id)
            db.Close()
            raise 
        return obj


    def Duplicate(self, obj, user, updateValues=None, **kw):
        """
        Duplicate the object including all data and files and store as new subobject. ::
        
            obj = the object to be duplicated
            user = the currently active user
            updateValues = dictionary containing meta, data, files
            **kw = version information
            returns new object or None
            
        Events
        
        - beforeCreate(data=data, type=type, kw) called for the container
        - duplicate(kw) called for the new object

        Workflow action

        - add (called in context of the container)
        - create (called in context of the new object)
        """
        if not updateValues:
            updateValues={}
        app = self.GetApp()
        type=obj.GetTypeID()
        # allow subobject
        if not self.IsTypeAllowed(type, user):
            raise ContainmentError, "Add type not allowed here (%s)" % (str(type))
        
        if not self.WfAllow("add", user=user):
            raise WorkflowNotAllowed, "Workflow: Not allowed (add)"

        self.Signal("beforeCreate", data=updateValues, type=type, **kw)
        newDataEntry = None
        try:
            newDataEntry = obj.dbEntry.Duplicate()
            updateValues["pool_unitref"] = self.GetID()
            data, meta, files = obj.SplitData(updateValues)
            newDataEntry.meta.update(meta)
            newDataEntry.data.update(data)
            newDataEntry.files.update(files)
            id = newDataEntry.GetID()
            typedef = obj.configuration
    
            newobj = self._GetObj(id, dbEntry = newDataEntry, parentObj = self, configuration = typedef)
            newobj.CreateSelf(data, user=user)
            newobj.Signal("duplicate", **kw)
            
        except Exception, e:
            if newDataEntry:
                id = newDataEntry.GetID()
                db = app.db
                db.DeleteEntry(id)
                db.Close()
            raise 

        try:    
            if obj.IsContainer():
                for o in obj.GetObjs(queryRestraints=False):
                    newobj._RecursiveDuplicate(o, user, **kw)
            self.WfAction("add", user=user)
            if app.configuration.autocommit:
                newobj.CommitInternal(user=user)
        except Exception, e:
             self._DeleteObj(newobj)
             raise 
         
        return newobj
    
        
    def _RecursiveDuplicate(self, obj, user, **kw):
        """
        Recursively duplicate all subobjects. 
        """
        type=obj.GetTypeID()
        
        updateValues = {}
        self.Signal("beforeCreate", data=updateValues, type=type, **kw)
        newDataEntry = obj.dbEntry.Duplicate()
        updateValues["pool_unitref"] = self.GetID()
        data, meta, files = obj.SplitData(updateValues)
        newDataEntry.meta.update(meta)
        newDataEntry.data.update(data)
        newDataEntry.files.update(files)
        id = newDataEntry.GetID()
        typedef = obj.configuration

        newobj = self._GetObj(id, dbEntry = newDataEntry, parentObj = self, configuration = typedef)
        newobj.CreateSelf({}, user=user)
        newobj.Signal("duplicate", **kw)
        
        if obj.IsContainer():
            for o in obj.GetObjs(queryRestraints=False):
                newobj._RecursiveDuplicate(o, user, **kw)

        if self.app.configuration.autocommit:
            newobj.CommitInternal(user=user)


    def Delete(self, id, user, obj=None, **kw):
        """
        Delete the subobject referenced by id. ::
        
            id = id of object to be deleted
            user = the currently active user
            obj = the object to be deleted. Will be loaded automatically if None
            **kw = version information
            returns True or False
        
        Events
        
        - delete() called on object to be deleted
        - afterDelete(id=id) called on container after object has been deleted

        Workflow action

        - remove (called in context of the container)
        - delete (called in context of the new object)
        """
        app = self.GetApp()
        if not obj:
            obj = self.GetObj(id, queryRestraints=False, **kw)
            if not obj:
                return False
        if obj.GetParent().id!=self.id:
            raise ContainmentError, "Object is not a child (%s)" % (str(id))

        # call workflow
        if not self.WfAllow("remove", user=user):
            raise WorkflowNotAllowed, "Workflow: Not allowed (remove)"
        if not obj.WfAllow("delete", user=user):
            raise WorkflowNotAllowed, "Workflow: Not allowed (delete)"
        obj.Signal("delete")
        if hasattr(obj, "_RecursiveDelete"):
            obj._RecursiveDelete(user)

        # call workflow
        obj.WfAction("delete", user=user)
        self._DeleteObj(obj)
        if app.configuration.autocommit:
            self.db.Commit()
        self.WfAction("remove", user=user)
        self.Signal("afterDelete", id=id)

        return True


    def DeleteInternal(self, id, user, obj=None, **kw):
        """
        Like *Delete()* but does not call any workflow action. ::
        
            id = id of object to be deleted
            user = the currently active user
            obj = the object to be deleted. Will be loaded automatically if None
            **kw = version information
            returns True or False

        Events
        
        - delete() called on object to be deleted
        - afterDelete(id=id) called on container after object has been deleted
        """
        app = self.GetApp()
        if not obj:
            obj = self.GetObj(id, queryRestraints=False, **kw)
        else:
            if not obj.GetParent()==self:
                raise ContainmentError, "Object is not a child (%s)" % (str(id))
        obj.Signal("delete")
        if hasattr(obj, "_RecursiveDeleteInternal"):
            obj._RecursiveDeleteInternal(user)
        self._DeleteObj(obj)
        self.Signal("afterDelete", id=id)
        return 1


    def _RecursiveDelete(self, user):
        """
        Recursively deletes all subobjects
        """
        objs = self.GetObjs(queryRestraints=False)
        for o in objs:
            self.Delete(o.id, obj=o, user=user)


    def _RecursiveDeleteInternal(self, user):
        """
        Recursively deletes all subobjects
        """
        objs = self.GetObjs(queryRestraints=False)
        for o in objs:
            self.DeleteInternal(o.id, obj=o, user=user)
            
            
class ContainerSecurity:
    """
    Provides functionality to allow or disallow the creation of objects based
    on object configuration.subtypes.
    """

    def GetAllowedTypes(self, user=None, visible=1):
        """
        List types allowed to be created in this container based on
        configuration.subtypes.    ::
        
            user = the currently active user
            visible = will skip all hidden object types 
            returns list of configurations
            
        """
        subtypes = self.configuration.subtypes
        if not subtypes:
            return False
        all = self.app.GetAllObjectConfs(visibleOnly=visible)
        if subtypes == "*":
            return all

        # check types by interface
        allowed = []
        for conf in all:
            # create type from configuration
            type = self._GetVirtualObj(conf)
            if not type:
                continue
            # loop subtypes
            for iface in subtypes:
                if isinstance(iface, basestring):
                    iface = ResolveName(iface, raiseExcp=False)
                    if not iface:
                        continue
                try:
                    if iface.providedBy(type):
                        allowed.append(conf)
                except:
                    pass
        return allowed


    def IsTypeAllowed(self, type, user=None):
        """
        Check if *type* is allowed to be created in this container based on
        configuration.subtypes.::
        
            type = the type to be checked
            user = the currently active user
            returns True/False
        
        *type* can be passed as
        
        - type id string
        - configuration object
        - type object instance
        """
        if not type:
            return False
        subtypes = self.configuration.subtypes
        if subtypes == "*":
            return True
        if not subtypes:
            return False
        if isinstance(type, basestring):
            # dotted python to obj configuration
            type = self.app.GetObjectConf(type)
            if not type:
                return False
            # create type from configuration
            type = self._GetVirtualObj(type)
            if not type:
                return False
        if not IObject.providedBy(type) and not IConf.providedBy(type):
            return False
        # loop subtypes
        for iface in subtypes:
            if isinstance(iface, basestring):
                iface = ResolveName(iface, raiseExcp=False)
                if not iface:
                    continue
            try:
                if iface.providedBy(type):
                    return True
            except:
                pass
        return False
    

class ContainerFactory:
    """
    Container object factory. Creates objects based on type configuration.
    """

    def _GetObj(self, id, dbEntry = None, parentObj = None, configuration = None, **kw):
        """
        Loads and initializes the object. ::
        
            id = id of the object to be loaded
            dbEntry = the database entry. Will be loaded automatically if None
            parentObj = if a different parent than the container
            configuration = the object configuration to be loaded
            returns the object or None
            
        """
        useCache = ICache.providedBy(self)
        if useCache:
            o = self.GetFromCache(id)
            if o:
                return o
        app = self.app
        if not dbEntry:
            # check restraints
            qr = kw.get("queryRestraints",None)
            if qr!=False:
                root = self.root()
                p,o = root.ObjQueryRestraints(self)
                p["id"] = id
                e = root.Select(parameter=p, operators=o)
                if len(e)==0:
                    return None

            dbEntry = app.db.GetEntry(id, **kw)
            if not dbEntry:
                return None
                #raise Exception, "NotFound"

        # create object for type
        if not parentObj:
            parentObj = self
        obj = None
        if not configuration:
            type = dbEntry.GetMetaField("pool_type")
            if not type:
                raise ConfigurationError, "Type not found (%s)" % (str(type))
            configuration = app.GetObjectConf(type)
            if not configuration:
                raise ConfigurationError, "Type not found (%s)" % (str(type))
        obj = ClassFactory(configuration, app.reloadExtensions, True, base=None)
        obj = obj(id, dbEntry, parent=parentObj, configuration=configuration, **kw)
        if useCache:
            self.Cache(obj, obj.id)
        return obj


    def _GetVirtualObj(self, configuration):
        """
        This loads an object for a non existing database entry.
        """
        if not configuration:
            raise ConfigurationError, "Type not found"
        app = self.app
        obj = ClassFactory(configuration, app.reloadExtensions, True, base=None)
        dbEntry = app.db.GetEntry(0, virtual=1)
        obj = obj(0, dbEntry, parent=None, configuration=configuration)
        return obj

    
    def _GetObjBatch(self, ids, parentObj = None, **kw):
        """
        Load multiple objects at once.
        """
        if len(ids)==0:
            return []
        useCache = ICache.providedBy(self)
        objs = []
        if useCache:
            load = []
            for id in ids:
                o = self.GetFromCache(id)
                if o:
                    objs.append(o)
                else:
                    load.append(id)
            if len(load)==0:
                return objs
            ids = load

        app = self.GetApp()
        entries = app.db.GetBatch(ids, preload="all", **kw)

        # create object for type
        if not parentObj:
            parentObj = self
        for dbEntry in entries:
            obj = None
            type = dbEntry.meta.get("pool_type")
            if not type:
                continue
            configuration = app.GetObjectConf(type, skipRoot=1)
            if not configuration:
                continue
            obj = ClassFactory(configuration, app.reloadExtensions, True, base=None)
            obj = obj(dbEntry.id, dbEntry, parent=parentObj, configuration=configuration, **kw)
            if useCache:
                self.Cache(obj, obj.id)
            objs.append(obj)
        return objs


    def _CloseObj(self):
        pass

    def _DeleteObj(self, obj, id=0):
        """
        Deletes the object and additional data from wfdata, wflog, fulltext,
        security tables.
        """
        if obj:
            id = obj.GetID()
        obj.Close()
        db = self.db
        if id > 0:
            db.DeleteEntry(id)



class Root(object):
    """
    The root is a container for objects but does not store any data in the database itself. It
    is the entry point for object access. Roots are only handled by the application. 

    Requires (Container, ContainerFactory, Event)
    """
    
    def __init__(self, path, app, rootDef):
        self.__name__ = str(path)
        self.__parent__ = app
        self.id = abs(hash(self.__name__))*-1
        self.path = path
        self.app_ = app
        self.configuration = rootDef
        self.queryRestraints = {}, {}

        self.meta = {"pool_type": rootDef["id"], "title": rootDef["name"], "pool_state": 1, "pool_filename": path, "pool_wfa": u""}
        self.data = {}
        self.Signal("init")


    # Properties -----------------------------------------------------------

    def root(self):
        """ this will return itself. Used for object compatibility. """
        return self

    @property
    def app(self):
        """ returns the cms application the root is used for """
        return self.app_

    @property
    def db(self):
        """ returns the datapool object """
        return self.app_.db

    @property
    def parent(self):
        """ this will return None. Used for object compatibility. """
        return None

    # Object Lookup -----------------------------------------------------------

    def LookupObj(self, id, **kw):
        """
        Lookup the object referenced by id *anywhere* in the tree structure. Use obj() to 
        restrain lookup to the first sublevel only. ::
        
            id = number
            **kw = version information
        
        returns the object or None
        """
        try:
            id = long(id)
        except:
            return None
        if id <= 0:
            return self
        if not id:
            return None
            #raise Exception, "NotFound"

        # proxy object
        if kw.has_key("proxyObj") and kw["proxyObj"]:
            obj = obj._GetObj(id, parentObj = kw["proxyObj"], **kw)
            if not obj:
                raise ContainmentError, "Proxy object not found"
            return obj

        # load tree structure
        path = self.app_.db.GetParentPath(id)
        if path == None:
            return None
            #raise Exception, "NotFound"
        
        # check and adjust root id
        if hasattr(self, "rootID"):
            if self.rootID in path:
                path = path[path.index(self.rootID)+1:]
        if hasattr(self.app_, "rootID"):
            if self.app_.rootID in path:
                path = path[path.index(self.app_.rootID)+1:]

        # reverse lookup of object tree. loads all parent objs.
        path.append(id)
        #opt
        obj = self
        for id in path:
            if id == self.id:
                continue
            obj = obj._GetObj(id, **kw)
            if not obj:
                return None
                #raise Exception, "NotFound"
        return obj


    def LookupTitle(self, id):
        """
        Lookup the object title referenced by id *anywhere* in the tree structure.
        
        returns title as string or empty string
        """
        p, o = self.ObjQueryRestraints(self)
        p["id"] = id
        v = self.Select(parameter = p, operators = o, fields = [u"title"], start = 0, max = 1)
        if len(v):
            return v[0][0]
        return ""


    def ObjQueryRestraints(self, containerObj=None, parameter=None, operators=None):
        """
        The functions returns two dictionaries (parameter, operators) used to restraint
        object lookup in subtree. For example a restraint can be set to ignore all
        objects with meta.pool_state=0. All container get (GetObj, GetObjs, ...) functions 
        use query restraints internally. 
        
        See `nive.search` for parameter and operator usage.
        
        Please note: Setting the wrong values for query restraints can easily crash 
        the application. 
        
        Event:
        - loadRestraints(parameter, operators)
        
        returns parameter dict, operators dict
        """
        p, o = self.queryRestraints
        if parameter:
            parameter.update(p)
            if operators:
                operators.update(o)
            else:
                operators = o.copy()
        else:
            parameter=p.copy()
            operators=o.copy()
        self.Signal("loadRestraints", parameter=parameter, operators=operators)
        return parameter, operators


    # Values ------------------------------------------------------

    def GetID(self):
        """ returns 0. the root id is always zero. """
        return self.id

    def GetTypeID(self):
        """ returns the root type id from configuration """
        return self.configuration.id

    def GetTypeName(self):
        """ returns the root type name from configuration """
        return self.configuration.name

    def GetTitle(self):
        """ returns the root title from configuration. """
        return self.meta["title"]

    def GetPath(self):
        """ returns the url path name as string. """
        return self.__name__


    # Parents ----------------------------------------------------

    def IsRoot(self):
        """ returns always True. """
        return True

    def GetRoot(self):
        """ returns self. """
        return self

    def GetApp(self):
        """ returns the cms application. """
        return self.app_

    def GetParent(self):
        """ returns None. """
        return None

    def GetParents(self):
        """ returns empty list. Used for object compatibility. """
        return []

    def GetParentIDs(self):
        """ returns empty list. Used for object compatibility. """
        return []

    def GetParentTitles(self):
        """ returns empty list. Used for object compatibility. """
        return []

    def GetParentPaths(self):
        """ returns empty list. Used for object compatibility. """
        return []


    # tools ----------------------------------------------------

    def GetTool(self, name):
        """
        Load a tool in the roots' context. Only works for tools registered for roots or this root type. ::
            
            returns the tool object or None
        
        Event
        - loadToool(tool=toolObj)
        """
        t = self.app.GetTool(name, self)
        self.Signal("loadTool", tool=t)
        return t


    def Close(self):
        """
        Close the root and all contained objects. Currently only used in combination with caches.
        
        Event
        - close()
        """
        self.Signal("close")
        if ICache.providedBy(self):
            #opt
            for o in self.GetAllFromCache():
                o.Close()
        return


class RootWorkflow:
    """
    Provides workflow functionality for roots. 
    Workflow process objects are handled and loaded by the application. Meta layer fields `pool_wfp` stores the 
    process id and `pool_wfa` the current state.
    """

    def WfAllow(self, action, user, transition = None):
        """
        Check if action is allowed in current state in workflow. This functions returns True or False
        and unlike WFAction() will not raise a WorkflowNotAllowed Exception.
        
        Event: 
        - wfAllow(name)

        returns bool
        """
        wf = self.GetWf()
        if not wf:
            return True
        self.Signal("wfAllow", name=action)
        return wf.Allow(action, self, user=user, transition=transition)


    def WfAction(self, action, user, transition = None):
        """
        Trigger workflow action. If several transitions are possible for the action in the current state
        the first is used. In this case the transition id can be passed as parameter.
        
        Event: 
        - wfAction(name)

        raises WorkflowNotAllowed 
        """
        wf = self.GetWf()
        if not wf:
            return 
        wf.Action(action, self, user=user, transition=transition)
        self.Signal("wfAction", name=action)


    def GetWf(self):
        """
        Returns the workflow process for the object.

        Event: 
        - wfLoad(workflow) 
        
        returns object
        """
        app = self.app
        if not app.configuration.workflowEnabled:
            return None
        wfTag = self.GetNewWf()
        if not wfTag:
            return None
        # load workflow
        wf = app.GetWorkflow(wfTag, contextObject=self)
        # enable strict workflow checking
        if not wf:
            raise ConfigurationError, "Workflow process not found (%s)"%(wfTag)
        self.Signal("wfLoad", workflow=wf)
        return wf


    def GetNewWf(self):
        """
        Returns the workflow process id for the object based on configuration settings. 

        returns string
        """
        if self.configuration.workflowDisabled:
            return ""
        return self.configuration.workflowID


    def GetWfInfo(self, user):
        """
        returns the current workflow state as dictionary
        """
        wf = self.GetWf()
        if not wf:
            return {}
        return wf.GetObjInfo(self, user)


    def GetWfState(self):
        """
        """
        return self.meta["pool_wfa"]


    def SetWfState(self, stateID):
        """
        Sets the workflow state for the object. The new is state is set
        regardless of transitions or calling any workflow actions.
        """
        self.meta["pool_wfa"] = stateID

    

