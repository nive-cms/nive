
import time
import unittest

from nive.definitions import ObjectConf, FieldConf, Conf
from nive.helper import *
from nive.utils.path import DvPath

# -----------------------------------------------------------------

class text(object):
    pass

class text1(object):
    pass
class text2(object):
    pass
class text3(object):
    pass

testconf = ObjectConf(
    id = "text",
    name = "Text",
    dbparam = "texts",
    context = "nive.tests.thelper.text",
    selectTag = 1,
    description = ""
)

testconf.data = (
    FieldConf(id="textblock", datatype="htext", size=10000, default="", name="Text", fulltext=True, description="")
)

testconf.forms = {
    "create": { "fields":  ["textblock"],
                "actions": ["create"]},
    "edit":   { "fields":  ["textblock"], 
                "actions": ["save"]}
}
configuration = testconf


class ConfigurationTest(unittest.TestCase):

    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    

    def test_resolve1(self, **kw):
        self.assert_(ResolveName("nive.tests.thelper.text", base=None))
        self.assert_(ResolveName(".thelper.text", base="nive.tests"))
        self.assert_(ResolveName("nive.components.tools.dbStructureUpdater", base=None))
        self.assert_(ResolveName(".dbStructureUpdater.dbStructureUpdater", base="nive.components.tools"))
        
    def test_resolve2(self, **kw):
        i,c = ResolveConfiguration(testconf, base=None)
        self.assert_(c)
        i,c = ResolveConfiguration("nive.tests.thelper.testconf", base=None)
        self.assert_(c)
        i,c = ResolveConfiguration(".thelper.testconf", base="nive.tests")
        self.assert_(c)
        i,c = ResolveConfiguration("nive.tests.thelper", base=None)
        self.assert_(c)

    def test_load(self, **kw):
        p=DvPath(__file__)
        p.SetNameExtension("app.json")
        i,c = ResolveConfiguration(str(p))
        self.assert_(c)
        p.SetNameExtension("db.json")
        c = LoadConfiguration(str(p))
        self.assert_(c)
        
        
    def test_classref(self):
        #self.assert_(GetClassRef(testconf.context, reloadClass=False, raiseError=False)==text)
        self.assert_(GetClassRef(text, reloadClass=False, raiseError=False)==text)
        self.assert_(GetClassRef("nive.tests.thelper.textxxxxxx", reloadClass=False, raiseError=False)==None)
        self.assertRaises(ImportError, GetClassRef, "nive.tests.thelper.textxxxxxx", reloadClass=False, raiseError=True)
        

    def test_factory(self):
        #self.assert_(ClassFactory(testconf, reloadClass=False, raiseError=False)==text)
        c=testconf.copy()
        c.context=text
        self.assert_(ClassFactory(c, reloadClass=False, raiseError=False)==text)
        c.context="nive.tests.thelper.textxxxxxx"
        self.assert_(ClassFactory(c, reloadClass=False, raiseError=False)==None)
        self.assertRaises(ImportError, ClassFactory, c, reloadClass=False, raiseError=True)

        c=testconf.copy()
        c.extensions=(text1,text2,text3)
        self.assert_(len(ClassFactory(c, reloadClass=False, raiseError=False).mro())==6)
        c.extensions=("text66666",text2,"text5555")
        self.assert_(len(ClassFactory(c, reloadClass=False, raiseError=False).mro())==4)
        c.extensions=("nive.tests.thelper.text1","nive.tests.thelper.text2","nive.tests.thelper.text3")
        self.assert_(len(ClassFactory(c, reloadClass=False, raiseError=False).mro())==6)



if __name__ == '__main__':
    unittest.main()
