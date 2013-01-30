#----------------------------------------------------------------------
# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
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

__doc__ = ""


import os, sys
import string, time, cPickle, re, types
from datetime import datetime

from nive.utils.path import DvPath
from nive.utils.utils import ConvertToDateTime


MYSQL = 0
SQLITE3 = 0

try:    
    import sqlite3
    SQLITE3 = 1
except:
    pass

try:    
    import MySQLdb
    MYSQL = 1
except:    
    pass 
    #print "MySQLdb not imported!"



class MySQLManager(object):
    """
    """

    modifyColumns = True

    def __init__(self):
        import MySQLdb
        self.db = None
        self.dbConn = None
        self.engine = "MyISAM"
        self.useUtf8 = True

    # Database Options ---------------------------------------------------------------------

    def Connect(self, databaseName = "", inIP = "", inUser = "", inPW = ""):
        self.dbConn = MySQLdb.connect(db = databaseName, host = inIP, user = inUser, passwd = inPW)
        self.db = self.dbConn.cursor()
        return self.db != None


    def SetDB(self, inDB):
        self.dbConn = inDB
        self.db = self.dbConn.cursor()
        return self.db != None


    def Close(self):
        try:
            self.dbConn.close()
            self.db.close()
        except:
            pass
        self.db = None


    def IsDB(self):
        return self.db != None


    # Options ----------------------------------------------------------------

    def ConvertDate(self, date):
        if not isinstance(date, datetime):
            date = ConvertToDateTime(date)
        if not date:
            return u""
        return date.strftime(u"%Y-%m-%d %H:%M:%S")


    def UpdateStructure(self, tableName, structure, modify = None):
        """
        modify = None to skip changing existing columns, list of column ids to modify if changed
        """
        # check table exists
        if not self.IsTable(tableName):
            if not self.CreateTable(tableName, inColumns=structure):
                return False
            # delay until table is created
            time.sleep(0.3)
            aCnt = 1
            while not self.IsTable(tableName):
                time.sleep(0.5)
                aCnt += 1
                if aCnt == 10:
                    raise OperationalError, "timeout create table"
            return True

        columns = self.GetColumns(tableName, structure)

        for col in structure:
            name = col["id"]
            options = self.ConvertConfToColumnOptions(col)

            # skip id column
            if name == u"id":
                continue

            if not self.IsColumn(tableName, name):
                if not self.CreateColumn(tableName, name, options):
                    return False
                continue

            if not modify:
                continue

            if not name in modify:
                continue

            # modify column settings
            if name in columns and columns["name"].get("db"):
                if not self.ModifyColumn(tableName, name, u"", options):
                    return False
            else:
                if not self.CreateColumn(tableName, name, options):
                    return False

        return True


    def ConvertConfToColumnOptions(self, conf):
        """
        field representation:
        {"id": "type", "datatype": "list", "size"/"maxLen": 0, "default": ""}

        datatypes:
        list -> list || listn

        string -> VARCHAR(size) NOT NULL DEFAULT default
        number -> INT NOT NULL DEFAULT default
        float -> FLOAT NOT NULL DEFAULT default
        bool -> TINYINT(4) NOT NULL DEFAULT default
        percent -> TINYINT(4) NOT NULL DEFAULT default
        text -> TEXT NOT NULL DEFAULT default
        htext -> TEXT NOT NULL DEFAULT default
        lines -> TEXT NOT NULL DEFAULT default
        xml -> TEXT NOT NULL DEFAULT default
        unit -> INT NOT NULL DEFAULT default
        unitlist -> VARCHAR(2048) NOT NULL DEFAULT default
        date -> DATE NULL DEFAULT default
        datetime -> DATETIME NULL DEFAULT default
        timestamp -> TIMESTAMP
        listt -> VARCHAR(30) NOT NULL DEFAULT default
        listn -> SMALLINT NOT NULL DEFAULT default
        mselection, mcodelist, mcheckboxes -> VARCHAR(2048) NOT NULL DEFAULT default
        json -> TEXT
        [file] -> BLOB
        [bytesize] -> BIGINT(20) NOT NULL DEFAULT default
        url -> TEXT NOT NULL DEFAULT default
        """
        datatype = conf["datatype"]
        aStr = ""

        # convert datatype list
        if datatype == "list":
            if isinstance(conf["default"], basestring):
                datatype = "listt"
            else:
                datatype = "listn"

        if datatype in ("string", "email", "password"):
            if conf.get("size", conf.get("maxLen",0)) <= 3:
                aStr = u"CHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])
            else:
                aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype in ("number", "long", "int"):
            aN = conf["default"]
            if aN == u"" or aN == u" " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = long(aN)
            if conf.get("size", conf.get("maxLen",0)) == 4:
                aStr = u"TINYINT(4) NOT NULL DEFAULT %d" % (aN)
            elif conf.get("size", conf.get("maxLen",0)) >16:
                aStr = u"BIGINT(20) NOT NULL DEFAULT %d" % (aN)
            else:
                aStr = u"INT NOT NULL DEFAULT %d" % (aN)

        elif datatype == "float":
            aN = conf["default"]
            if aN == u"" or aN == u" " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = float(aN)
            aStr = u"FLOAT NOT NULL DEFAULT %d" % (aN)

        elif datatype == "bool":
            aN = conf["default"]
            if aN == u"" or aN == u" " or aN == None or aN == u"False":
                aN = 0
            if aN == u"True":
                aN = 1
            if isinstance(aN, basestring):
                aN = int(aN)
            aStr = u"TINYINT(4) NOT NULL DEFAULT %d" % (aN)

        elif datatype in ("text", "htext", "url", "urllist", "json", "code"):
            aStr = u"TEXT NOT NULL" # DEFAULT '%s'" % (conf["default"])

        elif datatype == "unit":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = long(aN)
            aStr = u"INT UNSIGNED NOT NULL DEFAULT %d" % (aN)

        elif datatype == "unitlist":
            aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "date":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = u"NULL"
            if aD in ("now", "nowdate", "nowtime"):
                aD = u""
            if isinstance(aD, basestring) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == u"":
                aStr = u"DATE NULL"
            else:
                aStr = u"DATE NULL DEFAULT '%s'" % (aD)

        elif datatype == "datetime":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = u"NULL"
            if aD in ("now", "nowdate", "nowtime"):
                aD = u""
            if isinstance(aD, basestring) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == u"":
                aStr = u"DATETIME NULL"
            else:
                aStr = u"DATETIME NULL DEFAULT '%s'" % (aD)

        elif datatype == "timestamp":
            aStr = u"TIMESTAMP"

        elif datatype == "listt":
            aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "listn" or datatype == "codelist":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = int(aN)
            aStr = u"SMALLINT(6) NOT NULL DEFAULT %d" % (aN)

        elif datatype == "mselection" or datatype == "mcheckboxes" or datatype == "mcodelist" or datatype == "radio":
            aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "file":
            aStr = u"BLOB"

        elif datatype == "bytesize":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = long(aN)
            aStr = u"BIGINT(20) NOT NULL DEFAULT %d" % (aN)

        return aStr


    # Database ------------------------------------------------------------

    def IsDatabase(self, databaseName):
        for aD in self.GetDatabases():
            if aD[0] == databaseName:
                return True
        return False

    def CreateDatabase(self, databaseName):
        if not self.IsDB():
            return False
        self.db.execute(u"create database " + databaseName)
        self.dbConn.commit()
        return True


    def UseDatabase(self, databaseName):
        if not self.IsDB():
            return False
        #self.db.execute(u"use " + databaseName)
        return True


    # Table --------------------------------------------------------------
    """
    inTableEntrys --> ColumnName ColumnDataTyp ColumnOptions
    ColumnOptions --> [NOT][NULL][DEFAULT = ""][PRIMARY KEY][UNIQUE]

    ENGINE = MyISAM
    CHARACTER SET utf8 COLLATE utf8_general_ci;

    ENGINE = InnoDB
    CHARACTER SET utf8 COLLATE utf8_general_ci;
    """

    def IsTable(self, tableName):
        for aD in self.GetTables():
            if string.lower(aD[0]) == string.lower(tableName):
                return True
        return False


    def CreateTable(self, tableName, inColumns = None, inCreateIdentity = True, primaryKeyName="id"):
        if not self.IsDB():
            return False
        if not tableName or tableName == "":
            return False
        assert(tableName != "user")
        aSql = u""
        if inCreateIdentity:
            aSql = u"CREATE TABLE %s(%s INT UNSIGNED AUTO_INCREMENT UNIQUE NOT NULL PRIMARY KEY" % (tableName, primaryKeyName)
            if inColumns:
                for c in inColumns:
                    if c.id == primaryKeyName:
                        continue
                    aSql += ","
                    aSql += c.id + u" " + self.ConvertConfToColumnOptions(c)
            aSql += u")"
            aSql += u" AUTO_INCREMENT = 1 "
        else:
            aSql = u"CREATE TABLE %s" % (tableName)
            if not inColumns:
                raise ConfigurationError, "No database fields defined."
            aCnt = 0
            aSql += u"("
            for c in inColumns:
                if aCnt:
                    aSql += u","
                aCnt = 1
                aSql += c.id + u" " + self.ConvertConfToColumnOptions(c)
            aSql += u")"
        aSql += u" ENGINE = %s" %(self.engine)
        if self.useUtf8:
            aSql += u" CHARACTER SET utf8 COLLATE utf8_general_ci"

        self.db.execute(aSql)
        # delay until table is created
        time.sleep(0.3)
        aCnt = 1
        while not self.IsTable(tableName):
            time.sleep(0.5)
            aCnt += 1
            if aCnt == 30:
                return False
        return True

    def RenameTable(self, inTableName, inNewTableName):
        if not self.IsDB():
            return False
        self.db.execute(u"alter table %s rename as %s" % (inTableName, inNewTableName))
        return True


    def DeleteTable(self, inTableName):
        if not self.IsDB():
            return False
        self.db.execute(u"drop table %s" % (inTableName))
        return True

    # Columns --------------------------------------------------------------
    """
    inColumnData --> "ColumnName ColumnDatdatatype ColumnOptions"
        Column Options --> [Not] [NULL] [DEFAULT 'default']
    SetPrimaryKey&SetUnique --> can also get a ColumnList
        ColumnList --> ColumnName1,ColumName2,...
    """

    def IsColumn(self, tableName, columnName):
        columns = self.GetColumns(tableName)
        cn = columnName
        if cn in columns and columns[cn].get("db"):
            return True
        return False


    def CreateColumn(self, tableName, columnName, columnOptions):
        if not self.IsDB():
            return False
        #print("alter table %s add column %s %s" % (tableName, columnName, columnOptions))
        if columnOptions == "" or columnName == "" or tableName == "":
            return False
        if columnOptions == "identity":
            return self.CreateIdentityColumn(tableName, columnName)
        self.db.execute(u"alter table %s add column %s %s" % (tableName, columnName, columnOptions))
        return True


    def CreateIdentityColumn(self, tableName, columnName):
        if not self.IsDB():
            return False
        return self.CreateColumn(tableName, columnName, u"INT UNSIGNED AUTO_INCREMENT UNIQUE NOT NULL PRIMARY KEY")


    def ModifyColumn(self, tableName, columnName, inNewColumnName, columnOptions):
        if not self.IsDB():
            return False
        #print("alter table %s change %s %s %s" % (tableName, columnName, inNewColumnName, columnOptions))
        if columnOptions == "" or columnName == "" or tableName == "":
            return False
        aN = inNewColumnName
        if aN == "":
            aN = columnName
        self.db.execute(u"alter table %s change %s %s %s" % (tableName, columnName, aN, columnOptions))
        return True


    # physical database structure ----------------------------------------------------------------

    def GetDatabases(self):
        if not self.IsDB():
            return ""
        self.db.execute(u"show databases")
        return self.db.fetchall()


    def GetTables(self):
        if not self.IsDB():
            return ""
        self.db.execute(u"show tables")
        return self.db.fetchall()


    def GetColumns(self, tableName, structure=None):
        """
        returns a dict of columns. each column is represented by and stored und column id:
        {db: {id, type, identity, default, null}, conf: FieldConf()}
        """
        if not self.IsDB():
            return []
        if not self.IsTable(tableName):
            return []
        self.db.execute(u"show columns from %s" % (tableName))
        table = {}
        for c in self.db.fetchall():
            table[c[0]] = {"db": {"id": c[0], "type": c[1], "identity": c[3]!="", "default": c[4], "null": ""}, 
                           "conf": None} 
        if structure:
            for conf in structure:
                if conf.id in table:
                    table[conf.id]["conf"] = conf
                else:
                    table[conf.id] = {"db": None, "conf": conf} 
        return table



    
    
    
