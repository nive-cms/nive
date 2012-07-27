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

__doc__ = "Data Pool 2 SQL Base Module"

import string, time, re, os
import iso8601
from datetime import datetime
from types import *
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from nive.utils.utils import ConvertToStr, ConvertListToStr, ConvertToList
from nive.utils.utils import BREAK, STACKF, DUMP
from nive.utils.path import DvPath
from nive.utils.strings import DvString
from nive.utils.dateTime import DvDateTime

from nive import ConfigurationError

#from Helper import *
from files import File


"""
error handling and messages
"""


# Pool Constants ---------------------------------------------------------------------------

#
StdEncoding = u"utf-8"
EncodeMapping = u"replace"
StdMetaFlds = (u"id", u"pool_dataref", u"pool_datatbl")


class OperationalError(Exception):
    pass
class ProgrammingError(Exception):
    pass
class Warning(Exception):
    pass


class Base(object):
    """
    Data Pool 2 SQL Base implementation

    Manage typed data units consisting of meta layer, data layer and files.
    Meta layer is the same for all units, data layer is based on types and files
    are stored by tag.
    Meta and data is mapped to database, files are stored in filesystem.

    Pool structure is required and must contain the used database fields as list
    (table names and column names).

    Entries are referenced by pool_meta.id as unique ID.

    All basic SQL is handled internally.


    Configuration Parameter
    -----------------------
    root:          string. filesystem root path
    codePage:      string. the codepage used on output
    dbCodePage:    string. database codepage
    structure:     PoolStructure object defining the database structure and field types.
    version:       string. the default version
    useBackups:    bool.     store backup versions of files on replace
    useTrashcan:   bool.     moves files to trashcan rather than delete physically
    debug:         number. turn debugging on. 0 = off, 1=on (no traceback), 2...20=on (traceback lines) 
    log:           string. log file path for debugging


    Standard Meta
    -------------
    A list consisting of meta layer fields which are used in preloading

    "meta_flds": (
    ("pool_dataref", "integer not null default 0"),
    ("pool_datatbl", "ENUM() not null"),
    )
    """
    # map db system exceptions to one type
    _OperationalError=OperationalError
    _ProgrammingError=ProgrammingError
    _Warning=Warning
    
    EmptyValues = None

    MetaTable = u"pool_meta"
    FulltextTable = u"pool_fulltext"
    GroupsTable = u"pool_groups"


    def __init__(self, connParam = None, structure = None, root = "",
                 useTrashcan = False, useBackups = False, 
                 codePage = StdEncoding, dbCodePage = None,
                 debug = 0, log = "sql.log", **kw):

        self.codePage = codePage
        self.dbCodePage = dbCodePage
        self.useBackups = useBackups
        self.useTrashcan = useTrashcan

        self._debug = debug
        self._log = log
        
        self.conn = None
        self.name = u""        # used for logging

        self.SetRoot(root)
        if not self.dbCodePage:
            self.dbCodePage = self._GetDefaultDBEncoding()
        if not structure:
            self.structure = self._GetDefaultPoolStructure()(pool=self)
        else:
            self.structure = structure
        if connParam:
            self.CreateConnection(connParam)



    def __del__(self):
         self.Close()


    def Close(self):
        if self.conn:
            self.conn.Close()
        #self.structure = None


    # Database ---------------------------------------------------------------------

    def GetConnection(self):
        """
        Returns the pool database connection
        """
        return self.conn


    def DB(self):
        """
        Returns the basic database connection
        """
        if not self.conn:
            raise ConnectionError, "No Connection"
        return self.conn.DB()


    def GetCursor(self):
        """
        Returns a cursor for database queries
        """
        return self.DB().cursor()


    def CreateConnection(self, connParam):
        self.conn = Connection(connParam)
        if not self.name:
            self.name = connParam.get("dbName",u"")


    def SetConnection(self, conn):
        self.conn = conn


    def GetPlaceholder(self):
        return u"%s"

    
    def GetDBDate(self, date=None):
        if not date:
            return DvDateTime(time.localtime()).GetDBMySql()
        return DvDateTime(str(date)).GetDBMySql()


    # SQL queries ---------------------------------------------------------------------

    def GetSQLSelect(self, flds, parameter={}, dataTable = u"", start = 0, max = 0, **kw):
        """
        Create a select statement based on pool_structure and given parameters.
        
        Aggregate functions can be included in flds but must be marked with
        the prefix '-' e.g. '-count(*)'
        
        Tables in the generated statement get an alias prefix:
        meta__ for meta table
        data__ for data table
        
        flds: select fields
        parameter: where clause parameter
        dataTable: add join statement for the table
        start: start number of record to be returned
        max: maximum nubers of records in result

        **kw:
        singleTable: 1/0 skip join. only use datatable for select
        version: version key. select content from specific version
        operators: operators used for fields in where clause: =,LIKE,<,>,...
        jointype: type of join. default = INNER
        logicalOperator = link between conditions. default = and. and, or, not
        condition = custom condition statement. default = empty
        join = custom join statement. default = empty
        groupby: add GROUP BY statement
        sort: result sort order
        ascending: result sort order ascending or descending
        """
        operators = kw.get("operators",{})
        jointype = operators.get("jointype", u"INNER")
        singleTable = kw.get("singleTable",0)
        version = kw.get("version")
        metaStructure = self.structure.get(self.MetaTable, version=version)
        mapJoinFld = kw.get("mapJoinFld")
        fields = []
        for f in flds:
            if singleTable:
                aTable = u""
                if f[0] == u"-":
                    f = f[1:]
            else:
                aTable = u"meta__."
                # aggregate functions marked with - e.g. "-count(*)"
                if f[0] == u"-":
                    aTable = u""
                    f = f[1:]
                asName = f.find(u" as ")!=-1
                f2=f
                if asName:
                    f2 = f.split(u" as ")[0]
                elif f2 in metaStructure or f2 == u"pool_stag":
                    aTable = u"meta__."
                elif dataTable != u"":
                    if jointype.lower() != u"inner":
                        if f == mapJoinFld:
                            fields.append(u"IF(meta__.pool_datatbl='%s', %s, meta__.title)" % (dataTable, f))
                        else:
                            fields.append(u"IF(meta__.pool_datatbl='%s', %s, '')" % (dataTable, f))
                        continue
                    aTable = u"data__."
            if(len(fields) > 0):
                fields.append(u", ")
            fields.append(aTable + f)
        fields = u"".join(fields)

        aCombi = kw.get("logicalOperator")
        if not aCombi:
            aCombi = u"AND"
        else:
            aCombi = aCombi.upper()
            if not aCombi in (u"AND",u"OR",u"NOT"):
                aCombi = u"AND"
        addCombi = False
        connection = self.GetConnection()

        where = []
        for aK in parameter.keys():
            aT = type(parameter[aK])
            aKey = aK

            aOperator = u"="
            if operators:
                if operators.has_key(aK):
                    aOperator = operators.get(aK)

            if singleTable:
                aTable = u""
            else:
                aTable = u"meta__."
                # aggregate functions marked with - e.g. "-count(*)"
                if aK[0] == u"-":
                    aTable = u""
                    aKey = aK[1:]
                elif aK in metaStructure or aK == u"pool_stag":
                    aTable = u"meta__."
                elif dataTable != u"":
                    aTable = u"data__."
            
            # fmt string values
            if aT in (StringType, UnicodeType):
                aW = self.DecodeText(parameter[aK])
                if aOperator == u"LIKE":
                    if aW == u"":
                        continue
                    aW = aW.replace(u"*", u"%")
                    if aW.find(u"%") == -1:
                        aW = u"%%%s%%" % (aW)
                    aW = connection.FmtParam(aW)
                    if addCombi:
                        where.append(u" %s " % aCombi)
                    where.append(u"%s%s %s %s " % (aTable, aKey, aOperator, aW))
                elif aOperator == u"BETWEEN":
                    if aW == u"":
                        continue
                    if addCombi:
                        where.append(u" %s " % aCombi)
                    where.append(u"%s%s %s %s " % (aTable, aKey, aOperator, aW))
                else:
                    aW = connection.FmtParam(aW)
                    if addCombi:
                        where.append(u" %s " % aCombi)
                    where.append(u"%s%s %s %s " % (aTable, aKey, aOperator, aW))
                addCombi = True

            # fmt list values
            elif aT in (TupleType, ListType):
                aW = parameter[aK]
                if aW == None or len(aW)==0:
                    continue
                if addCombi:
                    where.append(u" %s " % aCombi)
                if aOperator.upper() in (u"IN",u"NOT IN"):
                    aW = u""
                    for item in parameter[aK]:
                        if aW != u"":
                            aW += u","
                        if type(item) == StringType:
                            item = self.DecodeText(item)
                        aW += connection.FmtParam(item)
                    if aW == u"":
                        aW = u"None"
                    where.append(u"%s%s %s (%s) " % (aTable, aKey, aOperator, aW))
                elif aOperator == u"BETWEEN":
                    if len(aW) < 2:
                        continue
                    where.append(u"%s%s %s %s AND %s" % (aTable, aKey, aOperator, connection.FmtParam(aW[0]), connection.FmtParam(aW[1])))
                else:
                    aW = u"%%%s%%" % (self.DecodeText(ConvertToStr(aW, "list")))
                    aW = connection.FmtParam(aW)
                    where.append(u"%s%s LIKE %s " % (aTable, aKey, aW))
                addCombi = True

            # fmt number values
            elif aT in (IntType, LongType, FloatType):
                if addCombi:
                    where.append(u" %s " % aCombi)
                if aOperator == u"LIKE":
                    aOperator = u"="
                aW = connection.FmtParam(parameter[aK])
                where.append(u"%s%s %s %s" % (aTable, aKey, aOperator, aW))
                addCombi = True

        condition = kw.get("condition")
        if condition != None and condition != u"":
            if len(where):
                where.append(u" %s %s" %(aCombi, condition))
            else:
                where = [condition]
        where = self._FmtWhereClause(where, singleTable)

        order = u"ASC"
        if kw.get("ascending", 1) == 0:
            order = u"DESC"

        # map sort fields
        sort = kw.get("sort", u"")
        if sort==None:
            sort = u""
        if sort != u"" and not singleTable:
            aTable = u"meta__."
            s = sort.split(u",")
            sort = []
            for sortfld in s:
                sortfld = DvString(sortfld)
                sortfld.Trim()
                sortfld = str(sortfld)
                if len(sortfld) > 0 and sortfld[0] == u"-":
                    aTable = u""
                    sortfld = sortfld[1:]
                elif sortfld in metaStructure or sortfld == u"pool_stag":
                    aTable = u"meta__."
                elif dataTable != u"":
                    aTable = u"data__."
                if len(sort):
                    sort.append(u", ")
                sort.append(aTable)
                sort.append(sortfld)
            sort = u"".join(sort)

        customJoin = kw.get("join", u"")
        if customJoin == None:
            customJoin = u""

        join = u""
        joindata = u""
        if not singleTable:
            # joins
            if dataTable != u"":
                joindata = u"%s JOIN %s AS data__ ON (meta__.pool_dataref = data__.id) " % (jointype, dataTable)

        limit = ""
        if max:
            limit = self._FmtLimit(start, max)

        groupby = u""
        if kw.get("groupby"):
            groupby = u"GROUP BY %s" % kw.get("groupby")

        table = self.MetaTable + u" AS meta__"
        if singleTable:
            table = dataTable

        if sort != u"":
            sort = u"ORDER BY %s %s" % (sort, order)

        aSql = u"""
        SELECT %s
        FROM %s
        %s %s %s
        %s
        %s %s %s
        """ % (fields, table, join, joindata, customJoin, where, groupby, sort, limit)
        return aSql


    def _FmtWhereClause(self, where, singleTable):
        if len(where):
            where = u"WHERE %s" % u"".join(where)
        else:
            where = u""
        return where


    def _FmtLimit(self, start, max):
        if start != None:
            return u"LIMIT %s, %s" % (unicode(start), unicode(max))
        return u"LIMIT %s" % (unicode(max))


    def GetFulltextSQL(self, searchPhrase, flds, parameter, dataTable = "", **kw):
        """
        generate sql statement for fulltext query

        searchPhrase: text to be searched

        **kw:
        skipRang
        useMatch

        For further options see -> GetSQLSelect
        """
        aSql = self.GetSQLSelect(flds, parameter, dataTable=dataTable, **kw)
        connection = self.GetConnection()
        searchPhrase = connection.FmtParam(self.DecodeText(searchPhrase))

        if kw.get("useMatch"):
            aM = u"""MATCH (%s.text) AGAINST (%s)""" % (self.FulltextTable, searchPhrase)
        else:
            aM = u"""%s.text LIKE %s""" % (self.FulltextTable, searchPhrase)

        if not kw.get("skipRang"):
            aSql = aSql.replace(u"SELECT ", "SELECT %s AS rang__, " % (aM))

        if not searchPhrase in (u"", u"'%%'", None):
            if aSql.find(u"WHERE ") == -1:
                aSql = aSql.replace(u"ORDER BY ", "WHERE %s \r\nORDER BY " % (aM))
            else:
                aSql = aSql.replace(u"WHERE ", "WHERE %s AND " % (aM))
        aSql = aSql.replace(u"FROM %s AS meta__"%(self.MetaTable), "FROM %s AS meta__\r\n\t\tLEFT JOIN %s ON (meta__.id = %s.id)"%(self.MetaTable, self.FulltextTable, self.FulltextTable))
        #aSql = aSql.replace("ORDER BY ", "ORDER BY rang__, ")
        return aSql


    def Query(self, sql, values = None, cursor=None, getResult=True):
        """
        execute a query on the database. non unicode texts are converted according to codepage settings.
        """
        cc=True
        if cursor:
            c = cursor
            cc=False
        else:
            c = self.GetCursor()
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        sql = self.DecodeText(sql)
        if values:
            #opt
            v1 = []
            for v in values:
                if type(v) == StringType:
                    v1.append(self.DecodeText(v))
                else:
                    v1.append(v)
            values = v1
        # adjust different accepted empty values sets
        if not values:
            values = self.EmptyValues
        try:
            c.execute(sql, values)
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
            self.Undo()
        except self._ProgrammingError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            self.Undo()
            raise ProgrammingError, e
        if not getResult:
            if cc:
                c.close()
            return
        r = c.fetchall()
        if cc:
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


    def QueryRaw(self, sql, values = None, cursor=None, getResult=True):
        """
        execute a query on the database.
        """
        cc=True
        if cursor:
            c = cursor
            cc=False
        else:
            c = self.GetCursor()
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        # adjust different accepted empty values sets
        if not values:
            values = self.EmptyValues
        try:
            c.execute(sql, values)
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        except self._ProgrammingError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            self.Undo()
            raise ProgrammingError, e
        if not getResult:
            if cc:
                c.close()
            return
        l = c.fetchall()
        if cc:
            c.close()
        return l


    def InsertFields(self, table, data, cursor = None):
        """
        insert row with multiple fields in the table.
        codepage and dates are converted automatically
        returns the converted data 
        """
        dataList = []
        flds = []
        phdata = []
        ph = self.GetPlaceholder()
        for aK in data.keys():
            if len(flds):
                flds.append(u",")
                phdata.append(u",")
            flds.append(aK)
            phdata.append(ph)

            if type(data[aK]) == StringType:
                data[aK] = self.DecodeText(data[aK])
            dataList.append(self.structure.serialize(table, aK, data[aK]))
            data[aK] = dataList[-1]

        sql = u"INSERT INTO %s (%s) VALUES (%s)" % (table, u"".join(flds), u"".join(phdata))

        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)

        cc = 0
        if not cursor:
            cc = 1
            cursor = self.GetCursor()
        try:
            cursor.execute(sql, dataList)
        except self._Warning:
            pass
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        if cc:
            cursor.close()
        return data


    def UpdateFields(self, table, id, data, cursor = None):
        """
        updates multiple fields in the table.
        codepage and dates are converted automatically
        returns the converted data 
        """
        sql = [u"UPDATE %s SET " % (table)]
        dataList = []
        ph = self.GetPlaceholder()
        for aK in data.keys():
            if len(sql)>1:
                sql.append(u",%s=%s"%(aK, ph))
            else:
                sql.append(u"%s=%s"%(aK, ph))

            if type(data[aK]) == StringType:
                data[aK] = self.DecodeText(data[aK])
            dataList.append(self.structure.serialize(table, aK, data[aK]))
            data[aK] = dataList[-1]

        sql.append(u" WHERE id = %d" % (id))
        sql = u"".join(sql)
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)

        aClose = 0
        if not cursor:
            aClose = 1
            cursor = self.GetCursor()
        try:
            cursor.execute(sql, dataList)
        except self._Warning:
            pass
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        if aClose:
            cursor.close()
        return data


    def DeleteRecords(self, table, parameter, cursor=None):
        """
        Delete records referenced by parameters
        """
        if not parameter:
            return False
        p = []
        v = []
        ph = self.GetPlaceholder()
        for field, value in parameter.items():
            p.append(u"%s=%s"%(field, ph))
            v.append(value)
        sql = u"DELETE FROM %s WHERE %s" % (table, u" AND ".join(p))
        if self._debug:
            STACKF(0,aSql+"\r\n\r\n",self._debug, self._log,name=self.name)
        cc=False
        if not cursor:
            cc=True
            cursor = self.GetCursor()
        cursor.execute(sql, v)
        if cc:
            cursor.close()


    def Begin(self):
        """
        Start a database transaction, if supported
        """
        self.GetConnection().Begin()


    def Commit(self, user=""):
        """
        Commit the changes made to the database, if supported
        """
        self.GetConnection().Commit()


    def Undo(self):
        """
        Rollback the changes made to the database, if supported
        """
        self.GetConnection().Undo()


    # Text conversion -----------------------------------------------------------------------

    def EncodeText(self, text):
        """
        Used for text read from the database. 
        Converts the text to unicode based on self.dbCodePage.
        """
        if text==None:
            return text
        if type(text) == StringType:
            return unicode(text, self.dbCodePage, EncodeMapping)
        return text


    def DecodeText(self, text):
        """
        Used for text stored in database.
        Convert the text to unicode based on self.codePage.
        """
        if text==None:
            return text
        if type(text) == StringType:
            return unicode(text, self.codePage, EncodeMapping)
        return text


    def ConvertRecToDict(self, rec, flds):
        """
        Convert a database record tuple to dictionary based on flds list
        """
        aD = {}
        if not rec:
            return aD

        #opt
        for aI in range(len(flds)):
            aStr = flds[aI]
            # data unicode and codepage conversion
            if type(rec[aI]) == StringType:
                aD[aStr] = self.EncodeText(rec[aI])
            else:
                aD[aStr] = rec[aI]
        return aD


    # groups - userid assignment storage ------------------------------------------------------------------------------------

    def GetGroups(self, id, userid=None, group=None):
        """
        Add a local group assignment for userid.
        
        returns a group assignment list [["userid", "groupid", "id"], ...]
        """
        # check if exists
        p = {}
        
        if id!=None:
            p["id"] = id
        else:
            raise TypeError, "id must not be none"
        if userid:
            p["userid"] = userid
        if group:
            p["groupid"] = group
        sql = self.GetSQLSelect(["userid", "groupid", "id"], parameter=p, dataTable = self.GroupsTable, singleTable=1)
        r = self.Query(sql)
        return r


    def AddGroup(self, id, userid, group):
        """
        Add a local group assignment for userid.
        """
        data = {"userid": userid, "groupid": group}
        if id!=None:
            data["id"] = id
        else:
            raise TypeError, "id must not be none"
        self.InsertFields(self.GroupsTable, data)
        self.Commit()


    def RemoveGroups(self, id, userid=None, group=None):
        """
        Remove a local group assignment for userid or all for the id/ref.
        """
        p = {}
        if id!=None:
            p["id"] = id
        else:
            raise TypeError, "id must not be none"
        if userid:
            p["userid"] = userid
        if group:
            p["groupid"] = group
        self.DeleteRecords(self.GroupsTable, p)
        self.Commit()


    # Entries -------------------------------------------------------------------------------------------

    def CreateEntry(self, pool_datatbl, id = 0, user = "", **kw):
        """
        Create new entry.
        Requires pool_datatbl as parameter
        """
        if id:
            id, dataref = self._CreateFixID(id, dataTbl=pool_datatbl)
        else:
            id, dataref = self._CreateNewID(table=self.MetaTable, dataTbl=pool_datatbl)
        if not id:
            return None
        kw["preload"] = u"skip"
        kw["pool_dataref"] = dataref
        entry = self._GetPoolEntry(id, **kw)
        entry._InitNew(pool_datatbl, user)
        return entry


    def GetEntry(self, id, **kw):
        """
        Get entry from db by ID
        """
        return self._GetPoolEntry(id, **kw)


    def DeleteEntry(self, id, version=None):
        """
        Delete the entry and files
        """
        if version:
            BREAK("version")
        cursor = self.GetCursor()

        # base record
        sql = self.GetSQLSelect([u"pool_dataref", u"pool_datatbl"], parameter={"id":id}, dataTable=self.MetaTable, singleTable=1)
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        cursor.execute(sql)
        r = cursor.fetchone()
        if not r:
            return 0
        dataref = r[0]
        datatbl = r[1]

        tables = (self.MetaTable, self.FulltextTable, self.GroupsTable)
        for table in tables:
            self.DeleteRecords(table, parameter={"id":id})

        self.DeleteRecords(datatbl, parameter={"id":dataref})

        # delete files
        self._DeleteFiles(id, cursor, version)

        cursor.close()
        return 1


    def IsIDUsed(self, id):
        """
        Query database if id exists
        """
        sql = self.GetSQLSelect(["id"], parameter={"id":id}, dataTable = self.MetaTable, singleTable=1)
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        c = self.GetCursor()
        c.execute(sql)
        n = c.fetchone()
        c.close()
        return n!=None


    def GetBatch(self, ids, **kw):
        """
        Get all entries as objects at once. returns a list.
        supports preload: all, skip, meta
        
        kw: 
        - meta: list of meta pool_datatbl for faster lookup
        """
        preload = kw.get("preload", u"all")
        entries = []
        version = kw.get("version")
        sort = kw.get("sort")
        if len(ids) == 0:
            return entries

        if preload == u"skip":
            for id in ids:
                e = self._GetPoolEntry(id, preload=u"skip", version=version)
                entries.append(e)
            return entries

        if preload == u"meta":
            flds = self.structure.get(self.MetaTable, version=version)
            if not flds:
                raise ConfigurationError, "Meta layer is empty."
            parameter = {"id": ids}
            operators = {"id": u"IN"}
            sql = self.GetSQLSelect(flds, parameter=parameter, dataTable=self.MetaTable, max=len(ids), sort=sort, operators=operators, singleTable=1)
            recs = self.Query(sql)
            for r in recs:
                meta = self.ConvertRecToDict(r, flds)
                e = self._GetPoolEntry(meta[u"id"], pool_dataref=meta[u"pool_dataref"], pool_datatbl=meta[u"pool_datatbl"], preload=u"skip")
                e._UpdateCache(meta = meta, data = None)
                entries.append(e)
            return entries

        if "meta" in kw and kw["meta"] and "pool_datatbl" in kw["meta"][0]:
            # use meta pool_datatbl passed in kw[meta]
            tables = []
            for r in kw["meta"]:
                if not r["pool_datatbl"] in tables:
                    tables.append(r["pool_datatbl"])
        else:
            # select data tables for ids
            flds = [u"pool_datatbl"]
            parameter = {"id": ids}
            operators = {"id": u"IN"}
            # select list of datatbls
            sql = self.GetSQLSelect(flds, parameter=parameter, dataTable=self.MetaTable, sort=sort, groupby=u"pool_datatbl", operators=operators, singleTable=1)
            tables = []
            for r in self.Query(sql):
                if not r["pool_datatbl"] in tables:
                    tables.append(r[0])
        t = u""
        fldsm = self.structure.get(self.MetaTable, version=version)
        if not fldsm:
            raise ConfigurationError, "Meta layer is empty."
        unsorted = []
        for table in tables:
            structure = self.structure.get(table, version=version)
            if not structure:
                continue
            fldsd = list(structure)
            flds = list(fldsm) + fldsd
            parameter = {u"id": ids, u"pool_datatbl": table}
            operators = {u"id": u"IN", u"pool_datatbl": u"="}
            # select type data
            sql = self.GetSQLSelect(flds, parameter=parameter, dataTable=table, sort=sort, operators=operators)
            typeData = self.Query(sql)
            for r2 in typeData:
                meta = self.ConvertRecToDict(r2[:len(fldsm)], fldsm)
                data = self.ConvertRecToDict(r2[len(fldsm):], fldsd)
                e = self._GetPoolEntry(meta[u"id"], pool_dataref=meta[u"pool_dataref"], pool_datatbl=meta[u"pool_datatbl"], preload=u"skip")
                e._UpdateCache(meta = meta, data = data)
                unsorted.append(e)
        # sort entries
        for id in ids:
            for o in unsorted:
                if o.id==id:
                    entries.append(o)
                    break
        return entries


    def _CreateNewID(self, table = ""):
        BREAK("assert", "subclass")
        return 0

    def _CreateFixID(self, id, dataTbl):
        BREAK("assert", "subclass")
        return 0

    def _GetEntryClassType(self):
        BREAK("assert", "subclass")
        return 0

    def _GetPoolEntry(self, id, **kw):
        BREAK("assert", "subclass")
        return 0


    # Tree structure --------------------------------------------------------------

    def GetContainedIDs(self, base=0, sort=u"title", parameter=u""):
        """
        Search subtree and returns a list of all contained ids.
        id needs to be first field, pool_unitref second
        """
        refs = u"""
        pool_unitref as ref1,
        (select pool_unitref from %(meta)s where id = ref1) as ref2,
        (select pool_unitref from %(meta)s where id = ref2) as ref3,
        (select pool_unitref from %(meta)s where id = ref3) as ref4,
        (select pool_unitref from %(meta)s where id = ref4) as ref5,
        (select pool_unitref from %(meta)s where id = ref5) as ref6,
        (select pool_unitref from %(meta)s where id = ref6) as ref7,
        (select pool_unitref from %(meta)s where id = ref7) as ref8,
        (select pool_unitref from %(meta)s where id = ref8) as ref9,
        (select pool_unitref from %(meta)s where id = ref9) as ref10,
        """ % {"meta": self.MetaTable}

        if parameter:
            parameter = u"where " + parameter
        sql = u"""
        select %s id
        from %s %s
        order by pool_unitref, %s
        """ % (refs, self.MetaTable, parameter, sort)
        aC = self.GetCursor()
        aC.execute(sql)
        l = aC.fetchall()
        aC.close()
        if len(l) == 0:
            return []

        ids = []
        for rec in l:
            #ignore outside tree
            if not base in rec or rec[10] == base:
                continue
            #data
            ids.append(rec[10])

        return ids


    def GetTree(self, flds=[u"id"], sort=u"title", base=0, parameter=u""):
        """
        Loads a subtree as dictionary. 
        The returned dictionary has the following format:
        {"id": 123, "items": [{"id": 124, "items": [], "data": "q", ....}, ...], "data": "q", ....}
        
        id needs to be first field, pool_unitref second
        """
        refs = u"""
        pool_unitref as ref1,
        (select pool_unitref from %(meta)s where id = ref1) as ref2,
        (select pool_unitref from %(meta)s where id = ref2) as ref3,
        (select pool_unitref from %(meta)s where id = ref3) as ref4,
        (select pool_unitref from %(meta)s where id = ref4) as ref5,
        (select pool_unitref from %(meta)s where id = ref5) as ref6,
        (select pool_unitref from %(meta)s where id = ref6) as ref7,
        (select pool_unitref from %(meta)s where id = ref7) as ref8,
        (select pool_unitref from %(meta)s where id = ref8) as ref9,
        (select pool_unitref from %(meta)s where id = ref9) as ref10,
        """ % {"meta":self.MetaTable}

        if parameter:
            parameter = u"where " + parameter
        sql = u"""
        select 
        %s 
        %s
        from %s %s
        order by pool_unitref, %s
        """ % (refs, ConvertListToStr(flds), self.MetaTable, parameter, sort)
        aC = self.GetCursor()
        aC.execute(sql)
        l = aC.fetchall()
        tree = {"items":[]}
        aC.close()
        if len(l) == 0:
            return tree

        flds2 = [u"ref1", u"ref2", u"ref3", u"ref4", u"ref5", u"ref6", u"ref7", u"ref8", u"ref9", u"ref10"] + flds
        rtree = [u"ref10", u"ref9", u"ref8", u"ref7", u"ref6", u"ref5", u"ref4", u"ref3", u"ref2", u"ref1"]
        for rec in l:
            #ignore outside tree
            if not base in rec:  # or rec[10] == base:
                continue
            #data
            data = self.ConvertRecToDict(rec, flds2)
            #parent and path, lookup base in parents 
            add = 0
            current = tree
            for ref in rtree:
                if data[ref] == None:
                    continue
                if data[ref] == base:
                    add = 1
                if not add:
                    continue
                # add item to tree list
                if not current.has_key("items"):
                    current["items"] = []
                refentry = self._InList(current["items"], data[ref])
                if not refentry:
                    refentry = {"id":data[ref], "items": []}
                    current["items"].append(refentry)
                current = refentry
            # add data 
            if not current.has_key("items"):
                current["items"] = []
            entry = self._InList(current["items"], data["id"])
            if not entry:
                entry = data
                current["items"].append(entry)
            else:
                entry.update(data)

        return tree

    def _InList(self, l, id):
        for i in l:
            if i["id"] == id:
                return i
        return None
    
    
    def GetParentPath(self, id):
        """
        Returns id references of parents for the given id.
        Maximum 10 parents
        """
        if id <= 0:
            return []
        sql = u"""
        SELECT t1.pool_unitref AS ref1, 
         t2.pool_unitref as ref2, 
         t3.pool_unitref as ref3, 
         t4.pool_unitref as ref4,
         t5.pool_unitref as ref5,
         t6.pool_unitref as ref6,
         t7.pool_unitref as ref7,
         t8.pool_unitref as ref8,
         t9.pool_unitref as ref9,
         t10.pool_unitref as ref10
        FROM %(meta)s AS t1
        LEFT JOIN %(meta)s AS t2 ON t2.id = t1.pool_unitref
        LEFT JOIN %(meta)s AS t3 ON t3.id = t2.pool_unitref
        LEFT JOIN %(meta)s AS t4 ON t4.id = t3.pool_unitref
        LEFT JOIN %(meta)s AS t5 ON t5.id = t4.pool_unitref
        LEFT JOIN %(meta)s AS t6 ON t6.id = t5.pool_unitref
        LEFT JOIN %(meta)s AS t7 ON t7.id = t6.pool_unitref
        LEFT JOIN %(meta)s AS t8 ON t8.id = t7.pool_unitref
        LEFT JOIN %(meta)s AS t9 ON t9.id = t8.pool_unitref
        LEFT JOIN %(meta)s AS t10 ON t10.id = t9.pool_unitref
        WHERE t1.id = %(id)d;""" % {"id":id, "meta": self.MetaTable}
        
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        aC = self.GetCursor()
        aC.execute(sql)
        aL = aC.fetchall()
        parents = []
        if len(aL) == 0:
            return parents
        cnt = 10
        for i in range(0, cnt-1):
            id = aL[0][i]
            if id == None:
                continue
            if id <= 0:
                break
            parents.insert(0, id)
        aC.close()
        return parents


    def GetParentTitles(self, id):
        """
        Returns titles of parents for the given id.
        maximum 10 parents
        """
        if id <= 0:
            return []
        aC = self.GetCursor()
        sql = u"""
        SELECT t1.pool_unitref AS ref1, t1.title AS title1, 
         t2.pool_unitref as ref2, t2.title AS title2,
         t3.pool_unitref as ref3, t3.title AS title3,
         t4.pool_unitref as ref4, t4.title AS title4,
         t5.pool_unitref as ref5, t5.title AS title5,
         t6.pool_unitref as ref6, t6.title AS title6,
         t7.pool_unitref as ref7, t7.title AS title7,
         t8.pool_unitref as ref8, t8.title AS title8,
         t9.pool_unitref as ref9, t9.title AS title9,
         t10.pool_unitref as ref10, t10.title AS title10 
        FROM %(meta)s AS t1
        LEFT JOIN %(meta)s AS t2 ON t2.id = t1.pool_unitref
        LEFT JOIN %(meta)s AS t3 ON t3.id = t2.pool_unitref
        LEFT JOIN %(meta)s AS t4 ON t4.id = t3.pool_unitref
        LEFT JOIN %(meta)s AS t5 ON t5.id = t4.pool_unitref
        LEFT JOIN %(meta)s AS t6 ON t6.id = t5.pool_unitref
        LEFT JOIN %(meta)s AS t7 ON t7.id = t6.pool_unitref
        LEFT JOIN %(meta)s AS t8 ON t8.id = t7.pool_unitref
        LEFT JOIN %(meta)s AS t9 ON t9.id = t8.pool_unitref
        LEFT JOIN %(meta)s AS t10 ON t10.id = t9.pool_unitref
        WHERE t1.id = %(id)d;""" % {"id": id, "meta": self.MetaTable}        
        
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        aC.execute(sql)
        aL = aC.fetchall()
        parents = []
        if len(aL) == 0:
            return parents
        cnt = 10
        for i in range(1, cnt-1):
            title = aL[0][i*2+1]
            if title == None:
                break
            parents.insert(0, self.EncodeText(title))
        aC.close()
        return parents


    # Configuration ---------------------------------------------------------------------

    def SetRoot(self, root):
        """
        Set the local root path for files
        """
        self.root = DvPath()
        self.root.SetStr(root)


    def GetRoot(self):
        return str(self.root)


    # Pool status ---------------------------------------------------------------------

    def GetCountEntries(self, table = None):
        """
        Returns the total number of entries in the pool
        """
        if not table:
            table = self.MetaTable
        aC = self.GetCursor()
        aC.execute(u"SELECT COUNT(*) FROM %s" % (table))
        aN = aC.fetchone()[0]
        aC.close()
        return aN

    def Log(self, s):
        DUMP(s, self._log,name=self.name)


    def _DeleteFiles(self, id, cursor, version):
        pass

    def _GetDefaultDBEncoding(self):
        return u"utf-8"

    def _GetDefaultPoolStructure(self):
        return PoolStructure

    def _GetDataWrapper(self):
        return DataWrapper

    def _GetMetaWrapper(self):
        return MetaWrapper

    def _GetFileWrapper(self):
        return FileWrapper




