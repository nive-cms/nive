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
User and security functions.
"""


from pyramid.security import Allow 
from pyramid.security import Deny
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Everyone, Authenticated
from pyramid.security import remember, forget, authenticated_userid

from nive.definitions import ModuleConf, Conf
from nive.definitions import Interface, implements


def GetUsers(app):
    """
    Loads all users from user database if available.
    """
    portal = app.portal
    try:
        userdb = portal.userdb
        return userdb.root().GetUsers()
    except:
        return []

    
class User(object):
    """
    A fake user object for testing.
    """
    def __str__(self):
        return self.name
    
    def __init__(self, name, id=0):
        self.name = name
        self.id = id
        self.groups = []
        
    def GetGroups(self, context=None):
        return self.groups
    



class Unauthorized(Exception):
    """
    failed login
    """

class UserFound(Exception):
    """
    Can be used in *getuser* listeners to break user lookup and
    pass a session user to LookupUser. The second argument is the session
    user 
    """
    def __init__(self, user):
        self.user = user



class IAdminUser(Interface):
    """
    Used for admin user instance hard coded in configration 
    """


class AdminUser(object):
    """
    Admin User object with groups and login possibility. 
    """
    implements(IAdminUser)
    
    def __init__(self, values, ident):
        self.id = 0
        self.data = Conf(**values)
        self.meta = Conf()
        self.identity = ident or str(self.id)
        self.groups = self.data.groups = (u"group:admin",)

    def __str__(self):
        return str(self.identity)

    def Authenticate(self, password):
        return password == self.data["password"]
    
    def Login(self):
        """ """

    def Logout(self):
        """ """

    def GetGroups(self, context=None):
        """ """
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
    
    def ReadableName(self):
        return self.data.name
    

        