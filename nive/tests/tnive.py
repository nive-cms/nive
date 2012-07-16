
import time
import unittest

from nive import OperationalError
from nive.application import *
from nive.definitions import *
from nive.helper import *
from nive.events import Events
from nive.portal import Portal

from nive.tests import db_app

mApp = AppConf(id="app", groups=[GroupConf(id="g1",name="G1")], categories=[CategoryConf(id="c1",name="C1")])
dbConfiguration = DatabaseConf(dbName="test")

mObject = ObjectConf(id="object", dbparam="object", name="Object",
                     data=(FieldConf(id="a1",datatype="string",name="A1"),FieldConf(id="a2",datatype="number",name="A2"),))

mRoot = RootConf(id="root")
mTool = ToolConf(id="tool", context="nive.components.tools.example")
mViewm = ViewModuleConf(id="vm")
mView = ViewConf(id="v",context=mApp,view=mApp)
mMod = ModuleConf(id="mod", context=mApp)



mApp2 = AppConf(id="app2", 
                context="nive.tests.tnive.testapp",
                modules=[mObject,mRoot,mTool,mViewm,mView,mMod], 
                groups=[GroupConf(id="g1",name="G1")], 
                categories=[CategoryConf(id="c1",name="C1")])
dbConfiguration2 = DatabaseConf(dbName="test")



class testapp(Application, Registration, Configuration, AppFactory, Events):
    """
    """
    
def app():
    app = testapp()
    app.Register(mApp2)
    app.Register(dbConfiguration2)
    app.Startup(None)
    portal = Portal()
    portal.Register(app, "nive")
    return app



class modTest(unittest.TestCase):
    
    def setUp(self):
        self.app = testapp()

    def tearDown(self):
        pass


    def test_Register(self):
        self.app.Register(mApp)
        self.app.Register(dbConfiguration)
        self.app.Register(mObject)
        self.app.Register(mRoot)
        self.app.Register(mTool)
        self.app.Register(mViewm)
        self.app.Register(mView)
        self.app.Register(mMod)
        self.app.Register(ModuleConf(id="aaa"), provided=IObject, name="testttttt")
        self.app.Startup(None)
        self.assert_(self.app.db)

    def test_include2(self):
        self.app.Register(mApp2)
        self.app.Register(dbConfiguration2)
        self.app.Startup(None)
        self.assert_(self.app.db)

    def test_includefailure(self):
        self.app.Register(mApp2)
        #no database: self.app.Register(dbConfiguration2)
        self.app.Startup(None)
        self.assertRaises(OperationalError, self.app.db)


