import unittest

def invalid_exc(func, *arg, **kw):
    from nive.components.reform.schema import Invalid
    try:
        func(*arg, **kw)
    except Invalid, e:
        return e
    else:
        raise AssertionError('Invalid not raised') # pragma: no cover

class TestInvalid(unittest.TestCase):
    def _makeOne(self, node, msg=None, val=None):
        from nive.components.reform.schema import Invalid
        exc = Invalid(node, msg, val)
        return exc

    def test_ctor(self):
        exc = self._makeOne(None, 'msg', 'val')
        self.assertEqual(exc.node, None)
        self.assertEqual(exc.msg, 'msg')
        self.assertEqual(exc.value, 'val')
        self.assertEqual(exc.children, [])

    def test_add(self):
        exc = self._makeOne(None, 'msg')
        other = Dummy()
        exc.add(other)
        self.failIf(hasattr(other, 'positional'))
        self.assertEqual(exc.children, [other])

    def test_add_positional(self):
        from nive.components.reform.schema import Positional
        p = Positional()
        node = DummySchemaNode(p)
        exc = self._makeOne(node, 'msg')
        other = Dummy()
        exc.add(other)
        self.assertEqual(other.positional, True)
        self.assertEqual(exc.children, [other])

    def test__keyname_no_parent(self):
        node = DummySchemaNode(None, name='name')
        exc = self._makeOne(None, '')
        exc.node = node
        self.assertEqual(exc._keyname(), 'name')

    def test__keyname_positional(self):
        exc = self._makeOne(None, '')
        exc.positional = True
        exc.pos = 2
        self.assertEqual(exc._keyname(), '2')

    def test__keyname_nonpositional_parent(self):
        parent = Dummy()
        parent.node = DummySchemaNode(None)
        exc = self._makeOne(None, 'me')
        exc.parent = parent
        exc.pos = 2
        exc.node = DummySchemaNode(None, name='name')
        self.assertEqual(exc._keyname(), 'name')

    def test_paths(self):
        exc1 = self._makeOne(None, 'exc1')
        exc2 = self._makeOne(None, 'exc2')
        exc3 = self._makeOne(None, 'exc3')
        exc4 = self._makeOne(None, 'exc4')
        exc1.add(exc2)
        exc2.add(exc3)
        exc1.add(exc4)
        paths = list(exc1.paths())
        self.assertEqual(paths, [(exc1, exc2, exc3), (exc1, exc4)])

    def test_asdict(self):
        from nive.components.reform.schema import Positional
        node1 = DummySchemaNode(None, 'node1')
        node2 = DummySchemaNode(Positional(), 'node2')
        node3 = DummySchemaNode(Positional(), 'node3')
        node4 = DummySchemaNode(Positional(), 'node4')
        exc1 = self._makeOne(node1, 'exc1')
        exc1.pos = 1
        exc2 = self._makeOne(node2, 'exc2')
        exc3 = self._makeOne(node3, 'exc3')
        exc4 = self._makeOne(node4, 'exc4')
        exc1.add(exc2, 2)
        exc2.add(exc3, 3)
        exc1.add(exc4, 4)
        d = exc1.asdict()
        self.assertEqual(d, {'node1.node2.3': 'exc1; exc2; exc3',
                             'node1.node4': 'exc1; exc4'})

    def test___str__(self):
        from nive.components.reform.schema import Positional
        node1 = DummySchemaNode(None, 'node1')
        node2 = DummySchemaNode(Positional(), 'node2')
        node3 = DummySchemaNode(Positional(), 'node3')
        node4 = DummySchemaNode(Positional(), 'node4')
        exc1 = self._makeOne(node1, 'exc1')
        exc1.pos = 1
        exc2 = self._makeOne(node2, 'exc2')
        exc3 = self._makeOne(node3, 'exc3')
        exc4 = self._makeOne(node4, 'exc4')
        exc1.add(exc2, 2)
        exc2.add(exc3, 3)
        exc1.add(exc4, 4)
        result = str(exc1)
        self.assertEqual(
            result,
            "{'node1.node2.3': 'exc1; exc2; exc3', 'node1.node4': 'exc1; exc4'}"
            )

    def test___setitem__fails(self):
        node = DummySchemaNode(None)
        exc = self._makeOne(node, 'msg')
        self.assertRaises(KeyError, exc.__setitem__, 'notfound', 'msg')

    def test___setitem__succeeds(self):
        node = DummySchemaNode(None)
        child = DummySchemaNode(None)
        child.name = 'found'
        node.children = [child]
        exc = self._makeOne(node, 'msg')
        exc['found'] = 'msg2'
        self.assertEqual(len(exc.children), 1)
        childexc = exc.children[0]
        self.assertEqual(childexc.pos, 0)
        self.assertEqual(childexc.node.name, 'found')

    def test_messages_msg_iterable(self):
        node = DummySchemaNode(None)
        exc = self._makeOne(node, [123, 456])
        self.assertEqual(exc.messages(), [123, 456])

    def test_messages_msg_not_iterable(self):
        node = DummySchemaNode(None)
        exc = self._makeOne(node, 'msg')
        self.assertEqual(exc.messages(), ['msg'])

class TestAll(unittest.TestCase):
    def _makeOne(self, validators):
        from nive.components.reform.schema import All
        return All(*validators)

    def test_success(self):
        validator1 = DummyValidator()
        validator2 = DummyValidator()
        validator = self._makeOne([validator1, validator2])
        self.assertEqual(validator(None, None), None)

    def test_failure(self):
        validator1 = DummyValidator('msg1')
        validator2 = DummyValidator('msg2')
        validator = self._makeOne([validator1, validator2])
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg, ['msg1', 'msg2'])

class TestFunction(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from nive.components.reform.schema import Function
        return Function(*arg, **kw)

    def test_success_function_returns_True(self):
        validator = self._makeOne(lambda x: True)
        self.assertEqual(validator(None, None), None)

    def test_fail_function_returns_empty_string(self):
        validator = self._makeOne(lambda x: '')
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg, 'Invalid value')

    def test_fail_function_returns_False(self):
        validator = self._makeOne(lambda x: False)
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg, 'Invalid value')

    def test_fail_function_returns_string(self):
        validator = self._makeOne(lambda x: 'fail')
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg, 'fail')

    def test_propagation(self):
        validator = self._makeOne(lambda x: 'a' in x, 'msg')
        self.assertRaises(TypeError, validator, None, None)

class TestRange(unittest.TestCase):
    def _makeOne(self, **kw):
        from nive.components.reform.schema import Range
        return Range(**kw)

    def test_success_no_bounds(self):
        validator = self._makeOne()
        self.assertEqual(validator(None, 1), None)

    def test_success_upper_bound_only(self):
        validator = self._makeOne(max=1)
        self.assertEqual(validator(None, -1), None)

    def test_success_minimum_bound_only(self):
        validator = self._makeOne(min=0)
        self.assertEqual(validator(None, 1), None)

    def test_success_min_and_max(self):
        validator = self._makeOne(min=1, max=1)
        self.assertEqual(validator(None, 1), None)

    def test_min_failure(self):
        validator = self._makeOne(min=1)
        e = invalid_exc(validator, None, 0)
        self.assertEqual(e.msg.interpolate(), '0 is less than minimum value 1')

    def test_min_failure_msg_override(self):
        validator = self._makeOne(min=1, min_err='wrong')
        e = invalid_exc(validator, None, 0)
        self.assertEqual(e.msg, 'wrong')

    def test_max_failure(self):
        validator = self._makeOne(max=1)
        e = invalid_exc(validator, None, 2)
        self.assertEqual(e.msg.interpolate(),
                         '2 is greater than maximum value 1')

    def test_max_failure_msg_override(self):
        validator = self._makeOne(max=1, max_err='wrong')
        e = invalid_exc(validator, None, 2)
        self.assertEqual(e.msg, 'wrong')

