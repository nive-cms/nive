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
Website Design
----------------
This module includes everything required to render the public website:

- css, javascript, layout images (in design/static)
- templates for page elements and pages (in design/templates)
- the main template (design/templates/index.pt)
- required views
"""

import os
from time import time
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
from pyramid.renderers import get_renderer, render_to_response
from pyramid.httpexceptions import HTTPNotFound

from nive.i18n import _
from nive.definitions import ViewModuleConf, ViewConf, ConfigurationError
from nive.definitions import IWebsite, IWebsiteRoot, IPage, IRoot, IPageElement, IObject, IViewModuleConf
from nive.views import BaseView

    
# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf(
    id = "design",
    name = _(u"Website design and view"),
    static = "nive.cms.design:static",
    templates = "nive.cms.design:templates",
    mainTemplate = "index.pt",
    permission = "view",
    view = "nive.cms.design.view.Design",
    views = [
        ViewConf(id="appview",  name = "",     attr = "app",  context = IWebsite),
        ViewConf(id="search",   name ="search",attr="search", context = IRoot),
        ViewConf(id="su",       name ="su",    attr = "open", context = IRoot),
        ViewConf(id="rootview", name = "",     attr = "view", context = IWebsiteRoot),
        ViewConf(id="objview",  name = "",     attr = "view", context = IPage,        containment = IWebsiteRoot),
        ViewConf(id="objview",  name = "",     attr = "view", context = IPageElement),
        ViewConf(id="objfile",  name = "file", attr = "file", context = IObject),
    ]
)





class Design(BaseView):
    """
    get view module as attr for view class
    """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.viewModule = context.app.QueryConfByName(IViewModuleConf, "design")
        if not self.viewModule:
            raise ConfigurationError, "'design' view module configuration not found"
        #self.viewModule = configuration
        self.appRequestKeys = []
        self._t = time()
        self.fileExpires = 3600
        
    def IsEditmode(self):
        try:
            return self.request.editmode
        except:
            return False
        
    def HtmlTitle(self):
        t = self.request.environ.get(u"htmltitle")
        if not t:
            t = self.context.GetTitle()
        t2 = self.context.app.configuration.title
        return t2 + u" - " + t

    # routed views -------------------------------------------------------------------------------------
    
    def view(self, cmsview = None):
        # redirect if page is linked
        if IPage.providedBy(self) and self.context.IsLinked():
            return self.Redirect(self.context.data["pagelink"]) 
        values = {u"cmsview": cmsview, u"context": self.context, u"view": self} 
        return self.DefaultTemplateRenderer(values)
    
    def search(self, cmsview = None):
        values = {u"cmsview": cmsview, u"context": self.context, u"view": self}
        name = u"search.pt"
        return self.DefaultTemplateRenderer(values, templatename=name)

   # main template ------------------------------------------------------------
        
    def index_tmpl(self):
        tmpl = self._LookupTemplate(self.viewModule.mainTemplate)
        i = get_renderer(tmpl).implementation()
        return i
       
    # redirects ----------------------------------------------------

    def app(self):
        root = self.context.GetRoot()
        url = self.PageUrl(root)
        self.Redirect(url)
    
    def open(self):
        ref = self.GetFormValue(u"r")
        page = self.context.LookupObj(ref)
        if not page:
            raise HTTPNotFound, unicode(ref)
        page = page.GetPage()
        url = self.PageUrl(page)
        self.Redirect(url)
    
        
    # html widgets ----------------------------------------------------
    
    def breadcrumbs(self, addHome=0):
        """
        """
        base = self.context.GetPage()
        parents = base.GetParents()
        parents.reverse()
        if not addHome:
            parents = parents[1:]
        if len(parents)==0:
            return u""
        html = StringIO()
        for page in parents:
            html.write(u"""<li><a href="%s">%s</a> <span class="divider">/</span></li>""" % (self.PageUrl(page), page.GetTitle()))
        html.write(u"""<li class="active">%s </li>""" % (base.GetTitle()))
        return html.getvalue()
    

    def navigationTop(self, addHome=1):
        """
        only first level pages
        """
        html = StringIO()
        page = self.context
        root = page.GetRoot()
        if addHome:
            highlight = u""
            if page.id == root.id:
                highlight = u"active"
            html.write(u"""<li class="%s"><a href="%s">%s</a></li>""" % (highlight, 
                                                                         self.PageUrl(root, usePageLink=1), 
                                                                         root.GetTitle()))
        
        path = page.GetParentIDs()
        pages = root.GetPages()
        for page in pages:
            if page.data.get("navHidden"):
                continue
            # highlight, current
            if page.id == self.context.id or page.id in path:
                highlight = u"active"
            else:
                highlight = u""
            # link
            html.write(u"""<li class="%s"><a href="%s">%s</a></li>""" % (highlight, 
                                                                         self.PageUrl(page, usePageLink=not self.IsEditmode()), 
                                                                         page.GetTitle()))
        return html.getvalue()


    def navigationTree(self, addHome=1, page=None, ulclass="nav nav-tabs nav-stacked"):
        """
        tree navigation for all levels
        """
        if not page:
            page = self.context.GetPage()
        root = page.GetRoot()
        html = StringIO()
        html.write(u"""<ul id="level1" class="%s">""" % (ulclass))
        if addHome:
            highlight = u""
            selected = u""
            if page.id == root.id:
                selected = u"current"
                highlight = u"active"
            html.write(u"""<li class="%s"><a href="%s" class="%s">%s</a></li>""" % (highlight, 
                                                                                    self.PageUrl(root, usePageLink=not self.IsEditmode()), 
                                                                                    selected, 
                                                                                    root.GetTitle()))
        
        path = page.GetParentIDs()
        level = 1
        html = self._navigationLevel(root, level, page, path, html, ulclass)
        html.write(u"""</ul>""")   #str(DateTime().timeTime()-t)   
        return html.getvalue()


    def navigationSub(self, page=None, ulclass="nav nav-tabs nav-stacked"):
        """
        tree subpages of current first level page
        """
        if not page:
            page = self.context.GetPage()
        base = page.GetParent()
        if page.GetID()<=0:
            return u""
        elif base.GetID()<=0:
            base = page
        else:
            while base.GetParent().GetID() > 0:
                base = base.GetParent()
        
        root = base
        path = page.GetParentIDs()
        level = 1
        html = StringIO()
        html.write(u"""<ul id="level1" class="%s">""" % (ulclass))
        html = self._navigationLevel(root, level, page, path, html, ulclass)
        html.write(u"""</ul>""")
        return html.getvalue()


    def _navigationLevel(self, current, level, active, path, io, ulclass):
        """
        """
        pages = current.GetPages()
        # sublevel
        if len(pages) and level > 1:
            io.write(u"""<li><ul id="level%d" class="%s">""" % (level, ulclass))
        
        for page in pages:
            if page.data.get("navHidden"):
                continue
        
            # highlight, current
            highlight = u""
            selected = u""
            if active.id == page.id:
                selected = u"current"
                highlight = u"active"
            elif page.id in path:
                highlight = u"active"
            
            # link
            io.write(u"""<li class="%s"><a href="%s" class="%s">%s</a></li>""" % (highlight, 
                                                                                  self.PageUrl(page, usePageLink=not self.IsEditmode()), 
                                                                                  selected, 
                                                                                  page.GetTitle()))
            
            if highlight or selected:
                io = self._navigationLevel(page, level+1, active, path, io, ulclass)
        
        if len(pages) and level > 1:
            io.write(u"""</ul></li>\r\n""")
        return io

    
