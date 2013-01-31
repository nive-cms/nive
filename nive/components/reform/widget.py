import csv
import random
import string
import StringIO
import urllib

from nive.components.reform import schema 
from nive.components.reform.i18n import _
from nive.components.reform.schema import Invalid
from nive.components.reform.schema import null

try:
    import json 
except ImportError: # PRAGMA: no cover
    import simplejson as json 


class Widget(object):
    """
    A widget is the building block for rendering logic.  The
    :class:`reform.widget.Widget` class is never instantiated
    directly: it is the abstract class from which all other widget
    types within :mod:`reform.widget` derive.  It should likely also
    be subclassed by application-developer-defined widgets.

    A widget instance is attached to a field during normal operation.
    A widget is not meant to carry any state.  Instead, widget
    implementations should use the ``field`` object passed to them
    during :meth:`reform.widget.Widget.serialize` and
    :meth:`reform.widget.Widget.deserialize` as a scratchpad for state
    information.

    All widgets have the following attributes:

    hidden
        An attribute indicating the hidden state of this widget.  The
        default is ``False``.  If this attribute is not ``False``, the
        field associated with this widget will not be rendered in the
        form (although, if the widget is a structural widget, its
        children will be; ``hidden`` is not a recursive flag).  No
        label, no error message, nor any furniture such as a close
        button when the widget is one of a sequence will exist for the
        field in the rendered form.

    category
        A string value indicating the *category* of this widget.  This
        attribute exists to inform structural widget rendering
        behavior.  For example, when a text widget or another simple
        'leaf-level' widget is rendered as a child of a mapping widget
        using the default template mapping template, the field title
        associated with the child widget will be rendered above the
        field as a label by default.  This is because simple child
        widgets are in the ``default`` category and no special action
        is taken when a structural widget renders child widgets that
        are in the ``default`` category.  However, if the default
        mapping widget encounters a child widget with the category of
        ``structural`` during rendering (the default mapping and
        sequence widgets are in this category), it omits the title.
        Default: ``default``

    error_class
        The name of the CSS class attached to various tags in the form
        renderering indicating an error condition for the field
        associated with this widget.  Default: ``error``.
    
    css_class
        The name of the CSS class attached to various tags in
        the form renderering specifying a new class for the field
        associated with this widget.  Default: ``None`` (no class).

    requirements
        A sequence of two-tuples in the form ``( (requirement_name,
        version_id), ...)`` indicating the logical external
        requirements needed to make this widget render properly within
        a form.  The ``requirement_name`` is a string that *logically*
        (not concretely, it is not a filename) identifies *one or
        more* Javascript or CSS resources that must be included in the
        page by the application performing the form rendering.  The
        requirement name string value should be interpreted as a
        logical requirement name (e.g. ``jquery`` for JQuery,
        'tinymce' for Tiny MCE).  The ``version_id`` is a string
        indicating the version number (or ``None`` if no particular
        version is required).  For example, a rich text widget might
        declare ``requirements = (('tinymce', '3.3.8'),)``.  See also:
        :ref:`specifying_widget_requirements` and
        :ref:`widget_requirements`.

        Default: ``()`` (the empty tuple, meaning no special
        requirements).

    These attributes are also accepted as keyword arguments to all
    widget constructors; if they are passed, they will override the
    defaults.

    Particular widget types also accept other keyword arguments that
    get attached to the widget as attributes.  These are documented as
    'Attributes/Arguments' within the documentation of each concrete
    widget implementation subclass.
    """

    hidden = False
    category = 'default'
    error_class = 'error'
    css_class = None
    requirements = ()

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def serialize(self, field, cstruct):
        """
        The ``serialize`` method of a widget must serialize a
        :term:`cstruct` value to an HTML rendering.  A :term:`cstruct`
        value is the value which results from a :term:`Colander`
        schema serialization for the schema node associated with this
        widget.  ``serialize`` should return the HTML rendering: the
        result of this method should always be a string containing
        HTML.  The ``field`` argument is the :term:`field` object to
        which this widget is attached.  
        """
        raise NotImplementedError

    def deserialize(self, field, pstruct, formstruct=None):
        """
        The ``deserialize`` method of a widget must deserialize a
        :term:`pstruct` value to a :term:`cstruct` value and return the
        :term:`cstruct` value.  The ``pstruct`` argument is a value looked up in
        the request or source data. ``formstruct`` contains all values. The
        ``field`` argument is the field object to which this widget is
        attached.
        """
        raise NotImplementedError

    def handle_error(self, field, error):
        """
        The ``handle_error`` method of a widget must:

        - Set the ``error`` attribute of the ``field`` object it is
          passed, if the ``error`` attribute has not already been set.

        - Call the ``handle_error`` method of each subfield which also
          has an error (as per the ``error`` argument's ``children``
          attribute).
        """
        if field.error is None:
            field.error = error
        # XXX exponential time
        for e in error.children:
            for num, subfield in enumerate(field.children):
                if e.pos == num:
                    subfield.widget.handle_error(subfield, e)


