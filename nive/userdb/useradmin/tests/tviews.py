# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import FieldConf
from nive.portal import Portal
from nive.i18n import _

from nive.userdb.tests.db_app import *
from nive.userdb.useradmin import view
from nive.userdb.useradmin import adminroot
from nive.views import BaseView

from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPOk, HTTPForbidden
from pyramid import testing 


class TestView(BaseView):
    """
    """
    

class tViews(unittest.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.config = testing.setUp(request=request)
        self.app = app()
        self.portal = Portal()
        self.portal.Register(self.app, "nive")
        self.app.Register(adminroot.configuration)
        self.app.Startup(self.config)
        self.root = self.app.root("usermanagement")
        self.request.context = self.root
    

    def tearDown(self):
        self.app.Close()
        testing.tearDown()


    def test_views(self):
        v = view.UsermanagementView(context=self.root, request=self.request)

        self.assert_(v.index_tmpl())
        v.view()
        self.assert_(v.add())
        self.assert_(v.edit())
        self.assert_(v.delete())


    def test_add(self):
        user = self.root.GetUserByName("testuser")
        if user:
            self.root.DeleteUser("testuser")
        v = view.UsermanagementView(context=self.root, request=self.request)
        r = v.add()
        self.assert_(r["result"])
        if self.root.GetUserByName("testuser"):
            self.assert_(False, "User should not exist")
        self.request.POST = {"name":"testuser", "password":"", "email":"test@aaa.com", "groups":("group:admin",)}
        r = v.add()
        self.assert_(r["result"])
        if self.root.GetUserByName("testuser"):
            self.assert_(False, "User should not exist")
        
        self.request.POST["create$"] = "create"
        r = v.add()
        self.assertFalse(r["result"])
        if self.root.GetUserByName("testuser"):
            self.assert_(False, "User should not exist")
        self.request.POST["password"] = "password"
        self.request.POST["password-confirm"] = "password"
        
        self.assertRaises(HTTPFound, v.add)
        self.assert_(self.root.GetUserByName("testuser"))
        
        self.root.DeleteUser("testuser")


    def test_edit(self):
        user = self.root.GetUserByName("testuser")
        if user:
            self.root.DeleteUser("testuser")
        v = view.UsermanagementView(context=self.root, request=self.request)
        self.request.POST = {"name":"testuser", "email":"test@aaa.com", "groups":("group:admin",)}
        self.request.POST["password"] = "password"
        self.request.POST["password-confirm"] = "password"
        self.request.POST["create$"] = "create"
        self.assertRaises(HTTPFound, v.add)
        user = self.root.GetUserByName("testuser")
        if not user:
            self.assert_(False, "User should exist")
        
        v = view.UsermanagementView(context=user, request=self.request)
        self.request.POST = {}
        r = v.edit()
        self.assert_(r["result"])

        self.request.POST = {"name":"testuser", "email":"test", "groups":("group:admin",)}
        self.request.POST["edit$"] = "edit"
        r = v.edit()
        self.assertFalse(r["result"])
        self.assert_(self.root.GetUserByName("testuser").data.email != "test")
        
        self.request.POST = {"name":"testuser", "email":"test@bbb.com", "groups":("group:admin",)}
        self.request.POST["edit$"] = "edit"
        r = v.edit()
        self.assert_(r["result"])
        self.assert_(self.root.GetUserByName("testuser").data.email == "test@bbb.com")
        
        self.root.DeleteUser("testuser")


    def test_delete(self):
        v = view.UsermanagementView(context=self.root, request=self.request)
        user = self.root.GetUserByName("testuser")
        if not user:
            self.request.POST = {"name":"testuser", "email":"test@aaa.com", "groups":("group:admin",)}
            self.request.POST["password"] = "password"
            self.request.POST["password-confirm"] = "password"
            self.request.POST["create$"] = "create"
            self.assertRaises(HTTPFound, v.add)
        user = self.root.GetUserByName("testuser")
        if not user:
            self.assert_(False, "User should exist")
            
        r = v.delete()
        self.assert_(r["result"])
        self.assertFalse(r["confirm"])

        ids = (user.id,)
        self.request.POST = {"ids":ids}
        r = v.delete()
        self.assert_(r["result"])
        self.assertFalse(r["confirm"])
        self.assert_(len(r["users"])==1)

        self.request.POST = {"ids":ids, "confirm": 1}
        self.assertRaises(HTTPFound, v.delete)
        self.assertFalse(self.root.GetUserByName("testuser"))
        

if __name__ == '__main__':
    unittest.main()
