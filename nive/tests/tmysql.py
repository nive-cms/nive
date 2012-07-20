
import time
import unittest
from StringIO import StringIO

from nive.utils.path import DvPath

from nive.definitions import *
from nive.security import User
from nive.components.objects.base import ApplicationBase

from db_app import *
from tnive import appTest_db
from tcontainer import containerTest_db
from tobjects import objTest_db, objToolTest_db, objWfTest_db


# real database test configuration
# change these to fit your system
ENABLE_MYSQL_TESTS = True
try:
    import MySQLdb
except ImportError:
    ENABLE_MYSQL_TESTS = False

dbconfMySql = DatabaseConf(
    dbName = "ut_nive",
    fileRoot = "/var/tmp/nive",
    context = "MySql",
    host = "localhost",
    user = "root"
)

if not ENABLE_MYSQL_TESTS:
    class utc:
        pass
    uTestCase = utc
else:
    uTestCase = unittest.TestCase
    
    
def myapp(modules=None):
    a = ApplicationBase()
    a.Register(appconf)
    a.Register(dbconfMySql)
    if modules:
        for m in modules:
            a.Register(m)
    p = Portal()
    p.Register(a, "nive")
    a.LoadConfiguration()
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

class myobjTest_db(objTest_db, uTestCase):

    def setUp(self):
        #emptypool()
        self.app = myapp()
        self.remove=[]

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



