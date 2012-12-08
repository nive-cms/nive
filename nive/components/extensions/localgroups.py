#----------------------------------------------------------------------
# Copyright (C) 2012 Arndt Droullier. All rights reserved.
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
LocalGroups extension module
----------------------------
Security extension to handle local group assginments for users.
Can be used for Roots and Objects or any other python class supporting events
and id attribute (number). Uses idhash for root objects.
"""

from nive.definitions import ModuleConf, Conf
from nive.definitions import implements, ILocalGroups

class LocalGroups(object):
    """
    """
    _owner = u"group:owner"
    implements(ILocalGroups)
    
    def Init(self):
        self._localRoles = {}
        self.RegisterEvent("create", "AddOwner")
        self._secid = self.id or self.idhash
        
    
    def GetLocalGroups(self, username):
        """
        Group assignments use the user name.
        returns a list of all local user groups, including parent settings
        """
        if self.id <= 0:
            return self._LocalGroups(username)
        g = []
        o = self
        while o:
            g += o._LocalGroups(username)
            o = o.GetParent()
        return g 


    def AllLocalGroups(self):
        """
        returns a list of all local user group settings as list including 
        [username, group, id]. This function does not include parent level
        settings.
        """
        return self.db.GetGroups(self._secid)


    def AddOwner(self, user, **kw):
        """
        Add the current user as group:owner to local roles
        """
        if not user or not str(user):
            return
        self.AddLocalGroup(str(user), self._owner)
    
        
    def AddLocalGroup(self, username, group):
        """
        Add a local group assignment for username.
        """
        groups = self._LocalGroups(username)
        if group in groups:
            return 
        if username==None:
            return
        self._AddLocalGroupsCache(username, group)
        self.db.AddGroup(self._secid, userid=username, group=group)

        
    def RemoveLocalGroups(self, username, group=None):
        """
        Remove a local group assignment. If group is None all local groups
        will be removed.
        """
        self._DelLocalGroupsCache(username, group)
        self.db.RemoveGroups(self._secid, userid=username, group=group)


    def _LocalGroups(self, username):
        if username in self._localRoles:
            return list(self._localRoles[username])
        g = [r[1] for r in self.db.GetGroups(self._secid, userid=username)]
        self._localRoles[username] = tuple(g)
        return g
    
    def _AddLocalGroupsCache(self, username, group):
        if username in self._localRoles:
            if group in self._localRoles[username]:
                return
            l = list(self._localRoles[username])
            l.append(group)
            self._localRoles[username] = tuple(l)
            return 
        self._localRoles[username] = (group,)
    
    def _DelLocalGroupsCache(self, username, group=None):
        if not username in self._localRoles:
            return
        if username in self._localRoles and not group:
            del self._localRoles[username]
            return
        if not group in self._localRoles[username]:
            return
        l = list(self._localRoles[username])
        l.remove(group)
        self._localRoles[username] = tuple(l)



def SetupLocalGroups(app, pyramidConfig):
    # get all roots and add extension
    extension = "nive.components.extensions.localgroups.LocalGroups"
    def add(confs):
        for c in confs:
            e = c.extensions
            if e and extension in e:
                continue
            if e == None:
                e = []
            if isinstance(e, tuple):
                e = list(e)
            e.append(extension)
            c.extensions = tuple(e) 
    
    add(app.GetAllRootConfs())
    add(app.GetAllObjectConfs())
    
    
configuration = ModuleConf(
    id = "localGroups",
    name = u"Local Group assignment for objects and roots",
    context = "nive.components.extensions.localgroups",
    events = (Conf(event="startRegistration", callback=SetupLocalGroups),),
)
