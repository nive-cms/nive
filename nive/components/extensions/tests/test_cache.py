

import unittest

from nive.definitions import *

from nive.components.extensions.cache import *

from nive.tests import db_app


class testobj(object, ContainerCache):
    type = "object"
    def GetTypeID(self):
        return self.type
        
        

class ContainerCache(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    
    def test_1(self):
        obj = testobj()
        obj2 = testobj()
        
        self.assert_(obj.Cache(obj2, "cid"))
        self.assert_(obj.GetFromCache("cid")==obj2)
        self.assert_(len(obj.GetAllFromCache())==1)
        self.assert_(obj.RemoveCache("cid"))
        self.assert_(len(obj.GetAllFromCache())==0)
        self.assert_(obj.GetFromCache(id="cid")==None)


    def test_2(self):
        obj = testobj()
        obj.cacheTypes = ["object"]
        obj2 = testobj()
        obj3 = testobj()
        obj3.type = "aaaaa"
        
        self.assert_(obj.Cache(obj2, "cid"))
        self.assert_(obj.GetFromCache("cid")==obj2)
        self.assert_(len(obj.GetAllFromCache())==1)
        self.assert_(obj.RemoveCache("cid"))
        self.assert_(len(obj.GetAllFromCache())==0)
        self.assert_(obj.GetFromCache(id="cid")==None)
        
        
    def test_3(self):
        obj = testobj()
        obj.cacheTypes = ["object"]
        obj2 = testobj()
        obj2.type = "aaaaa"
        
        self.assertFalse(obj.Cache(obj2, "cid"))
        self.assert_(obj.GetFromCache("cid")!=obj2)
        self.assert_(len(obj.GetAllFromCache())==0)