class FormWidget(Widget):
    """
    The top-level widget; represents an entire form.

    **Attributes/Arguments**

    template
        The template name used to render the widget.  Default:
        ``form``.

    item_template
        The template name used to render each item in the form.
        Default: ``mapping_item``.

    """
    template = 'form'
    item_template = 'field'
    error_class = None
    category = 'structural'
    requirements = ( ('reform', None), )

    def serialize(self, field, cstruct):
        if cstruct in (null, None):
            cstruct = {}
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct,
                              null=null)

    def deserialize(self, field, pstruct, formstruct=None):
        error = None
        
        result = {}

        if pstruct is null:
            pstruct = {}

        for num, subfield in enumerate(field.children):
            name = subfield.name
            subval = pstruct.get(name, null)
                            
            try:
                result[name] = subfield.deserialize(subval, pstruct)
            except Invalid, e:
                result[name] = e.value
                if error is None:
                    error = Invalid(field.schema, value=result)
                error.add(e, num)

        if error is not None:
            raise error

        return result
    
    
class TextInputWidget(Widget):
    """
    Renders an ``<input type="text"/>`` widget.

    **Attributes/Arguments**

    size
        The size, in columns, of the text input field.  Defaults to
        ``None``, meaning that the ``size`` is not included in the
        widget output (uses browser default size).

    template
       The template name used to render the widget.  Default:
        ``textinput``.

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).

    mask
        A :term:`jquery.maskedinput` input mask, as a string.

        a - Represents an alpha character (A-Z,a-z)
        9 - Represents a numeric character (0-9)
        * - Represents an alphanumeric character (A-Z,a-z,0-9)

        All other characters in the mask will be considered mask
        literals.

        Example masks:

          Date: 99/99/9999

          US Phone: (999) 999-9999

          US SSN: 999-99-9999

        When this option is used, the :term:`jquery.maskedinput`
        library must be loaded into the page serving the form for the
        mask argument to have any effect.  See :ref:`masked_input`.

    mask_placeholder
        The placeholder for required nonliteral elements when a mask
        is used.  Default: ``_`` (underscore).
    """
    template = 'textinput'
    size = None
    strip = True
    mask = None
    mask_placeholder = "_"
    requirements = ( ('jquery.maskedinput', None), )

    def serialize(self, field, cstruct):
        if cstruct in (null, None):
            cstruct = ''
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct is null:
            return null
        if self.strip:
            pstruct = pstruct.strip()
        if not pstruct and field.required:
            return null
        return pstruct

class AutocompleteInputWidget(Widget):
    """
    Renders an ``<input type="text"/>`` widget which provides
    autocompletion via a list of values.

    When this option is used, the :term:`jquery.ui.autocomplete`
    library must be loaded into the page serving the form for
    autocompletion to have any effect.  See also
    :ref:`autocomplete_input`.  A version of :term:`JQuery UI` which
    includes the autoinclude sublibrary is included in the reform
    static directory. The default styles for JQuery UI are also
    available in the reform static/css directory.

    **Attributes/Arguments**

    size
        The size, in columns, of the text input field.  Defaults to
        ``None``, meaning that the ``size`` is not included in the
        widget output (uses browser default size).

    template
        The template name used to render the widget.  Default:
        ``autocomplete_textinput``.

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).

    values
        ``values`` from which :term:`jquery.ui.autocomplete` provides
        autocompletion. It MUST be an iterable that can be converted
        to a json array by [simple]json.dumps. It is also possible
        to pass a [base]string representing a remote URL.

        If ``values`` is a string it will be treated as a
        URL. If values is an iterable which can be serialized to a
        :term:`json` array, it will be treated as local data.

        If a string is provided to a URL, an :term:`xhr` request will
        be sent to the URL. The response should be a JSON
        serialization of a list of values.  For example:

          ['foo', 'bar', 'baz']

        Defaults to ``None``.

    min_length
        ``min_length`` is an optional argument to
        :term:`jquery.ui.autocomplete`. The number of characters to
        wait for before activating the autocomplete call.  Defaults to
        ``2``.

    delay
        ``delay`` is an optional argument to
        :term:`jquery.ui.autocomplete`. It sets the time to wait after a
        keypress to activate the autocomplete call.
        Defaults to ``10`` ms or ``400`` ms if a url is passed.
    """
    delay = None
    min_length = 2
    size = None
    strip = True
    template = 'autocomplete_input'
    values = None
    requirements = ( ('jqueryui', None), )

    def serialize(self, field, cstruct):
        if cstruct in (null, None):
            cstruct = ''
        options = {}
        if not self.delay:
            # set default delay if None
            options['delay'] = (isinstance(self.values,
                                          basestring) and 400) or 10
        options['minLength'] = self.min_length
        options = json.dumps(options)
        values = json.dumps(self.values)
        template = self.template
        return field.renderer(template,
                              cstruct=cstruct,
                              field=field,
                              options=options,
                              values=values)

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct is null:
            return null
        if self.strip:
            pstruct = pstruct.strip()
        if not pstruct:
            return null
        return pstruct


