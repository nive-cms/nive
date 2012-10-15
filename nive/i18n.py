"""
use as import:
from nive.i18n import _
"""
from translationstring import TranslationStringFactory
_ = TranslationStringFactory('nive')


from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request

def translator(request=None):
    """
    a shortcut to create a translator to translate a term. calls pyramid `get_localizer(get_current_request())`
    to get the current language or creates a placeholder if in testing mode.
    
    the returned translator is a reference to the translate function.
    
    ::
        translate = translator()
        t = translate(term)

    """
    try:
        localizer = get_localizer(request or get_current_request())
    except:
        # for testing. just returns the term on translate().
        import helper
        localizer = helper.FakeLocalizer()
    return localizer.translate

def translate(term, request=None):
    """
    a shortcut to translate a term. calls pyramid `get_localizer(get_current_request())`
    to get the current language or creates a placeholder if in testing mode

    ::
        t = translate(term)

    """
    try:
        localizer = get_localizer(request or get_current_request())
    except:
        # for testing. just returns the term on translate().
        import helper
        localizer = helper.FakeLocalizer()
    return localizer.translate(term) 

