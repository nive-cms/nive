

import unittest

from nive.definitions import *

from nive.components.extensions.persistence import *

from nive.tests import db_app

        

class Persistence(unittest.TestCase):
    
    def setUp(self):
        self.app = db_app.app_nodb()
        pass
    
    def tearDown(self):
        pass
    
    
    def test_1(self):
        p = PersistentConf(self.app, self.app.configuration)
        
        
    def test_2(self):
        LoadStoredConfValues(self.app, None)
        
        
        
class tdbPersistence(unittest.TestCase):
    
    def setUp(self):
        self.app = db_app.app_db(["nive.components.extensions.persistence.dbPersistenceConfiguration"])
        pass
    
    def tearDown(self):
        pass
    
    def test_conf1(self):
        r=dbPersistenceConfiguration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")
        
        
    def test_2(self):
        storage = self.app.Factory(IModuleConf, "persistence")
        self.assert_(storage)
        LoadStoredConfValues(self.app, None)