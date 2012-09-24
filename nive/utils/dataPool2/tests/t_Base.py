# -*- coding: latin-1 -*-

import copy, time, StringIO
import unittest

from nive.utils.dataPool2.base import *


conf = {}
conf["root"] = u"/var/tmp/nive"
conf["log"] = u"/var/tmp/nive/sqllog.txt"
conf["codePage"] =    u"utf-8"
conf["dbCodePage"] = u"utf-8"
conf["backupVersions"] = 0
conf["useTrashcan"] = 0

conf["debug"] = 0


stdMeta = [u"id",
u"title",
u"pool_type",
u"pool_category",
u"pool_state",
u"pool_create",
u"pool_change",
u"pool_createdby",
u"pool_changedby",
u"pool_unitref",
u"pool_wfp",
u"pool_wfa",
u"pool_filename",
u"pool_stag",
u"pool_sort",
u"pool_datatbl",
u"pool_dataref"]

struct = {}
struct[u"pool_meta"] = stdMeta
struct[u"data1"] = (u"ftext",u"fnumber",u"fdate",u"flist",u"fmselect",u"funit",u"funitlist")
struct[u"data2"] = (u"fstr",u"ftext")

ftypes = {}
ftypes[u"data2"] = {u"fstr":"string" ,u"ftext":"text"}

