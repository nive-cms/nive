#----------------------------------------------------------------------
# Nive cms
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
from types import StringType, UnicodeType, IntType, LongType

from nive.definitions import StagPage, StagPageElement

        
class AlternatePath:
    """
    Enables readable url path names instead of ids for object traversal.
    Names are stored as meta.pool_filename and generated from
    title by default. Automatic generation can be disabled by setting
    *meta.customfilename* to False for each object 
    """
    
    def Init(self):
        if self.id == 0:
            return
        self.RegisterEvent("commit", "TitleToFilename")
        self._SetName()

    
    def TitleToFilename(self, **kw):
        """
        Uses title for filename
        """
        customfilename = self.data.get("customfilename",False)
        if customfilename:
            return
        filename = self.EscapeFilename(self.meta["title"], self.meta["pool_filename"])
        if filename:
            self.meta["pool_filename"] = filename
            self._SetName()
        
        
    def UniqueFilename(self, name):    
        """
        Converts name to valid path/url
        """
        cnt = 1
        root = self.root()
        if name == u"file":
            name = u"file_"
        while root.FilenameToID(name, self.GetParent().id, parameter={u"id":self.id}, operators={u"id":u"!="}) != 0:
            if cnt>1:
                name = name[:-1]+str(cnt)
            else:
                name = name+str(cnt)
            cnt += 1
        return name


    def EscapeFilename(self, path, currentPath):
        """
        Converts name to valid path/url
        """
        path = path.lower()
        path = path.encode("iso-8859-1")
        path = path.replace(".","_")
        if path == currentPath:
            return None
        plen = 50
        if len(path) <= 55:
            plen = 55
        p = ""
        for c in path[:plen]:
            o = ord(c)
            if c == ".":
                p+="."
                continue    
            # space
            if c == " ":
                p += "_"
                continue
            
            # umlaute
            if o in (196, 228):
                p += "ae"
                continue
            if o in (214, 246):
                p += "oe"
                continue
            if o in (220, 252):
                p += "ue"
                continue
            if o == 223:
                p += "ss"
                continue
            
            # ascii
            if o == 95 or 47 < o < 58 or 96 < o < 123:
                p += chr(o)
        
        if p[-1] == "_":
            p = p[:-1]
        
        while len(p) and p[0] == "_":
            p = p[1:]
        
        p = self.StrAscii(p)

        if path.find(".")!=-1 and len(path) > 55:
            ext = path.split(".")
            if len(ext) >= 2:
                p = p + "." + ext[-1]
        
        p = unicode(p)
        return self.UniqueFilename(p)

    
    def StrAscii(self, s):
        return filter(lambda x: x in string.ascii_lowercase+"0123456789_.", s.lower())


    # system functions -----------------------------------------------------------------
    
    def __getitem__(self, id):
        if id == u"file":
            raise KeyError, id
        id = id.split(u".")
        if len(id)>2:
            id = (u".").join(id[:-1])
        else:
            id = id[0]
        try:
            id = long(id)
        except:
            name = id
            id = 0
            if name:
                id = self.root().FilenameToID(name, self.id)
            if not id:
                raise KeyError, id
        o = self.GetObj(id)
        if o:
            return o
        raise KeyError, id

    def _SetName(self):
        self.__name__ = self.meta["pool_filename"]
        if not self.__name__:
            self.__name__ = str(self.id)

    