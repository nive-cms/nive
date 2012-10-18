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

try:    import win32api, win32con
except:    pass

try:    from win32pipe import popen
except: from os import popen

import os, sys, string, stat, shutil, tempfile, time, re, binascii, subprocess, types
import zipfile, tarfile
from datetime import datetime

WIN32 = sys.platform == "win32"
USE_WIN32 = False
kSeperator = os.sep

class DvPath(object):
    """
    Common path and directory operations
    
    ...to be refactored...
    """

    def __init__(self, path = None):
        """ (string path) """
        self._path = u""
        self._pFindList = None
        self._pFindDirList = None
        self._pFindPos = 0
        self._pSearchSubDirs = False
        if path:
            if type(path) == types.UnicodeType:
                self.SetStr(path)
            else:
                self.SetStr(str(path))

    def __str__(self):
        return self._path

    def SetStr(self, path):
        """(string path)"""
        self._path = path

    def GetStr(self):
        """return string """
        return self._path


    # set ----------------------------------------------------------------------------
    def SetDrive(self, drive):
        """(string drive) """
        aD, aP = os.path.splitdrive(self._path)
        self._path = drive + aP

    def SetPath(self, path):
        """(string path) """
        aP, aNE = os.path.split(self._path)
        self._path = path
        self.AppendSeperator()
        self._path += aNE

    def SetName(self, n):
        """(string name) """
        aP, aStr = os.path.split(self._path)
        aStr, aE = os.path.splitext(self._path)
        if len(aP) > 0:
            aP += os.sep
        self._path = aP + n + aE

    def SetExtension(self, ext):
        """(string ext) """
        if not ext or len(ext) == 0:
            return
        if not ext[0] == ".":
            ext = "." + ext
        aP, aE = os.path.splitext(self._path)
        self._path = aP + ext

    def SetNameExtension(self, nameExt):
        """(string nameExt) """
        aP, aStr = os.path.split(self._path)
        self._path = aP
        self.AppendSeperator()
        self._path += nameExt

    def SetModTime(self, time):
        """(string time) return bool"""
        return False

    def AppendDirectory(self, inDir):
        self.AppendSeperator()
        self.SetName(inDir)
        self.AppendSeperator()

    def Append(self, inPath):
        """(string inPath) """
        if inPath == "":
            return
        if inPath[0] == os.sep:
            inPath = inPath[1:]
        self.AppendSeperator()
        self._path += inPath

    def RemoveLastDirectory(self):
        name = self.GetNameExtension()
        self.SetNameExtension("")
        if self.HasSeperatorEnd():
            self._path = self._path[:-1]
        self.SetNameExtension("")
        self.AppendSeperator()
        self.SetNameExtension(name)


    # get ----------------------------------------------------------------------------
    def GetDrive(self):
        """return string """
        if not self.IsValid():
            return ""
        aD, aP = os.path.splitdrive(self._path)
        return aD

    def GetPath(self):
        """return string
        Path includes trailing seperator
        """
        if not self.IsValid():
            return ""
        aP, aNE = os.path.split(self._path)
        if aP == "":
            return ""
        if not aP[-1] == os.sep:
            aP += os.sep
        return aP

    def GetName(self):
        """return string """
        if not self.IsValid():
            return ""
        aP, aNE = os.path.split(self._path)
        aN, aE = os.path.splitext(aNE)
        return aN

    def GetExtension(self):
        """return string """
        if not self.IsValid():
            return ""
        aP, aE = os.path.splitext(self._path)
        if len(aE) and aE[0] == ".":
            aE = aE[1:]
        return aE

    def GetNameExtension(self):
        """return string """
        if not self.IsValid():
            return ""
        aP, aNE = os.path.split(self._path)
        return aNE

    def GetAccessTime(self):
        """return datetime"""
        if not self.IsValid():
            return ""
        try:
            return datetime.fromtimestamp(os.stat(self._path)[stat.ST_ATIME])
        except:
            return 0

    def GetModTime(self):
        """return datetime"""
        if not self.IsValid():
            return ""
        try:
            return datetime.fromtimestamp(os.stat(self._path)[stat.ST_MTIME])
        except:
            return 0

    def GetSize(self):
        """return long"""
        if not self.IsValid():
            return ""
        if self.IsDirectory():
            return 0
        try:
            return os.stat(self._path)[stat.ST_SIZE]
        except:
            return -1

    def GetLastDirectory(self):
        """return string
        name of last directory
        """
        if not self.IsValid():
            return ""
        aP, aNE = os.path.split(self._path)
        if aP[-1] == os.sep:
            aP = aP[:-1]
        aL = string.split(aP, os.sep)
        if len(aL) == 0:
            return ""
        return aL[-1]

    def HasExtension(self):
        """return bool"""
        if not self.IsValid():
            return False
        return self._path.find(".") != -1


    # state ----------------------------------------------------------------------------
    def IsFile(self):
        """return bool """
        return os.path.isfile(self._path)

    def IsDirectory(self):
        """return bool """
        return os.path.isdir(self._path)

    def Exists(self):
        """return bool """
        return self.IsFile() or self.IsDirectory()

    def IsValid(self):
        """return bool """
        return len(self._path) > 0

    def IsEmpty(self):
        """return bool """
        if os.path.isdir(self._path):
            temp = self._path
            self.SetName("*")
            result = self.FindFirst(inSearchSubDirs = False, inReturnDirectories = True)
            self._path = temp
            return not result
        return self.GetSize()


    # find loop ----------------------------------------------------------------------------

    def FindFiles(self, regex = False):
        """
        regex = filename in path is a regular expression
        return list
        """
        if WIN32 and USE_WIN32:
            return self._FindFilesWin()
        return self._FindFilesUnix(regex)


    def FindFirst(self, inSearchSubDirs = False, inReturnDirectories = False, regex = False):
        """
        regex = filename in path is a regular expression
        return bool
        """
        if WIN32 and USE_WIN32:
            return self._FindFirstWin(inSearchSubDirs, inReturnDirectories)
        return self._FindFirstUnix(inSearchSubDirs, inReturnDirectories, regex)


    def FindNext(self):
        """return bool """
        if WIN32 and USE_WIN32:
            return self._FindNextWin()
        return self._FindNextUnix()


    def GetSubDirList(self, inAbsolut = False):
        """(bool inAbsolut) return list
        Excludes files with attribute hidden from search
        """
        if WIN32 and USE_WIN32:
            return self._GetSubDirListWin(inAbsolut)
        return self._GetSubDirListUnix(inAbsolut)


    def FindClose(self):
        """return void"""
        #if self._pFindList:
        #    del(self._pFindList)
        self._pFindDirList = None
        self._pFindPos = 0


    # seperators ----------------------------------------------------------------------------

    def HasSeperatorEnd(self):
        """return bool """
        if len(self._path) == 0:
            return 0
        if not self._path[-1] == os.sep:
            return 0
        return 1

    def AppendSeperator(self):
        """return void"""
        if self._path!="" and not self.HasSeperatorEnd():
            self._path += os.sep

    def ConvertSeperators(self):
        """
        """
        if self._path.find("\\") != -1 and kSeperator != "\\":
            self._path = self._path.replace("\\", kSeperator)
        if self._path.find("/") != -1 and kSeperator != "/":
            self._path = self._path.replace("/", kSeperator)


    # operations ----------------------------------------------------------------------------

    def Move(self, newPath):
        """(string newPath) return bool
        Move file to new path
        """
        try:
            aOldPath = self._path
            self._path = newPath
            self.CreateDirectories()
            os.rename(aOldPath, newPath)
            return True
        except:
            self._path = aOldPath
            return False


    def Copy(self, copyPath):
        """(string copyPath) return bool
        Copy file to copyPath. Directories are created if necessary
        """
        try:
            aOldPath = self._path
            self._path = copyPath
            self.CreateDirectories()
            shutil.copy2(aOldPath, copyPath)
            return True
        except Exception, e:
            self._path = aOldPath
            self.err = str(e)
            return False


    def CopyExcp(self, copyPath):
        """(string copyPath) return bool
        Copy file to copyPath. Directories are created if necessary
        """
        aOldPath = self._path
        self._path = copyPath
        self.CreateDirectories()
        shutil.copy2(aOldPath, copyPath)
        return True


    def CopyList(self, fileList, srcRoot = "", destRoot = ""):
        """(list fileList, string srcRoot, string destRoot) return bool
        Copy a list of files from a src directory to a dest directory. Static Function.
        """
        try:
            if srcRoot[-1] != kSeperator:
                srcRoot += kSeperator
            if destRoot[-1] != kSeperator:
                destRoot += kSeperator
            os.makedirs(destRoot)

            for file in fileList:
                aF = destRoot + file
                aP, aNE = os.path.split(aF)
                os.makedirs(aP)
                shutil.copy2(srcRoot + file, aF)
            return True
        except:
            return False


    def CopySub(self, destRoot = ""):
        """
        copy all subdirectories
        """
        if destRoot[-1] != kSeperator:
            destRoot += kSeperator
        aRoot = self.GetPath()
        if not self.FindFirst(True):
            return True
        aCopy = True
        while aCopy:
            aSrcPath = self._path
            aDestPath = destRoot + aSrcPath[len(aRoot):]
            try:
                aP, aNE = os.path.split(aDestPath)
                os.makedirs(aP)
            except:
                pass
            shutil.copy2(aSrcPath, aDestPath)
            aCopy = self.FindNext()
        return True


    def CopySubStatus(self, destRoot = "", statusFunction = None):
        """
        copy all subdirectories
        statusFunction is called after each file with parameters: (succeed, path, dest, size, errorstring)
        """
        if destRoot[-1] != kSeperator:
            destRoot += kSeperator
        aRoot = self.GetPath()
        if not self.FindFirst(True):
            return True
        aCopy = True
        while aCopy:
            aSrcPath = self._path
            aDestPath = destRoot + aSrcPath[len(aRoot):]
            try:
                aP, aNE = os.path.split(aDestPath)
                if not os.path.isdir(aP):
                    os.makedirs(aP)
                shutil.copy2(aSrcPath, aDestPath)
                if statusFunction:
                    statusFunction(True, aSrcPath, aDestPath, self.GetSize(), "")
            except Exception, e:
                statusFunction(False, aSrcPath, aDestPath, 0, str(e))
            aCopy = self.FindNext()
        return True


    def Delete(self, inDeleteSubdirs = False):
        """return bool """
        if inDeleteSubdirs:
            aRoot = self.GetPath()
            if not self.IsDirectory():
                return False
            self.AppendSeperator()
            self.SetNameExtension("*.*")
            if not self.FindFirst(True):
                try:
                    os.rmdir(self._path)
                except:
                    pass
                return not self.IsDirectory()
            aDel = True
            while aDel:
                if os.path.isfile(self._path):
                    os.remove(self._path)
                aDel = self.FindNext()
            self._path = aRoot
            try:
                os.removedirs(self._path)
            except:
                pass
            return not self.IsDirectory()

        if self.IsDirectory():
            os.rmdir(self._path)
            return not self.IsDirectory()
        try:
            os.remove(self._path)
        except:
            pass
        return not self.IsFile()


    def DeleteEmptyDirectories(self):
        """return bool """
        # list directories
        level = 0
        dirs = [[self._path]]
        path = self._path
        dirs = self._SubList(self._path, dirs, level+1)
        self._path = path

        # delete
        dirs.reverse()
        cnt = 0
        for l in dirs:
            for path in l:
                try:
                    os.rmdir(path)
                    cnt += 1
                except:
                    pass
        return cnt


    def CreateDirectories(self):
        """return bool"""
        if self.Exists():
            return True
        try:
            aP, aNE = os.path.split(self._path)
            os.makedirs(aP)
            return True
        except:
            return False


    def CreateDirectoriesExcp(self):
        """return bool"""
        if self.Exists():
            return True
        aP, aNE = os.path.split(self._path)
        os.makedirs(aP)
        return True


    def Rename(self, inNewName):
        """return bool"""
        if not self.IsFile():
            return False
        os.renames(self._path, inNewName)
        return True


    def ReadData(self):
        """
        return data
        compare this file with inFile
        """
        f = open(self._path)
        d = f.read()
        f.close()
        return d


    # system ----------------------------------------------------------------------------

    def SetUniqueTempFileName(self):
        """
        () return string
        """
        if not WIN32:
            aDir = tempfile.gettempdir()
            if not aDir:
                return False
            self._path = aDir
            self.AppendSeperator()
            aName = "tmp_" + str(time.time())
            self.SetNameExtension(aName)
            return True

        self._path, x = win32api.GetTempFileName(win32api.GetTempPath(), "tmp_", 0)
        return True


    def SetUniqueTempDir(self, prefix = "tmp_"):
        """
        () return string
        """
        if not WIN32:
            aDir = tempfile.gettempdir()
            if not aDir:
                return False
            self._path = aDir
            self.AppendSeperator()
            aName = prefix + str(time.time())
            self.AppendDirectory(aName)
            return True

        self._path, x = win32api.GetTempFileName(win32api.GetTempPath(), prefix, 0)
        return True


    def SetTempDir(self):
        """
        () return string
        """
        if not WIN32:
            aDir = tempfile.gettempdir()
            if not aDir:
                return False
            self._path = aDir
            self.AppendSeperator()
            return True

        self._path = win32api.GetTempPath()
        return True


    def SetModulePath(self, module=None):
        """
        set the path to module or DvLib module path
        """
        if not module:
            import DvLib
            self._path = nive.utils.path.__file__
            self.SetNameExtension("")
        else:
            self._path = module.__file__
            self.SetNameExtension("")


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


    def AddToPathEnv(self):
        """
        adds the current path to the PATH enviroment
        """
        path=os.environ["PATH"]
        if path.find(self._path) != -1:
            return
        path += ":" + self._path
        os.environ["PATH"] = path


    # archives -------------------------------------------------------------------------------------

    def Extract(self, destDirectory):
        """
        extract archive (zip or tar) to destination directory
        """
        if self.GetExtension() in ("zip",):
            return self.Unzip(destDirectory)
        return self.Untar(destDirectory)


    def Unzip(self, destDirectory):
        """
        unzip to destination directory
        """
        zfobj = zipfile.ZipFile(self._path)
        for name in zfobj.namelist():
            while name.startswith(os.sep):
                name = name[1:]
            name = name.replace("../","")
            if not name.endswith('/'): 
                root, file = os.path.split(name)
                directory = os.path.normpath(os.path.join(destDirectory, root))
                if not os.path.isdir(directory):
                    os.makedirs(directory)
                outfile = open(os.path.join(destDirectory, name), "wb")
                outfile.write(zfobj.read(name))
                outfile.close()

        return True


    def Untar(self, destDirectory):
        """
        unzip to destination directory
        """
        tar = tarfile.open(self._path, "r:gz")
        tar.extractall(destDirectory)
        return True


    def Pack(self, add=[], rootDir=""):
        """
        create a zip or tar archive from file/directory list.
        to store files with relative directory set rootdir
        to base directory for files 
        format is choosen from extension
        """
        if self.GetExtension()=="zip":
            return self.Zip(add, rootDir)
        return self.Tar(add, rootDir)

    
    def Zip(self, add=[], rootDir=""):
        zfobj = zipfile.ZipFile(self._path, mode="w")
        if rootDir != "" and not rootDir.endswith(os.sep):
            rootDir += os.sep
        for path in add:
            if rootDir and not path.startswith(rootDir):
                path = rootDir + path
            if os.path.isfile(path):
                zfobj.write(path, path[len(rootDir):], zipfile.ZIP_DEFLATED)
            else:
                self._ZipPath(zfobj, path, rootDir)
        zfobj.close()
        return True


    def _ZipPath(self, zfobj, path, rootDir):
        temp = self._path
        self._path = path
        self.SetName("*")
        f = self.FindFirst(inSearchSubDirs = True, inReturnDirectories = False)
        if not f:
            self._path = temp
            return False
        while f:
            if os.path.isfile(self._path):
                zfobj.write(self._path, self._path[len(rootDir):], zipfile.ZIP_DEFLATED)
            f = self.FindNext()
        self._path = temp
        return True
        

    def Tar(self, add=[], rootDir=""):
        files = ""
        for f in add:
            files += "'%s' "%(f)
        cmd = """cvzf %(path)s %(files)s""" % {"path": self._path, "files": str(files)}
        s = popen("tar " + cmd, "r")
        r = ""
        while 1:
            d = s.readline()
            if not d or d == ".\n" or d == ".\r":
                break
            r += d
        return True


    # directory rotation ----------------------------------------------------------------------------

    def AppendDirectoryRotation(self, period):
        d = datetime.now()
        if period == "day":
            return True
        elif period == "week":
            name = d.strftime("%A")
        elif period == "month":
            name = d.strftime("%d")
        elif period == "year-month":
            name = d.strftime("%Y-%m")
        elif period == "timestamp":
            name = d.strftime("%Y-%m-%d_%H%M%S")
        self.AppendSeperator()
        self.AppendDirectory(name)
        return True


    # internal -------------------------------------------------------------------------------

    def _SubList(self, path, dirs, level):
        self._path = path
        l = self.GetSubDirList(True)
        if len(dirs) <= level:
            dirs.append(l)
        else:
            dirs[level] = dirs[level] + l
        for p in l:
            dirs = self._SubList(p, dirs, level+1)
        return dirs


    # windows specific -------------------------------------------------------------------------------

    def _FindFilesWin(self):
        """return list """
        return win32api.FindFiles(self._path)


    def _FindFirstWin(self, inSearchSubDirs = False, inReturnDirectories = False):
        """return bool """
        try:    self._pFindList = win32api.FindFiles(self._path)
        except: return False
        self._pFindPos = -1
        self._pFindDirList = []
        self.pFindFile = self.GetNameExtension()
        self._pSearchSubDirs = inSearchSubDirs
        self._pReturnDirs = inReturnDirectories
        sys.setrecursionlimit(100000)
        return self.FindNext()


    def _FindNextWin(self):
        """return bool """
        if self._pFindList == None:
            return False

        self._pFindPos += 1
        if len(self._pFindList) == 0 or self._pFindPos >= len(self._pFindList):
            if not self._pSearchSubDirs:
                self.FindClose()
                return False

            aSubDirList = self.GetSubDirList(True)                   # search subdirectories
            self._pFindDirList.extend(aSubDirList)
            if len(self._pFindDirList) == 0:
                self.FindClose()
                return False
            self._pFindDirList.sort()

            self._path = self._pFindDirList.pop(0)                   # get NEXT directory
            self.AppendSeperator()
            self.SetNameExtension(self.pFindFile)
            self._pFindList = win32api.FindFiles(self._path)         # start find in new directory
            self._pFindPos = -1
            return self.FindNext()

        if ((self._pFindList[self._pFindPos][0] & win32con.FILE_ATTRIBUTE_DIRECTORY) >> 4):
            if not self._pReturnDirs:                                 # skip directories
                return self.FindNext()
            if self._pFindList[self._pFindPos][8] in ("..", "."):    # parent reference
                return self.FindNext()

        self.SetNameExtension(self._pFindList[self._pFindPos][8])

        return True


    def _GetSubDirListWin(self, inAbsolut = False):
        """(bool inAbsolut) return list
        Excludes files with attribute hidden from search
        """
        aP = self.GetPath()
        aP += "*.*"
        aL = win32api.FindFiles(aP)
        aDirs = []
        for aFI in aL:
            if aFI[8] == "." or aFI[8] == "..":
                continue
            if ((aFI[0] & win32con.FILE_ATTRIBUTE_DIRECTORY) >> 4):
                if ((aFI[0] & win32con.FILE_ATTRIBUTE_HIDDEN) >> 1):        # exclude files with attribute hidden from search
                    continue
                if inAbsolut:
                    aDirs.append(self.GetPath() + aFI[8] + os.sep)
                else:
                    aDirs.append(aFI[8] + os.sep)
        return aDirs


    # unix specific -------------------------------------------------------------------------------

    def _FindFilesUnix(self, regex = False):
        """return list """
        p = self.GetPath()
        for root, dirs, files in os.walk(p):
            fl = []
            for f in files:
                if not self._PathMatch(self.GetNameExtension(), f, regex):
                    continue
                fl.append(f)
            return fl
        return []


    def _FindFirstUnix(self, inSearchSubDirs = False, inReturnDirectories = False, regex = False):
        """return bool """
        self._pFindPos = -1
        self.regex = regex
        self._pFindDirList = []
        self.pFindFile = self.GetNameExtension()
        self._pSearchSubDirs = inSearchSubDirs
        self._pReturnDirs = inReturnDirectories
        sys.setrecursionlimit(100000)
        self._pFindList = self._FindFilesUnix(regex)
        return self._FindNextUnix()


    def _FindNextUnix(self):
        """return bool """
        if self._pFindList == None:
            return False
        if self._pFindDirList == None:
            return False

        self._pFindPos += 1
        while len(self._pFindList) == 0 or self._pFindPos >= len(self._pFindList):
            if not self._pSearchSubDirs:
                self.FindClose()
                return False

            aSubDirList = self._GetSubDirListUnix(True)                   # search subdirectories
            self._pFindDirList.extend(aSubDirList)
            if len(self._pFindDirList) == 0:
                self.FindClose()
                return False
            self._pFindDirList.sort()

            self._path = self._pFindDirList.pop(0)                   # get NEXT directory
            #print self._path
            self.AppendSeperator()
            self.SetNameExtension(self.pFindFile)
            self._pFindList = self._FindFilesUnix(self.regex)        # start find in new directory
            self._pFindPos = -1
            #return self.FindNext()

        self.SetNameExtension(self._pFindList[self._pFindPos])

        return True


    def _GetSubDirListUnix(self, inAbsolut = False):
        """(bool inAbsolut) return list
        Excludes files with attribute hidden from search
        """
        aDirs = []
        p = self.GetPath()
        for root, dirs, files in os.walk(p):
            for d in dirs:
                if inAbsolut:
                    aDirs.append(p + d + os.sep)
                else:
                    aDirs.append(d + os.sep)
            return aDirs
        return []


    def _PathMatch(self, path1, path2, regex):
        if not regex and path1.find("*") == -1:
            return True
        if not regex:
            s1=path1.split("*")
            #if s1[-1] != path2[-len(s1[-1]):]:
            #    return False
            path1 = path1.replace("\\", "\\\\")
            path1 = path1.replace(".", "\.")
            path1 = path1.replace("*", ".*")
        p = re.compile(path1, re.I)
        r = p.match(path2)
        return r


