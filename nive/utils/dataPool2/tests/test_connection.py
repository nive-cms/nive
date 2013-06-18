# -*- coding: latin-1 -*-

import copy
from time import time
import unittest

from nive.definitions import DatabaseConf
from nive.utils.dataPool2.connection import *
from nive.utils.dataPool2.sqlite3Pool import Sqlite3

from sqlite3 import OperationalError

from nive.tests.db_app import app_db

from nive.tests import __local

# configuration ---------------------------------------------------------------------------
conn = DatabaseConf(
    dbName = __local.ROOT+"nive.db"
)


class ConnectionTest(unittest.TestCase):
    """
    """
    def test_conn(self):
        self.assert_(Connection(conn))
        
    def test_conntl(self):
        self.assert_(ConnectionThreadLocal(conn))
    
    def test_connreq(self):
        self.assert_(ConnectionRequest(conn))



