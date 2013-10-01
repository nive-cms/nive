
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
    r = Request({"PATH_INFO": "http://aaa.com/test?key=123", "wsgi.url_scheme":"http", "SERVER_NAME": "testserver.de","SERVER_PORT":80, "REQUEST_METHOD": "GET"})
    r.subpath = ["file1.txt"]
    r.context = None
    return r

class viewModule(object):
    mainTemplate = "nive.cms.design:templates/index.pt"
    templates = u"nive.cms.design:templates/"
    parent = None
    static = u""

class viewTest(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        self.request = testing.DummyRequest()
        self.request._LOCALE_ = "en"
        self.request.subpath = ["file1.txt"]
        self.request.context = None
        self.app = db_app.app_db()
        #self.request = getRequest()
        user = User(u"test")
        r = self.app.root()
        self.context = db_app.createObj1(r)
        self.context2 = db_app.createObj2(r)
        self.context2.StoreFile("file1", db_app.file2_1, user=user)
        self.context2.StoreFile("file2", db_app.file2_2, user=user)

    def tearDown(self):
        user = User(u"test")
        r = self.app.root()
        r.Delete(self.context.id, user=user)
        r.Delete(self.context2.id, user=user)
        testing.tearDown()
        pass
    

    def test_excp(self):
        def rtest():
            raise Unauthorized, "test"
        self.assertRaises(Unauthorized, rtest)
    

    def test_urls(self):
        view = BaseView(self.context2, self.request)

        #urls
        self.assert_(view.Url())
        self.assert_(view.Url(self.context))
        self.assert_(view.FolderUrl())
        self.assert_(view.FolderUrl(self.context))
        self.assertRaises(ValueError, view.StaticUrl, "file.js")
        self.assert_(view.FileUrl("file1"))
        self.assert_(view.FileUrl("file1", self.context2))
        self.assert_(view.PageUrl())
        self.assert_(view.PageUrl(self.context, usePageLink=1))
        self.assert_(view.CurrentUrl(retainUrlParams=False))
        self.assert_(view.CurrentUrl(retainUrlParams=True))

        urls = ["page_url", "obj_url", "obj_folder_url", "parent_url"]
        for url in urls:
            self.assert_(view.ResolveUrl(url, object=None))
            self.assert_(view.ResolveUrl(url, object=self.context2))
        self.assertFalse(view.ResolveUrl("", object=None))
        
        self.assert_(view.ResolveLink(str(self.context.id))!=str(self.context.id))
        self.assert_(view.ResolveLink("none")=="none")

    
    def test_http(self):
        view = BaseView(self.context2, self.request)
        
        self.assertRaises(HTTPFound, view.Redirect, "nowhere", messages=None, slot="")
        self.assertRaises(HTTPFound, view.Redirect, "nowhere", messages=[u"aaa",u"bbb"], slot="")
        self.assertRaises(HTTPFound, view.Redirect, "nowhere", messages=[u"aaa",u"bbb"], slot="test")
        self.assertRaises(HTTPOk, view.Relocate, "nowhere", messages=None, slot="", raiseException=True)
        self.assertRaises(HTTPOk, view.Relocate, "nowhere", messages=[u"aaa",u"bbb"], slot="", raiseException=True)
        self.assertRaises(HTTPOk, view.Relocate, "nowhere", messages=[u"aaa",u"bbb"], slot="test", raiseException=True)
        self.assert_(view.Relocate("nowhere", messages=[u"aaa",u"bbb"], slot="test", raiseException=False)==u"")
        view.ResetFlashMessages(slot="")
        view.ResetFlashMessages(slot="test")
        view.AddHeader("name", "value")


    def test_send(self):
        view = BaseView(self.context2, self.request)
        self.assert_(view.SendResponse("the response", mime="text/html", raiseException=False, filename=None))
        self.assert_(view.SendResponse("the response", mime="text/html", raiseException=False, filename="file.html"))
        self.assertRaises(HTTPOk, view.SendResponse, "the response", mime="text/html", raiseException=True, filename="file.html")        


    def test_files(self):
        view = BaseView(self.context2, self.request)
        #files
        view.File()
        file = self.context2.GetFile("file1")
        view.SendFile(file)

    
    def test_render(self):
        view = BaseView(self.context2, self.request)
        self.assert_(view.index_tmpl(path=None)==None)
        self.assert_(view.index_tmpl(path="nive.cms.design:templates/index.pt"))
        
        view.viewModule=viewModule()
        self.assert_(view.index_tmpl(path=None))
        
        self.assertRaises(ValueError, view.DefaultTemplateRenderer, {}, templatename = None)
        view.DefaultTemplateRenderer({}, templatename = "spacer.pt")

        #views
        view.RenderView(self.context, name="", secure=True, raiseUnauthorized=False)
        view.RenderView(self.context, name="test", secure=False, raiseUnauthorized=True)
        view.RenderView(self.context, name="", secure=True, raiseUnauthorized=False, codepage="utf-8")
        view.IsPage(self.context)
        view.IsPage()
        view.tmpl()

    
    def test_cache(self):
        view = BaseView(self.context2, self.request)
        # header
        view.CacheHeader(Response(), user=None)
        view.NoCache(Response(), user=None)
        view.Modified(Response(), user=None)
        user = view.User()
        view.CacheHeader(Response(), user=user)
        view.NoCache(Response(), user=user)
        view.Modified(Response(), user=user)
        

    def test_user(self):
        view = BaseView(self.context2, self.request)
        #users
        view.user
        view.User()
        view.UserName()
        view.Allowed("test", context=None)
        view.Allowed("test", context=self.context)
        view.InGroups([])
        

    def test_forms(self):
        view = BaseView(self.context2, self.request)
        #values
        self.assert_(view.GetFormValue("test", default=123, method=None)==123)
        self.assert_(view.GetFormValue("test", default=123, method="GET")==123)
        self.assert_(view.GetFormValue("test", default=111, method="POST")==111)
        view.GetFormValues()
        view.GetFormValues(method="POST")
        
        self.assert_(view.FmtURLParam(**{u"aaa":123,u"bbb":u"qwertz"}))
        self.assert_(view.FmtFormParam(**{u"aaa":123,u"bbb":u"qwertz"}))



    def test_renderer(self):
        view2 = BaseView(self.context, self.request)
        #render fields
        self.assert_(view2.RenderField("ftext"))
        self.assert_(view2.RenderField("fnumber"))
        self.assert_(view2.RenderField("fdate"))
        self.assert_(view2.RenderField("flist"))
        self.assert_(view2.RenderField("pool_type"))
        self.assert_(view2.RenderField("pool_category"))
        self.assert_(view2.HtmlTitle()=="")
        self.request.environ["htmltitle"] = "test"
        self.assert_(view2.HtmlTitle()=="test")
        self.assert_(view2.FmtTextAsHTML("text"))
        self.assert_(view2.FmtDateText("2008/06/23 16:55", language=None))
        self.assert_(view2.FmtDateNumbers( "2008/06/23 16:55", language=None))
        self.assert_(view2.FmtSeconds(2584))
        self.assert_(view2.FmtBytes(135786))

