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

__doc__ = ""


import re, os, sys
from types import *
from StringIO import StringIO

from nive.utils.utils import BREAK, STACKF
from nive.utils.path import DvPath
from nive.utils.utils import GetMimeTypeExtension, GetExtensionMimeType, ConvertToLong



# FileManager Constants ---------------------------------------------------------------------------

#[<]
DirectoryCnt = -4                 # directory id range limit
FileTable = u"pool_files"    # file table name
FileTableFields = (u"id", u"fileid", u"tag", u"path", u"filename", u"size", u"extension", u"version")
PoolKeyPos = 2
Trashcan = u"_trashcan"
BackupVersion = u"_versions"
CntVersions = 10
#[>]


class File(object):
    """
    Simple file maping object. file can be stored as data or stream object
    """

    def __init__(self, tag="", filename="", file=None, size=0, path="", extension="", fileid=0, uid="", tempfile=False, mime="", filedict=None, fileentry=None):
        self.tag = tag
        self.filename = filename
        self.file = file
        self.fileid = fileid
        self.uid = str(fileid)
        self.size = size
        self.path = path
        self.mime = ""
        self.extension = extension
        self.tempfile = tempfile
        self.fileentry = fileentry
        if filedict:
            self.update(filedict)

        if isinstance(self.file, basestring):
            self.file = StringIO(self.file)

        if self.filename=="" and self.path!="":
            p = DvPath(self.path)
            self.filename = p.GetNameExtension()

        if self.filename != "" and self.extension == "":
            p = DvPath(self.filename)
            self.extension = p.GetExtension()
    

    def SetFromPath(self, path):
        p = DvPath(path)
        if self.filename == "":
            self.filename = p.GetNameExtension()
            self.extension = p.GetExtension()
        if self.size == 0:
            self.size = p.GetSize()
        self.tempfile = True
        self.path = path


    def read(self, size=-1):
        if not self.file and not size:
            file = open(self.path)
            data = file.read()
            file.close()
            return data
        elif not size:
            data = self.file.read()
            self.file.close()
            self.file = None
            return data
        elif not self.file:
            self.file = open(self.path)
            data = self.file.read(size)
            if not size:
                self.file.close()
                self.file = None
            return data
        if self.file.closed:
            self.file = open(self.path)
            data = self.file.read(size)
            if not size:
                self.file.close()
                self.file = None
            return data
        return self.file.read(size)
    
    
    def seek(self, offset):
        if not self.file:
            return
        self.file.seek(offset)


    def tell(self):
        if not self.file:
            return 0
        return self.file.tell()
    

    def close(self):
        if self.file:
            self.file.close()

    def __iter__(self):
        return iter(self.__dict__.keys())
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def get(self, key, default=None):
        try:
            return getattr(self, key)
        except:
            return default
        
    def update(self, data):
        for k in data.keys():
            setattr(self, k, data[k])



