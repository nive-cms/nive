

import copy, time, StringIO
import unittest
from datetime import datetime
from datetime import date

from nive.utils.dataPool2.structure import *

from nive.tests import __local

from nive.utils.dataPool2.tests import test_Base


ftypes = {}
ftypes[u"data2"] = {u"fstr":"string",
                    u"ftext":"text", 
                    u"ftime":"timestamp", 
                    u"fmselection":"mselection",
                    u"fmcheckboxes":"mcheckboxes", 
                    u"furllist":"urllist", 
                    u"funitlist":"unitlist",
                    u"fbool":"bool",
                    u"fjson":"json"}

ftypes[u"pool_meta"] = {}
for i in test_Base.SystemFlds:
    ftypes[u"pool_meta"][i["id"]] = i

class StructureTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_set1(self):
        structure = PoolStructure(structure=test_Base.struct, 
                                  fieldtypes=ftypes, 
                                  stdMeta=[u"id",u"pool_type"])
        self.assert_(structure.get(u"pool_meta"))
        self.assert_(len(structure.get(u"pool_meta")) == len(test_Base.struct[u"pool_meta"]))
        self.assert_(len(structure.get(u"data1"))==len(test_Base.struct[u"data1"]))
        self.assert_(len(structure.get(u"data2"))==len(test_Base.struct[u"data2"]))
        self.assert_(len(structure.stdMeta)==2)
        self.assert_(structure.fieldtypes[u"data2"][u"fstr"]=="string")
        self.assert_(structure.codepage==u"utf-8")

    def test_set2(self):
        structure = PoolStructure()
        structure.Init(structure=test_Base.struct, 
                       fieldtypes=ftypes, 
                       codepage="latin-1")
        self.assert_(structure.get(u"pool_meta"))
        self.assert_(len(structure.get(u"pool_meta")) == len(test_Base.struct[u"pool_meta"]))
        self.assert_(len(structure.get(u"data1"))==len(test_Base.struct[u"data1"]))
        self.assert_(len(structure.get(u"data2"))==len(test_Base.struct[u"data2"]))
        self.assert_(len(structure.stdMeta)==0)
        self.assert_(structure.fieldtypes[u"data2"][u"fstr"]=="string")
        self.assert_(structure.codepage==u"latin-1")
        
    def test_set3(self):
        structure = PoolStructure()
        structure.Init(structure={u"pool_meta": [], u"data1": [], u"data2": []}, 
                       fieldtypes=ftypes, 
                       codepage="latin-1")
        self.assert_(structure.get(u"pool_meta"))
        self.assert_(len(structure.get(u"pool_meta"))==2)
        self.assert_(len(structure.get(u"data1"))==0)
        self.assert_(len(structure.get(u"data2"))==0)
        


    def test_empty(self):
        structure = PoolStructure()
        self.assert_(structure.IsEmpty())


    def test_func(self):
        structure = PoolStructure(structure=test_Base.struct, 
                                  fieldtypes=ftypes, 
                                  stdMeta=[u"id",u"pool_type"])
        self.assertFalse(structure.IsEmpty())
        
        self.assert_(structure.get("pool_meta"))
        self.assert_(structure.get("none","aaa")=="aaa")
        self.assert_(structure["pool_meta"])
        self.assert_(structure["data1"])
        self.assert_(structure["data2"])
        self.assert_(structure.has_key("data2"))
        self.assert_(len(structure.keys())==3)
        
        

        