class Entry:
    """
    Entry object of data pool
    """

    def __init__(self, dataPool, id, **kw):
        """[a]
        version: version of this entry
        dataTbl: data table name of this entry type
        preload: meta/data flds to preload on init. "all" (default), "skip", "stdmetadata", "stdmeta", "meta"
        kw virtual = 1 to disable preload() and exists() 
        """
        # key values
        self.id = id
        self.version = kw.get("version", None)
        self.dataTbl = kw.get("pool_datatbl", None)
        self.dataRef = kw.get("pool_dataref", 0)

        # basic properties
        self.pool = dataPool
        self.meta = dataPool._GetMetaWrapper()(self)
        self.data = dataPool._GetDataWrapper()(self)
        self.files = dataPool._GetFileWrapper()(self)
        self.cacheRec = True
        self._localRoles = None
        self._permissions = None
        self.virtual = kw.get("virtual")==1
        
        #self._debug = 0#dataPool._debug

        if self.virtual:
            return
        preload = kw.get("preload", u"all")
        if self.id and self.cacheRec and preload != u"skip":
            self.Load(preload)
            if self.data.IsEmpty() and self.meta.IsEmpty() and self.files.IsEmpty():
                if not self.Exists():
                    raise NotFound, "%s not found" % str(id)
        #else:
        #    if not self.Exists():
        #        raise NotFound, "%s not found" % str(id)


    def __del__(self):
         self.Close()


    def Close(self):
        self.meta.Close()
        self.data.Close()
        self.files.Close()
        self.pool = None


    def Exists(self):
        """
        Check if the entry physically exists in the database
        """
        if self.virtual:
            return True
        if not self.IsValid():
            #print "not valid"
            return False
        return self.pool.IsIDUsed(self.id)


    def IsValid(self):
        """
        Check if the id is valid
        """
        return self.id > 0

    # Transactions ------------------------------------------------------------------------

    def Commit(self, user=""):
        """
        Commit temporary changes (meta, data, files) to database
        """
        self.Touch(user)
        try:
            cursor = self.pool.GetCursor()
            # meta
            if self.meta.HasTemp():
                self.pool.UpdateFields(self.pool.MetaTable, self.id, self.meta.GetTemp(), cursor)
            # data
            if self.data.HasTemp():
                self.pool.UpdateFields(self.GetDataTbl(), self.GetDataRef(), self.data.GetTemp(), cursor)
            # files
            if self.files.HasTemp():
                temp = self.files.GetTemp()
                if temp:
                    for tag in temp.keys():
                        file = temp[tag]
                        result = self.SetFile(tag, file, cursor=cursor)
                        if not result:
                            raise TypeError, "File save error (%s)." #%(self.GetError())
            self.pool.Commit()
            cursor.close()
            self.data.SetContent(self.data.GetTemp())
            self.data.clear()
            self.meta.SetContent(self.meta.GetTemp())
            self.meta.clear()
            self.files.clear()
        except Exception, e:
            try:
                self.Undo()
            except:
                pass
            raise 
        return True


    def Undo(self):
        """
        Undo changes in database
        """
        self.meta.EmptyTemp()
        self.data.EmptyTemp()
        self.files.EmptyTemp()
        self.pool.Undo()


    # Reading Values ------------------------------------------------------------------------

    def GetMetaField(self, fld, fromDB=False):
        """
        Read a single field from meta layer
        if fromDB data is loaded from db, not cache
        """
        if fld == u"id":
            return self.id
        elif fld == u"pool_size":
            return self.GetDataSize()

        if not fromDB and self.cacheRec and self.meta.has_key(fld):
            return self.meta[fld]

        sql = self.pool.GetSQLSelect([fld], parameter={"id":self.id}, dataTable=self.pool.MetaTable, singleTable=1)
        data = self._GetFld(sql)
        data = self.pool.structure.deserialize(self.pool.MetaTable, fld, data)
        self._UpdateCache({fld: data})
        return data


    def GetDataField(self, fld, fromDB=False):
        """
        Read a single field from data layer
        if fromDB data is loaded from db, not cache
        """
        if not fromDB and self.cacheRec and self.data.has_key(fld):
            return self.data[fld]

        tbl = self.GetDataTbl()
        sql = self.pool.GetSQLSelect([fld], parameter={"id":self.GetDataRef()}, dataTable=tbl, singleTable=1)
        data = self._GetFld(sql)
        data = self.pool.structure.deserialize(tbl, fld, data)
        self._UpdateCache(None, {fld: data})
        return data


    def GetMeta(self):
        """
        Read meta layer and return as dictionary
        """
        if self.cacheRec and not self.meta.IsEmpty():
            return self.meta.copy()

        data =  self._SQLSelect(self.pool.structure.get(self.pool.MetaTable, version=self.version))
        data = self.pool.structure.deserialize(self.pool.MetaTable, None, data)
        self._UpdateCache(data)
        data[u"id"] = self.id
        return data


    def GetData(self):
        """
        Read data layer and return as dictionary
        """
        if self.cacheRec and not self.data.IsEmpty():
            return self.data

        tbl = self.GetDataTbl()
        try:
            flds = self.pool.structure.get(tbl, version=self.version)
        except:
            return None

        data = self._SQLSelect(flds, table=tbl)
        data = self.pool.structure.deserialize(tbl, None, data)
        self._UpdateCache(None, data)
        return data


    # Writing Values ------------------------------------------------------------------------

    def SetMetaField(self, fld, data):
        """
        Update single field to meta layer.
        Commits changes immediately to database without calling touch.
        """
        temp = self.pool.UpdateFields(self.pool.MetaTable, self.id, {fld:data})
        self.pool.Commit()
        self._UpdateCache(temp)
        return True


    def SetDataField(self, fld, data):
        """
        Update single field to data layer
        Commits changes immediately to database without calling touch.
        """
        if fld == u"id":
            return False

        cursor = self.pool.GetCursor()
        # check if data record already exists
        id = self.GetDataRef(cursor)
        if id <= 0:
            cursor.close()
            return False

        temp = self.pool.UpdateFields(self.GetDataTbl(), id, {fld:data}, cursor)
        cursor.close()
        self.pool.Commit()

        self._UpdateCache(None, temp)
        return True


    def Touch(self, user=""):
        """
        Tets change date and changed by to now
        """
        temp = {}
        temp[u"pool_change"] = self.pool.GetDBDate()
        if user==None:
            user=""
        else:
            user=str(user)
        temp[u"pool_changedby"] = user
        self.meta.update(temp)
        return True


    # Files -------------------------------------------------------------------------------------------

    def DuplicateFile(self, newEntry):
        """
        """
        BREAK("subclass")
        pass


    def SetFile(self, tag, file):
        """
        """
        BREAK("subclass")
        pass


    # Actions ---------------------------------------------------------------------------

    def Duplicate(self, duplicateFiles = True):
        """
        Create a copy of the entry with a new id.
        """
        if self.cacheRec:
            self.Load("all")

        newEntry = self.pool.CreateEntry(pool_datatbl=self.GetDataTbl())
        if not newEntry:
            return None
        id = newEntry.GetID()

        # copy data
        newEntry.meta.update(self.GetMeta())
        newEntry.data.update(self.GetData())

        # check if entry contains file and file exists
        if duplicateFiles:
            if not self.DuplicateFile(newEntry):
                self.pool.DeleteEntry(id)
                del newEntry
                return None

        return newEntry


    # Preloading -------------------------------------------------------------------------------------------

    def Load(self, option = u"all", reload = False):
        """
        Loads different sets of fields in single sql statement

        options:
        skip
        all: all meta and data fields
        stdmeta: fields configured in stdMeta list
        stdmetadata: fields configured in stdMeta list and all data fields
        meta: all meta fields
        """
        if self.virtual:
            return True
        if option == u"skip":
            return True

        # check data already in memory
        if not reload:
            if option == u"all" and not self.data.IsEmpty() and not self.meta.IsEmpty():
                return True

            elif option == u"stdmetadata" and not self.data.IsEmpty() and not self.meta.IsEmpty():
                return True

            elif option == u"stdmeta" and not self.meta.IsEmpty():
                return True

            elif option == u"meta" and not self.meta.IsEmpty():
                return True

        # shortcut sql load functions based on pool structure
        if option == u"all":
            return self._PreloadAll()
        elif option == u"stdmetadata":
            return self._PreloadStdMetaData()
        elif option == u"stdmeta":
            return self._PreloadStdMeta()
        elif option == u"meta":
            return self._PreloadMeta()

        return True


    # System Values ------------------------------------------------------------------------

    def GetID(self):
        return self.id

    def GetDataTbl(self):
        if self.dataTbl:
            return self.dataTbl
        self.dataTbl = self.GetMetaField(u"pool_datatbl")
        return self.dataTbl

    def GetDataRef(self):
        if self.dataRef:
            return self.dataRef
        self.dataRef = self.GetMetaField(u"pool_dataref")
        return self.dataRef

    def GetSize(self):
        return 0

    def GetVersion(self):
        return self.version


    # Caching --------------------------------------------------------------------

    def Clear(self):
        """
        empty cache
        """
        self.meta.clear()
        self.data.clear()
        self.files.clear()


    # Fulltext ---------------------------------------------------------------------------------------

    def WriteFulltext(self, text):
        """
        Update or create fulltext for entry
        """
        if text==None:
            text=""
        sql = self.pool.GetSQLSelect(["id"], parameter={"id":self.id}, dataTable=self.pool.FulltextTable, singleTable=1)
        cursor = self.pool.GetCursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n", self.pool._debug, self.pool._log, name=self.pool.name)
        cursor.execute(sql)
        r = cursor.fetchone()
        text = self.pool.DecodeText(text)
        if not r:
            self.pool.InsertFields(self.pool.FulltextTable, {"text": text, "id": self.id}, cursor = cursor)
        else:
            self.pool.UpdateFields(self.pool.FulltextTable, self.id, {"text": text}, cursor = cursor)
        cursor.close()


    def GetFulltext(self):
        """
        read fulltext from entry
        """
        sql = self.pool.GetSQLSelect(["text"], parameter={"id":self.id}, dataTable=self.pool.FulltextTable, singleTable=1)
        cursor = self.pool.GetCursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n", self.pool._debug, self.pool._log, name=self.pool.name)
        cursor.execute(sql)
        r = cursor.fetchone()
        cursor.close()
        if not r:
            return u""
        return self.pool.DecodeText(r[0])


    def DeleteFulltext(self):
        """
        Delete fulltext for entry
        """
        ph = self.pool.GetPlaceholder()
        aSql = u"DELETE FROM %s WHERE id = %s"%(self.pool.FulltextTable, ph)
        if self.pool._debug:
            STACKF(0,aSql+"\r\n\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
        aCursor = self.pool.GetCursor()
        aCursor.execute(aSql, (self.id,))
        aCursor.close()


    # Locking ---------------------------------------------------------------------

    def Lock(self, owner):
        return False

    def UnLock(self, owner, forceUnlock = False):
        return False

    def IsLocked(self, owner):
        return False


    # SQL functions -------------------------------------------------------------------------------------------

    def _GetFld(self, sql):
        """
        select single field from sql
        """
        try:
            cursor = self.pool.GetCursor()
            if self.pool._debug:
                STACKF(0,sql+"\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
            cursor.execute(sql)
            r = cursor.fetchone()
            cursor.close()
            if type(r[0]) == StringType:
                data = self.pool.EncodeText(r[0])
            else:
                data = r[0]
            return data
        except self.pool._Warning, e:
            try:    cursor.close()
            except: pass
            if self.pool._debug:
                STACKF(0,str(e)+"\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
            return None
    
    
    def _SQLSelect(self, flds, cursor = None, table=None):
        """
        select one entry and convert to dictionary
        """
        pool = self.pool
        if not table:
            table = pool.MetaTable
            param = {u"id": self.id}
        else:
            param = {u"id": self.GetDataRef()}
        sql = pool.GetSQLSelect(flds, param, dataTable = table, version=self.version, singleTable=1)

        c = 0
        if not cursor:
            c = 1
            cursor = pool.GetCursor()
        if pool._debug:
            STACKF(0,sql+"\r\n\r\n",pool._debug, pool._log,name=pool.name)
        cursor.execute(sql)
        r = cursor.fetchone()
        if c:
            cursor.close()
        if not r:
            return None
        return pool.ConvertRecToDict(r, flds)


    def _SQLSelectAll(self, metaFlds, dataFlds, cursor = None):
        """
        select meta and data of one entry and convert to dictionary
        """
        pool = self.pool
        flds2 = list(metaFlds) + list(dataFlds)
        param = {u"id": self.id}
        sql = pool.GetSQLSelect(flds2, param, dataTable = self.GetDataTbl(), version=self.version)

        c = 0
        if not cursor:
            c = 1
            cursor = pool.GetCursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n",pool._debug, pool._log,name=pool.name)
        cursor.execute(sql)
        r = cursor.fetchone()
        if c:
            cursor.close()
        if not r:
            raise TypeError, sql
        # split data and meta
        meta = pool.ConvertRecToDict(r[:len(metaFlds)], metaFlds)
        data = pool.ConvertRecToDict(r[len(metaFlds):], dataFlds)
        return meta, data


    def _PreloadAll(self):
        if self.virtual:
            return True
        if not self.dataTbl or not self.dataRef:
            if not self._PreloadMeta():
                return False
            self._PreloadData()
            return True
        dataTbl = self.GetDataTbl()
        c = self.pool.GetCursor()
        meta, data = self._SQLSelectAll(self.pool.structure.get(self.pool.MetaTable, version=self.version),
                                        self.pool.structure.get(dataTbl, version=self.version), c)
        c.close()
        if not meta:
            return False
        meta = self.pool.structure.deserialize(self.pool.MetaTable, None, meta)
        data = self.pool.structure.deserialize(dataTbl, None, data)
        self._UpdateCache(meta, data)
        return True


    def _PreloadMeta(self):
        if self.virtual:
            return True
        c = self.pool.GetCursor()
        meta = self._SQLSelect(self.pool.structure.get(self.pool.MetaTable, self.version), c)
        c.close()
        if not meta:
            return False
        meta = self.pool.structure.deserialize(self.pool.MetaTable, None, meta)
        self._UpdateCache(meta)
        return True


    def _PreloadData(self):
        if self.virtual:
            return True
        c = self.pool.GetCursor()
        dataTbl = self.GetDataTbl()
        data = self._SQLSelect(self.pool.structure.get(dataTbl, version=self.version), c, dataTbl)
        # load local roles, security
        c.close()
        if not data:
            return False
        data = self.pool.structure.deserialize(dataTbl, None, data)
        self._UpdateCache(None, data)
        return True


    def _PreloadStdMeta(self):
        if self.virtual:
            return True
        c = self.pool.GetCursor()
        meta = self._SQLSelect(self.pool.structure.stdMeta, c)
        c.close()
        if not meta:
            return False
        meta = self.pool.structure.deserialize(self.pool.MetaTable, None, meta)
        self._UpdateCache(meta)
        return True


    def _PreloadStdMetaData(self):
        if self.virtual:
            return True
        dataTbl = self.GetDataTbl()
        c = self.pool.GetCursor()
        meta, data = self._SQLSelectAll(self.pool.structure.stdMeta, self.pool.structure.get(dataTbl, version=self.version), c)
        c.close()
        if not meta:
            return False
        meta = self.pool.structure.deserialize(self.pool.MetaTable, None, meta)
        data = self.pool.structure.deserialize(dataTbl, None, data)
        self._UpdateCache(meta, data)
        return True


    # Internal -------------------------------------------------------------------------------------------

    def _InitNew(self, dataTable = None, user = ""):
        """
        sets create date and created by to now
        """
        aC = self.pool.GetCursor()
        self.dataTbl = dataTable
        aMeta = {}
        date = self.pool.GetDBDate()
        aMeta[u"pool_create"] = date
        aMeta[u"pool_change"] = date
        if user==None:
            user=""
        else:
            user=str(user)
        aMeta[u"pool_createdby"] = user
        aMeta[u"pool_changedby"] = user
        if self.dataTbl and self.dataTbl != u"":
            aMeta[u"pool_datatbl"] = self.dataTbl
        self.meta.update(aMeta, force=True)


    def _UpdateCache(self, meta = None, data = None, files = None):
        if meta:
            self.meta.SetContent(meta)
        if data:
            self.data.SetContent(data)
        if files:
            self.files.SetContent(files)



class Connection:
    """
    Base database connection class. Parameter depend on database version.

    config parameter in dictionary:
    user = database user
    pass = password user
    host = host server
    port = port server
    db = initial database name
    """

    def __init__(self, config = None, connectNow = True):
        self.db = None
        self.host = u""
        self.port = u""
        self.user = u""
        self.password = u""
        self.dbName = u""
        self.unicode = True
        self.timeout = 3

        if(config):
            self.SetConfig(config)
        if(connectNow):
            self.Connect()


    def __del__(self):
         self.Close()


    def Connect(self):
        """ Close and connect to server """
        self.Close()
        # "please use a subclassed connection"


    def Close(self):
        """ Close database connection """
        db = self._get()
        if db:
            db.close()
            self._set(None)

    
    def IsConnected(self):
        """ Check if database is connected """
        try:
            self.Ping()
            db = self._get()
            return db.cursor()!=None
        except:
            return False
    

    def VerifyConnection(self):
        """ reconnects if not connected """
        if not self.IsConnected():
            return self.Connect()
        return True
    
    
    def Ping(self):
        """ ping database server """
        db = self._get()
        return db.ping()


    def DB(self):
        """ returns the database connection class """
        db = self._get()
        if db:
            return db
        self.Connect()
        return self._get()


    def GetDBManager(self):
        """ returns the database manager obj """
        raise TypeError, "please use a subclassed connection"


    def Undo(self):
        """ Calls rollback on the current transaction, if supported """
        db = self._get()
        db.rollback()
        return


    def Commit(self):
        """ Calls commit on the current transaction, if supported """
        db = self._get()
        db.commit()
        return


    def Begin(self):
        """ Calls commit on the current transaction, if supported """
        return


    def GetUser(self):
        """ returns the current database user """
        return self.user


    def FmtParam(self, param):
        """format a parameter for sql queries like literal for mysql db"""
        return str(param)


    def Duplicate(self):
        """ Duplicates the current connection and returns a new unconnected connection """
        raise TypeError, "please use a subclassed connection"
        new = Connection(None, False)
        new.user = self.user
        new.host = self.host
        new.password = self.password
        new.port = self.port
        new.dbName = self.dbName
        return new


    def SetConfig(self, config):
        if type(config)==DictType:
            for k in config.keys():
                setattr(self, k, config[k])
        else:
            self.user = config.user
            self.host = config.host
            self.password = config.password
            self.port = config.port
            self.dbName = config.dbName
            self.unicode = config.unicode
            try:
                self.timeout = config.timeout
            except:
                pass

    def _get(self):
        # get stored database connection
        return self.db
        
    def _set(self, dbconn):
        # locally store database connection
        self.db = dbconn




#  Wrapper ---------------------------------------------------------------------------

class Wrapper(object):
    """
    Wrappers are mapping objects for data, files and meta. Content can be accessed as
    dictionary field.
    Changes are stored temporarily in memory.
    """

    __wrapper__ = 1

    def __init__(self, inEntry, content=None):
        #[a]
        self._entry_ = inEntry
        self._temp_ = {}
        self._content_ = None


    def __repr__(self):
        return str(type(self)) 
    
    def __dir__(self):
        return ["_temp_", "_content_", "_entry_"]
    
    def __setitem__(self, key, value):
        if key in (u"id",u"pool_datatbl", u"pool_dataref"):
            return
        if type(value) == StringType:
            value = self._entry_.pool.DecodeText(value)
        self._temp_[key] = value


    def __getitem__(self, key):
        if self._temp_.has_key(key):
            return self._temp_[key]
        if not self._content_:
            self._Load()
        return self._content_.get(key)


    def __getattr__(self, key):
        if key in self.__dict__.keys():
            return self.__dict__[key]
        if self._temp_.has_key(key):
            return self._temp_[key]
        if not self._content_:
            self._Load()
        return self._content_.get(key)


    def clear(self):
        """
        Reset contents, temp data and entry obj
        """
        #self._entry_ = None
        #self._content_ = None
        self._temp_.clear()


    def copy(self):
        """
        Returns a copy of current content
        """
        if not self._content_:
            self._Load()
        c = self._content_.copy()
        c.update(self._temp_)
        return c


    def has_key(self, key):
        if self.HasTempKey(key):
            return True
        return key in self.keys()


    def get(self, key, default=None):
        try:
            data = self[key]
            if data == None:
                return default
            return data
        except:
            return default


    def set(self, key, data):
        if type(data) == StringType:
            data = self._entry_.pool.DecodeText(data)
        self[key] = data


    def update(self, dict, force = False):
        if force:
            for k in dict.keys():
                data = dict[k]
                if type(data) == StringType:
                    dict[k] = self._entry_.pool.DecodeText(data)
            self._temp_.update(dict)
            return
        for k in dict.keys():
            self[k] = dict[k]


    def keys(self):
        if not self._content_:
            self._Load()
        t = self._content_.keys()
        t += self._temp_.keys()
        return t



    def IsEmpty(self):                return self._content_ == None
    def GetTemp(self):                return self._temp_
    def HasTemp(self):                return self._temp_ != {}
    def GetTempKey(self, key):        return self._temp_.get(key)
    def HasTempKey(self, key):        return self._temp_.has_key(key)

    def GetEntry(self):                return self._entry_

    def SetContent(self, content):
        if not self._content_:
            self._content_ = content
        else:
            self._content_.update(content)

    def EmptyTemp(self):
        self._temp_.clear()

    def Close(self):
        self._entry_ = None
        self._temp_.clear()
        self._content_ = None

    def _Load(self):
        self._content_ = {}
        pass


class MetaWrapper(Wrapper):
    """
    wrapper class for meta content
    """

    def _Load(self):
        self._content_ = {}
        self._entry_._PreloadMeta()



class DataWrapper(Wrapper):
    """
    wrapper class for data content
    """

    def _Load(self):
        self._content_ = {}
        self._entry_._PreloadData()


class FileWrapper(Wrapper):
    """
    wrapperclass for files. contains only filemta and returns file streams on read.
    update and __setitem__ take File object with o.file and o.filename attr as parameter
    entry = {"filename": "", "path": <absolute path for temp files>, "file": <file stream>}
    """

    def __setitem__(self, key, filedata):
        """
        filedata can be a dictionary, File object or file path
        """
        if not filedata:
            if key in self._temp_:
                del self._temp_[key]
            elif self._content_ and key in self._content_:
                del self._content_[key]
            return
        if type(filedata) == DictType:
            file = File(key, filedict=filedata, fileentry=self._entry_)
            filedata = file
        elif type(filedata) == StringType:
            # load from temp path
            file = File(key, fileentry=self._entry_)
            file.SetFromPath(filedata)
            filedata = file
        filedata.tempfile = True
        self._temp_[key] = filedata


    def set(self, key, filedata):
        self[key] = filedata


    def SetContent(self, files):
        self._content_ = {}
        for f in files:
            self._content_[f["tag"]] = f


    def _Load(self):
        files = self._entry_.Files()
        self._content_ = {}
        for f in files:
            self._content_[f["tag"]] = f
        return self._content_.keys()


#  Pool Structure ---------------------------------------------------------------------------


class PoolStructure:
    """
    Data Pool 2 Structure handling. Defines a table field mapping. If field types are available serializing 
    and deserializing is performed on database reads and writes.

    ::
    
        structure =
            {
             meta:   (field1, field2, ...),
             type1_table: (field5, field6, ...),
             type2_table: (field8, field9, ...),
            }

        fieldtypes = 
            {
             meta: {field1: string, field2: number},
             type1_table: {field5: DateTime, field6: text},
             type2_table: {field8: DateTime, field9: text},
            }
            
        stdMeta = (field1, field2)

    """
    MetaTable = u"pool_meta"
    
    def __init__(self, structure=None, fieldtypes=None, stdMeta=None, **kw):
        #
        self.stdMeta = ()
        self.structure = {}
        self.fieldtypes = {}
        if structure:
            self.Init(structure, fieldtypes, stdMeta, **kw)


    def Init(self, structure, fieldtypes=None, stdMeta=None, **kw):
        s = structure.copy()
        meta = list(s[self.MetaTable])
        # add default fields
        if not u"pool_dataref" in s[self.MetaTable]:
            meta.append(u"pool_dataref")
        if not u"pool_datatbl" in s[self.MetaTable]:
            meta.append(u"pool_datatbl")
        s[self.MetaTable] = tuple(meta)
        for k in s:
            s[k] = tuple(s[k])
        self.structure = s
        
        if fieldtypes:
            self.fieldtypes = fieldtypes
        
        if stdMeta:
            m = list(stdMeta)
            for f in StdMetaFlds:
                if not f in m:
                    m.append(f)
            self.stdMeta = tuple(m)


    def IsEmpty(self):
        return self.structure=={}

    
    def __getitem__(self, key, version=None):
        return self.structure[key]

    def get(self, key, default=None, version=None):
        return self.structure.get(key, default)

    def has_key(self, key, version=None):
        return self.structure.has_key(key)

    def keys(self, version=None):
        return self.structure.keys()
    
    
    def serialize(self, table, field, value):
        # if field==None and value is a dictionary multiple values are deserialized
        if field==None and isinstance(value, dict):
            for field, v in value.items():
                try:        t = self.fieldtypes[table][field]
                except:     t = None
                value[field] = self._se(v, t)
        else:
            try:        t = self.fieldtypes[table][field]
            except:     t = None
            value = self._se(value, t)
        return value
        

    def deserialize(self, table, field, value):
        # if field==None and value is a dictionary multiple values are deserialized
        if field==None and isinstance(value, dict):
            for field, v in value.items():
                try:        t = self.fieldtypes[table][field]
                except:     t = None
                value[field] = self._de(v, t)
        else:
            try:        t = self.fieldtypes[table][field]
            except:     t = None
            value = self._de(value, t)
        return value


    def _se(self, value, fieldtype):
        if not fieldtype:
            if type(value) == InstanceType and str(value.__class__).find("DvDateTime") != -1:
                return value.GetDBMySql()
            elif type(value) in (ListType, TupleType):
                return ConvertListToStr(value)
            return value
        
        if fieldtype in ("date", "datetime", "timestamp"):
            if isinstance(value, DvDateTime):
                value = value.GetDBMySql()
            else:
                value = str(value)
        
        elif fieldtype in ("mselection", "mcheckboxes", "list", "urllist", "unitlist"):
            if type(value) in (ListType, TupleType):
                value = ConvertListToStr(value)

        elif fieldtype in ("bool"):
            if isinstance(value, basestring):
                if value.lower()=="true":
                    value = 1
                elif value.lower()=="false":
                    value = 0
            else:
                try:
                    value = int(value)
                except:
                    value = 0

        return value

    def _de(self, value, fieldtype):
        if not fieldtype:
            return value

        if fieldtype in ("date", "datetime", "timestamp"):
            if isinstance(value, basestring):
                try:
                    value = iso8601.parse_date(value)
                except:
                    d = DvDateTime(value)
                    value = datetime.fromtimestamp(d.GetFloat())
                    
        elif fieldtype in ("mselection", "mcheckboxes", "urllist", "unitlist"):
            if not type(value) in (ListType, TupleType):
                value = ConvertToList(value)

        return value
    
    



class NotFound(Exception):
    """ raised if entry not found """
    pass

class ConnectionError(Exception):
    """    No connection """
    pass
