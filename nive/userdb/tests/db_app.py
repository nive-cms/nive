# -*- coding: utf-8 -*-

import time
import unittest

from nive.helper import *
from nive.utils.path import DvPath
from nive.definitions import *
from nive.security import *
from nive.portal import Portal
from nive.userdb.app import UserDB

dbconf = DatabaseConf(
    dbName = "/var/tmp/nivecms/users.db", #":memory:"
    fileRoot = "/var/tmp/nivecms",
    context = "Sqlite3"
)
appconf = AppConf("nive.userdb.app")
appconf.modules.append("nive.userdb.userview.view")
appconf.modules.append("nive.components.tools.sendMail")

def app():
    a = UserDB(appconf)
    a.dbConfiguration=dbconf
    p = Portal()
    p.Register(a)
    a.Startup(None)
    dbfile = DvPath(a.dbConfiguration.dbName)
    if not dbfile.IsFile():
        dbfile.CreateDirectories()
    try:
        a.Query("select id from pool_meta where id=1")
        a.Query("select id from data1 where id=1")
        a.Query("select id from data2 where id=1")
        a.Query("select id from data3 where id=1")
        a.Query("select id from pool_files where id=1")
    except:
        a.GetTool("nive.components.tools.dbStructureUpdater")()
    return a

def app_nodb():
    a = WebsitePublisher(appconf)
    a.dbConfiguration=DatabaseConf()
    p = Portal()
    p.Register(a)
    a.Startup(None)
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
    db.Query(u"delete FROM data2")
    db.Query(u"delete FROM data1")
    DvDirCleaner(str(db.root)).DeleteFiles(subdirectories = true)
    db.root.CreateDirectories()

def createpool(path,app):
    path.CreateDirectories()
    app.GetTool("nive.components.tools.dbStructureUpdater")()

def create_user(name,email):
    type = "user"
    data = {"name": name, "password": "11111", "email": email, "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
    user = User("test")
    r = a.GetRoot()
    o = r.Create(type, data = data, user = user)
    #o.Commit()
    return o