class TestRegex(unittest.TestCase):
    def _makeOne(self, pattern):
        from nive.components.reform.schema import Regex
        return Regex(pattern)

    def test_valid_regex(self):
        self.assertEqual(self._makeOne('a')(None, 'a'), None)
        self.assertEqual(self._makeOne('[0-9]+')(None, '1111'), None)
        self.assertEqual(self._makeOne('')(None, ''), None)
        self.assertEqual(self._makeOne('.*')(None, ''), None)

    def test_invalid_regexs(self):
        from nive.components.reform.schema import Invalid
        self.assertRaises(Invalid, self._makeOne('[0-9]+'), None, 'a')
        self.assertRaises(Invalid, self._makeOne('a{2,4}'), None, 'ba')

    def test_regex_not_string(self):
        from nive.components.reform.schema import Invalid
        import re
        regex = re.compile('[0-9]+')
        self.assertEqual(self._makeOne(regex)(None, '01'), None)
        self.assertRaises(Invalid, self._makeOne(regex), None, 't')


class TestEmail(unittest.TestCase):
    def _makeOne(self):
        from nive.components.reform.schema import Email
        return Email()

    def test_valid_emails(self):
        validator = self._makeOne()
        self.assertEqual(validator(None, 'me@here.com'), None)
        self.assertEqual(validator(None, 'me1@here1.com'), None)
        self.assertEqual(validator(None, 'name@here1.us'), None)
        self.assertEqual(validator(None, 'name@here1.info'), None)
        self.assertEqual(validator(None, 'foo@bar.baz.biz'), None)

    def test_empty_email(self):
        validator = self._makeOne()
        e = invalid_exc(validator, None, '')
        self.assertEqual(e.msg, 'Invalid email address')

    def test_invalid_emails(self):
        validator = self._makeOne()
        from nive.components.reform.schema import Invalid
        self.assertRaises(Invalid, validator, None, 'me@here.')
        self.assertRaises(Invalid, validator, None, 'name@here.comcom')
        self.assertRaises(Invalid, validator, None, '@here.us')
        self.assertRaises(Invalid, validator, None, '(name)@here.info')

class TestLength(unittest.TestCase):
    def _makeOne(self, min=None, max=None):
        from nive.components.reform.schema import Length
        return Length(min=min, max=max)

    def test_success_no_bounds(self):
        validator = self._makeOne()
        self.assertEqual(validator(None, ''), None)

    def test_success_upper_bound_only(self):
        validator = self._makeOne(max=1)
        self.assertEqual(validator(None, 'a'), None)

    def test_success_minimum_bound_only(self):
        validator = self._makeOne(min=0)
        self.assertEqual(validator(None, ''), None)

    def test_success_min_and_max(self):
        validator = self._makeOne(min=1, max=1)
        self.assertEqual(validator(None, 'a'), None)

    def test_min_failure(self):
        validator = self._makeOne(min=1)
        e = invalid_exc(validator, None, '')
        self.assertEqual(e.msg.interpolate(), 'Shorter than minimum length 1')

    def test_max_failure(self):
        validator = self._makeOne(max=1)
        e = invalid_exc(validator, None, 'ab')
        self.assertEqual(e.msg.interpolate(), 'Longer than maximum length 1')

class TestOneOf(unittest.TestCase):
    def _makeOne(self, values):
        from nive.components.reform.schema import OneOf
        return OneOf(values)

    def test_success(self):
        validator = self._makeOne([1])
        self.assertEqual(validator(None, 1), None)

    def test_failure(self):
        validator = self._makeOne([1, 2])
        e = invalid_exc(validator, None, None)
        self.assertEqual(e.msg.interpolate(), '"None" is not one of 1, 2')

