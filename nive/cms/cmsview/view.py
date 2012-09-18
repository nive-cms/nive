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
nive CMS toolbox and editor view layer
----------------------------------------
"""
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
from operator import itemgetter, attrgetter
    
from pyramid.i18n import get_localizer

from nive.i18n import _
from nive.definitions import ViewModuleConf, ViewConf, WidgetConf
from nive.definitions import IContainer, IApplication, IPortal, IPage, IObject, IRoot, IToolboxWidgetConf, IEditorWidgetConf
from nive.definitions import IToolboxWidgetConf, IEditorWidgetConf, ICMSRoot
from nive.cms.design import view as design 


# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf(
    id = "cmsview",
    name = u"CMS Editor",
    static = "nive.cms.cmsview:static",
    templates = "nive.cms.cmsview:",
    permission = "read",
    context = IObject,
    containment = ICMSRoot,  #"nive.cms.cmsview.cmsroot.cmsroot",
    view = "nive.cms.cmsview.view.Editor"
)
# views -----------------------------------------------------------------------------
# shortcuts
t = configuration.templates 

configuration.views = [
    ViewConf(name = "editor", attr = "editor", context=IContainer, permission="view", containment=IApplication),
    ViewConf(name = "exiteditor", attr = "exit", context=IContainer, permission="view", containment=IApplication),
    ViewConf(name = "exiteditor", attr = "exitapp", context=IApplication, permission="view", containment=IPortal),
    
    ViewConf(id="rootview", name = "",     attr = "view", context = ICMSRoot, containment=IApplication),
    ViewConf(id="objview",  name = "",     attr = "view", context = IPage),
    
    # object
    ViewConf(name = "edit", attr = "edit", renderer = t+"edit.pt", permission="edit"),
    ViewConf(name = "meta", attr = "meta", renderer = t+"meta.pt"),
    ViewConf(name ="delfile",attr= "delfile", permission="delete"),
                
    # cut, copy
    ViewConf(name = "cut",  attr = "cut",  context = IContainer, permission="edit"),
    ViewConf(name = "copy", attr = "copy", context = IContainer, permission="edit"),
    
    # widgets
    ViewConf(name = "elementListWidget", attr = "elementListWidget", context = IContainer, permission="edit"),
    ViewConf(name = "elementAddWidget",  attr = "elementAddWidget",  context = IObject, permission = "add"),
    ViewConf(name = "elementAddWidget",  attr = "elementAddWidget",  context = IRoot, permission = "add"),
    
    # container
    ViewConf(name = "add",       attr = "add",    context = IContainer, renderer = t+"add.pt", permission="add"),
    ViewConf(name = "delete",    attr = "delete", context = IContainer, renderer = t+"delete.pt", permission = "delete"),
    
    # sort
    ViewConf(name = "sortpages", attr = "sortpages", context = IPage, renderer = t+"sort.pt", permission="edit"),
    ViewConf(name = "sortpages", attr = "sortpages", context = IRoot, renderer = t+"sort.pt", permission="edit"),
    ViewConf(name="sortelements",attr="sortelements",context = IContainer, renderer = t+"sort.pt", permission="edit"),
    ViewConf(name = "moveup",    attr = "moveup",    context = IContainer, permission="edit"),
    ViewConf(name = "movedown",  attr = "movedown",  context = IContainer, permission="edit"),
    ViewConf(name = "movetop",   attr = "movetop",   context = IContainer, permission="edit"),
    ViewConf(name = "movebottom",attr = "movebottom",context = IContainer, permission="edit"),
    
    # paste
    ViewConf(name = "paste", attr = "paste", context = IContainer, permission = "add"),
    
    # widgets
    ViewConf(name = "addpageWidget",  attr = "tmpl", renderer = t+"widgets/widget_addpage.pt",    context = IContainer, permission="add"),
    ViewConf(name = "editpageWidget", attr = "tmpl", renderer = t+"widgets/widget_editpage.pt",   context = IContainer, permission="edit"),
    ViewConf(name = "subpagesWidget", attr = "tmpl", renderer = t+"widgets/widget_subpages.pt",   context = IContainer),
    ViewConf(name = "settingsWidget", attr = "tmpl", renderer = t+"widgets/widget_settings.pt",   context = IContainer)
]


# toolbox and editor widgets ----------------------------------------------------------------------------------
configuration.widgets = [
    WidgetConf(name=_(u"Add new page"),         widgetType=IToolboxWidgetConf, apply=(IContainer,), viewmapper="addpageWidget", id="cms.addpage", sort=100),
    WidgetConf(name=_(u"Edit page"),            widgetType=IToolboxWidgetConf, apply=(IContainer,), viewmapper="editpageWidget", id="cms.editpage", sort=200),
    WidgetConf(name=_(u"Sub pages and parent"), widgetType=IToolboxWidgetConf, apply=(IContainer,), viewmapper="subpagesWidget", id="cms.subpages", sort=300),
    WidgetConf(name=_(u"Settings"),             widgetType=IToolboxWidgetConf, apply=(IApplication,IContainer), viewmapper="settingsWidget", id="cms.settings", sort=400),
    
    WidgetConf(name=_(u"Edit"),          widgetType=IEditorWidgetConf, apply=(IObject,),    viewmapper="edit",   id="editor.edit", sort=100),
    WidgetConf(name=_(u"Add"),           widgetType=IEditorWidgetConf, apply=(IContainer,), viewmapper="add",    id="editor.add",  sort=200),
    WidgetConf(name=_(u"Sort sub pages"),widgetType=IEditorWidgetConf, apply=(IPage,),      viewmapper="sortpages", id="editor.sortpages", sort=300),
    WidgetConf(name=_(u"Meta"),          widgetType=IEditorWidgetConf, apply=(IObject,),    viewmapper="meta",   id="editor.meta", sort=400)
]


        
        
# view implementation ------------------------------------------------------------------
        
from nive.forms import ObjectForm
from nive.views import BaseView

from nive.components.extensions.sort import SortView
from nive.components.extensions.cutcopy import CopyView

from pyramid.response import Response
from pyramid.renderers import get_renderer, render, render_to_response


class Editor(BaseView, CopyView, SortView):

    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        request.editmode = "editmode"

    def cmsIndex_tmpl(self):
        i = get_renderer('nive.cms.cmsview:index.pt').implementation()
        return i
    
    def editorHead(self):
        # necessary includes 
        t = self.cmsIndex_tmpl()
        return t.macros[u'editorHead'](self.request, self.context)
        

    def view(self):
        #if self..Allowed(u"edit", self.context):
        #    vars["cmsview"] = cmsview.CMS(self.context, self.request)
        d = design.Design(self.context, self.request)
        html = d.view(self)
        self.NoCache(self.request.response, user=self.User())
        return html
    
    def editor(self):
        # switch to editor mode
        root = self.context.app.root("editor")
        url = self.FolderUrl(root)
        if not self.context.IsRoot():
            url = url + self.PageUrl(self.context)[len(self.FolderUrl(self.context.GetRoot())):]
        self.Redirect(url)

    
    def exit(self):
        # leave editor mode
        root = self.context.app.root()
        url = self.FolderUrl(root)
        if not self.context.IsRoot():
            url = url + self.PageUrl(self.context)[len(self.FolderUrl(self.context.root())):]
        self.Redirect(url)

    def exitapp(self):
        # leave editor mode
        root = self.context.root()
        url = self.FolderUrl(root)
        self.Redirect(url)
    
    
    # cms editor interface elements -------------------------------------------------
    
    def IsEditmode(self):
        return True
        
    def cmsMain(self, obj, elements=None):
        """
        nive toolbox widget.
        call with obj = current object / page
        """
        if not obj:
            obj = self.context
        return render("widgets/toolbox.pt", {u"obj":obj, u"view":self, u"elements": elements}, request=self.request)

    
    def cmsEditorBlocks(self, obj, elements=None):
        """
        Javascript for interactive elements 
        call with obj = current container / page
        """
        if not obj:
            return u""
        js = u"""<script>$(document).ready(function(){ %(js)s });</script>"""
        #attr = u""" $("#pe%(id)s").attr({ondblclick:"peDblClickElement('%(id)s',event)", onclick:"peClickElement('%(id)s',event)"});\n"""
        attr = u""" $("#pe%(id)s").click(function() { peClickElement('%(id)s',arguments[0] || window.event); });\n"""
        insert = u""" $("#edit%(id)s").prependTo("#pe%(id)s");\n"""
        insertPage = u""" $("#edit%(id)s").prependTo("#pe%(id)s");\n"""
        newjs = StringIO()
        html = StringIO()
        
        if not elements:
            elements = obj.GetPageElements()
        
        for el in elements:
            if el.GetTypeID()=='box':
                html.write(self.editBlockElement(obj=el))
                newjs.write(insert % {u"id": unicode(el.GetID())})
                newjs.write(attr % {u"id": unicode(el.GetID())})
                for elb in el.GetPageElements():
                    html.write(self.editBlockElement(obj=elb))
                    newjs.write(insert % {u"id": unicode(elb.GetID())})
                    newjs.write(attr % {u"id": unicode(elb.GetID())})
        
            else:
                html.write(self.editBlockElement(obj=el))
                newjs.write(insert % {u"id": unicode(el.GetID())})
                newjs.write(attr % {u"id": unicode(el.GetID())})
        
        html.write(js % {u"js": newjs.getvalue()})
        return html.getvalue()


    def editBlockPage(self, page=None):
        """
        Edit bar for page main content area or columns
        if page is None current context is used
        """
        if not page:
            page=self.context
        return render("widgets/editblock_page.pt", {u"obj":page, u"view":self}, request=self.request)

    
    def editBlockElement(self, obj=None):
        """
        Edit bar for elements
        if obj is None current context is used
        """
        if not obj:
            obj=self.context
        return render("widgets/editblock_element.pt", {u"obj":obj, u"view":self}, request=self.request)


    def editBlockColumn(self, page=None, column=None, name=None):
        """
        Edit bar for columns
        if column is None current context is used
        """
        if not column:
            column=self.context
            if not IColumn.providedBy(column):
                column = None
        if page == None and name == None and column != None:
            name = column.meta.get("title")
            page = column.GetPage()
        return render("widgets/editblock_column.pt", 
                      {u"column":column, u"page": page, u"name": name, u"view":self}, 
                      request=self.request)

    
    def editBlockList(self, obj=None, page=None, showCCP=False):
        """
        Edit bar used in lists
        call with obj = current object / page
        """
        if not obj:
            obj=self.context
        if not page:
            page = obj.GetPage()
            elementContainer = obj.GetElementContainer()
        else:
            elementContainer = page
        return render("widgets/editblock_list.pt", 
                      {u"obj":obj, u"page": page, u"elementContainer": elementContainer, u"view":self, u"showCCP":showCCP}, 
                      request=self.request)

    
    def elementAddWidget(self, obj=None, addResponse=True):
        """
        Widget with links to add elements as subobjects of obj
        call with obj = current object / element
        """
        if not obj:
            obj=self.context
        if addResponse:
            return render_to_response("widgets/element_add_list.pt", {"obj":obj, "view":self}, request=self.request)
        return render("widgets/element_add_list.pt", {u"obj":obj, u"view":self}, request=self.request)


    def elementListWidget(self, obj=None, elements=None, addResponse=True):
        """
        Widget with existing elements list and edit options
        call with obj = current object / page
        """
        #i18n?
        if not obj:
            obj=self.context
        html = u"""<div>
  <h4 onclick="peToggleBlock('elements%(id)s',event)">%(title)s</h4>
  %(blocks)s