# --------------------------------------------------------------------------------

class DvDirCleaner(object):
    """
    Clean up directories

    baseDirectories
    regex
    """

    def __init__(self, baseDirectories, regex = False):
        """
        """
        if type(baseDirectories) == type(""):
            baseDirectories = [baseDirectories]
        self.baseDirectories = baseDirectories
        self.regex = regex


    def DeleteNotReferenced(self, searchDirectories, skipSearchExtensions = ["jpg","gif","pdf","jpeg","exe","bmp"], delete = False, searchSubdirectories = True):
        """
        Cleans directories and deletes all files which are not referenced.
        Directories to be cleaned are passed as baseDirectories. References
        are searched for in searchDirectories.
        """
        if type(searchDirectories) == type(""):
            searchDirectories = [searchDirectories]
        self.searchDirectories = searchDirectories
        self.skipSearchExtensions = skipSearchExtensions

        # get files to search reference for
        files = {}
        for base in self.baseDirectories:
            path = DvPath(base)
            if not path.FindFirst(searchSubdirectories, self.regex):
                continue
            files[str(path)] = 0
            while path.FindNext():
                files[str(path)] = 0

        if files == {}:
            return [], []

        # loop search directories
        checked = []
        for search in self.searchDirectories:
            search = DvPath(search)
            if not search.FindFirst(searchSubdirectories, self.regex):
                continue
            if search.GetExtension().lower() not in self.skipSearchExtensions:
                files = self._ProcessFile(search, files)
                checked.append(str(search))
            while search.FindNext():
                if search.GetExtension().lower() not in self.skipSearchExtensions:
                    files = self._ProcessFile(search, files)
                checked.append(str(search))

        # list not referenced
        l = []
        for ref in files.keys():
            if files[ref] == 0:
                l.append(ref)
        files = l

        # delete not referenced
        if delete:
            self._DeleteFiles(files)

            # remove unused references in files in base directories
            # run again until all not referenced are deleted
            if len(files) != 0:
                f2, c2 = self.DeleteNotReferenced(searchDirectories,skipSearchExtensions=skipSearchExtensions,  searchSubdirectories=searchSubdirectories, delete=delete)
                for f in f2:
                    if not f in files:
                        files.append(f)

        return files, checked


    def DeleteNotListed(self, fileList, skipSearchExtensions = [], delete = False, searchSubdirectories = True):
        """
        Processes each file in directory/subdirectories and search for reference in
        files in same or different directories. Not referenced files can be deleted.
        """
        # get files not in List
        files = []
        for base in self.baseDirectories:
            path = DvPath(base)
            if not path.FindFirst(searchSubdirectories, self.regex):
                continue
            if not path.GetExtension() in skipSearchExtensions and not str(path) in fileList:
                files.append(str(path))
            while path.FindNext():
                if not path.GetExtension() in skipSearchExtensions and not str(path) in fileList:
                    files.append(str(path))

        if not delete:
            return files

        # delete not referenced
        self._DeleteFiles(files)

        return files


    def MoveFilesList(self, fileList, bakupDirectory):
        """
        move the files in the list to a bakup directory
        uses self.baseDirectories to get relative path of files
        returns list with errors
        """
        err = []
        for f in fileList:
            rel = ""
            for b in self.baseDirectories:
                if f.find(b) == -1:
                    continue
                rel = f.replace(b, "")
                break
            file = DvPath(f)
            bakup = DvPath(bakupDirectory)
            bakup.Append(rel)
            if not file.Move(str(bakup)):
                err.append(str(bakup))
        return err


    def DeleteFiles(self, subdirectories = True, bakupDirectory = None):
        """
        delete all files matching base directories name/pattern
        if bakupDirectory is not none: files are moved to the directory
        returns list of deleted files
        """
        files = []
        for base in self.baseDirectories:
            path = DvPath(base)
            #path.Append
            if not path.FindFirst(subdirectories, self.regex):
                continue
            files.append(str(path))
            while path.FindNext():
                files.append(str(path))
        for f in files:
            p = DvPath(f)
            try:
                p.Delete()
            except:
                pass
        return files


    def DeleteEmptyDirectories(self):
        """
        delete empty subdirectories in base directories
        """
        n = 0
        for base in self.baseDirectories:
            path = DvPath(base)
            n += path.DeleteEmptyDirectories()
        return n



    def _ProcessFile(self, file, references):
        # load file data
        name = file.GetNameExtension()
        import utils
        data = utils.LoadFromFile(str(file))
        # loop files
        for ref in references.keys():
            if ref == str(file):
                continue
            refPath = DvPath(ref)
            refName = refPath.GetNameExtension()
            if data.find(refName) != -1:
                references[ref] = references[ref] + 1
        return references


    def _DeleteFiles(self, files):
        for f in files:
            p = DvPath(f)
            try:
                p.Delete()
            except:
                pass

