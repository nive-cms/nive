# -*- coding: latin-1 -*-

import copy, time
import unittest


from nive.definitions import FieldConf
from nive.utils.dataPool2.dbManager import *
from nive.utils.path import DvPath

dbpath = ":memory:"
tablename = "testtable"
tablename2 = "testtable2"
columns = ("ftext","fnumber","fdate","flist","fmselect","funit","funitlist")

SystemFlds = (
FieldConf(**{"id": "id",            "datatype": "number",   "size": 8,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1000, "name": "ID",             "description": ""}),
FieldConf(**{"id": "title",         "datatype": "string",   "size": 255,"default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1100, "name": "Title",            "description": ""}),
FieldConf(**{"id": "pool_type",     "datatype": "list",     "size": 35, "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1200, "name": "Type",              "description": ""}),
FieldConf(**{"id": "pool_category", "datatype": "list",     "size": 35, "default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1300, "name": "Category",          "description": ""}),
FieldConf(**{"id": "pool_filename", "datatype": "string",   "size": 255,"default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1400, "name": "Filename",         "description": ""}),
FieldConf(**{"id": "pool_create",   "datatype": "datetime", "size": 0,  "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1500, "name": "Created",         "description": ""}),
FieldConf(**{"id": "pool_change",   "datatype": "datetime", "size": 0,  "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1600, "name": "Changed",         "description": ""}),
FieldConf(**{"id": "pool_createdby","datatype": "string",   "size": 35, "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1700, "name": "Created by",     "description": ""}),
FieldConf(**{"id": "pool_changedby","datatype": "string",   "size": 35, "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1800, "name": "Changed by",        "description": ""}),
FieldConf(**{"id": "pool_wfp",      "datatype": "list",     "size": 35, "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1900, "name": "Workflow Process",     "description": ""}),
FieldConf(**{"id": "pool_wfa",      "datatype": "list",     "size": 35, "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  2000, "name": "Workflow Activity",    "description": ""}),
FieldConf(**{"id": "pool_state",    "datatype": "number",   "size": 4,  "default": 1,     "required": 0,     "readonly": 1, "settings": {}, "sort":  2100, "name": "State",             "description": ""}),
FieldConf(**{"id": "pool_sort",     "datatype": "number",   "size": 8,  "default": 0,     "required": 0,     "readonly": 1, "settings": {}, "sort":  2200, "name": "Sort",             "description": ""}),
FieldConf(**{"id": "pool_unitref",  "datatype": "number",   "size": 8,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  5000, "name": "Reference",         "description": ""}),
FieldConf(**{"id": "pool_stag",     "datatype": "number",   "size": 4,  "default": 0,     "required": 0,     "readonly": 1, "settings": {}, "sort":  5100, "name": "Select Number",     "description": ""}),
FieldConf(**{"id": "pool_datatbl",  "datatype": "string",   "size": 35, "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  5200, "name": "Data Table Name",    "description": ""}),
)

class Sqlite3Test(unittest.TestCase):

    def setUp(self):
        p=DvPath(dbpath)
        p.Delete()
        self.db = Sqlite3Manager()
        self.db.Connect(dbpath)
        pass

    def tearDown(self):
        self.db.Close()
        p=DvPath(dbpath)
        p.Delete()
        pass

    def test_Connect(self):
        db = Sqlite3Manager()
        self.assert_(db.Connect(dbpath))
        self.assert_(db.IsDB())
        db.Close()
        self.assert_(not db.IsDB())
        

    def test_CreateTable(self):
        try:
            self.db.DeleteTable(tablename)
        except:
            pass
        self.assertFalse(self.db.IsTable(tablename))
        self.assert_(self.db.CreateTable(tablename))
        self.assert_(self.db.IsTable(tablename))
        self.assert_(self.db.DeleteTable(tablename))
        self.assertFalse(self.db.IsTable(tablename))

        self.assert_(self.db.CreateTable(tablename))
        self.assert_(self.db.IsTable(tablename))
        self.assert_(self.db.RenameTable(tablename, tablename2))
        self.assert_(self.db.DeleteTable(tablename2))
        self.assertFalse(self.db.IsTable(tablename))
        self.assertFalse(self.db.IsTable(tablename2))


    def test_CreateColumns(self):
        self._createtbl()
        self._createcols()
        self._deltable()


    def test_CreateColumns2(self):
        self._createtbl()
        self._createcols()
        #self.db.Close()
        #self.db.Connect(dbpath)
        for col in columns:
            self.assert_(self.db.IsColumn(tablename, col))
        self._deltable()


    def test_CreateColumnsStructure(self):
        for f in SystemFlds:
            self.assert_(self.db.ConvertConfToColumnOptions(f))
        self._createtbl()
        self.assert_(self.db.UpdateStructure(tablename, SystemFlds))
        for f in SystemFlds:
            self.assert_(self.db.IsColumn(tablename, f["id"]))
        self._deltable()


    
    def _createtbl(self):
        try:
            self.db.DeleteTable(tablename)
        except:
            pass
        self.assertFalse(self.db.IsTable(tablename))
        self.assert_(self.db.CreateTable(tablename))
        self.assert_(self.db.IsTable(tablename))

        
    def _createcols(self):
        for col in columns:
            self.assert_(not self.db.IsColumn(tablename, col))
            self.assert_(self.db.CreateColumn(tablename, col))
            self.assert_(self.db.IsColumn(tablename, col))
        
        
    def _deltable(self):
        self.db.DeleteTable(tablename)
        self.assertFalse(self.db.IsTable(tablename))
        
        
        
def __test():
    unittest.main()

if __name__ == '__main__':
    __test()