class FileManager:
    """
    Data Pool File Manager class for SQL Database with version support.

    Files are stored in filesystem, aditional information in database table.
    Table "pool_files" ("id", "fileid", "tag", "path", "filename", "size", "extension", "version").
    Field path stores internal path to the file in filesystem without root.

    Preperty descriptions are dictionaries with key:value pairs.
    Property values:
    id = unit id to store file for (id is required)
    version = the version of the file
    tag = custom value

    key:
    id_tag_version_backup

    directory structure:
    root/id[-4:-2]00/id_tag_version.ext
    """

    def SetRoot(self, root):
        """
        Set the local root path for files
        """
        self.root = DvPath()
        self.root.SetStr(root)
        if root == u"":
            return
        self.root.AppendSeperator()
        self.root.CreateDirectoriesExcp()


    # Searching --------------------------------------------------------------

    def SearchFilename(self, filename):
        """
        search for filename
        """
        return self.SearchFiles({u"filename": filename})


    def SearchFiles(self, parameter, sort=u"filename", start=0, max=100, ascending = 1, **kw):
        """
        search files
        """
        flds = FileTableFields
        kw["singleTable"] = 1
        sql = self.GetSQLSelect(flds, parameter, dataTable=FileTable, sort = sort, start=start, max=max, ascending = ascending, **kw)
        files = self.Query(sql)
        f2 = []
        for f in files:
            f2.append(self.ConvertRecToDict(f, flds))
        return f2


    # Filename conversion -------------------------------------------------------------

    def ConvertFilenameToProp(self, key):
        aProp = {}
        aL = key.split(self.GetKeySep())
        self.FillPropWC(aProp)
        aProp[u"id"] = ConvertToLong(aL[0])
        if len(aL) > 1:        aProp[u"tag"] = aL[1]
        if len(aL) > 2:        aProp[u"version"] = aL[2]
        if len(aL) > 3:        aProp[u"backup"] = ConvertToLong(aL[3])
        return aProp


    def FillPropWC(self, prop = {}):
        if not prop.has_key(u"id") or prop[u"id"] == u"" or prop[u"id"] == 0:
            prop[u"id"] = self.GetWC()
        if not prop.has_key(u"version") or prop[u"version"] == u"":
            prop[u"version"] = self.GetWC()
        if not prop.get(u"tag") or prop[u"tag"] == u"":
            prop[u"tag"] = self.GetWC()
        if not prop.get(u"backup") or prop[u"backup"] == u"":
            prop[u"backup"] = self.GetWC()
        return prop


    def GetWC(self):
        return u"*"


    def GetKeySep(self):
        return u"_"


    # Internal --------------------------------------------------------------

    def GetSystemPath(self, file, path="", absolute = True, includeTemp = True):
        """
        Get the physical path of the file. Checks the database.
        """
        if file and file.tempfile:
            return file[u"path"]
        elif file:
            if absolute and file[u"path"][:len(str(self.root))] != str(self.root):
                path = DvPath(str(self.root))
                path.AppendSeperator()
                path.Append(file[u"path"])
            else:
                path = DvPath(file[u"path"])
            return path.GetStr()
        else:
            p = DvPath()
            if absolute and path[:len(str(self.root))] != str(self.root):
                p = DvPath(str(self.root))
                p.AppendSeperator()
                p.Append(path)
                return p.GetStr()
            return path


    def _DeleteFiles(self, id, cursor=None, version=None):
        """
        Delete the file with the prop description
        """
        files = self.SearchFiles({u"id":id}, sort=u"id")
        for f in files:
            aOriginalPath = DvPath(self.GetSystemPath(None, path=f["path"]))
            if aOriginalPath.Exists() and not self._MoveToTrashcan(aOriginalPath, id):
                #self.pool._Error(-305)
                #self.err = u"Delete failed!"
                pass
        if len(files):
            aSql = u"delete from %s where id = %d" % (FileTable, id)
            self.Query(aSql, cursor=cursor)
        return True


    def _GetDirectory(self, id):
        """
        construct directory path without root
        """
        return (u"%06d" % (id))[DirectoryCnt:-2] + u"00/" + (u"%06d" % (id))[DirectoryCnt+2:]
        #return ("%06d" % (id))[DirectoryCnt:-2] + "00"


    def _MoveToTrashcan(self, path, id):
        if not self.useTrashcan:
            return path.Delete()

        aP = self._GetTrashcanDirectory(id)
        aP.SetNameExtension(path.GetNameExtension())
        if aP.Exists():
            aP.Delete()
        return path.Rename(str(aP))


    def _GetBackupDirectory(self, id):
        aP = DvPath()
        aP.SetStr(str(self.root))
        aP.AppendSeperator()
        aP.AppendDirectory(BackupVersion)
        aP.AppendSeperator()
        aP.AppendDirectory(self._GetDirectory(id))
        aP.AppendSeperator()
        return aP


    def _GetTrashcanDirectory(self, id):
        aP = DvPath()
        aP.SetStr(str(self.root))
        aP.AppendSeperator()
        aP.AppendDirectory(Trashcan)
        aP.AppendSeperator()
        aP.AppendDirectory(self._GetDirectory(id))
        aP.AppendSeperator()
        return aP




