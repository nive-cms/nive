# -*- coding: latin-1 -*-

import copy
from time import time
import unittest
from types import *

from nive.utils.dataPool2.base import *
from nive.utils.dataPool2.sqlite3Pool import Sqlite3
from nive.utils.path import DvPath

from sqlite3 import OperationalError

from nive.tests.db_app import app_db
from t_Base import conf, stdMeta, struct, SystemFlds, Fulltext, Files, data1_1, data2_1, meta1, file1_1, file1_2


# configuration ---------------------------------------------------------------------------
conn = {}
conn["dbName"] = u"/var/tmp/nive/nive.db"

def getPool():
    p = Sqlite3(connParam=conn, **conf)
    p.structure.Init(structure=struct, stdMeta=struct[u"pool_meta"])
    return p


countdb = 1

class dbTest:

    def tearDown(self):
        self.pool.Close()

    def statdb(self):
        c = self.pool.GetCountEntries()
        countdb = c
        #print "Count entries in DB:", c
        return c

    def checkdb(self):
        app_db()


    # entries ---------------------------------------------------------------------------
    def create1(self):
        #print "Create Entry",
        e=self.pool.CreateEntry(u"data1", user="unittest")
        e.Commit(user="unittest")
        #print e.GetID(), "OK"
        return e.GetID()

    def create2(self):
        #print "Create Entry",
        e=self.pool.CreateEntry(u"data2", user="unittest")
        e.Commit(user="unittest")
        #print e.GetID(), "OK"
        return e.GetID()

    def get(self, id):
        #print "Load entry", id
        e=self.pool.GetEntry(id)
        #print "OK"
        return e

    # set ---------------------------------------
    def set1(self, id):
        #print "Store data", id,
        e=self.pool.GetEntry(id)
        self.assert_(e)
        e.data.update(data1_1)
        e.meta.update(meta1)
        e.Commit(user="unittest")
        self.assert_(e.GetMeta())
        d=e.GetData()
        self.assert_(d.get(u"ftext")    == data1_1.get(u"ftext")    )
        self.assert_(d.get(u"fnumber")    == data1_1.get(u"fnumber")    )
        self.assert_(self.pool.GetDBDate(str(d.get(u"fdate"))) == self.pool.GetDBDate(str(data1_1.get(u"fdate"))))
        self.assert_(d.get(u"flist")    == data1_1.get(u"flist")    )
        self.assert_(d.get(u"fmselect") == data1_1.get(u"fmselect") )
        self.assert_(d.get(u"funit")    == data1_1.get(u"funit")    )
        self.assert_(d.get(u"funitlist")== data1_1.get(u"funitlist"))
        self.assert_(type(d.get(u"ftext"))==UnicodeType    )
        #print "OK"

    def set2(self, id):
        #print "Store data", id,
        e=self.pool.GetEntry(id)
        self.assert_(e)
        e.data.update(data2_1)
        e.meta.update(meta1)
        e.Commit(user="unittest")
        self.assert_(e.GetMeta())
        d=e.GetData()
        self.assert_(d.get(u"ftext")    == data2_1.get(u"ftext")    )
        self.assert_(d.get(u"fstr")     == data2_1.get(u"fstr")    )
        self.assert_(type(d.get(u"ftext"))==UnicodeType    )
        #print "OK"

    def setfile1(self, id):
        #print "Store file", id,
        e=self.pool.GetEntry(id)
        self.assert_(e)
        self.assert_(e.CommitFile(u"file1", {"file":file1_1, "filename":"file1.txt"}))
        e.Commit(user="unittest")
        self.assert_(e.GetFile(u"file1").read() == file1_1)
        #print "OK"

    def setfile2(self, id):
        #print "Store file", id,
        e=self.pool.GetEntry(id)
        self.assert_(e)
        self.assert_(e.CommitFile(u"file2", {"file":file1_2, "filename":u"file2.txt"}))
        e.Commit(user="unittest")
        self.assert_(e.GetFile(u"file2").read() == file1_2)
        #print "OK"


    # get --------------------------------------------------------------------------
    def data1(self, id):
        #print "Check entry data", id,
        e=self.pool.GetEntry(id)
        d=e.GetData()
        self.assert_(d.get(u"ftext")    == data1_1.get(u"ftext")    )
        self.assert_(d.get(u"fnumber")    == data1_1.get(u"fnumber")    )
        self.assert_(self.pool.GetDBDate(str(d.get(u"fdate"))) == self.pool.GetDBDate(str(data1_1.get(u"fdate"))))
        self.assert_(d.get(u"flist")    == data1_1.get(u"flist")    )
        self.assert_(d.get(u"fmselect") == data1_1.get(u"fmselect") )
        self.assert_(d.get(u"funit")    == data1_1.get(u"funit")    )
        self.assert_(d.get(u"funitlist")== data1_1.get(u"funitlist"))
        self.assert_(type(d.get(u"ftext"))==UnicodeType    )
        #print "OK"

    def data2(self, id):
        #print "Check entry data", id,
        e=self.pool.GetEntry(id)
        d=e.GetData()
        self.assert_(d.get(u"ftext")    == data2_1.get(u"ftext")    )
        self.assert_(d.get(u"fstr")     == data2_1.get(u"fstr")    )
        self.assert_(type(d.get(u"ftext"))==UnicodeType    )
        #print "OK"

    def file1(self, id):
        #print "Load file", id,
        e=self.pool.GetEntry(id)
        self.assert_(e.GetFile(u"file1").read() == file1_1)
        #print "OK"

    def file2(self, id):
        #print "Load file", id,
        e=self.pool.GetEntry(id)
        self.assert_(e.GetFile(u"file2").read() == file1_2)
        #print "OK"

    def fileErr(self, id):
        #print "Load non existing file", id,
        e=self.pool.GetEntry(id)
        self.assert_(e.GetFile(u"file1") == None)
        #print "OK"

    # getstream --------------------------------------------------------------------------
    def file1stream(self, id):
        #print "Load file", id,
        e=self.pool.GetEntry(id)
        s=e.GetFile(u"file1")
        d = s.read()
        s.close()
        self.assert_(d == file1_1)
        #print "OK"

    def file2stream(self, id):
        #print "Load file", id,
        e=self.pool.GetEntry(id)
        s=e.GetFile(u"file2")
        s.read()
        s.close()
        self.assert_(d == file1_2)
        #print "OK"

    # functions ------------------------------------------------------------------------
    def stat(self, id):
        e=self.pool.GetEntry(id)
        self.assert_(e.GetMetaField(u"pool_createdby")==u"unittest")
        self.assert_(e.GetMetaField(u"pool_changedby")==u"unittest")
        #print "Create: %s by %s    Changed: %s by %s" % (e.GetMetaField("pool_create"), e.GetMetaField("pool_createdby"), e.GetMetaField("pool_change"), e.GetMetaField("pool_changedby"))

    def delete(self, id):
        #print "Delete", id,
        e=self.pool.GetEntry(id)
        self.assert_(e)
        del e
        self.assert_(self.pool.DeleteEntry(id))
        self.pool.Commit(user="unittest")

    def duplicate(self, id,file=True):
        #print "Duplicate", id,
        e=self.pool.GetEntry(id)
        n=e.Duplicate(file)
        self.assert_(n)
        n.Commit(user="unittest")
        #print "OK"
        return n.GetID()

    def filetest(self, id):
        #print "File test", id,
        e=self.pool.GetEntry(id)
        self.assert_(e)

        self.assertItemsEqual(e.FileKeys(), [u"file1",u"file2"])

        self.assert_(e.FileExists(e.GetFile(u"file1")))
        self.assert_(e.FileExists(e.GetFile(u"file2")))
        self.assert_(e.FileExists(e.GetFile(u"file_xxx"))==False)

        self.assert_(e.GetFile(u"file1").filename==u"file1.txt")
        self.assert_(e.GetFile(u"file2").filename==u"file2.txt")
        self.assert_(type(e.GetFile(u"file1").filename)==UnicodeType)
        self.assert_(type(e.GetFile(u"file2").filename)==UnicodeType)

        self.assert_(e.GetFile(u"file1"))
        self.assert_(e.GetFile(u"file2"))
        self.assert_(e.GetFile(u"file3")==None)
        self.assert_(e.GetFile(u"")==None)

        l=e.Files({})
        self.assert_(len(l)==2)
        l2=[]
        for f in l:
            l2.append(f[u"filekey"])
        self.assert_(u"file1" in l2)
        self.assert_(u"file2" in l2)
        #print "OK"





    # helper ------------------------------------------------------------------------
    def bakupSQL(self):
        #print "Bakup SQL Dump to file"
        p = PoolBakup(self.pool)
        r,p1 = p.SQLDump()
        r,p2 = p.SQLArchive()
        #print r
        p1 = DvPath(p1)
        self.assert_(p1.Exists())
        p2 = DvPath(p2)
        self.assert_(p2.Exists())


    # new test fncs -----------------------------------------------------------------------------

    def test_create_empty(self):

        t = time()
        c = self.statdb()
        # creating
        id1=self.create1()
        e=self.get(id1)
        del e
        self.stat(id1)

        id2=self.create2()
        e=self.get(id2)
        del e
        self.stat(id2)

        # cnt    ok
        c2 = self.statdb()
        self.assert_(c+2==c2)

        # deleting
        self.delete(id1)
        self.delete(id2)
        c3 = self.statdb()
        self.assert_(c==c3)




    def test_create_base(self):

        t = time()
        c = self.statdb()
        # creating
        id1=self.create1()
        e=self.get(id1)
        del e
        self.stat(id1)

        id2=self.create2()
        e=self.get(id2)
        del e
        self.stat(id2)

        # cnt    ok
        c2 = self.statdb()
        self.assert_(c+2==c2)

        #update data
        self.set1(id1)
        self.set2(id2)
        self.setfile1(id1)
        self.setfile2(id1)

        #load data
        self.data1(id1)
        self.data2(id2)
        self.file1(id1)
        self.file2(id1)

        # deleting
        self.delete(id1)
        self.delete(id2)
        c3 = self.statdb()
        self.assert_(c==c3)



    def test_files_base(self):

        t = time()
        c = self.statdb()

        # creating
        id1=self.create1()
        e=self.get(id1)

        #update data
        self.set1(id1)
        self.setfile1(id1)
        self.setfile2(id1)

        #load data
        self.file1(id1)
        self.file2(id1)

        # file
        self.filetest(id1)

        # deleting
        self.delete(id1)
        c3 = self.statdb()
        self.assert_(c==c3)


    def test_preload(self):

        t = time()
        self.statdb()

        id=self.create1()

        #print "Preload Skip", id,
        e = self.pool.GetEntry(id, preload=u"skip")
        self.assert_(e.GetDataRef()>0 and e.GetDataTbl()!=u"")
        del e
        #print "OK"

        #print "Preload Meta", id,
        e = self.pool.GetEntry(id, preload=u"meta")
        self.assert_(e.GetDataRef()>0 and e.GetDataTbl()!=u"")
        del e
        #print "OK"

        #print "Preload All", id,
        e = self.pool.GetEntry(id, preload=u"all")
        self.assert_(e.GetDataRef()>0 and e.GetDataTbl()!=u"")
        del e
        #print "OK"

        #print "Preload MetaData", id,
        e = self.pool.GetEntry(id, preload=u"metadata")
        self.assert_(e.GetDataRef()>0 and e.GetDataTbl()!=u"")
        del e
        #print "OK"

        #print "Preload StdMeta", id,
        e = self.pool.GetEntry(id, preload=u"stdmeta")
        self.assert_(e.GetDataRef()>0 and e.GetDataTbl()!=u"")
        del e
        #print "OK"

        #print "Preload StdMetaData", id,
        e = self.pool.GetEntry(id, preload=u"stdmetadata")
        self.assert_(e.GetDataRef()>0 and e.GetDataTbl()!=u"")
        del e
        #print "OK"

        self.delete(id)
        self.assert_(self.pool.IsIDUsed(id) == False)


    def test_duplicate_base(self):

        t = time()
        c=self.statdb()

        # creating
        id1=self.create1()
        id2=self.create2()

        # cnt    ok
        c2 = self.statdb()
        self.assert_(c+2==c2)

        #update data
        self.set1(id1)
        self.set2(id2)
        self.setfile1(id1)
        self.setfile2(id1)

        #load data
        self.data1(id1)
        self.data2(id2)
        self.file1(id1)
        self.file2(id1)

        # duplicate
        id3=self.duplicate( id1)
        id4=self.duplicate( id2)
        id5=self.duplicate( id1, file=False)

        #load dupl. data
        self.data1(id3)
        self.data1(id5)
        self.data2(id4)
        self.file1(id3)
        self.file2(id3)
        self.fileErr(id5)

        # deleting
        self.delete(id1)
        self.delete(id2)
        self.delete(id3)
        self.delete(id4)
        self.delete(id5)
        c3 = self.statdb()
        self.assert_(c==c3)


    def test_sql(self):

        t = time()
        #print "GetSQLSelect",
        sql, values=self.pool.GetSQLSelect(list(stdMeta)+list(struct[u"data1"]),
                        {u"pool_type": "data1", u"ftext": "123", u"fnumber": 300000},
                        sort = u"title, id, fnumber",
                        ascending = 0,
                        dataTable = u"data1",
                        operators={u"pool_type":u"=", u"ftext": u"<>", u"fnumber": u"<"},
                        start=1,
                        max=123)
        self.pool.Query(sql, values)
        c=self.pool.Execute(sql, values)
        c.close()
        #print "OK"

        #print "GetSQLSelect singleTable",
        sql, values=self.pool.GetSQLSelect(list(struct[u"data1"]),
                                     {u"ftext": "", u"fnumber": 3},
                                     dataTable=u"data1",
                                     sort = u"id, fnumber",
                                     ascending = 1,
                                     operators={u"ftext": u"=", u"fnumber": u"="},
                                     start=1,
                                     max=123,
                                     singleTable=1)
        self.pool.Query(sql, values)
        c=self.pool.Execute(sql, values)
        c.close()
        #print "OK"

        #print "GetFulltextSQL",
        sql, values=self.pool.GetFulltextSQL(u"is",
                            list(stdMeta)+list(struct[u"data1"]),
                            {},
                            sort = u"title",
                            ascending = 1,
                            dataTable = u"data1")
        self.pool.Query(sql, values)
        c=self.pool.Execute(sql, values)
        c.close()
        #print "OK"


    def test_sql2(self):

        t = time()
        sql1, values1=self.pool.GetSQLSelect(list(stdMeta)+list(struct[u"data1"]),
                        {u"pool_type": "data1", u"ftext": "", u"fnumber": 3},
                        sort = u"title, id, fnumber",
                        ascending = 0,
                        dataTable = u"data1",
                        operators={u"pool_type":u"=", u"ftext": u"<>", u"fnumber": u">"},
                        start=1,
                        max=123)
        sql2, values2=self.pool.GetSQLSelect(list(struct[u"data1"]),
                                     {u"ftext": u"", u"fnumber": 3},
                                     dataTable=u"data1",
                                     sort = u"id, fnumber",
                                     ascending = 1,
                                     operators={u"ftext": u"<>", u"fnumber": u">"},
                                     start=1,
                                     max=123,
                                     singleTable=1)
        sql3, values3=self.pool.GetFulltextSQL(u"is",
                            list(stdMeta)+list(struct[u"data1"]),
                            {},
                            sort = u"title",
                            ascending = 1,
                            dataTable = u"data1")
        c=self.pool.connection.cursor()
        c.execute(sql1, values1)
        c.execute(sql2, values2)
        c.execute(sql3, values3)


    def test_insertdelete(self):
        self.pool.DeleteRecords("pool_meta", {"pool_type": "notype", "title": "test entry"}, cursor=None)
        self.pool.Commit()

        self.pool.InsertFields("pool_meta", {"pool_type": "notype", "title": "test entry"}, cursor = None)
        self.pool.Commit()
        sql, values = self.pool.GetSQLSelect(["id"], {"pool_type": "notype", "title": "test entry"}, dataTable="pool_meta", singleTable=1) 
        id = self.pool.Query(sql, values)
        self.assert_(id)
        
        self.pool.UpdateFields("pool_meta", id[0][0], {"pool_type": "notype 123", "title": "test entry 123"}, cursor = None)
        self.pool.Commit()
        sql, values = self.pool.GetSQLSelect(["id"], {"pool_type": "notype", "title": "test entry"}, dataTable="pool_meta", singleTable=1) 
        id = self.pool.Query(sql, values)
        self.assertFalse(id)
        sql, values = self.pool.GetSQLSelect(["id"], {"pool_type": "notype 123", "title": "test entry 123"}, dataTable="pool_meta", singleTable=1) 
        id = self.pool.Query(sql, values)
        self.assert_(id)
        
        for i in id:
            self.pool.DeleteRecords("pool_meta", {"id":i[0]}, cursor=None)
        self.pool.Commit()
        sql, values = self.pool.GetSQLSelect(["id"], {"pool_type": "notype 123", "title": "test entry 123"}, dataTable="pool_meta", singleTable=1) 
        id = self.pool.Query(sql, values)
        self.assertFalse(id)


    def test_groups(self):
        userid = 123
        group = u"group:test"
        id = 1
        ref = u"o"
        self.pool.RemoveGroups(id=id)
        self.assertFalse(self.pool.GetGroups(id, userid, group))
        self.assertFalse(self.pool.GetGroups(id))
        self.pool.AddGroup(id, userid, group)
        self.assert_(self.pool.GetGroups(id, userid, group))
        self.assert_(self.pool.GetGroups(id))
        
        self.pool.RemoveGroups(userid=userid, group=group, id=id)
        self.assertFalse(self.pool.GetGroups(id, userid, group))




    def test_search_files(self):

        t = time()
        c = self.statdb()

        # creating
        id1=self.create1()
        id2=self.create1()
        id3=self.create1()

        #update data
        self.set1(id1)
        self.setfile1(id1)
        self.setfile2(id1)

        self.set1(id2)
        self.setfile1(id2)
        self.setfile2(id2)

        self.set1(id3)
        self.setfile1(id3)
        self.setfile2(id3)

        dbfile = self.pool
        #print "SearchFilename",
        f1 = dbfile.SearchFilename(u"file1.txt")
        #print len(f1),
        self.assert_(len(f1)>=3)
        f2 = dbfile.SearchFilename(u"file2.txt")
        #print len(f2),
        self.assert_(len(f2)>=3)
        f3 = dbfile.SearchFilename(u"fileXXX.txt")
        #print len(f3),
        self.assert_(len(f3)==0)
        f4 = dbfile.SearchFilename(u"file%")
        #print len(f4),
        if countdb == 0:
            self.assert_(len(f4)>=len(f1)+len(f2))
        #print "OK"

        #print "SearchFiles",
        parameter={u"id": (id1,id2,id3)}
        operators={u"id": u"IN"}
        f = dbfile.SearchFiles(parameter, operators=operators) #sort="filename",
        #print len(f),
        if countdb==0:
            self.assert_(len(f)==6)
        parameter[u"filename"] = u"file2.txt"
        operators[u"filename"] = u"="
        f = dbfile.SearchFiles(parameter, operators=operators) #sort="size",
        #print len(f),
        if countdb==0:
            self.assert_(len(f)==3)
        #print "OK"

        # deleting
        self.delete(id1)
        self.delete(id2)
        self.delete(id3)
        c3 = self.statdb()
        self.assert_(c==c3)


    def test_tree(self):
        base = self.pool
        #base.GetContainedIDs(base=0, sort=u"title", parameter=u"")
        #base.GetTree(flds=[u"id"], sort=u"title", base=0, parameter=u"")
        base.GetParentPath(1)
        base.GetParentTitles(1)





class Sqlite3Test(dbTest, unittest.TestCase):
    """
    """
    def setUp(self):
        self.pool = getPool()
        dbfile = DvPath(conn["dbName"])
        if not dbfile.IsFile():
            dbfile.CreateDirectories()
        self.checkdb()
        self.connect()

    def tearDown(self):
        self.pool.Close()

    def connect(self):
        #print "Connect DB on", conn["host"],
        self.pool.CreateConnection(conn)
        self.assert_(self.pool.connection.IsConnected())
        #print "OK"

    

if __name__ == '__main__':
    unittest.main()


