#----------------------------------------------------------------------
# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#----------------------------------------------------------------------

"""
nive Form description
------------------------
This class manages cms integration, field configuration, actions and form processing. 
Rendering, validation and data extraction is not included and requires a separate form 
library (nive.components.reform).

nive Forms can be connected to existing object or tool configurations and reuse all
therein defined fields for forms. To setup a form like this use ``Setup(subset='action to handled')`` 
to load fields, actions, subsets automatically from the objects configuration. 

A form does represent a single action but a set of form fields and multiple actions. nive forms can 
be rendered as ``subsets`` with a reduced selection of fields and different actions. 

This is an example to be used in object view code: ::

    form = ObjectForm(view=self, 
                      loadFromType=self.context.configuration)
    form.Setup(subset="edit") 
    # process and render the form.
    result, data, action = form.Process()

*view* must be an instance of `nive.views.BaseView`.  
*data* will contain the rendered HTML whether the is loaded for the first time, validated ok or 
not. *result* will be *false* if the form input did not validate. The *ObjectForm* already includes 
all necessary functions to load data initially, create an object and store data for existing objects.
All you have to do is switch the subset from *edit* to *create*. ::

    form = ObjectForm(view=self,
                      loadFromType=self.context.configuration)
    form.Setup(subset="create")
    # process and render the form.
    result, data, action = form.Process()

The configuration is loaded from the object configuration itself so all field settings are 
dynamically included. In fact the example above works for *any* object type.

Form action callback methods use the following footage: ::

    def Method(self, action, **kw):
        ...
        return result, data

These callback methods are automatically looked up and executed in Process(). Use action.method to
link a method to a specific form action. Pass `user` as kw argument if the forms view attribute is 
None. If form.view is set view.User() is used to lookup the current user.

A custom HTMLForm example: ::

    form = HTMLForm(view=self)
    form.actions = [
        Conf(id="default",    method="StartForm",             name=u"Initialize",          hidden=True),
        Conf(id="create",     method="ReturnDataOnSuccess",   name=u"Create a new group",  hidden=False),
    ]
    form.fields = [
        FieldConf(id="id",   name=u"Group id",   datatype="string", size="20", required=True),
        FieldConf(id="name", name=u"Group name", datatype="string", size="40", required=True)
    ]
    form.Setup()
    data, html, action = form.Process()


Callback for dynamic list item loading: ::

    def loadGroups(fieldconf, object):
        return [{"id": id, "name":name}]


    FieldConf(..., listItems=loadGroups, ...)


In short forms are explained as follows:

- fields are defined by field definitions as specified in :py:class:`nive.definitions.FieldConf`.
- configured fields are stored as list in self.fields.
- for display order and grouping self.subsets is used. Each subset is a list of field ids.
- subsets can be any selection and reference fields by id
- actions are mapped as buttons for the html form and callable for the result
- fields can directly be loaded from type or set manually. if loadFromType is specified, fields are loaded from this type. 
- create and edit can be used as default behavior for objects. 
- custom messages can be defined for errors and success of forms

**Please note:** These form classes are for autogenerating forms. If you need more control over validation
or rendering use a form library directly. 


Control sets for Select and Radio fields
========================================
Conditional sets can be automatically shown and hidden by setting a list `controlset:True`
and extending each listitem with a fields list. :: 

      FieldConf(id="flist",   
                datatype="list",   
                size=100,  
                name="flist", 
                settings={"controlset":True},
                listItems=[Conf(id="item 1", name="Item 1", 
                                fields=[FieldConf(id="ftext",datatype="text",size=10,name="ftext")]),
                           Conf(id="item 2", name="Item 2", 
                                fields=[FieldConf(id="fnum",datatype="number",size=8,name="fnum")])
                           ]
                ),

Example
=======
Internally the form uses a structure like in the following manually defined form example ::

    fields  = [
      FieldConf(id="ftext",   datatype="text",   size=1000, name="ftext", fulltext=1),
      FieldConf(id="fnumber", datatype="number", size=8,    name="fnumber", required=1),
      FieldConf(id="fdate",   datatype="datetime", size=8,  name="fdate"),
      FieldConf(id="flist",   datatype="list",   size=100,  name="flist", 
                listItems=[{"id": "item 1", "name":"Item 1"},
                             {"id": "item 2", "name":"Item 2"}]),
      FieldConf(id="fmselect", datatype="mselection", size=50, name="fmselect"),
    ]
    
    actions = [
      Conf(id="default",    method="StartForm", name="Initialize", hidden=True),
      Conf(id="defaultEdit",method="LoadUser",  name="Initialize", hidden=True),
      Conf(id="create",     method="AddUser",   name="Create",     hidden=False),
      Conf(id="edit",       method="Update",    name="Edit",       hidden=False)
    ]
    
    subsets = {
      "create": {"fields":  ["ftext", "fnumber", "fdate"], 
                 "actions": ["create"],
                 "defaultAction": "default"},
      "create2":{"fields":  ["ftext", "fnumber", "fdate", "flist", "fmselect"], 
                 "actions": ["create"],
                 "defaultAction": "default"},
      "edit":   {"fields":  ["ftext"], 
                 "actions": ["edit"],
                 "defaultAction": "defaultEdit"},
    }
    
    form = Form(view=self)
    form.fields = fields
    form.actions = actions
    form.subsets = subsets
    form.Setup(subset="create")
    # validating data
    result,data,errors = form.Validate(data)
    
Requires: Events

--------------------------------------------------------------------------
"""

