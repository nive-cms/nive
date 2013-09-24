"""
Running mysql tests
-------------------
Create a database 'ut_nive' and assign all permissions for user 'root@localhost'. 
File root is '/var/tmp/nive'.

To customize settings change 'dbconfMySql' in this file and 'conn' in 
nive/utils/dataPool2/tests/t_MySql.py.  

"""


import time
import unittest
from StringIO import StringIO

from nive.utils.path import DvPath

from nive.definitions import *
from nive.security import User
from nive.components.objects.base import ApplicationBase

from db_app import *
from test_nive import appTest_db
from test_container import containerTest_db, groupsrootTest_db
from test_objects import objTest_db, objToolTest_db, objWfTest_db, groupsTest_db

from nive.tests import __local

# real database test configuration
# change these to fit your system
ENABLE_MYSQL_TESTS = True
try:
    import MySQLdb
except ImportError:
    ENABLE_MYSQL_TESTS = False

dbconfMySql = DatabaseConf(
    context = "MySql",
    dbName = __local.DATABASE,
    fileRoot = __local.ROOT,
    host = __local.HOST,
    user = __local.USER,
    port = __local.PORT,
    password = __local.PASSWORD
)

if not ENABLE_MYSQL_TESTS:
    class utc:
        pass
    uTestCase = utc
else:
    uTestCase = unittest.TestCase
    
    
def myapp(modules=None):
    a = ApplicationBase()
    appconf.unlock()
    appconf.dbConfiguration = dbconfMySql
    appconf.lock()
    a.Register(appconf)
    if modules:
        for m in modules:
            a.Register(m)
    p = Portal()
    p.Register(a, "nive")
    a.SetupRegistry()
    root = DvPath(a.dbConfiguration.fileRoot)
    if not root.IsDirectory():
        root.CreateDirectories()
    try:
        a.Query("select id from pool_meta where id=1")
        a.Query("select id from data1 where id=1")
        a.Query("select id from data2 where id=1")
        a.Query("select id from data3 where id=1")
        a.Query("select id from pool_files where id=1")
        a.Query("select id from pool_sys where id=1")
        a.Query("select id from pool_groups where id=1")
    except:
        a.GetTool("nive.components.tools.dbStructureUpdater")()
    a.Startup(None)
    return a


class myappTest_db(appTest_db, uTestCase):

    def setUp(self):
        #emptypool()
        self.app = myapp()
        self.remove=[]


class mycontainerTest_db(containerTest_db, uTestCase):

    def setUp(self):
        #emptypool()
        self.app = myapp()
        self.remove=[]

class mygroupsTest_db(groupsTest_db, uTestCase):

    def setUp(self):
        #emptypool()
        self.app = myapp(["nive.components.extensions.localgroups"])
        self.remove=[]

class myobjTest_db(objTest_db, uTestCase):

    def setUp(self):
        #emptypool()
        self.app = myapp()
        self.remove=[]


class mygroupsrootTest_db(groupsrootTest_db, uTestCase):

    def setUp(self):
        #emptypool()
        self.app = myapp(["nive.components.extensions.localgroups"])
        self.remove=[]



#tests!
#class myobjToolTest_db(objToolTest_db, uTestCase):
#
#    def setUp(self):
#        #emptypool()
#        self.app = myapp()

#class myobjWfTest_db(objWfTest_db, uTestCase):
#
#    def setUp(self):
#        #emptypool()
#        self.app = myapp()



if __name__ == '__main__':
    unittest.main()



