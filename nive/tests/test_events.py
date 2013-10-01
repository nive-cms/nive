
import time
import unittest

from nive.definitions import *
from nive.events import *



# -----------------------------------------------------------------

class testobj(Events):
    def __init__(self):
        self.called = 0
        self.InitEvents()
    
    def callme(self):
        self.Signal("callme", data=1)

    def event_testLocal(self, **kw):
        self.called = kw.get("data")
        

class EventTest(unittest.TestCase):

    def setUp(self):
        self.obj = testobj()


    def event_test(self, **kw):
        self.called = kw.get("data")

    def test_events1(self):
        self.obj.ListenEvent("test", "event_testLocal")
        self.obj.Signal("test", data=12345)
        self.assert_(self.obj.called==12345)
        self.obj.RemoveListener("test", "event_testLocal")
        self.obj.Signal("test", data=67890)
        self.assert_(self.obj.called==12345)

    def test_eventobj(self):
        self.called = 0
        self.obj.ListenEvent("callme", self.event_test)
        self.obj.callme()
        self.assert_(self.called==1)
        self.obj.RemoveListener("callme", self.event_test)
        self.called=0
        self.obj.callme()
        self.assert_(self.called==0)


    def test_eventcontext(self):
        
        def event_fnc_test(context=None, data=None):
            self.assert_(context==self.obj)
            self.called=1
        
        self.called = 0
        self.obj.ListenEvent("callme", event_fnc_test)
        self.obj.callme()
        self.assert_(self.called==1)
        self.obj.RemoveListener("callme", event_fnc_test)
        self.called=0
        self.obj.callme()
        self.assert_(self.called==0)