class TestSchemaType(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from nive.components.reform.schema import SchemaType
        return SchemaType(*arg, **kw)

    def test_flatten(self):
        node = DummySchemaNode(None, name='node')
        typ = self._makeOne()
        result = typ.flatten(node, 'appstruct')
        self.assertEqual(result, {'node':'appstruct'})

    def test_flatten_listitem(self):
        node = DummySchemaNode(None, name='node')
        typ = self._makeOne()
        result = typ.flatten(node, 'appstruct', listitem=True)
        self.assertEqual(result, {'':'appstruct'})

    def test_unflatten(self):
        node = DummySchemaNode(None, name='node')
        typ = self._makeOne()
        result = typ.unflatten(node, ['node'], {'node': 'appstruct'})
        self.assertEqual(result, 'appstruct')

    def test_set_value(self):
        typ = self._makeOne()
        self.assertRaises(
            AssertionError, typ.set_value, None, None, None, None)

    def test_get_value(self):
        typ = self._makeOne()
        self.assertRaises(
            AssertionError, typ.get_value, None, None, None)

class TestMapping(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from nive.components.reform.schema import Mapping
        return Mapping(*arg, **kw)

    def test_ctor_bad_unknown(self):
        self.assertRaises(ValueError, self._makeOne, 'badarg')

    def test_ctor_good_unknown(self):
        try:
            self._makeOne('ignore')
            self._makeOne('raise')
            self._makeOne('preserve')
        except ValueError, e: # pragma: no cover
            raise AssertionError(e)

    def test_deserialize_not_a_mapping(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, None)
        self.failUnless(
            e.msg.interpolate().startswith('"None" is not a mapping type'))

    def test_deserialize_null(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, reform.schema.null)
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_no_subnodes(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, {})
        self.assertEqual(result, {})

    def test_deserialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.deserialize(node, {'a':1})
        self.assertEqual(result, {'a':1})

    def test_deserialize_unknown_raise(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne(unknown='raise')
        e = invalid_exc(typ.deserialize, node, {'a':1, 'b':2})
        self.assertEqual(e.msg.interpolate(),
                         "Unrecognized keys in mapping: \"{'b': 2}\"")


    def test_deserialize_unknown_preserve(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne(unknown='preserve')
        result = typ.deserialize(node, {'a':1, 'b':2})
        self.assertEqual(result, {'a':1, 'b':2})

    def test_deserialize_subnodes_raise(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a', exc='Wrong 2'),
            DummySchemaNode(None, name='b', exc='Wrong 2'),
            ]
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, {'a':1, 'b':2})
        self.assertEqual(e.msg, None)
        self.assertEqual(len(e.children), 2)

    def test_deserialize_subnode_missing_default(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a'),
            DummySchemaNode(None, name='b', default='abc'),
            ]
        typ = self._makeOne()
        result = typ.deserialize(node, {'a':1})
        self.assertEqual(result, {'a':1, 'b':reform.schema.null})

    def test_serialize_null(self):
        from nive.components import reform
        val = reform.schema.null
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, {})

    def test_serialize_not_a_mapping(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, None)
        self.failUnless(
            e.msg.interpolate().startswith('"None" is not a mapping type'))

    def test_serialize_no_subnodes(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, {})
        self.assertEqual(result, {})

    def test_serialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.serialize(node, {'a':1})
        self.assertEqual(result, {'a':1})

    def test_serialize_with_unknown(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a'),
            ]
        typ = self._makeOne()
        result = typ.serialize(node, {'a':1, 'b':2})
        self.assertEqual(result, {'a':1})

    def test_serialize_value_is_null(self):
        node = DummySchemaNode(None)
        from nive.components.reform.schema import null
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.serialize(node, null)
        self.assertEqual(result, {'a':null})

    def test_flatten(self):
        node = DummySchemaNode(None, name='node')
        int1 = DummyType()
        int2 = DummyType()
        node.children = [
            DummySchemaNode(int1, name='a'),
            DummySchemaNode(int2, name='b'),
            ]
        typ = self._makeOne()
        result = typ.flatten(node, {'a':1, 'b':2})
        self.assertEqual(result, {'node.appstruct': 2})

    def test_flatten_listitem(self):
        node = DummySchemaNode(None, name='node')
        int1 = DummyType()
        int2 = DummyType()
        node.children = [
            DummySchemaNode(int1, name='a'),
            DummySchemaNode(int2, name='b'),
            ]
        typ = self._makeOne()
        result = typ.flatten(node, {'a':1, 'b':2}, listitem=True)
        self.assertEqual(result, {'appstruct': 2})

    def test_unflatten(self):
        node = DummySchemaNode(None, name='node')
        int1 = DummyType()
        int2 = DummyType()
        node.children = [
            DummySchemaNode(int1, name='a'),
            DummySchemaNode(int2, name='b'),
            ]
        typ = self._makeOne()
        result = typ.unflatten(node,
            ['node', 'node.a', 'node.b'],
            {'node': {'a':1, 'b':2}, 'node.a':1, 'node.b':2})
        self.assertEqual(result, {'a': 1, 'b': 2})

    def test_unflatten_nested(self):
        node = DummySchemaNode(None, name='node')
        inttype = DummyType()
        one = DummySchemaNode(self._makeOne(), name='one')
        one.children = [
            DummySchemaNode(inttype, name='a'),
            DummySchemaNode(inttype, name='b'),
        ]
        two = DummySchemaNode(self._makeOne(), name='two')
        two.children = [
            DummySchemaNode(inttype, name='c'),
            DummySchemaNode(inttype, name='d'),
        ]
        node.children = [one, two]
        typ = self._makeOne()
        result = typ.unflatten(
            node, ['node', 'node.one', 'node.one.a', 'node.one.b',
                   'node.two', 'node.two.c', 'node.two.d'],
            {'node': {'one': {'a': 1, 'b': 2}, 'two': {'c': 3, 'd': 4}},
             'node.one': {'a': 1, 'b': 2},
             'node.two': {'c': 3, 'd': 4},
             'node.one.a': 1,
             'node.one.b': 2,
             'node.two.c': 3,
             'node.two.d': 4,})
        self.assertEqual(result, {
            'one': {'a': 1, 'b': 2}, 'two': {'c': 3, 'd': 4}})

    def test_set_value(self):
        typ = self._makeOne()
        node1 = DummySchemaNode(typ, name='node1')
        node2 = DummySchemaNode(typ, name='node2')
        node1.children = [node2]
        appstruct = {'node2': {'foo': 'foo', 'baz': 'baz'}}
        typ.set_value(node1, appstruct, 'node2.foo', 'bar')
        self.assertEqual(appstruct, {'node2': {'foo': 'bar', 'baz': 'baz'}})

    def test_get_value(self):
        typ = self._makeOne()
        node1 = DummySchemaNode(typ, name='node1')
        node2 = DummySchemaNode(typ, name='node2')
        node1.children = [node2]
        appstruct = {'node2': {'foo': 'bar', 'baz': 'baz'}}
        self.assertEqual(typ.get_value(node1, appstruct, 'node2'),
                         {'foo': 'bar', 'baz': 'baz'})
        self.assertEqual(typ.get_value(node1, appstruct, 'node2.foo'), 'bar')


class TestTuple(unittest.TestCase):
    def _makeOne(self):
        from nive.components.reform.schema import Tuple
        return Tuple()

    def test_deserialize_not_iterable(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, None)
        self.assertEqual(
            e.msg.interpolate(),
            '"None" is not iterable')
        self.assertEqual(e.node, node)

    def test_deserialize_no_subnodes(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, ())
        self.assertEqual(result, ())

    def test_deserialize_null(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, reform.schema.null)
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.deserialize(node, ('a',))
        self.assertEqual(result, ('a',))

    def test_deserialize_toobig(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, ('a','b'))
        self.assertEqual(e.msg.interpolate(),
      "\"('a', 'b')\" has an incorrect number of elements (expected 1, was 2)")

    def test_deserialize_toosmall(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, ())
        self.assertEqual(e.msg.interpolate(),
           '"()" has an incorrect number of elements (expected 1, was 0)')

    def test_deserialize_subnodes_raise(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a', exc='Wrong 2'),
            DummySchemaNode(None, name='b', exc='Wrong 2'),
            ]
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, ('1', '2'))
        self.assertEqual(e.msg, None)
        self.assertEqual(len(e.children), 2)

    def test_serialize_null(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, reform.schema.null)
        self.assertEqual(result, reform.schema.null)

    def test_serialize_no_subnodes(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, ())
        self.assertEqual(result, ())

    def test_serialize_ok(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        result = typ.serialize(node, ('a',))
        self.assertEqual(result, ('a',))

    def test_serialize_toobig(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, ('a','b'))
        self.assertEqual(e.msg.interpolate(),
     "\"('a', 'b')\" has an incorrect number of elements (expected 1, was 2)")

    def test_serialize_toosmall(self):
        node = DummySchemaNode(None)
        node.children = [DummySchemaNode(None, name='a')]
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, ())
        self.assertEqual(e.msg.interpolate(),
           '"()" has an incorrect number of elements (expected 1, was 0)'
           )

    def test_serialize_subnodes_raise(self):
        node = DummySchemaNode(None)
        node.children = [
            DummySchemaNode(None, name='a', exc='Wrong 2'),
            DummySchemaNode(None, name='b', exc='Wrong 2'),
            ]
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, ('1', '2'))
        self.assertEqual(e.msg, None)
        self.assertEqual(len(e.children), 2)

    def test_flatten(self):
        node = DummySchemaNode(None, name='node')
        int1 = DummyType()
        int2 = DummyType()
        node.children = [
            DummySchemaNode(int1, name='a'),
            DummySchemaNode(int2, name='b'),
            ]
        typ = self._makeOne()
        result = typ.flatten(node, (1, 2))
        self.assertEqual(result, {'node.appstruct': 2})

    def test_flatten_listitem(self):
        node = DummySchemaNode(None, name='node')
        int1 = DummyType()
        int2 = DummyType()
        node.children = [
            DummySchemaNode(int1, name='a'),
            DummySchemaNode(int2, name='b'),
            ]
        typ = self._makeOne()
        result = typ.flatten(node, (1, 2), listitem=True)
        self.assertEqual(result, {'appstruct': 2})

    def test_unflatten(self):
        node = DummySchemaNode(None, name='node')
        int1 = DummyType()
        int2 = DummyType()
        node.children = [
            DummySchemaNode(int1, name='a'),
            DummySchemaNode(int2, name='b'),
            ]
        typ = self._makeOne()
        result = typ.unflatten(node, ['node', 'node.a', 'node.b'],
                               {'node': (1, 2), 'node.a': 1, 'node.b': 2})
        self.assertEqual(result, (1, 2))

    def test_set_value(self):
        typ = self._makeOne()
        node = DummySchemaNode(typ, name='node')
        node.children = [
            DummySchemaNode(typ, name='foo'),
            DummySchemaNode(typ, name='bar')
        ]
        node['foo'].children = [
            DummySchemaNode(None, name='a'),
            DummySchemaNode(None, name='b'),
        ]
        node['bar'].children = [
            DummySchemaNode(None, name='c'),
            DummySchemaNode(None, name='d'),
        ]
        appstruct = ((1, 2), (3, 4))
        result = typ.set_value(node, appstruct, 'bar.c', 34)
        self.assertEqual(result, ((1, 2), (34, 4)))

    def test_set_value_bad_path(self):
        typ = self._makeOne()
        node = DummySchemaNode(typ, name='node')
        node.children = [
            DummySchemaNode(None, name='foo'),
            DummySchemaNode(None, name='bar')
        ]
        self.assertRaises(
            KeyError, typ.set_value, node, (1, 2), 'foobar', 34)

    def test_get_value(self):
        typ = self._makeOne()
        node = DummySchemaNode(typ, name='node')
        node.children = [
            DummySchemaNode(typ, name='foo'),
            DummySchemaNode(typ, name='bar')
        ]
        node['foo'].children = [
            DummySchemaNode(None, name='a'),
            DummySchemaNode(None, name='b'),
        ]
        node['bar'].children = [
            DummySchemaNode(None, name='c'),
            DummySchemaNode(None, name='d'),
        ]
        appstruct = ((1, 2), (3, 4))
        self.assertEqual(typ.get_value(node, appstruct, 'foo'), (1, 2))
        self.assertEqual(typ.get_value(node, appstruct, 'foo.b'), 2)

    def test_get_value_bad_path(self):
        typ = self._makeOne()
        node = DummySchemaNode(typ, name='node')
        node.children = [
            DummySchemaNode(None, name='foo'),
            DummySchemaNode(None, name='bar')
        ]
        self.assertRaises(
            KeyError, typ.get_value, node, (1, 2), 'foobar')

