
import time
import unittest

from nive.application import *
from nive.definitions import *
from nive.helper import *
from nive.portal import Portal

from nive.tests.db_app import *


class containerTest_db:
    
    def setUp(self):
        self.app = app_db()
        self.remove=[]

    def tearDown(self):
        u = User(u"test")
        root = self.app.root()
        for r in self.remove:
            root.Delete(r, u)
        self.app.Close()


    def test_basics(self):
        #print "Testing shortcuts"
        a=self.app
        user = User(u"test")
        ccc = a.db.GetCountEntries()
        self.assert_(a.root())
        self.assert_(a.db)
        r = a.root()
        o1 = createObj1(r)
        o2 = createObj2(o1)
        id1 = o1.id
        id2 = o2.id
        self.remove.append(id1)
        self.assert_(a.obj(id1))
        self.assert_(r.__getitem__(str(id1)))
        self.assert_(r.obj(id1))
        self.assert_(o1.obj(id2))
        self.assert_(o1.db==a.db)
        self.assert_(r.db==a.db)
        
        self.assert_(r.IsTypeAllowed("type1", user=user))
        self.assert_(o1.IsTypeAllowed("type1", user=user))
        
        try:
            o2.IsTypeAllowed("type1", user=user)
            self.assert_(False, "ObjectBase is not a container: IsTypeAllowed")
        except AttributeError:
            pass
        self.assert_(r.GetAllowedTypes(user=user))
        self.assert_(o1.GetAllowedTypes(user=user))
        r.Delete(id1, user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        

    def test_createroots(self):
        #print "Testing root basics"
        a=self.app
        ccc = a.db.GetCountEntries()
        r=root(a)
        user = User(u"test")
        #rootValues()
        self.assert_(r.GetID()<=0)
        self.assert_(r.GetTypeID())
        self.assert_(r.GetTitle())
        self.assert_(r.GetPath())
        #rootParents()
        self.assert_(r.GetRoot()==r)
        self.assert_(r.GetApp())
        self.assert_(r.GetParent()==None)
        self.assert_(len(r.GetParents())==0)
        self.assert_(len(r.GetParentTitles())==0)
        self.assert_(len(r.GetParentPaths())==0)
        self.assertEqual(ccc, a.db.GetCountEntries())
        

    def test_createobjs(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=root(a)
        # create
        user = User(u"test")
        ccc = a.db.GetCountEntries()
        o1 = createObj1(r)
        self.assert_(o1)
        self.remove.append(o1.id)
        o2 = createObj2(r)
        self.assert_(o2)
        self.remove.append(o2.id)
        o3 = createObj1(o1)
        self.assert_(o3)
        o4 = createObj1(o3)
        self.assert_(o4)
        
        o5 = createObj3(o1)
        self.assert_(o5)
        o6 = createObj2(o5)
        self.assert_(o6)
        self.assertRaises(ContainmentError, createObj1, o5)
        
        self.assert_(ccc+6==statdb(a))
        #Values()
        self.assert_(r.IsContainer())
        self.assert_(o1.IsContainer())
        self.assert_(o2.IsContainer()==False)
        self.assert_(o1.GetID())
        self.assert_(o1.GetTypeID()=="type1")
        self.assert_(o1.GetTitle())
        self.assert_(o1.GetPath())
        #Parents()
        self.assert_(o1.GetRoot()==r)
        self.assert_(o1.GetApp()==a)
        self.assert_(o1.GetParent()==r)
        self.assert_(len(o1.GetParents())==1)
        self.assert_(len(o1.GetParentIDs())==1)
        self.assert_(len(o1.GetParentTitles())==1)
        self.assert_(len(o1.GetParentPaths())==1)

        self.assert_(o4.GetParent()==o3)
        self.assert_(len(o4.GetParents())==3)
        self.assert_(len(o4.GetParentIDs())==3)
        self.assert_(len(o4.GetParentTitles())==3)
        self.assert_(len(o4.GetParentPaths())==3)
        self.assert_(o3.GetObj(o4.GetID()))
        
        newO = r.Duplicate(o1, user)
        self.assert_(newO)
        self.remove.append(newO.id)
        
        r.Delete(o3.GetID(), user=user)
        r.Delete(o1.GetID(), user=user)
        r.Delete(o2.GetID(), user=user)
        self.assertEqual(ccc+5, a.db.GetCountEntries())
        r.Delete(newO.GetID(), user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        

    def test_lists(self):
        #print "Testing objects and subobjects"
        a=self.app
        r=root(a)
        ccc = a.db.GetCountEntries()
        user = User(u"test")
        # errors
        id = 9865898568444
        try:
            r.LookupObj(id)
            self.assert_(False)
        except:
            pass
        try:
            r.GetObj(id)
            self.assert_(False)
        except:
            pass
        # objects and parents
        self.assert_(r.GetSort())
        ccontainer = len(r.GetContainers(batch=False))
        cobjs = len(r.GetObjs(batch=False))
        ccontainer2 = len(r.GetContainerList(parameter={u"pool_type":u"type2"}))
        cobjs2 = len(r.GetObjsList(parameter={u"pool_type":u"type2"}))
        c=statdb(a)
        o1 = createObj1(r)
        self.assert_(o1)
        self.remove.append(o1.id)
        o2 = createObj2(r)
        self.assert_(o2)
        self.remove.append(o2.id)
        o3 = createObj1(o1)
        self.assert_(o3)
        o4 = createObj2(o3)
        self.assert_(o4)
        o5 = createObj2(o3)
        self.assert_(o5)
        self.assert_(c+5==statdb(a))
        try:
            createObj1(o5)
            self.assert_(False)
        except:
            pass
        try:
            createObj2(o5)
            self.assert_(False)
        except:
            pass

        # objects
        id = o1.GetID()
        self.assert_(r.LookupObj(id))
        self.assert_(r.GetObj(id))
        self.assert_(o1.GetObj(o3.GetID()))
        self.assert_(o3.GetObj(o4.GetID()))
        id = o5.GetID()
        self.assert_(r.LookupObj(id))
        self.assert_(r.LookupTitle(id))

        # subitems
        #root
        self.assert_(len(r.GetContainers(batch=False))==ccontainer+2)
        self.assert_(len(r.GetObjs(batch=False))==cobjs+2)
        self.assert_(len(r.GetContainers())==ccontainer+2)  # less failsafe than batch=False. On failure reset testdata.
        self.assert_(len(r.GetObjs())==cobjs+2)
        self.assert_(len(r.GetContainerList(parameter={u"pool_type":u"type2"}))==ccontainer2+1)
        self.assert_(len(r.GetObjsList(parameter={u"pool_type":u"type2"}))==cobjs2+1)
        self.assert_(len(o3.GetObjsBatch([o4.id,o5.id])))
        # object
        self.assert_(len(o3.GetContainers())==2)
        self.assert_(len(o3.GetObjs())==2)
        self.assert_(len(o3.GetContainerList(parameter={u"pool_type":u"type2"}))==2)
        self.assert_(len(o3.GetObjsList(parameter={u"pool_type":u"type2"}))==2)
        self.assert_(len(o3.GetContainerList(parameter={u"pool_type":u"type2"}, operators={"pool_type":u"<>"}))==0)
        self.assert_(len(o3.GetObjsList(parameter={u"pool_type":u"type2"}, operators={u"pool_type":u"<>"}))==0)
        self.assert_(len(o1.GetContainedIDs())==3)
        
        r.DeleteInternal(o1.GetID(), user=user)
        r.DeleteInternal(o2.GetID(), user=user, obj=o2)
        self.assertEqual(ccc, a.db.GetCountEntries())
        


    def test_restraintsConf(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=root(a)
        
        p,o=r.ObjQueryRestraints(self)
        p1,o1=r.queryRestraints
        self.assert_(p==p1)
        self.assert_(o==o1)
        
        r.queryRestraints = {"id":123}, {"id":"="}
        p,o=r.ObjQueryRestraints(self)
        self.assert_(p=={"id":123})
        self.assert_(o=={"id":"="})
        
        r.queryRestraints = {"id":123}, {"id":"="}
        p,o=r.ObjQueryRestraints(self, {"aa":123}, {"aa":"="})
        self.assert_(p=={"id":123,"aa":123})
        self.assert_(o=={"id":"=","aa":"="})
        
        def callback(**kw):
            kw["parameter"]["id"] = 456
            kw["operators"]["id"] = "LIKE"
        r.RegisterEvent("loadRestraints", callback)
        p,o=r.ObjQueryRestraints(self)
        self.assert_(p=={"id":456})
        self.assert_(o=={"id":"LIKE"})


    def test_restraintsLookup(self):
        #print "Testing objects and subobjects"
        a=self.app
        r=root(a)
        ccc = a.db.GetCountEntries()
        user = User(u"test")
        # errors
        id = 9865898568444
        try:
            r.LookupObj(id)
            self.assert_(False)
        except:
            pass
        try:
            r.GetObj(id)
            self.assert_(False)
        except:
            pass
        # objects and parents
        self.assert_(r.GetSort())
        ccontainer = len(r.GetContainers(batch=False))
        cobjs = len(r.GetObjs(batch=False))
        ccontainer2 = len(r.GetContainerList(parameter={u"pool_type":u"type2"}))
        cobjs2 = len(r.GetObjsList(parameter={u"pool_type":u"type2"}))
        c=statdb(a)
        o1 = createObj1(r)
        self.assert_(o1)
        self.remove.append(o1.id)
        o2 = createObj2(r)
        self.assert_(o2)
        self.remove.append(o2.id)
        o3 = createObj1(o1)
        self.assert_(o3)
        o4 = createObj2(o3)
        self.assert_(o4)
        o5 = createObj2(o3)
        self.assert_(o5)
        self.assert_(c+5==statdb(a))
        try:
            createObj1(o5)
            self.assert_(False)
        except:
            pass
        try:
            createObj2(o5)
            self.assert_(False)
        except:
            pass

        r.queryRestraints = {"pool_state":99}, {"pool_state":">"}

        # objects
        id = o1.GetID()
        self.assertFalse(r.LookupObj(id))
        self.assertFalse(r.GetObj(id))
        self.assertFalse(o1.GetObj(o3.GetID()))
        self.assertFalse(o3.GetObj(o4.GetID()))
        id = o5.GetID()
        self.assertFalse(r.LookupObj(id))
        self.assertFalse(r.LookupTitle(id))

        # subitems
        #root
        self.assert_(len(r.GetContainers(batch=False))==0)
        self.assert_(len(r.GetObjs(batch=False))==0)
        self.assert_(len(r.GetContainers())==0)
        self.assert_(len(r.GetObjs())==0)
        self.assert_(len(r.GetContainerList(parameter={u"pool_type":u"type2"}))==0)
        p,o=r.ObjQueryRestraints(r)
        p.update({u"pool_type":u"type2"})
        self.assert_(len(r.GetObjsList(parameter=p))==0)
        self.assert_(len(o3.GetObjsBatch([o4.id,o5.id]))==0)
        # object
        self.assert_(len(o3.GetContainers())==0)
        self.assert_(len(o3.GetObjs())==0)
        self.assert_(len(o3.GetContainerList(parameter={u"pool_type":u"type2"}))==0)
        p,o=r.ObjQueryRestraints(self)
        p.update({u"pool_type":u"type2"})
        self.assert_(len(o3.GetObjsList(parameter=p))==0)
        p,o=r.ObjQueryRestraints(self)
        self.assert_(len(o3.GetContainerList(parameter={u"pool_type":u"type2"}, operators={u"pool_type":u"<>"}))==0)
        p,o=r.ObjQueryRestraints(self)
        p.update({u"pool_type":u"type2"})
        o.update({u"pool_type":u"<>"})
        self.assert_(len(o3.GetObjsList(parameter=p, operators=o))==0)
        
        r.queryRestraints = {}, {}

        r.DeleteInternal(o1.GetID(), user=user)
        r.DeleteInternal(o2.GetID(), user=user, obj=o2)
        self.assertEqual(ccc, a.db.GetCountEntries())
        


    def test_shortcuts(self):
        #print "Testing shortcuts"
        a=self.app
        user = User(u"test")
        ccc = a.db.GetCountEntries()
        self.assert_(a.root())
        self.assert_(a.db)
        r = a.root()
        #root
        r.Close()
        r.app
        r.db
        r.root()
        r.GetID()
        r.GetTypeID()
        r.GetTypeName()
        r.GetTitle()
        r.GetPath()
        r.IsRoot()
        r.GetRoot()
        r.GetApp()
        r.GetParent()
        r.GetParents()
        r.GetParentIDs()
        r.GetParentTitles()
        r.GetParentPaths()
        r.GetTool("nive.components.tools.example")


    def test_shortcuts2(self):
        #print "Testing shortcuts"
        a=self.app
        user = User(u"test")
        ccc = a.db.GetCountEntries()
        self.assert_(a.root())
        self.assert_(a.db)
        r = a.root()
        o1 = createObj1(r)
        self.assert_(o1)
        self.remove.append(o1.id)
        #root
        o1.app
        o1.db
        o1.root()
        o1.GetID()
        o1.GetTypeID()
        o1.GetTypeName()
        o1.GetTitle()
        o1.GetPath()
        o1.IsRoot()
        o1.GetRoot()
        o1.GetApp()
        o1.GetParent()
        o1.GetParents()
        o1.GetParentIDs()
        o1.GetParentTitles()
        o1.GetParentPaths()
        o1.GetTool("nive.components.tools.example")
        o1.Close()
        self.assertEqual(ccc+1, a.db.GetCountEntries())
        r.Delete(o1.id, user)

class containerTest_db_(containerTest_db, unittest.TestCase):
    """
    """



class groupsrootTest_db:
    
    def setUp(self):
        self.app = app_db(["nive.components.extensions.localgroups"])
        self.remove=[]

    def tearDown(self):
        u = User(u"test")
        root = self.app.root()
        for r in self.remove:
            root.Delete(r, u)
        pass

    def test_rootsGroups(self):
        a=self.app
        r=root(a)

        userid = u"test"
        r.RemoveLocalGroups(None, None)
        self.assertFalse(r.GetLocalGroups(userid))
        r.AddLocalGroup(userid, u"group:local")
        self.assertItemsEqual(r.GetLocalGroups(userid), [u"group:local"])
        r.RemoveLocalGroups(u"nouser", u"nogroup")
        self.assertItemsEqual(r.GetLocalGroups(userid), [u"group:local"])
        r.RemoveLocalGroups(userid, u"nogroup")
        self.assertItemsEqual(r.GetLocalGroups(userid), [u"group:local"])
        r.RemoveLocalGroups(u"nouser", u"group:local")
        self.assertItemsEqual(r.GetLocalGroups(userid), [u"group:local"])
        r.RemoveLocalGroups(userid, u"group:local")
        self.assertFalse(r.GetLocalGroups(userid))
        r.AddLocalGroup(userid, u"group:local")
        r.RemoveLocalGroups(userid, None)
        self.assertFalse(r.GetLocalGroups(userid))





class groupsrootTest_db_(groupsrootTest_db, unittest.TestCase):
    """
    """


if __name__ == '__main__':
    unittest.main()
