# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import *
from nive.portal import Portal
from nive.i18n import _

from nive.tests.db_app import *
from nive.adminview import view
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
        self.app.Register(view.configuration)
        self.app.Register(view.dbAdminConfiguration)
        self.app.Startup(self.config)
        self.request.context = self.app
    

    def tearDown(self):
        self.app.Close()
        testing.tearDown()


    def test_views(self):
        v = view.AdminView(context=self.app, request=self.request)
        self.assert_(v.RenderConf(view.configuration))
        self.assert_(v.Format(view.configuration, view.configuration.id))
        self.assert_(v.AdministrationLinks(context=None))
        self.assert_(v.AdministrationLinks(context=self.app))
        self.assert_(v.index_tmpl())
        self.assert_(v.getAdminWidgets())
        v.view()
        self.assert_(v.editbasics())
        self.assert_(v.editdatabase())
        self.assert_(v.editportal())
        self.assert_(v.tools())


    
    def test_form(self):
        v = TestView(context=self.app, request=self.request)
        form = view.ConfigurationForm(context=view.configuration, request=self.request, view=v, app=self.app)
        form.fields = (
            FieldConf(id=u"title",           datatype="string", size=255,  required=0, name=_(u"Application title")),
            FieldConf(id=u"description",     datatype="text",   size=5000, required=0, name=_(u"Application description")),
            FieldConf(id=u"workflowEnabled", datatype="bool",   size=2,    required=0, name=_(u"Enable workflow engine")),
            FieldConf(id=u"fulltextIndex",   datatype="bool",   size=2,    required=0, name=_(u"Enable fulltext index")),
            FieldConf(id=u"frontendCodepage",datatype="string", size=10,   required=1, name=_(u"Codepage used in html frontend")),
        )
        form.Setup()
        self.request.POST = {"name": "testuser", "email": "testuser@domain.net"}
        self.request.GET = {}

        self.assert_(form.Start(None, None))
        self.assert_(form.Update(None, None))
             

if __name__ == '__main__':
    unittest.main()