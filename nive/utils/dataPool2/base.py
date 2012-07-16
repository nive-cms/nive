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
MetaTable = u"pool_meta"
VersionTable = u"pool_versions"
VersionMapTable = u"pool_vmap"
StdEncoding = u"utf-8"
EncodeMapping = u"replace"
StdMetaFlds = (u"id", u"pool_dataref", u"pool_datatbl")
#

class OperationalError(Exception):
    pass
class ProgrammingError(Exception):
    pass
class Warning(Exception):
    pass


class Base:
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

    def GetSQLSelect(self, flds, parameter={}, dataTable = "", start = 0, max = 0, **kw):
        """
        create select statement based on pool_structure and parameter.
        aggregate functions can be included in flds but must be marked with
        prefix - e.g. "-count(*)"
        Tables in statement get alias
        meta__ for pool_meta
        data__ for data table
        version__ for version table

        flds: select fields
        parameter: where clause parameter
        dataTable: add join statement for the table

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
        start: start number of record to be returned
        max: maximum nubers of records in result
        ascending: result sort order ascending or descending
        """
        aF = u""
        aOpList = kw.get("operators",{})
        jointype = aOpList.get("jointype", u"INNER")
        singleTable = kw.get("singleTable",0)
        version = kw.get("version")
        aMetaStructure = self.structure.get(MetaTable, version=version)
        mapJoinFld = kw.get("mapJoinFld")
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
                elif f2 in aMetaStructure or f2 == u"pool_stag":
                    aTable = u"meta__."
                elif dataTable != u"":
                    if jointype.lower() != u"inner":
                        if f == mapJoinFld:
                            aF += u"IF(meta__.pool_datatbl='%s', %s, meta__.title)" % (dataTable, f)
                        else:
                            aF += u"IF(meta__.pool_datatbl='%s', %s, '')" % (dataTable, f)
                        continue
                    aTable = u"data__."
            if(len(aF) > 0):
                aF += u", "
            aF += aTable + f

        aWhere = ""
        aCombi = kw.get("logicalOperator")
        if not aCombi:
            aCombi = u"AND"
        else:
            aCombi = aCombi.upper()
            if not aCombi in (u"AND",u"OR",u"NOT"):
                aCombi = u"AND"
        aAddCombi = False
        connection = self.GetConnection()

        for aK in parameter.keys():
            aT = type(parameter[aK])
            aKey = aK

            aOperator = u"="
            if aOpList:
                if aOpList.has_key(aK):
                    aOperator = aOpList.get(aK)

            if singleTable:
                aTable = u""
            else:
                aTable = u"meta__."
                # aggregate functions marked with - e.g. "-count(*)"
                if aK[0] == u"-":
                    aTable = u""
                    aKey = aK[1:]
                elif aK in aMetaStructure or aK == u"pool_stag":
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
                    if aAddCombi:
                        aWhere += u" " + aCombi + u" "
                    aWhere += u"%s%s %s %s " % (aTable, aKey, aOperator, aW)
                elif aOperator == u"BETWEEN":
                    if aW == u"":
                        continue
                    if aAddCombi:
                        aWhere += u" " + aCombi + u" "
                    aWhere += u"%s%s %s %s " % (aTable, aKey, aOperator, aW)
                else:
                    aW = connection.FmtParam(aW)
                    if aAddCombi:
                        aWhere += u" " + aCombi + u" "
                    aWhere += u"%s%s %s %s " % (aTable, aKey, aOperator, aW)
                aAddCombi = True

            # fmt list values
            elif aT in (TupleType, ListType):
                aW = parameter[aK]
                if aW == None or len(aW)==0:
                    continue
                if aAddCombi:
                    aWhere += u" " + aCombi + u" "
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
                    aWhere += u"%s%s %s (%s) " % (aTable, aKey, aOperator, aW)
                elif aOperator == u"BETWEEN":
                    if len(aW) < 2:
                        continue
                    aWhere += u"%s%s %s %s AND %s" % (aTable, aKey, aOperator, connection.FmtParam(aW[0]), connection.FmtParam(aW[1]))
                else:
                    aW = ConvertToStr(aW, "list")
                    aW = self.DecodeText(parameter[aK])
                    aW = u"%%%s%%" % (aW)
                    aW = connection.FmtParam(aW)
                    aWhere += u"%s%s LIKE %s " % (aTable, aKey, aW)
                aAddCombi = True

            # fmt number values
            elif aT in (IntType, LongType, FloatType):
                if aAddCombi:
                    aWhere += u" " + aCombi + u" "
                if aOperator == u"LIKE":
                    aOperator = u"="
                aW = connection.FmtParam(parameter[aK])
                aWhere += u"%s%s %s %s" % (aTable, aKey, aOperator, aW)
                aAddCombi = True

        condition = kw.get("condition")
        if condition != None and condition != u"":
            if aWhere != u"":
                aWhere += u" %s %s" %(aCombi, condition)
            else:
                aWhere = condition
        if aWhere != u"":
            aWhere = u"WHERE %s" % aWhere

        aOrder = u"ASC"
        if kw.get("ascending", 1) == 0:
            aOrder = u"DESC"

        # map sort fields
        sort = kw.get("sort", u"")
        if sort==None:
            sort = u""
        if sort != u"" and not singleTable:
            aTable = u"meta__."
            s = sort.split(u",")
            sort = u""
            for sortfld in s:
                sortfld = DvString(sortfld)
                sortfld.Trim()
                sortfld = str(sortfld)
                if len(sortfld) > 0 and sortfld[0] == u"-":
                    aTable = u""
                    sortfld = sortfld[1:]
                #elif sortfld in aMetaStructure[1]:
                #    aTable = "version__."
                elif sortfld in aMetaStructure or sortfld == u"pool_stag":
                #elif sortfld in aMetaStructure[0] or sortfld == "pool_stag":
                    aTable = u"meta__."
                elif dataTable != u"":
                    aTable = u"data__."
                if sort != u"":
                    sort += u", "
                sort += aTable + sortfld

        customJoin = kw.get("join", u"")
        if customJoin == None:
            customJoin = u""

        join = u""
        aJodata = u""
        if not singleTable:
            # joins
            if version:
                BREAK("version")
                join = u"INNER JOIN %s AS version__ ON (meta__.id = version__.id)" % (VersionTable)

            if dataTable != u"":
                if version:
                    BREAK("version")
                    aJodata = u"%s JOIN %s AS data__ ON (version__.pool_dataref = data__.id) " % (jointype, dataTable)
                else:
                    aJodata = u"%s JOIN %s AS data__ ON (meta__.pool_dataref = data__.id) " % (jointype, dataTable)

        limit = ""
        if max:
            limit = self.FmtLimit(start, max)

        groupby = u""
        if kw.get("groupby"):
            groupby = u"GROUP BY %s" % kw.get("groupby")

        table = MetaTable + u" AS meta__"
        if singleTable:
            table = dataTable

        if sort != u"":
            sort = u"ORDER BY %s %s" % (sort, aOrder)

        aSql = u"""
        SELECT %s
        FROM %s
        %s %s %s
        %s
        %s %s %s
        """ % (aF, table, join, aJodata, customJoin, aWhere, groupby, sort, limit)
        return aSql


    def FmtLimit(self, start, max):
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
            aM = u"""MATCH (pool_fulltext.text) AGAINST (%s)""" % (searchPhrase)
        else:
            aM = u"""pool_fulltext.text LIKE %s""" % (searchPhrase)

        if not kw.get("skipRang"):
            aSql = aSql.replace(u"SELECT ", "SELECT %s AS rang__, " % (aM))

        if not searchPhrase in (u"", u"'%%'", None):
            if aSql.find(u"WHERE ") == -1:
                aSql = aSql.replace(u"ORDER BY ", "WHERE %s \r\nORDER BY " % (aM))
            else:
                aSql = aSql.replace(u"WHERE ", "WHERE %s AND " % (aM))
        if kw.get("version"):
            BREAK("version")
            aSql = aSql.replace(u"INNER JOIN ", "LEFT JOIN pool_fulltext ON (meta__.id = pool_fulltext.id) \r\nINNER JOIN ")
        else:
            aSql = aSql.replace(u"FROM pool_meta AS meta__", "FROM pool_meta AS meta__\r\n\t\tLEFT JOIN pool_fulltext ON (meta__.id = pool_fulltext.id)")
        #aSql = aSql.replace("ORDER BY ", "ORDER BY rang__, ")
        return aSql


    def Query(self, sql, values = None):
        """
        execute a query on the database. non unicode texts are converted according to codepage settings.
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
        try:
            r = c.fetchall()
        except self._ProgrammingError, e:
            r = ()
            pass
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


    def QueryRaw(self, sql, values = None):
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


    def UpdateFields(self, table, id, data, cursor = None):
        """
        updates multiple fields in the table.
        codepage and dates are converted automatically
        returns the converted data 
        """
        aSql = u"UPDATE %s SET " % (table)
        dataList = []
        ph = self.GetPlaceholder()
        for aK in data.keys():
            aSql += aK + u"=%s,"%(ph)

            if type(data[aK]) == StringType:
                data[aK] = self.DecodeText(data[aK])
            dataList.append(self.structure.serialize(table, aK, data[aK]))
            data[aK] = dataList[-1]

        aSql = aSql[:-1]
        aSql += u" WHERE id = %d" % (id)

        if self._debug:
            STACKF(0,aSql+"\r\n",self._debug, self._log,name=self.name)

        aClose = 0
        if not cursor:
            aClose = 1
            cursor = self.GetCursor()
        try:
            cursor.execute(aSql, dataList)
        except self._Warning:
            pass
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        if aClose:
            cursor.close()
        return data


    def InsertFields(self, table, data, cursor = None):
        """
        insert row with multiple fields in the table.
        codepage and dates are converted automatically
        returns the converted data 
        """
        dataList = []
        flds = u""
        phdata = u""
        ph = self.GetPlaceholder()
        for aK in data.keys():
            if flds != u"":
                flds += u","
                phdata += u","
            flds += aK
            phdata += ph

            if type(data[aK]) == StringType:
                data[aK] = self.DecodeText(data[aK])
            dataList.append(self.structure.serialize(table, aK, data[aK]))
            data[aK] = dataList[-1]

        aSql = u"INSERT INTO %s (%s) VALUES (%s)" % (table, flds, phdata)

        if self._debug:
            STACKF(0,aSql+"\r\n",self._debug, self._log,name=self.name)

        aClose = 0
        if not cursor:
            aClose = 1
            cursor = self.GetCursor()
        try:
            cursor.execute(aSql, dataList)
        except self._Warning:
            pass
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        if aClose:
            cursor.close()
        return data


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


    def DeleteIDFromTable(self, table, id):
        """
        Delete record referenced by id
        """
        aSql = u"DELETE FROM %s WHERE id = %s" % (table, self.GetPlaceholder())
        if self._debug:
            STACKF(0,aSql+"\r\n\r\n",self._debug, self.pool._log,name=self.pool.name)
        aCursor = self.GetCursor()
        aCursor.execute(aSql, (id,))
        aCursor.close()


    def ConvertRecToDict(self, rec, flds):
        """
        Convert a database record tuple to dictionary based on flds list
        """
        aD = {}
        if not rec:
            return aD

        for aI in range(len(flds)):
            aStr = flds[aI]
            # data unicode and codepage conversion
            if type(rec[aI]) == StringType:
                aD[aStr] = self.EncodeText(rec[aI])
            else:
                aD[aStr] = rec[aI]
        return aD


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


    # Entries -------------------------------------------------------------------------------------------

    def CreateEntry(self, pool_datatbl, id = 0, user = "", **kw):
        """
        Create new entry.
        Requires pool_datatbl as parameter
        """
        if id:
            id, dataref = self._CreateFixID(id, dataTbl=pool_datatbl)
        else:
            id, dataref = self._CreateNewID(table=MetaTable, dataTbl=pool_datatbl)
        if not id:
            #self._Error(-100)
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
        aC = self.GetCursor()
        ph = self.GetPlaceholder()
        # base record
        if self._debug:
            STACKF(0,u"SELECT pool_dataref, pool_datatbl FROM %s WHERE id = %s"%(MetaTable, ph)+"\r\n",self._debug, self._log,name=self.name)
        aC.execute(u"SELECT pool_dataref, pool_datatbl FROM %s WHERE id = %s"%(MetaTable, ph), (id,))
        r = aC.fetchone()
        if not r:
            return 0
        dataref = r[0]
        datatbl = r[1]

        # data table
        if self._debug:
            STACKF(0,u"DELETE FROM %s WHERE id = %s"%(datatbl, ph),0, self._log,name=self.name)
            STACKF(0,u"DELETE FROM %s WHERE id = %s"%(MetaTable, ph),0, self._log,name=self.name)
            STACKF(0,u"DELETE FROM pool_fulltext WHERE id = %s",0, self._log,name=self.name)
            #STACKF(0,u"DELETE FROM pool_lroles WHERE id = %s",0, self._log,name=self.name)
            #STACKF(0,u"DELETE FROM pool_security WHERE id = %s",0, self._log,name=self.name)

        aC.execute(u"DELETE FROM %s WHERE id = %s"%(datatbl, ph), (dataref,))
        # meta table
        aC.execute(u"DELETE FROM %s WHERE id = %s"%(MetaTable, ph), (id,))
        # fulltext
        try:
            aC.execute(u"DELETE FROM pool_fulltext WHERE id = %s"%(ph), (id,))
        except:
            pass

        # delete files
        aResultFile = self._DeleteFiles(id, version)

        aC.close()
        return 1


    def IsIDUsed(self, id):
        """
        Query database if id exists
        """
        aC = self.GetCursor()
        ph = self.GetPlaceholder()
        if self._debug:
            STACKF(0,u"SELECT id FROM %s WHERE id = %d" % (MetaTable, id)+"\r\n",self._debug, self._log,name=self.name)
        aC.execute(u"SELECT id FROM %s WHERE id = %s"%(MetaTable, ph), (id,))
        aN = aC.fetchall()
        aC.close()
        return len(aN) == 1


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
            flds = self.structure.get(u"pool_meta", version=version)
            if not flds:
                raise ConfigurationError, "Meta layer is empty."
            parameter = {"id": ids}
            operators = {"id": u"IN"}
            sql = self.GetSQLSelect(flds, parameter=parameter, dataTable=MetaTable, max=len(ids), sort=sort, operators=operators, singleTable=1)
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
            sql = self.GetSQLSelect(flds, parameter=parameter, dataTable=MetaTable, sort=sort, groupby=u"pool_datatbl", operators=operators, singleTable=1)
            tables = []
            for r in self.Query(sql):
                if not r["pool_datatbl"] in tables:
                    tables.append(r[0])
        t = u""
        fldsm = self.structure.get(u"pool_meta", version=version)
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
        (select pool_unitref from pool_meta where id = ref1) as ref2,
        (select pool_unitref from pool_meta where id = ref2) as ref3,
        (select pool_unitref from pool_meta where id = ref3) as ref4,
        (select pool_unitref from pool_meta where id = ref4) as ref5,
        (select pool_unitref from pool_meta where id = ref5) as ref6,
        (select pool_unitref from pool_meta where id = ref6) as ref7,
        (select pool_unitref from pool_meta where id = ref7) as ref8,
        (select pool_unitref from pool_meta where id = ref8) as ref9,
        (select pool_unitref from pool_meta where id = ref9) as ref10,
        """

        if parameter:
            parameter = u"where " + parameter
        sql = u"""
        select %s id
        from pool_meta %s
        order by pool_unitref, %s
        """ % (refs, parameter, sort)
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
        (select pool_unitref from pool_meta where id = ref1) as ref2,
        (select pool_unitref from pool_meta where id = ref2) as ref3,
        (select pool_unitref from pool_meta where id = ref3) as ref4,
        (select pool_unitref from pool_meta where id = ref4) as ref5,
        (select pool_unitref from pool_meta where id = ref5) as ref6,
        (select pool_unitref from pool_meta where id = ref6) as ref7,
        (select pool_unitref from pool_meta where id = ref7) as ref8,
        (select pool_unitref from pool_meta where id = ref8) as ref9,
        (select pool_unitref from pool_meta where id = ref9) as ref10,
        """

        if parameter:
            parameter = u"where " + parameter
        sql = u"""
        select 
        %s 
        %s
        from pool_meta %s
        order by pool_unitref, %s
        """ % (refs, ConvertListToStr(flds), parameter, sort)
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
        if id == 0:
            return []
        #select pool_unitref as ref1,
        #(select pool_unitref from pool_meta where id = ref1) as ref2,
        #(select pool_unitref from pool_meta where id = ref2) as ref3,
        #(select pool_unitref from pool_meta where id = ref3) as ref4,
        #(select pool_unitref from pool_meta where id = ref4) as ref5,
        #(select pool_unitref from pool_meta where id = ref5) as ref6,
        #(select pool_unitref from pool_meta where id = ref6) as ref7,
        #(select pool_unitref from pool_meta where id = ref7) as ref8,
        #(select pool_unitref from pool_meta where id = ref8) as ref9,
        #(select pool_unitref from pool_meta where id = ref9) as ref10
        #from pool_meta where id = %d

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
        FROM pool_meta AS t1
        LEFT JOIN pool_meta AS t2 ON t2.id = t1.pool_unitref
        LEFT JOIN pool_meta AS t3 ON t3.id = t2.pool_unitref
        LEFT JOIN pool_meta AS t4 ON t4.id = t3.pool_unitref
        LEFT JOIN pool_meta AS t5 ON t5.id = t4.pool_unitref
        LEFT JOIN pool_meta AS t6 ON t6.id = t5.pool_unitref
        LEFT JOIN pool_meta AS t7 ON t7.id = t6.pool_unitref
        LEFT JOIN pool_meta AS t8 ON t8.id = t7.pool_unitref
        LEFT JOIN pool_meta AS t9 ON t9.id = t8.pool_unitref
        LEFT JOIN pool_meta AS t10 ON t10.id = t9.pool_unitref
        WHERE t1.id = %d;""" % (id)
        
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
            if id == 0:
                break
            parents.insert(0, id)
        aC.close()
        return parents


    def GetParentTitles(self, id):
        """
        Returns titles of parents for the given id.
        maximum 10 parents
        """
        if id == 0:
            return []
        aC = self.GetCursor()
        #select pool_unitref as ref1, title as title1,
        #(select pool_unitref from pool_meta where id = ref1) as ref2, (select title from pool_meta where id = ref1) as title2,
        #(select pool_unitref from pool_meta where id = ref2) as ref3, (select title from pool_meta where id = ref2) as title3,
        #(select pool_unitref from pool_meta where id = ref3) as ref4, (select title from pool_meta where id = ref3) as title4,
        #(select pool_unitref from pool_meta where id = ref4) as ref5, (select title from pool_meta where id = ref4) as title5,
        #(select pool_unitref from pool_meta where id = ref5) as ref6, (select title from pool_meta where id = ref5) as title6,
        #(select pool_unitref from pool_meta where id = ref6) as ref7, (select title from pool_meta where id = ref6) as title7,
        #(select pool_unitref from pool_meta where id = ref7) as ref8, (select title from pool_meta where id = ref7) as title8,
        #(select pool_unitref from pool_meta where id = ref8) as ref9, (select title from pool_meta where id = ref8) as title9,
        #(select pool_unitref from pool_meta where id = ref9) as ref10, (select title from pool_meta where id = ref9) as title10
        #from pool_meta where id = %d

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
        FROM pool_meta AS t1
        LEFT JOIN pool_meta AS t2 ON t2.id = t1.pool_unitref
        LEFT JOIN pool_meta AS t3 ON t3.id = t2.pool_unitref
        LEFT JOIN pool_meta AS t4 ON t4.id = t3.pool_unitref
        LEFT JOIN pool_meta AS t5 ON t5.id = t4.pool_unitref
        LEFT JOIN pool_meta AS t6 ON t6.id = t5.pool_unitref
        LEFT JOIN pool_meta AS t7 ON t7.id = t6.pool_unitref
        LEFT JOIN pool_meta AS t8 ON t8.id = t7.pool_unitref
        LEFT JOIN pool_meta AS t9 ON t9.id = t8.pool_unitref
        LEFT JOIN pool_meta AS t10 ON t10.id = t9.pool_unitref
        WHERE t1.id = %d;""" % (id)        
        
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

    def GetCountEntries(self, table = MetaTable):
        """
        Returns the total number of entries in the pool
        """
        aC = self.GetCursor()
        aC.execute(u"SELECT COUNT(*) FROM %s" % (table))
        aN = aC.fetchone()[0]
        aC.close()
        return aN

    def Log(self, s):
        DUMP(s, self._log,name=self.name)


    def _Error(self, err):
        """
        Lookup error message
    
        Erors
        -----
        0 = no error
    
        -100 = entry already exists
        -101 = entry not found
        -102 = entry invalid
        -200 = key Wildcard
        -201 = key invalid
        -202 = prop invalid
        -300 = error save file
        -301 = error open dest data file for writing
        -302 = error write data to dest file
        -303 = error read data from file
        -304 = file not found
        -305 = error delete file
        -306 = error copy file
        -307 = file exists
        -308 = error save meta
        -309 = error save data
        -400 = no connection
        -401 = connect failed
        -402 = unknown user
        -403 = unknown pass

        -500 = error open meta
        -501 = error create meta
        -502 = error dump meta
        -503 = error write stream data
        -504 = error create data
        -505 = error read meta
        -506 = error read data
        -507 = error lookup data structure
        """
        return str(err)

    def _DeleteFiles(self, id, version):
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

        # sql select id
        ph = self.pool.GetPlaceholder()
        if self.version:
            BREAK("version")
            aSql = u"SELECT id FROM %s WHERE id = %s" % (MetaTable, ph)
        else:
            aSql = u"SELECT id FROM %s WHERE id = %s" % (MetaTable, ph)
        aC = self.pool.GetCursor()
        if self.pool._debug:
            STACKF(0,aSql+"\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
        aC.execute(aSql, (self.id,))
        r = aC.fetchone() != None
        aC.close()
        return r


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
                self.pool.UpdateFields(MetaTable, self.id, self.meta.GetTemp(), cursor)
            # data
            if self.data.HasTemp():
                self.pool.UpdateFields(self.GetDataTbl(), self.GetDataRef(), self.data.GetTemp(), cursor)
            # files
            if self.files.HasTemp():
                temp = self.files.GetTemp()
                if temp:
                    for tag in temp.keys():
                        file = temp[tag]
                        result = self.SetFile(tag, file)
                        if not result:
                            raise TypeError, "File save error (%s)." #%(self.GetError())
            cursor.close()
            self.pool.Commit()
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
            raise Exception, e
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

        sql =u"SELECT %s FROM %s WHERE id = %s" % (fld, MetaTable, self.id)
        data = self._GetFld(sql)
        data = self.pool.structure.deserialize(MetaTable, fld, data)
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
        sql = u"SELECT %s FROM %s WHERE id = %s" % (fld, tbl, self.GetDataRef())
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

        data =  self._SQLSelect(self.pool.structure.get(MetaTable, version=self.version))
        data = self.pool.structure.deserialize(MetaTable, None, data)
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
            #self._Error(-507)
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
        temp = self.pool.UpdateFields(MetaTable, self.id, {fld:data})
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
        ph = self.pool.GetPlaceholder()
        if self.version:
            BREAK("version")
            aLang = self.GetLanguage()
            aSql = u"SELECT id FROM pool_fulltext WHERE id = %s AND pool_versions = '%s'" % (self.id, aLang)
        else:
            aSql = u"SELECT id FROM pool_fulltext WHERE id = %s"%(ph)
        aCursor = self.pool.GetCursor()
        if self.pool._debug:
            STACKF(0,aSql+"\r\n\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
        aCursor.execute(aSql, (self.id,))
        r = aCursor.fetchone()
        if not r:
            aSql = u"INSERT INTO pool_fulltext (text, id) VALUES (%s, %s)" %(ph, ph)
        else:
            aSql = u"UPDATE pool_fulltext SET text = %s WHERE id = %s" %(ph, ph)
        text = self.pool.DecodeText(text)
        if self.pool._debug:
            STACKF(0,aSql+"\r\n\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
        aCursor.execute(aSql, (text, self.id))
        aCursor.close()


    def GetFulltext(self):
        """
        read fulltext from entry
        """
        ph = self.pool.GetPlaceholder()
        if self.version:
            BREAK("version")
            aLang = self.GetLanguage()
            aSql = u"SELECT id,text FROM pool_fulltext WHERE id = %s AND pool_versions = '%s'" % (self.id, aLang)
        else:
            aSql = u"SELECT id,text FROM pool_fulltext WHERE id = %s"%(ph)
        aCursor = self.pool.GetCursor()
        if self.pool._debug:
            STACKF(0,aSql+"\r\n\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
        aCursor.execute(aSql, (self.id,))
        r = aCursor.fetchone()
        aCursor.close()
        if not r:
            return ""
        text = self.pool.DecodeText(r[1])
        return text


    def DeleteFulltext(self):
        """
        Delete fulltext for entry
        """
        ph = self.pool.GetPlaceholder()
        if self.version:
            BREAK("version")
            aLang = self.GetLanguage()
            aSql = u"DELETE FROM pool_fulltext WHERE id = %s AND pool_versions = '%s'" % (self.id, aLang)
        else:
            aSql = u"DELETE FROM pool_fulltext WHERE id = %s"%(ph)
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
        if not table:
            table = MetaTable
            param = {u"id": self.id}
        else:
            param = {u"id": self.GetDataRef()}
        sql = self.pool.GetSQLSelect(flds, param, dataTable = table, version=self.version, singleTable=1)

        c = 0
        if not cursor:
            c = 1
            cursor = self.pool.GetCursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
        cursor.execute(sql)
        r = cursor.fetchone()
        if c:
            cursor.close()
        if not r:
            return None
        return self.pool.ConvertRecToDict(r, flds)


    def _SQLSelectAll(self, metaFlds, dataFlds, cursor = None):
        """
        select meta and data of one entry and convert to dictionary
        """
        flds2 = list(metaFlds) + list(dataFlds)

        param = {u"id": self.id}
        sql = self.pool.GetSQLSelect(flds2, param, dataTable = self.GetDataTbl(), version=self.version)

        c = 0
        if not cursor:
            c = 1
            cursor = self.pool.GetCursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
        cursor.execute(sql)
        r = cursor.fetchone()
        if c:
            cursor.close()
        if not r:
            raise TypeError, sql
        # split data and meta
        meta = self.pool.ConvertRecToDict(r[:len(metaFlds)], metaFlds)
        data = self.pool.ConvertRecToDict(r[len(metaFlds):], dataFlds)
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
        meta, data = self._SQLSelectAll(self.pool.structure.get(MetaTable, version=self.version),
                                        self.pool.structure.get(dataTbl, version=self.version), c)
        c.close()
        if not meta:
            return False
        meta = self.pool.structure.deserialize(MetaTable, None, meta)
        data = self.pool.structure.deserialize(dataTbl, None, data)
        self._UpdateCache(meta, data)
        return True


    def _PreloadMeta(self):
        if self.virtual:
            return True
        c = self.pool.GetCursor()
        meta = self._SQLSelect(self.pool.structure.get(MetaTable, self.version), c)
        c.close()
        if not meta:
            return False
        meta = self.pool.structure.deserialize(MetaTable, None, meta)
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
        meta = self.pool.structure.deserialize(MetaTable, None, meta)
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
        meta = self.pool.structure.deserialize(MetaTable, None, meta)
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
        return self._content_.keys()


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
            file = File(key, filedict=filedata)
            filedata = file
        elif type(filedata) == StringType:
            # load from temp path
            file = File(key)
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
             pool_meta:   (field1, field2, ...),
             type1_table: (field5, field6, ...),
             type2_table: (field8, field9, ...),
            }

        fieldtypes = 
            {
             pool_meta: {field1: string, field2: number},
             type1_table: {field5: DateTime, field6: text},
             type2_table: {field8: DateTime, field9: text},
            }
            
        stdMeta = (field1, field2)

    """

    def __init__(self, structure=None, fieldtypes=None, stdMeta=None, **kw):
        #
        self.stdMeta = ()
        self.structure = {}
        self.fieldtypes = {}
        if structure:
            self.Init(structure, fieldtypes, stdMeta, **kw)


    def Init(self, structure, fieldtypes=None, stdMeta=None, **kw):
        s = structure.copy()
        meta = list(s[u"pool_meta"])
        # add default fields
        if not u"pool_dataref" in s[u"pool_meta"]:
            meta.append(u"pool_dataref")
        if not u"pool_datatbl" in s[u"pool_meta"]:
            meta.append(u"pool_datatbl")
        s[u"pool_meta"] = tuple(meta)
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
