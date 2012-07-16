
import time
import unittest
from types import DictType

from nive.definitions import *
from nive.security import *
from nive.tests import db_app
from nive.views import *

from pyramid.response import Response
from pyramid.request import Request
from pyramid import testing 

def getRequest():
    r = Request({"wsgi.url_scheme":"http", "SERVER_NAME": "testserver.de","SERVER_PORT":80, "REQUEST_METHOD": "GET"})
    r.subpath = ["file1.txt"]
    return r


class viewTest(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        self.app = db_app.app_db()
        self.request = getRequest()
        user = User(u"test")
        r = self.app.root()
        self.context = db_app.createObj1(r)
        self.context2 = db_app.createObj2(r)
        self.context2.SetFile("file1", db_app.file2_1, user=user)
        self.context2.SetFile("file2", db_app.file2_2, user=user)

    def tearDown(self):
        user = User(u"test")
        r = self.app.root()
        r.Delete(self.context.id, user=user)
        r.Delete(self.context2.id, user=user)
        testing.tearDown()
        pass
    
    def test_views1(self):
        view = BaseView(self.context2, self.request)

        #urls
        self.assertRaises(ValueError, view.StaticUrl, "file.js")
        self.assert_(view.Url())
        self.assert_(view.Url(self.context))
        self.assert_(view.FolderUrl())
        self.assert_(view.FolderUrl(self.context))
        self.assert_(view.FileUrl("file1"))
        self.assert_(view.FileUrl("file1", self.context2))
        self.assert_(view.PageUrl())
        self.assert_(view.PageUrl(self.context, usePageLink=1))
        self.assert_(view.ResolveLink(str(self.context.id)))
        #self.assertRaises(HTTPFound, view.Redirect("there", messages=None))
        #self.assertRaises(HTTPOk, view.AjaxRelocate("here", messages=None))
        
        #files
        view.File()
        view.FileByID("file1")
        file = self.context2.GetFile("file1")
        view.SendFile(file)

        # header
        view.CacheHeader(Response(), user=None)
        view.NoCache(Response(), user=None)
        view.Modified(Response(), user=None)
        user = view.User()
        view.CacheHeader(Response(), user=user)
        view.NoCache(Response(), user=user)
        view.Modified(Response(), user=user)
        
        #users
        view.User()
        view.UserName()
        view.Allowed("test", context=None)
        view.Allowed("test", context=self.context)
        
        #values
        self.assert_(view.GetFormValue("test", default=123, method=None)==123)
        self.assert_(view.GetFormValue("test", default=123, method="GET")==123)
        self.assert_(view.GetFormValue("test", default=111, method="POST")==111)
        view.GetFormValues()
        view.GetFormValues(method="POST")

        #views
        view.RenderView(self.context, name="", secure=True, raiseUnauthorized=False)
        view.RenderView(self.context, name="test", secure=False, raiseUnauthorized=True)


    def test_views2(self):
        view2 = BaseView(self.context, self.request)
        #render fields
        self.assert_(view2.RenderFld("ftext"))
        self.assert_(view2.RenderFld("fnumber"))
        self.assert_(view2.RenderFld("fdate"))
        self.assert_(view2.RenderFld("flist"))
        self.assert_(view2.RenderFld("pool_type"))
        self.assert_(view2.RenderFld("pool_category"))
        self.assert_(view2.HtmlTitle())
        self.assert_(view2.FmtTextAsHTML("text"))
        self.assert_(view2.FmtDateText("2008/06/23 16:55", language=None))
        self.assert_(view2.FmtDateNumbers( "2008/06/23 16:55", language=None))
        self.assert_(view2.FmtSeconds(2584))
        self.assert_(view2.FmtBytes(135786))

    

                
        

if __name__ == '__main__':
    unittest.main()
