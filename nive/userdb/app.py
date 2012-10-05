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
nive user database 
--------------------

You can specify a admin user on configuration level as `admin`. The admin user works without 
database connection.

The system admin for notification mails can be specified as `systemAdmin`.
::

    configuration.admin = {"name": "admin", "password": "adminpass", "email": "admin@domain.com"}
    configuration.systemAdmin = (u"email", u"display name")

"""

from nive.definitions import implements, AppConf, FieldConf, GroupConf, IUserDatabase, ILocalGroups
from nive.security import Allow, Deny, Everyone, ALL_PERMISSIONS, remember, forget
from nive.components.objects.base import ApplicationBase
from nive.i18n import _

#@nive_module
configuration = AppConf()
configuration.id = "userdb"
configuration.title = _(u"Users")
configuration.context = "nive.userdb.app.UserDB"
#configuration.systemAdmin = (u"email", u"display name")
#configuration.admin = {"name": "admin", "password": "adminpass", "email": "admin@domain.com"}
configuration.loginByEmail = False

configuration.modules = [
    "nive.userdb.root", "nive.userdb.user", 
    # user administration
    "nive.userdb.useradmin.adminroot", 
    # tools
    "nive.components.tools.dbStructureUpdater", 
    # administration and persistence
    "nive.adminview.view",
    #"nive.components.extensions.persistence.dbPersistenceConfiguration"
]

configuration.acl= [
    (Allow, Everyone, 'view'),
    (Allow, Everyone, 'updateuser'),
    (Allow, "group:useradmin", 'signup'), 
    (Allow, "group:useradmin", 'manage users'),
    (Allow, "group:admin", ALL_PERMISSIONS),
]

configuration.groups = [ 
    GroupConf(id="group:useradmin", name="group:useradmin"),
]


class UserDB(ApplicationBase):
    """
    """
    implements(IUserDatabase)


    def AuthenticatedUser(self, request):
        """
        returns the currently in request authenticated user object or none
        """
        name = self.UserName(request)
        return self.GetRoot().GetUserByName(name)


    def AuthenticatedUserName(self, request):
        """
        returns the currently in request authenticated user name as logged in
        """
        return authenticated_userid(request)    


    # pyramid specific -------------------------------------------------------------------
        
    def Groupfinder(self, userid, request):
        """
        returns the list of groups assigned to the user 
        """
        groups = self.GetRoot().GetUserGroups(userid)
        if hasattr(request, "context"):
            ctx = request.context
            if ctx and ILocalGroups.providedBy(ctx):
                local = ctx.GetLocalGroups(userid)
                return tuple(list(groups)+list(local))
        return groups


    def RememberLogin(self, request, user):
        """
        add login info to cookies or session. 
        """
        if not hasattr(request.response, "headerlist"):
            request.response.headerlist = []
        headers = remember(request, user)
        request.response.headerlist += list(headers)


    def ForgetLogin(self, request, url=None):
        """
        removes login info from cookies and session
        """
        if not hasattr(request.response, "headerlist"):
            setattr(request.response, "headerlist", [])
        headers = forget(request)
        request.response.headerlist += list(headers)