import copy, json
from types import StringType

from pyramid.url import static_url

from nive.definitions import Conf, FieldConf, ConfigurationError
from nive.definitions import ISort
from nive.events import Events

from nive.components import reform
from nive.components.reform.form import Form as ReForm
from nive.components.reform.schema import null, Invalid
from nive.components.reform.exception import ValidationFailure

from nive.components.reform.reformed import SchemaFactory
from nive.components.reform.reformed import zpt_renderer
from nive.components.reform.i18n import _


class ValidationError(Exception):
    """
    Used for validation failures
    """

""" 
0.9.7 changed nive.Form:
- renamed parameter `redirect_success` to `redirectSuccess` and pass as **kw argument to functions
- form action method footage has changed: `def Method(self, action, **kw)`

0.9.4 changed nive.Form:
- __init__ parameters if view is not None: app, request, context are extracted from view context
- added Setup(subset) function
- removed LoadConfiguration()
- ObjectForm.AddTypeField() removed. Use Setup(addTypeField=True).
- form conf changed: object.configuration.forms = {"subset": {"fields": [...], "actions": [...]}}
- changed password widgets
"""

class Form(Events, ReForm):
    """
    Base form class.
    """
    _schemaFactory = SchemaFactory
    default_renderer = zpt_renderer

    # form configuration values
    fields = None
    actions = None
    subsets = None
    subset = None
    loadFromType = None
    
    
    def __init__(self, view=None, loadFromType=None, context=None, request=None, app=None, **kw):
        """
        Initialize form context. If view is not None and context, request, app are automatically
        extracted from the view object. Form fields and actions are processed in Setup(). 
        
        Please note: `view` must be an instance of `nive.views.BaseView`  
        """
        # form context
        self.view = view
        self.context = context or view.context
        self.request = request or view.request
        self.app = app or self.context.app
        
        if loadFromType:
            self.loadFromType = loadFromType

        # optional form parameters
        self.title = u""
        self.description = u""
        self.formid = u""
        self.startEmpty = False
        self.method = u"POST"
        
        # reform setup
        self._c_form = None
        self._c_fields = None
        self._c_actions = None
        ReForm.__init__(self, **kw)
        
        self.Signal("init")
            
            
    def Setup(self, subset=None):
        """
        1) Load fields from object definition
        2) Loads subsets and actions from object form definition
        
        Event
        - loadFields() after fields have been loaded
        """
        self._c_form = None
        self._c_fields = None
        self._c_actions = None
        self.subset=subset

        subsets=self.subsets
        config = None

        # load form fields
        if self.loadFromType:
            typeOrConfiguration = self.loadFromType
            if isinstance(typeOrConfiguration, basestring):
                config = self.app.GetObjectConf(typeOrConfiguration)
                if not config:
                    raise ConfigurationError, "Type not found (%s)" % (str(typeOrConfiguration))
            else:
                config = typeOrConfiguration
            self.loadFromType = config
        
        # unconfigured form
        if not subset and not subsets and not config and not self.fields:
            raise ConfigurationError, "No form fields defined"
        # unknown subset
        if subset and (not subsets or not subset in subsets):
            raise ConfigurationError, "Unknown form subset"

        # field lookup
        #(1) subsets[subset]["fields"]
        #(x) subsets[subset]
        #(3) type["form"][subset]["fields"]
        #(x) type["form"][subset]
        #(5) fields
        #(6) config.fields
        #(7) *fields.controlset=True -> field.listItems[].fields
        temp = None
        if subsets and subset in subsets and "fields" in subsets[subset]:
            #(1)
            temp = subsets[subset]["fields"]
        elif config and "forms" in config and config.forms and subset in config.forms and "fields" in config.forms[subset]:
            #(3)
            temp = config.forms[subset]["fields"]
        elif self.fields:
            temp = self.fields
        elif config and self.app:
            temp = list(self.app.GetAllMetaFlds(ignoreSystem = True)) + list(config.data)
        if not temp:
            raise ConfigurationError, "No form fields defined"
        # lookup field configurations
        self._c_fields = []
        for f in temp:
            if isinstance(f, basestring):
                fld = None
                if self.fields:
                    for a in config.data:
                        if a.id == f:
                            fld = a
                            break
                elif config:
                    for a in config.data:
                        if a.id == f:
                            fld = a
                            break
                if not fld:
                    fld = self.app.GetMetaFld(f)
                if not fld:
                    raise ConfigurationError, "Form field lookup failed: " + f
                f = fld
            self._c_fields.append(f)
            # add controlset fields
            if f.settings.get("controlset"):
                items = f.listItems
                if not isinstance(items, (list, tuple)):
                    items = items(f, self.context)
                for item in items:
                    if not item.get("fields"):
                        continue
                    for controlf in item.fields:
                        self._c_fields.append(controlf)
                    
        
        # action lookup
        #(1) subsets[subset]["actions"]
        #(2) type["form"][subset]["actions"]
        #(3) actions 
        temp = None
        if subsets and subset in subsets:
            if isinstance(subsets[subset], dict) and "actions" in subsets[subset]:
                #(1)
                temp = subsets[subset]["actions"]
        elif config and "forms" in config and config.forms and subset in config.forms:
            if isinstance(config.forms[subset], dict) and "actions" in config.forms[subset]:
                #(3)
                temp = config.forms[subset]["actions"]
        elif self.actions:
            temp = self.actions
        if temp:
            # lookup action configurations
            self._c_actions = []
            for a in temp:
                if isinstance(a, basestring):
                    action = None
                    if self.actions:
                        for v in self.actions:
                            if v.id == a:
                                action = v
                                break
                    if not action:
                        raise ConfigurationError, "Form action lookup failed: " + a
                    a = action
                self._c_actions.append(a)
                
        self.Signal("loadFields")
        
        
        
    def _SetUpSchema(self, force=False):
        """
        set up form schema for configured configuration.
        """
        if self._c_form:
            return 
        fields = self.GetFields()
        actions = self.GetActions(True)
        self._schemaFactory(self, fields, actions, force)
        self._c_form = True
        return 


    # Data extraction and validation --------------------------------------------------------------------------------------------

    def Validate(self, data, removeNull=True):
        """
        Extracts fields from request or source data dictionary, converts and
        validates
        
        Event
        - validate(data) before validate is called
        - process(data)  after validate has succeeded, is not called if validate failed
        
        returns bool, dictionary, list (result,data,errors)
        """
        self._SetUpSchema()
        error = None
        self.Signal("validate", data=data)
        try:
            data = self.validate(data)
        except ValidationFailure, e:
            return False, e.cstruct, e
        if removeNull:
            data = dict(filter(lambda d: d[1] != null, data.items()))
        self.Signal("process", data=data)
        return True, data, None


    def ValidateSchema(self, data, removeNull=True):
        """
        Extracts fields from request or source data dictionary, converts and
        validates
        
        Event
        - validate(data) before validate is called
        
        returns bool, dictionary, list (result,data,errors)
        """
        self._SetUpSchema()
        self.Signal("validate", data=data)
        errors = None
        result = True
        try:
            data = self.schema.deserialize(data)
        except Invalid, e:
            errors = e.children
            result = False
        
        if removeNull:
            data = dict(filter(lambda d: d[1] != null, data.items()))
        return result, data, errors

        
    def Extract(self, data, removeNull=True, removeEmpty=False):
        """
        Extract fields from request or source data dictionary and convert
        data types without validation. 
        
        returns bool, dictionary (result, data)
        """
        self._SetUpSchema()
        result = True
        try:
            data = self.validate(data)
        except ValidationFailure, e:
            result = False
            data = e.cstruct
        except ValueError:
            return self.ExtractDeserialized(data, removeNull)

        if removeNull:
            data = dict(filter(lambda d: d[1] != null, data.items()))
        if removeEmpty:
            data = dict(filter(lambda d: d[1] not in (u"",[],()), data.items()))
        
        return result, data
    
        
    def ExtractSchema(self, data, removeNull=False, removeEmpty=False):
        """
        Extract fields from request or source data dictionary and convert
        data types without validation. 
        
        returns bool, dictionary (result, data)
        """
        self._SetUpSchema()
        errors = None
        result = True
        try:
            data = self.schema.deserialize(data)
        except Invalid, e:
            result = False

        if removeNull:
            data = dict(filter(lambda d: d[1] != null, data.items()))
        if removeEmpty:
            data = dict(filter(lambda d: d[1] not in (u"",[],()), data.items()))

        return result, data


    # Loading initital data --------------------------------------------------------------------------------------------

    def LoadObjData(self, obj=None):
        """
        Load data from existing object
        
        Event
        - loadDataObj(data, obj) after data has been looked up
        
        returns dict
        """
        if not obj:
            obj = self.context
        data = {}
        for f in self.GetFields():
            # data
            if f.datatype == "file":
                data[f.id] = obj.files[f.id]
            if f.datatype == "password":
                data[f.id] = u""
            else:
                if obj.data.has_key(f.id):
                    data[f.id] = obj.data[f.id]
                elif obj.meta.has_key(f.id):
                    data[f.id] = obj.meta[f.id]
        self.Signal("loadDataObj", data=data, obj=obj)
        return data


    def LoadDefaultData(self):
        """
        Load default data from configuration
        
        Event
        - loadDefault(data) after data has been looked up
        
        returns dict
        """
        data = dict(filter(lambda y: y[1]!=None, 
                           map(lambda x: (x["id"],x["default"]), self.GetFields())))
        self.Signal("loadDefaultForm", data=data)
        return data


    # Field definitions and configuration --------------------------------------------------------------------------------------------

    def GetFields(self, removeReadonly=True):
        """
        Returns the list of field definitions. Readonly fields are removed by default.
        
        returns list
        """
        if not self._c_fields:
            return ()
        elif not removeReadonly:
            return self._c_fields
        return filter(lambda field: not (removeReadonly and field.readonly), self._c_fields)


    def GetActions(self, removeHidden=False):
        """
        Returns the list of form actions. Hidden actions are removed by default.
        
        returns list
        """
        if not self._c_actions:
            return ()
        elif not removeHidden:
            return self._c_actions
        return filter(lambda a: not (removeHidden and a.get("hidden",False)), self._c_actions)

    
    def GetField(self, fieldid):
        """
        Get the field configuration by field id.
        
        returns configuration or None
        """
        for f in self._c_fields:
            if f.id == fieldid:
                return f
        return None


    # form values --------------------------------------------------------------------------------------------

    def GetFormValue(self, key, request=None, method=None):
        """
        Extract single value from request
        
        returns value
        """
        if not request:
            request = self.request
        if isinstance(request, dict):
            return request.get(key)
        if not method:
            method = self.method
        try:
            if method == "POST":
                value = request.POST.getall(key)
            elif method == "GET":
                value = request.GET.getall(key)
            else:
                value = request.POST.getall(key)
                if not value:
                    value = request.GET.getall(key)
            if type(value)==StringType:
                value = unicode(value, self.app.configuration.frontendCodepage)
        except (AttributeError,KeyError):
            if method == "POST":
                value = request.POST.get(key)
            elif method == "GET":
                value = request.GET.get(key)
            else:
                value = request.POST.get(key)
                if not value:
                    value = request.GET.get(key)
            if type(value)==StringType:
                value = unicode(value, self.app.configuration.frontendCodepage)
            return value
        if not len(value):
            return None
        elif len(value)==1:
            return value[0]
        return value


    def GetFormValues(self, request=None, method=None):
        """
        Extract all values from request
        
        returns sict
        """
        if not request:
            request = self.request
        if not method:
            method = self.method
        try:
            if method == "POST":
                values = request.POST.mixed()
            elif method == "GET":
                values = request.GET.mixed()
            else:
                values = request.GET.mixed()
                values.update(request.POST.mixed())
        except AttributeError:
            try:
                if method == "POST":
                    values = request.POST
                elif method == "GET":
                    values = request.GET
                else:
                    values = request.GET
                    values.update(request.POST)
            except AttributeError:
                values = request
        if not values:
            return {}
        cp=self.app.configuration.frontendCodepage
        for k in values.items():
            if type(k[1]) == StringType:
                values[k[0]] = unicode(values[k[0]], cp)
        return values


    def ConvertFileUpload(self, key, method="post"):
        """
        Convert a file upload to the internal File object
        """
        value = self.GetFormValue(key, self.request, method=method)
        # prepare file
        file = self.app.db.GetFileClass()()
        file.filename = value.get('filename','')
        file.file = value.get('file')
        file.filekey = ticket.filekey
        file.mime = value.get('mimetype')
        file.size = value.get('size')
        file.tempfile = True
        return file



