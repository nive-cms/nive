from zope.interface import implements

import unittest
from nive.cms.app import WebsitePublisher
from nive.definitions import *

from nive.cms.tests.db_app import *
from nive.components.objects.base import PageBase

from nive.cms.workflow.wf import *
from nive.cms.workflow.view import *

class testpage(object):
    implements(IPage)


class wfTest(unittest.TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_wfconf(self):
        self.assert_(len(wfProcess.test())==0)
        
    def test_include(self):
        app = WebsitePublisher()
        app.Register(wfProcess)
        self.assert_(app.GetWorkflowConf(wfProcess.id, testpage())[0].id==wfProcess.id)

    def test_wfviewconf(self):
        self.assert_(len(configuration.test())==0)
