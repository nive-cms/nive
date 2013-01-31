
import time
import unittest
from types import DictType

from nive.definitions import *

# -----------------------------------------------------------------


class baseConfTest(unittest.TestCase):

    def test_init(self):
        c = Conf()
        c = Conf(**{"test":1})
        self.assert_(c.test==1)
        c = Conf(test=2)
        self.assert_(c.test==2)
        self.assert_(repr(c).find("<Conf ")==0)
        
    def test_set(self):
        c = Conf()
        c["test"] = 1
        self.assert_(c.test==1)
        c.test=2
        self.assert_(c.test==2)
        c.update({"test":4})
        self.assert_(c.test==4)

    def test_get(self):
        c = Conf()
        c.test=1
        self.assert_(c["test"]==1)
        self.assert_(c.get("test")==1)
        self.assert_(c.get("aaaa",3)==3)
        c.aaa=2
        c.ccc="3"
        self.assert_(c.get("ccc")=="3")
        self.assert_(c.get("aaa")==2)
        self.assert_(c.get("ooo",5)==5)
        
    def test_copy(self):
        c = Conf()
        c.test=1
        c.aaa=2
        c.bbb="4"
        c.ccc="3"
        x=c.copy()
        self.assert_(x.test==1)
        self.assert_(x.aaa==2)
        self.assert_(x.bbb=="4")
        self.assert_(x.ccc=="3")
        x=c.copy(test=5,bbb=1)
        self.assert_(x.test==5)
        self.assert_(x.aaa==2)
        self.assert_(x.bbb==1)
        self.assert_(x.ccc=="3")

    def test_copy2(self):
        c = Conf()
        c.test=1
        c.aaa=2
        c.bbb="4"
        c.ccc="3"
        x = Conf(c)
        self.assert_(x.test==1)
        self.assert_(x.aaa==2)
        self.assert_(x.bbb=="4")
        self.assert_(x.ccc=="3")
        
    def test_fncs(self):
        c = Conf(Conf(inparent=1), **{"test":1})
        c2 = c.copy(**{"test2":2})
        k=c2.keys()
        self.assert_(c2.has_key("test2"))
        self.assert_(c2.has_key("test"))
        c2.update({"test":3})
        self.assert_(c2.get("test")==3)
        self.assert_(c2.test==3)
        c2.test=4
        self.assert_(c2.inparent==1)
        self.assert_(c2.test==4)

    def test_lock(self):
        c = Conf(Conf(inparent=1), **{"test":1})
        c.test=2
        c.lock()
        self.assertRaises(ConfigurationError, c.update, {"test":4})
        self.assert_(c.test==2)
        c.unlock()
        c.test=4
        self.assert_(c.test==4)



