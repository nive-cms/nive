#-*- coding: utf-8 -*-

import time
import unittest

from nive.application import *
from nive.definitions import *
from nive.helper import *
from nive.portal import Portal

from nive.tests.db_app import *


class objTest_db:
    
    def setUp(self):
        self.app = app_db()

    def tearDown(self):
        self.app.Close()
        pass


    def test_obj1(self):
        a=self.app
        r=root(a)
        user = User(u"test")
        o = createObj1(r)
        id = o.id
        o.Close()
        o = r.obj(id)
        self.assert_(o)
        self.assert_(o.app)
        self.assert_(o.root())
        self.assert_(o.db)
        self.assert_(o.IsRoot()==False)
        self.assert_(o.GetRoot())
        self.assert_(o.GetApp())
        
        self.assert_(o.GetParent())
        self.assert_(o.GetParents())
        self.assert_(o.GetParentIDs())
        self.assert_(o.GetParentTitles())
        self.assert_(o.GetParentPaths())
        r.Delete(id, user=user)


    def test_objectedit(self):
        #print "Testing object update and commit"
        a=self.app
        ccc = a.db.GetCountEntries()
        r=root(a)
        # create
        user = User(u"test")

        oo = createObj1(r)
        o1 = createObj1(oo)
        self.assert_(oo.GetTypeID()=="type1")
        self.assert_(oo.GetTypeName()==u"Type 1 container")
        self.assert_(oo.GetFieldConf("ftext").name=="ftext")
        self.assert_(oo.GetTitle()==u"")
        self.assert_(oo.GetPath()==str(oo.id))

        id = o1.GetID()
        o1.Update(data1_2, user)
        self.assert_(o1.GetID()==id)
        self.assert_(o1.GetFld(u"ftext")==data1_2[u"ftext"])
        self.assert_(o1.GetFld(u"pool_filename")==data1_2[u"pool_filename"])
        del o1
        o1 = oo.obj(id)
        self.assert_(o1.GetFld(u"ftext")==data1_2[u"ftext"])
        self.assert_(o1.GetFld(u"pool_filename")==data1_2[u"pool_filename"])
        oo.Delete(id, user=user)


        o1 = createObj1(oo)
        id = o1.GetID()
        data, meta, files = o1.SplitData(data1_2)
        o1.meta.update(meta)
        o1.data.update(data)
        o1.files.update(files)
        o1.Commit(user)
        self.assert_(o1.GetID()==id)
        self.assert_(o1.GetFld(u"ftext")==data1_2[u"ftext"])
        self.assert_(o1.GetFld(u"pool_filename")==data1_2[u"pool_filename"])
        del o1
        o1 = oo.obj(id)
        self.assertFalse(o1.GetFld(u"ftext")==data1_1[u"ftext"])
        self.assertFalse(o1.GetFld(u"pool_filename")==data1_1[u"pool_filename"])
        
        o1.UpdateInternal(data1_1)
        o1.CommitInternal(user)
        self.assert_(o1.GetFld(u"ftext")==data1_1[u"ftext"])
        self.assert_(o1.GetFld(u"pool_filename")==data1_1[u"pool_filename"])

        self.assertRaises(ContainmentError, r.Delete, id, user)
        r.Delete(oo.GetID(), user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        a.Close()


    def test_objectfiles(self):
        #print "Testing object files update and commit"
        a=self.app
        r=root(a)
        ccc = a.db.GetCountEntries()
        # create
        user = User(u"test")

        # testing StoreFile()
        o1 = createObj2(r)
        o2 = createObj2(r)
        o1.Update(data2_1, user)
        o2.Update(data2_2, user)
        o1.StoreFile(u"file1", File(**file2_1), user=user)
        o1.StoreFile(u"file2", File(**file2_2), user=user)
        o2.StoreFile(u"file2", File(**file2_2), user=user)
        self.assert_(o1.GetFld(u"ftext")==data2_1[u"ftext"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assert_(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assert_(o1.GetFile(u"file2").filename==file2_2["filename"])
        self.assert_(o2.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assert_(o2.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assert_(o2.GetFile(u"file2").filename==file2_2["filename"])

        id1 = o1.id
        id2 = o2.id
        del o1
        del o2
        o1 = r.obj(id1)
        o2 = r.obj(id2)
        self.assert_(o1.GetFld(u"ftext")==data2_1[u"ftext"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assert_(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assert_(o1.GetFile(u"file2").filename==file2_2["filename"])
        self.assert_(o2.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assert_(o2.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assert_(o2.GetFile(u"file2").filename==file2_2["filename"])
        self.assert_(o2.GetFileByName(file2_2["filename"]))

        #delete files
        self.assert_(o1.DeleteFile(u"file1", user=user))
        self.assert_(o1.DeleteFile(u"file2", user=user))
        self.assertFalse(o1.GetFile(u"file1"))
        self.assertFalse(o1.GetFile(u"file2"))
        self.assertFalse(o1.GetFileByName(file2_2["filename"]))

        r.Delete(o1.GetID(), user=user)
        r.Delete(o2.GetID(), user=user)

        # testing files wrapper
        o1 = createObj2(r)
        o2 = createObj2(r)
        d = data2_1.copy()
        d[u"file1"] = File(**file2_1)
        d[u"file2"] = File(**file2_2)
        o1.Update(d, user)
        d = data2_2.copy()
        d[u"file2"] = File(**file2_2)
        o2.Update(d, user)
        self.assert_(o1.GetFld(u"ftext")==data2_1[u"ftext"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assert_(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assert_(o1.GetFile(u"file2").filename==file2_2["filename"])
        self.assert_(o2.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assert_(o2.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assert_(o2.GetFile(u"file2").filename==file2_2["filename"])

        id1 = o1.id
        id2 = o2.id
        del o1
        del o2
        o1 = r.obj(id1)
        o2 = r.obj(id2)
        self.assert_(o1.GetFld(u"ftext")==data2_1[u"ftext"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assert_(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assert_(o1.GetFile(u"file2").filename==file2_2["filename"])
        self.assert_(o2.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assert_(o2.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assert_(o2.GetFile(u"file2").filename==file2_2["filename"])

        r.Delete(o1.GetID(), user=user)
        r.Delete(o2.GetID(), user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        a.Close()


    def test_commitundo(self):
        #print "Testing object commit and undo for data and files"
        a=self.app
        ccc = a.db.GetCountEntries()
        r=root(a)
        # create
        user = User(u"test")

        # testing commit
        o1 = createObj2(r)
        d = data2_2.copy()
        d[u"file1"] = File(**file2_1)
        d[u"file2"] = File(**file2_2)
        data, meta, files = o1.SplitData(d)
        o1.data.update(data)
        o1.meta.update(meta)
        o1.files.update(files)
        self.assert_(o1.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assert_(o1.files[u"file1"]["filename"]==file2_1["filename"])
        self.assert_(o1.files[u"file2"]["filename"]==file2_2["filename"])
        o1.Commit(user)
        self.assert_(o1.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assert_(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assert_(o1.GetFile(u"file2").filename==file2_2["filename"])
        id = o1.id
        del o1
        o1 = r.obj(id)
        self.assert_(o1.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assert_(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assert_(o1.GetFile(u"file2").filename==file2_2["filename"])
        r.Delete(o1.GetID(), user=user)

        # testing undo
        o1 = createObj2(r)
        o1.StoreFile(u"file1", File(**file2_1), user=user)
        d = data2_2.copy()
        d[u"file1"] = File(**file2_2)
        data, meta, files = o1.SplitData(d)
        o1.data.update(data)
        o1.meta.update(meta)
        o1.files.update(files)
        self.assert_(o1.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assert_(o1.files.get(u"file1").filename==file2_2["filename"])
        o1.Undo()
        self.assert_(o1.GetFld(u"fstr")==data2_1[u"fstr"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assert_(o1.files.get(u"file1").filename==file2_1["filename"])
        id = o1.id
        del o1
        o1 = r.obj(id)
        self.assert_(o1.GetFld(u"fstr")==data2_1[u"fstr"])
        self.assert_(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assert_(o1.GetFile(u"file1").filename==file2_1["filename"])
        r.Delete(o1.GetID(), user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        a.Close()

    

class objTest_db_(objTest_db, unittest.TestCase):    
    """
    """
    


class groupsTest_db:
    
    def setUp(self):
        self.app = app_db(["nive.components.extensions.localgroups"])
        #emptypool(self.app)
        self.remove=[]

    def tearDown(self):
        u = User(u"test")
        root = self.app.root()
        for r in self.remove:
            root.Delete(r, u)
        pass

    def test_objectgroups(self):
        a=self.app
        r=root(a)
        # create
        user = User(u"test")
        o = createObj1(r)
        id = o.id
        
        userid = u"test"
        self.assertItemsEqual(o.GetLocalGroups(userid), [u"group:owner"])
        r.RemoveLocalGroups(userid, None)
        o.RemoveLocalGroups(userid, None)
        self.assertFalse(o.GetLocalGroups(userid))
        o.AddLocalGroup(userid, u"group:local")
        self.assertItemsEqual(o.GetLocalGroups(userid), [u"group:local"])
        o.RemoveLocalGroups(u"nouser", u"nogroup")
        self.assertItemsEqual(o.GetLocalGroups(userid), [u"group:local"])
        o.RemoveLocalGroups(userid, u"nogroup")
        self.assertItemsEqual(o.GetLocalGroups(userid), [u"group:local"])
        o.RemoveLocalGroups(u"nouser", u"group:local")
        self.assertItemsEqual(o.GetLocalGroups(userid), [u"group:local"])
        o.RemoveLocalGroups(userid, u"group:local")
        self.assertFalse(o.GetLocalGroups(userid))
        o.AddLocalGroup(userid, u"group:local")
        o.RemoveLocalGroups(userid, None)
        self.assertFalse(o.GetLocalGroups(userid))

        r.Delete(id, user=user)

        

class groupsTest_db_(groupsTest_db, unittest.TestCase):
    """
    """

 
    
#tests!

class objToolTest_db:
    """
    """
    def setUp(self):
        self.app = app()

    def tearDown(self):
        self.app.Close()
        pass

    
    def test_tools(self):
        GetTool(name)
        GetTools(user)

class objToolTest_db_: #(objToolTest_db, unittest.TestCase):
    """
    """

class objWfTest_db:
    """
    """
    def setUp(self):
        self.app = app()

    def tearDown(self):
        self.app.Close()
        pass

    
    def test_wf(self):
        GetWorkflow()
        GetNewWfID()
        GetWfStateName(user)
        GetWfInfo(user)
        WfAction(action, transition = None, user = None)
        WfAllow(action, transition = None, user = None)
        SetWfp(processID, user, force=False)
        SetWfState(stateID, user)
        SetWfData(state, key, data, user)
        GetWfData(state = None, key = None)
        DeleteWfData(user, state = None, key = None)
        GetWfLog(lastEntryOnly=1)
        AddWfLog(action, transition, user, comment="")    


class objWfTest_db_:#(objWfTest_db, unittest.TestCase):
    """
    """



















if __name__ == '__main__':
    unittest.main()