class FileEntry:
    """
    File container class
    """

    # Searching and file meta-------------------------------------------------------------------------

    def Files(self, param={}):
        """
        List all files matching the parameters.
        Returns a dictionary.
        """
        param[u"id"] = self.id
        operators={u"tag":u"=", u"version":u"=", "filename": u"="}
        if param.has_key(u"version") and type(param[u"version"]) in (type(()), type([])):
            BREAK("version")
            operators[u"version"] = u"in"
        sql = self.pool.GetSQLSelect(FileTableFields, param, dataTable=FileTable, operators=operators, singleTable=1)
        recs = self.pool.Query(sql)
        if len(recs) == 0:
            return []
        files = []
        for f in recs:
            d = self.pool.ConvertRecToDict(f, FileTableFields)
            file = File(d["tag"], filedict=d, fileentry=self)
            file.path = self.pool.GetSystemPath(file, True)
            files.append(file)
        return files


    def GetTags(self):
        """
        return all existing file tags as list
        """
        aFlds = u"tag"
        if self.version:
            BREAK("version")
        aSql = u"select %s from %s where id = %d group by tag" % (aFlds, FileTable, self.id)

        aList = self.pool.Query(aSql)
        if len(aList) == 0:
            return []
        l = []
        for i in aList:
            l.append(i[0])
        return l


    def GetFileID(self, file):
        """
        lokkup unique fileid for file
        """
        f = self.Files(param={"tag":file.tag})
        if len(f)==0:
            return 0
        return f[0]["fileid"]
         
         
    # Read File --------------------------------------------------------------------

    def GetFile(self, tag):
        """
        return the meta file informations from db or None if no
        matching record found
        """
        if not tag or tag == u"":
            return None
        param = {u"tag": tag}
        files = self.Files(param)
        if len(files)==0:
            return None
        file = files[0]
        return file


    def GetFileData(self, tag=None, fileid=None):
        """
        Get the file matching the prop description
        """
        file = self.GetFile(tag)
        if not file:
            return None
        data = file.read()
        file.close()
        return data


    # Store File --------------------------------------------------------------------

    def SetFile(self, tag, file, cursor=None):
        """
        Store the file under tag. File can either be a path, dictionary with file informations 
        or a File object.
        """
        if not self.IsTagValid(tag):
            #self.err = u"Invalid Tag!"
            return False

        # convert to File object
        if type(file) == DictType:
            file = File(tag, filedict=file, fileentry=self)
        elif isinstance(file, basestring):
            # load from temp path
            f = File(tag, fileentry=self)
            f.SetFromPath(file)
            file = f
        else:
            file.tag = tag

        return self._SetStream(file)


    def UpdateFileMeta(self, file):
        """
        store file meta information in database table
        """
        if not self.IsTagValid(file.tag):
            #self.err = u"Invalid Tag!"
            return False
        aInternalPath = self._CutInternalPath(str(file.path))
        version = u"" #
        
        ph = self.pool.GetPlaceholder()
        if file.fileid == 0:
            fileid = self.GetFileID(file)
        else:
            fileid = file.fileid
        if fileid:
            aSql = u"""UPDATE %(table)s SET
                    filename = %(ph)s,
                    path = %(ph)s,
                    tag = %(ph)s,
                    extension = %(ph)s,
                    version = %(ph)s,
                    size = %(ph)s
                    WHERE fileid = %(ph)s and id = %(ph)s
                    """ % {u"table":FileTable, u"ph":ph}
            values = (file.filename,
                    aInternalPath,
                    file.tag,
                    file.extension,
                    version,
                    file.size,
                    fileid,
                    self.id)
            self.pool.Query(aSql, values)
        else:
            aSql = u"""INSERT INTO %(table)s
                    (id,
                    filename,
                    path,
                    tag,
                    extension,
                    version,
                    size)
                    VALUES
                    (%(ph)s, %(ph)s, %(ph)s, %(ph)s, %(ph)s, %(ph)s, %(ph)s)
                    """ % {u"table":FileTable, u"ph":ph}
            values = (self.id,
                    file.filename,
                    aInternalPath,
                    file.tag,
                    file.extension,
                    version,
                    file.size)
            self.pool.Query(aSql, values)
        return True


    # Options --------------------------------------------------------------------

    def FileExists(self, file):
        """
        check if the file physically exists
        """
        if type(file) in (StringType, UnicodeType):
            path = DvPath(self.GetPath(file))
            return path.Exists()
        aP = DvPath(self.pool.GetSystemPath(file))
        return aP.Exists()
            

    def IsTagValid(self, tag):
        """
        validate tag
        """
        if tag in (u"", None):
            return False
        return True


    def CopyFile(self, file, newPath):
        """
        Returns the physical path of the file or copies it to newpath if set
        """
        if not newPath:
            return False
        if type(file) in (StringType, UnicodeType):
            path = DvPath(self.GetPath(file))
        else:
            path = DvPath(self.pool.GetSystemPath(file))
        try:
            return path.Copy(newPath)
        except Exception, e:
            #self.err = str(e)
            #self.pool._Error(-306)
            pass
        return False


    def DuplicateFile(self, newEntry, parameter = {}, replaceExisting = True):
        """
        Copy the file
        If tag = "" all files are copied
        """
        aFiles = self.Files(parameter)
        result = True
        for f in aFiles:
            if not self.FileExists(f):
                #self.pool._Error(-304)
                #self.err = u"File not found!"
                result = False
                continue

            #p = self.pool.GetPropertiesFromMeta(f)
            if newEntry.FileExists(f[u"tag"]):
                if not replaceExisting:
                    #self.pool._Error(-307)
                    #self.err = u"File exists!"
                    result = False
                    continue

            if not newEntry.SetFile(f[u"tag"], self.pool.GetSystemPath(f)):
                #self.err = u"File copy error!"
                result = False
        return result


    def DeleteFile(self, tag):
        """
        Delete the file with the prop description
        """
        self.files.set(tag, None)
        aMeta = self.GetFile(tag)
        if not aMeta:
            #not found
            return False
        aOriginalPath = DvPath(self.pool.GetSystemPath(aMeta))
        if not aOriginalPath.IsFile():
            #not a file
            return False
        if aOriginalPath.Exists() and not self.pool._MoveToTrashcan(aOriginalPath, self.id):
            #Delete failed!
            return False

        aSql = u"delete from %s where fileid = %d" % (FileTable, aMeta[u"fileid"])
        self.pool.Query(aSql)
        return True


    # Path handling --------------------------------------------------------------------

    def GetPath(self, file, absolute = True):
        """
        Get the physical path of the file. Checks the database.
        """
        if type(file) in (StringType, UnicodeType):
            file = self.GetFile(file)
        if not file:
            return u""
        return self.pool.GetSystemPath(file, absolute)


    # Backups -------------------------------------------------------------------------

    def GetRecentBackup(self, tag):
        """
        Lookup the last version of the file in the vesion bakup folder
        """
        aFile = DvPath(self._CreatePath(tag, u"", backup=u"*"))

        # get version path
        aP = self._GetBackupDirectory()
        aP.SetNameExtension(aFile.GetNameExtension())

        # loop all files
        aVersion = 0
        if not aP.FindFirst():
            return aVersion
        aVersionProp = self.pool.ConvertPathToProp(str(aP))
        aVersion = int(aVersionProp.get(u"backup"))
        while aP.FindNext():
            aVersionProp = self.pool.ConvertPathToProp(str(aP))
            if int(aVersionProp.get(u"backup")) > aVersion:
                aVersion = int(aVersionProp.get(u"backup"))
        return aVersion


    def GetBackups(self, tag):
        """
        Lookup all versions of the file in the vesion bakup folder
        """
        aFile = DvPath(self._CreatePath(tag, u"", backup=u"*"))

        # get version path
        aP = self._GetBackupDirectory()
        aP.SetNameExtension(aFile.GetNameExtension())

        # get all files
        aFiles = aP.FindFiles()
        return aFiles


    # internal --------------------------------------------------------------------

    def _SetStream(self, file, cursor=None):
        """
        Save the stream. the prop description is extracted from stream meta settings
        Mime type is used if the filename has no extension. basically
        the extension is converted to mime type

        *tempfile = True
        the file is stored as temp file. the functions filemaeta for new file including
        the temporary path. fielmeta is not updated in database.

        """
        # get the filename and extension
        extension = file.extension
        if not extension or extension == u"" and file.mime:
            extension = GetExtensionMimeType(file.mime)

        tempPath = DvPath(self._CreatePath(file.tag, file.filename))
        finalPath = str(tempPath)
        tempPath.SetName(u"_temp_" + tempPath.GetName())

        if tempPath.Exists():
            tempPath.Delete()
        tempPath.CreateDirectories()
        size = 0
        try:
            out = open(tempPath.GetStr(), "wb")
            data = file.read(10000)
            while data:
                size += len(data)
                out.write(data)
                data = file.read(10000)
            out.close()
            file.close()
        except:
            try:    file.file.close()
            except: pass
            try:    out.close()
            except: pass
            #self.pool._Error(-503)
            # reset old file
            tempPath.Delete()
            return False

        # delete existing file
        originalPath = DvPath(finalPath)
        if originalPath.Exists() and not self._MakeBackup(file.tag, originalPath):
            #self.err = u"Delete failed!"
            return False
        # rename temp path
        if not size:
            size = tempPath.GetSize()
        result = tempPath.Rename(finalPath)
        if not result:
            tempPath.Delete()
            #self.err = u"Rename failed!"
            return False
        # update meta properties
        file.path = str(finalPath)
        file.size = size
        self.UpdateFileMeta(file)
        self.Touch()
        return True


    def _GetKey(self, tag, backup = None):
        """
        Constructs the key for the file. Used as filename.
        """
        aID = u"%06d" % (self.id)
        version = ""
        if self.version:
            BREAK("version")
        backup = u""
        if backup:
            backup = u"_" + backup

        return u"%s_%s_%s%s" % (aID, tag, version, backup)


    def _CreatePath(self, tag, filename, backup = None):
        """
        Create the physical path of the file
        """
        aExtension = DvPath(filename).GetExtension()

        aP = DvPath()
        aP.SetStr(str(self.pool.root))
        aP.AppendSeperator()
        aP.AppendDirectory(self._GetDirectory())
        aP.AppendSeperator()

        aP.SetName(self._GetKey(tag, backup))
        aP.SetExtension(aExtension)
        return aP.GetStr()


    def _GetDirectory(self):
        return self.pool._GetDirectory(self.id)

    def _GetBackupDirectory(self):
        return self.pool._GetBackupDirectory(self.id)

    def _GetTrashcanDirectory(self):
        return self.pool._GetTrashcanDirectory(self.id)


    def _CutInternalPath(self, path):
        p = path[len(str(self.pool.root)):]
        p = p.replace(u"\\", u"/")
        return p


    def _MakeBackup(self, tag, path):
        if not self.pool.useBackups:
            return path.Delete()

        aFile = path
        aP = self._GetBackupDirectory()
        aP.SetNameExtension(aFile.GetNameExtension())
        result = path.Rename(str(aP))

        # delete versions
        aVersions = self.GetBackups(tag)
        aV = 1
        if len(aVersions) > CntVersions:
            # find lowest number
            aDel = ""
            for p in aVersions:
                aVersionProp = self.pool.ConvertPathToProp(p)
                if int(aVersionProp.get(u"backup")) < aV:
                    aV = int(aVersionProp.get(u"backup"))
                    aDel = p
            if aDel != u"":
                aP = self._GetBackupDirectory()
                aP.SetNameExtension(aDel)
                #if aP.Exists():
                aP.Delete()

        return result