class HTMLForm(Form):
    """
    Simple HTML form 

    """
    # html styling
    formid = u"upload"
    css_class = u"form form-horizontal"
    
    # Form actions --------------------------------------------------------------------------------------------

    def Process(self, **kw):
        """
        Processes the request and calls the required actions. kw parameter ::
        
            defaultAction: default action if none found in request. Can also be configured in subset
            redirectSuccess: default=None. url to redirect on action success 
            renderSuccess: default=False. render the form on action success 
        
        If renderSuccess is set to False the form itself will not be rendered if 
        the action succeeds. Only the feedback message will be rendered.
         
        Action definitions must define a callback method to process the action. 
        The callback takes two parameters: ::
    
            method(action, **kw)

        returns bool, html, dict (result, data, action)
        """
        # bw 0.9.7
        if u"redirect_success" in kw:
            redirectSuccess = kw[u"redirect_success"]

        # find default action
        defaultAction = None
        if self.subset:
            defaultAction = self.subsets[self.subset].get("defaultAction")
        if not defaultAction:
            defaultAction = kw.get("defaultAction", "default")
        
        # find action
        action = None
        formValues = self.GetFormValues(self.request)
        actions = self.GetActions()
        for a in actions:
            if a["id"]+u"$" in formValues.keys():
                action = a
                break

        if not action and defaultAction:
            # lookup default action 
            if isinstance(defaultAction, basestring):
                for a in self.actions:
                    if a["id"]==defaultAction:
                        action = a
                        break
            else:
                action = defaultAction

        # no action -> raise exception
        if not action:
            raise ConfigurationError, "No action found to process the form"

        # call action
        if isinstance(action["method"], basestring):
            method = getattr(self, action["method"])
        else:
            method = action["method"]
        
        # lookup and merge keyword parameter for action call
        methodKws = action.get("options")
        if methodKws:
            callKws = methodKws.copy()
            callKws.update(kw)
        else:
            callKws = kw
        result, html = method(action, **callKws)
        return result, html, action


    def IsRequestAction(self, action):
        """
        Check request for the given action.
        
        returns bool
        """
        formValues = self.GetFormValues(self.request)
        return action+u"$" in formValues.keys()


    def StartForm(self, action, **kw):
        """
        Default action. Use this function to initially render a form if:
        - startEmpty is True
        - defaultData is passed in kw
        - load form default data

        returns bool, html
        """
        if self.startEmpty:
            data = {}
        elif "defaultData" in kw:
            data = kw["defaultData"]
        else:
            data = self.LoadDefaultData()
        return True, self.Render(data)


    def StartRequestGET(self, action, **kw):
        """
        Default action. Initially loads data from request GET values.
        Loads default data for initial from display on object creation.
        
        returns bool, html
        """
        data = self.GetFormValues(self.request, method="GET")
        return True, self.Render(data)


    def ReturnDataOnSuccess(self, action, **kw):
        """
        Process request data and returns validated data as `result` and rendered
        form as `data`. If validation fails `result` is False. `redirectSuccess`
        is ignored.
        
        A custom success message can be passed as success_message as keyword.

        returns bool, html
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            if kw.get("success_message"):
                msgs.append(kw.get("success_message"))
            # disabled default message. msgs.append(_(u"OK."))
            errors=None
            result = data
            #data = {}
        return result, self.Render(data, msgs=msgs, errors=errors)

    
    def Cancel(self, action, **kw):
        """
        Cancel form action
        
        returns bool, string
        """
        redirectSuccess = kw.get("redirectSuccess")
        if self.view and redirectSuccess:
            self.view.Redirect(redirectSuccess)
        return True, ""


    # Data extraction and validation --------------------------------------------------------------------------------------------

    def Validate(self, data, removeNull=True):
        """
        Extracts fields from request or source data dictionary, converts and
        validates. 
        
        Event
        - validate(data) before validate is called
        - process(data)  after validate has succeeded, is not called if validate failed
        
        returns bool, dict, list (result,data,errors)
        """
        if not isinstance(data, dict):
            data = self.GetFormValues(data)
        result,data,errors = Form.Validate(self, data, removeNull)
        return result,data,errors

    
    def Extract(self, data, removeNull=False, removeEmpty=False):
        """
        Extracts fields from request or source data dictionary and converts
        data types without validation and error checking. 
        
        returns bool, dict (result, data)
        """
        if not isinstance(data, dict):
            data = self.GetFormValues(data)
        self._SetUpSchema()
        result, data = Form.Extract(self, data, removeNull, removeEmpty)
        return result, data


    # Form view functions --------------------------------------------------------------------------------------------

    def Render(self, data, msgs=None, errors=None, messagesOnly=False):
        """
        renders the form with data, messages
        
        messagesOnly=True will skip form and error rendering on just render the messages as 
        html block.
        """
        if messagesOnly:
            return self._Msgs(msgs=msgs)

        self._SetUpSchema()
        if errors:
            html = self._Msgs(msgs=msgs)
            return html + errors.render()
            #return html + exception.ValidationFailure(self._form, data, errors).render()
        self.messages = msgs
        html = self.render(data)
        return html


    def RenderBody(self, data, msgs=None, errors=None):
        """
        renders the form without header and footer
        """
        self._SetUpSchema()
        html = self._Msgs(msgs=msgs)
        if errors:
            return html + errors.render()
        self.widget.template = "form_body"
        html += self.render(data)
        self.widget.template = "form"
        return html

    
    def HTMLHead(self, ignore=(u"jquery.js",u"jquery-ui.js")):
        """
        Get necessary includes (js and css) for html header.
        Jquery and Jquery-ui are included by default in cmsview editor pages. So by default these two
        will be ignored. 
        """
        self._SetUpSchema()
        resources = self.get_widget_resources()
        js_resources = resources.get('js')
        css_resources = resources.get('css')
        resources = resources.get('seq')
                
        # js and css
        req = self.request
        js_links = []
        css_links = []
        if js_resources:
            js_links = [static_url(r, req) for r in filter(lambda v: v not in ignore, js_resources)]
        if css_resources:
            css_links = [static_url(r, req) for r in filter(lambda v: v not in ignore, css_resources)]
        # seq
        if resources:
            js_links.extend([static_url(r[1], req) for r in filter(lambda v: v[0] not in ignore and v[1].endswith(u".js"), resources)])
            css_links.extend([static_url(r[1], req) for r in filter(lambda v: v[0] not in ignore and v[1].endswith(u".css"), resources)])
        js_tags = [u'<script src="%s" type="text/javascript"></script>' % link for link in js_links]
        css_tags = [u'<link href="%s" rel="stylesheet" type="text/css" media="all"/>' % link for link in css_links]
        return (u"\r\n").join(js_tags + css_tags)
    
        
    def _FinishFormProcessing(self, result, data, msgs, errors, **kw):
        """
        Handles the default form processing after the action has been executed
        based on passed keywords and result:
        
        Used kw arguments:
        - redirectSuccess
        - renderSuccess
        
        """
        redirectSuccess = kw.get("redirectSuccess")
        renderSuccess = kw.get("renderSuccess", True)
        redirectSuccess = self.view.ResolveUrl(redirectSuccess, result)

        if not result:
            return result, self.Render(data, msgs=msgs, errors=errors)
    
        if self.use_ajax:
            if redirectSuccess:
                # raises HTTPFound 
                return result, self.view.Relocate(redirectSuccess, messages=msgs, raiseException=True)
        
        elif redirectSuccess:
            # raises HTTPFound 
            return result, self.view.Redirect(redirectSuccess, messages=msgs)

        if not renderSuccess:        
            return result, self._Msgs(msgs=msgs)
        return result, self.Render(data, msgs=msgs, errors=errors)


    def _Msgs(self, **values):
        err = values.get("errors")!=None
        msgs = values.get("msgs")
        if not msgs:
            return u""
        h = []
        if isinstance(msgs, basestring):
            msgs = [msgs]
        for m in msgs:
            h.append(u"""<li>%s</li>""" % (m))
        css = u"alert"
        if err:
            css = u"alert alert-danger"
        return u"""<div class="%s"><ul>%s</ul></div>
        """ % (css, u"".join(h))




# Preconfigured forms -----------------------------------------------------------------

class ObjectForm(HTMLForm):
    """
    Contains actions for object creation and updates.
    """
    actions = [
        Conf(id=u"default",    method="StartFormRequest",  name=u"Initialize", hidden=True,  css_class=u"",            html=u"", tag=u""),
        Conf(id=u"create",     method="CreateObj",  name=u"Create",     hidden=False, css_class=u"formButton btn-primary",  html=u"", tag=u""),
        Conf(id=u"defaultEdit",method="StartObject",name=u"Initialize", hidden=True,  css_class=u"",            html=u"", tag=u""),
        Conf(id=u"edit",       method="UpdateObj",  name=u"Save",       hidden=False, css_class=u"formButton btn-primary",  html=u"", tag=u""),
        Conf(id=u"cancel",     method="Cancel",     name=u"Cancel",     hidden=False, css_class=u"buttonCancel",html=u"", tag=u"")
    ]
    subsets = {
        "create": {"actions": [u"create"],  "defaultAction": "default"},
        "edit":   {"actions": [u"edit"],    "defaultAction": "defaultEdit"}
    }


    def Setup(self, subset=None, addTypeField=False, addPosField=True):
        """
        Calls Form.Setup() with the addition to automatically add the pool_type field. 
        
        1) Load fields from object definition
        2) Loads subsets and actions from object form definition
        
        Event
        - loadFields() after fields have been loaded
        """
        Form.Setup(self, subset)
        if not addTypeField:
            return
        #add type field 
        #opt
        pos = 0
        for field in self._c_fields:
            if field.id == "pool_type":
                if field.readonly:
                    # replace readonly field
                    type_fld = FieldConf(id="pool_type",datatype="string",hidden=1)
                    del self._c_fields[pos]
                    self._c_fields.append(type_fld)
                return
            pos += 1
        type_fld = FieldConf(id="pool_type",datatype="string",hidden=1)
        self._c_fields.append(type_fld)
        if addPosField:
            # insert at position
            pepos = self.GetFormValue(u"pepos", method=u"ALL")
            if pepos:
                pos_fld = FieldConf(id="pepos",datatype="string",hidden=1)
                self._c_fields.append(pos_fld)


    def StartForm(self, action, **kw):
        """
        Default action. Called if no action in request or self.actions.default set.
        Loads default data for initial from display on object creation.
        
        returns bool, html
        """
        if self.startEmpty:
            data = {}
        else:
            data = self.LoadDefaultData()
        if isinstance(self.loadFromType, basestring):
            data["pool_type"] = self.loadFromType
        else:
            data["pool_type"] = self.loadFromType.id
        # insert at position
        pepos = self.GetFormValue(u"pepos", method=u"ALL")
        if pepos:
            data["pepos"] = pepos
        return True, self.Render(data)


    def StartFormRequest(self, action, **kw):
        """
        Default action. Called if no action in request or self.actions.default set.
        Loads default data from request for initial from display on object creation.
        
        returns bool, html
        """
        if self.startEmpty:
            data = {}
        else:
            data = self.LoadDefaultData()
            r, d = self.ExtractSchema(self.GetFormValues(method=u"ALL"), removeNull=True, removeEmpty=True)
            data.update(d)
        if isinstance(self.loadFromType, basestring):
            data["pool_type"] = self.loadFromType
        else:
            data["pool_type"] = self.loadFromType.id
        # insert at position
        pepos = self.GetFormValue(u"pepos", method=u"ALL")
        if pepos:
            data["pepos"] = pepos
        return True, self.Render(data)


    def StartObject(self, action, **kw):
        """
        Initially load data from object. 
        context = obj
        
        returns bool, html
        """
        data = self.LoadObjData()
        return data!=None, self.Render(data)


    def UpdateObj(self, action, **kw):
        """
        Process request data and update object.
        
        `Process()` returns the form data as result if update succeeds.

        Event
        - success(obj) after data has been successfully committed

        returns form data or false, html or redirects
        """
        redirectSuccess = kw.get("redirectSuccess")
        msgs = []
        obj=self.context
        result,data,errors = self.Validate(self.request)
        if result:
            user = kw.get("user") or self.view.User()
            result = obj.Update(data, user)
            if result:
                #obj.Commit(user)
                msgs.append(_(u"OK. Data saved."))
                self.Signal("success", obj=obj)
                result = obj

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def CreateObj(self, action, **kw):
        """
        Process request data and create object as child for current context.
        
        Pass kw['pool_type'] to specify type to be created. If not passed pool_type
        will be extracted from data dictionary.

        `Process()` returns the new object as result if create succeeds.

        Event
        - success(obj) after data has been successfully committed

        returns new object or none, html or redirects
        """
        redirectSuccess = kw.get("redirectSuccess")
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            if "pool_type" in kw:
                objtype = kw["pool_type"]
            else:
                objtype = data.get("pool_type")
                
            user=kw.get("user") or self.view.User()
            result = self.context.Create(objtype, data, user)
            if result:
                # insert at position
                pepos = self.GetFormValue(u"pepos")
                if pepos:
                    if ISort.providedBy(self.context):
                        if pepos in (u"last", u"first"):
                            self.context.InsertAtPosition(result.id, pepos, user=user)
                        else:
                            self.context.InsertAfter(pepos, result.id, user=user)
                msgs.append(_(u"OK. Data saved."))
                self.Signal("success", obj=result)

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


class ToolForm(HTMLForm):
    """
    Contains default actions for tool form processing.

    Example ::

        tool = app.GetTool("tool id", contextObject=app)
        form = ToolForm(view=self, context=tool, loadFromType=tool.configuration)
        form.Setup()
        result, data, action = form.Process()

    A simple example to render a tool form and execute it.
    """
    actions = [
        Conf(id=u"default", method="StartForm", name=u"Initialize", hidden=True,  css_class=u"", html=u"", tag=u""),
        Conf(id=u"run",     method="RunTool",   name=u"Start",      hidden=False, css_class=u"", html=u"", tag=u""),
    ]

    def Setup(self, subset=None):
        """
        1) Load fields from tool definition
        2) Loads subsets and actions from tool form definition
        
        Event
        - loadFields() after fields have been loaded
        """
        self._c_form = None
        self._c_fields = None
        self._c_actions = None
        self.subset=subset

        subsets=self.subsets
        config = None

        # load form fields
        if self.loadFromType:
            typeOrConfiguration = self.loadFromType
            if isinstance(typeOrConfiguration, basestring):
                config = self.app.GetToolConf(typeOrConfiguration)
                if not config:
                    raise ConfigurationError, "Tool not found (%s). Use configuration instance instead of a string." % (str(typeOrConfiguration))
            else:
                config = typeOrConfiguration
            self.loadFromType = config
        
        # unconfigured form
        if not subset and not subsets and not config and not self.fields:
            raise ConfigurationError, "No form fields defined."
        # unknown subset
        if subset and (not subsets or not subset in subsets):
            raise ConfigurationError, "Unknown subset."

        # field lookup
        #(1) subsets[subset]["fields"]
        #(3) tool["form"][subset]["fields"]
        #(5) fields
        #(6) config.fields
        temp = None
        if subsets and subset in subsets and "fields" in subsets[subset]:
            #(1)
            temp = subsets[subset]["fields"]
        elif config and "forms" in config and config.forms and subset in config.forms and "fields" in config.forms[subset]:
            #(3)
            temp = config.forms[subset]["fields"]
        elif self.fields:
            temp = self.fields
        elif config and self.app:
            temp = config.data
        if not temp:
            raise ConfigurationError, "No form fields defined."
        # lookup field configurations
        self._c_fields = []
        for f in temp:
            if isinstance(f, basestring):
                fld = None
                if self.fields:
                    for a in config.data:
                        if a.id == f:
                            fld = a
                            break
                elif config:
                    for a in config.data:
                        if a.id == f:
                            fld = a
                            break
                if not fld:
                    raise ConfigurationError, "Form field lookup failed: " + f
                f = fld
            self._c_fields.append(f)
        
        # action lookup
        #(1) subsets[subset]["actions"]
        #(2) tool["form"][subset]["actions"]
        #(3) actions 
        temp = None
        if subsets and subset in subsets:
            if isinstance(subsets[subset], dict) and "actions" in subsets[subset]:
                #(1)
                temp = subsets[subset]["actions"]
        elif config and "forms" in config and config.forms and subset in config.forms:
            if isinstance(config.forms[subset], dict) and "actions" in config.forms[subset]:
                #(3)
                temp = config.forms[subset]["actions"]
        elif self.actions:
            temp = self.actions
        if temp:
            # lookup action configurations
            self._c_actions = []
            for a in temp:
                if isinstance(a, basestring):
                    action = None
                    if self.actions:
                        for v in self.actions:
                            if v.id == a:
                                action = v
                                break
                    if not action:
                        raise ConfigurationError, "Form action lookup failed: " + a
                    a = action
                self._c_actions.append(a)
                
        self.Signal("loadFields")
        
            
    def RunTool(self, action, **kw):
        """
        Process request data and run tool. 

        returns bool, html
        """
        msgs = []
        validated,data,errors = self.Validate(self.request)
        if validated:
            return self.context.Run(request=self.request,**data)
        return False, self.Render(data, msgs=msgs, errors=errors)




class WorkflowForm(HTMLForm):
    """
    Contains default actions for workflow transition form processing
    Requires Form, HTMLForm or TemplateForm
    """

    def CallWf(self, action, **kw):
        """
        process request data and call workflow transition for object. 
        context = obj
        """
        redirectSuccess = kw.get("redirectSuccess")
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            wfa = ""
            wft = ""
            user = kw.get("user") or self.view.User()
            if not obj.WfAction(action=wfa, transition=wft, user = user):
                result = False

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)
        


class JsonMappingForm(HTMLForm):
    """
    Maps form fields to a single dumped json text field
    json data is always stored as dictionary. ::
    
        jsonDataField = the field to merge data to
        mergeContext = if true the database values will be updated
                       by form values
                       
    `Process()` returns the form data as dictionary on success.
    
    """
    jsonDataField = "data"
    mergeContext = True

    actions = [
        Conf(id=u"default",    method="StartObject",name=u"Initialize", hidden=True,  css_class=u"",            html=u"", tag=u""),
        Conf(id=u"edit",       method="UpdateObj",  name=u"Save",       hidden=False, css_class=u"formButton btn-primary",  html=u"", tag=u""),
    ]

    def Validate(self, data, removeNull=True):
        """
        Extracts fields from request or source data dictionary, converts and
        validates. 
        
        Event
        - validate(data) before validate is called
        - process(data)  after validate has succeeded, is not called if validate failed
        
        returns bool, dict, list (result,data,errors)
        """
        if not isinstance(data, dict):
            data = self.GetFormValues(data)
        result,data,errors = Form.Validate(self, data, removeNull)
        if not result:
            return result,data,errors
        # merge existing data
        if self.mergeContext and self.context:
            jdata = self.context.data[self.jsonDataField] or {}
            jdata.update(data)
            data = jdata
        return result,data,errors

    
    def Extract(self, data, removeNull=False, removeEmpty=False):
        """
        Extracts fields from request or source data dictionary and converts
        data types without validation and error checking. 
        
        returns bool, dict (result, data)
        """
        if not isinstance(data, dict):
            data = self.GetFormValues(data)
        self._SetUpSchema()
        result, data = Form.Extract(self, data, removeNull, removeEmpty)
        # merge existing data
        if self.mergeContext and self.context:
            jdata = self.context.data[self.jsonDataField]
            jdata.update(data)
            data = jdata
        return result,data


    def StartObject(self, action, **kw):
        """
        Initially load data from configured object json data field. 
        context = obj
        
        returns bool, html
        """
        data = self.context.data.get(self.jsonDataField) or {}
        return data!=None, self.Render(data)


    def UpdateObj(self, action, **kw):
        """
        Process request data and update object.
        
        returns bool, html
        """
        redirectSuccess = kw.get("redirectSuccess")
        msgs = []
        obj=self.context
        result,data,errors = self.Validate(self.request)
        if result:
            user = kw.get("user") or self.view.User()
            result = obj.Update({self.jsonDataField: data}, user)
            if result:
                #obj.Commit(user)
                msgs.append(_(u"OK. Data saved."))
                result = data

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)
        
        
        
class JsonSequenceForm(HTMLForm):
    """
    Maps form fields as sequence to a single dumped json text field
    the sequence is always stored as list, json data as dictionary. 
    
    The form fields/values can be stored multiple times as sequence and
    the template offers options to add, delete and edit single items.
    Items in read only mode are not rendered by the form. 
    
    Sequence items are referenced by list position starting by 1.
    ::
    
        jsonDataField = the field to merge data to
                       
    `Process()` returns the form data as dictionary on success.
    
    """
    jsonDataField = u"data"
    delKey = u"aa876352"
    editKey = u"cc397785"
    
    actions = [
        Conf(id=u"default",    method="StartObject",name=u"Initialize", hidden=True,  css_class=u"",            html=u"", tag=u""),
        Conf(id=u"edit",       method="UpdateObj",  name=u"Save",       hidden=False, css_class=u"formButton btn-primary",  html=u"", tag=u""),
    ]
    editKeyFld = FieldConf(id=editKey, name=u"indexKey", datatype="number", hidden=True, default=u"")
    
    def Init(self):
        self.RegisterEvent("loadFields", "AddKeyFld")
        
    def AddKeyFld(self):
        self._c_fields.append(self.editKeyFld)


    def StartObject(self, action, **kw):
        """
        Initially load data from configured object json data field. 
        context = obj
        
        returns bool, html
        """
        sequence = self.context.data.get(self.jsonDataField)
        if sequence in (u"", None):
            sequence = []
        # process action
        msgs = []
        if self.GetFormValue(self.editKey, self.request, "GET"):
            seqindex = int(self.GetFormValue(self.editKey, self.request, "GET"))
            if not seqindex or seqindex > len(sequence):
                data = []
            else:
                data = sequence[seqindex-1]
                data[self.editKey] = seqindex
        elif self.GetFormValue(self.delKey, self.request, "GET"):
            seqindex = int(self.GetFormValue(self.delKey, self.request, "GET"))
            if not seqindex or seqindex > len(sequence):
                data = []
            else:
                del sequence[seqindex-1]
                self.context.data[self.jsonDataField] = sequence
                self.context.Commit(kw.get("user") or self.view.User())
                self.context.data[self.jsonDataField] = sequence
                msgs=[_(u"Item deleted!")]
                data = []
        else:
            data = []
        return data!=None, self.Render(data, msgs=msgs)


    def UpdateObj(self, action, **kw):
        """
        Process request data and update object.
        
        returns bool, html
        """
        redirectSuccess = kw.get("redirectSuccess")
        msgs = []
        obj=self.context
        result,data,errors = self.Validate(self.request)
        if result:
            user = kw.get("user") or self.view.User()
            # merge sequnce list with edited item
            sequence = self.context.data.get(self.jsonDataField)
            if sequence in (u"", None):
                sequence = []
            try:
                seqindex = int(data.get(self.editKey))
            except:
                seqindex = 0
            if self.editKey in data:
                del data[self.editKey]
            if not seqindex or seqindex > len(sequence):
                sequence.append(data)
            else:
                sequence[seqindex-1] = data
            result = obj.Update({self.jsonDataField: sequence}, user)
            if result:
                obj.data.sequence = sequence
                #obj.Commit(user)
                msgs.append(_(u"OK. Data saved."))
                data = {}

        return result, self.Render(data, msgs=msgs, errors=errors)
        
        
        