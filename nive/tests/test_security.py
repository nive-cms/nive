
import time
import unittest
from types import DictType

from nive.definitions import implements
from nive.security import User, AdminUser, GetUsers, Unauthorized, UserFound, IAdminUser
from nive.tests import db_app


class securityTest(unittest.TestCase):

    def test_excps(self):
        u = Unauthorized()
        f = UserFound("user")

    def test_iface(self):
        class aaaaa(object):
            implements(IAdminUser)
        a = aaaaa()

    def test_init1(self):
        app = db_app.app_db()
        GetUsers(app)
    
    def test_user(self):
        u = User("name", 123)
        self.assert_(str(u)=="name")
        self.assert_(u.id==123)
        u.GetGroups()

    def test_adminuser(self):
        u = AdminUser({"name":"admin", "password":"11111", "email":"admin@aaa.ccc", "groups":("group:admin",)}, "admin")
        
        self.assert_(u.identity=="admin")
        self.assert_(str(u)=="admin")
        self.assert_(u.Authenticate("11111"))
        self.assertFalse(u.Authenticate("aaaaaaa"))
        u.Login()
        u.Logout()
        self.assert_(u.GetGroups()==("group:admin",))
        self.assert_(u.InGroups("group:admin"))
        self.assertFalse(u.InGroups("group:traa"))
        self.assert_(u.ReadableName()=="admin")
        


                
        

if __name__ == '__main__':
    unittest.main()
