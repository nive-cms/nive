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
"""

from pyramid.renderers import get_renderer

from nive.i18n import _
from nive.definitions import ViewConf, ViewModuleConf, FieldConf, WidgetConf, Conf
from nive.definitions import IApplication, IUser, IAdminWidgetConf, IUserDatabase, IPersistent, IModuleConf
from nive.definitions import IWebsiteRoot, ICMSRoot

from nive.views import BaseView
from nive.forms import ValidationError, HTMLForm

from nive.utils.utils import SortConfigurationList, ConvertDictToStr


# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf(
    id = "administration",
    name = _(u"Administration"),
    static = "",
    context = IApplication,
    view = "nive.adminview.view.AdminView",
    templates = "nive.adminview:",
    permission = "administration"
)
t = configuration.templates
configuration.views = [
    # User Management Views
    ViewConf(name = "admin",    attr = "view",   renderer = t+"root.pt"),
    ViewConf(name = "basics",   attr = "editbasics",   renderer = t+"form.pt"),
    #ViewConf(name = "portal",   attr = "editportal",   renderer = t+"form.pt"),
    ViewConf(name = "tools",    attr = "tools",   renderer = t+"tools.pt"),
    ViewConf(name = "modules",  attr = "view",   renderer = t+"modules.pt"),
    ViewConf(name = "views",    attr = "view",   renderer = t+"views.pt"),
]

configuration.widgets = [
    WidgetConf(name=_(u"Basics"),    viewmapper="basics",     id="admin.basics",   sort=100,   apply=(IApplication,), widgetType=IAdminWidgetConf,
               description=u""),
    #WidgetConf(name=_(u"Global"),    viewmapper="portal",     id="admin.portal",   sort=300,   apply=(IApplication,), widgetType=IAdminWidgetConf),
    WidgetConf(name=_(u"Tools"),     viewmapper="tools",      id="admin.tools",    sort=400,   apply=(IApplication,), widgetType=IAdminWidgetConf,
               description=u""),
    WidgetConf(name=_(u"Modules"),   viewmapper="modules",    id="admin.modules",  sort=800,   apply=(IApplication,), widgetType=IAdminWidgetConf,
               description=_(u"Read only listing of all registered modules and settings.")),
    WidgetConf(name=_(u"Views"),     viewmapper="views",      id="admin.views",    sort=900,   apply=(IApplication,), widgetType=IAdminWidgetConf,
               description=_(u"Read only listing of all registered views grouped by view modules.")),
]


"""
dbAdminConfiguration
--------------------
managing database settings through the web interface makes sense if the values are
stored outside the database.
"""
#@nive_module
dbAdminConfiguration = ViewModuleConf(
    id = "databaseAdministration",
    name = _(u"Database Administration"),
    static = "",
    context = IApplication,
    view = "nive.adminview.view.AdminView",
    templates = "nive.adminview:",
    permission = "administration",
    views = [
        # Database Management Views
        ViewConf(name = "database", attr = "editdatabase",   renderer = "nive.adminview:form.pt"),
    ],
    widgets = [
        WidgetConf(name=_(u"Database"),  viewmapper="database",   id="admin.database", sort=200,   apply=(IApplication,), widgetType=IAdminWidgetConf),
    ]
)

        
    
# view and form implementation ------------------------------------------------------------------


class ConfigurationForm(HTMLForm):
    
    actions = [
        Conf(id=u"default",    method="Start",   name=u"Initialize", hidden=True,  css_class=u"",            html=u"", tag=u""),
        Conf(id=u"edit",       method="Update",  name=u"Save",       hidden=False, css_class=u"formButton btn-primary",  html=u"", tag=u""),
    ]
    
    def Start(self, action, redirect_success, **kw):
        """
        Initially load data from object. 
        context = obj
        
        returns bool, html
        """
        conf = self.context
        data = {}
        for f in self.GetFields():
            # data
            if f.id in conf:
                if f.datatype=="password":
                    continue
                data[f.id] = conf.get(f.id,"")
        return data!=None, self.Render(data)


    def Update(self, action, redirect_success, **kw):
        """
        Process request data and update object.
        
        returns bool, html
        """
        msgs = []
        conf=self.context
        result,data,errors = self.Validate(self.request)
        if result:
            # lookup persistent manager for configuration
            storage = self.app.Factory(IModuleConf, "persistence")
            if storage:
                storage(app=self.app, configuration=conf).Save(data)
                msgs.append(_(u"OK. Data saved."))
            else:
                msgs.append(_(u"No persistent storage for configurations activated. Nothing saved."))
                result = False
            errors=None
            if self.view and redirect_success:
                redirect_success = self.view.ResolveUrl(redirect_success, obj)
                if self.use_ajax:
                    self.view.AjaxRelocate(redirect_success, messages=msgs)
                else:
                    self.view.Redirect(redirect_success, messages=msgs)
        return result, self.Render(data, msgs=msgs, errors=errors)    


class AdminBasics(BaseView):

    def index_tmpl(self):
        i = get_renderer("nive.adminview:index.pt").implementation()
        return i

    def getAdminWidgets(self):
        app = self.context.app
        widgets = app.QueryConf(IAdminWidgetConf, app)
        confs = []
        if not widgets:
            return confs
        for n,w in widgets:
            confs.append(w)
        return SortConfigurationList(confs, "sort")

    def view(self):
        return {}

    def RenderConf(self, c):
        return u"""<strong><a onclick="$('#%d').toggle()" style="cursor:pointer">%s</a></strong><br/>%s""" % (
                abs(id(c)), 
                unicode(c).replace("<", "&lt;").replace(">", "&gt;"), 
                self.Format(c, str(abs(id(c))))
                )
        
        
    def Format(self, conf, ref):
        """
        Format configuration for html display
        
        returns string
        """
        v=[u"<table id='%s' style='display:none'>"%(ref)]
        for d in conf.__dict__.items():
            if d[0]=="_empty":
                continue
            if d[0]=="_parent" and not d[1]:
                continue
            value = d[1]
            if value==None:
                try:
                    value = conf.parent.get(d[0])
                except:
                    pass
            if isinstance(value, basestring):
                pass
            elif isinstance(value, (tuple, list)):
                a=[u""]
                for i in value:
                    if hasattr(i, "ccc"):
                        a.append(self.RenderConf(i))
                    else:
                        a.append(unicode(i).replace(u"<", u"&lt;").replace(u">", u"&gt;")+u"<br/>")
                value = u"".join(a)
            elif isinstance(value, dict):
                value = ConvertDictToStr(value, u"<br/>")
            else:
                value = unicode(value).replace(u"<", u"&lt;").replace(u">", u"&gt;")
            v.append(u"<tr><th>%s</th><td>%s</td></tr>\r\n" % (d[0], value))
        v.append(u"</table>")
        return u"".join(v)


    def AdministrationLinks(self, context=None):
        if context:
            apps = (context,)
        else:
            apps = self.context.app.portal.GetApps()
        links = []
        for app in apps:
            if not hasattr(app, "registry"):
                continue
            # search for cms editor
            for root in app.GetRoots():
                if ICMSRoot.providedBy(root):
                    links.append({"href":self.Url(root), "title":app.configuration.title + u": " + _(u"editor")})
                elif IWebsiteRoot.providedBy(root):
                    links.append({"href":self.Url(root), "title":app.configuration.title + u": " + _(u"public")})
            # administration
            links.append({"href":self.FolderUrl(app)+u"admin", "title":app.configuration.title + u": " + _(u"administration")})
            # user management
            if IUserDatabase.providedBy(app):
                links.append({"href":self.FolderUrl(app)+u"usermanagement", "title":app.configuration.title + u": " + _(u"user management")})
        return links
                
    

class AdminView(AdminBasics):
    
    def editbasics(self):
        fields = (
            FieldConf(id=u"title",           datatype="string", size=255,  required=0, name=_(u"Application title")),
            FieldConf(id=u"description",     datatype="text",   size=5000, required=0, name=_(u"Application description")),
            FieldConf(id=u"workflowEnabled", datatype="bool",   size=2,    required=0, name=_(u"Enable workflow engine")),
            FieldConf(id=u"fulltextIndex",   datatype="bool",   size=2,    required=0, name=_(u"Enable fulltext index")),
            FieldConf(id=u"frontendCodepage",datatype="string", size=10,   required=1, name=_(u"Codepage used in html frontend")),
        )
        form = ConfigurationForm(view=self, context=self.context.configuration, app=self.context)
        form.fields = fields
        form.Setup() 
        # process and render the form.
        result, data, action = form.Process()
        return {u"content": data, u"result": result, u"head": form.HTMLHead()}


    def editdatabase(self):
        dbtypes=[{"id":"MySql","name":"MySql"},{"id":"Sqlite3","name":"Sqlite3"}]
        fields = (
            FieldConf(id=u"context",  datatype="list",   size=20,   required=1, name=_(u"Database type to be used"), listItems=dbtypes, 
                      description=_(u"Supports 'Sqlite3' and 'MySql' by default. MySql requires python-mysqldb installed.")),
            FieldConf(id=u"fileRoot", datatype="string", size=500,  required=0, name=_(u"Relative or absolute root directory for files")),
            FieldConf(id=u"dbName",   datatype="string", size=500,  required=1, name=_(u"Database file path or name"),
                      description=_(u"Sqlite3=database file path, MySql=database name")),
            FieldConf(id=u"host",     datatype="string", size=100,  required=0, name=_(u"Database server host")),
            FieldConf(id=u"port",     datatype="number", size=8,    required=0, name=_(u"Database server port")),
            FieldConf(id=u"user",     datatype="string", size=100,  required=0, name=_(u"Database server user")),
            FieldConf(id=u"password", datatype="password", size=100,required=0, name=_(u"Database server password")),
        )
        form = ConfigurationForm(view=self, context=self.context.dbConfiguration, app=self.context)
        form.fields = fields
        form.Setup()
        # process and render the form.
        result, data, action = form.Process()
        return {u"content": data, u"result": result, u"head": form.HTMLHead()}


    def editportal(self):
        fields = (
            FieldConf(id=u"portalDefaultUrl", datatype="string", size=200, required=1, name=_(u"Redirect for portal root (/) requests")),
            FieldConf(id=u"favicon",      datatype="string", size=200,  required=0, name=_(u"Favicon asset path")),
            FieldConf(id=u"robots",       datatype="text",   size=10000,required=0, name=_(u"robots.txt contents")),
            FieldConf(id=u"loginUrl",     datatype="string", size=200,  required=1, name=_(u"Login form url")),
            FieldConf(id=u"forbiddenUrl", datatype="string", size=200,  required=1, name=_(u"Redirect for unauthorized requests")),
            FieldConf(id=u"logoutUrl",    datatype="string", size=200,  required=1, name=_(u"Redirect on logout")),
            FieldConf(id=u"accountUrl",   datatype="string", size=200,  required=0, name=_(u"User account page url")),
        )
        form = ConfigurationForm(view=self, context=self.context.portal.configuration, app=self.context)
        form.fields = fields
        form.Setup() 
        # process and render the form.
        result, data, action = form.Process()
        return {u"content": data, u"result": result, u"head": form.HTMLHead()}

    
    def tools(self):
        app = self.context.app
        head = data = u""
        
        selected = self.GetFormValue('t')
        if selected:
            tool = app.GetTool(selected, contextObject=app)
            data = self.RenderView(tool)
            # pyramid bug? reset the active view in request
            self.request.__dict__['__view__'] = self
            return {u"content": data, u"tools": [], u"tool":tool}

        t = app.GetAllToolConfs(contextObject=app)
        return {u"content": data, u"tools": t, u"tool":None}

    
