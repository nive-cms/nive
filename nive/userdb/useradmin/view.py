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

from pyramid.renderers import get_renderer, render, render_to_response

from nive.i18n import _
from nive.definitions import ViewConf, ViewModuleConf, Conf
from nive.definitions import IApplication, IUser


# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf(
    id = "useradmin",
    name = _(u"User management"),
    static = "",
    containment = "nive.userdb.useradmin.adminroot.adminroot",
    context = "nive.userdb.useradmin.adminroot.adminroot",
    view = "nive.userdb.useradmin.view.AdminView",
    templates = "nive.userdb.useradmin:",
    permission = "manage users"
)
t = configuration.templates
configuration.views = [
    # User Management Views
    ViewConf(name = "",       attr = "view",   containment=IApplication, renderer = t+"root.pt"),
    ViewConf(name = "add",    attr = "add",    containment=IApplication, renderer = t+"add.pt"),
    ViewConf(name = "delete", attr = "delete", containment=IApplication, renderer = t+"delete.pt"),
    ViewConf(name = "",       attr = "edit",   context = IUser, renderer = t+"edit.pt"),
]


        
    
# view and form implementation ------------------------------------------------------------------

from nive.views import BaseView, Unauthorized, Mail
from nive.forms import ObjectForm, ValidationError
from nive.userdb.root import UsernameValidator

from nive.adminview.view import AdminBasics
    

class AdminView(AdminBasics):
    
    def index_tmpl(self):
        i = get_renderer("nive.userdb.useradmin:index.pt").implementation()
        return i

    def view(self):
        return {}

    
    def add(self):
        name = self.context.app.GetObjectFld("name", "user").copy()
        name.settings["validator"] = UsernameValidator()
        form = ObjectForm(loadFromType="user", view=self)
        form.subsets = {
            "create": {"fields":  [name, "password", "email", "groups", "surname", "lastname"], 
                       "actions": ["default", "create"]}
        }
        form.Setup(subset="create")
        result, data, action = form.Process(redirect_success="obj_url", pool_type="user")
        return {u"content": data, u"result": result, u"head": form.HTMLHead()}


    def edit(self):
        pwd = self.context.app.GetObjectFld("password", "user").copy()
        pwd.settings["update"] = True
        pwd.required = False
        form = ObjectForm(loadFromType="user", subset="edit", view=self)
        def removepasswd(data, obj):
            try:
                del data["password"]
            except:
                pass
        form.RegisterEvent("loadDataObj", removepasswd)
        form.subsets = {
            "edit":   {"fields":  [pwd, "email", "groups", "surname", "lastname"], 
                       "actions": ["defaultEdit", "edit"]},
        }        
        form.Setup(subset="edit")
        result, data, action = form.Process(defaultAction="defaultEdit")#, redirect_success="obj_url")
        return {u"content": data, u"result": result, u"head": form.HTMLHead()}
            
    
    def delete(self):
        ids = self.GetFormValue("ids")
        confirm = self.GetFormValue("confirm")
        users = []
        msgs = []
        root = self.context.root()
        if isinstance(ids, basestring):
            ids = (ids,)
        elif not ids:
            ids = ()
        for i in ids:
            u = root.GetUserByID(i, activeOnly=0)
            if not u:
                msgs.append(self.Translate(_(u"User not found. (id %(name)s)", mapping={"name": i})))
            else:
                users.append(u)
        result = True
        if confirm:
            for u in users:
                name = u.data.name
                if not root.Delete(id=u.id, obj=u, user=self.User()):
                    result = False
                    msgs.append(self.Translate(_(u"Delete failed: User '%(name)s'", mapping={"name": u.meta.title})))
                root.RemoveCache(name)
            users=()
            if result:
                if len(ids)>1:
                    msgs.append(self.Translate(_(u"OK. Users deleted.")))
                else:
                    msgs.append(self.Translate(_(u"OK. User deleted.")))
            return self.Redirect(self.Url(root), msgs)
        return {"ids": ids, "users":users, "result": result, "msgs": msgs, "confirm": confirm} 
    