class DateInputWidget(Widget):
    """
    
    Renders a JQuery UI date picker widget
    (http://jqueryui.com/demos/datepicker/).  Most useful when the
    schema node is a ``colander.Date`` object.

    **Attributes/Arguments**

    size
        The size, in columns, of the text input field.  Defaults to
        ``None``, meaning that the ``size`` is not included in the
        widget output (uses browser default size).

    template
        The template name used to render the widget.  Default:
        ``dateinput``.

    """
    template = 'dateinput'
    size = None
    requirements = ( ('jqueryui', None), )

    def serialize(self, field, cstruct):
        if cstruct in (null, None):
            cstruct = ''
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct in ('', null):
            return null
        return pstruct

class DateTimeInputWidget(DateInputWidget):
    """
    Renders a a jQuery UI date picker with a JQuery Timepicker add-on
    (http://trentrichardson.com/examples/timepicker/).  Used for
    ``colander.DateTime`` schema nodes.

    **Attributes/Arguments**

    options
        A dictionary of options that's passed to the datetimepicker.

    size
        The size, in columns, of the text input field.  Defaults to
        ``None``, meaning that the ``size`` is not included in the
        widget output (uses browser default size).

    template
        The template name used to render the widget.  Default:
        ``dateinput``.

    """
    template = 'datetimeinput'
    size = None
    requirements = ( ('jqueryui', None), ('datetimepicker', None), )
    option_defaults = {'dateFormat': 'yy-mm-dd',
                       'timeFormat': 'hh:mm:ss',
                       'separator': ' '}
    options = {}

    def _options(self):
        options = self.option_defaults.copy()
        options.update(self.options)
        return options

    def serialize(self, field, cstruct):
        if cstruct in (null, None):
            cstruct = ''
        template = self.template
        options = self._options()
        if len(cstruct) == 25: # strip timezone if it's there
            cstruct = cstruct[:-6]
        cstruct = options['separator'].join(cstruct.split('T'))
        return field.renderer(
            template,
            field=field,
            cstruct=cstruct,
            options=json.dumps(self._options()),
            )

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct in ('', null):
            return null
        options = self._options()
        return pstruct.replace(options['separator'], 'T')

class TextAreaWidget(TextInputWidget):
    """
    Renders a ``<textarea>`` widget.

    **Attributes/Arguments**

    cols
        The size, in columns, of the text input field.  Defaults to
        ``None``, meaning that the ``cols`` is not included in the
        widget output (uses browser default cols).

    rows
        The size, in rows, of the text input field.  Defaults to
        ``None``, meaning that the ``rows`` is not included in the
        widget output (uses browser default cols).

    template
        The template name used to render the widget.  Default:
        ``textarea``.

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).
    """
    template = 'textarea'
    cols = None
    rows = None
    strip = True

