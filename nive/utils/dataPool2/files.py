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

import weakref
import os
import uuid
from StringIO import StringIO

from nive.utils.path import DvPath



# FileManager Constants ---------------------------------------------------------------------------

class File(object):
    """
    File mapping object. The file attribute can be stored as data or readable stream object.
    This file class is used to map files stored and read from the storage system.
    
    Two modes are supported:
    - BlobFile: Files stored as Blob files in filesystem
    - TempFile: Temp files to be stored
    
    Pass a dictionry to set all attributes as filemeta
    """

    def __init__(self, 
                 filekey="", 
                 filename="", 
                 file=None, 
                 size=0, 
                 path="", 
                 extension="", 
                 fileid=0, 
                 uid="", 
                 tempfile=False, 
                 filedict=None, 
                 fileentry=None):
        self.filekey = filekey
        self.filename = filename
        self.file = file
        self.fileid = fileid
        self.uid = str(fileid)
        self.size = size
        self.path = path
        self.extension = extension
        self.tempfile = tempfile
        if fileentry:
            self.fileentry = weakref.ref(fileentry)
        else:
            self.fileentry = None
        if filedict:
            # update attributes from dictionary
            self.update(filedict)

        # file data is set as string -> create string io and mark as tempfile
        if isinstance(self.file, basestring):
            self.size = len(self.file)
            self.file = StringIO(self.file)
            self.tempfile = True

        # get extension and file name if not set
        if self.filename == "" and self.path != "":
            self.filename = os.path.basename(path)
        if self.filename != "" and self.extension == "":
            fileName, fileExtension = os.path.splitext(self.filename)
            self.extension = fileExtension[1:6]
    

    def isTempFile(self):
        return self.tempfile
    
    def abspath(self):
        return self.fileentry()._Path(self)

    def fromPath(self, path):
        """
        Set temp file and load file values from file path
        """
        if self.filename == "":
            self.filename = os.path.basename(path)
            f, fileExtension = os.path.splitext(path)
            self.extension = fileExtension[1:6]
        if self.size == 0:
            p = DvPath(path)
            self.size = p.GetSize()
        self.tempfile = True
        self.file = open(path, "rb")


    def read(self, size=-1):
        # 1) read temp file
        if self.isTempFile():
            if not self.file:
                # error no file 
                raise IOError("Tempfile is none")
            data = self.file.read(size)
            return data
            
        # 2) read blob file
        if not self.file:
            # read all
            file = open(self.fileentry()._Path(self))
            if size < 1 or size == None:
                data = file.read()
                file.close()
                return data
            self.file = file
        data = self.file.read(size)        
        return data
 
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
    Table "pool_files" ("id", "fileid", "filekey", "path", "filename", "size", "extension", "version").
    Field path stores internal path to the file in filesystem without root.

    Preperty descriptions are dictionaries with key:value pairs.
    Property values:
    id = unit id to store file for (id is required)
    version = the version of the file
    filekey = custom value

    key:
    id_filekey_version

    directory structure:
    root/id[-4:-2]00/id_filekey_version.ext
    """

    DirectoryCnt = -4                 # directory id range limit
    FileTable = u"pool_files"    # file table name
    FileTableFields = (u"id", u"fileid", u"filekey", u"path", u"filename", u"size", u"extension", u"version")
    Trashcan = u"_trashcan"
    
    def GetFileClass(self):
        """
        Returns the required file class for File object instantiation 
        """
        return File

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
        flds = self.FileTableFields
        kw["singleTable"] = 1
        sql, values = self.FmtSQLSelect(flds, parameter, dataTable=self.FileTable, sort = sort, start=start, max=max, ascending = ascending, **kw)
        files = self.Query(sql, values)
        f2 = []
        for f in files:
            f2.append(self.ConvertRecToDict(f, flds))
        return f2


    # Internal --------------------------------------------------------------

    def _GetSystemPath(self, file, path="", absolute = True, includeTemp = True):
        """
        Constructs the physical path of the file.
        """
        if file and file.tempfile:
            return u""
        elif file:
            if not file.path:
                return u""
            if absolute and file.path[:len(str(self.root))] != str(self.root):
                path = DvPath(str(self.root))
                path.AppendSeperator()
                path.Append(file.path)
            else:
                path = DvPath(file.path)
            return path.GetStr()
        elif path:
            p = DvPath()
            if absolute and path[:len(str(self.root))] != str(self.root):
                p = DvPath(str(self.root))
                p.AppendSeperator()
                p.Append(path)
                return p.GetStr()
            return path
        return u""


    def _DeleteFiles(self, id, cursor=None, version=None):
        """
        Delete the file with the prop description
        """
        files = self.SearchFiles({u"id":id}, sort=u"id")
        for f in files:
            if f["path"]:
                originalPath = DvPath(self._GetSystemPath(None, path=f["path"]))
                if originalPath.Exists() and not self._MoveToTrashcan(originalPath, id):
                    pass
        if len(files):
            sql = u"delete from %s where id = %d" % (self.FileTable, id)
            self.Query(sql, cursor=cursor, getResult=False)
        return True


    def _GetDirectory(self, id):
        """
        construct directory path without root
        """
        return (u"%06d" % (id))[self.DirectoryCnt:-2] + u"00/" + (u"%06d" % (id))[self.DirectoryCnt+2:]
        #return ("%06d" % (id))[self.DirectoryCnt:-2] + "00"


    def _MoveToTrashcan(self, path, id):
        if not self.useTrashcan:
            return path.Delete()

        aP = self._GetTrashcanDirectory(id)
        aP.SetNameExtension(path.GetNameExtension())
        if aP.Exists():
            aP.Delete()
        return path.Rename(str(aP))


    def _GetTrashcanDirectory(self, id):
        aP = DvPath()
        aP.SetStr(str(self.root))
        aP.AppendSeperator()
        aP.AppendDirectory(self.Trashcan)
        aP.AppendSeperator()
        aP.AppendDirectory(self._GetDirectory(id))
        aP.AppendSeperator()
        return aP




class FileEntry:
    """
    Data pool entry extension to handle physical files. 
    
    This class provides all functions to store and read files from the backend. Each file
    is stored with a key (a field name like and other data field) and loaded and stored using
    the `File` container class. The file entry has no restrictions on the number of files.
    """

    def Files(self, parameter=None, cursor=None, loadFileData=False):
        """
        List all files matching the parameters.
        Returns a dictionary.
        """
        if not parameter:
            parameter = {}
        parameter[u"id"] = self.id
        operators={u"filekey":u"=", "filename": u"="}
        sql, values = self.pool.FmtSQLSelect(self.pool.FileTableFields, parameter, dataTable=self.pool.FileTable, operators=operators, singleTable=1)
        recs = self.pool.Query(sql, values)
        if len(recs) == 0:
            return []
        files = []
        for f in recs:
            d = self.pool.ConvertRecToDict(f, self.pool.FileTableFields)
            file = File(d["filekey"], filedict=d, fileentry=self)
            files.append(file)
        return files


    def FileKeys(self):
        """
        return all existing file keys as list
        """
        sql = u"select filekey from %s where id = %d group by filekey" % (self.pool.FileTable, self.id)

        aList = self.pool.Query(sql)
        if len(aList) == 0:
            return []
        l = []
        for i in aList:
            l.append(i[0])
        return l


    def GetFile(self, key, fileid=None, loadFileData=False):
        """
        return the meta file informations from db or None if no
        matching record found
        """
        if not key or key == u"":
            return None
        if fileid!=None:
            parameter = {u"fileid":fileid}
        else:
            parameter = {u"filekey": key}
        files = self.Files(parameter, loadFileData=loadFileData)
        if len(files)==0:
            return None
        file = files[0]
        return file


    # Store File --------------------------------------------------------------------

    def CommitFiles(self, files, cursor=None):
        """
        Commit multiple files in a row
        """
        for key, file in files.items():
            self.CommitFile(key, file, cursor=cursor)


    def CommitFile(self, key, file, cursor=None):
        """
        Store the file under key. File can either be a path, dictionary with file informations 
        or a File object.
        """
        if key in (u"", None):
            raise IOError("File key invalid")

        # convert to File object
        if isinstance(file, dict):
            file = File(key, filedict=file, fileentry=self)
        elif isinstance(file, basestring):
            # load from temp path
            f = File(key, fileentry=self)
            f.fromPath(file)
            file = f
        else:
            file.filekey = key

        # lookup exiting file to replace
        if file.fileid == 0:
            fileid = self._LookupFileID(file, cursor)
            file.fileid = fileid
        else:
            fileid = file.fileid
        
        # update file records
        self._Write(file)
        self._UpdateMeta(file, cursor=cursor)
        return True


    def _Write(self, file, abortSize=0):
        """
        This functions writes the file to the pool directory. If the file is not marked
        as tempfile, nothing is written.
        
        Files are processed in the following order:
        - a temp path is created
        - the file is written to this path
        - the original file is renamed to be deleted on success and stored as `file.deleteOnSuccess`
        - the tempfile is renamed to the original path
        - the original file can be removed by calling `Cleanup()`
        """
        if not file.isTempFile():
            # nothing to write -> return
            return True
        
        # create temp path for current
        backupPath = None
        originalPath = DvPath(self._Path(file))
        
        newPath = DvPath(self._CreatePath(file.filekey, file.filename))
        tempPath = DvPath(str(newPath))
        tempPath.SetName(u"_temp_" + unicode(uuid.uuid4()))
        tempPath.SetExtension(newPath.GetExtension())

        if tempPath.Exists():
            tempPath.Delete()
        tempPath.CreateDirectories()
        size = 0
        try:
            out = open(tempPath.GetStr(), "wb")
            data = file.read(10000)
            while data:
                size += len(data)
                if abortSize and size > abortSize:
                    raise IOError, "File too big"
                out.write(data)
                data = file.read(10000)
            out.close()
            #file.close()
        except Exception, e:
            try:    file.file.close()
            except: pass
            try:    out.close()
            except: pass
            # reset old file
            tempPath.Delete()
            raise Exception, e

        # store path for cleanup on success
        if str(originalPath) and originalPath.Exists():
            backupPath = DvPath(str(originalPath))
            backupPath.SetName("_del_" + unicode(uuid.uuid4()))
            backupPath.SetExtension(originalPath.GetExtension())
            if originalPath.Exists() and not originalPath.Rename(backupPath):
                tempPath.Delete()
                raise IOError, "Rename file failed"
            file.deleteOnSuccess = str(backupPath)

        try:
            # rename temp path
            os.renames(str(tempPath), str(newPath))
            # update meta properties
            file.path = self._RelativePath(str(newPath))
            file.size = size
            return True
        except:
            tempPath.Delete()
            if backupPath:
                backupPath.Rename(originalPath)
            raise


    def _UpdateMeta(self, file, cursor):
        """
        store file meta information in database table
        """
        data = {
            "filename": file.filename,
            "path": file.path,
            "filekey": file.filekey,
            "extension": file.extension,
            "size": file.size
        }
        if file.fileid:
            file.fileid = self.pool.UpdateFields(self.pool.FileTable, file.fileid, data, cursor=cursor, idColumn=u"fileid")
        else:
            data["id"] = self.id
            data, file.fileid = self.pool.InsertFields(self.pool.FileTable, data, cursor=cursor, idColumn=u"fileid")
        return True


    def Cleanup(self, files):
        """
        Cleanup tempfiles after succesful writes
        """
        if not isinstance(files, dict):
            files = {"":files}
        for key, file in files.items():
            if not hasattr(file, "deleteOnSuccess"):
                continue
            path = DvPath(file.deleteOnSuccess)
            try:
                path.Delete()
            except:
                pass

    
    # Options --------------------------------------------------------------------

    def FileExists(self, file):
        """
        check if the file physically exists
        """
        if not file:
            return False
        if not file.path:
            return True
        path = DvPath(self._Path(file))
        return path.Exists()
            

    def CopyFile(self, file, newPath):
        """
        Returns the physical path of the file or copies it to newpath if set
        """
        if not newPath:
            return False
        path = DvPath(self._Path(file))
        try:
            return path.Copy(newPath)
        except Exception, e:
            pass
        return False


    def DuplicateFiles(self, newEntry, replaceExisting = True):
        """
        Copy the file
        If filekey = "" all files are copied
        """
        files = self.Files()
        result = True
        for file in files:
            if not self.FileExists(file):
                result = False
                continue
            if newEntry.FileExists(file) and not replaceExisting:
                continue
            newFile = self.pool.GetFileClass()(file=file, filename=file.filename, size=file.size, tempfile=True)
            try:
                newEntry.CommitFile(file.filekey, newFile)
            except:
                newFile.file = None
                raise 
        return result


    def DeleteFile(self, key):
        """
        Delete the file with the prop description
        """
        self.files.set(key, None)
        file = self.GetFile(key)
        if not file:
            # not found
            return False
        if file.path:
            originalPath = DvPath(self._Path(file))
            if not originalPath.IsFile():
                #not a file
                return False
            if originalPath.Exists() and not self.pool._MoveToTrashcan(originalPath, self.id):
                #Delete failed!
                return False
        
        sql = u"delete from %s where fileid = %d" % (self.pool.FileTable, file.fileid)
        self.pool.Query(sql, getResult=False)
        return True


    def RenameFile(self, key, filename):
        """
        Changes the filename field of the file `key`.
        """
        self.files.set(key, None)
        file = self.GetFile(key)
        if not file:
            return False
        data = {"filename": filename}
        return self.pool.UpdateFields(self.pool.FileTable, file.fileid, data, idColumn=u"fileid")


    # internal --------------------------------------------------------------------

    def _Path(self, file, absolute = True):
        """
        Get the physical path of the file. Checks the database.
        """
        if isinstance(file, basestring):
            file = self.GetFile(file)
        if not file:
            return u""
        return self.pool._GetSystemPath(file, absolute)


    def _LookupFileID(self, file, cursor=None):
        """
        lookup unique fileid for file
        """
        f = self.Files(parameter={"filekey":file.filekey})
        if len(f)==0:
            return 0
        return f[0]["fileid"]
         
         
    def _FmtFilename(self, key):
        """
        Constructs the key for the file. Used as filename.
        """
        aID = u"%06d" % (self.id)
        return u"%s_%s_" % (aID, key)


    def _CreatePath(self, key, filename):
        """
        Create the physical path of the file
        """
        aExtension = DvPath(filename).GetExtension()

        aP = DvPath()
        aP.SetStr(str(self.pool.root))
        aP.AppendSeperator()
        aP.AppendDirectory(self._GetDirectory())
        aP.AppendSeperator()

        aP.SetName(self._FmtFilename(key))
        aP.SetExtension(aExtension)
        return aP.GetStr()


    def _GetDirectory(self):
        return self.pool._GetDirectory(self.id)

    def _GetTrashcanDirectory(self):
        return self.pool._GetTrashcanDirectory(self.id)

    def _RelativePath(self, path):
        p = path[len(str(self.pool.root)):]
        p = p.replace(u"\\", u"/")
        return p

