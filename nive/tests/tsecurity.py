
import time
import unittest
from types import DictType

from nive.definitions import *
from nive.security import *
from nive.tests import db_app


class securityTest(unittest.TestCase):

    def test_init1(self):
        app = db_app.app_db()
        GetUsers(app)
    
    def test_user(self):
        u = User("name", 123)
        self.assert_(str(u)=="name")
        self.assert_(u.id==123)
        u.GetGroups()



                
        

if __name__ == '__main__':
    unittest.main()
