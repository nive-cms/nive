class ValidationFailure(Exception):
    """
    The exception raised by :meth:`reform.widget.Widget.validate`
    (most often called as ``form.validate(fields)``) when the supplied
    field data does not pass the overall constraints of the schema
    associated with the widget.

    **Attributes**

    ``field``
       The field :meth:`reform.form.Field.validate` was
       called on (usually a :class:`reform.form.Form` object).

    ``cstruct``
       The unvalidatable :term:`cstruct` that was returned from
       :meth:`reform.widget.Widget.deserialize`.

    ``error``
       The original :class:`colander.Invalid` exception raised by
       :meth:`reform.schema.SchemaNode.deserialize` which caused
       this exception to need to be raised.
    """
    def __init__(self, field, cstruct, error):
        Exception.__init__(self)
        self.field = field
        self.cstruct = cstruct
        self.error = error

    def render(self):
        """
        Used to reserialize the form in such a way that the user will
        see error markers in the form HTML.  This method accepts no
        arguments and returns text representing the HTML of a form
        rendering.
        """
        return self.field.widget.serialize(self.field, self.cstruct)

class TemplateError(Exception):
    pass

