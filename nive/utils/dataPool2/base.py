#----------------------------------------------------------------------
# Nive cms
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

import weakref
from time import time
from time import localtime

from nive.utils.utils import ConvertListToStr
from nive.utils.utils import STACKF, DUMP
from nive.utils.path import DvPath
from nive.utils.dateTime import DvDateTime

from nive.definitions import ConfigurationError, OperationalError, ProgrammingError, Warning

from nive.utils.dataPool2.files import File
from nive.utils.dataPool2.structure import PoolStructure, DataWrapper, MetaWrapper, FileWrapper


# Pool Constants ---------------------------------------------------------------------------

#
StdEncoding = u"utf-8"
EncodeMapping = u"replace"


class Base(object):
    """
    Data Pool 2 SQL Base implementation

    Manage typed data units consisting of meta layer, data layer and files.
    Meta layer is the same for all units, data layer is based on types and files
    are stored by key.
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
    defaultConnection = None
    EmptyValues = None

    MetaTable = u"pool_meta"
    FulltextTable = u"pool_fulltext"
    GroupsTable = u"pool_groups"


    def __init__(self, connection = None, structure = None, root = "",
                 useTrashcan = False, useBackups = False, 
                 codePage = StdEncoding, dbCodePage = StdEncoding,
                 connParam = None, 
                 debug = 0, log = "sql.log", **kw):

        self.codePage = codePage
        self.dbCodePage = dbCodePage
        self.useBackups = useBackups
        self.useTrashcan = useTrashcan

        self._debug = debug
        self._log = log
        
        self._conn = None
        self.name = u""        # used for logging

        self.SetRoot(root)
        if not structure:
            self.structure = self._GetDefaultPoolStructure()(pool=self)
        else:
            self.structure = structure
        if connection:
            self._conn = connection
        elif connParam:
            self._conn = self.CreateConnection(connParam)
            if not self.name:
                self.name = connParam.get("dbName",u"")
        

    def Close(self):
        if self._conn:
            self._conn.close()
        #self.structure = None

    def __del__(self):
         self.Close()


    # Database api ---------------------------------------------------------------------

    @property
    def connection(self):
        """
        Returns the database connection and attempts a reconnect or verifies the connection
        depending on configuration settings.
        """
        self._conn.VerifyConnection()
        return self._conn

    def dbapi(self):
        if not self._conn:
            raise ConnectionError, "No Connection"
        return self._conn.dbapi()


    def GetConnection(self):
        """
        Returns the database connection without verifying the connection.
        """
        return self._conn

    def GetPlaceholder(self):
        return u"%s"
    
    def GetDBDate(self, date=None):
        #
        if not date:
            return DvDateTime(localtime()).GetDBMySql()
        return DvDateTime(str(date)).GetDBMySql()


    # SQL queries ---------------------------------------------------------------------

    def FmtSQLSelect(self, flds, parameter={}, dataTable = u"", start = 0, max = 0, **kw):
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
        plist = []   # sorted list of query parameters for execute()
        ph = self.GetPlaceholder()   # placeholder to be used instead plist values
        fields = []
        for field in flds:
            if singleTable:
                table = u""
                if field[0] == u"-":
                    field = field[1:]
            else:
                table = u"meta__."
                # aggregate functions marked with - e.g. "-count(*)"
                if field[0] == u"-":
                    table = u""
                    field = field[1:]
                asName = field.find(u" as ")!=-1
                f2=field
                if asName:
                    f2 = field.split(u" as ")[0]
                elif f2 in metaStructure:   # ?? or f2 == u"pool_stag":
                    table = u"meta__."
                elif dataTable != u"":
                    if jointype.lower() != u"inner":
                        if field == mapJoinFld:
                            fields.append(u"IF(meta__.pool_datatbl='%s', %s, meta__.title)" % (dataTable, field))
                        else:
                            fields.append(u"IF(meta__.pool_datatbl='%s', %s, '')" % (dataTable, field))
                        continue
                    table = u"data__."
            if(len(fields) > 0):
                fields.append(u", ")
            fields.append(table + field)
        fields = u"".join(fields)

        aCombi = kw.get("logicalOperator")
        if not aCombi:
            aCombi = u"AND"
        else:
            aCombi = aCombi.upper()
            if not aCombi in (u"AND",u"OR",u"NOT"):
                aCombi = u"AND"
        addCombi = False
        connection = self.connection

        where = []
        for key in parameter.keys():
            value = parameter[key]
            paramname = key

            operator = u"="
            if operators and key in operators:
                operator = operators[key]

            if singleTable:
                table = u""
            else:
                table = u"meta__."
                # aggregate functions marked with - e.g. "-count(*)"
                if key[0] == u"-":
                    table = u""
                    paramname = key[1:]
                elif key in metaStructure:   # ?? or key == u"pool_stag":
                    table = u"meta__."
                elif dataTable != u"":
                    table = u"data__."
            
            # fmt string values
            if isinstance(value, basestring):
                if operator == u"LIKE":
                    if value == u"":
                        continue
                    value = u"%%%s%%" % value.replace(u"*", u"%")
                    if addCombi:
                        where.append(u" %s " % aCombi)
                    where.append(u"%s%s %s %s " % (table, paramname, operator, ph))
                    plist.append(value)
                elif operator == u"BETWEEN":
                    if value == u"":
                        continue
                    if addCombi:
                        where.append(u" %s " % aCombi)
                    where.append(u"%s%s %s %s " % (table, paramname, operator, ph))
                    plist.append(value)
                else:
                    if addCombi:
                        where.append(u" %s " % aCombi)
                    where.append(u"%s%s %s %s " % (table, paramname, operator, ph))
                    plist.append(value)
                addCombi = True

            # fmt list values
            elif isinstance(value, (tuple, list)):
                if not value:
                    continue
                if addCombi:
                    where.append(u" %s " % aCombi)
                if operator == u"BETWEEN":
                    if len(value) < 2:
                        continue
                    where.append(u"%s%s %s %s AND %s" % (table, paramname, operator, ph, ph))
                    plist.append(value[0])
                    plist.append(value[1])
                elif len(value)==1:
                    if operator == u"IN":
                        operator = u"="
                    elif operator == u"NOT IN":
                        operator = u"<>"
                    where.append(u"%s%s %s %s " % (table, paramname, operator, ph))
                    plist.append(value[0])
                else:
                    v = self.FormatListForQuery(value)
                    if isinstance(v, basestring):
                        # sqlite error
                        where.append(u"%s%s %s (%s) " % (table, paramname, operator, v))
                    else:
                        where.append(u"%s%s %s %s " % (table, paramname, operator, ph))
                        plist.append(value)
                addCombi = True

            # fmt number values
            elif isinstance(value, (int, long, float)):
                if addCombi:
                    where.append(u" %s " % aCombi)
                if operator == u"LIKE":
                    operator = u"="
                where.append(u"%s%s %s %s" % (table, paramname, operator, ph))
                plist.append(value)
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
            table = u"meta__."
            s = sort.split(u",")
            sort = []
            for sortfld in s:
                sortfld = sortfld.strip(u" ")
                if len(sortfld) > 0 and sortfld[0] == u"-":
                    table = u""
                    sortfld = sortfld[1:]
                elif sortfld in metaStructure or sortfld == u"pool_stag":
                    table = u"meta__."
                elif dataTable != u"":
                    table = u"data__."
                if len(sort):
                    sort.append(u", ")
                sort.append(table)
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

        sql = u"""
        SELECT %s
        FROM %s
        %s
        %s
        %s
        %s
        %s
        %s
        %s
        """ % (fields, table, join, joindata, customJoin, where, groupby, sort, limit)
        return sql, plist


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

        For further options see -> FmtSQLSelect
        """
        sql, values = self.FmtSQLSelect(flds, parameter, dataTable=dataTable, **kw)
        connection = self.connection
        searchPhrase = self.DecodeText(searchPhrase)
        values.insert(0, searchPhrase)
        ph = self.GetPlaceholder()
        phrase = u"""%s.text LIKE %s""" % (self.FulltextTable, ph)

        if not searchPhrase in (u"", u"'%%'", None):
            if sql.find(u"WHERE ") == -1:
                if sql.find(u"ORDER BY ") != -1:
                    sql = sql.replace(u"ORDER BY ", "WHERE %s \r\n        ORDER BY " % (phrase))
                elif sql.find(u"LIMIT ") != -1:
                    sql = sql.replace(u"LIMIT ", "WHERE %s \r\n        LIMIT " % (phrase))
                else:
                    sql += u"WHERE %s " % (phrase)
            else:
                sql = sql.replace(u"WHERE ", "WHERE %s AND " % (phrase))

        sql = sql.replace(u"FROM %s AS meta__"%(self.MetaTable), "FROM %s AS meta__\r\n        LEFT JOIN %s ON (meta__.id = %s.id)"%(self.MetaTable, self.FulltextTable, self.FulltextTable))
        return sql, values


    def Query(self, sql, values = None, cursor=None, getResult=True):
        """
        execute a query on the database. non unicode texts are converted according to codepage settings.
        """
        cc=True
        if cursor:
            c = cursor
            cc=False
        else:
            c = self.connection.cursor()
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        sql = self.DecodeText(sql)
        if values:
            # check for list and strings
            found = [isinstance(v, list) or isinstance(v, bytes) for v in values]
            if True in found:
                # shouldnt happen
                v1 = []
                for v in values:
                    if isinstance(v, list):
                        v1.append(tuple(v))
                    elif isinstance(v, bytes):
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
            self.Undo()
            raise OperationalError, e
        except self._ProgrammingError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            self.Undo()
            raise ProgrammingError, e
        if not getResult:
            if cc:
                c.close()
            return
        result = c.fetchall()
        if cc:
            c.close()

        return result


    def Execute(self, sql, values = None, cursor=None):
        """
        Execute a query on the database. Returns the dbapi cursor. Use `cursor.fetchall()` or
        `cursor.fetchone()` to retrieve results. The cursor should be closed after usage.
        """
        if not cursor:
            cursor = self.connection.cursor()
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        # adjust different accepted empty values sets
        if not values:
            values = self.EmptyValues
        try:
            cursor.execute(sql, values)
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        except self._ProgrammingError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            self.Undo()
            raise ProgrammingError, e
        return cursor

    
    def FormatListForQuery(self, value):
        return tuple(value)

    def GetPlaceholder(self):
        return u"%s"
    

    def InsertFields(self, table, data, cursor = None, idColumn = None):
        """
        Insert row with multiple fields in the table.
        Codepage and dates are converted automatically
        Set `idColumn` to the column name of the auto increment unique id column
        to get it returned.
        
        returns the converted data 
        """
        dataList = []
        flds = []
        phdata = []
        ph = self.GetPlaceholder()
        data = self.structure.serialize(table, None, data)
        for key, value in data.items():
            flds.append(key)
            phdata.append(ph)
            dataList.append(value)

        sql = u"INSERT INTO %s (%s) VALUES (%s)" % (table, u",".join(flds), u",".join(phdata))

        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)

        cc = 0
        if not cursor:
            cc = 1
            cursor = self.connection.cursor()
        try:
            cursor.execute(sql, dataList)
        except self._Warning:
            pass
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        id = 0
        if idColumn:
            id = self._GetInsertIDValue(cursor)
        if cc:
            cursor.close()
        return data, id


    def UpdateFields(self, table, id, data, cursor = None, idColumn = u"id", autoinsert=False):
        """
        Updates multiple fields in the table.
        If `autoinsert` is True the a new record is automatically inserted if it does not exist. Also
        the function returns the converted data *and* id (non zero if a new record was inserted)
        
        If `autoinsert` is False the function returns the converted data.
        """
        cc = 0
        if not cursor:
            cc = 1
            cursor = self.connection.cursor()
        ph = self.GetPlaceholder()
        if autoinsert:
            # if record does not exist, insert it
            sql = """select id from %s where %s=%s""" %(table, idColumn, ph)
            self.Execute(sql, (id,), cursor=cursor)
            r = cursor.fetchone()
            if not r:
                data, id = self.InsertFields(table, data, cursor = cursor, idColumn = idColumn)
                if cc:
                    cursor.close()
                return data, id
            
        dataList = []
        data = self.structure.serialize(table, None, data)
        sql = [u"UPDATE %s SET " % (table)]
        for key, value in data.items():
            dataList.append(value)
            if len(sql)>1:
                sql.append(u",%s=%s"%(key, ph))
            else:
                sql.append(u"%s=%s"%(key, ph))

        sql.append(u" WHERE %s=%s" % (idColumn, ph))
        dataList.append(id)
        sql = u"".join(sql)
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)

        try:
            cursor.execute(sql, dataList)
        except self._Warning:
            pass
        except self._OperationalError, e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError, e
        if cc:
            cursor.close()
        if autoinsert:
            return data, 0
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
            STACKF(0,sql+"\r\n\r\n",self._debug, self._log,name=self.name)
        cc=False
        if not cursor:
            cc=True
            cursor = self.connection.cursor()
        cursor.execute(sql, v)
        if cc:
            cursor.close()


    def Begin(self):
        """
        Start a database transaction, if supported
        """
        self.connection.Begin()


    def Commit(self, user=""):
        """
        Commit the changes made to the database, if supported
        """
        self.connection.commit()


    def Undo(self):
        """
        Rollback the changes made to the database, if supported
        """
        self.connection.rollback()


    # Text conversion -----------------------------------------------------------------------

    def EncodeText(self, text):
        """
        Used for text read from the database. 
        Converts the text to unicode based on self.dbCodePage.
        """
        if text==None:
            return text
        if isinstance(text, bytes):
            return unicode(text, self.dbCodePage, EncodeMapping)
        return text


    def DecodeText(self, text):
        """
        Used for text stored in database.
        Convert the text to unicode based on self.codePage.
        """
        if text==None:
            return text
        if isinstance(text, bytes):
            return unicode(text, self.codePage, EncodeMapping)
        return text


    def ConvertRecToDict(self, rec, flds):
        """
        Convert a database record tuple to dictionary based on flds list
        """
        return dict(zip(flds, rec))


    # groups - userid assignment storage ------------------------------------------------------------------------------------

    def GetGroups(self, id, userid=None, group=None):
        """
        Get local group assignment for userid.
        
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
        sql, values = self.FmtSQLSelect(["userid", "groupid", "id"], parameter=p, dataTable = self.GroupsTable, singleTable=1)
        r = self.Query(sql, values)
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


    def GetAllUserGroups(self, userid):
        """
        Get all local group assignment for userid.
        
        returns a group assignment list [["userid", "groupid", "id"], ...]
        """
        # check if exists
        p = {u"userid": userid}
        o = {u"userid": u"="}
        sql, values = self.FmtSQLSelect([u"userid", u"groupid", u"id"], parameter=p, operators=o, dataTable=self.GroupsTable, singleTable=1)
        r = self.Query(sql, values)
        return r


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
        cursor = self.connection.cursor()

        # base record
        sql, values = self.FmtSQLSelect([u"pool_dataref", u"pool_datatbl"], parameter={"id":id}, dataTable=self.MetaTable, singleTable=1)
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        cursor.execute(sql, values)
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
        sql, values = self.FmtSQLSelect(["id"], parameter={"id":id}, dataTable = self.MetaTable, singleTable=1)
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        c = self.connection.cursor()
        c.execute(sql, values)
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
            sql, values = self.FmtSQLSelect(flds, parameter=parameter, dataTable=self.MetaTable, max=len(ids), sort=sort, operators=operators, singleTable=1)
            recs = self.Query(sql, values)
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
            sql, values = self.FmtSQLSelect(flds, parameter=parameter, dataTable=self.MetaTable, sort=sort, groupby=u"pool_datatbl", operators=operators, singleTable=1)
            tables = []
            for r in self.Query(sql, values):
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
            sql, values = self.FmtSQLSelect(flds, parameter=parameter, dataTable=table, sort=sort, operators=operators)
            typeData = self.Query(sql, values)
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

    def _GetInsertIDValue(self, cursor):
        #("assert", "subclass")
        return 0

    def _CreateNewID(self, table = ""):
        #("assert", "subclass")
        return 0

    def _CreateFixID(self, id, dataTbl):
        #("assert", "subclass")
        return 0

    def _GetPoolEntry(self, id, **kw):
        #("assert", "subclass")
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
        aC = self.connection.cursor()
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
        aC = self.connection.cursor()
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
        aC = self.connection.cursor()
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
        aC = self.connection.cursor()
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
        aC = self.connection.cursor()
        aC.execute(u"SELECT COUNT(*) FROM %s" % (table))
        aN = aC.fetchone()[0]
        aC.close()
        return aN

    def Log(self, s):
        DUMP(s, self._log,name=self.name)


    def SetConnection(self, conn):
        self._conn = conn

    def CreateConnection(self, connParam):
        return self.defaultConnection(connParam)

    
    # internal subclassing
    
    def _DeleteFiles(self, id, cursor, version):
        pass

    def _GetDefaultPoolStructure(self):
        return PoolStructure

    def _GetDataWrapper(self):
        return DataWrapper

    def _GetMetaWrapper(self):
        return MetaWrapper

    def _GetFileWrapper(self):
        return FileWrapper
    



class Entry(object):
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
        selfref = weakref.ref(self)
        self.meta = dataPool._GetMetaWrapper()(selfref)
        self.data = dataPool._GetDataWrapper()(selfref)
        self.files = dataPool._GetFileWrapper()(selfref)
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
        self.meta.close()
        self.data.close()
        self.files.close()
        self.pool = None


    def Exists(self):
        """
        Check if the entry physically exists in the database
        """
        if self.virtual:
            return True
        if not self.IsValid():
            return False
        return self.pool.IsIDUsed(self.id)


    def IsValid(self):
        """
        Check if the id is valid
        """
        return self.id > 0


    def SerializeValue(self, fieldname, value, meta=False):
        if meta:
            tbl = self.pool.MetaTable
        else:
            tbl = self.GetDataTbl()
        return self.pool.structure.serialize(tbl, fieldname, value)

    def DeserializeValue(self, fieldname, value, meta=False):
        if meta:
            tbl = self.pool.MetaTable
        else:
            tbl = self.GetDataTbl()
        return self.pool.structure.deserialize(tbl, fieldname, value)

    # Transactions ------------------------------------------------------------------------

    def Commit(self, user=""):
        """
        Commit temporary changes (meta, data, files) to database
        """
        self.Touch(user)
        try:
            cursor = self.pool.connection.cursor()
            # meta
            if self.meta.HasTemp():
                self.pool.UpdateFields(self.pool.MetaTable, self.id, self.meta.GetTemp(), cursor)
            # data
            if self.data.HasTemp():
                self.pool.UpdateFields(self.GetDataTbl(), self.GetDataRef(), self.data.GetTemp(), cursor)
            # files
            if self.files.HasTemp():
                self.CommitFiles(self.files.GetTemp(), cursor=cursor)
            self.pool.Commit()
            cursor.close()
            # remove previous files
            self.Cleanup(self.files.GetTemp())
            self.data.SetContent(self.data.GetTemp())
            self.data.clear()
            self.meta.SetContent(self.meta.GetTemp())
            self.meta.clear()
            self.files.SetContent(self.files.GetTemp())
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

        sql, values = self.pool.FmtSQLSelect([fld], parameter={"id":self.id}, dataTable=self.pool.MetaTable, singleTable=1)
        data = self._GetFld(sql, values)
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
        sql, values = self.pool.FmtSQLSelect([fld], parameter={"id":self.GetDataRef()}, dataTable=tbl, singleTable=1)
        data = self._GetFld(sql, values)
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

    def SetMetaField(self, fld, data, cache=True):
        """
        Update single field to meta layer.
        Commits changes immediately to database without calling touch.
        """
        temp = self.pool.UpdateFields(self.pool.MetaTable, self.id, {fld:data})
        self.pool.Commit()
        if cache:
            self._UpdateCache(temp)
        return True


    def SetDataField(self, fld, data, cache=True):
        """
        Update single field to data layer
        Commits changes immediately to database without calling touch.
        """
        if fld == u"id":
            return False

        cursor = self.pool.connection.cursor()
        # check if data record already exists
        id = self.GetDataRef()
        if id <= 0:
            cursor.close()
            return False

        temp = self.pool.UpdateFields(self.GetDataTbl(), id, {fld:data}, cursor)
        cursor.close()
        self.pool.Commit()

        if cache:
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

    def DuplicateFiles(self, newEntry):
        """
        """
        #BREAK("subclass")
        pass


    def CommitFile(self, key, file, cursor=None):
        """
        """
        #BREAK("subclass")
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
            if not self.DuplicateFiles(newEntry):
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
        sql, values = self.pool.FmtSQLSelect(["id"], parameter={"id":self.id}, dataTable=self.pool.FulltextTable, singleTable=1)
        cursor = self.pool.connection.cursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n", self.pool._debug, self.pool._log, name=self.pool.name)
        cursor.execute(sql, values)
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
        sql, values = self.pool.FmtSQLSelect(["text"], parameter={"id":self.id}, dataTable=self.pool.FulltextTable, singleTable=1)
        cursor = self.pool.connection.cursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n", self.pool._debug, self.pool._log, name=self.pool.name)
        cursor.execute(sql, values)
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
        sql = u"DELETE FROM %s WHERE id = %s"%(self.pool.FulltextTable, ph)
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
        aCursor = self.pool.connection.cursor()
        aCursor.execute(sql, (self.id,))
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
            cursor = self.pool.connection.cursor()
            if self.pool._debug:
                STACKF(0,sql+"\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
            cursor.execute(sql)
            r = cursor.fetchone()
            cursor.close()
            return r[0]
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
        sql, values = pool.FmtSQLSelect(flds, param, dataTable = table, version=self.version, singleTable=1)

        c = 0
        if not cursor:
            c = 1
            cursor = pool.GetCursor()
        if pool._debug:
            STACKF(0,sql+"\r\n\r\n",pool._debug, pool._log,name=pool.name)
        cursor.execute(sql, values)
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
        sql, values = pool.FmtSQLSelect(flds2, param, dataTable = self.GetDataTbl(), version=self.version)

        c = 0
        if not cursor:
            c = 1
            cursor = pool.GetCursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n",pool._debug, pool._log,name=pool.name)
        cursor.execute(sql, values)
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
        c = self.pool.connection.cursor()
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
        c = self.pool.connection.cursor()
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
        c = self.pool.connection.cursor()
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
        c = self.pool.connection.cursor()
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
        c = self.pool.connection.cursor()
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
        aC = self.pool.connection.cursor()
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



class Connection(object):
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
        self.revalidate = 100
        self.verifyConnection = False
        self._vtime = time()
        if(config):
            self.SetConfig(config)
        if(connectNow):
            self.connect()
       

    def __del__(self):
        self.close()


    def cursor(self):
        db = self._get()
        if not db:
            raise OperationalError, "Database is closed"
        return db.cursor()
        
    
    def rollback(self):
        """ Calls rollback on the current transaction, if supported """
        db = self._get()
        db.rollback()
        return


    def commit(self):
        """ Calls commit on the current transaction, if supported """
        db = self._get()
        db.commit()
        return


    def connect(self):
        """ Close and connect to server """
        self.close()
        # "use a subclassed connection"


    def close(self):
        """ Close database connection """
        db = self._get()
        if db:
            db.close()
            self._set(None)

    
    def ping(self):
        """ ping database server """
        db = self._get()
        return db.ping()


    def dbapi(self):
        """ returns the database connection class """
        self.VerifyConnection()
        db = self._get()
        if not db:
            self.connect()
        return self._get()


    def Connect(self):
        """ Close and connect to server """
        self.connect()

    def IsConnected(self):
        """ Check if database is connected """
        try:
            db = self._get()
            return db.cursor()!=None
        except:
            return False
    

    def VerifyConnection(self):
        """ 
        reconnects if not connected. If revalidate is larger than 0 IsConnected() will only be called 
        after `revalidate` time
        """
        db = self._get()
        if not db:
            return self.connect()
        if not self.verifyConnection:
            return True
        if self.revalidate > 0:
            if self._getvtime()+self.revalidate > time():
                return True
        if not self.IsConnected():
            return self.connect()
        self._setvtime()
        return True
    
    
    def RawConnection(self):
        """ """
        return None

    
    def Begin(self):
        """ Calls commit on the current transaction, if supported """
        return


    def GetUser(self):
        """ returns the current database user """
        return self.user


    def GetPlaceholder(self):
        return u"%s"

    
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
        if isinstance(config, dict):
            for k in config.keys():
                setattr(self, k, config[k])
        else:
            self.user = config.user
            self.host = config.host
            self.password = config.password
            self.port = config.port
            self.dbName = config.dbName
            self.unicode = config.unicode
            self.verifyConnection = config.verifyConnection
            self.unicode = config.unicode
            try:
                self.timeout = config.timeout
            except:
                pass
            try:
                self.revalidate = config.revalidate
            except:
                pass
            

    def GetDBManager(self):
        """ returns the database manager obj """
        raise TypeError, "please use a subclassed connection"


    def _get(self):
        # get stored database connection
        return self.db
        
    def _set(self, dbconn):
        # locally store database connection
        self.db = dbconn

    def _getvtime(self):
        # get stored database connection
        return self._vtime
        
    def _setvtime(self):
        # locally store database connection
        self._vtime = time()


class ConnectionThreadLocal(Connection):
    """
    Caches database connections as thread local values.
    """

    def _get(self):
        # get stored database connection
        if not hasattr(self.local, "db"):
            return None
        return self.local.db
        
    def _set(self, dbconn):
        # locally store database connection
        self.local.db = dbconn
        
    def _getvtime(self):
        # get stored database connection
        if not hasattr(self.local, "_vtime"):
            self._setvtime()
        return self.local._vtime
        
    def _setvtime(self):
        # locally store database connection
        self.local._vtime = time()


class NotFound(Exception):
    """ raised if entry not found """
    pass

class ConnectionError(Exception):
    """    No connection """
    pass
