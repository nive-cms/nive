# -*- coding: utf-8 -*-

import unittest

from nive.utils import language_data
from nive.utils import language


class Langugage_data(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    
    def test_defs(self):
        for lang in language_data.languages:
            conf = language_data.GetConf(lang)
            self.assert_(conf.get("code"), lang)
            self.assert_(conf.get("code2"), lang)
            self.assert_(conf.get("name"), lang)
        conf = language_data.GetConf("xxx")
        self.assert_(conf.get("code")==u"")
        
    def test_codes(self):
        for conf in language_data.GetLanguages():
            self.assert_(conf.get("id"), conf)
            self.assert_(conf.get("name"), conf)
            
            
    def test_get(self):
        self.assert_(language_data.GetConf(u"ger").get(u"code2")==u"de")
        self.assert_(language_data.GetConf(u"de").get(u"code")==u"ger")
                        
        


class Langugage(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    
    def test_lang(self):
        lext = language.LanguageExtension()
        for c in lext.Codelist():
            self.assert_(c.get("id"))
            self.assert_(c.get("name"))
            
    def test_conf(self):
        lext = language.LanguageExtension()
        for l in language_data.languages:
            conf = lext.GetConf(l)
            self.assert_(conf.get("code"), l)
            self.assert_(conf.get("code2"), l)
            self.assert_(conf.get("name"), l)
            

    def test_name(self):
        lext = language.LanguageExtension()
        for l in language_data.languages:
            name = lext.GetName(l)
            self.assert_(name, l)
            
            
            
            
            