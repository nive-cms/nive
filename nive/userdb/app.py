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
configuration.loginByEmail = False

# configuration.systemAdmin = (u"email", u"display name")
# configuration.admin = {"name": "admin", "password": "adminpass", "email": "admin@domain.com"}

configuration.modules = [
    "nive.userdb.root", 
    "nive.userdb.user", 
    # session user cache
    "nive.components.extensions.sessionuser",
    # user administration
    "nive.userdb.useradmin", 
    # tools
    "nive.components.tools.dbStructureUpdater", 
    # administration and persistence
    "nive.adminview",
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


        
    def Groupfinder(self, userid, request=None, context=None):
        """
        returns the list of groups assigned to the user 
        """
        if request:
            try:
                user = request.environ["authenticated_user"]
            except:
                user = self.root().GetUser(userid)
                request.environ["authenticated_user"] = user
                def remove_user(request):
                    if "authenticated_user" in request.environ:
                        del request.environ["authenticated_user"]
                request.add_finish_callback(remove_user)
        else:
                user = self.root().GetUser(userid)
        if not user:
            return None

        # users groups or empty list
        groups = user.groups or ()

        # lookup context for local roles
        if not context and hasattr(request, "context"):
            context = request.context
        if context and ILocalGroups.providedBy(context):
            local = context.GetLocalGroups(userid, user=user)
            if not groups:
                return local
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
        #request.authenticate




    def AuthenticatedUser(self, request):
        # bw 0.9.6. removed in next version.
        name = self.UserName(request)
        return self.GetRoot().GetUserByName(name)

    def AuthenticatedUserName(self, request):
        # bw 0.9.6. removed in next version.
        return authenticated_userid(request)    