SystemFlds = (
{"id": u"id",             "datatype": "number",     "size": 8,     "default": "",     "required": 0,     "readonly": 1, "settings": {}, "sort":  1000, "name": "ID",             "description": ""},
{"id": u"title",         "datatype": "string",     "size": 255,"default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1100, "name": "Title",            "description": ""},
{"id": u"pool_type",     "datatype": "list",     "size": 35, "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1200, "name": "Type",              "description": ""},
{"id": u"pool_category",    "datatype": "list",     "size": 35, "default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1300, "name": "Category",          "description": ""},
{"id": u"pool_filename",    "datatype": "string",     "size": 255,"default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1400, "name": "Filename",         "description": ""},
{"id": u"pool_create",    "datatype": "datetime",    "size": 0,    "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1500, "name": "Created",         "description": ""},
{"id": u"pool_change",    "datatype": "datetime",    "size": 0,     "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1600, "name": "Changed",         "description": ""},
{"id": u"pool_createdby","datatype": "string",    "size": 35, "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1700, "name": "Created by",     "description": ""},
{"id": u"pool_changedby","datatype": "string",    "size": 35, "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1800, "name": "Changed by",        "description": ""},
{"id": u"pool_wfp",        "datatype": "list",        "size": 35, "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1900, "name": "Workflow Process",     "description": ""},
{"id": u"pool_wfa",        "datatype": "list",        "size": 35, "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  2000, "name": "Workflow Activity",    "description": ""},
{"id": u"pool_state",    "datatype": "number",    "size": 4,     "default": 1,    "required": 0,     "readonly": 1, "settings": {}, "sort":  2100, "name": "State",             "description": ""},
{"id": u"pool_sort",        "datatype": "number",    "size": 8,     "default": 0,    "required": 0,     "readonly": 1, "settings": {}, "sort":  2200, "name": "Sort",             "description": ""},
{"id": u"pool_unitref",    "datatype": "number",     "size": 8,     "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  5000, "name": "Reference",         "description": ""},
{"id": u"pool_stag",        "datatype": "number",    "size": 4,     "default": 0,    "required": 0,     "readonly": 1, "settings": {}, "sort":  5100, "name": "Select Number",     "description": ""},
{"id": u"pool_datatbl",    "datatype": "string",    "size": 35, "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  5200, "name": "Data Table Name",    "description": ""},
{"id": u"pool_dataref",    "datatype": "number",    "size": 8,  "default":  0,    "required": 1,     "readonly": 1, "settings": {}, "sort":  5200, "name": "Data Table Name",    "description": ""},
)
Fulltext = ("id","text","files")
Files = ("id","filename","path","size","extension","filekey","version")

# test data ----------------------------------------------------------------------
data1_1 = {u"ftext": "this is text!",
             u"fnumber": 123456,
             u"fdate": "2008/06/23 16:55",
             u"flist": "item 1, item 2, item 3",
             u"fmselect": "item 5",
             u"funit": 35,
             u"funitlist": "34, 35, 36"}
data2_1 = {u"fstr": u"this is sting!",
             u"ftext": u"this is text!"}
meta1 = {u"title":"title "}
file1_1 = "File 1 content, text text text text."
file1_2 = "File 2 content, text text text text."


class StructureTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_set(self):
        self.structure = PoolStructure(structure=struct, fieldtypes=ftypes)
        self.assert_(self.structure.get(u"pool_meta"))
        self.assert_(len(self.structure.get(u"pool_meta")) == len(struct[u"pool_meta"]))
        self.assert_(len(self.structure.get(u"data1"))==len(struct[u"data1"]))
        self.assert_(len(self.structure.get(u"data2"))==len(struct[u"data2"]))



class BaseTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_structure(self):
        base = Base()
        base.structure.Init(structure=struct, stdMeta=struct[u"pool_meta"])
        self.assert_(len(base.structure.stdMeta)==len(struct[u"pool_meta"]))

    def test_config(self):
        base = Base(**conf)
        self.assert_(str(base.GetRoot()).find(conf["root"])!=-1)

    def test_database(self):
        base = Base()
        try:
            base.SetConnection(Connection())
        except TypeError:
            pass
        base.GetConnection()
        base.connection
        try:
            base.dbapi()
        except ConnectionError:
            pass
            
    def test_sql(self):
        base = Base()
        base.structure.Init(structure=struct, stdMeta=struct[u"pool_meta"])
        try:
            base.SetConnection(Connection())
        except TypeError:
            pass
        #GetSQLSelect(self, flds, parameter={}, dataTable = "", start = 0, max = 1000, **kw)
        flds = list(struct[u"pool_meta"])+list(struct[u"data1"])
        base.GetSQLSelect(struct[u"pool_meta"])
        base.GetSQLSelect(struct[u"pool_meta"], parameter={u"id":1})
        base.GetSQLSelect(struct[u"pool_meta"], parameter={u"pool_type":u"data1"})
        base.GetSQLSelect(flds, parameter={u"pool_type":u"data1"}, dataTable=u"data1")
        base.GetSQLSelect(list(struct[u"data1"])+[u"-count(*)"], parameter={u"id":123}, dataTable=u"data1", singleTable=1)
        base.GetSQLSelect(flds,
                          parameter={u"pool_type":u"data1"},
                          dataTable=u"data1",
                          operators={u"pool_type":u">"})
        base.GetSQLSelect(flds,
                          parameter={u"pool_type":u"data1"},
                          dataTable=u"data1",
                          operators={u"pool_type":u"="},
                          start=3,
                          max=20,
                          ascending=1,
                          sort=u"title, pool_type")
        base.GetSQLSelect(flds,
                          parameter={u"pool_type":u"data1",u"id":[1,2,3,4,5,6,7,8,9,0]},
                          dataTable=u"data1",
                          operators={u"pool_type":u"=", u"id":u"IN"},
                          jointype=u"LEFT",
                          logicalOperator=u"or",
                          condition=u"meta__.id > 2",
                          join=u"INNER JOIN table1 on (meta__.id=table1.id)",
                          groupby=u"pool_type",
                          start=3,
                          max=20,
                          sort=u"title, pool_type")
        base.GetFulltextSQL(u"test",
                            flds,
                          parameter={u"pool_type":u"data1",u"id":[1,2,3,4,5,6,7,8,9,0]},
                          dataTable=u"data1",
                          operators={u"pool_type":u"=", u"id":u"IN"},
                          jointype=u"LEFT",
                          logicalOperator=u"or",
                          condition=u"meta__.id > 2",
                          join=u"INNER JOIN table1 on (meta__.id=table1.id)",
                          groupby=u"pool_type",
                          start=3,
                          max=20,
                          sort=u"title, pool_type")





class FileTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_file1(self):
        file = File("aaa")
        file.update({"filename":"qqqq.png", "size": 123, "extension": "png"})
        self.assert_(file.filename=="qqqq.png")
        self.assert_(file.size==123)
        self.assert_(file.extension=="png")

    def test_file2(self):
        file = File("aaa", filename="qqqq.png", size=123, extension="png")
        self.assert_(file.filename=="qqqq.png")
        self.assert_(file.size==123)
        self.assert_(file.extension=="png")

    def test_file3(self):
        file = File("aaa", filename="import.zip", tempfile=True)
        self.assert_(file.filename=="import.zip")
        self.assert_(file.extension=="zip")
        self.assertRaises(IOError, file.read)

        from pkg_resources import resource_filename
        root = resource_filename('nive.utils.dataPool2', 'tests/')
        file = File("aaa")
        file.fromPath(root+"t_db.py")
        self.assert_(file.filename=="t_db.py")
        self.assert_(file.extension=="py")
        



def __test():
    unittest.main()

if __name__ == '__main__':
    __test()

