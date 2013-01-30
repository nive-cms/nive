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

__doc__ = """
Using configuration classes
-----------------------------
The predefined configuration classes are meant to handle the different cms 
modules and parts. Empty configurations are already filled with default values for convenience.
Also configuration classes provide functions for easy copying and changing. 

You have to use one of these to extend or change anything in the application.

Each configuration class can be used with python dictionary or attribute notation to set
or get values.    
    
Values can be defined in python files as ::

    baseConf(id='test',name='test')

or ::

    c = baseConf()
    c.id = 'test'
    c.name = 'test'

or dictionary syntax: ::

    baseConf(**{'id':'test','name':'test'})
    c["id"]
    c.get("id")
    c.update(values)
    c.keys()
    c.copy()

Alternatively configurations can be defined outside python code as json files. The specific
configuration class is mapped from the type value ::

    {
        "type":    "ObjectConf",
        "copyFrom":"nive.cms.app",
        "id":      "my_object",
        "name":    "My Object",
        "dbparam": "my_object",
        "context": "website.my_object",
        ...
    }

Json files are distinguished by their file extension ".json" from python dotted path names. You
can manually load json files by calling nive.helper.LoadConfiguration(filename). ::

    nive.helper.LoadConfiguration("my_object.json")

To copy and customize existing configurations call the constructor with the 
configuration to be copied as first non-keyword parameter: ::

    a = baseConf(id='test',name='test')
    b = baseConf(a, id='test2')

or ::

    cms = AppConf("nive.cms.app", id="my_website", ...)

Json: add "copyFrom" ::

    {
        "type":    "AppConf",
        "copyFrom":"nive.cms.app",
        "id":      "my_website",
        ...
    }    

Data field types
----------------
These types define both: the data storage type (like string or number), widget
and internal handling. Use these for FieldConf.datatypes.

===========  ==============================================
id           Name
===========  ==============================================
string       String 
number       Number 
float        Float 
bool         Bool 
htext        HTML Text 
text         Text 
unit         ID Reference 
unitlist     ID Reference List 
date         Date 
datetime     Datetime 
list         List 
radio        Radio Selection 
mselection   Multiple Selection 
mcheckboxes  Multiple Checkboxes 
xml          XML 
code         HTML / Javascript / CSS 
json         Json 
file         File 
timestamp    Timestamp 
lines        Lines /Log 
bytesize     Filesize 
url          URL 
urllist      URL List 
email        E-Mail 
password     Password 
percent      Percent 
===========  ==============================================


Configurations
---------------
"""

import copy
from types import ListType,TupleType,DictType

from zope.interface import Interface, Attribute, implements, Provides, alsoProvides, directlyProvidedBy, directlyProvides

from pyramid.path import DottedNameResolver
from pyramid.renderers import render

from nive.i18n import _


# interfaces ----------------------------------------------------------------------
# objects, root and application
class IApplication(Interface):
    pass
class IRoot(Interface):
    pass
class IObject(Interface):
    pass
class IContainer(Interface):
    pass
class INonContainer(Interface):
    pass
class IReadonly(Interface):
    pass
class IPortal(Interface):
    pass

# pages and elements
class IWebsite(Interface):
    pass
class IPage(Interface):
    pass
class IPageContainer(Interface):
    pass
class IPageElement(Interface):
    pass
class IPageElementContainer(Interface):
    pass
class IFolder(Interface):
    pass
class IColumn(Interface):
    pass
class IFile(Interface):
    pass
class ITool(Interface):
    pass
class IIFaceRoot(Interface):
    pass
class ICMSRoot(Interface):
    pass
class IWebsiteRoot(Interface):
    pass
class ICache(Interface):
    pass
class IPersistent(Interface):
    pass
class IUser(Interface):
    pass
        
# configuration 
class IConf(Interface):
    pass
class IAppConf(Interface):
    pass
class IDatabaseConf(Interface):
    pass
class IRootConf(Interface):
    pass
class IObjectConf(Interface):
    pass
class IToolConf(Interface):
    pass
class IViewModuleConf(Interface):
    pass
class IViewConf(Interface):
    pass
class IModuleConf(Interface):
    pass
class IWidgetConf(Interface):
    pass
class IPortalConf(Interface):
    pass

class IFieldConf(Interface):
    pass
class IGroupConf(Interface):
    pass
class IAclConf(Interface):
    pass
class ICategoryConf(Interface):
    pass
class IWorkflowConf(Interface):
    pass

class IFormWorker(Interface):
    pass
    
# workflow
class IWfProcessConf(Interface):
    pass
class IWfStateConf(Interface):
    pass
class IWfTransitionConf(Interface):
    pass
class IProcess(Interface):
    pass


# userdb
class IUserDatabase(Interface):
    pass
class ILocalGroups(Interface):
    pass

# interface extensions
class IToolboxWidgetConf(Interface):
    """
    IToolboxWidgetConf refers to the nive.cmsview toolbox plugin point. Use IToolboxWidgetConf as widgetType
    in your WidgetConf() to link a widget to the nive toolbox.
    """

class IEditorWidgetConf(Interface):
    """
    IEditorWidgetConf refers to the nive.cmsview editor tab plugin point. Use IEditorWidgetConf as widgetType
    in your WidgetConf() to link a new tab to the nive editor header.
    """