#<removed class TestSequence(unittest.TestCase):

class TestString(unittest.TestCase):
    def _makeOne(self, encoding=None):
        from nive.components.reform.schema import String
        return String(encoding)

    def test_alias(self):
        from nive.components.reform.schema import Str
        from nive.components.reform.schema import String
        self.assertEqual(Str, String)

    def test_deserialize_emptystring(self):
        from nive.components.reform.schema import null
        node = DummySchemaNode(None)
        typ = self._makeOne(None)
        result = typ.deserialize(node, '')
        self.assertEqual(result, '')

    def test_deserialize_uncooperative(self):
        val = Uncooperative()
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.failUnless(e.msg)

    def test_deserialize_unicode_from_None(self):
        uni = u'\xf8'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, uni)
        self.assertEqual(result, uni)

    def test_deserialize_nonunicode_from_None(self):
        value = object()
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, value)
        self.assertEqual(result, unicode(value))

    def test_deserialize_from_utf8(self):
        uni = u'\xf8'
        utf8 = uni.encode('utf-8')
        node = DummySchemaNode(None)
        typ = self._makeOne('utf-8')
        result = typ.deserialize(node, utf8)
        self.assertEqual(result, uni)

    def test_deserialize_from_utf16(self):
        uni = u'\xf8'
        utf16 = uni.encode('utf-16')
        node = DummySchemaNode(None)
        typ = self._makeOne('utf-16')
        result = typ.deserialize(node, utf16)
        self.assertEqual(result, uni)

    def test_serialize_null(self):
        from nive.components.reform.schema import null
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, null)
        self.assertEqual(result, null)

    def test_serialize_uncooperative(self):
        val = Uncooperative()
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, val)
        self.failUnless(e.msg)

    def test_serialize_nonunicode_to_None(self):
        value = object()
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, value)
        self.assertEqual(result, unicode(value))

    def test_serialize_unicode_to_None(self):
        value = u'abc'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, value)
        self.assertEqual(result, value)

    def test_serialize_to_utf8(self):
        uni = u'\xf8'
        utf8 = uni.encode('utf-8')
        node = DummySchemaNode(None)
        typ = self._makeOne('utf-8')
        result = typ.serialize(node, uni)
        self.assertEqual(result, utf8)

    def test_serialize_to_utf16(self):
        uni = u'\xf8'
        utf16 = uni.encode('utf-16')
        node = DummySchemaNode(None)
        typ = self._makeOne('utf-16')
        result = typ.serialize(node, uni)
        self.assertEqual(result, utf16)

    def test_serialize_string_with_high_unresolveable_high_order_chars(self):
        not_utf8 = '\xff\xfe\xf8\x00'
        node = DummySchemaNode(None)
        typ = self._makeOne('utf-8')
        e = invalid_exc(typ.serialize, node, not_utf8)
        self.failUnless('cannot be serialized' in e.msg)

class TestInteger(unittest.TestCase):
    def _makeOne(self):
        from nive.components.reform.schema import Integer
        return Integer()

    def test_alias(self):
        from nive.components.reform.schema import Int
        from nive.components.reform.schema import Integer
        self.assertEqual(Int, Integer)

    def test_serialize_null(self):
        from nive.components import reform
        val = reform.schema.null
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_serialize_emptystring(self):
        from nive.components import reform
        val = ''
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.failUnless(e.msg)

    def test_deserialize_ok(self):
        val = '1'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, 1)

    def test_serialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, val)
        self.failUnless(e.msg)

    def test_serialize_ok(self):
        val = 1
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, '1')

class TestFloat(unittest.TestCase):
    def _makeOne(self):
        from nive.components.reform.schema import Float
        return Float()

    def test_serialize_null(self):
        from nive.components import reform
        val = reform.schema.null
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_serialize_emptystring(self):
        from nive.components import reform
        val = ''
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.failUnless(e.msg)

    def test_deserialize_ok(self):
        val = '1.0'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, 1.0)

    def test_serialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, val)
        self.failUnless(e.msg)

    def test_serialize_ok(self):
        val = 1.0
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, '1.0')

class TestDecimal(unittest.TestCase):
    def _makeOne(self):
        from nive.components.reform.schema import Decimal
        return Decimal()

    def test_serialize_null(self):
        from nive.components import reform
        val = reform.schema.null
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_serialize_emptystring(self):
        from nive.components import reform
        val = ''
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, val)
        self.failUnless(e.msg)

    def test_deserialize_ok(self):
        import decimal
        val = '1.0'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, val)
        self.assertEqual(result, decimal.Decimal('1.0'))

    def test_serialize_fails(self):
        val = 'P'
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, node, val)
        self.failUnless(e.msg)

    def test_serialize_ok(self):
        val = 1.0
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, '1.0')

