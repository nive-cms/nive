import unittest
import datetime
import nive.components.reform.widget
from nive.components.reform.schema import deferred

class TestFunctional(unittest.TestCase):
    def _makeSchema(self):
        from nive.components.reform.schema import Schema
        #from nive.components.reform.schema import MappingSchema
        #from nive.components.reform.schema import SequenceSchema
        from nive.components.reform.schema import SchemaNode
        from nive.components.reform.schema import String
        from nive.components.reform.schema import Boolean
        from nive.components.reform.schema import Date
    
        #class DatesSchema(SequenceSchema):
        #    date = SchemaNode(Date())

        #class SeriesSchema(MappingSchema):
        #    name = SchemaNode(String())
        #    dates = DatesSchema()

        class MySchema(Schema):
            name = SchemaNode(String())
            title = SchemaNode(String())
            cool = SchemaNode(Boolean(), default=True, missing=True)
            date = SchemaNode(Date())
            #series = SeriesSchema()

        schema = MySchema()
        return schema

    def _makeForm(self, schema):
        from nive.components.reform.form import Form
        return Form(schema, formid='myform')

    def _soupify(self, html):
        from BeautifulSoup import BeautifulSoup
        return BeautifulSoup(html)

    #<removed def test_render_empty(self):
    #<removed def test_render_not_empty(self):

    def test_widget_deserialize(self):
        filled = {
            'name': 'project1',
            'title': 'Cool project',
            'date': '2008-10-12',
            }
        schema = self._makeSchema()
        form = self._makeForm(schema)
        result = form.widget.deserialize(form, filled)
        expected = {'date': '2008-10-12',
                    'name': 'date series 1',
                    'cool': 'false',
                    'name': 'project1',
                    'title': 'Cool project'}
        self.assertEqual(result, expected)

    def test_validate(self):
        from nive.components.reform.schema import null
        from nive.components.reform.exception import ValidationFailure
        schema = self._makeSchema()
        form = self._makeForm(schema)
        try:
            form.validate([])
        except ValidationFailure, ve:
            e = ve.error
        self.assertEqual(form.error, e)
        self.assertEqual(form.children[0].error, e.children[0])
        self.assertEqual(form.children[1].error, e.children[1])
        #self.assertEqual(form.children[3].error, e.children[2])
        #self.assertEqual(form.children[3].children[0].error,
        #                 e.children[2].children[0])
        self.assertEqual(
            ve.cstruct,
            {
                'date': null, 
                'cool': 'false',
                'name': null,
                'title': null,
             }
            )
        
@deferred
def deferred_date_validator(node, kw):
    max_date = kw.get('max_date')
    if max_date is None: max_date = datetime.date.today()
    return schema.Range(min=datetime.date.min, max=max_date)

@deferred
def deferred_date_description(node, kw):
    max_date = kw.get('max_date')
    if max_date is None: max_date = datetime.date.today()
    return 'Blog post date (no earlier than %s)' % max_date.ctime()

@deferred
def deferred_date_missing(node, kw):
    default_date = kw.get('default_date')
    if default_date is None: default_date = datetime.date.today()
    return default_date

@deferred
def deferred_body_validator(node, kw):
    max_bodylen = kw.get('max_bodylen')
    if max_bodylen is None:  max_bodylen = 1 << 18
    return schema.Length(max=max_bodylen)

@deferred
def deferred_body_description(node, kw):
    max_bodylen = kw.get('max_bodylen')
    if max_bodylen is None:  max_bodylen = 1 << 18
    return 'Blog post body (no longer than %s bytes)' % max_bodylen

@deferred
def deferred_body_widget(node, kw):
    body_type = kw.get('body_type')
    if body_type == 'richtext':
        widget = reform.widget.RichTextWidget()
    else: # pragma: no cover
        widget = reform.widget.TextAreaWidget()
    return widget

@deferred
def deferred_category_validator(node, kw):
    categories = kw.get('categories', [])
    return schema.OneOf([ x[0] for x in categories ])

@deferred
def deferred_category_widget(node, kw):
    categories = kw.get('categories', [])
    return reform.widget.RadioChoiceWidget(values=categories)

from nive.components.reform import schema
from nive.components import reform

class BlogPostSchema(schema.Schema):
    title = schema.SchemaNode(
        schema.String(),
        title = 'Title',
        description = 'Blog post title',
        validator = schema.Length(min=5, max=100),
        widget = reform.widget.TextInputWidget(),
        )
    date = schema.SchemaNode(
        schema.Date(),
        title = 'Date',
        missing = deferred_date_missing,
        description = deferred_date_description,
        validator = deferred_date_validator,
        widget = reform.widget.DateInputWidget(),
        )
    body = schema.SchemaNode(
        schema.String(),
        title = 'Body',
        description = deferred_body_description,
        validator = deferred_body_validator,
        widget = deferred_body_widget,
        )
    category = schema.SchemaNode(
        schema.String(),
        title = 'Category',
        description = 'Blog post category',
        validator = deferred_category_validator,
        widget = deferred_category_widget,
        )

def remove_date(node, kw):
    if kw.get('nodates'): del node['date']

class TestDeferredFunction(unittest.TestCase):
    def test_it(self):
        schema = BlogPostSchema(after_bind=remove_date).bind(
            max_date = datetime.date.max,
            max_bodylen = 5000,
            body_type = 'richtext',
            default_date = datetime.date.today(),
            categories = [('one', 'One'), ('two', 'Two')]
            )
        self.assertEqual(schema['date'].missing, datetime.date.today())
        self.assertEqual(schema['date'].validator.max, datetime.date.max)
        self.assertEqual(schema['date'].widget.__class__.__name__,
                         'DateInputWidget')
        self.assertEqual(schema['body'].description,
                         'Blog post body (no longer than 5000 bytes)')
        self.assertEqual(schema['body'].validator.max, 5000)
        self.assertEqual(schema['body'].widget.__class__.__name__,
                         'RichTextWidget')
        self.assertEqual(schema['category'].validator.choices, ['one', 'two'])
        self.assertEqual(schema['category'].widget.values,
                         [('one', 'One'), ('two', 'Two')])
        
        
        
        
