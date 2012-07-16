# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import *

from nive.cms.tests.db_app import *

from nive.cms.design.view import *

from pyramid import testing 
from pyramid.renderers import render



class tDesign(unittest.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.config = testing.setUp(request=request)
        self.request = request
        self.app = app()
        self.app.Startup(self.config)        
        self.root = self.app.root()
        user = User(u"test")
        user.groups.append("group:editor")
        self.page = create_page(self.root, user)
        self.request.context = self.page

    def tearDown(self):
        user = User(u"test")
        self.app.Close()
        testing.tearDown()
        root = self.app.root()
        self.root.Delete(self.page.id, user=user)

    def test_views1(self):
        view = Design(self.root, self.request)

        view.index_tmpl()
        view.view(cmsview = None)
        view.HtmlTitle()
        view.navigationTop(addHome=1)
        view.navigationTop(addHome=0)
        view.navigationTree(addHome=1, page=None)
        view.navigationTree(addHome=0, page=None)
        view.navigationTree(addHome=1, page=self.page)
        view.navigationSub(page=None)
        view.navigationSub(page=self.page)
        view.breadcrumbs(addHome=0)
        view.breadcrumbs(addHome=1)
    
        view = Design(self.page, self.request)

        view.index_tmpl()
        view.view(cmsview = None)
        view.HtmlTitle()
        view.navigationTop(addHome=1)
        view.navigationTop(addHome=0)
        view.navigationTree(addHome=1, page=None)
        view.navigationTree(addHome=0, page=None)
        view.navigationSub(page=None)
        view.breadcrumbs(addHome=0)
        view.breadcrumbs(addHome=1)
        
        
    def test_templates(self):
        user = User(u"test")
        user.groups.append("group:editor")
        view = Design(self.page, self.request)
        b1 = create_box(self.page, user)
        render("nive.cms.design:templates/box.pt", {"context":b1, "view":view})
        b2 = create_column(self.page, user)
        render("nive.cms.design:templates/column.pt", {"context":b2, "view":view})
        b3 = create_file(self.page, user)
        render("nive.cms.design:templates/file.pt", {"context":b3, "view":view})
        b4 = create_image(self.page, user)
        render("nive.cms.design:templates/image.pt", {"context":b4, "view":view})
        b5 = create_media(self.page, user)
        render("nive.cms.design:templates/media.pt", {"context":b5, "view":view})
        b6 = create_note(self.page, user)
        render("nive.cms.design:templates/note.pt", {"context":b6, "view":view})
        b7 = create_text(self.page, user)
        render("nive.cms.design:templates/text.pt", {"context":b7, "view":view})
        b8 = create_spacer(self.page, user)
        render("nive.cms.design:templates/spacer.pt", {"context":b8, "view":view})
        b9 = create_link(self.page, user)
        render("nive.cms.design:templates/link.pt", {"context":b9, "view":view})
        b10 = create_code(self.page, user)
        render("nive.cms.design:templates/code.pt", {"context":b10, "view":view})
        b0 = create_menublock(self.page, user)
        render("nive.cms.design:templates/menublock.pt", {"context":b0, "view":view, "request": self.request})
        render("nive.cms.design:templates/page.pt", {"context":self.page, "view":view, "cmsview":None})
        
        # render page with elements
        r=view.view()
        self.assertEqual(r.status_int, 200)
        self.assertGreater(r.content_length, 2000)
        


if __name__ == '__main__':
    unittest.main()
