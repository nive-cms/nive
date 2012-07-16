import unittest

class TestAPI(unittest.TestCase):
    def test_it(self):
        # none of these imports should fail
        from nive.components.reform import Form
        from nive.components.reform import Button
        from nive.components.reform import Field

        from nive.components.reform import FileData
        from nive.components.reform import Set

        from nive.components.reform import ValidationFailure
        from nive.components.reform import TemplateError

        from nive.components.reform import ZPTRendererFactory
        from nive.components.reform import default_renderer

        from nive.components.reform import widget
        
        
        
        
        