class RichTextWidget(TextInputWidget):
    """
    Renders a ``<textarea>`` widget with the
    :term:`TinyMCE Editor`.

    To use this widget the :term:`TinyMCE Editor` library must be
    provided in the page where the widget is rendered. A version of
    :term:`TinyMCE Editor` is included in reform's static directory.
    

    **Attributes/Arguments**

    height
        The height, in pixels, of the text editor.  Defaults to 240.

    delayed_load
        If you have many richtext fields, you can set this option to
        ``true``, and the richtext editor will only be loaded when
        clicking on the field (default ``false``)

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).

    template
        The template name used to render the widget.  Default:
        ``richtext``.

    skin 
        The skin for the WYSIWYG editor. Normally only needed if you
        plan to reuse a TinyMCE js from another framework that
        defined a skin.

    theme
        The theme for the WYSIWYG editor, ``simple`` or ``advanced``.
        Defaults to ``simple``.

    width
        The width, in pixels, of the editor.  Defaults to 500.
        The width can also be given as a percentage (e.g. '100%')
        relative to the width of the enclosing element.
    """
    height = 240
    width = 500
    delayed_load = False
    strip = True
    template = 'richtext'
    skin = 'default'
    theme = 'simple'
    requirements = ( ('tinymce', None), )

class PasswordWidget(TextInputWidget):
    """
    Renders a single <input type="password"/> input field.

    **Attributes/Arguments**

    template
        The template name used to render the widget.  Default:
        ``password``.

    size
        The ``size`` attribute of the password input field (default:
        ``None``).

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).
    """
    template = 'password'

class HiddenWidget(Widget):
    """
    Renders an ``<input type="hidden"/>`` widget.

    **Attributes/Arguments**

    template
        The template name used to render the widget.  Default:
        ``hidden``.
    """
    template = 'hidden'
    hidden = True

    def serialize(self, field, cstruct):
        if cstruct in (null, None):
            cstruct = ''
        return field.renderer(self.template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct, formstruct=None):
        if not pstruct:
            return null
        return pstruct

class CheckboxWidget(Widget):
    """
    Renders an ``<input type="checkbox"/>`` widget.

    **Attributes/Arguments**

    true_val
        The value which should be returned during deserialization if
        the box is checked.  Default: ``true``.

    false_val
        The value which should be returned during deserialization if
        the box was left unchecked.  Default: ``false``.

    template
        The template name used to render the widget.  Default:
        ``checkbox``.

    """
    true_val = 'true'
    false_val = 'false'

    template = 'checkbox'

    def serialize(self, field, cstruct):
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct is null:
            return self.false_val
        return (pstruct == self.true_val) and self.true_val or self.false_val

class SelectWidget(Widget):
    """
    Renders ``<select>`` field based on a predefined set of values.

    **Attributes/Arguments**

    values
        A sequence of two-tuples (both values must be **string** or
        **unicode** values) indicating allowable, displayed values,
        e.g. ``( ('true', 'True'), ('false', 'False') )``.  The first
        element in the tuple is the value that should be returned when
        the form is posted.  The second is the display value.

    size
        The ``size`` attribute of the select input field (default:
        ``None``).

    null_value
        The value which represents the null value.  When the null
        value is encountered during serialization, the
        :attr:`colander.null` sentinel is returned to the caller.
        Default: ``''`` (the empty string).

    template
        The template name used to render the widget.  Default:
        ``select``.

    """
    template = 'select'
    null_value = ''
    values = ()
    size = None

    def serialize(self, field, cstruct):
        if cstruct in (null, None):
            cstruct = self.null_value
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct in (null, self.null_value):
            return null
        return pstruct
    
    
    def controlset_fields(self, field, value=None, format='html'):
        """
        Returns a list of controlset field ids. If `value` is None all controlled
        fields will be returned otherwise only the ids linked to this value.
        """
        items = self.form.GetField(field.name).listItems(field, None)
        ids = []
        for i in items:
            if value and value!=i.id:
                continue
            for v in i.fields:
                ids.append(v.id)
        if format=="html":
            return json.dumps(ids)
        return ids
        

class RadioChoiceWidget(SelectWidget):
    """
    Renders a sequence of ``<input type="radio"/>`` buttons based on a
    predefined set of values.

    **Attributes/Arguments**

    values
        A sequence of two-tuples (both values must be **string** or
        **unicode** values) indicating allowable, displayed values,
        e.g. ``( ('true', 'True'), ('false', 'False') )``.  The first
        element in the tuple is the value that should be returned when
        the form is posted.  The second is the display value.

    template
        The template name used to render the widget.  Default:
        ``radio_choice``.

    null_value
        The value used to replace the ``colander.null`` value when it
        is passed to the ``serialize`` or ``deserialize`` method.
        Default: the empty string.
    """
    template = 'radio_choice'