class ConversionTest(unittest.TestCase):

    def setUp(self):
        self.structure = PoolStructure(structure=test_Base.struct, 
                                       fieldtypes=ftypes, 
                                       stdMeta=[u"id",u"pool_type"])

    def tearDown(self):
        pass


    def test_serialize_notype(self):
        self.assert_(self.structure.serialize(u"pool_meta", u"somevalue", 123)==123)
        self.assert_(isinstance(self.structure.serialize(u"pool_meta", u"somevalue", "123"), unicode))
        value = datetime.now()
        self.assert_(self.structure.serialize(u"pool_meta", u"somevalue", value)==value.strftime("%Y-%m-%d %H:%M:%S"))
        value = ("aaa","bbb")
        self.assert_(self.structure.serialize(u"pool_meta", u"somevalue", value).startswith(u"_json_"))
        value = (u"aaa",u"bbb")
        self.assert_(self.structure.serialize(u"pool_meta", u"somevalue", value).startswith(u"_json_"))
        value = [1,2,3]
        self.assert_(self.structure.serialize(u"pool_meta", u"somevalue", value).startswith(u"_json_"))
        
    def test_se_mselection(self):
        v = {u"id":u"123", u"pool_sort":u"123.12", u"pool_wfa":["value"], u"somevalue": "test"}
        values = self.structure.serialize(u"pool_meta", None, v)
        self.assert_(values[u"id"]==123)
        self.assert_(values[u"pool_sort"]==123.12)
        self.assert_(values[u"pool_wfa"]==u"value")        

    def test_se_number(self):
        self.assert_(self.structure.serialize(u"pool_meta", u"id", 123)==123)
        self.assert_(self.structure.serialize(u"pool_meta", u"id", u"123")==123)
        self.assert_(self.structure.serialize(u"pool_meta", u"id", "123")==123)
        self.assert_(self.structure.serialize(u"pool_meta", u"id", 123.12)==123)

    def test_se_float(self):
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_sort", 123)==123.0)
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_sort", u"123.12")==123.12)
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_sort", "123.0")==123.0)
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_sort", 123.12)==123.12)

    def test_se_date(self):
        value = datetime.now()
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_change", value)==unicode(value))
        value = date.today()
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_create", value)==unicode(value))
        value = time.time()
        self.assert_(self.structure.serialize(u"data2", u"ftime", value)==unicode(value))

    def test_se_list(self):
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_wfa", u"value")==u"value")
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_wfa", ["value"])=="value")
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_wfa", ())=="")

    def test_se_mlist(self):
        self.assert_(self.structure.serialize(u"data2", u"fmselection", u"value"))
        self.assert_(self.structure.serialize(u"data2", u"fmselection", [u"value"]))
        self.assert_(self.structure.serialize(u"data2", u"fmselection", ("value",)))
        self.assertFalse(self.structure.serialize(u"data2", u"fmselection", u""))
        
        self.assert_(self.structure.serialize(u"data2", u"mcheckboxes", u"value"))
        self.assert_(self.structure.serialize(u"data2", u"furllist", u"value"))
        self.assert_(self.structure.serialize(u"data2", u"funitlist", u"value"))

    def test_se_bool(self):
        self.assert_(self.structure.serialize(u"data2", u"fbool", u"true")==1)
        self.assert_(self.structure.serialize(u"data2", u"fbool", u"false")==0)
        self.assert_(self.structure.serialize(u"data2", u"fbool", True)==1)
        self.assert_(self.structure.serialize(u"data2", u"fbool", False)==0)
        self.assert_(self.structure.serialize(u"data2", u"fbool", u"True")==1)
        self.assert_(self.structure.serialize(u"data2", u"fbool", u"False")==0)
        self.assert_(self.structure.serialize(u"data2", u"fbool", ("???",))==0)

    def test_se_json(self):
        self.assert_(self.structure.serialize(u"data2", u"fjson", {"a":123,"b":"aaa"}))
        self.assert_(json.loads(self.structure.serialize(u"data2", u"fjson", {"a":123,"b":"aaa"}))["a"]==123)
        self.assert_(json.loads(self.structure.serialize(u"data2", u"fjson", {"a":123,"b":"aaa"}))["b"]==u"aaa")
    
    
    def test_deserialize_notype(self):
        value = u"_json_"+json.dumps(("aaa","bbb"))
        self.assert_(self.structure.deserialize(u"pool_meta", u"somevalue", value)[0]==u"aaa")
        self.assert_(self.structure.deserialize(u"pool_meta", u"somevalue", "somevalue")==u"somevalue")
        
    def test_ds_mselection(self):
        v = {u"fmselection": json.dumps(["aaa","bbb"]),u"furllist":json.dumps(["aaa","bbb"]), u"somevalue": "test"}
        values = self.structure.deserialize(u"data2", None, v)
        self.assert_(values[u"fmselection"][0]=="aaa")
        self.assert_(values[u"furllist"][0]=="aaa")

    def test_ds_date(self):
        value = datetime.now()
        x=self.structure.deserialize(u"pool_meta", u"pool_change", unicode(value))
        self.assert_(x.strftime("%Y-%m-%d %H:%M:%S")==value.strftime("%Y-%m-%d %H:%M:%S"))
        value = date.today()
        x=self.structure.deserialize(u"pool_meta", u"pool_create", unicode(value))
        self.assert_(x.strftime("%Y-%m-%d")==value.strftime("%Y-%m-%d"))
        value = time.time()
        self.assert_(self.structure.deserialize(u"data2", u"ftime", value))

    def test_ds_mselection(self):
        self.assert_(self.structure.deserialize(u"data2", u"fmselection", json.dumps(["aaa","bbb"]))[0]=="aaa")
        self.assert_(self.structure.deserialize(u"data2", u"fmcheckboxes", json.dumps(["aaa","bbb"]))[0]=="aaa")
        self.assert_(self.structure.deserialize(u"data2", u"furllist", json.dumps(["aaa","bbb"]))[0]=="aaa")
        self.assert_(self.structure.deserialize(u"data2", u"funitlist", json.dumps(["aaa","bbb"]))[0]=="aaa")
        
    def test_ds_json(self):
        self.assert_(self.structure.deserialize(u"data2", u"fjson", json.dumps(["aaa","bbb"]))[0]=="aaa")



def seCallback(value, field):
    return value.swapcase()

def deCallback(value, field):
    return value.capitalize()



class CallbackTest(unittest.TestCase):

    def setUp(self):
        self.structure = PoolStructure(structure=test_Base.struct, 
                                       fieldtypes=ftypes, 
                                       stdMeta=[u"id",u"pool_type"])
        self.structure.serializeCallbacks = {"string": seCallback}
        self.structure.deserializeCallbacks = {"string": deCallback}


    def tearDown(self):
        pass


    def test_serialize_callback(self):
        self.assert_(self.structure.serialize(u"pool_meta", u"title", u"somevalue")==u"SOMEVALUE")
        self.assert_(self.structure.deserialize(u"pool_meta", u"title", u"somevalue")==u"Somevalue")

        
    def test_se_mselection(self):
        v = {u"id":u"123", u"pool_sort":u"123.12", u"pool_wfa":["value"], u"somevalue": "test"}
        values = self.structure.serialize(u"pool_meta", None, v)
        self.assert_(values[u"id"]==123)
        self.assert_(values[u"pool_sort"]==123.12)
        self.assert_(values[u"pool_wfa"]==u"value")        

    def test_se_number(self):
        self.assert_(self.structure.serialize(u"pool_meta", u"id", 123)==123)
        self.assert_(self.structure.serialize(u"pool_meta", u"id", u"123")==123)
        self.assert_(self.structure.serialize(u"pool_meta", u"id", "123")==123)
        self.assert_(self.structure.serialize(u"pool_meta", u"id", 123.12)==123)

    def test_se_float(self):
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_sort", 123)==123.0)
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_sort", u"123.12")==123.12)
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_sort", "123.0")==123.0)
        self.assert_(self.structure.serialize(u"pool_meta", u"pool_sort", 123.12)==123.12)

        