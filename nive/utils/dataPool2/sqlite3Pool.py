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
Data Pool Sqlite Module
----------------------
*Requires python-sqlite*
"""

import string, time, re, os
from types import *

import sqlite3

from nive.utils.utils import STACKF
from nive.utils.dateTime import DvDateTime

from nive.utils.dataPool2.dbManager import Sqlite3Manager
from nive.utils.dataPool2.base import *

from nive.utils.dataPool2.files import FileManager
from nive.utils.dataPool2.files import FileEntry

from nive import OperationalError

DBEncoding = u"utf-8"


class Sqlite3(FileManager, Base):
    """
    Data Pool Sqlite3 implementation
    """
    _OperationalError = sqlite3.OperationalError


    def GetContainedIDs(self, base=0, sort=u"title", parameter=u""):
        """
        select list of all entries
        id needs to be first field, pool_unitref second
        """
        def _SelectIDs(base, ids, sql, cursor):
            cursor.execute(sql%(base))
            entries = cursor.fetchall()
            for e in entries:
                ids.append(e[0])
                ids = _SelectIDs(e[0], ids, sql, cursor)
            return ids
        parameter = u"where pool_unitref=%d " + parameter
        sql = u"""select id from %s %s order by %s""" % (self.MetaTable, parameter, sort)
        cursor = self.GetCursor()
        ids = _SelectIDs(base, [], sql, cursor)
        cursor.close()
        return ids


    def GetTree(self, flds=[u"id"], sort=u"title", base=0, parameter=u""):
        """
        select list of all entries
        id needs to be first field if flds
        """
        def _Select(base, tree, flds, sql, cursor):
            cursor.execute(sql%(base))
            entries = cursor.fetchall()
            for e in entries:
                data = self.ConvertRecToDict(e, flds)
                data.update({"id": e[0], "items": []})
                tree["items"].append(data)
                data = _Select(e[0], data, flds, sql, cursor)
            return tree

        if parameter != u"":
            parameter = u"and " + parameter
        parameter = u"where pool_unitref=%d " + parameter
        sql = u"""select %s from %s %s order by %s""" % (ConvertListToStr(flds), self.MetaTable, parameter, sort)
        cursor = self.GetCursor()
        tree = {"id":base, "items":[]}
        tree = _Select(base, tree, flds, sql, cursor)
        cursor.close()
        return tree
    
        
    def Query(self, sql, values = []):
        """
        execute a query on the database. texts are converted according to codepage settings.
        """
        c = self.GetCursor()
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        sql = self.DecodeText(sql)
        if values:
            v1 = []
            for v in values:
                if type(v) == StringType:
                    v1.append(self.DecodeText(v))
                else:
                    v1.append(v)
            values = v1
        try:
            c.execute(sql, values)
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        r = c.fetchall()
        c.close()

        set2 = []
        for rec in r:
            rec2 = []
            for d in rec:
                if type(d) == StringType:
                    rec2.append(self.EncodeText(d))
                else:
                    rec2.append(d)
            set2.append(rec2)
        return set2
    

    def QueryRaw(self, sql, values = []):
        """
        execute a query on the database.
        """
        c = self.GetCursor()
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        try:
            c.execute(sql, values)
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        l = c.fetchall()
        c.close()
        return l

        
    def _CreateNewID(self, table = u"", dataTbl = None):
        #[i]
        aC = self.GetCursor()
        if table == "":
            table = self.MetaTable
        if table == self.MetaTable:
            if not dataTbl:
                raise "Missing data table", "Entry not created"

            # sql insert empty rec in data table
            if self._debug:
                STACKF(0,u"INSERT INTO %s (id) VALUES(null)" % (dataTbl)+"\r\n",self._debug, self._log,name=self.name)
            aC.execute(u"INSERT INTO %s (id) VALUES(null)" % (dataTbl))
            # sql get id of created rec
            if self._debug:
                STACKF(0,u"SELECT last_insert_rowid()\r\n",0, self._log,name=self.name)
            aC.execute(u"SELECT last_insert_rowid()")
            dataref = aC.fetchone()[0]
            # sql insert empty rec in meta table
            if self._debug:
                STACKF(0,u"INSERT INTO %s (pool_datatbl, pool_dataref) VALUES ('%s', %s)"% (self.MetaTable, dataTbl, dataref),0, self._log,name=self.name)
            aC.execute(u"INSERT INTO %s (pool_datatbl, pool_dataref) VALUES ('%s', %s)"% (self.MetaTable, dataTbl, dataref))
            if self._debug:
                STACKF(0,u"SELECT last_insert_rowid()\r\n",0, self._log,name=self.name)
            aC.execute(u"SELECT last_insert_rowid()")
            aID = aC.fetchone()[0]
            aC.close()
            return aID, dataref

        # sql insert empty rec in meta table
        if self._debug:
            STACKF(0,u"INSERT INTO %s (id) VALUES(null)" % (table)+"\r\n",self._debug, self._log,name=self.name)
        aC.execute(u"INSERT INTO %s (id) VALUES(null)" % (table))
        # sql get id of created rec
        if self._debug:
            STACKF(0,u"SELECT last_insert_rowid()\r\n",0, self._log,name=self.name)
        aC.execute(u"SELECT last_insert_rowid()")
        aID = aC.fetchone()[0]
        aC.close()
        return aID, 0


    def _CreateFixID(self, id, dataTbl):
        if self.IsIDUsed(id):
            self._Error(-100)
            return None
        aC = self.GetCursor()
        ph = self.GetPlaceholder()
        if not dataTbl:
            raise TypeError, "Missing data table."

        # sql insert empty rec in data table
        if self._debug:
            STACKF(0,u"INSERT INTO %s (id) VALUES(null)" % (dataTbl)+"\r\n",self._debug, self._log,name=self.name)
        aC.execute(u"INSERT INTO %s (id) VALUES(null)" % (dataTbl))
        # sql get id of created rec
        if self._debug:
            STACKF(0,u"SELECT last_insert_rowid()\r\n",0, self._log,name=self.name)
        aC.execute(u"SELECT last_insert_rowid()")
        dataref = aC.fetchone()[0]
        # sql insert empty rec in meta table
        if self._debug:
            STACKF(0,u"INSERT INTO %s (id, pool_datatbl, pool_dataref) VALUES (%d, '%s', %s)"% (self.MetaTable, id, dataTbl, dataref),0, self._log,name=self.name)
        aC.execute(u"INSERT INTO %s (id, pool_datatbl, pool_dataref) VALUES (%d, '%s', %s)"% (self.MetaTable, id, dataTbl, dataref))
        if self._debug:
            STACKF(0,u"SELECT last_insert_rowid()\r\n",0, self._log,name=self.name)
        aC.execute(u"SELECT last_insert_rowid()")
        aID = aC.fetchone()[0]
        aC.close()
        return id, dataref

    #[i] types/classes -------------------------------------------------------------------

    def CreateConnection(self, connParam):
        #[i]
        self.conn = Sqlite3Conn(connParam)
        if not self.name:
            self.name = connParam.get("dbName",u"")


    def GetDBDate(self, date=None):
        #[i]
        if not date:
            return DvDateTime(time.localtime()).GetDBMySql()
        return DvDateTime(str(date)).GetDBMySql()


    def GetPlaceholder(self):
        return u"?"

    
    def _GetDefaultDBEncoding(self):
        return DBEncoding


    def _GetPoolEntry(self, id, **kw):
        try:
            return Sqlite3Entry(self, id, **kw)
        except NotFound:
            return None


    def _GetEntryClassType(self):
        return Sqlite3Entry





class Sqlite3Entry(FileEntry, Entry):
    """
    Data Pool Entry Sqlite3 implementation
    """






class Sqlite3ConnBase(Connection):
    """
    Sqlite connection handling class

    config parameter in dictionary:
    db = database path
    
    user = unused - database user
    password = unused - password user
    host = unused - host server
    port = unused - port server

    timeout is set to 3.
    """

    def __init__(self, config = None, connectNow = True):
        self.db = None
        self.dbName = u""
        
        self.user = u""
        self.host = u""
        self.password = u""
        self.port = u""
        self.unicode = True
        self.timeout = 3
        
        self.check_same_thread = False
        if(config):
            self.SetConfig(config)
        if(connectNow):
            self.Connect()


    def Connect(self):
        """[i] Close and connect to server """
        self.Close()
        if not self.dbName:
            raise OperationalError, "Connection failed. Database name is empty." 
        db = sqlite3.connect(self.dbName, check_same_thread=self.check_same_thread)
        if not db:
            raise OperationalError, "Cannot connect to database '%s'" % (self.dbName)
        c = db.cursor()
        c.execute("PRAGMA journal_mode = TRUNCATE")
        #c.execute("PRAGMA secure_delete = 0")
        #c.execute("PRAGMA temp_store = MEMORY")
        c.execute("PRAGMA synchronous = OFF")
        c.close()
        self._set(db)


    def IsConnected(self):
        """[i] Check if database is connected """
        try:
            db = self._get()
            return db.cursor()!=None
        except:
            return False
    

    def Ping(self):
        """[i] ping database server """
        return True


    def GetDBManager(self):
        """ returns the database manager obj """
        aDB = Sqlite3Manager()
        aDB.SetDB(self._get())
        return aDB


    def FmtParam(self, param):
        """??? format a parameter for sql queries like literal for  db"""
        #return self.db.literal(param)
        if type(param) in (IntType, LongType, FloatType):
            return unicode(param)
        d = unicode(param)
        if d.find(u'"')!=-1:
            d = d.replace(u'"',u'\\"')
        return u'"'+d+u'"'


    def Duplicate(self):
        """[i] Duplicates the current connection and returns a new unconnected connection """
        new = Sqlite3Conn(None, False)
        new.dbName = self.dbName
        return new


    def SetConfig(self, config):
        """[i] """
        self.dbName = config.get("dbName")



import threading

class Sqlite3Conn(Sqlite3ConnBase):
    """
    Stores database connections as thread locals.
    Usage is the same as Sqlite3 connection.
    """

    def __init__(self, config = None, connectNow = True):
        self.local = threading.local()
        Sqlite3ConnBase.__init__(self, config, False)
        self.check_same_thread = True
        if(connectNow):
            self.Connect()

    def _get(self):
        # get stored database connection
        if not hasattr(self.local, "db"):
            return None
        return self.local.db
        
    def _set(self, dbconn):
        # store database connection
        self.local.db = dbconn
        
    