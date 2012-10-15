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

import hashlib
from datetime import datetime

from nive.i18n import _
from nive.definitions import implements, IUser

from nive.components.objects.base import ObjectBase



def Sha(password):
    return hashlib.sha224(password).hexdigest()


class user(ObjectBase):
    """
    User object with groups and login possibility. 
    """
    implements(IUser)
    
    def __str__(self):
        return self.data.get("name",str(self.id))

    def Init(self):
        self.groups = tuple(self.data.get("groups",()))
        self.RegisterEvent("commit", "HashPassword")
        self.RegisterEvent("commit", "OnCommit")


    def HashPassword(self):
        if not self.data.HasTempKey("password"):
            return
        pw = Sha(self.data.password)
        self.data["password"] = pw


    def Authenticate(self, password):
        return Sha(password) == self.data["password"]

    
    def Login(self):
        """
        events: login()
        """
        lastlogin = self.data.get("lastlogin")
        date = datetime.now()
        self.data.set("lastlogin", date)
        self.Signal("login")
        self.Commit(self)
        self.AddToCache()


    def Logout(self):
        """
        events: logout()
        """
        self.Signal("logout")
        self.Commit(self)
        self.RemoveFromCache()


    def SecureUpdate(self, data, user):
        """
        Update existing user data.
        name, groups, pool_state cannot be changed
        """
        if data.has_key("name"):
            del data["name"]
        if data.has_key("groups"):
            del data["groups"]
        if data.has_key("pool_state"):
            del data["pool_state"]

        if not self.Update(data, user):
            return False, [_(u"Update failed.")]
        
        self.Commit(user)
        self.RemoveFromCache()
        return True, []


    def UpdateGroups(self, groups):
        """
        update groups of user
        """
        self.groups = tuple(groups)
        self.data["groups"] = groups
        self.RemoveFromCache()
        return True


    def AddGroup(self, group, user):
        """
        add user to this group
        """
        if group in self.groups:
            return True
        g = list(self.groups)
        g.append(group)
        self.groups = tuple(g)
        self.data["groups"] = g
        self.Commit(user)
        self.RemoveFromCache()
        return True


    def GetGroups(self, context=None):
        """
        groups
        """
        return self.groups


    def InGroups(self, groups):
        """
        check if user has one of these groups
        """
        if isinstance(groups, basestring):
            return groups in self.groups
        for g in groups:
            if g in self.groups:
                return True
        return False
    
    # System ------------------------------------------------

    def TitleFromName(self, surname, lastname, name):
        title = surname + u" " + lastname
        if title.replace(u" ",u"")==u"":
            title = name
        return title


    def OnCommit(self):
        title = self.TitleFromName(self.data["surname"], self.data["lastname"], self.data["name"])
        self.meta["title"] = title
        self.RemoveFromCache()


    def AddToCache(self):
        self.GetParent().Cache(self, self.id)

    def RemoveFromCache(self):
        self.GetParent().RemoveCache(self.id)



# user definition ------------------------------------------------------------------
from nive.definitions import StagUser, ObjectConf, FieldConf
#@nive_module
configuration = ObjectConf(
    id = "user",
    name = _(u"User"),
    dbparam = "users",
    context = "nive.userdb.user.user",
    template = "user.pt",
    selectTag = StagUser,
    container = False,
    description = __doc__
)

configuration.data = (
    FieldConf(id="name",     datatype="string",      size= 30, default=u"", required=1, name=_(u"User ID"), description=u""),
    FieldConf(id="password", datatype="password",    size= 30, default=u"", required=1, name=_(u"Password"), description=u""),
    FieldConf(id="email",    datatype="email",       size=255, default=u"", required=1, name=_(u"Email"), description=u""),
    FieldConf(id="groups",   datatype="mcheckboxes", size=255, default=u"", name=_(u"Groups"), settings={"codelist":"groups"}, description=u""),
    
    FieldConf(id="notify",   datatype="bool",        size= 4,  default=True, name=_(u"Activate email notifications"), description=u""),
    
    FieldConf(id="surname",  datatype="string",      size= 30, default=u"", name=_(u"Surname"), description=u""),
    FieldConf(id="lastname", datatype="string",      size= 30, default=u"", name=_(u"Lastname"), description=u""),
    FieldConf(id="organisation", datatype="string",  size=255, default=u"", name=_(u"Organisation"), description=u""),
    
    FieldConf(id="lastlogin", datatype="datetime", size=0, readonly=True, default=u"", name=_(u"Last login"), description=u""),
    
)

#password2 = FieldConf(id="password2", datatype="password", size= 30, default="", required=1, name="Passwort - Wiederholung", description="")
configuration.forms = {
    "create": {"fields": ["name", "password", "email", "surname", "lastname"]},
    "edit":   {"fields": ["password", "email", "surname", "lastname"]},
}
