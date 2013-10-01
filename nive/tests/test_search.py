
import time
import unittest

from nive.security import User
from nive.definitions import *

import db_app

# -----------------------------------------------------------------

class SearchTest_db(unittest.TestCase):

    def setUp(self):
        self.app = db_app.app_db()
        r=self.app.root()
    
        # create three levels of entries
        level1 = 5
        level2 = 5
        level3_1 = 5
        level3_2 = 5
        c=r
        ids=[]
        n=0
        user = User(u"test")
        for i in range(0,level1):
            o=db_app.createObj1(c)
            n+=1
            ids.append(o.id)
            for i2 in range(0,level2):
                o2=db_app.createObj1(o)
                n+=1
                for i3 in range(0,level3_1):
                    db_app.createObj1(o2)
                    n+=1
                for i3 in range(0,level3_2):
                    o4 = db_app.createObj2(o2)
                    id = o4.id
                    n+=1
        self.ids = ids
        self.lastid = id

    def tearDown(self):
        user = User(u"test")
        r=self.app.root()
        for id in self.ids:
            r.Delete(id, user=user)
        self.app.Close()

    
    def test_search(self):
        r = self.app.root()
        #test_tree
        self.assert_(len(r.TreeParentIDs(self.lastid))==2)
        self.assert_(len(r.TreeParentTitles(self.lastid))==2)
        self.assert_(len(r.TreeParentIDs(self.ids[3]))==0)
        self.assert_(len(r.TreeParentTitles(self.ids[3]))==0)

        #test_select
        self.assert_(r.Select())
        self.assert_(r.SelectDict())
        self.assert_(r.Select(pool_type="type1"))
        self.assert_(r.SelectDict(pool_type="type1"))
        self.assertFalse(r.Select(parameter={"pool_type": "type"}, operators={"pool_type": "="}, sort="id", ascending = 0))
        self.assertFalse(r.SelectDict(parameter={"pool_type": "type"}, operators={"pool_type": "="}, sort="id", ascending = 0))
        self.assert_(r.Select(parameter={"pool_type": "type"}, operators={"pool_type": "LIKE"}, sort="id", ascending = 0))
        self.assert_(r.SelectDict(parameter={"pool_type": "type"}, operators={"pool_type": "LIKE"}, sort="id", ascending = 0))
        self.assert_(r.Select(pool_type="type1", parameter={}, fields=["id","pool_filename","ftext","fnumber","fdate"], start=10, max=1))
        self.assert_(r.SelectDict(pool_type="type1", parameter={}, fields=["id","pool_filename","ftext","fnumber","fdate"], start=10, max=1))
        self.assert_(r.Select(parameter={"pool_type": "notype", "pool_filename": "others"}, logicalOperator="or", operators={"pool_type":"LIKE", "pool_filename":"LIKE"}))
        self.assert_(r.SelectDict(parameter={"pool_type": "notype", "pool_filename": "others"}, logicalOperator="or", operators={"pool_type":"LIKE", "pool_filename":"LIKE"}))
        self.assertFalse(r.Select(parameter={"pool_type": "notype", "pool_filename": "notitle"}, logicalOperator="or", operators={"pool_type":"LIKE", "pool_filename":"LIKE"}))
        self.assertFalse(r.SelectDict(parameter={"pool_type": "notype", "pool_filename": "notitle"}, logicalOperator="or", operators={"pool_type":"LIKE", "pool_filename":"LIKE"}))
        self.assert_(r.Select(groupby="pool_filename"))
        self.assert_(r.SelectDict(groupby="pool_filename"))
        self.assert_(r.Select(condition="id > 23"))
        self.assert_(r.SelectDict(condition="id > 23"))

        #test_codelists
        pool_type="type1"
        name_field="pool_filename"
        self.assert_(r.GetEntriesAsCodeList(pool_type, name_field))
        self.assert_(r.GetEntriesAsCodeList2(name_field))
        self.assert_(r.GetGroupAsCodeList(pool_type, name_field))
        self.assert_(r.GetGroupAsCodeList2(name_field))
        parameter = {"pool_state":1}
        operators = {"pool_state":"<="}
        self.assert_(r.GetEntriesAsCodeList(pool_type, name_field, parameter= parameter, operators = operators))
        self.assert_(r.GetEntriesAsCodeList2(name_field, parameter= parameter, operators = operators))
        self.assert_(r.GetGroupAsCodeList(pool_type, name_field, parameter= parameter, operators = operators))
        self.assert_(r.GetGroupAsCodeList2(name_field, parameter= parameter, operators = operators))

        #test_conversion
        pool_type="type1"
        r.FilenameToID("number1")
        r.IDToFilename(self.lastid)
        dataref = r.Select(parameter={"pool_type": pool_type}, fields=["id","pool_dataref"], max=1)[0]
        self.assert_(r.ConvertDatarefToID(pool_type, dataref[1])==dataref[0])
        self.assert_(r.GetMaxID())

        #test_refs
        self.assert_(r.GetReferences(35))
        self.assert_(r.GetReferences(35, types=["type1"]))

        #test_search
        r = self.app.root()
        parameter = {"pool_state":1}
        operators = {"pool_state":"<="}
        pool_type = "type1"
        fields1 = ["id","pool_filename","pool_state","pool_unitref"]
        fields2 = ["id","pool_filename","pool_state","pool_unitref","ftext"]
        fields3 = ["id","ftext"]

        d=r.Select(fields=["-count(*)"])
        self.assert_(r.Select(parameter=parameter, fields=fields1, start=0, max=100))
        self.assert_(r.Select(pool_type=pool_type, parameter=parameter, fields=fields2, start = 0, max=100, operators=operators))
        self.assert_(r.SelectDict(parameter=parameter, fields=fields1, start=0, max=100))
        self.assert_(r.SelectDict(pool_type=pool_type, parameter=parameter, fields=fields2, start = 0, max=100, operators=operators))

        self.assert_(r.Search(parameter, fields = fields1, sort = "pool_filename", ascending = 1, start = 0, max = 100)["count"])
        self.assert_(r.SearchType(pool_type, parameter, fields = fields2, sort = "pool_filename", ascending = 1, start = 0, max = 100, operators=operators)["count"])
        self.assert_(r.SearchData(pool_type, {}, fields = fields3, sort = "id", ascending = 1, start = 0, max = 100, operators={})["count"])
        self.assert_(r.SearchFulltext("text", fields = fields1, sort = "pool_filename", ascending = 1, start = 0, max = 300)) #["count"]
        self.assert_(r.SearchFulltextType(pool_type, "text", fields = fields2, sort = "pool_filename", ascending = 1, start = 0, max = 300))   #["count"]
        r.SearchFilename("file1.txt", parameter, fields = [], sort = "pool_filename", ascending = 1, start = 0, max = 100, operators=operators)
        
        #test_listitems
        self.assert_(len(r.LoadListItems(self.app.GetFld("pool_type"), obj=None, pool_type=None, force=True))==3)
        r.LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"users"}))
        self.assert_(r.LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"groups"})))
        self.assert_(r.LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"languages"})))
        self.assert_(r.LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"countries"})))
        self.assert_(r.LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"types"})))
        self.assert_(r.LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"meta"})))
        #self.assert_(r.LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"type:type1"})))