</div>
        """
        
        elHtml = u"""<div class="element">
  <div class="el_title">%(title)s</div>
  <div class="el_options">%(options)s</div>
  <br style="clear:both"/>
</div>"""
        
        if not elements:
            elements = obj.GetPageElements()
            
        localizer = get_localizer(self.request)
        
        blocks = StringIO()
        static = self.StaticUrl("nive.cms.cmsview:static/images/types/")
        for el in elements:
        
            t = el.GetTitle()
            if not t:
                t = u"<em>%s</em>" % (localizer.translate(el.GetTypeName()))

            if el.GetTypeID()=="box":
                title = u"<img src='%s%s.png' align='top'/> %s: %s" % (static, el.GetTypeID(), localizer.translate(u"Box"), t)
                blocks.write(elHtml % {u"title": title, u"options": self.editBlockList(obj=el, showCCP=True)})
                for elb in el.GetPageElements():
                    t = elb.GetTitle()
                    if not t:
                        t = u"<em>%s</em>" % (localizer.translate(elb.GetTypeName()))
                    title = u"&gt; <img src='%s%s.png' align='top'/> %s" % (static, elb.GetTypeID(), t)
                    blocks.write(elHtml % {u"title": title, u"options": self.editBlockList(obj=elb, showCCP=True)})
        
            else:
                title = u"<img src='%s%s.png' align='top'/> %s" % (static, el.GetTypeID(), t)
                blocks.write(elHtml % {u"title": title, u"options": self.editBlockList(obj=el, showCCP=True)})
        if not len(elements):
            blocks.write(localizer.translate(_(u"<i>empty</i>")))
        data = html % {u"blocks": blocks.getvalue(), u"id": str(obj.GetID()), u"title": localizer.translate(_(u"Page elements"))}
        if addResponse:
            r = Response(content_type="text/html", conditional_response=True)
            r.unicode_body = data
            return r
        return data
        

    def pageListWidget(self, page=None, pages=None):
        """
        Widget with existing pages list and edit options
        call with page = current page
        """
        if not page:
            page=self.context
        html = u"""<div class="subpages"> %(blocks)s </div>"""
        
        pHtml = u"""<div class="element">
  <div class="el_title">%(workflow)s<a href="%(url)s">%(title)s </a> </div>
  <div class="el_options">%(options)s</div>
  <br style="clear:both"/>
