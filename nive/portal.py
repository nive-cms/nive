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
The *portal* manages applications and is the pyramid_ or wsgi_ root. There is only one
portal in each instance.

The portal handles the cms applications and global components like the user database. 
Applications have to be registered by calling ``Register(application)`` on initialisation.

- Routes url names to applications
- Calls ``Startup()`` for each registered application on server startup
- Provides connection start and finish events
- Collects all registered security groups from applications 

Allows by default all permissions for admins ::

    __acl__ = (Allow, "group:admin", ALL_PERMISSIONS)

Also redirects for login, forbidden, logout and default url are configured here ::

        portalDefaultUrl = "/website/"
        loginUrl = "/userdb/udb/login"
        loginSuccessUrl = "/website/"
        forbiddenUrl = "/userdb/udb/login"
        logoutUrl = "/userdb/udb/logout"
        logoutSuccessUrl = "/website/"
        accountUrl = "/userdb/udb/update"

Interface: IPortal
"""

import copy
import time
import logging
import gc

from pyramid.events import NewRequest

from nive.i18n import _
from nive.definitions import IPortal, PortalConf, implements, Conf
from nive.definitions import ConfigurationError
from nive.helper import ResolveConfiguration, ResolveName
from nive.security import User, authenticated_userid, Allow, ALL_PERMISSIONS
from nive.events import Events
from nive.utils.utils import SortConfigurationList



class Portal(Events, object):
    """ """
    implements(IPortal)

    __name__ = u""
    __parent__ = None
    
    def __init__(self, configuration = None):
        """
        Events:
        - init(configuration)
        """
        self.components = []
        self.groups = [Conf(id=u"authenticated", name=_(u"Authenticated"), visible=True)]
        self.__acl__ = [(Allow, "group:admin", ALL_PERMISSIONS)]
        
        self.configuration = configuration or PortalConf()
        
        # 0.9.4 - moved to configuration
        #self.portalDefaultUrl = "/website/"
        #self.loginUrl = "/userdb/udb/login"
        #self.forbiddenUrl = "/userdb/udb/login"
        #self.logoutUrl = "/userdb/udb/logout"
        #self.accountUrl = "/userdb/udb/update"
        #self.robots = u""

        self.Signal("init", configuration=self.configuration)

    def __del__(self):
        self.Close()
        #print "del portal"
        
    def __getitem__(self, name):
        """
        Called by traversal machinery
        
        event: getitem(obj) called with the traversed object
        """
        try:
            obj = getattr(self, name)
            self.Signal("getitem", obj=obj)
            return obj
        except AttributeError:
            raise KeyError, name
        
    def Register(self, comp, name=None):
        """
        Register an application or component. This is usually done in the pyramid
        app file. The registered component is automatically loaded and set up to work
        with url traversal.
        
        *comp* can be one of the following cases

        - AppConf object
        - AppConf string as python dotted name
        - python object. Requires *name* parameter or *comp.id* attribute
        
        *name* is used as the url path name to lookup the component.

        """
        log = logging.getLogger("portal")
        iface, conf = ResolveConfiguration(comp)
        if not conf:
            if not name or isinstance(comp, basestring):
                raise ConfigurationError, "Portal registration failure. No name given (%s)" % (str(comp))
        elif isinstance(comp, basestring):
            c = ResolveName(conf.context)
            comp = c(conf)
        elif iface and iface.providedBy(comp):
            c = ResolveName(conf.context)
            comp = c(conf)
        try:
            if not name:
                name = conf.id
        except:
            pass
        if not name:
            raise ConfigurationError, "Portal registration failure. No name given (%s)" % (str(comp))

        log.debug("Portal.Register: %s %s", name, repr(conf))
        self.__dict__[name] = comp
        comp.__parent__ = self
        comp.__name__ = name
        self.components.append(name)
        #self.RegisterGroups(comp)


    def Startup(self, pyramidConfig, debug=False):
        """
        *Startup* is called once by the *main* function of the pyramid wsgi app on 
        server startup. All configuration, registration and setup is handled during
        the startup call. Calls *Startup()* for each registered component.
        
        *pyramidConfig* is the pyramid registration configuration object for views and other 
        system components. nive ViewConf_ and ViewModuelConf_ are automatically with
        pyramid. 
        
        *debug* signals whether running in debug mode or not.
        """
        log = logging.getLogger("portal")
        log.debug("Portal.Startup with debug=%s", str(debug))
        if pyramidConfig:
            self.SetupPortalViews(pyramidConfig)
            #pyramidConfig.add_subscriber(self.StartConnection, iface=NewRequest)
        for c in self.components:
            component = getattr(self, c)
            if hasattr(component, "Startup"):
                component.Startup(pyramidConfig, debug=debug)


    def GetApps(self, interface=None):
        """
        Returns registered components and apps as list.
        """
        if isinstance(interface, basestring):
            interface = ResolveName(interface)
        apps=[]
        for name in self.components:
            a = getattr(self, name)
            if interface:
                if not interface.providedBy(a):
                    continue
            apps.append(a)
        return apps


    def StartConnection(self, event):
        """
        Called by pyramid for each new connection with event as parameter. The
        current request stored as *event.request*. Stores the authenticated user 
        *event.request.environ["REMOTE_USER"]*.
        
        Event:
        - start(event)
        """
        uid = authenticated_userid(event.request)
        event.request.environ["REMOTE_USER"] = uid
        event.request.environ["START_TIME"] = time.time()
        self.Signal("start", event=event)
        #event.request.add_finished_callback(self.FinishConnection)


    def FinishConnection(self, request):
        """
        Called by pyramid on termination for each connection with request as parameter.

        Event:
        - finish(request)
        """
        self.Signal("finish", request)
        

    def GetGroups(self, sort=u"id", visibleOnly=False):
        """
        returns all groups registered by components as list
        """
        if visibleOnly:
            #opt
            g = []
            for a in self.groups:
                if not a.get("hidden"):
                    g.append(a)
        else:
            g = self.groups
        if not sort:
            return g
        l = copy.deepcopy(g)
        return SortConfigurationList(l, sort)


    @property
    def portal(self):
        return self
    

    def RegisterGroups(self, component):
        """
        Collects groups from the component
        """
        try:
            gr = component.configuration.groups
            for g in gr:
                add = 1
                for g2 in self.groups:
                    if g["id"] == g2["id"]:
                        add = 0
                        break
                if add:
                    self.groups.append(g)
        except:
            pass
                

    def SetupPortalViews(self, config):
        # redirects
        config.add_view(error_view, context=HTTPError)
        config.add_view(forbidden_view, context=Forbidden)
        config.add_view(portal_view, name="", context="nive.portal.Portal")
        config.add_view(robots_view, name="robots.txt", context="nive.portal.Portal")
        config.add_view(sitemap_view, name="sitemap.xml", context="nive.portal.Portal")
        config.add_view(logout_view, name="logout", context="nive.portal.Portal")
        config.add_view(login_view,  name="login", context="nive.portal.Portal")
        config.add_view(account_view,name="account", context="nive.portal.Portal")
        #config.add_view(favicon_view, name=u"favicon.txt", context=u"nive.portal.Portal", view=PortalViews)
    
        # translations
        config.add_translation_dirs('nive:locale/')
        
        config.commit()

    
    def Close(self):
        for name in self.components:
            a = getattr(self, name)
            a.Close()
            setattr(self, name, None)
            

    # bw 0.9.4
    def GetComponents(self):
        return self.GetApps()





from views import Redirect
from pyramid.exceptions import Forbidden
from pyramid.response import Response
from pyramid.httpexceptions import HTTPError, HTTPNotFound, HTTPServerError


def forbidden_view(request):
    # login form
    url = request.referrer
    portal = request.context.app.portal
    return Redirect(portal.configuration.forbiddenUrl+"?redirect="+request.url, request, messages=[u"Please log in"])
       
def login_view(context, request):
    # login form
    portal = context
    return Redirect(portal.configuration.loginUrl+"?redirect="+request.GET.get("redirect",""), request)
    
def logout_view(context, request):
    # logout to login form
    portal = context
    return Redirect(portal.configuration.logoutUrl+"?redirect="+request.GET.get("redirect",""), request)
    
def portal_view(context, request):
    # website root / domain root redirect
    portal = context
    return Redirect(portal.configuration.portalDefaultUrl, request)
    
def account_view(context, request):
    # account page
    portal = context
    return Redirect(portal.configuration.accountUrl, request)
    
def robots_view(context, request):
    portal = request.context
    # website root / domain root redirect
    r = Response(content_type="text/plain", conditional_response=False)
    r.unicode_body = portal.configuration.robots
    return r

def sitemap_view(context, request):
    portal = request.context
    # portal google sitemap link
    r = Response(content_type="text/plain", conditional_response=False)
    r.unicode_body = portal.configuration.get("sitemap", u"")
    return r

def error_view(context, request):
    #context.body = str(context)
    return context





    
