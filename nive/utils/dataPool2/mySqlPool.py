#----------------------------------------------------------------------
# Nive CMS
# Copyright (C) 2012  Arndt Droullier, DV Electric, info@dvelectric.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#----------------------------------------------------------------------

__doc__ = """
Data Pool MySql Module

*Requires python-mysqldb*
"""


import string, re, os
from time import time, localtime
from types import *

import MySQLdb


from nive.utils.utils import STACKF
from nive.utils.dateTime import DvDateTime

from dbManager import MySQLManager
from base import *
from files import *


DBEncoding = u"utf-8"


class MySql(FileManager, Base):
    """
    Data Pool MySql 5 implementation
    """
    _OperationalError = MySQLdb.OperationalError
    _ProgrammingError = MySQLdb.ProgrammingError
    _Warning = MySQLdb.Warning


    def _CreateNewID(self, table = u"", dataTbl = None):
        #
        aC = self.connection.cursor()
        if table == u"":
            table = self.MetaTable
        if table == self.MetaTable:
            if not dataTbl:
                raise "Missing data table", "Entry not created"

            # sql insert empty rec in meta table
            if self._debug:
                STACKF(0,u"INSERT INTO %s () VALUES ()" % (dataTbl)+"\r\n",self._debug, self._log,name=self.name)
            try:
                aC.execute(u"INSERT INTO %s () VALUES ()" % (dataTbl))
            except self._Warning:
                pass
            # sql get id of created rec
            if self._debug:
                STACKF(0,u"SELECT LAST_INSERT_ID()\r\n",0, self._log,name=self.name)
            aC.execute(u"SELECT LAST_INSERT_ID()")
            dataref = aC.fetchone()[0]
            # sql insert empty rec in meta table
            if self._debug:
                STACKF(0,u"INSERT INTO %s (pool_datatbl, pool_dataref) VALUES ('%s', %s)"% (self.MetaTable, dataTbl, dataref),0, self._log,name=self.name)
            aC.execute(u"INSERT INTO %s (pool_datatbl, pool_dataref) VALUES ('%s', %s)"% (self.MetaTable, dataTbl, dataref))
            if self._debug:
                STACKF(0,u"SELECT LAST_INSERT_ID()\r\n",0, self._log,name=self.name)
            aC.execute(u"SELECT LAST_INSERT_ID()")
            aID = aC.fetchone()[0]
            aC.close()
            return aID, dataref

        # sql insert empty rec in meta table
        if self._debug:
            STACKF(0,u"INSERT INTO %s () VALUES ()" % (table)+"\r\n",self._debug, self._log,name=self.name)
        aC.execute(u"INSERT INTO %s () VALUES ()" % (table))
        # sql get id of created rec
        if self._debug:
            STACKF(0,u"SELECT LAST_INSERT_ID()\r\n",0, self._log,name=self.name)
        aC.execute(u"SELECT LAST_INSERT_ID()")
        aID = aC.fetchone()[0]
        aC.close()
        return aID, 0


    # types/classes -------------------------------------------------------------------

    def CreateConnection(self, connParam):
        #
        self._conn = MySqlConnThreadLocal(connParam)
        if not self.name:
            self.name = connParam.get("dbName",u"")


    def GetDBDate(self, date=None):
        #
        if not date:
            return DvDateTime(localtime()).GetDBMySql()
        return DvDateTime(str(date)).GetDBMySql()


    def GetPlaceholder(self):
        return u"%s"

    
    def _GetDefaultDBEncoding(self):
        return DBEncoding


    def _GetPoolEntry(self, id, **kw):
        try:
            return MySqlEntry(self, id, **kw)
        except NotFound:
            return None


    def _GetEntryClassType(self):
        return MySqlEntry

    def _GetConnection(self):
        return MySqlConnSingle


    # MySql 4 tree structure --------------------------------------------------------------

    def GetParentPath4(self, id):
        """
        MySql 4 version
        returns id references of parents for id.
        """
        sql = u"""
        SELECT p0.pool_unitref as ref1,p1.pool_unitref as ref2,p2.pool_unitref as ref3,p3.pool_unitref as ref4,p4.pool_unitref as ref5,p5.pool_unitref as ref6,p6.pool_unitref as ref7
        FROM %(meta)s p0, %(meta)s p1, %(meta)s p2, %(meta)s p3, %(meta)s p4, %(meta)s p5, %(meta)s p6
        WHERE  p0.id = %(id)d
        and    p1.id = p0.pool_unitref
        and IF(p1.pool_unitref > 0, p2.id = p1.pool_unitref, p2.id = p0.pool_unitref)
        and IF(p2.pool_unitref > 0, p3.id = p2.pool_unitref, p3.id = p0.pool_unitref)
        and IF(p3.pool_unitref > 0, p4.id = p3.pool_unitref, p4.id = p0.pool_unitref)
        and IF(p4.pool_unitref > 0, p5.id = p4.pool_unitref, p5.id = p0.pool_unitref)
        and IF(p5.pool_unitref > 0, p6.id = p5.pool_unitref, p6.id = p0.pool_unitref)
        Group by ref1""" % {"meta":self.MetaTable, "id":int(id)}
        t = self.Query(sql)
        parents = []
        if len(t) == 0:
            return parents
        cnt = 7
        for i in range(0, cnt-1):
            id = t[0]
            if id == 0:
                break
            parents.insert(0, id)
        return parents


    def GetParentTitles4(self, id):
        """
        MySql 4 version
        returns titles of parents for id.
        """
        sql = u"""
        SELECT p0.pool_unitref as ref1,p0.title as t1,p1.pool_unitref as ref2,p1.title as t2,p2.pool_unitref as ref3,p2.title as t3,p3.pool_unitref as ref4,p3.title as t4,p4.pool_unitref as ref5,p4.title as t5,p5.pool_unitref as ref6,p5.title as t6,p6.pool_unitref as ref7,p6.title as t7
        FROM %(meta)s p0, %(meta)s p1, %(meta)s p2, %(meta)s p3, %(meta)s p4, %(meta)s p5, %(meta)s p6
        WHERE  p0.id = %(id)d
        and    p1.id = p0.pool_unitref
        and IF(p1.pool_unitref > 0, p2.id = p1.pool_unitref, p2.id = p0.pool_unitref)
        and IF(p2.pool_unitref > 0, p3.id = p2.pool_unitref, p3.id = p0.pool_unitref)
        and IF(p3.pool_unitref > 0, p4.id = p3.pool_unitref, p4.id = p0.pool_unitref)
        and IF(p4.pool_unitref > 0, p5.id = p4.pool_unitref, p5.id = p0.pool_unitref)
        and IF(p5.pool_unitref > 0, p6.id = p5.pool_unitref, p6.id = p0.pool_unitref)
        Group by ref1""" % {"meta":self.MetaTable, "id":int(id)}
        t = self.Query(sql)
        parents = []
        if len(t) == 0:
            return parents
        cnt = 4
        for i in range(1, cnt-1):
            title = t[0][i*2+1]
            parents.insert(0, self.EncodeText(title))
            if t[0][i*2] == 0:
                break
        return parents





