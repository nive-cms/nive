# -*- coding: latin-1 -*-

import copy, time
import unittest

from nive.tests.tmysql import ENABLE_MYSQL_TESTS, myapp

class utc:
    pass
uTestCase = utc

if ENABLE_MYSQL_TESTS:
    from nive.utils.dataPool2.mySqlPool import *
    uTestCase = unittest.TestCase
    
from nive.utils.dataPool2.base import *
from nive.utils.path import DvPath

from t_db import dbTest
from t_Base import conf, stdMeta, struct, SystemFlds, Fulltext, Files, data1_1, data2_1, meta1, file1_1, file1_2



conn = {}
conn["user"] = u"root"
conn["password"] = u""
conn["host"] = u"localhost"
conn["port"] = u""
conn["dbName"] = u"ut_nive"
conn["unicode"] = 1
conn["timeout"] = 1
myconn = conn

def getPool():
    p = MySql(connParam=myconn, **conf)
    p.structure.Init(structure=struct, stdMeta=struct[u"pool_meta"])
    return p


class MySqlTest(dbTest, uTestCase):
    """
    """

    def setUp(self):
        self.pool = getPool()
        self.checkdb()
        self.connect()

    def connect(self):
        #print "Connect DB on", conn["host"],
        self.pool.CreateConnection(myconn)
        self.assert_(self.pool.connection.IsConnected())
        #print "OK"

    def checkdb(self):
        myapp()
    
def __test():
    unittest.main()
