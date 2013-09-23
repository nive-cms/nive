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

try:    from win32pipe import popen
except: from os import popen

import os
import string
import stat
import shutil


class DvPath(object):
    """
    Common path and directory operations
    """

    def __init__(self, path = None):
        """
        string: path
        """
        self._path = ""
        if path:
            if isinstance(path, basestring):
                self.SetStr(path)
            else:
                self.SetStr(str(path))

    def __str__(self):
        return self._path

    def SetStr(self, path):
        """
        string: path
        """
        self._path = path

    def GetStr(self):
        """
        returns string
        """
        return self._path


    # set ----------------------------------------------------------------------------
    def SetName(self, name):
        """
        string: name
        """
        p, s = os.path.split(self._path)
        s, ext = os.path.splitext(self._path)
        if len(p) > 0:
            p += os.sep
        self._path = p + name + ext

    def SetExtension(self, ext):
        """
        string: ext
        """
        if not ext:
            return
        if not ext.startswith("."):
            ext = "." + ext
        p, old = os.path.splitext(self._path)
        self._path = p + ext

    def SetNameExtension(self, nameExt):
        """
        string: nameExt
        """
        self._path, s = os.path.split(self._path)
        self.AppendSeperator()
        self._path += nameExt

    def Append(self, path):
        """
        string: path
        """
        if not path:
            return
        if not path.startswith(os.sep):
            self.AppendSeperator()
        self._path += path

    def AppendSeperator(self):
        if self._path!="" and not self._path.endswith(os.sep):
            self._path += os.sep

    def AppendDirectory(self, dir):
        """
        string: dir
        """
        self.AppendSeperator()
        self.SetName(dir)
        self.AppendSeperator()

    def RemoveLastDirectory(self):
        name = self.GetNameExtension()
        self.SetNameExtension("")
        if self._path.endswith(os.sep):
            self._path = self._path[:-1]
        self.SetNameExtension("")
        self.AppendSeperator()
        self.SetNameExtension(name)


    # get ----------------------------------------------------------------------------

    def GetPath(self): 
        """
        Path includes trailing seperator
        return: string
        """
        if not self.IsValid():
            return ""
        path, name = os.path.split(self._path)
        if not path:
            return ""
        if not path.endswith(os.sep):
            path += os.sep
        return path

    def GetName(self):
        """
        return: string
        """
        if not self.IsValid():
            return ""
        path, name = os.path.split(self._path)
        name, ext = os.path.splitext(name)
        return name

    def GetExtension(self):
        """
        return: string
        """
        if not self.IsValid():
            return ""
        path, ext = os.path.splitext(self._path)
        if ext.startswith("."):
            ext = ext[1:]
        return ext

    def GetNameExtension(self):
        """
        return: string
        """
        if not self.IsValid():
            return ""
        path, name = os.path.split(self._path)
        return name

    def GetSize(self):
        """
        return long
        """
        if not self.IsValid():
            return ""
        if self.IsDirectory():
            return 0
        try:
            return os.stat(self._path)[stat.ST_SIZE]
        except:
            return -1

    def GetLastDirectory(self):
        """
        Name of last directory
        return string
        """
        if not self.IsValid():
            return ""
        path, name = os.path.split(self._path)
        if path.endswith(os.sep):
            path = path[:-1]
        parts = path.split(os.sep)
        if not parts:
            return ""
        return parts[-1]


    # state ----------------------------------------------------------------------------
    def IsFile(self):
        """
        return bool
        """
        return os.path.isfile(self._path)

    def IsDirectory(self):
        """
        return bool
        """
        return os.path.isdir(self._path)

    def Exists(self):
        """
        return bool
        """
        return self.IsFile() or self.IsDirectory()

    def IsValid(self): #INTERN
        """
        return bool
        """
        return len(self._path) > 0


    # operations ----------------------------------------------------------------------------

    def Delete(self, deleteSubdirs = False):
        """
        Ignores exceptions
        return bool
        """
        if deleteSubdirs:
            path = self.GetPath()
            if not self.IsDirectory():
                return False
            shutil.rmtree(self._path, ignore_errors=True)
            return not self.IsDirectory()

        try:
            if self.IsDirectory():
                os.rmdir(self._path)
                return not self.IsDirectory()
            os.remove(self._path)
        except OSError:
            pass
        return not self.IsFile()


    def CreateDirectories(self):
        """
        Ignores exceptions
        return bool
        """
        if self.Exists():
            return True
        try:
            path, name = os.path.split(self._path)
            os.makedirs(path)
            return True
        except:
            return False


    def CreateDirectoriesExcp(self):
        """
        Throws exceptions
        return bool
        """
        if self.Exists():
            return True
        path, name = os.path.split(self._path)
        os.makedirs(path)
        return True


    def Rename(self, newName):
        """
        return bool
        """
        if not self.IsFile():
            return False
        os.renames(self._path, newName)
        return True


    def Execute(self, cmd, returnStream = True):
        """
        execute the current path with popen and returns std out
        """
        s = popen(self._path + " " + cmd, "r")
        if returnStream:
            return s
        r = ""
        while 1:
            d = s.readline()
            if not d or d == ".\n" or d == ".\r":
                break
            r += d
        return r

