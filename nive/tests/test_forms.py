
import time
import unittest

from nive.definitions import *
from nive.forms import *
from nive.events import Events
from nive.views import BaseView
from nive.security import User as UserO
from nive.helper import Request
import db_app


data1_1 = { u"ftext": "this is text!",
            u"fnumber": "123456",
            u"fdate": "2008-06-23 16:55:20",#
            u"flist": ["item 1", "item 2", "item 3"],
            u"fmselect": "item 5",
            u"funit": "35",
            u"funitlist": "34\n35\n36",
            u"pool_type": "type1"}

data1_2 = { u"ftext": "this is a new text!",
            u"funit": "0",
            u"fdate": "2008-06-23 12:00:00"}


class Viewy(BaseView):
    def __init__(self):
        self.request = Request()
        self.context = None
    
    def User(self):
        return UserO(u"test")

# -----------------------------------------------------------------
from pyramid import testing

class FormTest(unittest.TestCase):

    def setUp(self):
        self.app = db_app.app_nodb()
        self.view = Viewy()
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.config = testing.setUp(request=request)
    
    def tearDown(self):
        self.app.Close()
        testing.tearDown()
        pass
    

    def test_form(self, **kw):
        form = Form(loadFromType="type1", context=None, request=Request(), app=self.app, view=self.view)
        form.Setup()
        self.assert_(form.GetFields())
        form._SetUpSchema()
        self.assertFalse(form.GetField("test000"))
        request = Request()
        form.LoadDefaultData()
        form.GetActions(True)
        form.GetActions(False)
        form.GetFormValue("test", request=request, method=None)
        form.GetFormValues(request)
        #form.StartForm()
        #form.StartRequestGET()
        #form.Cancel()


    def test_empty(self, **kw):
        form = Form(loadFromType="type1", app=self.app, view=self.view)
        form.Setup()
        result, data = form.Extract({"ftext": ""})
        self.assert_(data.get("ftext")=="")
        
        form = Form(loadFromType="type2", app=self.app, view=self.view)
        form.Setup()
        result, data = form.Extract({"fstr": ""})
        self.assert_(data.get("fstr")=="" and data.get("ftext")==None)

        
    def test_values(self, **kw):
        form = Form(loadFromType="type1", app=self.app, view=self.view)
        form.Setup()

        v,d,e = form.Validate(data=data1_1)
        self.assert_(v, e)
        
        v,d,e = form.Validate(data1_2)
        self.assertFalse(v, e)
        
        result, data = form.Extract(data1_1)
        self.assert_(data)
        result, data = form.Extract(data1_2)
        self.assert_(data)        


    def test_values2(self, **kw):
        form = Form(loadFromType="type1", app=self.app, view=self.view)
        subsets = {"test": {"fields": ["ftext",u"funit"]}}
        form.subsets = subsets
        form.Setup(subset="test")
        v,d,e = form.Validate(data1_2)
        self.assert_(v, e)

        form = Form(loadFromType="type1", app=self.app, view=self.view)
        subsets = {u"test": {"fields": [u"ftext", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "section", "fields": [u"funit"]})]}}
        form.subsets = subsets
        form.Setup(subset=u"test")
        v,d,e = form.Validate(data1_2)
        self.assert_(v, e)

        result, data = form.Extract(data1_1)
        self.assert_(data)
        result, data = form.Extract(data1_2)
        self.assert_(data)


    def test_html(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = u"upload"
        form.css_class = u"niveform"
        form.Setup()

        v,d,e = form.Validate(data1_1)
        self.assert_(v, e)
        
        v,d,e = form.Validate(data1_2)
        self.assertFalse(v, e)
        form.Render(d, msgs=None, errors=None)
        
        result, data = form.Extract(data1_1)
        self.assert_(data)
        result, data = form.Extract(data1_2)
        self.assert_(data)
        
        
    def test_html2(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = u"upload"
        form.css_class = u"niveform"
        form.subsets = {u"test": {"fields": [u"ftext",u"funit"]}}
        form.Setup(subset=u"test")
        v,d,e = form.Validate(data1_2)
        self.assert_(v, e)
        form.Render(d, msgs=None, errors=None)


    def test_html3(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = u"upload"
        form.css_class = u"niveform"
        form.subsets = {u"test": {"fields": [u"ftext", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "section", "fields": [u"funit"]})]}}
        form.Setup(subset=u"test")
        v,d,e = form.Validate(data1_2)
        self.assert_(v, e)
        form.Render(d, msgs=None, errors=None)


    def test_tool(self, **kw):
        tool = self.app.GetTool("nive.components.tools.example")
        form = ToolForm(loadFromType=tool.configuration, context=tool,app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = u"upload"
        form.css_class = u"niveform"
        form.actions = [
            Conf(**{"id": "default", "name": "Speichern", "method": "StartForm", "description": "", "hidden":True, "css_class":"", "html":"", "tag":""}),
            Conf(**{"id": "run",       "name": "Speichern", "method": "RunTool",      "description": "", "css_class":"", "html":"", "tag":""}),
            Conf(**{"id": "cancel",  "name": "Abbrechen", "method": "Cancel",    "description": "", "css_class":"", "html":"", "tag":""})
            ]
        form.Setup()
        data = {"parameter1": "True", "parameter2": "test"}

        form.Process()
        req = {"run$":1}
        req.update(data)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()
        
        form.subsets = {u"test": {"fields": [u"parameter1"]}}
        form.Setup("test")
        form.Process()
        req = {"run$":1}
        req.update(data)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()

        form.subset = "test"
        form.subsets = {u"test": {"fields": [u"parameter1", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "section", "fields": [u"parameter2"]})]}}
        form.Setup("test")
        form.Process()
        req = {"run$":1}
        req.update(data)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()
        

    def test_json(self, **kw):
        form = JsonMappingForm(request=Request(),app=self.app, view=self.view)
        form.fields = (
            FieldConf(id="parameter1", datatype="text", size=1000),
            FieldConf(id="parameter2", datatype="string", size=100),
        )
        form.Setup()

        data = {"parameter1": "True", "parameter2": "test"}
        r,v,e = form.Validate(data)
        self.assert_(r, e)
        self.assert_(isinstance(v, dict))
        data = {"parameter1": "True", "parameter2": "test"}
        r,v = form.Extract(data)
        self.assert_(r, v)
        self.assert_(isinstance(v, dict))
        

    def test_actions(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = u"upload"
        form.css_class = u"niveform"

        # create
        form.actions = [
        Conf(**{"id": "default", "method": "StartForm","name": "Initialize", "hidden":True,  "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "create",  "method": "CreateObj","name": "Create",     "hidden":False, "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "cancel",  "method": "Cancel",   "name": "Cancel",     "hidden":False, "description": "", "css_class":"", "html":"", "tag":""})
        ]
        form.Setup()
        a = form.GetActions(removeHidden=False)
        self.assert_(len(a)==3)
        a = form.GetActions(removeHidden=True)
        self.assert_(len(a)==2)


    def test_fields(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = u"upload"
        form.css_class = u"niveform"
        # create
        form.Setup()

        f = form.GetFields(removeReadonly=True)
        self.assert_(len(f)==8)
        f = form.GetFields(removeReadonly=False)
        self.assert_(len(f)==13)

        

class FormTest_db(unittest.TestCase):

    def setUp(self):
        self.app = db_app.app_db()
        self.request = testing.DummyRequest()
        self.request._LOCALE_ = "en"
        self.config = testing.setUp(request=self.request)
        self.remove=[]
    
    def tearDown(self):
        v = Viewy()
        u = v.User()
        root = self.app.root()
        for r in self.remove:
            root.Delete(r, u)
        self.app.Close()
        testing.tearDown()
        pass
    
    def test_obj(self, **kw):
        root = self.app.GetRoot()
        v = Viewy()
        form = ObjectForm(loadFromType="type1", context=root, view=v, request=Request(), app=self.app)
        form.formUrl = "form/url"
        form.cssID = u"upload"
        form.css_class = u"niveform"

        # create
        form.actions = [
        Conf(**{"id": "default", "method": "StartForm","name": "Initialize", "hidden":True,  "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "create",  "method": "CreateObj","name": "Create",     "hidden":False, "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "cancel",  "method": "Cancel",   "name": "Cancel",     "hidden":False, "description": "", "css_class":"", "html":"", "tag":""})
        ]
        form.Setup(addTypeField = True)
        
        count = self.app.db.GetCountEntries()
        result, data, action=form.Process()
        self.assert_(result)
        self.assertEqual(action.id,"default")
        self.assertEqual(count, self.app.db.GetCountEntries())

        req = {"create$":1, "pool_type":"type1"}
        req.update(data1_1)
        form.request = req
        result, data, action=form.Process()
        self.assert_(result)
        self.assertEqual(action.id,"create")
        self.assertEqual(count+1, self.app.db.GetCountEntries())
        self.remove.append(result.id)
        
        req = {"cancel$":1}
        form.request = req
        result, data, action=form.Process()
        self.assert_(result)
        self.assertEqual(action.id,"cancel")
        self.assertEqual(count+1, self.app.db.GetCountEntries())
        
        form = ObjectForm(loadFromType="type1", context=root, view=v, request=Request(), app=self.app)
        form.subsets = {u"test": {"fields": [u"ftext",u"funit"], 
                                  "actions": [u"default", u"create",u"cancel"]}}
        form.Setup(subset = "test", addTypeField = True)
        result, data, action=form.Process()
        self.assert_(result)
        self.assertEqual(action.id,"default")
        self.assertEqual(count+1, self.app.db.GetCountEntries())

        req = {"create$":1, "pool_type":"type1"}
        req.update(data1_2)
        form.request = req
        result, data, action=form.Process()
        self.assert_(result)
        self.assertEqual(action.id,"create")
        self.assertEqual(count+2, self.app.db.GetCountEntries())
        self.remove.append(result.id)
        
        req = {"cancel$":1}
        form.request = req
        result, data, action=form.Process()
        self.assert_(result)
        self.assertEqual(action.id,"cancel")
        self.assertEqual(count+2, self.app.db.GetCountEntries())

        form = ObjectForm(loadFromType="type1", context=root, view=v, request=Request(), app=self.app)
        form.subsets = {u"test": {"fields": [u"ftext", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "section", "fields": [u"fnumber"]})], 
                                  "actions": [u"default", u"create",u"cancel"]}}
        form.Setup(subset = "test", addTypeField = True)
        result, data, action=form.Process()
        self.assert_(result)
        self.assertEqual(action.id,"default")
        self.assertEqual(count+2, self.app.db.GetCountEntries())
        
        req = {"create$":1, "pool_type":"type1"}
        req.update(data1_2)
        form.request = req
        result, data, action=form.Process()
        self.assert_(result)
        self.assertEqual(action.id,"create")
        self.assertEqual(count+3, self.app.db.GetCountEntries())
        self.remove.append(result.id)

        req = {"cancel$":1}
        form.request = req
        result, data, action=form.Process()
        self.assert_(result)
        self.assertEqual(action.id,"cancel")
        self.assertEqual(count+3, self.app.db.GetCountEntries())


    def test_obj2(self, **kw):
        user = UserO(u"test")
        root = self.app.GetRoot()
        obj = root.Create("type1", data1_2, user)
        self.remove.append(obj.id)
        v = Viewy()

        form = ObjectForm(loadFromType="type1", context=obj, view=v, request=Request(), app=self.app)
        form.formUrl = "form/url"
        form.cssID = u"upload"
        form.css_class = u"niveform"
        count = self.app.db.GetCountEntries()
        # edit
        form.actions = [
        Conf(**{"id": "default", "method": "StartObject","name": "Initialize",    "hidden":True, "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "save",       "method": "UpdateObj","name": "Save",         "hidden":False, "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "cancel",  "method": "Cancel",    "name": "Cancel",         "hidden":False, "description": "", "css_class":"", "html":"", "tag":""})
        ]
        form.Setup()
        form.Process()
        req = {"save$":1}
        req.update(data1_1)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()
        d = form.LoadObjData()
        self.assertEqual(count, self.app.db.GetCountEntries())

        form = ObjectForm(loadFromType="type1", context=obj, view=v, request=Request(), app=self.app)
        form.subsets = {u"test": {"fields": [u"ftext",u"funit"], 
                                  "actions": [u"defaultEdit",u"edit",u"cancel"]}}
        form.Setup(subset = "test")
        form.Process()
        req = {"edit$":1}
        req.update(data1_2)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()
        self.assertEqual(count, self.app.db.GetCountEntries())

        form = ObjectForm(loadFromType="type1", context=obj, view=v, request=Request(), app=self.app)
        form.subsets = {u"test": {"fields": [u"ftext", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "section", "fields": [u"fnumber"]})],
                                  "actions": [u"defaultEdit",u"edit",u"cancel"]}}
        form.subset = "test"
        form.Setup(subset = "test")
        form.Process()
        req = {"edit$":1}
        req.update(data1_2)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()
        self.assertEqual(count, self.app.db.GetCountEntries())

        form = ObjectForm(loadFromType="type1", context=obj, view=v, request=Request(), app=self.app)
        form.subsets = {u"test": {"fields": [u"ftext", FieldConf(**{"fields": [u"parameter2"], "id": "section1", "name": "Section 1", "datatype": "section"})],
                                  "actions": [u"defaultEdit",u"edit",u"cancel"]}}
        try:
            form.Setup(subset="test3")
            form.Process()
            self.assert_(False)
        except ConfigurationError:
            pass
        self.assertEqual(count, self.app.db.GetCountEntries())


    def test_json(self, **kw):
        user = UserO(u"test")
        root = self.app.GetRoot()
        obj = root.Create("type1", data1_2, user)
        obj.data["fjson"] = {}
        obj.Commit(user=user)
        self.remove.append(obj.id)
        v = Viewy()

        form = JsonMappingForm(request=Request(),app=self.app,context=obj, view=v)
        form.fields = (
            FieldConf(id="parameter1", datatype="string", size=1000),
            FieldConf(id="parameter2", datatype="string", size=100),
        )
        form.jsonDataField = "fjson"
        form.Setup()

        data = {"parameter1": "True", "parameter2": "test"}
        form.request = data
        form.Process()
        
        data["edit$"] = 1
        form.request = data
        form.Process()

        self.assert_(obj.data.get("ftext"))
        

