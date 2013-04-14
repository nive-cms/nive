# -*- coding: latin-1 -*-

import copy, time
import unittest
from types import *

from nive.utils.dataPool2.base import *
from nive.utils.dataPool2.sqlite3Pool import *
from nive.utils.path import DvPath

from sqlite3 import OperationalError

from test_db import dbTest

class Sqlite3ConnMultithreading(dbTest):
    """
    multithreading test
    """
    def runTest(self):
        return
    
    def setUp(self):
        dbfile = DvPath(conn["dbName"])
        if not dbfile.IsFile():
            dbfile.CreateDirectories()
            checkdb()
        db = Sqlite3(conf, conn)
        db.GetPoolStructureObj().SetStructure(struct)
        self.pool = db
    
    
    def connect(self):
        #print "Connect DB on", conn["host"],
        self.pool.CreateConnection(conn)
        self.pool.connection.IsConnected()
        try:
            self.pool.Query("select id from pool_meta where id=1")
        except OperationalError:
            checkdb()

    def assert_(self, *kw):
        return True

        
import threading
        
class ThreadClass(threading.Thread):

    def run(self):
        print "starting thread %s"%self.name
        testcnt = 5
        for i in range(testcnt):
            self.runapp()
        print "terminating thread %s"%self.name

    def runapp(self):    
        self.app.test_create_empty()
        self.app.test_create_empty2()
        self.app.test_create_base()
        self.app.test_files_base()
        self.app.test_preload()
        self.app.test_duplicate_base()
        self.app.test_sql()
        self.app.test_sql2()
        self.app.test_search_files()
        self.app.test_tree()
            

def __test():
    dbfile = DvPath(conn["dbName"])
    if not dbfile.IsFile():
        dbfile.CreateDirectories()
        checkdb()
    db = Sqlite3(conf, conn)
    db.GetPoolStructureObj().SetStructure(struct)
    app = Sqlite3ConnMultithreading()
    app.pool = db
    app.setUp()

    threadcnt = 10
    ts = []
    for i in range(threadcnt):
        t = ThreadClass()
        ts.append(t)
        t.app = app
        t.start()
    for t in ts:
        t.join()
    print "OK"



if __name__ == '__main__':
    __test()


