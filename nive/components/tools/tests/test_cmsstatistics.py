
import time
import unittest

from nive.definitions import *
from nive.components.tools.cmsstatistics import *

from nive.tests import db_app

from nive.helper import FormatConfTestFailure

# -----------------------------------------------------------------

class DBSqlDataTest1(unittest.TestCase):

    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

    def test_tool(self):
        cmsstatistics(configuration,None)
        
    
class DBSqlDataTest1_db(unittest.TestCase):

    def setUp(self):
        self.app = db_app.app_db()
        self.app.Register(configuration)

    def tearDown(self):
        self.app.Close()
    
    def test_toolrun1(self):
        t = self.app.GetTool("cmsstatistics", self.app)
        self.assert_(t)
        r,v = t()
        #print v.getvalue()
        self.assert_(r)