class appTest(unittest.TestCase):
    
    def setUp(self):
        self.app = testapp()
        self.app.Register(mApp2)
        self.app.Register(dbConfiguration2)
        self.portal = Portal()
        self.portal.Register(self.app, "nive")
        self.app.Startup(None)

    def tearDown(self):
        pass


    def test_include2(self):
        s = self.app._structure.structure
        self.assert_("pool_meta" in s)
        self.assert_("object" in s)
        self.assert_(len(s["pool_meta"])>10)
        self.assert_(len(s["object"])==2)
        pass


    def test_fncs(self):
        self.assert_(self.app.ConvertID(23)==23)
        self.assert_(self.app.ConvertID("23")==23)
        self.assert_(self.app.ConvertID("aaa")==-1)
        self.assert_(self.app.GetVersion())
        self.assert_(self.app.CheckVersion())
        

    def test_objs(self):
        self.assert_(self.app.root(name=""))
        self.assert_(self.app.root(name="root"))
        self.assert_(self.app.root(name="aaaaaaaa")==None)
        #self.assert_(self.app.portal)
        self.assert_(self.app.__getitem__("root"))
        self.assert_(self.app.GetRoot(name="root"))
        self.assert_(len(self.app.GetRoots())==1)
        self.assert_(self.app.GetApp())
        #self.assert_(self.app.GetPortal())
        self.assert_(self.app.GetTool("nive.components.tools.example"))
        #!!! self.app.GetWorkflow(wfProcID)

    def test_confs(self):
        self.assert_(self.app.GetRootConf(name=""))
        self.assert_(self.app.GetRootConf(name="root"))
        self.assert_(len(self.app.GetAllRootConfs()))
        self.assert_(len(self.app.GetRootIds())==1)
        self.assert_(self.app.GetDefaultRootName()=="root")

    def test_confs2(self):
        self.assert_(self.app.GetObjectConf("object", skipRoot=False))
        self.assert_(self.app.GetObjectConf("root", skipRoot=True)==None)
        self.assert_(self.app.GetObjectConf("oooooh", skipRoot=False)==None)
        self.assert_(len(self.app.GetAllObjectConfs(visibleOnly = False))==1)
        self.assert_(self.app.GetTypeName("object")=="Object")

    def test_confs3(self):
        self.assert_(self.app.GetToolConf("tool"))
        self.assert_(len(self.app.GetAllToolConfs()))
        
    def test_confs4(self):
        self.assert_(self.app.GetCategory(categoryID = "c1"))
        self.assert_(len(self.app.GetAllCategories(sort=u"name", visibleOnly=False))==1)
        self.assert_(self.app.GetCategoryName("c1")=="C1")
        self.assert_(self.app.GetGroups(sort=u"name", visibleOnly=False))
        self.assert_(self.app.GetGroupName("g1")=="G1")

    def test_flds(self):
        self.assert_(self.app.GetFld("title", typeID = None))
        self.assert_(self.app.GetFld("aaaaa", typeID = None)==None)
        self.assert_(self.app.GetFld("pool_stag", typeID = "object"))
        self.assert_(self.app.GetFld("a1", typeID = "object"))
        self.assert_(self.app.GetFld("a1", typeID = None)==None)
        self.assert_(self.app.GetFld("a2", typeID = "object"))
        self.assert_(self.app.GetFld("a2", typeID = "ooooo")==None)
        self.assert_(self.app.GetFld("ooooo", typeID = "object")==None)
        
        self.assert_(self.app.GetFldName("a2", typeID = "object")=="A2")
        self.assert_(self.app.GetObjectFld("a1", "object"))
        self.assert_(len(self.app.GetAllObjectFlds("object"))==2)
        self.assert_(self.app.GetMetaFld("title"))
        self.assert_(len(self.app.GetAllMetaFlds(ignoreSystem = True)))
        self.assert_(len(self.app.GetAllMetaFlds(ignoreSystem = False)))
        self.assert_(self.app.GetMetaFldName("title")=="Title")
        
    def test_flds2(self):    
        self.app.LoadStructure(forceReload = False)
        self.assert_(self.app._structure)
        self.app.LoadStructure(forceReload = True)
        self.assert_(self.app._structure)

    def test_flds4(self):    
        self.assert_(self.app._GetDBObj())
        self.app._CloseDBObj()
        self.assert_(self.app._GetDBObj())
        self.assert_(self.app._GetRootObj("root"))
        self.app._CloseRootObj(name="root")
        self.assert_(self.app._GetRootObj("root"))
        self.assert_(self.app._GetToolObj("nive.components.tools.example", None))



class appTest_db:
    
    def setUp(self):
        self.app = db_app.app
        
    def tearDown(self):
        pass


    def test_database(self):
        r = self.app.root()
        o = db_app.createObj1(r)
        self.assert_(o)
        id = o.id
        del o
        self.assert_(self.app.obj(id, rootname = ""))
        self.assert_(self.app.obj(id, rootname = "root"))
        self.assert_(self.app.db)
        self.assert_(self.app.GetDB())
        self.app.CloseDB()
        self.assert_(self.app.GetDB())
        self.assert_(self.app.LookupObj(id))
        self.assert_(len(self.app.Query("select id from pool_meta", values = [])))
        ph = self.app.db.GetPlaceholder()
        self.assert_(len(self.app.Query("select id from pool_meta where pool_type="+ph, values = ["type1"])))
        self.assert_(self.app.GetCountEntries())
        o=self.app.obj(id, rootname = "")
        self.assert_(o)
        self.app.Register("nive.components.tools.example")
        self.assert_(self.app.GetTool("exampletool"))
        user = User(u"test")
        self.app.root().Delete(id, user=user)


class appTest_db_(appTest_db, unittest.TestCase):
    """
    """


if __name__ == '__main__':
    unittest.main()
