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
User and security functions.
"""


from pyramid.security import Allow 
from pyramid.security import Deny
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Everyone, Authenticated
from pyramid.security import remember, forget, authenticated_userid


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
    



class LocalGroups:
    """
    Security extension to handle local group assginments for users.
    Can be used for Roots and Objects or any other python class supporting events
    and id attribute (number).
    """

    def Init(self):
        self._localRoles = {}

    
    def GetLocalGroups(self, userid):
        """
        Group assignments use the unique user id (a number), not the user name.
        returns a list of all local user groups, including parent settings
        """
        if self.id <= 0:
            return self._LocalGroups(userid)
        g = []
        o = self
        while o:
            g += o._LocalGroups(userid)
            o = o.GetParent()
        return g 


    
    def AddLocalGroup(self, userid, group):
        """
        Add a local group assignment for userid.
        """
        groups = self._LocalGroups(userid)
        if group in groups:
            return 
        if userid==None:
            return
        self._AddLocalGroupsCache(userid, group)
        userid=hash(userid)
        self.db.AddGroup(userid=userid, group=group, id=self.id)

        
    def RemoveLocalGroups(self, userid, group=None):
        """
        Remove a local group assignment. If group is None all local groups
        will be removed.
        """
        self._DelLocalGroupsCache(userid, group)
        if userid!=None:
            userid=hash(userid)
        self.db.RemoveGroups(userid=userid, group=group, id=self.id)


    def _LocalGroups(self, userid):
        uhash = hash(userid)
        if str(uhash) in self._localRoles:
            return list(self._localRoles[str(uhash)])
        g = [r[1] for r in self.db.GetGroups(userid=uhash, id=self.id)]
        self._localRoles[str(uhash)] = tuple(g)
        return g
    
    def _AddLocalGroupsCache(self, userid, group):
        uhash = str(hash(userid))
        if uhash in self._localRoles:
            if group in self._localRoles[uhash]:
                return
            l = list(self._localRoles[uhash])
            l.append(group)
            self._localRoles[uhash] = tuple(l)
            return 
        self._localRoles[uhash] = (group,)
    
    def _DelLocalGroupsCache(self, userid, group=None):
        uhash = str(hash(userid))
        if not uhash in self._localRoles:
            return
        if uhash in self._localRoles and not group:
            del self._localRoles[uhash]
            return
        if not group in self._localRoles[uhash]:
            return
        l = list(self._localRoles[uhash])
        l.remove(group)
        self._localRoles[uhash] = tuple(l)

    


        