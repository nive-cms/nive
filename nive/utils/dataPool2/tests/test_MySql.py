# -*- coding: latin-1 -*-

import copy, time
import unittest

from nive.tests.test_mysql import ENABLE_MYSQL_TESTS, myapp

class utc:
    pass
uTestCase = utc

if ENABLE_MYSQL_TESTS:
    from nive.utils.dataPool2.mySqlPool import *
    uTestCase = unittest.TestCase
    
from nive.definitions import DatabaseConf
from nive.utils.dataPool2.base import *
from nive.utils.path import DvPath

from test_db import dbTest
from test_Base import conf, stdMeta, struct, SystemFlds, Fulltext, Files, data1_1, data2_1, meta1, file1_1, file1_2

from nive.tests import __local

conn = DatabaseConf(
    user = __local.USER,
    password = __local.PASSWORD,
    host = __local.HOST,
    port = __local.PORT,
    dbName = __local.DATABASE,
    unicode = 1,
    timeout = 1
)
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