class TestBoolean(unittest.TestCase):
    def _makeOne(self):
        from nive.components.reform.schema import Boolean
        return Boolean()

    def test_alias(self):
        from nive.components.reform.schema import Bool
        from nive.components.reform.schema import Boolean
        self.assertEqual(Bool, Boolean)

    def test_serialize_null(self):
        from nive.components import reform
        val = reform.schema.null
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_deserialize(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        self.assertEqual(typ.deserialize(node, 'false'), False)
        self.assertEqual(typ.deserialize(node, 'FALSE'), False)
        self.assertEqual(typ.deserialize(node, '0'), False)
        self.assertEqual(typ.deserialize(node, 'true'), True)
        self.assertEqual(typ.deserialize(node, 'other'), True)

    def test_deserialize_unstringable(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        e = invalid_exc(typ.deserialize, node, Uncooperative())
        self.failUnless(e.msg.endswith('not a string'))

    def test_deserialize_null(self):
        from nive.components import reform
        typ = self._makeOne()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, reform.schema.null)
        self.assertEqual(result, reform.schema.null)

    def test_serialize(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        self.assertEqual(typ.serialize(node, 1), 'true')
        self.assertEqual(typ.serialize(node, True), 'true')
        self.assertEqual(typ.serialize(node, None), 'false')
        self.assertEqual(typ.serialize(node, False), 'false')

#<removed class TestGlobalObject(unittest.TestCase):


class TestDateTime(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from nive.components.reform.schema import DateTime
        return DateTime(*arg, **kw)

    def _dt(self):
        import datetime
        return datetime.datetime(2010, 4, 26, 10, 48)

    def _today(self):
        import datetime
        return datetime.date.today()

    def test_ctor_default_tzinfo_None(self):
        import iso8601
        typ = self._makeOne()
        self.assertEqual(typ.default_tzinfo.__class__, iso8601.iso8601.Utc)

    def test_ctor_default_tzinfo_non_None(self):
        import iso8601
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        typ = self._makeOne(default_tzinfo=tzinfo)
        self.assertEqual(typ.default_tzinfo, tzinfo)

    def test_serialize_null(self):
        from nive.components import reform
        val = reform.schema.null
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_serialize_with_garbage(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        e = invalid_exc(typ.serialize, node, 'garbage')
        self.assertEqual(e.msg.interpolate(),
                         '"garbage" is not a datetime object')

    def test_serialize_with_date(self):
        import datetime
        typ = self._makeOne()
        date = self._today()
        node = DummySchemaNode(None)
        result = typ.serialize(node, date)
        expected = datetime.datetime.combine(date, datetime.time())
        expected = expected.replace(tzinfo=typ.default_tzinfo).isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_naive_datetime(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        dt = self._dt()
        result = typ.serialize(node, dt)
        expected = dt.replace(tzinfo=typ.default_tzinfo).isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_none_tzinfo_naive_datetime(self):
        typ = self._makeOne(default_tzinfo=None)
        node = DummySchemaNode(None)
        dt = self._dt()
        result = typ.serialize(node, dt)
        self.assertEqual(result, dt.isoformat())

    def test_serialize_with_tzware_datetime(self):
        import iso8601
        typ = self._makeOne()
        dt = self._dt()
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        dt = dt.replace(tzinfo=tzinfo)
        node = DummySchemaNode(None)
        result = typ.serialize(node, dt)
        expected = dt.isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_datetime_str(self):
        import iso8601
        typ = self._makeOne()
        node = DummySchemaNode(None)
        dt = "2012-01-01T13:34:00"
        result = typ.serialize(node, dt)
        expected = iso8601.parse_date(dt).isoformat()
        self.assertEqual(result, expected)

    def test_deserialize_date(self):
        import datetime
        import iso8601
        date = self._today()
        typ = self._makeOne()
        formatted = date.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, formatted)
        expected = datetime.datetime.combine(result, datetime.time())
        tzinfo = iso8601.iso8601.Utc()
        expected = expected.replace(tzinfo=tzinfo)
        self.assertEqual(result.isoformat(), expected.isoformat())

    def test_deserialize_invalid_ParseError(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, 'garbage')
        self.failUnless('Invalid' in e.msg)

    def test_deserialize_null(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, reform.schema.null)
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_empty(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, '')
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_success(self):
        import iso8601
        typ = self._makeOne()
        dt = self._dt()
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        dt = dt.replace(tzinfo=tzinfo)
        iso = dt.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, iso)
        self.assertEqual(result.isoformat(), iso)

    def test_deserialize_naive_with_default_tzinfo(self):
        import iso8601
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        typ = self._makeOne(default_tzinfo=tzinfo)
        dt = self._dt()
        dt_with_tz = dt.replace(tzinfo=tzinfo)
        iso = dt.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, iso)
        self.assertEqual(result.isoformat(), dt_with_tz.isoformat())

    def test_deserialize_none_tzinfo(self):
        typ = self._makeOne(default_tzinfo=None)
        dt = self._dt()
        iso = dt.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, iso)
        self.assertEqual(result.isoformat(), dt.isoformat())

class TestDate(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from nive.components.reform.schema import Date
        return Date(*arg, **kw)

    def _dt(self):
        import datetime
        return datetime.datetime(2010, 4, 26, 10, 48)

    def _today(self):
        import datetime
        return datetime.date.today()

    def test_serialize_null(self):
        from nive.components import reform
        val = reform.schema.null
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_serialize_with_garbage(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        e = invalid_exc(typ.serialize, node, 'garbage')
        self.assertEqual(e.msg.interpolate(), '"garbage" is not a date object')

    def test_serialize_with_date(self):
        typ = self._makeOne()
        date = self._today()
        node = DummySchemaNode(None)
        result = typ.serialize(node, date)
        expected = date.isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_datetime(self):
        typ = self._makeOne()
        dt = self._dt()
        node = DummySchemaNode(None)
        result = typ.serialize(node, dt)
        expected = dt.date().isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_date_str(self):
        import iso8601
        typ = self._makeOne()
        date = "2012-01-01"
        node = DummySchemaNode(None)
        result = typ.serialize(node, date)
        self.assertEqual(result, date)

    def test_deserialize_invalid_ParseError(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, 'garbage')
        self.failUnless('Invalid' in e.msg)

    def test_deserialize_invalid_weird(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, '10-10-10-10')
        self.failUnless('Invalid' in e.msg)

    def test_deserialize_null(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, reform.schema.null)
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_empty(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, '')
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_success_date(self):
        typ = self._makeOne()
        date = self._today()
        iso = date.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, iso)
        self.assertEqual(result.isoformat(), iso)

    def test_deserialize_success_datetime(self):
        dt = self._dt()
        typ = self._makeOne()
        iso = dt.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, iso)
        self.assertEqual(result.isoformat(), dt.date().isoformat())

class TestTime(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from nive.components.reform.schema import Time
        return Time(*arg, **kw)

    def _dt(self):
        import datetime
        return datetime.datetime(2010, 4, 26, 10, 48)

    def _now(self):
        import datetime
        return datetime.datetime.now().time()

    def test_serialize_null(self):
        from nive.components import reform
        val = reform.schema.null
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.serialize(node, val)
        self.assertEqual(result, reform.schema.null)

    def test_serialize_with_garbage(self):
        typ = self._makeOne()
        node = DummySchemaNode(None)
        e = invalid_exc(typ.serialize, node, 'garbage')
        self.assertEqual(e.msg.interpolate(), '"garbage" is not a time object')

    def test_serialize_with_time(self):
        typ = self._makeOne()
        time = self._now()
        node = DummySchemaNode(None)
        result = typ.serialize(node, time)
        expected = time.isoformat().split('.')[0]
        self.assertEqual(result, expected)

    def test_serialize_with_datetime(self):
        typ = self._makeOne()
        dt = self._dt()
        node = DummySchemaNode(None)
        result = typ.serialize(node, dt)
        expected = dt.time().isoformat().split('.')[0]
        self.assertEqual(result, expected)

    def test_serialize_with_time_str(self):
        typ = self._makeOne()
        time = "12:34:00"
        node = DummySchemaNode(None)
        result = typ.serialize(node, time)
        self.assertEqual(result, time)

    def test_deserialize_invalid_ParseError(self):
        node = DummySchemaNode(None)
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, 'garbage')
        self.failUnless('Invalid' in e.msg)

    def test_deserialize_three_digit_string(self):
        import datetime
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, '11:00:11')
        self.assertEqual(result, datetime.time(11, 0, 11))

    def test_deserialize_two_digit_string(self):
        import datetime
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, '11:00')
        self.assertEqual(result, datetime.time(11, 0))

    def test_deserialize_null(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, reform.schema.null)
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_empty(self):
        from nive.components import reform
        node = DummySchemaNode(None)
        typ = self._makeOne()
        result = typ.deserialize(node, '')
        self.assertEqual(result, reform.schema.null)

    def test_deserialize_missing_seconds(self):
        import datetime
        typ = self._makeOne()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, '10:12')
        self.assertEqual(result, datetime.time(10, 12))

    def test_deserialize_success_time(self):
        import datetime
        typ = self._makeOne()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, '10:12:13')
        self.assertEqual(result, datetime.time(10, 12, 13))

    def test_deserialize_success_datetime(self):
        dt = self._dt()
        typ = self._makeOne()
        iso = dt.isoformat()
        node = DummySchemaNode(None)
        result = typ.deserialize(node, iso)
        self.assertEqual(result.isoformat(),
                dt.time().isoformat().split('.')[0])

