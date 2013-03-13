# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import Conf

from nive.cms.tests.db_app import *
from nive.cms.cmsview.view import *

from pyramid import testing 
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render

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


    def test_functions(self):
        view = Editor(self.page, self.request)
        self.assert_(view.GetEditorWidgets(self.page))
        self.assert_(view.IsEditmode())
        self.assertRaises(HTTPFound, view.editor)
        self.assertRaises(HTTPFound, view.exit)
        self.assertRaises(HTTPFound, view.exitapp)        


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

        # macros
        view.cmsIndex_tmpl()

        # edit forms
        view.context = self.page
        view.edit()
        view.context = b1
        view.edit()
        view.context = b2
        view.edit()
        view.context = b3
        view.edit()
        view.context = b4
        view.edit()
        view.context = b5
        view.edit()
        view.context = b6
        view.edit()
        view.context = b7
        view.edit()
        view.context = b8
        view.edit()
        view.context = b9
        view.edit()
        view.context = b0
        view.edit()
        
        # other views
        view.context = b3
        view.delfile()
        view.context = self.page
        view.delete()
        view.meta()
                
        # add forms
        view.context = self.page
        view.add()
        view.context = b1
        view.add()
        view.context = b2
        view.add()
        
        # test html widgets
        view.context = self.page
        view.cmsToolbox(self.page, elements=None)
        view.cmsEditorBlocks(self.page, elements=None)
        
        view.editBlockPage(page=self.page)
        view.editBlockElement(obj=b3)
        view.editBlockColumn(page=self.page, column=b2, name="left")
        view.editBlockList(obj=b1, page=None)
        
        view.elementAddWidget(obj=b5, addResponse=False)
        view.elementListWidget(obj=self.page, elements=None, addResponse=False)
        view.pageListWidget(page=self.root, pages=None)
        
        view.insertPageWidgets()
        view.insertAppWidgets()
        view.insertToolboxWidgets(self.page)
        
        view.breadcrumbs(addHome=0, link=True)
        view.selectType()
        view.selectPageElement()
                
        
    def test_templates(self):
        view = Editor(self.page, self.request)
        user = User(u"test")
        user.groups.append("group:editor")
        vrender = {"context":self.page, "view":view, "request": self.request}

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
        
        # page 
        values = view.add()
        values.update(vrender)
        render("nive.cms.cmsview:add.pt", values)
        values = view.add()
        values.update(vrender)
        render("nive.cms.cmsview:edit.pt", values)
        values = view.delete()
        values.update(vrender)
        render("nive.cms.cmsview:delete.pt", values)
        render("nive.cms.cmsview:meta.pt", values)

        # box
        values["context"] = b1
        values = view.add()
        values.update(vrender)
        render("nive.cms.cmsview:add.pt", values)
        values = view.add()
        values.update(vrender)
        render("nive.cms.cmsview:edit.pt", values)
        values = view.delete()
        values.update(vrender)
        render("nive.cms.cmsview:delete.pt", values)
        render("nive.cms.cmsview:meta.pt", values)

        # column        
        values["context"] = b2
        values = view.add()
        values.update(vrender)
        render("nive.cms.cmsview:add.pt", values)
        values = view.add()
        values.update(vrender)
        render("nive.cms.cmsview:edit.pt", values)
        render("nive.cms.cmsview:meta.pt", values)

        # elements
        for e in (b4,b5,b6,b7,b8,b9,b0):
            # element add form
            self.request.POST={"pool_type":e.GetTypeID()}
            values = view.add()
            values.update(vrender)
            render("nive.cms.cmsview:add.pt", values)
            values["context"] = e
            render("nive.cms.cmsview:edit.pt", values)
            render("nive.cms.cmsview:meta.pt", values)



if __name__ == '__main__':
    unittest.main()
