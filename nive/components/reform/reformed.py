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
FormWorker for reform
---------------------
This is the connection between nive.Form and reform and maps FieldConf()
to schema nodes. 
"""

from zope.interface import alsoProvides
from nive.definitions import ModuleConf, ViewModuleConf
from nive.components.reform.i18n import _

# view module definition ------------------------------------------------------------------
#@nive_module
configuration = ModuleConf()
configuration.id = "reformed"
configuration.name = u"Form widgets and resources"
configuration.context = "nive.components.reform.reformed"
configuration.views = (ViewModuleConf(static="nive.components.reform:static",id="reform"),)


from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request
from pkg_resources import resource_filename
from nive.components.reform.template import ZPTRendererFactory

def translator(term):
    localizer = get_localizer(get_current_request())
    return localizer.translate(term) 

template_dir = resource_filename('nive.components.reform', 'templates/')
zpt_renderer = ZPTRendererFactory([template_dir], translator=translator)

# change imports 
from schema import *
from widget import *
from form import Button
from field import Field

from nive.helper import File
from nive.utils.utils import ConvertDictListToTuple


class FileData2(object):
    """
    A type representing file data; used to shuttle data back and forth
    between an application and the
    :class:`reform.widget.FileUploadWidget` widget.

    """

    def serialize(self, node, value):
        """
        Serialize a dictionary representing partial file information
        to a dictionary containing information expected by a file
        upload widget.
        
        The file data dictionary passed as ``value`` to this
        ``serialize`` method *must* include:

        filename
            Filename of this file (not a full filesystem path, just the
            filename itself).

        uid
            Unique string id for this file.  Needs to be unique enough to
            disambiguate it from other files that may use the same
            temporary storage mechanism before a successful validation,
            and must be adequate for the calling code to reidentify it
            after deserialization.

        A fully populated dictionary *may* also include the following
        values:

        fp
            File-like object representing this file's content or
            ``None``.  ``None`` indicates this file has already been
            committed to permanent storage.  When serializing a
            'committed' file, the ``fp`` value should ideally not be
            passed or it should be passed as ``None``; ``None`` as an
            ``fp`` value is a signifier to the file upload widget that
            the file data has already been committed.  Using ``None``
            as an ``fp`` value helps prevent unnecessary data copies
            to temporary storage when a form is rendered, however its
            use requires cooperation from the calling code; in
            particular, the calling code must be willing to translate
            a ``None`` ``fp`` value returned from a deserialization
            into the file data via the ``uid`` in the deserialization.

        mimetype
            File content type (e.g. ``application/octet-stream``).

        size
            File content length (integer).

        preview_url
            URL which provides an image preview of this file's data.

        If a ``size`` is not provided, the widget will have no access
        to size display data.  If ``preview_url`` is not provided, the
        widget will not be able to show a file preview.  If
        ``mimetype`` is not provided, the widget will not be able to
        display mimetype information.
        """
        if value in (null, None, ""):
            return null
        
        if not hasattr(value, 'get'):
            mapping = {'value':repr(value)}
            raise Invalid(
                node,
                _('${value} is not a dictionary', mapping=mapping)
                )
        for n in ('filename',):
            if not n in value:
                mapping = {'value':repr(value), 'key':n}
                raise Invalid(
                    node,
                    _('${value} has no ${key} key', mapping=mapping)
                    )
        if isinstance(value, basestring):
            # from path
            file = File()
            file.fromPath(value)
            return file

        elif not isinstance(value, File):
            # dictionary or similar
            file = File()
            file.filename = value.get('filename','')
            file.file = value.get('file')
            file.filekey = node.name
            file.uid = value.get('uid', node.name)
            file.mime = value.get('mimetype')
            file.size = value.get('size')
            file.tempfile = True
            return file
        return value
    
    def deserialize(self, node, value, formstruct=None):
        return value


class FileUploadWidget2(Widget):
    """
    Represent a file upload.  Meant to work with a
    :class:`reform.FileData` schema node.

    **Attributes/Arguments**

    template
        The template name used to render the widget.  Default:
        ``file_upload``.

    size
        The ``size`` attribute of the input field (default ``None``).
    """
    template = 'file_upload'
    size = None

    def __init__(self, **kw):
        Widget.__init__(self, **kw)

    def serialize(self, field, cstruct):
        if cstruct in ("", null, None):
            cstruct = {}
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct in ("", null, None):
            return null
        file = File()
        file.filename = pstruct.filename
        file.file = pstruct.file
        file.filekey = field.name
        #file.uid = pstruct.uid
        file.mime = pstruct.type
        file.size = pstruct.length
        file.tempfile = True
        return file




def SchemaFactory(self, form, fields, actions, force=False):
    """
    converts the fields to colander schema nodes including widget.
    If fielddef has node set and force is false node is used as widget. To overwrite set
    force = True.
    
    SchemaNode(...)
    """
    context = form.context
    kwWidget = {"form": form}
    for field in fields:
        ftype = field.datatype
            
        if field.get("node") and not force:
            sc.add(field.get("node"))
            continue
            
        # for all fields
        kw = {  "name": field.id,
                "title": field.name,
                "description": field.description
        }
        # custom validator
        if field.settings and field.settings.get("validator"):
            kw["validator"] = field.settings["validator"]
        # custom widget
        if field.settings and field.settings.get("widget"):
            kw["widget"] = field.settings["widget"]

        if not field.required:
            kw["missing"] = null # or "" ?
        if field.default != None:
            kw["default"] = field.default 
            
        if field.hidden:
            if not "widget" in kw:
                kw["widget"] = HiddenWidget(**kwWidget)
            n = SchemaNode(String(), **kw)
                
        elif ftype == "string":
            if not "validator" in kw:
                kw["validator"] = Length(max=field.get("size",255))
            if not "widget" in kw:
                kw["widget"] = TextInputWidget(size=field.get("len",50), **kwWidget)
            n = SchemaNode(String(), **kw)
            
        elif ftype == "number":
            n = SchemaNode(Integer(), **kw)
                
        elif ftype == "float":
            n = SchemaNode(Float(), **kw)

        elif ftype == "bool":
            n = SchemaNode(Boolean(), **kw)

        elif ftype == "htext":
            if not "validator" in kw:
                kw["validator"] = Length(max=field.get("size",1000000))
            if not "widget" in kw:
                width = field.settings.get("width", 500)
                height = field.settings.get("height", 250)
                kw["widget"] = RichTextWidget(width=width, height=height, **kwWidget)
            n = SchemaNode(String(), **kw)

        elif ftype in ("text",):
            if not "validator" in kw:
                kw["validator"] = Length(max=field.get("size",1000000))
            if not "widget" in kw:
                kw["widget"] = TextAreaWidget(rows=10, cols=60, **kwWidget)
            n = SchemaNode(String(), **kw)
            
        elif ftype in ("code", "json"):
            if not "validator" in kw:
                kw["validator"] = Length(max=field.get("size",1000000))
            if not "widget" in kw:
                kw["widget"] = CodeTextWidget(**kwWidget)
            n = SchemaNode(String(), **kw)
            
        elif ftype == "file":
            if not "widget" in kw:
                kw["widget"] = FileUploadWidget2(**kwWidget)
            n = SchemaNode(FileData2(), **kw)
        #elif ftype == "file":
        #    kw["widget"] = FileUploadWidget(tmpstore, **kwWidget)
        #    n = SchemaNode(FileData(), **kw)
                
        elif ftype == "date":
            if not "widget" in kw:
                kw["widget"] = DateInputWidget(**kwWidget)
            #kw["options"] = {'dateFormat': 'yyyy/mm/dd', 'timeFormat': 'hh:mm:ss', 'separator': ' '}
            n = SchemaNode(Date(), **kw)
                
        elif ftype == "datetime":
            if not "widget" in kw:
                kw["widget"] = DateTimeInputWidget(**kwWidget)
            #kw["options"] = {'dateFormat': 'yyyy/mm/dd', 'timeFormat': 'hh:mm:ss', 'separator': ' '}
            n = SchemaNode(DateTime(), **kw)

        elif ftype == "list":
            if not "widget" in kw:
                v = form.app.root().LoadListItems(field, context)
                if field.settings and field.settings.get("addempty"):
                    v.insert(0,{"id":u"","name":u""})
                values=ConvertDictListToTuple(v)
                kw["widget"] = SelectWidget(values=values, **kwWidget)
            n = SchemaNode(String(), **kw)
            
        elif ftype == "radio":
            if not "widget" in kw:
                v = form.app.root().LoadListItems(field, context)
                values=ConvertDictListToTuple(v)
                kw["widget"] = RadioChoiceWidget(values=values, **kwWidget)
            n = SchemaNode(String(), **kw)

        elif ftype == "mselection":
            if not "widget" in kw:
                v = form.app.root().LoadListItems(field, context)
                values=ConvertDictListToTuple(v)
                kw["widget"] = SelectWidget(values=values, size=field.get("len", 4), **kwWidget)
            n = SchemaNode(List(allow_empty=True), **kw)

        elif ftype == "mcheckboxes":
            if not "widget" in kw:
                v = form.app.root().LoadListItems(field, context)
                values=ConvertDictListToTuple(v)
                kw["widget"] = CheckboxChoiceWidget(values=values, **kwWidget)
            n = SchemaNode(List(allow_empty=True), **kw)

        elif ftype == "email":
            if not "validator" in kw:
                kw["validator"] = Email()
            if not "widget" in kw:
                kw["widget"] = TextInputWidget(size=field.get("len",50), **kwWidget)
            n = SchemaNode(String(), **kw)
        
        elif ftype == "url":
            if not "validator" in kw:
                kw["validator"] = Length(max=field.get("size",255))
            kw["widget"] = TextInputWidget(size=field.get("len",50), **kwWidget)
            n = SchemaNode(String(), **kw)

        elif ftype == "urllist":
            if not "validator" in kw:
                kw["validator"] = Length(max=field.get("size",1000000))
            kw["widget"] = TextAreaWidget(rows=10, cols=60, **kwWidget)
            n = SchemaNode(String(), **kw)

        elif ftype == "password":
            if not "validator" in kw:
                kw["validator"] = Length(min=5, max=20)
            if not "widget" in kw:
                if field.settings.get("single",False):
                    kw["widget"] = PasswordWidget(size=field.get("len",50), **kwWidget)
                else:    
                    kw["widget"] = CheckedPasswordWidget(size=field.get("len",50), update=field.settings.get("update",False), **kwWidget)
            n = SchemaNode(String(), **kw)

        elif ftype == "unit":
            n = SchemaNode(Integer(), **kw)
            #id exists validator

        elif ftype == "unitlist":
            if not "validator" in kw:
                kw["validator"] = Length(max=field.get("size",255))
            if not "widget" in kw:
                kw["widget"] = TextInputWidget(size=field.get("len",50), **kwWidget)
            n = SchemaNode(String(), **kw)

        else:
            continue
            # skipped
            #timestamp (Timestamp) -> readonly
            
        # add to class
        form.add(n)
            
    # add buttons
    buttons = []
    for action in actions:
        if action.get("hidden"):
            continue
        buttons.append(Button(name=u"%s$"%(action.get("id")), title=action.get("name"), action=action, cls=action.get("cls", "btn submit")))
    form.buttons = buttons

    return form
    
    