class Sqlite3Manager(MySQLManager):
    """
    """
    modifyColumns = True #False

    def __init__(self):
        import sqlite3
        self.db = None
        self.dbConn = None
        self.useUtf8 = True


    def Connect(self, databaseName = ""):
        self.dbConn = sqlite3.connect(databaseName)
        self.db = self.dbConn.cursor()
        return self.db != None


    # Options ----------------------------------------------------------------

    def ConvertConfToColumnOptions(self, conf):
        """
        field representation:
        {"id": "type", "datatype": "list", "size"/"maxLen": 0, "default": ""}

        datatypes:
        list -> list || listn

        string -> VARCHAR(size) NOT NULL DEFAULT default
        number -> INT NOT NULL DEFAULT default
        float -> FLOAT NOT NULL DEFAULT default
        bool -> TINYINT(4) NOT NULL DEFAULT default
        percent -> TINYINT(4) NOT NULL DEFAULT default
        text -> TEXT NOT NULL DEFAULT default
        htext -> TEXT NOT NULL DEFAULT default
        lines -> TEXT NOT NULL DEFAULT default
        xml -> TEXT NOT NULL DEFAULT default
        unit -> INT NOT NULL DEFAULT default
        unitlist -> VARCHAR(2048) NOT NULL DEFAULT default
        date -> TIMESTAMP NULL DEFAULT default
        datetime -> TIMESTAMP NULL DEFAULT default
        timestamp -> TIMESTAMP
        listt -> VARCHAR(30) NOT NULL DEFAULT default
        listn -> SMALLINT NOT NULL DEFAULT default
        mselection, mcodelist, mcheckboxes -> VARCHAR(2048) NOT NULL DEFAULT default
        [file] -> BLOB
        [bytesize] -> BIGINT(20) NOT NULL DEFAULT default
        url -> TEXT NOT NULL DEFAULT default
        """
        datatype = conf["datatype"]
        aStr = u""

        # convert datatype list
        if(datatype == "list"):
            if isinstance(conf["default"], basestring):
                datatype = "listt"
            else:
                datatype = "listn"

        if datatype in ("string", "email", "password"):
            if conf.get("size", conf.get("maxLen",0)) <= 3:
                aStr = u"CHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])
            else:
                aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype in ("number", "long", "int"):
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = long(aN)
            if conf.get("size", conf.get("maxLen",0)) == 4:
                aStr = u"TINYINT NOT NULL DEFAULT %d" % (aN)
            elif conf.get("size", conf.get("maxLen",0)) in (11,12):
                aStr = u"INTEGER NOT NULL DEFAULT %d" % (aN)
            else:
                aStr = u"INTEGER NOT NULL DEFAULT %d" % (aN)

        elif datatype == "float":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = float(aN)
            aStr = u"FLOAT NOT NULL DEFAULT %d" % (aN)

        elif datatype == "bool":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None or aN == "False":
                aN = 0
            if aN == "True":
                aN = 1
            if isinstance(aN, basestring):
                aN = int(aN)
            aStr = u"TINYINT NOT NULL DEFAULT %d" % (aN)

        elif datatype in ("text", "htext", "url", "urllist", "json", "code"):
            aStr = u"TEXT NOT NULL DEFAULT '%s'" % (conf["default"])

        elif datatype == "unit":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = long(aN)
            aStr = u"INTEGER NOT NULL DEFAULT %d" % (aN)

        elif datatype == "unitlist":
            aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "date":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = "NULL"
            if aD in ("now", "nowdate", "nowtime"):
                aD = ""
            if isinstance(aD, basestring) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == "":
                aStr = u"TIMESTAMP NULL"
            else:
                aStr = u"TIMESTAMP NULL DEFAULT '%s'" % (aD)

        elif datatype == "datetime":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = "NULL"
            if aD in ("now", "nowdate", "nowtime"):
                aD = ""
            if isinstance(aD, basestring) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == "":
                aStr = u"TIMESTAMP NULL"
            else:
                aStr = u"TIMESTAMP NULL DEFAULT '%s'" % (aD)

        elif datatype == "timestamp":
            aStr = u"TIMESTAMP DEFAULT (datetime('now','localtime'))"

        elif datatype == "listt":
            aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype in ("listn", "codelist"):
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = int(aN)
            aStr = "SMALLINT NOT NULL DEFAULT %d" % (aN)

        elif datatype in ("mselection", "mcheckboxes", "mcodelist", "radio"):
            aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "file":
            aStr = u"BLOB"

        elif datatype == "bytesize":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = long(aN)
            aStr = u"INTEGER NOT NULL DEFAULT %d" % (aN)

        return aStr



    # physical database structure ----------------------------------------------------------------

    def GetDatabases(self):
        return []


    def GetTables(self):
        if not self.IsDB():
            return []
        sql = u"""SELECT name FROM 
                   (SELECT * FROM sqlite_master UNION ALL
                    SELECT * FROM sqlite_temp_master)
                WHERE type='table'
                ORDER BY name"""
        self.db.execute(sql)
        return self.db.fetchall()


    def GetColumns(self, tableName, structure=None):
        """
        returns a dict of columns. each column is represented by and stored und column id:
        {db: {id, type, identity, default, null}, conf: FieldConf()}
        """
        if not self.IsDB():
            return []
        if not self.IsTable(tableName):
            return []
        self.db.execute(u"PRAGMA table_info(%s)" % (tableName))
        table = {}
        for c in self.db.fetchall():
            table[c[1]] = {"db": {"id": c[1], "type": c[2], "identity": c[5], "default": c[4], "null": c[3]}, 
                           "conf": None} 
        if structure:
            for conf in structure:
                if conf.id in table:
                    table[conf.id]["conf"] = conf
                else:
                    table[conf.id] = {"db": None, "conf": conf} 
        return table


    # Tables --------------------------------------------------------------
    """
    inTableEntrys --> ColumnName ColumnDataTyp ColumnOptions
    ColumnOptions --> [NOT][NULL][DEFAULT = ""][PRIMARY KEY][UNIQUE]
    """

    def IsTable(self, tableName):
        for aD in self.GetTables():
            if string.lower(aD[0]) == string.lower(tableName):
                return True
        return False


    def CreateTable(self, tableName, inColumns = None, inCreateIdentity = True, primaryKeyName="id"):
        if not self.IsDB():
            return False
        if not tableName or tableName == "":
            return False
        assert(tableName != "user")
        aSql = u""
        if inCreateIdentity:
            aSql = u"CREATE TABLE %s(%s INTEGER PRIMARY KEY AUTOINCREMENT" % (tableName, primaryKeyName)
            if inColumns:
                for c in inColumns:
                    if c.id == primaryKeyName:
                        continue
                    aSql += ","
                    aSql += c.id + u" " + self.ConvertConfToColumnOptions(c)
            aSql += u")"
        else:
            aSql = u"CREATE TABLE %s" % (tableName)
            if not inColumns:
                raise ConfigurationError, "No database fields defined."
            aCnt = 0
            aSql += u"("
            for c in inColumns:
                if aCnt:
                    aSql += u","
                aCnt = 1
                aSql += c.id + u" " + self.ConvertConfToColumnOptions(c)
            aSql += u")"
        self.db.execute(aSql)
        # delay until table is created
        time.sleep(0.3)
        aCnt = 1
        while not self.IsTable(tableName):
            time.sleep(0.5)
            aCnt += 1
            if aCnt == 30:
                return False
        return True

    def RenameTable(self, inTableName, inNewTableName):
        if not self.IsDB():
            return False
        self.db.execute(u"alter table %s rename to %s" % (inTableName, inNewTableName))
        return True



    # Columns --------------------------------------------------------------
    """
    inColumnData --> "ColumnName ColumnDatdatatype ColumnOptions"
        Column Options --> [Not] [NULL] [DEFAULT 'default']
    SetPrimaryKey&SetUnique --> can also get a ColumnList
        ColumnList --> ColumnName1,ColumName2,...
    """

    def CreateColumn(self, tableName, columnName, columnOptions=""):
        if not self.IsDB():
            return False
        if columnName == "" or tableName == "":
            return False
        if columnOptions == "identity":
            return self.CreateIdentityColumn(tableName, columnName)
        self.db.execute(u"alter table %s add column %s %s" % (tableName, columnName, columnOptions))
        return True


    def CreateIdentityColumn(self, tableName, columnName):
        if not self.IsDB():
            return False
        return self.CreateColumn(tableName, columnName, u"INTEGER PRIMARY KEY AUTOINCREMENT")


    # Database Options ------------------------------------------------------------

    def IsDatabase(self, databaseName):
        try:
            db = sqlite3.connect(databaseName)
            db.close()
            return True
        except:
            return False

    def CreateDatabase(self, databaseName):
        return False

    def UseDatabase(self, databaseName):
        return False