class TestSchemaNode(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from nive.components.reform.schema import SchemaNode
        return SchemaNode(*arg, **kw)

    def test_new_sets_order(self):
        node = self._makeOne(None)
        self.failUnless(hasattr(node, '_order'))

    def test_ctor_no_title(self):
        node = self._makeOne(None, 0, validator=1, default=2, name='name_a',
                             missing='missing')
        self.assertEqual(node.typ, None)
        self.assertEqual(node.children, [0])
        self.assertEqual(node.validator, 1)
        self.assertEqual(node.default, 2)
        self.assertEqual(node.missing, 'missing')
        self.assertEqual(node.name, 'name_a')
        self.assertEqual(node.title, 'Name A')

    def test_ctor_with_title(self):
        node = self._makeOne(None, 0, validator=1, default=2, name='name',
                             title='title')
        self.assertEqual(node.typ, None)
        self.assertEqual(node.children, [0])
        self.assertEqual(node.validator, 1)
        self.assertEqual(node.default, 2)
        self.assertEqual(node.name, 'name')
        self.assertEqual(node.title, 'title')

    def test_ctor_with_description(self):
        node = self._makeOne(None, 0, validator=1, default=2, name='name',
                             title='title', description='desc')
        self.assertEqual(node.description, 'desc')

    def test_ctor_with_widget(self):
        node = self._makeOne(None, 0, widget='abc')
        self.assertEqual(node.widget, 'abc')

    def test_ctor_with_preparer(self):
        node = self._makeOne(None, 0, preparer='abc')
        self.assertEqual(node.preparer, 'abc')

    def test_ctor_without_preparer(self):
        node = self._makeOne(None, 0)
        self.assertEqual(node.preparer, None)

    def test_ctor_with_unknown_kwarg(self):
        node = self._makeOne(None, 0, foo=1)
        self.assertEqual(node.foo, 1)

    def test_required_true(self):
        node = self._makeOne(None)
        self.assertEqual(node.required, True)

    def test_required_false(self):
        node = self._makeOne(None, missing=1)
        self.assertEqual(node.required, False)

    def test_required_deferred(self):
        from nive.components.reform.schema import deferred
        node = self._makeOne(None, missing=deferred('123'))
        self.assertEqual(node.required, True)

    def test_deserialize_no_validator(self):
        typ = DummyType()
        node = self._makeOne(typ)
        result = node.deserialize(1)
        self.assertEqual(result, 1)

    def test_deserialize_with_preparer(self):
        from nive.components.reform.schema import Invalid
        typ = DummyType()
        def preparer(value):
            return 'prepared_'+value
        def validator(node, value):
            if not value.startswith('prepared'):
                raise Invalid(node, 'not prepared') # pragma: no cover
        node = self._makeOne(typ,
                             preparer=preparer,
                             validator=validator)
        self.assertEqual(node.deserialize('value'),
                         'prepared_value')

    def test_deserialize_preparer_before_missing_check(self):
        from nive.components.reform.schema import null
        typ = DummyType()
        def preparer(value):
            return null
        node = self._makeOne(typ,preparer=preparer)
        e = invalid_exc(node.deserialize, 1)
        self.assertEqual(e.msg, 'Required')

    def test_deserialize_with_validator(self):
        typ = DummyType()
        validator = DummyValidator(msg='Wrong')
        node = self._makeOne(typ, validator=validator)
        e = invalid_exc(node.deserialize, 1)
        self.assertEqual(e.msg, 'Wrong')

    def test_deserialize_value_is_null_no_missing(self):
        from nive.components.reform.schema import null
        from nive.components.reform.schema import Invalid
        typ = DummyType()
        node = self._makeOne(typ)
        self.assertRaises(Invalid, node.deserialize, null)

    def test_deserialize_value_is_null_with_missing(self):
        from nive.components.reform.schema import null
        typ = DummyType()
        node = self._makeOne(typ)
        node.missing = 'abc'
        self.assertEqual(node.deserialize(null), 'abc')

    def test_deserialize_noargs_uses_default(self):
        typ = DummyType()
        node = self._makeOne(typ)
        node.missing = 'abc'
        self.assertEqual(node.deserialize(), 'abc')

    def test_deserialize_null_can_be_used_as_missing(self):
        from nive.components.reform.schema import null
        typ = DummyType()
        node = self._makeOne(typ)
        node.missing = null
        self.assertEqual(node.deserialize(null), null)

    def test_deserialize_appstruct_deferred(self):
        from nive.components.reform.schema import null
        from nive.components.reform.schema import deferred
        from nive.components.reform.schema import Invalid
        typ = DummyType()
        node = self._makeOne(typ)
        node.missing = deferred('123')
        self.assertRaises(Invalid, node.deserialize, null)

    def test_serialize(self):
        typ = DummyType()
        node = self._makeOne(typ)
        result = node.serialize(1)
        self.assertEqual(result, 1)

    def test_serialize_value_is_null_no_default(self):
        from nive.components.reform.schema import null
        typ = DummyType()
        node = self._makeOne(typ)
        result = node.serialize(null)
        self.assertEqual(result, null)

    def test_serialize_value_is_null_with_default(self):
        from nive.components.reform.schema import null
        typ = DummyType()
        node = self._makeOne(typ)
        node.default = 1
        result = node.serialize(null)
        self.assertEqual(result, 1)

    def test_serialize_noargs_uses_default(self):
        typ = DummyType()
        node = self._makeOne(typ)
        node.default = 'abc'
        self.assertEqual(node.serialize(), 'abc')

    def test_serialize_default_deferred(self):
        from nive.components.reform.schema import deferred
        from nive.components.reform.schema import null
        typ = DummyType()
        node = self._makeOne(typ)
        node.default = deferred('abc')
        self.assertEqual(node.serialize(), null)

    def test_add(self):
        node = self._makeOne(None)
        node.add(1)
        self.assertEqual(node.children, [1])

    def test_repr(self):
        node = self._makeOne(None, name='flub')
        result = repr(node)
        self.failUnless(result.startswith('<nive.components.reform.schema.SchemaNode object at '))
        self.failUnless(result.endswith("(named flub)>"))

    def test___getitem__success(self):
        node = self._makeOne(None)
        another = self._makeOne(None, name='another')
        node.add(another)
        self.assertEqual(node['another'], another)

    def test___getitem__failure(self):
        node = self._makeOne(None)
        self.assertRaises(KeyError, node.__getitem__, 'another')

    def test___delitem__success(self):
        node = self._makeOne(None)
        another = self._makeOne(None, name='another')
        node.add(another)
        del node['another']
        self.assertEqual(node.children, [])

    def test___delitem__failure(self):
        node = self._makeOne(None)
        self.assertRaises(KeyError, node.__delitem__, 'another')

    def test___setitem__success(self):
        node = self._makeOne(None)
        another = self._makeOne(None, name='another')
        node.add(another)
        andanother = self._makeOne(None, name='andanother')
        node['another'] = andanother
        self.assertEqual(node['another'], andanother)
        self.assertEqual(andanother.name, 'another')

    def test___setitem__failure(self):
        node = self._makeOne(None)
        self.assertRaises(KeyError, node.__setitem__, 'another', None)

    def test___iter__(self):
        node = self._makeOne(None)
        node.children = ['a', 'b', 'c']
        it = node.__iter__()
        self.assertEqual(list(it), ['a', 'b', 'c'])

    def test___contains__(self):
        node = self._makeOne(None)
        another = self._makeOne(None, name='another')
        node.add(another)
        self.assertEquals('another' in node, True)
        self.assertEquals('b' in node, False)

    def test_clone(self):
        inner_typ = DummyType()
        outer_typ = DummyType()
        outer_node = self._makeOne(outer_typ, name='outer')
        inner_node = self._makeOne(inner_typ, name='inner')
        outer_node.foo = 1
        inner_node.foo = 2
        outer_node.children = [inner_node]
        outer_clone = outer_node.clone()
        self.failIf(outer_clone is outer_node)
        self.assertEqual(outer_clone.typ, outer_typ)
        self.assertEqual(outer_clone.name, 'outer')
        self.assertEqual(outer_node.foo, 1)
        self.assertEqual(len(outer_clone.children), 1)
        inner_clone = outer_clone.children[0]
        self.failIf(inner_clone is inner_node)
        self.assertEqual(inner_clone.typ, inner_typ)
        self.assertEqual(inner_clone.name, 'inner')
        self.assertEqual(inner_clone.foo, 2)

    def test_bind(self):
        from nive.components.reform.schema import deferred
        inner_typ = DummyType()
        outer_typ = DummyType()
        def dv(node, kw):
            self.failUnless(node.name in ['outer', 'inner'])
            self.failUnless('a' in kw)
            return '123'
        dv = deferred(dv)
        outer_node = self._makeOne(outer_typ, name='outer', missing=dv)
        inner_node = self._makeOne(inner_typ, name='inner', validator=dv,
                                   missing=dv)
        outer_node.children = [inner_node]
        outer_clone = outer_node.bind(a=1)
        self.failIf(outer_clone is outer_node)
        self.assertEqual(outer_clone.missing, '123')
        inner_clone = outer_clone.children[0]
        self.failIf(inner_clone is inner_node)
        self.assertEqual(inner_clone.missing, '123')
        self.assertEqual(inner_clone.validator, '123')

    def test_bind_with_after_bind(self):
        from nive.components.reform.schema import deferred
        inner_typ = DummyType()
        outer_typ = DummyType()
        def dv(node, kw):
            self.failUnless(node.name in ['outer', 'inner'])
            self.failUnless('a' in kw)
            return '123'
        dv = deferred(dv)
        def remove_inner(node, kw):
            self.assertEqual(kw, {'a':1})
            del node['inner']
        outer_node = self._makeOne(outer_typ, name='outer', missing=dv,
                                   after_bind=remove_inner)
        inner_node = self._makeOne(inner_typ, name='inner', validator=dv,
                                   missing=dv)
        outer_node.children = [inner_node]
        outer_clone = outer_node.bind(a=1)
        self.failIf(outer_clone is outer_node)
        self.assertEqual(outer_clone.missing, '123')
        self.assertEqual(len(outer_clone.children), 0)
        self.assertEqual(len(outer_node.children), 1)

class TestDeferred(unittest.TestCase):
    def _makeOne(self, wrapped):
        from nive.components.reform.schema import deferred
        return deferred(wrapped)

    def test_ctor(self):
        wrapped = '123'
        inst = self._makeOne(wrapped)
        self.assertEqual(inst.wrapped, wrapped)

    def test___call__(self):
        n = object()
        k = object()
        def wrapped(node, kw):
            self.assertEqual(node, n)
            self.assertEqual(kw, k)
            return 'abc'
        inst = self._makeOne(wrapped)
        result= inst(n, k)
        self.assertEqual(result, 'abc')

class TestSchema(unittest.TestCase):
    def test_alias(self):
        from nive.components.reform.schema import Schema
        from nive.components.reform.schema import MappingSchema
        self.assertEqual(Schema, MappingSchema)

    def test_it(self):
        from nive.components import reform
        class MySchema(reform.schema.Schema):
            thing_a = reform.schema.SchemaNode(reform.schema.String())
            thing2 = reform.schema.SchemaNode(reform.schema.String(), title='bar')
        node = MySchema(default='abc')
        self.failUnless(hasattr(node, '_order'))
        self.assertEqual(node.default, 'abc')
        self.assertEqual(node.__class__, reform.schema.SchemaNode)
        self.assertEqual(node.typ.__class__, reform.schema.Mapping)
        self.assertEqual(node.children[0].typ.__class__, reform.schema.String)
        self.assertEqual(node.children[0].title, 'Thing A')
        self.assertEqual(node.children[1].title, 'bar')

    def test_title_munging(self):
        from nive.components import reform
        class MySchema(reform.schema.Schema):
            thing1 = reform.schema.SchemaNode(reform.schema.String())
            thing2 = reform.schema.SchemaNode(reform.schema.String(), title=None)
            thing3 = reform.schema.SchemaNode(reform.schema.String(), title='')
            thing4 = reform.schema.SchemaNode(reform.schema.String(), title='thing2')
        node = MySchema()
        self.assertEqual(node.children[0].title, 'Thing1')
        self.assertEqual(node.children[1].title, None)
        self.assertEqual(node.children[2].title, '')
        self.assertEqual(node.children[3].title, 'thing2')

#<removed class TestSequenceSchema(unittest.TestCase):
#<removed class TestTupleSchema(unittest.TestCase):
#<removed class TestFunctional(object):
#<removed class TestImperative(unittest.TestCase, TestFunctional):
#<removed class TestDeclarative(unittest.TestCase, TestFunctional):

class Test_null(unittest.TestCase):
    def test___nonzero__(self):
        from nive.components.reform.schema import null
        self.failIf(null)

    def test___repr__(self):
        from nive.components.reform.schema import null
        self.assertEqual(repr(null), '<schema.null>')

    def test_pickling(self):
        from nive.components.reform.schema import null
        import cPickle
        self.failUnless(cPickle.loads(cPickle.dumps(null)) is null)

class Dummy(object):
    pass

class DummySchemaNode(object):
    def __init__(self, typ, name='', exc=None, default=None):
        self.typ = typ
        self.name = name
        self.exc = exc
        self.required = default is None
        self.default = default
        self.children = []

    def deserialize(self, val, formstruct=None):
        from nive.components.reform.schema import Invalid
        if self.exc:
            raise Invalid(self, self.exc)
        return val

    def serialize(self, val):
        from nive.components.reform.schema import Invalid
        if self.exc:
            raise Invalid(self, self.exc)
        return val

    def __getitem__(self, name):
        for child in self.children:
            if child.name == name:
                return child

class DummyValidator(object):
    def __init__(self, msg=None):
        self.msg = msg

    def __call__(self, node, value):
        from nive.components.reform.schema import Invalid
        if self.msg:
            raise Invalid(node, self.msg)

class Uncooperative(object):
    def __str__(self):
        raise ValueError('I wont cooperate')

    __unicode__ = __str__

class DummyType(object):
    def serialize(self, node, value):
        return value

    def deserialize(self, node, value, formstruct=None):
        return value

    def flatten(self, node, appstruct, prefix='', listitem=False):
        if listitem:
            key = prefix.rstrip('.')
        else:
            key = prefix + 'appstruct'
        return {key:appstruct}

    def unflatten(self, node, paths, fstruct):
        assert paths == [node.name]
        return fstruct[node.name]

class TestSet(unittest.TestCase):
    def _makeOne(self, **kw):
        from nive.components.reform.schema import Set
        return Set(**kw)

    def test_serialize(self):
        node = DummySchemaNode2()
        typ = self._makeOne()
        provided = []
        result = typ.serialize(node, provided)
        self.failUnless(result is provided)

    def test_serialize_null(self):
        from nive.components.reform.schema import null
        node = DummySchemaNode2()
        typ = self._makeOne()
        result = typ.serialize(node, null)
        self.assertEqual(result, null)

    def test_deserialize_no_iter(self):
        node = DummySchemaNode2()
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, 'str')
        self.assertEqual(e.msg, '${value} is not iterable')

    def test_deserialize_null(self):
        from nive.components.reform.schema import null
        node = DummySchemaNode2()
        typ = self._makeOne()
        result = typ.deserialize(node, null)
        self.assertEqual(result, null)

    def test_deserialize_valid(self):
        node = DummySchemaNode2()
        typ = self._makeOne()
        result = typ.deserialize(node, ('a',))
        self.assertEqual(result, set(('a',)))

    def test_deserialize_empty_allow_empty_false(self):
        node = DummySchemaNode2()
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, ())
        self.assertEqual(e.msg, 'Required')

    def test_deserialize_empty_allow_empty_true(self):
        node = DummySchemaNode2()
        typ = self._makeOne(allow_empty=True)
        result = typ.deserialize(node, ())
        self.assertEqual(result, set())

