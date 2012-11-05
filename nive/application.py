#----------------------------------------------------------------------
# Nive cms
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
This file contains the main application functionality. The application handles configuration
registration, roots and the database. Also it provides convenient functions to lookup all
different kinds of configurations. 

Application.modules stores configuration objects registered by calling `Register()`. 

See Application.Startup() for the main entry point and connected events. 

Not to be mixed up with pyramid applications or projects. It is possible to use multiple nive
applications in a single pyramid app.
"""
from nive import __version__

import copy
import logging

from time import time
from types import DictType

from zope.interface.registry import Components
from zope.interface import providedBy

from nive.utils.dataPool2.structure import PoolStructure
from nive.i18n import _

from nive.definitions import AppConf, DatabaseConf, SystemFlds, MetaTbl, ReadonlySystemFlds
from nive.definitions import IViewModuleConf, IViewConf, IRootConf, IObjectConf, IToolConf 
from nive.definitions import IAppConf, IDatabaseConf, IModuleConf, IWidgetConf

from nive.security import User, authenticated_userid
from nive.helper import ResolveName, ResolveConfiguration, FormatConfTestFailure, GetClassRef, ClassFactory
from nive.tools import _IGlobal, _GlobalObject
from nive.workflow import IWfProcessConf
from nive.utils.utils import SortConfigurationList


class Application(object):
    """
    nive Application implementaion.

    SQLite example:
    ::
    
        conf = AppConf(id="website", title="nive app", 
                       dbConfiguration = DatabaseConf(context="Sqlite3", 
                                                      fileRoot="data", 
                                                      dbName="data/ewp.db")
        )
    
    MySql example:
    ::
    
        conf = AppConf(id="website", title="nive app", 
                       dbConfiguration = DatabaseConf(context="MySql", 
                                                      fileRoot="data", 
                                                      dbName="nive",
                                                      host="localhost",
                                                      user="user",
                                                      password="password")
        )

    Requires (Configuration, Registration, AppFactory, Events.Events)
    """
    
    def __init__(self, configuration=None):
        """
        Use configuration and dbConfiguration objects to setup your application.
        
        Events:
        - init(configuration)
        """
        self.registry = Components()
        self.configuration = AppConf()
        self.dbConfiguration = DatabaseConf()
        # set id for logging
        if configuration:
            self.id = configuration.id
        else:
            self.id = __name__
        #bw 0.9.3
        self.modules = self.registry
        
        self.__name__ = u""
        self.__parent__ = None
        self.__acl__ = []

        # 0.9.4 - moved to configuration
        #self.id = u""
        #self.title = u""
        #self.description = u""
    
        # data pool
        # 0.9.4 - moved to configuration
        #self.fulltextIndex = False
        #self.autocommit = True
        #self.useCache = True
        #self.frontendCodepage = "utf-8"
        #self.workflowEnabled = False
        #self.groups = []
        #self.categories = []
        # development
        self.debug = False
        self.reloadExtensions = False
    
        # internal configuration
        self._defaultRoot = ""
        self._meta = copy.deepcopy(SystemFlds)
        self._views = []
        # cache database structure 
        self._structure = PoolStructure()
        self._dbpool = None
        log = logging.getLogger(self.id)
        log.debug("Initialize %s", repr(configuration))
        self.Signal("init", configuration=configuration)

        if configuration:
            self.Register(configuration)
        
    def __del__(self):
        self.Close()
        

    def Startup(self, pyramidConfig, debug=False):
        """
        Called by nive.portal.portal on application startup.

        Events (in order):

        - startup(app)
        - startRegistration(app, pyramidConfig)
        - finishRegistration(app, pyramidConfig)
        - run(app)
        """
        t = time()
        log = logging.getLogger(self.id)
        log.debug("Startup with debug=%s", str(debug))
        self.Signal("startup", app=self)
        self.SetupRegistry()
        self.debug = debug
        # disable caching during startup
        #cache = self.configuration.useCache
        #self.configuration.useCache = False
        
        self.Signal("startRegistration", app=self, pyramidConfig=pyramidConfig)
        # register pyramid views 
        if pyramidConfig:
            pyramidConfig = self.RegisterViewModules(pyramidConfig)
            pyramidConfig.commit()
            pyramidConfig = self.RegisterViews(pyramidConfig)
            pyramidConfig.commit()

        # register groups
        portal = self.portal
        if portal and hasattr(portal, "RegisterGroups"):
            portal.RegisterGroups(self)
        self.Signal("finishRegistration", app=self, pyramidConfig=pyramidConfig)
        log.debug('Finished registration.')
        
        # reload database structure
        self.LoadStructure(forceReload = True)
        self._dbpool = self._GetDataPoolObj()
                           
        # test and create database fields 
        if debug:
            self.GetTool("nive.components.tools.dbStructureUpdater", self).Run()
            result, report = self.TestDB()
            if not result:
                log.error('Database test result: %s %s', str(result), ", ".join(report))
            else:
                log.info('Database test result: %s %s', str(result), ", ".join(report))
            if not self._structure.get(u"pool_meta"):
                log.error('No meta fields in _structure %s', repr(self._structure))
 
        # reset caching after startup
        #self.configuration.useCache = cache
        self._Lock()
        
        # start
        self.Signal("run", app=self)
        log.info('Application running. Runtime logging as [%s]. Startup time: %.05f.', self.configuration.id, time()-t)
        self.id = self.configuration.id

    
    def Close(self):
        """
        Close database and roots.
        """
        self._CloseRootObj()
        if self._dbpool:
            self._dbpool.Close()



    # Properties -----------------------------------------------------------

    def root(self, name=""):
        """ returns root object     """
        return self._GetRootObj(name)

    def obj(self, id, rootname = "", **kw):
        """ returns object    """
        return self.LookupObj(id, rootname, **kw)

    @property
    def db(self):
        """ returns datapool object    """
        return self._dbpool

    @property
    def portal(self):
        """ returns the portal    """
        return self.__parent__

    @property
    def app(self):
        """ returns itself. for compatibility.    """
        return self

    # Content and root objects -----------------------------------------------------------

    def __getitem__(self, name):
        """
        This function is called by url traversal and looks up root objects for the corresponding
        name. 
        """
        name = name.split(".")[0]
        o = self.root(name)
        if o and o.configuration.urlTraversal:
            return o
        raise KeyError, name


    def GetRoot(self, name=""):
        """
        Returns the data root object. If name is empty the default root is returned.
        
        returns root object
        """
        return self._GetRootObj(name)


    def GetRoots(self):
        """
        Returns all root objects.
        
        returns list
        """
        return [self.GetRoot(r.id) for r in self.GetAllRootConfs()]


    def GetApp(self):
        return self


    def GetPortal(self):
        return self.__parent__

    
    def GetTool(self, toolID, contextObject=None):
        """
        Load tool object. *toolID* must be the tool.id or dotted python name.
        
        returns the tool object.
        """
        return self._GetToolObj(toolID, contextObject or _GlobalObject())


    def GetWorkflow(self, wfProcID, contextObject=None):
        """
        Load workflow process. *wfProcID* must be the wf.id or dotted python name.
        
        returns the workflow object
        """
        if not self.configuration.workflowEnabled or wfProcID == "":
            return None
        return self._GetWfObj(wfProcID, contextObject or _GlobalObject())


    def NewDBConnection(self):
        """
        Creates a new database connection. This one is independent from caching and 
        connections used internally.  
        """
        return self._GetConnectionObj()
        
    # Data Pool ------------------------------------------------------------------------------

    def GetDB(self):
        """
        Create data pool object and database connection.
        
        returns the datapool object
        """
        return self._dbpool


    def LookupObj(self, id, rootname = "", **kw):
        """
        Returns the object for the id. if root name is empty the default root is used.
        
        returns object
        """
        root = self.GetRoot(rootname)
        return root.LookupObj(id, **kw)


    def Query(self, sql, values = []):
        """
        Start a sql query on the database. 
        
        returns tuple or none
        """
        db = self.db
        r = db.Query(sql, values)
        return r


    def GetCountEntries(self):
        """
        Get the total number of entries in the data pool.
        
        returns number
        """
        db = self.db
        c = db.GetCountEntries()
        return c


    def TestDB(self):
        """
        Test database connection for errors. Returns state and list with errors.
        
        returns bool, list
        """
        try:
            e = []
            db = self.db
            if not db.connection.IsConnected():
                return False, e
            return True, e

        except Exception, err:
            e.append(str(err))
            return False, e


    def ConvertID(self, id):
        """
        Convert id to number.
        
        returns number
        """
        try:
            return int(id)
        except:
            return -1


    def GetVersion(self):
        """ """
        return __version__, __version__

    def CheckVersion(self):
        """ """
        return __version__ == __version__


class Registration(object):

    def Register(self, module, **kw):
        """
        Include a module or configuration to store in the registry.

        Handles configuration objects with the following interfaces:
        
        - IAppConf
        - IRootConf
        - IObjectConf
        - IViewModuleConf
        - IViewConf 
        - IToolConf
        - IModuleConf
        - IWidgetConf
        - IWfProcessConf
        
        Other modules are registered as utility with **kws as parameters.
        
        raises TypeError, ConfigurationError, ImportError
        """
        log = logging.getLogger(self.id)
        iface, conf = ResolveConfiguration(module)
        if not conf:
            try:
                log.debug('Register module: %s', str(module))
                return self.registry.registerUtility(module, **kw)
            except Exception, e:
                raise ConfigurationError, str(module)
        
        # test conf
        if self.debug:
            r=conf.test()
            if r:
                v = FormatConfTestFailure(r)
                log.warn('Configuration test failed:\r\n%s', v)
                #return False
        
        log.debug('Register module: %s %s', str(conf), str(iface))
        # register module views
        if iface not in (IViewModuleConf, IViewConf):
            self.RegisterConfViews(conf)
            
        # reset cached class value. makes testing easier
        try:
            del conf._v_class
        except:
            pass
            
        # register module itself
        conf.unlock()
        if iface == IRootConf:
            self.registry.registerUtility(conf, provided=IRootConf, name=conf.id)
            if conf.default or not self._defaultRoot:
                self._defaultRoot = conf.id
            return True
        elif iface == IObjectConf:
            self.registry.registerUtility(conf, provided=IObjectConf, name=conf.id)
            return True

        elif iface == IViewConf:
            self.registry.registerUtility(conf, provided=IViewConf, name=conf.id)
            return True
        elif iface == IViewModuleConf:
            self.registry.registerUtility(conf, provided=IViewModuleConf, name=conf.id)
            if conf.widgets:
                for w in conf.widgets:
                    self.Register(w)
            return True

        elif iface == IToolConf:
            if conf.apply:
                for i in conf.apply:
                    if i == None:
                        self.registry.registerAdapter(conf, (_IGlobal,), IToolConf, name=conf.id)
                    else:
                        self.registry.registerAdapter(conf, (i,), IToolConf, name=conf.id)
            else:
                self.registry.registerAdapter(conf, (_IGlobal,), IToolConf, name=conf.id)
            return True

        elif iface == IAppConf:
            self.registry.registerUtility(conf, provided=IAppConf, name="IApp")
            if conf.modules:
                for m in conf.modules:
                    self.Register(m)
            return True
        
        elif iface == IDatabaseConf:
            self.registry.registerUtility(conf, provided=IDatabaseConf, name="IDatabase")
            return True
        
        elif iface == IModuleConf:
            # events
            if conf.events:
                for e in conf.events:
                    log.debug('Register Event: %s for %s', str(e.event), str(e.callback))
                    self.RegisterEvent(e.event, e.callback)
            # modules
            if conf.modules:
                for m in conf.modules:
                    self.Register(m, **kw)
            self.registry.registerUtility(conf, provided=IModuleConf, name=conf.id)
            return True

        elif iface == IWidgetConf:
            for i in conf.apply:
                self.registry.registerAdapter(conf, (i,), conf.widgetType, name=conf.id)
            return True

        elif iface == IWfProcessConf:
            if conf.apply:
                for i in conf.apply:
                    self.registry.registerAdapter(conf, (i,), IWfProcessConf, name=conf.id)
            else:
                self.registry.registerAdapter(conf, (_IGlobal,), IWfProcessConf, name=conf.id)
            return True

        raise TypeError, "Unknown configuration interface type (%s)" % (str(conf))
        
        
        
    def RegisterConfViews(self, conf):    
        # register views included in configuration.views
        views = None
        try: 
            views = conf.views
        except:
            pass
        if not views:
            return
        for v in views:

            if isinstance(v, basestring):
                iface, conf = ResolveConfiguration(v)
                if not conf:
                    raise ConfigurationError, str(v)
                v = conf
                
            self.Register(v)


    def SetupRegistry(self):
        """
        Loads self.configuration, includes modules and updates meta fields.
        """
        c = self.registry.queryUtility(IAppConf, name="IApp")
        if c:
            self.configuration = c
        # bw 0.9.3
        if not self.configuration:
            raise TypeError, "Application configuration is not set"
        
        def idinlist(l, id):
            for i in l:
                if i["id"] == id:
                    return True
            return False

        c = self.configuration
        for k in c.keys():
            # special values
            if k == "id" and c.id:
                self.__name__ = c.id
            if k == "acl" and c.acl:
                self.__acl__ = c.acl
                continue
            if k == "meta" and c.meta:
                temp = []
                for system in self._meta:
                    if idinlist(c.meta, system["id"]):
                        continue
                    temp.append(system)
                for m in c.meta:
                    temp.append(m)
                self._meta = temp
                continue
            if k == "dbConfiguration" and c.dbConfiguration:
                if type(c.dbConfiguration) == DictType:
                    self.dbConfiguration = DatabaseConf(**c.dbConfiguration)
                else:
                    self.dbConfiguration = c.dbConfiguration
                continue
            
            # map value
            #setattr(self, k, c[k])

        dbc = self.registry.queryUtility(IDatabaseConf, name="IDatabase")
        # bw 0.9.3
        if dbc:
            self.dbConfiguration = dbc
        

    def RegisterViews(self, config):
        """
        Register configured views and static views with the pyramid web framework.
        """
        views = self.registry.getAllUtilitiesRegisteredFor(IViewConf)
        # single views
        for view in views:
            config.add_view(view=view.view,
                            context=view.context,
                            attr=view.attr,
                            name=view.name,
                            renderer=view.renderer,
                            permission=view.permission,
                            containment=view.containment,
                            custom_predicates=view.custom_predicates or (self.AppViewPredicate,),
                            **view.options)
            #try:
            #except Exception, e:
            #    pass
        return config


    def RegisterViewModules(self, config):
        """
        Register configured views and static views with the pyramid web framework.
        """
        mods = self.registry.getAllUtilitiesRegisteredFor(IViewModuleConf)
        for viewmod in mods:
            # object views
            for view in viewmod.views:
                config.add_view(attr=view.attr,
                                name=view.name,
                                view=view.view or viewmod.view,
                                context=view.context or viewmod.context,
                                renderer=view.renderer,
                                permission=view.permission or viewmod.permission,
                                containment=view.containment or viewmod.containment,
                                custom_predicates=view.custom_predicates or viewmod.custom_predicates or (self.AppViewPredicate,),
                                **view.options)
                #try:
                #except Exception, e:
                #    raise ConfigurationError, str(view)
            
            # static views
            maxage = 60*60*4
            if self.debug:
                maxage = None
            config.add_static_view(name=viewmod.staticName or viewmod.id, path=viewmod.static, cache_max_age=maxage)
        
        return config


    def AppViewPredicate(self, context, request):
        """
        Check if context of view is this application. For multisite support.
        """
        app = context.app
        return app == self
    AppViewPredicate.__text__ = "nive.AppViewPredicate"
        
        
    def _Lock(self):
        # lock all configurations
        # adapters
        for a in self.registry.registeredAdapters():
            try:       a.factory.lock()
            except:    pass
        for a in self.registry.registeredUtilities():
            try:       a.component.lock()
            except:    pass


    # bw 0.9.3
    def Include(self, module, **kw):
        return self.Register(module, **kw)

    def LoadConfiguration(self):
        return self.SetupRegistry()

    
    


class Configuration:
    """
    Read access functions for root, type, type field, meta field and category configurations.

    Requires:
    - nive.nive
    """

    def QueryConf(self, queryFor, context=None):
        """
        returns configuration or None
        """
        if isinstance(queryFor, basestring):
            queryFor = ResolveName(queryFor)
        if context:
            return self.registry.getAdapters((context,), queryFor)
        return self.registry.getAllUtilitiesRegisteredFor(queryFor)

    def QueryConfByName(self, queryFor, name, context=None):
        """
        returns configuration or None
        """
        if isinstance(queryFor, basestring):
            queryFor = ResolveName(queryFor)
        if context:
            return self.registry.queryAdapter(context, queryFor, name=name)
        return self.registry.queryUtility(queryFor, name=name)
    
    
    def Factory(self, queryFor, name, context=None):
        """
        Query for configuration and lookup class reference. Does not call __init__ for
        the new class.
        
        returns class or None
        """
        c = self.QueryConfByName(queryFor, name, context=context)
        if not c:
            return None
        return ClassFactory(c)


    # Roots -------------------------------------------------------------

    def GetRootConf(self, name=""):
        """
        Get the root object configuration. If name is empty, the default name is used.
        
        returns dict or None
        """
        if name == "":
            name = self._defaultRoot
        return self.registry.queryUtility(IRootConf, name=name)


    def GetAllRootConfs(self):
        """
        Get all root object configurations as list.
        
        returns list
        """
        return self.registry.getAllUtilitiesRegisteredFor(IRootConf)


    def GetRootIds(self):
        """
        Get all root object ids.
        
        returns list
        """
        return [r["id"] for r in self.GetAllRootConfs()]


    def GetDefaultRootName(self):
        """
        Returns the name of the default root.
        
        returns string
        """
        return self._defaultRoot


    # Types -------------------------------------------------------------

    def GetObjectConf(self, typeID, skipRoot=False):
        """
        Get the type configuration for typeID. If type is not found root definitions are
        searched as well.
        
        returns configuration or none
        """
        c = self.registry.queryUtility(IObjectConf, name=typeID)
        if c or skipRoot:
            return c
        return self.GetRootConf(typeID)


    def GetAllObjectConfs(self, visibleOnly = False):
        """
        Get all type configurations.
        
        returns list
        """
        c = self.registry.getAllUtilitiesRegisteredFor(IObjectConf)
        if not visibleOnly:
            return c
        return filter(lambda t: t.get("hidden") != True, c)


    def GetTypeName(self, typeID):
        """
        Get the object type name for the id.
        
        returns string
        """
        t = self.GetObjectConf(typeID)
        if t:
            return t.name
        return ""


    # Tool -------------------------------------------------------------

    def GetToolConf(self, toolID, contextObject=None):
        """
        Get the tool configuration.
        
        returns configuration or None
        """
        if not contextObject:
            contextObject = _GlobalObject()
        v = self.registry.queryAdapter(contextObject, IToolConf, name=toolID)
        if v:
            return v[0]
        return None

    def GetAllToolConfs(self, contextObject=None):
        """
        Get all tool configurations.
        
        returns list
        """
        tools = []
        for a in self.registry.registeredAdapters():
            if a.provided==IToolConf:
                if contextObject:
                    if not a.required[0] in providedBy(contextObject):
                        continue
                tools.append(a.factory)
        return tools


    # General Fields -------------------------------------------------------------

    def GetFld(self, fldID, typeID = None):
        """
        Get type or meta field definition. Type fields have the priority if typeID is not None.

        returns configuration or None
        """
        if typeID:
            f = self.GetObjectFld(fldID, typeID)
            if f:
                return f
        return self.GetMetaFld(fldID)


    def GetFldName(self, fldID, typeID = None):
        """
        Get type or meta field name. Type fields have the priority if typeID is not None.
        
        returns string
        """
        if typeID:
            f = self.GetObjectFld(fldID, typeID)
            if f:
                return f["name"]
        return self.GetMetaFldName(fldID)


    # Type Data Fields -------------------------------------------------------------

    def GetObjectFld(self, fldID, typeID):
        """
        Returns object field configuration.
        
        returns configuration or None
        """
        fields = self.GetAllObjectFlds(typeID)
        if not fields:
            return None
        for f in fields:
            if f["id"] == fldID:
                return f
        return None


    def GetAllObjectFlds(self, typeID):
        """
        Get all object field configurations.
        
        returns list or None
        """
        t = self.GetObjectConf(typeID)
        if not t:
            return None
        return t.data


    # Meta Fields -------------------------------------------------------------

    def GetMetaFld(self, fldID):
        """
        Get meta field configuration
        
        returns configuration or None
        """
        for fld in self._meta:
            if fld["id"] == fldID:
                return fld
        return None


    def GetAllMetaFlds(self, ignoreSystem = True):
        """
        Get all meta field configurations.
        
        returns list
        """
        if not ignoreSystem:
            return self._meta
        return filter(lambda m: m["id"] in ReadonlySystemFlds, self._meta)


    def GetMetaFldName(self, fldID):
        """
        Get meta field name for id.
        
        returns string
        """
        for fld in self._meta:
            if fld["id"] == fldID:
                return fld["name"]
        return ""


    # Categories -------------------------------------------------------------------------------------------------------

    def GetCategory(self, categoryID=""):
        """
        Get category configuration.
        
        returns configuration or None
        """
        for c in self.configuration.categories:
            if c["id"] == categoryID:
                return c
        return None


    def GetAllCategories(self, sort=u"name", visibleOnly=False):
        """
        Get all category configurations.
        
        returns list
        """
        if not visibleOnly:
            return SortConfigurationList(self.configuration.categories, sort)
        c = filter(lambda a: not a.get("hidden"), self.configuration.categories)
        return SortConfigurationList(c, sort)


    def GetCategoryName(self, categoryID):
        """
        Get category name for id.
        
        returns string
        """
        for c in self.configuration.categories:
            if c["id"] == categoryID:
                return c["name"]
        return u""


    # Groups -------------------------------------------------------------

    def GetGroups(self, sort=u"name", visibleOnly=False):
        """
        Get a list of configured groups.
        
        returns list
        """
        if not self.configuration.groups:
            return []
        if not visibleOnly:
            return SortConfigurationList(self.configuration.groups, sort)
        c = filter(lambda a: not a.get("hidden"), self.configuration.groups)
        return SortConfigurationList(c, sort)


    def GetGroupName(self, groupID):
        """
        Get group name for id.
        
        returns string
        """
        for c in self.configuration.groups:
            if c["id"] == groupID:
                return c["name"]
        return u""


    # Workflow -------------------------------------------------------------

    def GetWorkflowConf(self, processID, contextObject=None):
        """
        Get the workflow process configuration.
        
        returns configuration or None
        """
        return self.registry.queryAdapter(contextObject or _GlobalObject(), IWfProcessConf, name=processID)


    def GetAllWorkflowConfs(self, contextObject=None):
        """
        Get all workflow configurations.
        
        returns list
        """
        w = []
        adpts = self.registry.registeredAdapters()
        for a in adpts:
            if a.provided==IWfProcessConf:
                if contextObject:
                    if not a.required[0] in providedBy(contextObject):
                        continue
                w.append(a.factory)
        return w


    # nive Configuration -------------------------------------------------------------

    def StoreSysValue(self, key, value):
        """
        Stores a value in `pool_sys` table. Value must be a string of any size.
        """
        db = self.db
        db.UpdateFields(u"pool_sys", key, {u"id": key, u"value":value, u"ts":time()}, autoinsert=True)
        db.Commit()

    def LoadSysValue(self, key):
        """
        Loads the value stored as `key` from `pool_sys` table. 
        """
        db = self.db
        sql, values = db.FmtSQLSelect([u"value", u"ts"], parameter={"id":key}, dataTable=u"pool_sys", singleTable=1)
        r = db.Query(sql, values)
        if not r:
            return None
        return r[0][0]


    def LoadStructure(self, forceReload = False):
        """
        returns dictionary containing database tables and columns
        """
        if forceReload:
            self._structure = PoolStructure()
        if not self._structure.IsEmpty():
            return self._structure

        structure = {}
        fieldtypes = {}
        meta = self.GetAllMetaFlds(ignoreSystem = False)
        m = []
        f = {}
        for fld in meta:
            f[fld.id] = fld.datatype
            if fld.datatype == "file":
                continue
            m.append(fld.id)
        structure[MetaTbl] = m
        fieldtypes[MetaTbl] = f

        types = self.GetAllObjectConfs()
        for ty in types:
            t = []
            f = {}
            for fld in self.GetAllObjectFlds(ty.id):
                f[fld.id] = fld.datatype
                if fld.datatype == "file":
                    continue
                t.append(fld.id)
            structure[ty.dbparam] = t
            fieldtypes[ty.dbparam] = f
        
        self._structure.Init(structure, fieldtypes, m, self.configuration.frontendCodepage)
        # reset cached db
        self.Close()
        return structure



class AppFactory:
    """
    Internal class for dynamic object creation and caching.

    Requires:
    - Workflow.Workflow
    """

    def _GetDataPoolObj(self):
        """
        creates the database object
        """
        poolTag = self.dbConfiguration.context
        if not poolTag:
            raise TypeError, "Database type not set. application.dbConfiguration.context is empty. Use Sqlite or Mysql!"
        elif poolTag.lower() in ("sqlite","sqlite3"):
            poolTag = "nive.utils.dataPool2.sqlite3Pool.Sqlite3"
        elif poolTag.lower() == "mysql":
            poolTag = "nive.utils.dataPool2.mySqlPool.MySql"

        # if a database connection other than the default is configured
        cTag = self.dbConfiguration.connection
        if cTag:
            connObj = GetClassRef(cTag, self.reloadExtensions, True, None)
            connObj = connObj(config=self.dbConfiguration)
        else:
            connObj = None

        dbObj = GetClassRef(poolTag, self.reloadExtensions, True, None)
        conn = self.dbConfiguration
        dbObj = dbObj(connection=connObj,
                      connParam=conn,      # use the default connection defined in db if connection is none
                      structure=self._structure, 
                      root=conn.fileRoot, 
                      useTrashcan=conn.useTrashcan, 
                      dbCodePage=conn.dbCodePage,
                      debug=conn.querylog[0],
                      log=conn.querylog[1])
        return dbObj

    
    def _GetConnectionObj(self):
        """
        creates a new database connection object
        """
        cTag = self.dbConfiguration.connection
        poolTag = self.dbConfiguration.context
        if cTag:
            connObj = GetClassRef(cTag, self.reloadExtensions, True, None)
            connObj = connObj(config=self.dbConfiguration)
            return connObj
        if self._dbpool:
            return self._dbpool.CreateConnection(self.dbConfiguration)
        if not cTag and not poolTag:
            raise TypeError, "Database connection type not set. application.dbConfiguration.connection and application.dbConfiguration.context is empty. Use Sqlite or Mysql!"
        poolTag = self.dbConfiguration.context
        if not poolTag:
            raise TypeError, "Database type not set. application.dbConfiguration.context is empty. Use Sqlite or Mysql!"
        elif poolTag.lower() in ("sqlite","sqlite3"):
            poolTag = "nive.utils.dataPool2.sqlite3Pool.Sqlite3"
        elif poolTag.lower() == "mysql":
            poolTag = "nive.utils.dataPool2.mySqlPool.MySql"
        dbObj = GetClassRef(poolTag, self.reloadExtensions, True, None)
        return dbObj.defaultConnection(self.dbConfiguration)


    def _GetRootObj(self, rootConf):
        """
        creates the root object
        """
        if isinstance(rootConf, basestring):
            rootConf = self.GetRootConf(rootConf)
        if not rootConf:
            return None

        name = rootConf.id
        useCache = self.configuration.useCache
        cachename = "_c_root"+name
        if useCache and hasattr(self, cachename) and getattr(self, cachename):
            rootObj = getattr(self, cachename)
        else:
            rootObj = ClassFactory(rootConf, self.reloadExtensions, True, base=None)
            rootObj = rootObj(name, self, rootConf)
            if rootObj and useCache:
                setattr(self, cachename, rootObj)
        return rootObj


    def _CloseRootObj(self, name=None):
        """
        close root objects. if name = none, all are closed.
        """
        if not name:
            n = self.GetRootIds()
        else:
            n = (name,)
        for name in n:
            cachename = "_c_root"+name
            try:
                o = getattr(self, cachename)
                o.Close()
                setattr(self, cachename, None)
            except:
                pass


    def _GetToolObj(self, name, contextObject):
        """
        creates the tool object
        """
        if isinstance(name, basestring):
            conf = self.GetToolConf(name, contextObject)
            if isinstance(conf, (list, tuple)):
                conf = conf[0]
        else:
            conf = name
        if not conf:
            iface, conf = ResolveConfiguration(name)
            if not conf:
                raise ImportError, "Tool not found. Please load the tool by referencing the tool configuration. (%s)" % (str(name))
        tag = conf.context
        toolObj = GetClassRef(tag, self.reloadExtensions, True, None)
        toolObj = toolObj(conf, self)
        if not _IGlobal.providedBy(contextObject):
            toolObj.__parent__ = contextObject
        return toolObj


    def _GetWfObj(self, wfConf, contextObject):
        """
        creates the root object
        """
        if isinstance(wfConf, basestring):
            wfConf = self.GetWorkflowConf(wfConf, contextObject)
            if isinstance(wfConf, (list, tuple)):
                wfConf = wfConf[0]
        if not wfConf:
            return None

        name = wfConf["id"]
        useCache = self.configuration.useCache
        cachename = "_c_wf"+name
        if useCache and hasattr(self, cachename) and getattr(self, cachename):
            wfObj = getattr(self, cachename)
        else:
            wfTag = wfConf["context"]
            wfObj = GetClassRef(wfTag, self.reloadExtensions, True, None)
            wfObj = wfObj(wfConf, self)
            if wfObj and useCache:
                setattr(self, cachename, wfObj)
        return wfObj


    def _CloseWfObj(self, name=None):
        """
        close wf object. if name = none, all are closed.
        """
        if not name:
            n = self.GetWorkflowIds()
        else:
            n = (name,)
        for name in n:
            cachename = "_c_wf"+name
            try:
                o = getattr(self, cachename)
                o.Close()
                setattr(self, cachename, None)
            except:
                pass

