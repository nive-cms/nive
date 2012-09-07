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

import string

from nive.utils.utils import ConvertToNumberList
from nive.definitions import *
from nive.security import *


class ObjectFulltext:
    """    Fulltext support for objects. Automatically updates fulltext on commit. """
    
    def Init(self):
        self.RegisterEvent("commit", "UpdateFulltext")
        

    # Fulltext ------------------------------------------

    def UpdateFulltext(self):
        """
        Update fulltext for entry. Text is generated automatically.
        """
        root = self.GetRoot()
        if not root.app.configuration.fulltextIndex:
            return
        # loop all fulltext fields and make one string
        text = ""
        for f in self.app.GetAllMetaFlds(ignoreSystem=False):
            if f.get("fulltext") != True:
                continue
            #print inUnit.GetID(),f
            if f["datatype"]=="unit":
                id = self.meta.get(f["id"])
                t = root.LookupObjTitle(id)
                text += u" %s\r\n\r\n" % (t)
            elif f["datatype"]=="unitlist":
                ids = ConvertToNumberList(self.meta.get(f["id"]))
                for id in ids:
                    t = root.LookupObjTitle(id)
                    text += u" %s\r\n\r\n" % (t)
            else:
                text += u" %s\r\n\r\n" % (self.meta.get(f["id"],u""))

        # data
        for f in self.configuration.data:
            if f.get("fulltext") != True:
                continue
            if f["datatype"]=="unit":
                id = self.data.get(f["id"])
                t = root.LookupObjTitle(id)
                text += u" %s\r\n\r\n" % (t)
            elif f["datatype"]=="unitlist":
                ids = ConvertToNumberList(self.data.get(f["id"]))
                for id in ids:
                    t = root.LookupObjTitle(id)
                    text += u" %s\r\n\r\n" % (t)
            else:
                text += u" %s\r\n\r\n" % (self.data.get(f["id"]))
        # update text in fulltext table
        self.dbEntry.WriteFulltext(text)


    def GetFulltext(self):
        """
        Get current fulltext value
        """
        root = self.GetRoot()
        if not root.app.configuration.fulltextIndex:
            return u""
        return self.dbEntry.GetFulltext()

    
    def DeleteFulltext(self):
        """
        Delete fulltext
        """
        root = self.GetRoot()
        if not root.app.configuration.fulltextIndex:
            return
        self.dbEntry.DeleteFulltext()