class TestFileData(unittest.TestCase):
    def _makeOne(self):
        from nive.components.reform.schema import FileData
        return FileData()

    def test_deserialize_null(self):
        from nive.components.reform.schema import null
        typ = self._makeOne()
        node = DummySchemaNode2()
        result = typ.deserialize(node, null)
        self.assertEqual(result, null)

    def test_deserialize_not_null(self):
        typ = self._makeOne()
        node = DummySchemaNode2()
        result = typ.deserialize(node, '123')
        self.assertEqual(result, '123')

    def test_serialize_null(self):
        from nive.components.reform.schema import null
        typ = self._makeOne()
        node = DummySchemaNode2()
        result = typ.serialize(node, null)
        self.assertEqual(result, null)

    def test_serialize_no_filename(self):
        typ = self._makeOne()
        node = DummySchemaNode2()
        e = invalid_exc(typ.serialize, node, {'uid':'uid'})
        self.assertEqual(e.msg, "${value} has no ${key} key")

    def test_serialize_no_uid(self):
        typ = self._makeOne()
        node = DummySchemaNode2()
        e = invalid_exc(typ.serialize, node, {'filename':'filename'})
        self.assertEqual(e.msg, "${value} has no ${key} key")

    def test_serialize_with_values(self):
        typ = self._makeOne()
        node = DummySchemaNode2()
        result = typ.serialize(node, {'filename':'filename', 'uid':'uid',
                                      'mimetype':'mimetype', 'size':'size',
                                      'fp':'fp', 'preview_url':'preview_url'})
        self.assertEqual(result['filename'], 'filename')
        self.assertEqual(result['uid'], 'uid')
        self.assertEqual(result['mimetype'], 'mimetype')
        self.assertEqual(result['size'], 'size')
        self.assertEqual(result['fp'], 'fp')
        self.assertEqual(result['preview_url'], 'preview_url')
        

