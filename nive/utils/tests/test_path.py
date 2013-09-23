# -*- coding: utf-8 -*-

import unittest
import os
import tempfile

from nive.utils.path import DvPath



class Path(unittest.TestCase):
    
    def setUp(self):
        self.base = os.sep+"tmp_nivepathtest_000"+os.sep
        self.name = self.base+"nofile.txt"
        pass
    
    def tearDown(self):
        pass
    
    
    def test_Create(self):
        n = self.name
        p = DvPath(n)
        self.assert_(p._path==n)
        self.assert_(str(p)==n)
        p = DvPath(DvPath(n))
        self.assert_(str(p)==n)
        p.SetStr(n)
        self.assert_(str(p)==n)
        self.assert_(p.GetStr()==n)
        
        
    def test_Set(self):
        n = self.name
        p = DvPath(n)
        self.assert_(str(p)==n)
        p.SetName("new")
        self.assert_(str(p)==self.base+"new.txt", str(p))
        p.SetExtension("png")
        self.assert_(str(p)==self.base+"new.png")
        p.SetNameExtension("another.txt")
        self.assert_(str(p)==self.base+"another.txt")
        

    def test_Dirs(self):
        n = self.base
        p = DvPath(n)
        self.assert_(str(p)==n)
        p.Append("another_dir"+os.sep+"and.file")
        self.assert_(str(p)==n+"another_dir"+os.sep+"and.file", str(p))
        p = DvPath(n)
        p.AppendDirectory("the_last")
        self.assert_(str(p)==n+"the_last"+os.sep, str(p))
        p.RemoveLastDirectory()
        self.assert_(str(p)==n)
        p = DvPath(n[:-1])
        p.AppendSeperator()
        self.assert_(str(p)==self.base)
        
        
            
    def test_Get(self):
        n = self.name
        p = DvPath(n)
        self.assert_(p.GetPath() == self.base)
        self.assert_(p.GetName() == "nofile")
        self.assert_(p.GetExtension() == "txt")
        self.assert_(p.GetNameExtension() == "nofile.txt")
        self.assert_(p.GetSize() == -1)
        self.assert_(p.GetLastDirectory() == "tmp_nivepathtest_000")
        p.IsFile()
        p.IsDirectory()
        p.Exists()
        p.IsValid()

    
    def test_fncs(self):
        temp = tempfile.gettempdir()
        p = DvPath(temp)
        p.AppendDirectory("tmp_nivepathtest_000")
        p.Delete(deleteSubdirs = True)
        p.CreateDirectories()
        self.assert_(p.IsDirectory())
        p.CreateDirectoriesExcp()
        p.Rename("tmp_nivepathtest_111")
        p.AppendDirectory("tmp_nivepathtest_000")
        p.AppendDirectory("tmp_nivepathtest_000")
        p.CreateDirectories()
        self.assert_(p.IsDirectory())
        p = DvPath(temp)
        p.AppendDirectory("tmp_nivepathtest_000")
        p.Delete(deleteSubdirs = False)
        self.assert_(p.IsDirectory()==True)
        p.Delete(deleteSubdirs = True)
        self.assert_(p.IsDirectory()==False)
        #p.Execute("cmd", returnStream = True)
            
            
            