class MySqlEntry(FileEntry, Entry):
    """
    Data Pool Entry MySql 5 implementation
    """



class MySqlConnSingle(Connection):
    """
    MySql connection handling class

    config parameter in dictionary:
    user = database user
    password = password user
    host = host mysql server
    port = port mysql server
    db = initial database name

    timeout is set to 3.
    """

    def connect(self):
        """ Close and connect to server """
        self.close()
        use_unicode = self.unicode
        charset = None
        if use_unicode:
            charset = u"utf8"
        db = MySQLdb.connect(self.host, self.user, self.password, self.dbName, connect_timeout=self.timeout, use_unicode=use_unicode, charset=charset)
        if not db:
            raise OperationalError, "Cannot connect to database '%s.%s'" % (self.host, self.dbName)
        self._set(db)
        

    def RawConnection(self):
        """ This function will return a new and raw connection. It is up to the caller to close this connection. """
        use_unicode = self.unicode
        charset = None
        if use_unicode:
            charset = u"utf8"
        db = MySQLdb.connect(self.host, self.user, self.password, self.dbName, connect_timeout=self.timeout, use_unicode=use_unicode, charset=charset)
        return db


    def IsConnected(self):
        """ Check if database is connected """
        try:
            db = self._get()
            db.ping()
            return db.cursor()!=None
        except:
            return False


    def GetDBManager(self):
        """ returns the database manager obj """
        self.VerifyConnection()
        aDB = MySQLManager()
        aDB.SetDB(self._get())
        return aDB


    def GetPlaceholder(self):
        return u"%s"

    
    def FmtParam(self, param):
        """format a parameter for sql queries like literal for mysql db"""
        db = self._get()
        if not db:
            self.connect()
            db = self._get()
        return db.literal(param)


    def Duplicate(self):
        """ Duplicates the current connection and returns a new unconnected connection """
        new = MySqlConn(None, False)
        new.user = self.user
        new.host = self.host
        new.password = self.password
        new.port = self.port
        new.dbName = self.dbName
        return new


import threading

class MySqlConnThreadLocal(MySqlConnSingle, ConnectionThreadLocal):
    """
    Stores database connections as thread locals.
    Usage is the same as MySqlConn connection.
    """

    def __init__(self, config = None, connectNow = True):
        self.local = threading.local()
        MySqlConnSingle.__init__(self, config, connectNow)




class PoolBakup:

    def __init__(self, pool, path=u""):
        self.pool = pool
        self.path = path
        self.dump = u""
        self.rotation = u"timestamp"


    def SetDirectoryRotation(self, tag):
        self.rotation = tag


    def SQLDump(self):
        path = self._GetPath(u"sql")
        user = self.pool.connection.user
        password = self.pool.connection.password
        database = self.pool.connection.dbName

        scrp = DvPath(u"mysqldump")
        cmd = u"""--user=%(user)s --password=%(password)s --database %(database)s --opt --allow-keywords --complete-insert -c > %(path)s""" % {"path": path, "user": user, "password": password, "database": database}
        r = scrp.Execute(cmd, returnStream = False)
        return r, path


    def SQLArchive(self, deleteSrc=False):
        path = DvPath(self._GetPath(u"sql"))
        name = path.GetLastDirectory()
        path.SetNameExtension(u"")
        path.RemoveLastDirectory()
        path.SetName(name)
        path.SetExtension(u"tgz")
        scrp = DvPath(u"tar")
        cmd = u"""cvzf %(path)s %(base)s""" % {u"path": path, u"base": self.dump}
        r = scrp.Execute(cmd, returnStream = False)
        if path.Exists() and deleteSrc:
            folder = DvPath(self.dump)
            folder.Delete(true)
        return r, path


    def _GetPath(self, tag):
        if self.dump == u"":
            base = self.path
            if base == u"":
                base = DvPath(self.pool.root)
                base.AppendDirectory(u"_bakup")
            else:
                base = DvPath(base)
            base.AppendDirectoryRotation(self.rotation)
            base.CreateDirectories()
            self.dump = str(base)
        else:
            base = DvPath(self.dump)
        if tag == u"sql":
            base.SetName(self.pool.connection.dbName)
            base.SetExtension(u"sql")
            return str(base)

        if tag == u"files":
            base.AppendDirectory(u"files")
            base.CreateDirectories()
            return str(base)
        return u""





