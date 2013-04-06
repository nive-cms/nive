
from copy import deepcopy
import language_data 


class LanguageExtension(object):
    """    
    empty = {}
    empty["code"] = ""
    empty["code2"] = ""
    empty["name"] = ""
    empty["articles_used"] = 0 # 1=article, 2=f+m, 3=f+m+n
    empty["articles"] = {}
    empty["article_abbr"] = ""
    empty["verb_prefix"] = ""
    empty["plural"] = ""
    empty["codepage"] = ""
    empty["remove_chars"] = "\t\r\n"
    empty["special_chars"] = ""
    """
    
    def Codelist(self):
        """
        """
        return language_data.GetLanguages()


    def GetConf(self, lang):
        """
        """
        return language_data.GetConf(lang)


    def GetName(self, lang):
        """
        """
        return language_data.GetConf(lang).get("name")


import country_data 

class CountryExtension(object):
    """    
    empty = {}
    empty["code"] = ""
    empty["language"] = ""
    """

    def Codelist(self):
        """
        """
        return country_data.GetCountries()
        

    def GetConf(self, code):
        """
        """
        return country_data.GetConf(code)


    def GetName(self, code):
        """
        """
        return country_data.GetConf(code).get("name")

