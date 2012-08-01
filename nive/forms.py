#----------------------------------------------------------------------
# Nive CMS
# Copyright (C) 2012  Arndt Droullier, DV Electric, info@dvelectric.com
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

__doc__ = """
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
    result, data, action = form.Process(defaultAction="defaultEdit")

*data* will contain the rendered HTML whether the is loaded for the first time, validated ok or 
not. *result* will be *false* if the form input did not validate. The *ObjectForm* already includes 
all necessary functions to load data initially, create an object and store data for existing objects.
All you have to do is switch the subset from *edit* to *create*. ::

    form = ObjectForm(view=self,
                      loadFromType=self.context.configuration)
    form.Setup(subset="create")
    # process and render the form.
    result, data, action = form.Process(defaultAction="default")

The configuration is loaded from the object configuration itself so all field settings are 
dynamically included. In fact the example above works for *any* object type.

Form action callback methods use the following footage: ::

    def Method(self, defaultAction="default", redirect_success=None, **kw):
        ...
        return result, data

These callback methods are automatically looked up and executed in Process(). Use action.method to
link a method to a specific form action.

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

--------------------------------------------------------------------------

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
                {"actions": ["create"]},
      "create2":{"fields":  ["ftext", "fnumber", "fdate", "flist", "fmselect"], 
                {"actions": ["create"]},
      "edit":   {"fields":  ["ftext"], 
                {"actions": ["defaultEdit", "edit"]},
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
from types import *

from nive.utils.utils import GetDLItem, ConvertToList
from nive.definitions import Conf, FieldConf, ConfigurationError
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
0.9.4 changed nive.Form:

- __init__ parameters if view is not None: app, request, context are extracted from view context
- added Setup(subset) function
- removed LoadConfiguration()
- ObjectForm.AddTypeField() removed. Use Setup(addTypeField=True).
- form conf changed: object.configuration.forms = {"subset": {"fields": [...], "actions": [...]}}
- changed password widgets
"""

class Form(Events,ReForm):
    """
    Base form class.
    """
    _schemaFactory = SchemaFactory
    default_renderer = zpt_renderer

    # form configuration values
    fields = None
    actions = None
    subsets = None
    loadFromType = None
    
    
    def __init__(self, view=None, loadFromType=None, context=None, request=None, app=None, **kw):
        """
        Initialize form context. If view is not None and context, request, app are automatically
        extracted from the view object. Form fields and actions are processed in Setup(). 
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
            raise ConfigurationError, "No form fields defined."
        # unknown subset
        if subset and (not subsets or not subset in subsets):
            raise ConfigurationError, "Unknown subset."

        # field lookup
        #(1) subsets[subset]["fields"]
        #(x) subsets[subset]
        #(3) type["form"][subset]["fields"]
        #(x) type["form"][subset]
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
            temp = list(self.app.GetAllMetaFlds(ignoreSystem = True)) + config.data
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
                    fld = self.app.GetMetaFld(f)
                if not fld:
                    raise ConfigurationError, "Form field lookup failed: " + f
                f = fld
            self._c_fields.append(f)
        
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

    def GetFormValue(self, key, request, method=None):
        """
        Extract single value from request
        
        returns value
        """
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


    def GetFormValues(self, request, method=None):
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



class HTMLForm(Form):
    """
    Simple HTML form 

    Inline Form: ::
    
        form.widget.template = "form_simple"
        form.widget.item_template = "field_onecolumn"

    """
    # html styling
    formid = u"upload"
    css_class = u"poolform"
    use_ajax = False

    # Form actions --------------------------------------------------------------------------------------------

    def Process(self, defaultAction="default", redirect_success=None, **kw):
        """
        Processes the request and calls the required actions. ::
        
            defaultAction: default action if none found in request
            redirect_success: default=None. url to redirect on action success 
        
        Action definitions must define a callback method to process the action. 
        The callback takes two parameters: ::
    
            method(action, redirect_success)

        returns bool, html, dict (result, data, action)
        """
        # find action
        action = None
        default = None
        formValues = self.GetFormValues(self.request)
        actions = self.GetActions()
        for a in actions:
            if a["id"]+u"$" in formValues.keys():
                action = a
                break
            if a["id"] == defaultAction:
                default = a

        if not action and default:
            action = default

        # call action
        if action:
            if type(action["method"])==StringType:
                method = getattr(self, action["method"])
            else:
                method = action["method"]
            result, data = method(action, redirect_success, **kw)
        else:
            result, data = self.StartForm(None, redirect_success, **kw)
        return result, data, action


    def IsRequestAction(self, action):
        """
        Check request for the given action.
        
        returns bool
        """
        formValues = self.GetFormValues(self.request)
        return action+u"$" in formValues.keys()


    def StartForm(self, action, redirect_success, **kw):
        """
        Default action. Called if no action in request or self.actions.default set.
        Loads default data for initial from display from field definitions.
        
        returns bool, html
        """
        if self.startEmpty:
            data = {}
        else:
            data = self.LoadDefaultData()
        return True, self.Render(data)


    def StartRequestGET(self, action, redirect_success, **kw):
        """
        Default action. Initially loads data from request GET values.
        Loads default data for initial from display on object creation.
        
        returns bool, html
        """
        data = self.GetFormValues(self.request, method="GET")
        return True, self.Render(data)


    def Cancel(self, action, redirect_success, **kw):
        """
        Cancel form action
        
        returns bool, string
        """
        if self.view and redirect_success:
            self.view.Redirect(redirect_success)
        return True, ""


    # Data extraction and validation --------------------------------------------------------------------------------------------

    def Validate(self, data, removeNull=True):
        """
        Extracts fields from request or source data dictionary, converts and
        validates. 
        
        Event
        - validate(data) before validate is called
        
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

    def Render(self, data, msgs=None, errors=None, renderInline=False, messagesOnly=False):
        """
        renders the form with data, messages
        
        messagesOnly=True will skip form and error rendering on just render the messages as 
        html block.
        """
        if renderInline:
            self.widget.template = "form_simple"
            self.widget.item_template = "field_onecolumn"
            
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

    
    def HTMLHead(self, disableResources=[u"scripts/jquery.min.js",u"css/form.css"]):
        """
        get necessary includes (js and css) for html header
        """
        self._SetUpSchema()
        resources = self.get_widget_resources()
        js_resources = resources['js']
        css_resources = resources['css']
        js_links = [u'/reform/%s' % r for r in filter(lambda v: v not in disableResources, js_resources)]
        css_links = [ u'/reform/%s' % r for r in css_resources ]
        js_tags = [u'<script src="%s" type="text/javascript"></script>' % link for link in js_links]
        css_tags = [u'<link href="%s" rel="stylesheet" type="text/css" media="all"/>' % link for link in css_links]
        return (u"\r\n").join(js_tags + css_tags)
    
        
    def _Msgs(self, **values):
        err = values.get("errors")!=None
        msgs = values.get("msgs")
        if not msgs:
            return u""
        h = []
        if type(msgs) in (StringType, UnicodeType):
            msgs = [msgs]
        for m in msgs:
            h+= u"""<li>%s</li>""" % (m)
        css = u"boxOK"
        if err:
            css = u"boxAlert"
        return u"""<ul class="%s">%s</ul>
        """ % (css, u"".join(h))




