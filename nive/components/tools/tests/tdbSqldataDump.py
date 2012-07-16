
import time
import unittest

from nive.definitions import *
from nive.components.tools.dbSqldataDump import *

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
        dbSqldataDump(configuration,None)
        
    
class DBSqlDataTest1_db(unittest.TestCase):

    def setUp(self):
        self.app = db_app.app_db()
        self.app.Register(configuration)

    def tearDown(self):
        self.app.Close()
    
    def test_toolrun1(self):
        t = self.app.GetTool("dbSqldataDump", self.app)
        self.assert_(t)
        t.importWf = 0
        t.importSecurity = 0
        r,v = t()
        #print v
        self.assert_(r)


    def test_toolrun2(self):
        t = self.app.GetTool("dbSqldataDump", self.app)
        self.assert_(t)
        t.importWf = 1
        t.importSecurity = 1
        r,v = t()
        self.assert_(r)


if __name__ == '__main__':
    unittest.main()
