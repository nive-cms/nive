
import time
import unittest
import gc

from nive.definitions import OperationalError
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
                context="nive.tests.test_nive.testapp",
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



class baseTest(unittest.TestCase):
    
    def setUp(self):
        pass
    def tearDown(self):
        pass


    def test_referencing(self):
        pass
        #a = app()
        #r = a.root()
        #a.portal.Close()
        


class dbTest(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass


    def test_database(self):
        user = User(u"test")
        app = db_app.app_db()
        r = app.root()

        type = u"type1"
        data = db_app.data1_1
        o = r.Create(type, data = data, user = user)
        self.assert_(o)
        id = o.id
        #print "get_referents:"
        #for x in gc.get_referents(o):
        #    print x
        #print
        #print "get_referrers:"
        #for x in gc.get_referrers(o):
        #    print x
        del o
        
        o=app.obj(id, rootname = "")
        self.assert_(o)
        r.Delete(id, user=user)
        del o
        #app.portal.Close()
        print 
        a=1

