
import time
import unittest
from types import DictType

from nive.definitions import *
from zope.interface.registry import * 
from zope.interface import Interface, Attribute, implements, alsoProvides, Provides



# -----------------------------------------------------------------
class ITest(Interface):
    pass
class ITest2(Interface):
    pass
class ITestaaaa(Interface):
    pass

class Test(object):
    Provides(ITest)
    def __call__(self, context):
        return self, context

class Test2(object):
    implements(ITest)

# -----------------------------------------------------------------
testconf = ObjectConf(
    id = "text",
    name = "Text",
    dbparam = "texts",
    context = "nive.tests.thelper.text",
    selectTag = 1,
    description = ""
)
configuration = testconf



class registryTest(unittest.TestCase):

    def test_init1(self):
        registry = Components()
        #registerUtility(self, component=None, provided=None, name=u'', info=u'', event=True, factory=None)

        t2 = Test2()
        alsoProvides(t2, ITest2)
        self.assert_(ITest2.providedBy(t2))
        ITest.providedBy(Test())
        registry.registerUtility(Test(), provided=ITest, name='testconf')

        ITest2.providedBy(Test())
        registry.registerUtility(Test2(), name='testconf2')
        
        self.assert_(registry.queryUtility(ITestaaaa)==None)
        self.assert_(registry.queryUtility(ITest, name=u'testconf'))
        for u in registry.getUtilitiesFor(ITest):
            self.assert_(u)
        self.assert_(registry.getAllUtilitiesRegisteredFor(ITest))
        
        
    def test_init2(self):
        registry = Components()
        IConf.providedBy(Conf())
        registry.registerUtility(Conf(), provided=IConf, name='testconf2')
        
        IObjectConf.providedBy(testconf)
        registry.registerUtility(testconf, provided=IObjectConf, name='testconf3')
        
        registry.registerUtility(configuration, provided=IObjectConf, name='testconf')
        
        
        
    def test_init3(self):
        registry = Components()
        registry.registerAdapter(Test(), (IConf,), ITest, name='testadapter')
        registry.registerAdapter(Test(), (IConf,), ITest, name='testadapter2')
        registry.registerAdapter(Test(), (IConf,), ITest)
        c = Conf()
        
        self.assert_(IConf.providedBy(c))
        #registry.getAdapter(c, ITest, name='testadapter')
        self.assert_(registry.getAdapter(c, ITest))
        
        self.assertFalse(registry.queryAdapter(c, ITest, name='nix'))
        self.assert_(registry.queryAdapter(c, ITest, name='testadapter'))
        a = list(registry.getAdapters((c,), ITest))
        self.assert_(len(a)==3,a)
        
