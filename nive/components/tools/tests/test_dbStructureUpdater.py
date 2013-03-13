
import time
import unittest

from nive.definitions import *
from nive.helper import ResolveName
from nive.components.tools.dbStructureUpdater import *

from nive.tests import db_app


from nive.helper import FormatConfTestFailure


# -----------------------------------------------------------------

class DBStructureTest(unittest.TestCase):


    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

    def test_tool(self):
        t = dbStructureUpdater(configuration,None)
        self.assert_(t)

    
class DBStructureTest2(unittest.TestCase):
    """
    """
    def setUp(self):
        self.app = db_app.app_db()
        self.app.Register(configuration)

    def tearDown(self):
        self.app.Close()
        pass

    def test_toolrun1(self):
        t = self.app.GetTool("nive.components.tools.dbStructureUpdater")
        self.assert_(t)
        t.importWf = 0
        t.importSecurity = 0
        r,v = t()
        self.assert_(r)


    def test_toolrun2(self):
        t = self.app.GetTool("nive.components.tools.dbStructureUpdater")
        self.assert_(t)
        t.importWf = 1
        t.importSecurity = 1
        r,v = t()
        self.assert_(r)


if __name__ == '__main__':
    unittest.main()