class CheckboxChoiceWidget(Widget):
    """
    Renders a sequence of ``<input type="check"/>`` buttons based on a
    predefined set of values.

    **Attributes/Arguments**

    values
        A sequence of two-tuples (both values must be **string** or
        **unicode** values) indicating allowable, displayed values,
        e.g. ``( ('true', 'True'), ('false', 'False') )``.  The first
        element in the tuple is the value that should be returned when
        the form is posted.  The second is the display value.

    template
        The template name used to render the widget.  Default:
        ``checkbox_choice``.

    null_value
        The value used to replace the ``colander.null`` value when it
        is passed to the ``serialize`` or ``deserialize`` method.
        Default: the empty string.
    """
    null_value = ()
    template = 'checkbox_choice'
    values = ()

    def serialize(self, field, cstruct):
        if cstruct in (null, None):
            cstruct = self.null_value
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct is null:
            return self.null_value
        if isinstance(pstruct, basestring):
            return (pstruct,)
        return tuple(pstruct)

class CheckedInputWidget(Widget):
    """
    Renders two text input fields: 'value' and 'confirm'.
    Validates that the 'value' value matches the 'confirm' value.

    **Attributes/Arguments**

    template
        The template name used to render the widget.  Default:
        ``checked_input``.

    size
        The ``size`` attribute of the input fields (default:
        ``None``, default browser size).

    mismatch_message
        The message to be displayed when the value in the primary
        field doesn't match the value in the confirm field.

    mask
        A :term:`jquery.maskedinput` input mask, as a string.  Both
        input fields will use this mask.

        a - Represents an alpha character (A-Z,a-z)
        9 - Represents a numeric character (0-9)
        * - Represents an alphanumeric character (A-Z,a-z,0-9)

        All other characters in the mask will be considered mask
        literals.

        Example masks:

          Date: 99/99/9999

          US Phone: (999) 999-9999

          US SSN: 999-99-9999

        When this option is used, the :term:`jquery.maskedinput`
        library must be loaded into the page serving the form for the
        mask argument to have any effect.  See :ref:`masked_input`.

    mask_placeholder
        The placeholder for required nonliteral elements when a mask
        is used.  Default: ``_`` (underscore).
    """
    template = 'checked_input'
    size = None
    mismatch_message = _('Fields did not match')
    subject = _('Value')
    confirm_subject = _('Confirm Value')
    mask = None
    mask_placeholder = "_"
    requirements = ( ('jquery.maskedinput', None), )

    def serialize(self, field, cstruct):
        if cstruct in (null, None):
            cstruct = ''
        confirm = getattr(field, '%s-confirm' % (field.name,), '')
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct,
                              confirm=confirm, subject=self.subject,
                              confirm_subject=self.confirm_subject,
                              )

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct is null:
            return null
        value = pstruct
        confirm = ''
        if formstruct:
            confirm = formstruct.get('%s-confirm' % (field.name,)) or ''
        setattr(field, '%s-confirm' % (field.name,), confirm)
        if (value or confirm) and (value != confirm):
            raise Invalid(field.schema, self.mismatch_message, value)
        if not value:
            return null
        return value

class CheckedPasswordWidget(CheckedInputWidget):
    """
    Renders two password input fields: 'password' and 'confirm'.
    Validates that the 'password' value matches the 'confirm' value.

    **Attributes/Arguments**

    template
        The template name used to render the widget.  Default:
        ``checked_password``.

    size
        The ``size`` attribute of the password input field (default:
        ``None``).
    
    update
        The ``update`` attribute prevents rendering of existing passwords.
        Instead ``placeholder`` is used.
        
    """
    template = 'checked_password'
    mismatch_message = _('Password did not match confirm')
    size = None
    update = False
    placeholder = ''

    def serialize(self, field, cstruct):
        if self.update and cstruct in (null, None, ''):
            cstruct = confirm = self.placeholder
        elif cstruct in (null, None):
            cstruct = confirm = ''
        else:
            confirm = getattr(field, '%s-confirm' % (field.name,), '')
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct,
                              confirm=confirm, subject=self.subject,
                              confirm_subject=self.confirm_subject,
                              )

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct in (null, self.placeholder):
            return null
        value = pstruct
        confirm = formstruct.get('%s-confirm' % (field.name,)) or ''
        setattr(field, '%s-confirm' % (field.name,), confirm)
        if (value or confirm) and (value != confirm):
            raise Invalid(field.schema, self.mismatch_message, value)
        if not value:
            return null
        return value