# Preconfigured forms -----------------------------------------------------------------

class ObjectForm(HTMLForm):
    """
    Contains actions for object creation and updates.
    """
    actions = [
        Conf(id=u"default",    method="StartForm",  name=u"Initialize", hidden=True,  cssClass=u"",            html=u"", tag=u""),
        Conf(id=u"create",     method="CreateObj",  name=u"Create",     hidden=False, cssClass=u"formButton btn-primary",  html=u"", tag=u""),
        Conf(id=u"defaultEdit",method="StartObject",name=u"Initialize", hidden=True,  cssClass=u"",            html=u"", tag=u""),
        Conf(id=u"edit",       method="UpdateObj",  name=u"Save",       hidden=False, cssClass=u"formButton btn-primary",  html=u"", tag=u""),
        Conf(id=u"cancel",     method="Cancel",     name=u"Cancel",     hidden=False, cssClass=u"buttonCancel",html=u"", tag=u"")
    ]
    subsets = {
        "create": {"actions": [u"default",u"create"]},
        "edit":   {"actions": [u"defaultEdit",u"edit"]}
    }


    def Setup(self, subset=None, addTypeField=False):
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


    def StartForm(self, action, redirect_success, **kw):
        """
        Default action. Called if no action in request or self.actions.default set.
        Loads default data for initial from display on object creation.
        
        returns bool, html
        """
        if self.startEmpty:
            data = {}
        else:
            data = self.LoadDefaultData()
        data["pool_type"] = self.loadFromType.id
        return True, self.Render(data)


    def StartObject(self, action, redirect_success, **kw):
        """
        Initially load data from object. 
        context = obj
        
        returns bool, html
        """
        data = self.LoadObjData()
        return data!=None, self.Render(data)


    def UpdateObj(self, action, redirect_success, **kw):
        """
        Process request data and update object.
        
        returns bool, html
        """
        msgs = []
        obj=self.context
        result,data,errors = self.Validate(self.request)
        if result:
            user = self.view.User()
            result = obj.Update(data, user)
            if result:
                #obj.Commit(user)
                msgs.append(_(u"OK. Data saved."))
                errors=None
                if self.view and redirect_success:
                    redirect_success = self.view.ResolveUrl(redirect_success, obj)
                    if self.use_ajax:
                        self.view.AjaxRelocate(redirect_success, messages=msgs)
                    else:
                        self.view.Redirect(redirect_success, messages=msgs)
                result = obj
        return result, self.Render(data, msgs=msgs, errors=errors)


    def CreateObj(self, action, redirect_success, **kw):
        """
        Process request data and create object as child for current context.
        
        Pass kw['pool_type'] to specify type to be created. If not passed pool_type
        will be extracted from data dictionary.

        returns bool, html
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            if "pool_type" in kw:
                objtype = kw["pool_type"]
            else:
                objtype = data.get("pool_type")
                
            user=self.view.User()
            result = self.context.Create(objtype, data, user)
            if result:
                msgs.append(_(u"OK. Data saved."))
                errors=None
                if self.view and redirect_success:
                    redirect_success = self.view.ResolveUrl(redirect_success, result)
                    if self.use_ajax:
                        self.view.AjaxRelocate(redirect_success, messages=msgs)
                    else:
                        self.view.Redirect(redirect_success, messages=msgs)
        return result, self.Render(data, msgs=msgs, errors=errors)




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
        Conf(id=u"default", method="StartForm", name=u"Initialize", hidden=True,  cssClass=u"", html=u"", tag=u""),
        Conf(id=u"run",     method="RunTool",   name=u"Start",      hidden=False, cssClass=u"", html=u"", tag=u""),
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
        
            
    def RunTool(self, action, redirect_success, **kw):
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

    def CallWf(self, action, redirect_success, **kw):
        """
        process request data and call workflow transition for object. 
        context = obj
        """
        msgs = []
        validated,data,errors = self.Validate(self.request)
        if validated:
            wfa = ""
            wft = ""
            user = self.view.User()
            if obj.WfAction(action=wfa, transition=wft, user = user):
                if self.view and redirect_success:
                    if self.use_ajax:
                        self.view.AjaxRelocate(redirect_success, messages=msgs)
                    else:
                        self.view.Redirect(redirect_success, messages=msgs)
        return False, self.Render(data, msgs=msgs, errors=errors)
        


class JsonMappingForm(HTMLForm):
    """
    Maps form fields to a single dumped json text field
    json data is always stored as dictionary. ::
    
        jsonDataField = the field to merge data to
        mergeContext = if true the database values will be updated
                       by form values
    
    """
    jsonDataField = "data"
    mergeContext = True

    actions = [
        Conf(id=u"default",    method="StartObject",name=u"Initialize", hidden=True,  cssClass=u"",            html=u"", tag=u""),
        Conf(id=u"edit",       method="UpdateObj",  name=u"Save",       hidden=False, cssClass=u"formButton btn-primary",  html=u"", tag=u""),
    ]

    def Validate(self, data, removeNull=True):
        """
        Extracts fields from request or source data dictionary, converts and
        validates. 
        
        Event
        - validate(data) before validate is called
        
        returns bool, dict, list (result,data,errors)
        """
        if not isinstance(data, dict):
            data = self.GetFormValues(data)
        result,data,errors = Form.Validate(self, data, removeNull)
        if not result:
            return result,data,errors
        # merge existing data
        if self.mergeContext and self.context:
            jdata = self.context.data[self.jsonDataField]
            if jdata:
                jdata = json.loads(jdata)
            if not isinstance(jdata, dict):
                jdata = {}
            jdata.update(data)
            data = jdata
        # convert to json string 
        data = json.dumps(data)
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
            if jdata:
                jdata = json.loads(jdata)
            if not isinstance(jdata, dict):
                jdata = {}
            jdata.update(data)
            data = jdata
        # convert to json string 
        data = json.dumps(data)
        return result,data


    def StartObject(self, action, redirect_success, **kw):
        """
        Initially load data from configured object json data field. 
        context = obj
        
        returns bool, html
        """
        data = self.context.data.get(self.jsonDataField)
        if data:
            data = json.loads(data)
        else:
            data = self.LoadDefaultData()
        return data!=None, self.Render(data)


    def UpdateObj(self, action, redirect_success, **kw):
        """
        Process request data and update object.
        
        returns bool, html
        """
        msgs = []
        obj=self.context
        result,data,errors = self.Validate(self.request)
        if result:
            user = self.view.User()
            data = {self.jsonDataField: data}
            result = obj.Update(data, user)
            if result:
                #obj.Commit(user)
                msgs.append(_(u"OK. Data saved."))
                errors=None
                if self.view and redirect_success:
                    redirect_success = self.view.ResolveUrl(redirect_success, obj)
                    if self.use_ajax:
                        self.view.AjaxRelocate(redirect_success, messages=msgs)
                    else:
                        self.view.Redirect(redirect_success, messages=msgs)
                result = obj
        return result, self.Render(data, msgs=msgs, errors=errors)
        