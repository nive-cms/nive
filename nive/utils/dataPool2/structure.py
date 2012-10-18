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

import json
from datetime import datetime

from nive.utils.utils import ConvertToDateTime
from nive.utils.dataPool2.files import File


# Database records wrapper ---------------------------------------------------------------------------

class Wrapper(object):
    """
    Wrappers are mapping objects for data, files and meta. Content can be accessed as
    dictionary field.
    Changes are stored temporarily in memory.
    """

    __wrapper__ = 1
    meta = False
    
    def __init__(self, entry, content=None):
        self._entry_ = entry
        self._temp_ = {}
        self._content_ = None
        
    def __repr__(self):
        return str(type(self)) 
    
    def __dir__(self):
        return ["_temp_", "_content_", "_entry_"]
    
    def __setitem__(self, key, value):
        if key in (u"id",u"pool_datatbl", u"pool_dataref"):
            return
        self._temp_[key] = self._entry_().DeserializeValue(key, value, self.meta)

    def __getitem__(self, key):
        if self._temp_.has_key(key):
            return self._temp_[key]
        if not self._content_:
            self._Load()
        return self._content_.get(key)


    def __getattr__(self, key):
        if key in self.__dict__.keys():
            return self.__dict__[key]
        if self._temp_.has_key(key):
            return self._temp_[key]
        if not self._content_:
            self._Load()
        return self._content_.get(key)


    def close(self):
        self._entry_ = None
        self._temp_.clear()
        self._content_ = None


    def clear(self):
        """
        Reset contents, temp data and entry obj
        """
        self._temp_.clear()


    def copy(self):
        """
        Returns a copy of current content
        """
        if not self._content_:
            self._Load()
        c = self._content_.copy()
        c.update(self._temp_)
        return c


    def has_key(self, key):
        if self.HasTempKey(key):
            return True
        return key in self.keys()


    def get(self, key, default=None):
        try:
            data = self[key]
            if data == None:
                return default
            return data
        except:
            return default


    def set(self, key, data):
        self[key] = data


    def update(self, dict, force = False):
        dict = self._entry_().DeserializeValue(None, dict, self.meta)
        if force:
            for k in dict.keys():
                data = dict[k]
                if isinstance(data, bytes):
                    dict[k] = self._entry_().pool.DecodeText(data)
            self._temp_.update(dict)
            return
        for k in dict.keys():
            self[k] = dict[k]


    def keys(self):
        if not self._content_:
            self._Load()
        t = self._content_.keys()
        t += self._temp_.keys()
        return t



    def IsEmpty(self):                return self._content_ == None
    def GetTemp(self):                return self._temp_
    def HasTemp(self):                return self._temp_ != {}
    def GetTempKey(self, key):        return self._temp_.get(key)
    def HasTempKey(self, key):        return self._temp_.has_key(key)

    def GetEntry(self):                return self._entry_()

    def SetContent(self, content):
        if not self._content_:
            self._content_ = content
        else:
            self._content_.update(content)

    def EmptyTemp(self):
        self._temp_.clear()

    def _Load(self):
        self._content_ = {}
        pass


class MetaWrapper(Wrapper):
    """
    wrapper class for meta content
    """
    meta = True
    
    def _Load(self):
        self._content_ = {}
        self._entry_()._PreloadMeta()



class DataWrapper(Wrapper):
    """
    wrapper class for data content
    """

    def _Load(self):
        self._content_ = {}
        self._entry_()._PreloadData()


class FileWrapper(Wrapper):
    """
    wrapperclass for files. contains only filemta and returns file streams on read.
    update and __setitem__ take File object with o.file and o.filename attr as parameter
    entry = {"filename": "", "path": <absolute path for temp files>, "file": <file stream>}
    """

    def __setitem__(self, key, filedata):
        """
        filedata can be a dictionary, File object or file path
        """
        if not filedata:
            if key in self._temp_:
                del self._temp_[key]
            elif self._content_ and key in self._content_:
                del self._content_[key]
            return
        if isinstance(filedata, dict):
            file = File(key, filedict=filedata, fileentry=self._entry_())
            filedata = file
        elif isinstance(filedata, bytes):
            # load from temp path
            file = File(key, fileentry=self._entry_())
            file.fromPath(filedata)
            filedata = file
        filedata.tempfile = True
        self._temp_[key] = filedata


    def set(self, key, filedata):
        self[key] = filedata


    def SetContent(self, files):
        self._content_ = {}
        if isinstance(files, dict):
            for f in files:
                self._content_[f] = files[f]
            return
        for f in files:
            self._content_[f["filekey"]] = f


    def _Load(self):
        files = self._entry_().Files()
        self._content_ = {}
        for f in files:
            self._content_[f["filekey"]] = f
        return self._content_.keys()


#  Pool Structure ---------------------------------------------------------------------------

StdMetaFlds = (u"id", u"pool_dataref", u"pool_datatbl")