class IAdminWidgetConf(Interface):
    """
    IAdminWidgetConf refers to the nive.adminview tab plugin point. Use IAdminWidgetConf as widgetType
    in your WidgetConf() to link a new tab to the nive admin header.
    """



class baseConf(object):
    locked=0
    
    def copy(self, **newvalues):
        data = copy.deepcopy(self.__dict__)
        data.update(newvalues)
        data["locked"] = 0
        return self.__class__(**data)
    
    def test(self):
        return True
    
    #Provides(IConf)
    def __init__(self, copyFrom=None, **values):
        self._empty = True
        self._parent = None
        #alsoProvides(self, IConf)
        if copyFrom:
            self._empty=False
            import helper
            i,c = helper.ResolveConfiguration(copyFrom)
            if c:
                data = copy.deepcopy(c.__dict__)
                self.update(data)
                self._parent = c
        if values:
            self._empty=False
            self.update(values)
            
    def __len__(self):
        return not self._empty
    
    def keys(self):
        k = self.__dict__.keys()
        k.remove("_empty")
        k.remove("_parent")
        try:
            k.remove("locked")
        except:
            pass
        return k
    
    def has_key(self, key):
        if hasattr(self, key):
            return True
        return False
    
    def update(self, values):
        self._empty=False
        #opt
        for k in values.keys():
            setattr(self, k, values[k])
            
    @property
    def parent(self):
        return self._parent
            
    def get(self, key, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        return default

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        raise AttributeError, key

    def __setattr__(self, key, value):
        if self.locked:
            raise ConfigurationError, "Configuration locked."
        self.__dict__["_empty"]=False
        self.__dict__[key]=value

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        if self.locked:
            raise ConfigurationError, "Configuration locked."
        self._empty=False
        setattr(self, key, value)
        
    def __iter__(self):
        return iter(self.keys())

    def __deepcopy__(self, memo):
        data = copy.deepcopy(self.__dict__)
        if "locked" in data:
            del data["locked"]
        if "_empty" in data:
            del data["_empty"]
        return self.__class__(**data)
    
    def __str__(self):
        if hasattr(self, "id"):
            return str(self.id)
        elif hasattr(self, "name"):
            return str(self.name)
        return ""

    def __repr__(self):
        return "<%s at 0x%x (%s)>" % (self.__class__.__name__, abs(id(self)), str(self))

    def uid(self):
        # create a unique identifier for the configuration to support persistence
        return "nive."+self.__class__.__name__+"."+self.id
    
    def lock(self):
        self.__dict__["locked"] = 1

    def unlock(self):
        self.__dict__["locked"] = 0
    

class FieldConf(baseConf):
    """
    Definition of a field used for object.data, object.meta, form.field and tool.data

    Values ::

        *id :       Unique field id as ascii string with maximum 25 chars. Used as column name
                    in database tables.
        *datatype : Datatype of the field based on nive.definitions.DataTypes.
        size :      Field size of stored data. Depends on datatype. 
        default :   Default value.
        listItems : Used for list and checkbox types. Contains items with id and name 
                    definitions [{"id": "id1", "name": "name1"},...].
                    If listItems is a callable the callback must take two arguments:
                    callback(fieldconf, object) and return a list with id and name items.
        settings :  Extended settings for fields. Possible values depend on datatype.
        fulltext :  Use this field in fulltext index.
        
    Extended values (optional and used as default for forms) ::

        name :        Display name. 
        description : Description.
        required :    Form input is required.
        readonly :    This field is not included in forms.
        hidden :      This field is rendered as hidden field in forms.
        len :         Depends on datatype. 
        node :        Form field object for rendering and validation (colander schema node).
    
    Call ``FieldConf().test()`` to verify configuration values.

    Interface: IFieldConf
    """
    implements(IFieldConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.datatype = ""
        self.size = 0
        self.default = u""
        self.listItems = None
        self.settings = {}
        self.fulltext = False
        # used as default for forms
        self.name = u""
        self.description = u""
        self.required = False
        self.readonly = False
        self.hidden = False
        self.len = 50
        self.node = None
        baseConf.__init__(self, copyFrom, **values)

    def __str__(self):
        return "%(id)s (%(name)s): %(datatype)s" % self

    def test(self):
        report = []
        # check id
        if len(self.id) > 25:
            report.append((ConfigurationError, " FieldConf.id too long. 25 chars allowed.", self))
        # check datatype
        ok=0
        for d in DataTypes:
            if d["id"] == self.datatype:
                ok=1
                break
        if not ok:
            report.append((ConfigurationError, " FieldConf.datatype unknown.", self))
        return report


class AppConf(baseConf):
    """
    Application configuration class. Contains all configurable options for the cms 
    (nive.Application).
    
    Values ::

        *id :          Ascii used as name in url traversal.
        *context :     Dotted python name or class reference used as factory.
        title :        Application title (optional).
        description :  Application description (optional).
            
        # extensions
        meta :    Additional meta layer fields or replacements for system fields.
        modules : List of included configurations. Calls nive.Registration.Include for 
                  each module on startup. 
                  Refer to helper.ResolveConfiguration for possible values. 
        categories : list of CategoryConf definitions.
    
        # security
        groups : List of Definitions.GroupConf with groups used in this application.
        acl :    List of pyramid acls for permission settings.
            
        # options
        fulltextIndex :    Enable fulltext index based on FieldConf.fulltext setting.
        autocommit :       Enable autocommit for object write and delete operations.
        useCache :         Cache database on application level.
        frontendCodepage : Default=utf-8. The codepage used to render the html frontend.
        workflowEnabled :  Enable or disable the workflow engine.
        
    Call ``AppConf().test()`` to verify configuration values.
    
    Interface: IAppConf
    """
    implements(IAppConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = "app"
        self.context = "nive.components.objects.base.ApplicationBase"
        
        self.title = u""
        self.description = u""
        
        # data pool
        self.autocommit = True
        self.useCache = True
        self.frontendCodepage = "utf-8"
        self.fulltextIndex = False
        self.workflowEnabled = False
        
        # security
        self.groups = []
        self.acl = []
        
        # extensions
        self.meta = []
        self.modules = []
        self.categories = []
        
        # development
        self.reloadExtensions = False
        baseConf.__init__(self, copyFrom, **values)

        # bw 0.9.3 
        # database connection parameter
        if hasattr(self, "dbConfiguration") and isinstance(self.dbConfiguration, basestring):
            import helper
            self.dbConfiguration = helper.LoadConfiguration(self.dbConfiguration)
        
 
    def __str__(self):
        return "%(id)s (%(title)s) implemented by %(context)s" % self

    def uid(self):
        # create a unique identifier for the configuration to support persistence
        return "nive."+self.__class__.__name__

    
    def test(self):
        report = []
        #check id
        if not self.id:
            report.append((ConfigurationError, " AppConf.id is empty", self))
        # check context
        o = TryResolveName(self.context)
        if not o:
            report.append((ImportError, " for AppConf.context", self))
        # check modules
        for m in self.modules:
            if isinstance(m, basestring):
                o = TryResolveName(m)
                if not o:
                    report.append((ImportError, " AppConf.modules error: "+m, self, m))
            if hasattr(m, "test"):
                report += m.test()
        # check meta
        if not type(self.meta) in (ListType,TupleType):
            report.append((TypeError, " AppConf.meta error: Not a list", self))
        else:
            for m in self.meta:
                if hasattr(m, "test"):
                    report += m.test()
        return report
        

class DatabaseConf(baseConf):
    """
    Database configuration ::

        *context : Database type to be used. supports "Sqlite3" and "MySql" by default. 
                   MySql requires python-mysqldb installed.
        *dbName  : sqlite3=database file path, mysql=database name 
        fileRoot : Relative or absolute root directory for files.
        host     : mysql database server host.
        port     : mysql database server port.
        user     : mysql database server user.
        password : mysql database server password.
        useTrashcan : Move files to fileRoot.__traschcan directory on delete.
        unicode  : Database is using unicode mode.
        dbCodePage : If not in unicode mode, the database codepage used (default "utf-8").
        connection : Specifies the database connection management class. Default None.
        verifyConnection : Verify connection is still alive each time a connection is requested.
                           Automatically reconnects if the connection is closed.
        timeout  : Timeout in seconds for database requests, if supported.
        querylog : Enable database query log. "querylog" is used as filename the application 
                   will use for the query log and the number of traceback lines. 
                   use e.g. (10,'sql.log')
    
    Interface: IDatabaseConf
    
    Call ``DatabaseConf().test()`` to verify configuration values.
    """
    implements(IDatabaseConf)
    
    def __init__(self, copyFrom=None, **values):
        self.context = "Sqlite3"
        self.fileRoot = ""
        self.dbName = ""
        self.host = ""
        self.port = ""
        self.user = ""
        self.password = ""
        self.useTrashcan = False
        self.unicode = True
        self.timeout = 3
        self.verifyConnection = False
        self.connection = None
        self.dbCodePage = "utf-8"
        self.querylog=(0,None)
        baseConf.__init__(self, copyFrom, **values)
        
        
    def __str__(self):
        return "%(context)s %(dbName)s / %(fileRoot)s" % self

    def uid(self):
        # create a unique identifier for the configuration to support persistence
        return "nive."+self.__class__.__name__

    def test(self):
        report = []
        # check context
        c = self.context
        if c in ("Sqlite3", "Mysql", "MySql"):
            return report
        o = TryResolveName(c)
        if not o:
            report.append((ImportError, " for DatabaseConf.context", self))
        if not self.dbName:
            report.append((ConfigurationError, " DatabaseConf.dbName is empty", self))
        return report



class ObjectConf(baseConf):
    """
    Configuration of a object type definition

    Values ::

        *id :      Unique type id as ascii string with maximum 25 chars.
        *name :    Name used for display.
        *dbparam : Database table name.
        *context : Dotted python name or class reference used as factory. 
        extensions:List of dotted python names or class references to extend context with
                   additional functionality. Used in object factory.
        data :     List of nive.definitions.FieldConf classes. Are mapped to the data table
                   except for "file" data types. 
        template : Template file name to render the default view. If file name is a
                   relative path ('text.pt') the template is looked up in the active 
                   design or view module templatePath. The file name can also be a 
                   absolute dotted python name ('nive.cms.templates:text.pt').
        views :    List of object view definitions. Either nive.definitions.ViewConf or 
                   nive.definitions.ViewModuleConf.
        forms :    Configuration of object form subsets and actions. Refer to nive.Form.
    
        subtypes  : Define possible subtypes. None=no objects allowed, "*"=all objects allowed, 
                    [IContainer,IPageElement]=list with interfaces of allowed objects.
        selectTag : Default select tag for this type. Stored as meta.pool_stag.
        category  : Default category stored as meta.pool_category.
        hidden    : Hide in select lists in user interface.
        description      : Description.
        workflowDisabled : Enable or disable workflow for this type.
        workflowID       : Workflow process id.
        version   : Optional version string.

    Call ``ObjectConf().test()`` to verify configuration values.
    
    Object instances provide the configuration as `configuration` attribute.
    
    Interface: IObjectConf
    """
    implements(IObjectConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.dbparam = u""
        self.selectTag = 0
        self.context = "nive.components.objects.base.ObjectBase"
        self.template = None
        self.extensions = None
        self.data = []
        self.forms = {}
        self.views = []
        self.workflowDisabled = True
        self.workflowID = ""
        self.subtypes = "*"
        self.category = u""
        self.hidden = False
        self.description = u""
        self.version = "1"
        baseConf.__init__(self, copyFrom, **values)
        import helper
        d=[]
        for field in self.data:
            if isinstance(field, dict):
                field = helper.LoadConfiguration(field)
            d.append(field)
        self.data=d


    def __str__(self):
        return "%(id)s (%(name)s) implemented by %(context)s" % self

    def test(self):
        report = []
        # check id
        if not self.id:
            report.append((ConfigurationError, " ObjectConf.id is empty", self))
        # check context
        o = TryResolveName(self.context)
        if not o:
            report.append((ImportError, " for ObjectConf.context", self))
        # check extensions
        if self.extensions:
            for e in self.extensions:
                o = TryResolveName(e)
                if not o:
                    report.append((ImportError, " for ObjectConf.extensions", e))
        # check views
        if not type(self.views) in (ListType,TupleType):
            report.append((TypeError, " ObjectConf.views error: Not a list", self))
        else:
            for m in self.views:
                if hasattr(m, "test"):
                    report += m.test()
        # check data
        if not type(self.data) in (ListType,TupleType):
            report.append((TypeError, " ObjectConf.data error: Not a list", self))
        else:
            for m in self.data:
                if hasattr(m, "test"):
                    report += m.test()
        # check forms
        if self.forms:
            for subset in self.forms:
                s = self.forms[subset]
                if not isinstance(s, dict):
                    report.append((TypeError, " ObjectConf.forms."+subset+" error: Not a dictionary", self))
                elif "fields" in s:
                    if not type(s["fields"]) in (ListType,TupleType):
                        report.append((TypeError, " ObjectConf.forms."+subset+".fields error: Not a list", self))
                elif "actions" in s:
                    if not type(s["actions"]) in (ListType,TupleType):
                        report.append((TypeError, " ObjectConf.forms."+subset+".actions error: Not a list", self))
                    
        return report



class RootConf(baseConf):
    """
    Configuration of a root object

    Values ::

        *id      : Unique type id as ascii string.
        *name    : Display name.
        *context : Dotted python name or class reference used as factory. 
        extensions:List of dotted python names or class references to extend context with
                   additional functionality. Used in object factory.
        template : Template file name to render the default view. If file name is a
                   relative path ('root.pt') the template is looked up in the active 
                   design or view module templatePath. The file name can also be a 
                   absolute dotted python name ('nive.cms.templates:root.pt').
        views    : List of object view definitions. Either nive.definitions.ViewConf 
                   or nive.definitions.ViewModuleConf.
        default  : Use this root as default root
        subtypes : Define possible subtypes. None=no objects allowed, *=all objects allowed, 
                   [IContainer,IPageElement]=list with interfaces of allowed objects.
        urlTraversal : if True the root name is allowed to be used in url traversal.
        workflowDisabled : Enable or disable workflow for this type.
        workflowID       : Workflow process id.
        description : Description.

    Call RootConf().test() to verify configuration values.
    
    Interface: IRootConf
    """
    implements(IRootConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.context = "nive.components.objects.base.RootBase"
        self.extensions = None
        self.template = None
        self.default = True
        self.views = []
        self.subtypes = "*"
        self.workflowDisabled = True
        self.urlTraversal = True
        self.workflowID = ""
        self.description = u""
        baseConf.__init__(self, copyFrom, **values)


    def __str__(self):
        return "%(name)s (%(id)s) implemented by %(context)s" % self

    def test(self):
        report = []
        # check id
        if not self.id:
            report.append((ConfigurationError, " RootConf.id is empty", self))
        # check context
        o = TryResolveName(self.context)
        if not o:
            report.append((ImportError, " for RootConf.context", self))
        # check extensions
        if self.extensions:
            for e in self.extensions:
                o = TryResolveName(e)
                if not o:
                    report.append((ImportError, " for ObjectConf.extensions", e))
        # check views
        if not type(self.views) in (ListType,TupleType):
            report.append((TypeError, " RootConf.views error: Not a list", self))
        else:
            for m in self.views:
                if hasattr(m, "test"):
                    report += m.test()
        return report        


class ViewModuleConf(baseConf):
    """
    View module configuration
    
    Used to group views and define module based default values for included views.
    View modules are registered and loaded on application level.
    
    Values ::

        *id    : Unique view module id as ascii string. Used to register and 
                 lookup the view module.
        name   : Display name 
        mainTemplate : The main template containing the slots to insert content.
        static : Static directory
        staticName : By default ViewModule.id is used as url name to map the static
                     directory. To change the default specify a different name here.  
        acl    : Pyramid security definitions added to nive.Application acls
        description : optional description
    
    Included views ::

        views : a list of nive.definitions.ViewConf definitions. These views use the
                following default values.
        widgets : WidgetConf list for IToolboxWidgetConf and insertion points.

    View defaults, can be overridden by single views ::

        context      : default value for ViewModuleConf.views. 
        view         : default value for ViewModuleConf.views. 
        containment  : default value for ViewModuleConf.views. 
        permission   : default value for ViewModuleConf.views. 
        templates    : default value for ViewModuleConf.views, if renderers are used.
                       This refers to the directory templates with relative path are
                       looked up.

    Call ``ViewModuleConf().test()`` to verify configuration values.
        
    Interface: IViewModuleConf
    """
    implements(IViewModuleConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.static = ""
        self.staticName = None
        self.mainTemplate = None
        self.widgets = None
        self.acl = None
        self.description = u""
        
        # views and defaults
        self.context = None
        self.view = None
        self.containment = None    
        self.permission = None
        self.custom_predicates = None
        self.templates = ""
        self.views = []
        baseConf.__init__(self, copyFrom, **values)


    def __str__(self):
        return "%(id)s %(name)s" % self

    def test(self):
        report = []
        # check id
        if not self.id:
            report.append((ConfigurationError, " ViewModuleConf.id is empty", self))
        # check containment
        if self.containment:
            o = TryResolveName(self.containment)
            if not o:
                report.append((ImportError, " for ViewModuleConf.containment", self))
        # check view
        if self.view:
            o = TryResolveName(self.view)
            if not o:
                report.append((ImportError, " for ViewModuleConf.view", self))
        # check widgets
        if self.widgets:
            for w in self.widgets:
                report += w.test()
        # check defultTemplatePath
        #if self.defultTemplatePath:
        #    o = ResolveName(self.defultTemplatePath)
        #    if not o:
        #        report.append((ImportError, " ViewModuleConf.defultTemplatePath error", self))
        # check views
        if not type(self.views) in (ListType,TupleType):
            report.append((TypeError, " ViewModuleConf.views error: Not a list", self))
        else:
            for m in self.views:
                if hasattr(m, "test"):
                    report += m.test(viewModule=self)
        return report
        
        

class ViewConf(baseConf):
    """
    Configuration for a view definition
    
    Parameters refer mainly to pyramid.add_view. If the view is included in a ``ViewModuleConf``, defaults are 
    loaded from the module (see ``ViewModuleConf`` above). 

    Values ::

        *view       : the view class or function to be used 
        *name       : the url name used to call this view. May be empty as default view 
                      for object.
        attr        : if the view is mapped to a class, this is the function to be called
        context     : the object or interface this view is invoked for
        renderer    : renderer name or template path
        containment : load the view for this root context 
        permission  : permission required to access the view
        options     : additional view options supported by pyramid.add_view() as dict
        id          : (optional) unique view id as ascii string. Can be used to remove, 
                      change or replace a single view before the view is registered.
        description : (optional) description

    All parameters except *id* and *description* are passed to `pyramid.add_view() <http://docs.pylonsproject.org/projects/pyramid/en/latest/api/config.html#pyramid.config.Configurator.add_view>`_

    Call ``ViewConf().test()`` to verify configuration values.
    
    Interface: IViewConf
    """
    implements(IViewConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.attr = None
        self.name = None
        self.context = None
        self.view = None
        self.renderer = None
        self.containment = None
        self.permission = None
        self.options = {}
        self.custom_predicates = None
        self.settings = {}
        self.description = u""
        baseConf.__init__(self, copyFrom, **values)


    def __str__(self):
        return "<%(name)s> %(id)s" % self

    def test(self, viewModule=None):
        if not viewModule:
            viewModule = ViewModuleConf()
        report = []
        # check context
        c = self.context or viewModule.context
        if c:
            o = TryResolveName(c)
            if not o:
                report.append((ImportError, " for ViewConf.context", self))
        # check view
        v = TryResolveName(self.view or viewModule.view)
        if not v:
            report.append((ImportError, " for ViewConf.view", self))
        # check renderer
        if self.renderer:
            import helper
            r = helper.ResolveAsset(self.renderer)
            try:
                r = helper.ResolveAsset(self.renderer)
            except:
                r = None
            if not r:
                report.append((ImportError, " for ViewConf.renderer template", self))
        # check attr
        #if self.attr:
        #    if not hasattr(v, self.attr):
        #        report.append((ImportError, " ViewConf.attr error", self, v))
        # check containment
        if self.containment:
            #!!! test containment for interface or class (not module)
            c = TryResolveName(self.containment)
            if not c:
                report.append((ImportError, " for ViewConf.containment", self))
        return report



class PortalConf(baseConf):
    """
    Portal configuration class. Contains all configurable options for the portal 
    (nive.Portal).
    
    Values ::

        portalDefaultUrl : redirect for portal root (/) requests
        loginUrl         : login form url 
        loginSuccessUrl  : redirect after succesfull login url 
        forbiddenUrl     : redirect for unauthorized requests
        logoutUrl        : logout function
        logoutSuccessUrl : redirect on succesfull logout
        accountUrl       : user account page
        favicon          : favicon asset path
        robots           : robots.txt contents
        
    Call ``PortalConf().test()`` to verify configuration values.
    
    Interface: IPortalConf
    """
    implements(IPortalConf)
    
    def __init__(self, copyFrom=None, **values):
        self.portalDefaultUrl = "/website/"
        self.loginUrl = "/userdb/udb/login"
        self.loginSuccessUrl = "/website/editor/"
        self.forbiddenUrl = "/userdb/udb/login"
        self.logoutUrl = "/userdb/udb/logout"
        self.logoutSuccessUrl = "/userdb/udb/login"
        self.accountUrl = "/userdb/udb/update"
        self.favicon = ""
        self.robots = u"""
User-agent: *
Disallow: /login
Disallow: /logout
Disallow: /update
        """
        baseConf.__init__(self, copyFrom, **values)

 
    def uid(self):
        # create a unique identifier for the configuration to support persistence
        return "nive."+self.__class__.__name__
    
    def test(self):
        report = []
        #check id
        return report
        


class ToolConf(baseConf):
    """
    Tool configuration 
    
    Values ::
    
        *id      : Unique tool id as ascii string. Used to register and lookup the tool.
        *context : Dotted python name or class reference used as factory. 
        *apply   : List of interfaces the tool is registered for. 
        data     : Tool data defined as nive.definitions.FieldConf list.
        values   : Values to override data.default on execution.
        views    : List of nive.definitions.ViewConf definitions. 
        mimetype : Mimetype of tool return stream
        hidden   : Hide in user interface.
        name     : Display name
        description : Description
    
    Call ToolConf().test() to verify configuration values.
    
    Interface: IToolConf
    """
    implements(IToolConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.context = ""
        self.apply = None
        self.data = []
        self.values = {}
        self.views = []
        self.mimetype = ""
        self.hidden = False
        self.description = u""
        baseConf.__init__(self, copyFrom, **values)

    def __call__(self, context):
        # for adapter registration
        return self, context

    
    def __str__(self):
        return "%(id)s (%(name)s) implemented by %(context)s" % self

    def test(self):
        report = []
        # check id
        if not self.id:
            report.append((ConfigurationError, " ToolConf.id is empty", self))
        # check context
        o = TryResolveName(self.context)
        if not o:
            report.append((ImportError, " for ToolConf.context", self))
        # check data
        if not type(self.data) in (ListType,TupleType):
            report.append((TypeError, " ToolConf.data error: Not a list", self))
        else:
            for m in self.data:
                if hasattr(m, "test"):
                    report += m.test()
        # check views
        if not type(self.views) in (ListType,TupleType):
            report.append((TypeError, " ToolConf.views error: Not a list", self))
        else:
            for m in self.views:
                if hasattr(m, "test"):
                    report += m.test()
        #check apply
        return report
        


class ModuleConf(baseConf):
    """
    Generic module definition for application extension

    Values ::

        *id     : Unique type id as ascii string.
        context : Dotted python name or class reference used as factory.
        name    : Display name.
        views   : List containing ViewConf or ViewModuleConf definitions. 
        events  : Register for one or multiple Application events. 
                  Register each event as e.g. Conf(event="run", callback=function).
        modules : Additional module configuration to be included.
        description : Description.

    Call ``ModuleConf().test()`` to verify configuration values.
    
    Interface: IModuleConf
    """
    implements(IModuleConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.context = ""
        self.views = []
        self.events = None
        self.modules = []
        self.description = u""
        baseConf.__init__(self, copyFrom, **values)

    def __call__(self, context):
        return self

    
    def __str__(self):
        return "%(id)s (%(name)s)" % self

    def test(self):
        report = []
        # check id
        if not self.id:
            report.append((ConfigurationError, " ModuleConf.id is empty", self))
        # check context
        if self.context:
            o = TryResolveName(self.context)
            if not o:
                report.append((ImportError, " for ModuleConf.context", self))
        # check views
        if not type(self.views) in (ListType,TupleType):
            report.append((TypeError, " ModuleConf.views error: Not a list", self))
        else:
            for m in self.views:
                if hasattr(m, "test"):
                    report += m.test()
        # check modules
        for m in self.modules:
            if isinstance(m, basestring):
                o = TryResolveName(m)
                if not o:
                    report.append((ImportError, " AppConf.modules error: "+m, self, m))
            if hasattr(m, "test"):
                report += m.test()
        return report                
        

class WidgetConf(baseConf):
    """
    Configuration for a widget link
    
    Use this configuration to link existing views to plugin points
    in user interfaces. 
    Currently used for `nive.cms.cmsview` ToolboxWidget and EditorWidget

    Values ::    

        *apply      : List of interfaces of context objects this widget is used for.
        *viewmapper : View name in context to render widget contents.
        *widgetType : Plugin point to register this widget for (IToolboxWidgetConf or IEditorWidgetConf).
        *id         : Unique ascii string id to register this widget.
        name        : Widget name.
        sort        : Default sort for widgets as number.
        description : Description.

    Call ``WidgetConf().test()`` to verify configuration values.
    
    Interface: IWidgetConf
    """
    implements(IWidgetConf)
    
    def __init__(self, copyFrom=None, **values):
        self.apply = None
        self.viewmapper = None
        self.widgetType = None
        self.name = None
        self.id = None
        self.sort = 100
        self.description = u""
        baseConf.__init__(self, copyFrom, **values)

    def __call__(self, context):
        return self

    def __str__(self):
        return "%(id)s %(viewmapper)s %(widgetType)s" % self

    def test(self):
        report = []
        # check id
        if not self.id:
            report.append((ConfigurationError, " WidgetConf.id is empty", self))
        # check widgetType
        o = TryResolveName(self.widgetType)
        if not o:
            report.append((ImportError, " for WidgetConf.widgetType", self))
        #check view mapper
        if not self.viewmapper:
            report.append((ConfigurationError, " WidgetConf.viewmapper not defined", self))
        # check apply
        if not self.apply:
            report.append((ConfigurationError, " WidgetConf.apply not defined", self))
        else:
            for a in self.apply:
                o = TryResolveName(a)
                if not o:
                    report.append((ImportError, " for WidgetConf.apply", self))
        return report


class GroupConf(baseConf):
    """
    Configuration of a group or principal definition 

    Values ::

        id : Unique type id as ascii string with maximum 25 chars.
        name : Display name. 
        hidden : Hide in select lists in user interface.
        description : Description.

    Interface: IGroupConf
    """
    implements(IGroupConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.hidden = False
        self.description = u""
        baseConf.__init__(self, copyFrom, **values)


class AclConf(baseConf):
    """
    Configuration of a acl definition 

    Values ::

        access : Access definition. Allow or Deny.
        principal : User/Group to map this acl to. Group or 'Everyone'. 
        permission : Permission name of this acl. custom string or 'ALL_PERMISSIONS'

    Interface: IGroupConf
    """
    implements(IAclConf)
    
    def __init__(self, copyFrom=None, **values):
        self.access = Allow
        self.principal = u""
        self.permission = u""
        baseConf.__init__(self, copyFrom, **values)


class CategoryConf(baseConf):
    """
    Configuration of a category

    id : Unique type id as ascii string with maximum 25 chars.
    name : Display name. 
    hidden : Hide in select lists in user interface.
    description : Description.
    """
    implements(ICategoryConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.hidden = False
        self.description = u""
        baseConf.__init__(self, copyFrom, **values)


class Conf(baseConf):
    """
    Configuration class with no predefined fields
    
    Interface: IConf
    """
    implements(IConf)
    
        


class ConfigurationError(Exception):
    pass
class ContainmentError(Exception):
    pass
class OperationalError(Exception):
    pass
class ProgrammingError(Exception):
    pass
class Warning(Exception):
    pass




def TryResolveName(name, base=None):
    if not name:
        return None
    if not isinstance(name, basestring):
        return name
    d = DottedNameResolver(base)
    try:
        return d.maybe_resolve(name)
    except:
        return None




# field type definitions ---------------------------------------------------------------

DataTypes = (
Conf(id="string",      name=_(u"String"),             description=u""),
Conf(id="number",      name=_(u"Number"),             description=u""),
Conf(id="float",       name=_(u"Float"),              description=u""),
Conf(id="bool",        name=_(u"Bool"),               description=u""),
Conf(id="file",        name=_(u"File"),               description=u""),
Conf(id="htext",       name=_(u"HTML Text"),          description=u""),
Conf(id="text",        name=_(u"Text"),               description=u""),
Conf(id="date",        name=_(u"Date"),               description=u""),
Conf(id="datetime",    name=_(u"Datetime"),           description=u""),
Conf(id="list",        name=_(u"List"),               description=u""),
Conf(id="radio",       name=_(u"Radio Selection"),    description=u""),
Conf(id="mselection",  name=_(u"Multiple Selection"), description=u""),
Conf(id="mcheckboxes", name=_(u"Multiple Checkboxes"), description=u""),
Conf(id="url",         name=_(u"URL"),                description=u""),
Conf(id="urllist",     name=_(u"URL List"),           description=u""),
Conf(id="email",       name=_(u"Email"),              description=u""),
Conf(id="password",    name=_(u"Password"),           description=u""),
Conf(id="unit",        name=_(u"ID Reference"),       description=u""),
Conf(id="unitlist",    name=_(u"ID Reference List"),  description=u""),
Conf(id="code",        name=_(u"Code (Html, Javascript, Css)"), description=u""),
Conf(id="json",        name=_(u"Json"),               description=u""),
Conf(id="timestamp",   name=_(u"Timestamp"),          description=u""),
)


# system meta fields -----------------------------------------------------------------------
SystemFlds = (
FieldConf(id="id",             datatype="number",    size=8,     default=0,     required=0,   readonly=1, name=_(u"ID")),
FieldConf(id="pool_type",      datatype="list",      size=35,    default=u"",   required=1,   readonly=1, name=_(u"Type")),
FieldConf(id="pool_unitref",   datatype="number",    size=8,     default=0,     required=0,   readonly=1, name=_(u"Container")),
FieldConf(id="pool_state",     datatype="number",    size=4,     default=1,     required=0,   readonly=0, name=_(u"State")),
FieldConf(id="pool_stag",      datatype="number",    size=4,     default=0,     required=0,   readonly=0, name=_(u"Select Number")),
FieldConf(id="pool_datatbl",   datatype="string",    size=35,    default=u"",   required=1,   readonly=1, name=_(u"Data Table Name")),
FieldConf(id="pool_dataref",   datatype="number",    size=8,     default=0,     required=1,   readonly=1, name=_(u"Data Table Reference")),
FieldConf(id="title",          datatype="string",    size=255,   default=u"",   required=0,   readonly=0, name=_(u"Title"), fulltext=True),
FieldConf(id="pool_sort",      datatype="number",    size=8,     default=0,     required=0,   readonly=0, name=_(u"Sort")),
FieldConf(id="pool_wfp",       datatype="list",      size=35,    default=u"",   required=0,   readonly=0, name=_(u"Workflow Process")),
FieldConf(id="pool_wfa",       datatype="list",      size=35,    default=u"",   required=0,   readonly=0, name=_(u"Workflow Activity")),
FieldConf(id="pool_category",  datatype="list",      size=35,    default=u"",   required=0,   readonly=0, name=_(u"Category")),
FieldConf(id="pool_filename",  datatype="string",    size=255,   default=u"",   required=0,   readonly=0, name=_(u"Filename")),
FieldConf(id="pool_create",    datatype="datetime",  size=100,   default=u"",   required=0,   readonly=1, name=_(u"Created")),
FieldConf(id="pool_change",    datatype="datetime",  size=100,   default=u"",   required=0,   readonly=1, name=_(u"Changed")),
FieldConf(id="pool_createdby", datatype="string",    size=35,    default=u"",   required=0,   readonly=1, name=_(u"Created by")),
FieldConf(id="pool_changedby", datatype="string",    size=35,    default=u"",   required=0,   readonly=1, name=_(u"Changed by")),
)
ReadonlySystemFlds = ("id", "pool_type", "pool_datatbl", "pool_unitref", "pool_dataref")

# base table structure -------------------------------------------------------------------

MetaTbl = "pool_meta"
FileTbl = "pool_files"
FulltextTbl = "pool_fulltext"
SystemTbl = "pool_sys"
LocalGroupsTbl = "pool_groups"
"""
``Structure`` defines the additional tables with settings for identity column and table fields. 
"""
Structure={
FileTbl: {"identity": "fileid",
          "fields": (
    FieldConf(id="fileid",     datatype="number",    size=8,     default=0,    required=0,   readonly=1, name=_(u"Unique ID")),
    FieldConf(id="id",         datatype="number",    size=8,     default=0,    required=0,   readonly=1, name=_(u"Object ID")),
    FieldConf(id="filekey",    datatype="string",    size=35,    default='',   required=1,   readonly=0, name=_(u"File key")),
    FieldConf(id="filename",   datatype="string",    size=255,   default='',   required=0,   readonly=0, name=_(u"Filename")),
    FieldConf(id="path",       datatype="string",    size=255,   default='',   required=0,   readonly=0, name=_(u"Internal file path")),
    FieldConf(id="size",       datatype="number",    size=8,     default=0,    required=0,   readonly=0, name=_(u"File size")),
    FieldConf(id="extension",  datatype="string",    size=5,     default='',   required=0,   readonly=0, name=_(u"File extension")),
    FieldConf(id="version",    datatype="string",    size=5,     default='',   required=0,   readonly=0, name=_(u"Version")),
)},
FulltextTbl: {"identity": None,
              "fields": (
    FieldConf(id="id",     datatype="number",    size=8,     default=0,    required=1,   readonly=1, name=_(u"Object ID")),
    FieldConf(id="text",   datatype="text",      size=0,     default="",   required=0,   readonly=0, name=_(u"Text")),
    FieldConf(id="files",  datatype="text",      size=0,     default="",   required=0,   readonly=0, name=_(u"Files")),
)},
SystemTbl: {"identity": None,
            "fields": (
    FieldConf(id="id",     datatype="string",    size=50,    default='',   required=0,   readonly=0, name=_(u"Unique identifier")),
    FieldConf(id="value",  datatype="text",      size=0,     default="",   required=0,   readonly=0, name=_(u"Value")),
    FieldConf(id="ts",     datatype="number",    size=0,     default="",   required=0,   readonly=0, name=_(u"Timestamp")),
)},
LocalGroupsTbl: {"identity": None,
                "fields": (
    FieldConf(id="id",     datatype="number",    size=8,     default=0,    required=1,   readonly=1, name=_(u"Object ID")),
    FieldConf(id="userid", datatype="string",    size=35,    default="",   required=1,   readonly=1, name=_(u"User name")),
    FieldConf(id="groupid",datatype="string",    size=20,    default="",   required=1,   readonly=1, name=_(u"Group assignment")),
)}
}

# select tags (pool_stag) ----------------------------------------------------------------------------

StagContainer = 0        # 0-9
StagPage = 10            # 10-19
StagPageElement = 20     # 20-29
StagRessource = 50       # 50-59
StagUser = 100           # 100-109

AllTypes = 1


