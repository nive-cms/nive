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
LocalGroups extension module
----------------------------
Security extension to handle local group assginments for users.
Can be used for Roots and Objects or any other python class supporting events
and id attribute (number). Uses idhash for root objects.
"""

from nive import ModuleConf, Conf


class LocalGroups:
    """
    """
    _owner = u"group:owner"
    
    def Init(self):
        self._localRoles = {}
        self.RegisterEvent("create", self.AddOwner)
        self._secid = self.id or self.idhash
        

    
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


    def AddOwner(self, user, **kw):
        """
        Add the current user as group:owner to local roles
        """
        if not user or not str(user):
            return
        self.AddLocalGroup(str(user), self._owner)
    
        
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
        self.db.AddGroup(self._secid, userid=userid, group=group)

        
    def RemoveLocalGroups(self, userid, group=None):
        """
        Remove a local group assignment. If group is None all local groups
        will be removed.
        """
        self._DelLocalGroupsCache(userid, group)
        if userid!=None:
            userid=hash(userid)
        self.db.RemoveGroups(self._secid, userid=userid, group=group)


    def _LocalGroups(self, userid):
        uhash = hash(userid)
        if str(uhash) in self._localRoles:
            return list(self._localRoles[str(uhash)])
        g = [r[1] for r in self.db.GetGroups(self._secid, userid=uhash)]
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



def SetupLocalGroups(app, pyramidConfig):
    # get all roots and add extension
    extension = "nive.components.extensions.localgroups.LocalGroups"
    def add(confs):
        for c in confs:
            e = c.extensions
            if e == None:
                e = []
            if extension in e:
                continue
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