</div>"""
        
        useworkflow = 1
        localizer = get_localizer(self.request)
        static = self.StaticUrl("nive.cms.workflow:static/exclamation.png")

        if not pages:
            pages = page.GetPages(includeMenu=1)
        localizer = get_localizer(self.request) 
        blocks = StringIO()
        for p in pages:
            wf = u""
            if useworkflow and not p.meta.pool_state:
                wf = u"""<a href="%(url)sworkflow" class="right" rel="niveOverlay"><img src="%(static)s" title="%(name)s"/></a>""" % {u"static": static, u"url": self.FolderUrl(p), u"name": localizer.translate(_(u"This page is not public."))}
            blocks.write(pHtml % {u"url": self.FolderUrl(p), u"title": p.meta.get(u"title"), u"options": self.editBlockList(obj=p, page=page), u"workflow": wf})
        if not len(pages):
            blocks.write(localizer.translate(_(u"<p><i>no sub pages</i></p>")))
        return html % {u"blocks": blocks.getvalue()}
        

    def breadcrumbs(self, addHome=0, link=True):
        """
        """
        base = self.context #.GetPage()
        parents = base.GetParents()
        parents.reverse()
        if not addHome:
            parents = parents[1:]
        if len(parents)==0:
            return u""
        html = StringIO()
        for page in parents:
            if not link:
                html.write(u"""<span>%s</span> &gt; """ % (page.GetTitle()))
            else:
                html.write(u"""<a href="%s" class="nivecms">%s</a> &gt; """ % (self.PageUrl(page), page.GetTitle()))
        if not link:
            html.write(u"""<span>%s</span>""" % (base.GetTitle()))
        else:
            html.write(u"""<a href="%s" class="nivecms">%s</a>""" % (self.PageUrl(base), base.GetTitle()))
        return html.getvalue()
    
    
    def insertPageWidgets(self):
        return self.insertToolboxWidgets(self.context.GetPage())
        
    def insertAppWidgets(self):
        return self.insertToolboxWidgets(self.context.app)

    def insertToolboxWidgets(self, object):
        app = self.context.app
        widgets = app.QueryConf(IToolboxWidgetConf, context=object)
        html = u""
        if not widgets:
            return html
        l = []
        #opt
        for n,w in widgets:
            l.append({u"id":w.sort, u"data": self.RenderView(object, name=w.viewmapper, secure=True, raiseUnauthorized=False)})
        for i in sorted(l, key=itemgetter(u"id")):
            if i[u"data"]:
                html += i[u"data"]
        return html

    def getEditorWidgets(self, object):
        app = self.context.app
        widgets = app.QueryConf(IEditorWidgetConf, context=object)
        confs = []
        if not widgets:
            return confs
        #opt
        for n,w in widgets:
            confs.append(w)
        return sorted(confs, key=itemgetter(u"sort"))
        

    #class Edit(Editor):
    def edit(self):
        form = ObjectForm(view=self, loadFromType=self.context.configuration)
        form.use_ajax = True
        form.Setup(subset="edit")
        head = form.HTMLHead()
        result, data, action = form.Process(defaultAction="defaultEdit", redirect_success="page_url")
        return {u"content": data, u"result": result, u"cmsview":self, u"head": head}

    def delfile(self):
        file = self.GetFormValue(u"fid")
        try:
            r=self.context.DeleteFile(file, self.User())
            if not r:
                m=_(u"Delete failed")
            else:
                m=_(u"OK")
        except Exception, e:
            m=str(e)
        r = Response(content_type="text/html", conditional_response=True)
        r.text = """<span>%(msg)s</span>""" % {"name": str(file), "msg":m}
        return r

    def meta(self):
        return {}


    #class EditContainer(Editor, SortView):
    def add(self):
        typeID = self.GetFormValue("pool_type")
        if not typeID:
            return {u"content": u"", u"showAddLinks": True, u"result": True, u"head": u""}
        form = ObjectForm(view=self, loadFromType=typeID)
        form.Setup(subset="create", addTypeField=True)
        form.use_ajax = True
        head = form.HTMLHead()
        result, data, action = form.Process(defaultAction="default", redirect_success="page_url")
        return {u"content": data, u"result": result, u"cmsview": self, u"showAddLinks": False, u"head": head}

    
    def delete(self):
        id = self.GetFormValue(u"id")
        result = {u"msgs": [], u"objToDelete": None, u"content":u"", u"cmsview": self, u"result": False}
        if not id:
            result[u"msgs"] = [_(u"Nothing to delete")]
            return result
        delete = self.GetFormValue(u"delete")
        obj = self.context.obj(id)
        if not obj:
            result[u"msgs"] = [_(u"Object not found")]
            return result
        if obj.IsContainer() and delete != u"1":
            result[u"objToDelete"] = obj
            return result
        result[u"result"] = self.context.Delete(id, user=self.User(), obj=obj)
        return result
    

    # widgets -------------------------------------------------------------------

    def selectType(self):
        user = self.User()
        lt = self.context.GetAllowedTypes(user)
        tmpl = u"""<a href="add?pool_type=%s" rel="niveOverlay" class="nivecms addlink">%s</a> """
        html = StringIO()
        html.write(u"""<div class="addElements">""")
        #opt
        for t in lt:
            html.write(tmpl % (t[u"id"], _(t[u"name"])))
        html.write(u"</div>")
        return html.getvalue()
    
    def selectPageElement(self):
        user = self.User()
        lt = self.context.GetAllowedTypes(user)
        tmpl = u"""<a href="add?pool_type=%s" rel="niveOverlay" class="nivecms addlink">%s</a> """
        html = StringIO()
        html.write(u"""<div class="addElements">""")
        #opt
        for t in lt:
            html.write(tmpl % (t[u"id"], _(t[u"name"])))
        html.write(u"</div>")
        return html.getvalue()
    

        