class PoolStructure(object):
    """
    Data Pool 2 Structure handling. Defines a table field mapping. If field types are available serializing 
    and deserializing is performed on database reads and writes.

    ::
    
        structure =
            {
             meta:   (field1, field2, ...),
             type1_table: (field5, field6, ...),
             type2_table: (field8, field9, ...),
            }

        fieldtypes = 
            {
             meta: {field1: string, field2: number},
             type1_table: {field5: DateTime, field6: text},
             type2_table: {field8: DateTime, field9: text},
            }
            
        stdMeta = (field1, field2)

    De-Serialization datatypes ::
    
        string, htext, text, list, code, radio, email, password, url -> unicode
        number, float, unit -> number 
        bool -> 0/1
        file -> bytes
        date, datetime, timestamp -> datetime
        mselection, mcheckboxes, urllist -> string tuple
        unitlist -> number tuple
        json -> python type list, tuple or dict

    """
    MetaTable = u"pool_meta"
    
    def __init__(self, structure=None, fieldtypes=None, stdMeta=None, **kw):
        #
        self.stdMeta = ()
        self.structure = {}
        self.fieldtypes = {}
        if structure:
            self.Init(structure, fieldtypes, stdMeta, **kw)
        

    def Init(self, structure, fieldtypes=None, stdMeta=None, codepage="utf-8", **kw):
        s = structure.copy()
        self.codepage = codepage
        meta = list(s[self.MetaTable])
        # add default fields
        if not u"pool_dataref" in s[self.MetaTable]:
            meta.append(u"pool_dataref")
        if not u"pool_datatbl" in s[self.MetaTable]:
            meta.append(u"pool_datatbl")
        s[self.MetaTable] = tuple(meta)
        for k in s:
            s[k] = tuple(s[k])
        self.structure = s
        
        if fieldtypes:
            self.fieldtypes = fieldtypes
        
        if stdMeta:
            m = list(stdMeta)
            for f in StdMetaFlds:
                if not f in m:
                    m.append(f)
            self.stdMeta = tuple(m)


    def IsEmpty(self):
        return self.structure=={}

    
    def __getitem__(self, key, version=None):
        return self.structure[key]

    def get(self, key, default=None, version=None):
        return self.structure.get(key, default)

    def has_key(self, key, version=None):
        return self.structure.has_key(key)

    def keys(self, version=None):
        return self.structure.keys()
    
    
    def serialize(self, table, field, value):
        # if field==None and value is a dictionary multiple values are deserialized
        if field==None and isinstance(value, dict):
            for field, v in value.items():
                try:        t = self.fieldtypes[table][field]
                except:     t = None
                value[field] = self._se(v, t)
        else:
            try:        t = self.fieldtypes[table][field]
            except:     t = None
            value = self._se(value, t)
        return value
        

    def deserialize(self, table, field, value):
        # if field==None and value is a dictionary multiple values are deserialized
        if field==None and isinstance(value, dict):
            for field, v in value.items():
                try:        t = self.fieldtypes[table][field]
                except:     t = None
                value[field] = self._de(v, t)
        else:
            try:        t = self.fieldtypes[table][field]
            except:     t = None
            value = self._de(value, t)
        return value


    def _se(self, value, fieldtype):
        if not fieldtype:
            # no datatype information set
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, (list, tuple)):
                value = u"\n".join([unicode(v, self.codepage) for v in value])
            elif isinstance(value, bytes):
                value = unicode(value, self.codepage)
            return value
        
        if fieldtype in ("date", "datetime", "timestamp"):
            if not isinstance(value, unicode):
                value = unicode(value)
        
        elif fieldtype in ("list",):
            # to lines
            if isinstance(value, (list, tuple)):
                if value:
                    value = value[0]

        elif fieldtype in ("mselection", "mcheckboxes", "list", "urllist", "unitlist"):
            # to lines
            if not value:
                value = u""
            elif isinstance(value, (list, tuple)):
                if isinstance(value[0], bytes):
                    # list of strings:
                    value = u"\n".join([unicode(v, self.codepage) for v in value])
                else:
                    # other values
                    value = u"\n".join([unicode(v) for v in value])

        elif fieldtype in ("bool"):
            if isinstance(value, basestring):
                if value.lower()==u"true":
                    value = 1
                elif value.lower()==u"false":
                    value = 0
            else:
                try:
                    value = int(value)
                except:
                    value = 0

        elif fieldtype == "json":
            if not value:
                value = u""
            elif not isinstance(value, basestring):
                value = json.dumps(value)
            
        # assure unicode except filedata
        if isinstance(value, bytes) and fieldtype!="file":
            value = unicode(value, self.codepage)
        
        return value


    def _de(self, value, fieldtype):
        if not fieldtype:
            # no datatype information set
            if isinstance(value, bytes):
                value = unicode(value, self.codepage)
            return value

        if fieldtype in ("date", "datetime", "timestamp"):
            # -> to datatime
            if isinstance(value, basestring):
                value = ConvertToDateTime(value)
                    
        elif fieldtype in ("mselection", "mcheckboxes", "urllist", "unitlist"):
            # -> to string tuple
            # unitlist -> to number tuple
            if not value:
                value = u""
            elif isinstance(value, basestring):
                value = tuple(value.split(u"\n"))
            elif isinstance(value, list):
                value = tuple(value)
            elif value == None:
                value = ()
            if fieldtype == "unitlist":
                value = [long(v) for v in value]
            
        elif fieldtype == "json":
            # -> to python type
            if not value:
                value = None
            elif isinstance(value, basestring):
                value = json.loads(value)
            
        return value
    
    