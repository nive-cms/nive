# -*- coding: utf-8 -*-

import unittest

from nive.utils import country_data
from nive.utils import language


class Country_data(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    
    def test_defs(self):
        for ccc in country_data.countries:
            self.assert_(ccc[0], ccc)
            self.assert_(ccc[1], ccc)
            self.assert_(ccc[2], ccc)
            self.assert_(ccc[3], ccc)
                        
        
    def test_codes(self):
        for conf in country_data.GetCountries():
            self.assert_(conf.get("id"), conf)
            self.assert_(conf.get("name"), conf)
            
            
    def test_get(self):
        self.assert_(country_data.GetConf(u"DEU").get(u"code2")==u"DE")
        self.assert_(country_data.GetConf(u"DE").get(u"code")==u"DEU")
        self.assert_(country_data.GetConf(u"XX").get(u"code2")==None)
                        
        


class Country(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    
    def test_lang(self):
        cext = language.CountryExtension()
        for c in cext.Codelist():
            self.assert_(c.get("id"))
            self.assert_(c.get("name"))
            
    def test_conf(self):
        lext = language.CountryExtension()
        for c in country_data.countries:
            conf = lext.GetConf(c[0])
            self.assert_(conf.get("code"), c)
            self.assert_(conf.get("code2"), c)
            self.assert_(conf.get("name"), c)
            

    def test_name(self):
        lext = language.CountryExtension()
        for c in country_data.countries:
            name = lext.GetName(c[0])
            self.assert_(name, c)
            
            
            
            
            