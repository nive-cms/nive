#-*- coding: utf-8 -*-

import time
import unittest

from nive import OperationalError
from nive.utils.path import *

from nive.application import *
from nive.definitions import *
from nive.helper import *
from nive.portal import Portal
from nive.security import User

from nive.components.objects.base import ApplicationBase

# real database test configuration
# change these to fit your system
dbconf = DatabaseConf(
    dbName = "/var/tmp/nive/nive.db", #":memory:"
    fileRoot = "/var/tmp/nive",
    context = "Sqlite3"
)

root = RootConf(
    id = u"root",
    name = u"Data root",
    default = 1,
    context = "nive.components.objects.base.RootBase",
    subtypes = [IObject]
)

type1 = ObjectConf(
    id = u"type1",
    name = u"Type 1 container",
    hidden = False,
    dbparam = u"data1",
    context = "nive.components.objects.base.ObjectContainerBase",
    subtypes = [IObject]
)
type1.data = [
    FieldConf(id="ftext", datatype="text", size=1000, name=u"ftext", fulltext=1),
    FieldConf(id="fnumber", datatype="number", size=8, name=u"fnumber", required=1),
    FieldConf(id="fdate", datatype="datetime", size=8, name=u"fdate"),
    FieldConf(id="flist", datatype="list", size=100, name=u"flist", listItems=[{"id": u"item 1", "name":u"Item 1"},{"id": u"item 2", "name":u"Item 2"},{"id": u"item 3", "name":u"Item 3"}]),
    FieldConf(id="fmselect", datatype="mselection", size=50, name=u"fmselect"),
    FieldConf(id="funit", datatype="unit", size=8, name=u"funit"),
    FieldConf(id="funitlist", datatype="unitlist", size=100, name=u"funitlist")
]

type2 = ObjectConf(
    id = u"type2",
    name = u"Type 2 Object",
    hidden = True,
    dbparam = u"data2",
    context = "nive.components.objects.base.ObjectBase",
    subtypes = None
)
data2 = []
data2.append(FieldConf(**{"id":u"fstr", "datatype": "string", "size": 100, "name": u"fstr", "fulltext": 1}))
data2.append(FieldConf(**{"id":u"ftext", "datatype": "text", "size": 1000, "name": u"ftext"}))
data2.append(FieldConf(**{"id":u"file1", "datatype": "file", "size": 5*1024*1024, "name": u"file1"}))
data2.append(FieldConf(**{"id":u"file2", "datatype": "file", "size": 500*1024, "name": u"file2"}))
type2.data = data2

type3 = ObjectConf(
    id = u"type3",
    name = u"Type 3 Object",
    hidden = True,
    dbparam = u"data3",
    context = "nive.components.objects.base.ObjectContainerBase",
    subtypes = [INonContainer]
)
data3 = []
data3.append(FieldConf(**{"id":u"fstr", "datatype": "string", "size": 100, "name": u"fstr", "fulltext": 1}))
type3.data = data3

cat1 = CategoryConf(**{u"id":u"cat1", u"name":u"Category 1"})
cat2 = CategoryConf(**{u"id":u"cat2", u"name":u"Category 2"})

group1 = GroupConf(**{u"id":u"group1", u"name":u"Group 1"})
group2 = GroupConf(**{u"id":u"group2", u"name":u"Group 2"})

# configuration
appconf = AppConf(
    id = u"unittest",
    context="nive.components.objects.base.ApplicationBase",
    title = u"nive application python unittest",
    modules = [root, type1, type2, type3],
    meta = [FieldConf(id="testfld", datatype="number", size=4, name=u"Number")],
    categories = [cat1, cat2],
    groups = [group1, group2],
    fulltextIndex = True
)


# test data -----------------------------------------------------------------------
data1_1 = { u"ftext": "this is text!",
            u"fnumber": 123456,
            u"fdate": "2008/06/23 16:55:00",
            u"flist": "item 1, item 2, item 3",
            u"fmselect": "item 5",
            u"funit": 35,
            u"funitlist": "34, 35, 36",
            u"title":"äüöß and others",
            u"pool_type": "type1",
            u"pool_category": "cat1"}
data2_1 = { u"fstr": u"this is sting!",
            u"ftext": u"this is text!",
            u"title": u"äüöß and others",
            u"pool_type": u"type2",
            u"pool_category": u"cat2"}
data3_1 = { u"title": u"title data 3",
            u"fstr": u"testing type 3!"}

data1_2 = { u"ftext": "this is a new text!",
            u"funit": 0,
            u"title":"new title data 1"}
data2_2 = { u"fstr": "this is new sting!",
            u"title": "new title data 2"}

file2_1_data="This is the text in the first file"
file2_2_data=u"This is the text in the second file"
file2_1 = {"filename":"file1.txt", "file":file2_1_data}
file2_2 = {"filename":"file2.txt", "file":file2_2_data}


# empty -------------------------------------------------------------------------
def app_db(modules=None):
    a = ApplicationBase()
    a.Register(appconf)
    a.Register(dbconf)
    if modules:
        for m in modules:
            a.Register(m)
    p = Portal()
    p.Register(a, "nive")
    a.LoadConfiguration()
    dbfile = DvPath(a.dbConfiguration.dbName)
    if not dbfile.IsFile():
        dbfile.CreateDirectories()
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

def app_nodb():
    a = ApplicationBase()
    a.Register(appconf)
    a.Register(DatabaseConf())
    p = Portal()
    p.Register(a, "nive")
    a.LoadConfiguration()
    try:
        a.Startup(None)
    except OperationalError:
        pass
    return a

def emptypool(app):
    db = app.db
    db.Query(u"delete FROM pool_wflog")
    db.Query(u"delete FROM pool_wfdata")
    #db.Query(u"delete FROM pool_security")
    db.Query(u"delete FROM pool_meta")
    #db.Query(u"delete FROM pool_lroles")
    db.Query(u"delete FROM pool_fulltext")
    db.Query(u"delete FROM pool_files")
    db.Query(u"delete FROM pool_sys")
    db.Query(u"delete FROM data2")
    db.Query(u"delete FROM data1")
    DvDirCleaner(str(db.root)).DeleteFiles(subdirectories = True)
    db.root.CreateDirectories()

def createpool(path,app):
    path.CreateDirectories()
    app.GetTool("nive.components.tools.dbStructureUpdater")()


def statdb(app):
    c = app.db.GetCountEntries()
    countdb = c
    ##print "Count entries in DB:", c
    return c

def root(a):
    r = a.GetRoot("root")
    return r

def createObj1(c):
    type = u"type1"
    data = data1_1
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def createObj2(c):
    type = u"type2"
    data = data2_1
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def createObj3(c):
    type = u"type3"
    data = data3_1
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def createObj1file(c):
    type = "type1"
    data = data1_1.copy()
    data["file1"] = File(**file2_1)
    data["file2"] = File(**file2_2)
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def createObj2file(c):
    type = u"type2"
    data = data2_1.copy()
    data["file2"] = File(**file2_1)
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def maxobj(r):
    id = a.GetMaxID()
    return r.LookupObj(id)