class TestList(unittest.TestCase):
    def _makeOne(self, **kw):
        from nive.components.reform.schema import List
        return List(**kw)

    def test_serialize(self):
        node = DummySchemaNode2()
        typ = self._makeOne()
        provided = []
        result = typ.serialize(node, provided)
        self.failUnless(result is provided)

    def test_serialize_null(self):
        from nive.components.reform.schema import null
        node = DummySchemaNode2()
        typ = self._makeOne()
        result = typ.serialize(node, null)
        self.assertEqual(result, null)

    def test_deserialize_no_iter(self):
        node = DummySchemaNode2()
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, 123)
        self.assertEqual(e.msg, '${value} is not iterable')

    def test_deserialize_null(self):
        from nive.components.reform.schema import null
        node = DummySchemaNode2()
        typ = self._makeOne()
        result = typ.deserialize(node, null)
        self.assertEqual(result, null)

    def test_deserialize_valid(self):
        node = DummySchemaNode2()
        typ = self._makeOne()
        result = typ.deserialize(node, ('a',))
        self.assertEqual(result, ['a'])

        node = DummySchemaNode2()
        typ = self._makeOne()
        result = typ.deserialize(node, 'str')
        self.assertEqual(result, ['str'])

    def test_deserialize_empty_allow_empty_false(self):
        node = DummySchemaNode2()
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, node, ())
        self.assertEqual(e.msg, 'Required')

    def test_deserialize_empty_allow_empty_true(self):
        node = DummySchemaNode2()
        typ = self._makeOne(allow_empty=True)
        result = typ.deserialize(node, ())
        self.assertEqual(result, [])
        
        
class DummySchemaNode2(object):
    def __init__(self, typ=None, name='', exc=None, default=None):
        self.typ = typ
        self.name = name
        self.exc = exc
        self.required = default is None
        self.default = default
        self.children = []

