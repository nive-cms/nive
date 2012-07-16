# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import *

from nive.cms.tests.db_app import *
from nive.cms.cmsview.view import *

from pyramid import testing 


class tCMS(unittest.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.config = testing.setUp(request=request)
        self.app = app()
        self.app.Startup(self.config)
        self.root = self.app.root("editor")
        user = User(u"test")
        user.groups.append("group:editor")
        self.page = create_page(self.root, user)
        self.request.context = self.page

    def tearDown(self):
        user = User(u"test")
        self.root.Delete(self.page.id, user=user)
        self.app.Close()
        testing.tearDown()

    def test_views1(self):
        view = Editor(self.page, self.request)
        user = User(u"test")
        user.groups.append("group:editor")

        b1 = create_box(self.page, user)
        b2 = create_column(self.page, user)
        b3 = create_file(self.page, user)
        b4 = create_image(self.page, user)
        b5 = create_media(self.page, user)
        b6 = create_note(self.page, user)
        b7 = create_text(self.page, user)
        b8 = create_spacer(self.page, user)
        b9 = create_link(self.page, user)
        b0 = create_menublock(self.page, user)

        r=view.view()
        self.assertEqual(r.status_int, 200)
        self.assertGreater(r.content_length, 2000)

        view.cmsMain(self.page, elements=None)
        view.cmsEditorBlocks(self.page, elements=None)
        view.editBlockPage(page=self.page)
        view.editBlockElement(obj=b3)
        view.editBlockColumn(page=self.page, column=b2, name="left")
        view.editBlockList(obj=b1, page=None)
        view.elementAddWidget(obj=b5, addResponse=False)
        view.elementListWidget(obj=self.page, elements=None, addResponse=False)
        view.pageListWidget(page=self.root, pages=None)
        view.breadcrumbs(addHome=0, link=True)
        view.insertPageWidgets()
        view.insertAppWidgets()
        view.insertToolboxWidgets(self.page)
        view.getEditorWidgets(self.page)
                
        r=view.edit()
        self.assertGreater(r["content"], 500)
        view.context = b3
        view.delfile()
        view.context = self.page
        
        r=view.add()
        self.assertGreater(r["content"], 500)
        view.delete()
        view.selectType()
        view.selectPageElement()
        
        
        
        

if __name__ == '__main__':
    unittest.main()