class ConfTest(unittest.TestCase):

    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    

    def test_obj0(self, **kw):
        testconf = DatabaseConf(
            context = "Sqlite3",
            fileRoot = "",
            dbName = "",
            host = "",
            port = "",
            user = "",
            password = "",
            useTrashcan = False,
            unicode = True,
            timeout = 3,
            dbCodePage = "utf-8"
        )
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))

    def test_obj1(self, **kw):
        testconf = AppConf(
            id = "test",
            title = "Test",
            description = "",
            context = "nive.tests.tdefinitions.ConfTest",
            fulltextIndex = False,
        )
        self.assert_(testconf.id=="test")
        self.assert_(testconf.context=="nive.tests.tdefinitions.ConfTest")
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))

    def test_obj2(self, **kw):
        testconf = FieldConf(
            id = "aaa",
            datatype = "string",
            size = 100,
            default = "aaa",
            listItems = None,
            settings = {},
            fulltext = True,
        )
        self.assert_(testconf.id=="aaa")
        self.assert_(testconf.size==100)
        self.assert_(testconf.fulltext==True)
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))

    def test_obj3(self, **kw):
        testconf = ObjectConf(
            id = "text",
            name = "Text",
            dbparam = "texts",
            context = "nive.tests.thelper.text",
            selectTag = 1,
            description = ""
        )
        self.assert_(testconf.id=="text")
        self.assert_(testconf.name=="Text")
        self.assert_(testconf.selectTag==1)
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))

    def test_obj4(self, **kw):
        testconf = RootConf(
            id = "root",
            name = "Root",
            context = "nive.tests.tdefinitions.ConfTest",
            default = True
        )
        self.assert_(testconf.id=="root")
        self.assert_(testconf.name=="Root")
        self.assert_(testconf.default==True)
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))

    def test_obj5(self, **kw):
        testconf = ViewModuleConf(
            id = u"viewing",
            name = u"Oh",
            static = "here:static",
            containment = "nive.tests.tdefinitions.ConfTest",
            widgets = (WidgetConf(apply=(IObject,),viewmapper="test",widgetType=IWidgetConf,id="test"),),
        )
        self.assert_(testconf.id=="viewing")
        self.assert_(testconf.name=="Oh")
        self.assert_(testconf.containment=="nive.tests.tdefinitions.ConfTest")
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))

    def test_obj6(self, **kw):
        testconf = ViewConf(
            attr = "test_obj6",
            name = "",
            context = "nive.tests.tdefinitions.SystemTest",
            view = "nive.tests.tdefinitions.ConfTest",
            renderer = None
        )
        self.assert_(testconf.attr=="test_obj6")
        self.assert_(testconf.name=="")
        self.assert_(testconf.view=="nive.tests.tdefinitions.ConfTest")
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))

    def test_obj7(self, **kw):
        testconf = ToolConf(
            id = u"tool",
            name = u"Tool",
            context = "nive.tests.tdefinitions.ConfTest",
        )
        self.assert_(testconf.id=="tool")
        self.assert_(testconf.name=="Tool")
        self.assert_(testconf.context=="nive.tests.tdefinitions.ConfTest")
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))
    
    def test_obj8(self, **kw):
        testconf = ModuleConf(
            id = "module",
            name = "Module",
            context = "nive.tests.tdefinitions.ConfTest",
            events = None,
            description = ""
        )
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))
    
    def test_obj9(self, **kw):
        testconf = WidgetConf(
            apply = (IObject,IApplication),
            viewmapper = "viewme",
            widgetType = IWidgetConf,
            name = "widget",
            id = "widget",
            sort = 100,
            description = ""
        )
        self.assert_(testconf.id=="widget")
        self.assert_(testconf.name=="widget")
        self.assert_(len(testconf.test())==0)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))
    
    def test_obj10(self, **kw):
        testconf = GroupConf(
            id = "group",
            name = "Group",
            hidden = True,
            description = ""
        )
        self.assert_(testconf.id=="group")
        self.assert_(testconf.name=="Group")
        self.assert_(testconf.hidden==True)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))
    
    def test_obj11(self, **kw):
        testconf = CategoryConf(
            id = "category",
            name = "Category",
            hidden = True,
            description = ""
        )
        self.assert_(testconf.id=="category")
        self.assert_(testconf.name=="Category")
        self.assert_(testconf.hidden==True)
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))
    
    def test_obj12(self, **kw):
        testconf = PortalConf(
            portalDefaultUrl = "/website/",
            loginUrl = "/userdb/udb/login",
            forbiddenUrl = "/userdb/udb/login",
            logoutUrl = "/userdb/udb/logout",
            accountUrl = "/userdb/udb/update",
            favicon = "",
            robots = u""
        )
        self.assert_(testconf.portalDefaultUrl=="/website/")
        self.assert_(testconf.loginUrl == "/userdb/udb/login")
        self.assert_(testconf.forbiddenUrl == "/userdb/udb/login")
        self.assert_(testconf.logoutUrl == "/userdb/udb/logout")
        self.assert_(testconf.accountUrl == "/userdb/udb/update")
        self.assert_(testconf.robots == u"")
        self.assert_(len(testconf.uid()))
        str(testconf) # may be empty
        self.assert_(repr(testconf))
    
        
        
class SystemTest(unittest.TestCase):

    def test_data(self, **kw):
        self.assert_(len(DataTypes))
        self.assert_(len(SystemFlds))
        self.assert_(len(ReadonlySystemFlds))
        

    def test_structure1(self, **kw):
        for tbl in Structure.items():
            self.assert_(tbl[0])
            self.assert_("fields" in tbl[1])
        


if __name__ == '__main__':
    unittest.main()