#<removed class MappingWidget(Widget):
#<removed class SequenceWidget(Widget):

class FileUploadWidget(Widget):
    """
    Represent a file upload.  Meant to work with a
    :class:`deform.FileData` schema node.

    This widget accepts a single required positional argument in its
    constructor: ``tmpstore``.  This argument should be passed an
    instance of an object that implements the
    :class:`deform.interfaces.FileUploadTempStore` interface.  Such an
    instance will hold on to file upload data during the validation
    process, so the user doesn't need to reupload files if other parts
    of the form rendering fail validation.  See also
    :class:`deform.interfaces.FileUploadTempStore`.

    **Attributes/Arguments**

    template
        The template name used to render the widget.  Default:
        ``file_upload``.

    readonly_template
        The template name used to render the widget in read-only mode.
        Default: ``readonly/file_upload``.

    size
        The ``size`` attribute of the input field (default ``None``).
    """
    template = 'file_upload'
    readonly_template = 'readonly/file_upload'
    size = None

    def __init__(self, tmpstore, **kw):
        Widget.__init__(self, **kw)
        self.tmpstore = tmpstore

    def random_id(self):
        return ''.join(
            [random.choice(string.uppercase+string.digits) for i in range(10)])

    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (null, None):
            cstruct = {}
        if cstruct:
            uid = cstruct['uid']
            if not uid in self.tmpstore:
                self.tmpstore[uid] = cstruct

        template = readonly and self.readonly_template or self.template
        return field.renderer(template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct is null:
            return null
        #!!! switch to formstruct ?
        upload = pstruct.get('upload')
        uid = pstruct.get('uid')

        if hasattr(upload, 'file'):
            # the upload control had a file selected
            data = schema.filedict()
            data['fp'] = upload.file
            data['filename'] = upload.filename
            data['mimetype'] = upload.type
            data['size']  = upload.length
            if uid is None:
                # no previous file exists
                while 1:
                    uid = self.random_id()
                    if self.tmpstore.get(uid) is None:
                        data['uid'] = uid
                        data['preview_url'] = self.tmpstore.preview_url(uid)
                        self.tmpstore[uid] = data
                        break
            else:
                # a previous file exists
                data['uid'] = uid
                data['preview_url'] = self.tmpstore.preview_url(uid)
                self.tmpstore[uid] = data
        else:
            # the upload control had no file selected
            if uid is None:
                # no previous file exists
                return null
            else:
                # a previous file should exist
                data = self.tmpstore.get(uid)
                # but if it doesn't, don't blow up
                if data is None:
                    return null

        return data


class DatePartsWidget(Widget):
    """
    Renders a set of ``<input type='text'/>`` controls based on the
    year, month, and day parts of the serialization of a
    :class:`colander.Date` object or a string in the format
    ``YYYY-MM-DD``.  This widget is usually meant to be used as widget
    which renders a :class:`colander.Date` type; validation
    likely won't work as you expect if you use it against a
    :class:`colander.String` object, but it is possible to use it
    with one if you use a proper validator.

    **Attributes/Arguments**

    template
        The template name used to render the input widget.  Default:
        ``dateparts``.

    size
        The size (in columns) of each date part input control.
        Default: ``None`` (let browser decide).

    assume_y2k
        If a year is provided in 2-digit form, assume it means
        2000+year.  Default: ``True``.

    """
    template = 'dateparts'
    size = None
    assume_y2k = True

    def serialize(self, field, cstruct):
        if cstruct is null:
            year = ''
            month = ''
            day = ''
        else:
            year, month, day = cstruct.split('-', 2)
        template = self.template
        return field.renderer(template, field=field, cstruct=cstruct,
                              year=year, month=month, day=day)

    def deserialize(self, field, pstruct, formstruct=None):
        if formstruct and 'year' in formstruct and 'month' in formstruct and 'day' in formstruct:
            year = formstruct['year'].strip()
            month = formstruct['month'].strip()
            day = formstruct['day'].strip()
            
            if (not year and not month and not day):
                return null

            if self.assume_y2k and len(year) == 2:
                year = '20' + year
            result = '-'.join([year, month, day])

            if (not year or not month or not day):
                raise Invalid(field.schema, _('Incomplete date'), result)
        elif pstruct is null:
            return null
        else:
            result = pstruct

        return result

class TextAreaCSVWidget(Widget):
    """
    Widget used for a sequence of tuples of scalars; allows for
    editing CSV within a text area.  Used with a schema node which is
    a sequence of tuples.
    
    **Attributes/Arguments**

    cols
        The size, in columns, of the text input field.  Defaults to
        ``None``, meaning that the ``cols`` is not included in the
        widget output (uses browser default cols).

    rows
        The size, in rows, of the text input field.  Defaults to
        ``None``, meaning that the ``rows`` is not included in the
        widget output (uses browser default cols).

    template
        The template name used to render the widget.  Default:
        ``textarea``.

    """
    template = 'textarea'
    cols = None
    rows = None

    def serialize(self, field, cstruct):
        if cstruct is null:
            cstruct = []
        textrows = getattr(field, 'unparseable', None)
        if textrows is None:
            outfile = StringIO.StringIO()
            writer = csv.writer(outfile)
            writer.writerows(cstruct)
            textrows = outfile.getvalue()
        template = self.template
        return field.renderer(template, field=field, cstruct=textrows)
        
    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct is null:
            return null
        if not pstruct.strip():
            return null
        try:
            infile = StringIO.StringIO(pstruct)
            reader = csv.reader(infile)
            rows = list(reader)
        except Exception, e:
            field.unparseable = pstruct
            raise Invalid(field.schema, str(e))
        return rows

    def handle_error(self, field, error):
        msgs = []
        if error.msg:
            field.error = error
        else:
            for e in error.children:
                msgs.append('line %s: %s' % (e.pos+1, e))
            field.error = Invalid(field.schema, '\n'.join(msgs))


class TextInputCSVWidget(Widget):
    """
    Widget used for a tuple of scalars; allows for editing a single
    CSV line within a text input.  Used with a schema node which is a
    tuple composed entirely of scalar values (integers, strings, etc).
    
    **Attributes/Arguments**

    template
        The template name used to render the widget.  Default:
        ``textinput``.

    size
        The size, in columns, of the text input field.  Defaults to
        ``None``, meaning that the ``size`` is not included in the
        widget output (uses browser default size).
    """
    template = 'textinput'
    size = None
    mask = None

    def serialize(self, field, cstruct):
        if cstruct is null:
            cstruct = ''
        textrow = getattr(field, 'unparseable', None)
        if textrow is None:
            outfile = StringIO.StringIO()
            writer = csv.writer(outfile)
            writer.writerow(cstruct)
            textrow = outfile.getvalue().strip()
        template = self.template
        return field.renderer(template, field=field, cstruct=textrow)
        
    def deserialize(self, field, pstruct, formstruct=None):
        if pstruct is null:
            return null
        if not pstruct.strip():
            return null
        try:
            infile = StringIO.StringIO(pstruct)
            reader = csv.reader(infile)
            row = reader.next()
        except Exception, e:
            field.unparseable = pstruct
            raise Invalid(field.schema, str(e))
        return row

    def handle_error(self, field, error):
        msgs = []
        if error.msg:
            field.error = error
        else:
            for e in error.children:
                msgs.append('%s' % e)
            field.error = Invalid(field.schema, '\n'.join(msgs))

class CodeTextWidget(TextInputWidget):
    """
    Renders a ``<textarea>`` widget with the
    :term:`Codemirror Editor`.

    **Attributes/Arguments**

    height
        The height, in pixels, of the text editor.  Defaults to 240.

    template
        The template name used to render the widget.  Default:
        ``codetext``.

    codetype 
        The skin for the WYSIWYG editor. Normally only needed if you
        plan to reuse a TinyMCE js from another framework that
        defined a skin.

    theme
        The theme for the WYSIWYG editor, ``simple`` or ``advanced``.
        Defaults to ``simple``.

    width
        The width, in pixels, of the editor.  Defaults to 500.
        The width can also be given as a percentage (e.g. '100%')
        relative to the width of the enclosing element.
    """
    height = 400
    width = 500
    template = 'codetext'
    codetype = 'default'
    theme = 'simple'
    requirements = ( ('codemirror', None), )



class ResourceRegistry(object):
    """ A resource registry maps :term:`widget requirement` name/version
    pairs to one or more relative resources.  A resource registry can
    be passed to a :class:`reform.Form` constructor; if a resource
    registry is *not* passed to the form constructor, a default
    resource registry is used by that form.  The default resource
    registry contains only mappings from requirement names to
    resources required by the built-in Deform widgets (not by any
    add-on widgets).

    If the ``use_defaults`` flag is True, the default set of Deform
    requirement-to-resource mappings is loaded into the registry.
    Otherwise, the registry is initialized without any mappings.
    """
    def __init__(self, use_defaults=True):
        if use_defaults is True:
            self.registry = default_resources.copy()
        else:
            self.registry = {}

    def set_js_resources(self, requirement, version, *resources):
        """ Set the Javascript resources for the requirement/version
        pair, using ``resources`` as the set of relative resource paths."""
        reqt = self.registry.setdefault(requirement, {})
        ver = reqt.setdefault(version, {})
        ver['js'] = resources

    def set_css_resources(self, requirement, version, *resources):
        """ Set the CSS resources for the requirement/version
        pair, using ``resources`` as the set of relative resource paths."""
        reqt = self.registry.setdefault(requirement, {})
        ver = reqt.setdefault(version, {})
        ver['css'] = resources

    def __call__(self, requirements):
        """ Return a dictionary representing the resources required
        for a particular set of requirements (as returned by
        :meth:`reform.Field.get_widget_requirements`).  The dictionary
        will be a mapping from resource type (``js`` and ``css`` are
        both keys in the dictionary) to a list of relative resource
        paths.  Each path is relative to wherever you've mounted
        Deform's ``static`` directory in your web server.  You can use
        the paths for each resource type to inject CSS and Javascript
        on-demand into the head of dynamic pages that render Deform
        forms.  """
        result = {'js':[], 'css':[]}
        for requirement, version in requirements:
            tmp = self.registry.get(requirement)
            if tmp is None:
                raise ValueError(
                    'Cannot resolve widget requirement %r' % requirement)
            versioned = tmp.get(version)
            if versioned is None:
                raise ValueError(
                    'Cannot resolve widget requirement %r (version %r)' % (
                        (requirement, version)))
            for thing in ('js', 'css'):
                sources = versioned.get(thing)
                if sources is None:
                    continue
                if not hasattr(sources, '__iter__'):
                    sources = (sources,)
                for source in sources:
                    if not source in result[thing]:
                        result[thing].append(source)
        return result

            
default_resources = {
    'jquery': {
        None:{
            'js':'scripts/jquery.min.js',
            },
        },
    'jqueryui': {
        None:{
            'js':('scripts/jquery.min.js',
                  'scripts/jquery-ui-1.8.11.custom.min.js'),
            'css':'css/ui-lightness/jquery-ui-1.8.11.custom.css',
            },
        },
    'jquery.form': {
        None:{
            'js':('scripts/jquery.min.js',
                  'scripts/jquery.form.js'),
            },
        },
    'jquery.maskedinput': {
        None:{
            'js':('scripts/jquery.min.js',
                  'scripts/jquery.maskedinput-1.2.2.min.js'),
            },
        },
    'datetimepicker': {
        None:{
            'js':('scripts/jquery.min.js',
                  'scripts/jquery-ui-timepicker-addon.js'),
            'css':'css/jquery-ui-timepicker-addon.css',
            },
        },
    'reform': {
        None:{
            'js':('scripts/jquery.min.js',
                  'scripts/jquery.form.js',
                  'scripts/reform.js'),
            },
        },
    'tinymce': {
        None:{
            'js':'tinymce/jscripts/tiny_mce/tiny_mce.js',
            },
        },
    'codemirror': {
        None:{
            'js':('codemirror/lib/codemirror.js',
                  'codemirror/mode/xml/xml.js',
                  'codemirror/mode/javascript/javascript.js',
                  'codemirror/mode/css/css.js',
                  'codemirror/mode/htmlmixed/htmlmixed.js'),
            'css':'codemirror/lib/codemirror.css',
            },
        },
    }

default_resource_registry = ResourceRegistry()

default_widget_makers = {
    #<removed schema.Mapping: widget.MappingWidget,
    #<removed schema.Sequence: widget.SequenceWidget,
    schema.String: TextInputWidget,
    schema.Integer: TextInputWidget,
    schema.Float: TextInputWidget,
    schema.Decimal: TextInputWidget,
    schema.Boolean: CheckboxWidget,
    schema.Date: DateInputWidget,
    schema.DateTime: DateTimeInputWidget,
    schema.Tuple: TextInputCSVWidget,
    schema.Set: CheckboxChoiceWidget,
    schema.List: CheckboxChoiceWidget
}