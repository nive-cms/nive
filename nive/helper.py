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

__doc__ = ""

import json
import os

from pyramid.path import DottedNameResolver
from pyramid.path import AssetResolver
from pyramid.path import caller_package

from nive import *
from nive.definitions import implements, Interface
from nive.utils.dataPool2.files import File
from nive.utils import strings


def ResolveName(name, base=None, raiseExcp=True):
    """
    Lookup python object by dotted python name.
    Wraps pyramid.DottedNameResolver.
    
    returns object or None
    """
    if not name:
        return None
    if not isinstance(name, basestring):
        return name
    if not base:
        base = caller_package()
    if not raiseExcp:
        d = DottedNameResolver(base)
        return d.maybe_resolve(name)
    d = DottedNameResolver(base)
    return d.resolve(name)


def ResolveAsset(name, base=None, raiseExcp=True):
    """
    Lookup asset path (template, json or any other file) and returns asset 
    descriptor object or None.
    """
    if not name:
        return None
    if not isinstance(name, basestring):
        return name
    if not base:
        base = caller_package()
    if name.startswith("./"):
        # use relative file system path
        name = os.getcwd()+name[1:]
    if not raiseExcp:
        try:
            d = AssetResolver(base)
            return d.resolve(name)
        except:
            return None
    d = AssetResolver(base)
    return d.resolve(name)

    
def ResolveConfiguration(conf, base=None):
    """
    Lookup configuration object by dotted python name. Returns interface and configuration object.
    Extends pyramid.DottedNameResolver with .json file support for configuration objects.
    
    Supports the following cases:
    
    - Path and file name to .json file. requires `type` set to one of the 
      configuration types: 
      *AppConf, FieldConf, DatabaseConf, RootConf, ObjectConf, ViewModuleConf, ViewConf, ToolConf, 
      GroupConf, CategoryConf*
    - Dotted python name for configuration object including attribute name of configuration instance.
    - Dotted python name for object. Uses the convention to load the configuration from the 
      'configuration' attribute of the referenced object.
    - Configuration instance. Will just return it.
    
    returns Interface, configuration
    """
    # string instance
    if isinstance(conf, basestring):
        if not base:
            base = caller_package()
        # json file
        if conf.find(".json")!= -1:
            s = strings.DvString()
            path = ResolveAsset(conf, base)
            s.LoadFromFile(path.abspath())
            conf = json.loads(s.Get())
        # resolve attribute name
        elif conf:
            c = ResolveName(conf, base=base)
            if hasattr(c, "configuration"):
                conf = c.configuration
            else:
                conf = c

    # dict instance
    if isinstance(conf, dict):
        # load by interface
        if not "type" in conf:
            raise TypeError, "Configuration type not defined"
        c = ResolveName(conf["type"], base="nive")
        del conf["type"]
        conf = c(**conf)

    # module and not configuration
    if not IConf.providedBy(conf):
        if hasattr(conf, "configuration"):
            conf = conf.configuration
        
    # object instance
    if IAppConf.providedBy(conf): return IAppConf, conf
    if IDatabaseConf.providedBy(conf): return IDatabaseConf, conf
    if IFieldConf.providedBy(conf): return IFieldConf, conf
    if IRootConf.providedBy(conf): return IRootConf, conf
    if IObjectConf.providedBy(conf): return IObjectConf, conf
    if IViewModuleConf.providedBy(conf): return IViewModuleConf, conf
    if IViewConf.providedBy(conf): return IViewConf, conf
    if IToolConf.providedBy(conf): return IToolConf, conf
    if IPortalConf.providedBy(conf): return IPortalConf, conf
    if IGroupConf.providedBy(conf): return IGroupConf, conf
    if ICategoryConf.providedBy(conf): return ICategoryConf, conf
    if IModuleConf.providedBy(conf): return IModuleConf, conf
    if IWidgetConf.providedBy(conf): return IWidgetConf, conf
    if IWfProcessConf.providedBy(conf): return IWfProcessConf, conf
    if IWfStateConf.providedBy(conf): return IWfStateConf, conf
    if IWfTransitionConf.providedBy(conf): return IWfTransitionConf, conf
    if IConf.providedBy(conf): return IConf, conf
    return None, None
    #raise TypeError, "Unknown configuration object: %s" % (str(conf))
    
    
def LoadConfiguration(conf, base=None):
    """
    same as ResolveConfiguration except only the configuration object is
    returned
    """
    if not base:
        base = caller_package()
    i,c = ResolveConfiguration(conf, base)
    return c


def FormatConfTestFailure(report, fmt="text"):
    """
    Format configuration test() failure
    
    returns string
    """
    v=[]
    for r in report:
        v+= u"-----------------------------------------------------------------------------------\r\n"
        v+= str(r[0]) + " " + r[1] + "\r\n"
        v+= u"-----------------------------------------------------------------------------------\r\n"
        for d in r[2].__dict__.items():
            a = d[1]
            if a==None:
                try:
                    a = r[2].parent.get(d[0])
                except:
                    pass
            v+= str(d[0])+u":  "+str(a)+u"\r\n"
        v+= u"\r\n"
    return "".join(v)


def ClassFactory(configuration, reloadClass=False, raiseError=True, base=None):
    """
    Creates a python class reference from configuration. Uses configuration.context as class
    and dynamically adds classes listed as configuration.extensions as base classes.
    
    configuration requires

    - configuration.context
    - configuration.extensions [optional]
    """
    tag = configuration.context
    if "extensions" in configuration:
        bases = configuration.extensions
    else:
        bases = None
    c = GetClassRef(tag, reloadClass, raiseError, base)
    if not c:
        return None
    if not bases:
        return c
    # load extensions
    b = [c]
    #opt
    for r in bases:
        r = GetClassRef(r, reloadClass, raiseError, base)
        if not r:
            continue
        b.append(r)
    if len(b)==1:
        return c
    # create new class with name configuration.context
    return type("_factory_"+c.__name__, tuple(b), {})


def GetClassRef(tag, reloadClass=False, raiseError=True, base=None):
    """
    Resolve class reference from python dotted string.
    """
    if isinstance(tag, basestring):
        if raiseError:
            classRef = ResolveName(tag, base=base)
        else:
            try:
                classRef = ResolveName(tag, base=base)
            except ImportError, e:
                return None
        if not classRef:
            return None
        #if reloadClass:
        #    reload(classRef)
        return classRef
    # tag is class ref
    return tag




# test request and response --------------------------------------

class Response(object):
    headerlist = []

class Request(object):
    POST = {}
    GET = {}
    url = ""
    username = ""
    response = Response()
    environ = {}

class Event(object):
    request = Request()

class FakeLocalizer(object):
    def translate(self, text):
        return text
