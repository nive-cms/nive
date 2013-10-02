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

__doc__ = """
This file provides global *search* functionality, database lookup and sql query 
wrappers. It is usually attached to root objects.

Search parameter handling
--------------------------
Most functions support a similar parameter handling for generating sql queries.  

===========  ===========================================================================
Parameters
===========  ===========================================================================
fields       list of database fields (field ids) to include in result.
             prefix '-': special fields or aggregate functions can be inserted by adding 
                         a '-' in front of the field. -count(*) or -MAX(field1)
             prefix '+': special fields skipped in SQL query e.g. '+preview'
parameter    dictionary with fieldname:value entries used for search conditions
operators    dictionary with fieldname:operator entries used for search conditions
             default: strings=*LIKE*, all others='='
             possible values: ``=, LIKE, IN, >, <, <=, >=, !=, BETWEEN ``
sort         result sort field or list if multiple
ascending    sort ascending or decending
start        start position in result
max          maximum number of result records
===========  ===========================================================================

Parameter for operator BETWEEN has to be formatted: e.g. '2006/10/10' AND '2006/10/11'

================  =====================================================================
Keyword options   (Not supported by all functions)
================  =====================================================================
logicalOperator   link between conditions. default: *AND*. possible: ``AND, OR, NOT``
condition         custom sql condition statement appended to WHERE clause 
groupby           used as sql GROUP BY statement
join              adds a custom custom sql join statement
jointype          left, inner, right. default = inner (used by ``SearchType()``)
mapJoinFld        fieldname to map title by left/right join (used by ``SearchType()``)
addID             Add fld.id in query without showing in result list. used for custom 
                  columns e.g. -(select ...)
skipRender        render result flds as html element. 
                  default: ``pool_type, pool_wfa, pool_wfp`` 
                  to skip all: *True*, or a list of fields  ("pool_wfa","pool_type")
skipCount         enable or disable second query to get the number of all records. 
================  =====================================================================


=============  ========================================================================
Search result  (supported by Search*() functions)
=============  ========================================================================
criteria       dictionary containing parameters used in search
count          number of records contained in result
total          total number of records matching the query
items          result list. each record as dictionary. Each field is rendered for 
               display depending on *skipRender* keyword. This means list entries are
               replaced by their readable names, dates are rendered readable. 
start          record start number in result 
max            maximum number of records 
next           start number of next record set
nextend        end number of next record set
prev           start number of previous record set
prevend        end number of previous record set
sql            the sql statement used
=============  ========================================================================

"""

import time

from nive.utils.utils import ConvertToNumberList
from nive.utils.language import LanguageExtension, CountryExtension
from nive.views import FieldRenderer
from nive.security import GetUsers
from nive.definitions import IFieldConf
from nive.definitions import FieldConf
from nive.definitions import ConfigurationError

class Search:
    """    """


    # Simple search functions ----------------------------------------------------------------------------------------------
    
    def Select(self, pool_type=None, parameter=None, fields=None, operators=None, sort=None, ascending=1, start=0, max=0, **kw):
        """
        Fast and simple sql query. 
        
        If *pool_type* is not set the query will apply to the meta layer only. In this case you can
        only include pool_meta.fields in *fields*. To use a single table pass *dataTable* as keyword.
        
        If *pool_type* is set you can use meta and data *fields*. The query is restricted to a single 
        type.
        
        Supported keywords: ``groupby, logicalOperator, condition, dontAddType, dataTable``
        
        The following example selects all children of the current object ::
            
            fields = ["id", "title", "pool_type"]
            parameter["pool_unitref"] = self.id
            records = self.root().Select(parameter=parameter, fields=fields)
        
        returns records as list
        """
        parameter = parameter or {}
        operators = operators or {}
        fields = fields or ["id"]
        db = self.db
        if pool_type==None:
            dataTable=kw.get("dataTable") or u"pool_meta"
            sql, values = db.FmtSQLSelect(fields, 
                                          parameter, 
                                          dataTable=dataTable, 
                                          singleTable=1, 
                                          operators=operators, 
                                          sort=sort, 
                                          ascending=ascending, 
                                          start=start, 
                                          max=max, 
                                          groupby=kw.get("groupby"), 
                                          logicalOperator=kw.get("logicalOperator"), 
                                          condition=kw.get("condition"))
        else:
            if not parameter.has_key("pool_type") and not kw.get("dontAddType"):
                parameter["pool_type"] = pool_type
            if not operators.has_key("pool_type"):
                operators["pool_type"] = u"="
            typeInf = self.app.GetObjectConf(pool_type)
            if not typeInf:
                raise ConfigurationError, pool_type + " type not found"
            sql, values = db.FmtSQLSelect(fields, parameter, dataTable=typeInf["dbparam"], operators=operators, sort=sort, ascending=ascending, start=start, max=max, groupby=kw.get("groupby"), logicalOperator=kw.get("logicalOperator"), condition=kw.get("condition"))
        recs = db.Query(sql, values)
        return recs


    def SelectDict(self, pool_type=None, parameter=None, fields=None, operators=None, sort=None, ascending=1, start=0, max=0, **kw):
        """
        Fast and simple sql query. 
        
        If *pool_type* is not set the query will apply to the meta layer only. In this case you can
        only include pool_meta.fields in *fields*. 
        
        If *pool_type* is set you can use meta and data *fields*. The query is restricted to a single 
        type.
        
        Supported keywords: ``groupby, logicalOperator, condition``
        
        Records are returned as dictionaries
        
        The following example selects all children *not* of type *image* of the current object ::
            
            fields = ["id", "title", "pool_type"]
            parameter = {"pool_unitref": self.id}
            operators = {"pool_type": "!="}
            records = self.root().SelectDict("image", parameter=parameter, fields=fields, 
                                             operators=operators)
        
        returns records as dict list
        """
        fields = fields or ["id"]
        recs = self.Select(pool_type=pool_type,
                           parameter=parameter, 
                           fields=fields, 
                           operators=operators, 
                           sort=sort, 
                           ascending=ascending, 
                           start=start, 
                           max=max, 
                           **kw)
        if len(recs)==0:
            return recs
        # convert
        if len(fields) > len(recs[0]):
            raise TypeError, "Too many fields"
        for i in range(len(fields)):
            name = fields[i]
            if name.find(u" as ")!=-1:
                name = name.split(u" as ")[1]
                fields[i] = name
        return [dict(zip(fields, r)) for r in recs]


    # Extended search functions ----------------------------------------------------------------------------------------------

    def Search(self, parameter, fields=None, operators=None, sort=u"id", ascending=1, start=0, max=100, **kw):
        """
        Extended meta layer search function. Supports all keyword options and search result. 
        
        Example ::
        
            root.()Search({"title":"test"}, 
                          fields=["id", "pool_type", "title"], 
                          start=0, max=50, 
                          operators={"title":"="})
        
        returns search result (See above)
        """
        t = time.time()

        # check parameter
        try:    ascending = int(ascending)
        except:    ascending = 1
        try:    start = int(start)
        except:    start = 0
        try:    max = int(max)
        except:    max = 100
        debug = kw.get("debug",False)
        
        fields = fields or []
        operators = operators or {}

        # return empty result set and not all reords
        if kw.get("showAll",True) == False and parameter == {}:
            parameter["id"] = 0

        # lookup field definitions
        fields = self._GetFieldDefinitions(fields)
        fldList = []
        groupcol = 0
        for f in fields:
            if f["id"][0] == "-":
                groupcol += 1
            fldList.append(f["id"])

        # add id. required for group by  queries
        removeID = False
        if (not "id" in fldList and groupcol == 0 and kw.get("groupby") == None) or kw.get("addID")==1:
            fldList.append("id")
            fields.append(self.app.GetFld("id"))
            removeID = True

        db = self.db
        if not db:
            raise ConnectionError, "No database connection"

        sql, values = db.FmtSQLSelect(fldList, parameter=parameter, operators=operators, 
                              sort=sort, ascending=ascending, start=start, max=max, 
                              groupby=kw.get("groupby"), 
                              logicalOperator=kw.get("logicalOperator"), 
                              condition=kw.get("condition"), 
                              join=kw.get("join"))
        records = db.Query(sql, values)

        # prepare field renderer
        skipRender = kw.get("skipRender", False)
        renderer = None
        if not skipRender:
            # default values
            renderer = FieldRenderer(self, skip = ["pool_type", "pool_wfa", "pool_wfp"])
        elif isinstance(skipRender, (list,tuple)):
            renderer = FieldRenderer(self, skip = skipRender)

        # parse alias field names used in sql query
        p = 0
        for f in fldList:
            if f[0] == u"-" and f.find(u" as ") != -1:
                a = f.split(u" as ")[-1]
                a = a.replace(u" ", u"")
                a = a.replace(u")", u"")
                fldList[p] = a
            p += 1

        # convert records
        items = []
        cnt = 0
        total = 0
        for rec in records:
            cnt+=1
            # render if activated
            if renderer:
                rec2 = []
                for p in range(len(fields)):
                    rec2.append(renderer.Render(fields[p], rec[p], False, **kw))
                rec = rec2
            items.append(dict(zip(fldList, rec)))
            if max > 0 and cnt == max:
                break

        # total records
        total = len(items)
        if total == max and kw.get("skipCount") != 1:
            if not kw.get("groupby"):
                sql2, values =db.FmtSQLSelect([u"-count(*)"], parameter=parameter, operators=operators, 
                                      sort=sort, ascending=ascending, start=None, max=None, 
                                      logicalOperator=kw.get("logicalOperator"), 
                                      condition=kw.get("condition"), 
                                      join=kw.get("join"))
                total = db.Query(sql2, values)[0][0]
            else:
                sql2, values = db.FmtSQLSelect([u"-count(DISTINCT %s)" % (kw.get("groupby"))], parameter=parameter, operators=operators, 
                                       sort=sort, ascending=ascending, start=None, max=None, 
                                       logicalOperator=kw.get("logicalOperator"), 
                                       condition=kw.get("condition"), 
                                       join=kw.get("join"))
                total = db.Query(sql2, values)[0][0]

        # prepare result dictionary and paging information
        result = {}
        result["criteria"] = parameter
        result["count"] = cnt
        result["total"] = total
        result["items"] = items
        result["time"] = time.time() - t
        result["start"] = start
        result["max"] = max
        if debug:
            result["sql"] = sql
        
        next = start + max
        if next >= total:
            next = 0
        result["next"] = next
        nextend = next + max
        if nextend > total:
            nextend = total
        result["nextend"] = nextend

        prev = start - max
        if prev < 1:
            prev = 0
        result["prev"] = prev
        prevend = prev + max
        result["prevend"] = prevend

        return result


    def SearchType(self, pool_type, parameter, fields=None, operators=None, sort=u"id", ascending=1, start=0, max=100, **kw):
        """
        Extended meta and data layer search function. Supports all keyword options and search result. 
        
        Example ::
        
            root.()SearchType("image", 
                              parameter={"title":"test"}, 
                              fields=["id", "pool_type", "title"], 
                              start=0, max=50, 
                              operators={"title":"="})
        
        returns search result (See above)
        """
        t = time.time()

        # check parameter
        try:    ascending = int(ascending)
        except:    ascending = 1
        try:    start = int(start)
        except:    start = 0
        try:    max = int(max)
        except:    max = 100

        fields = fields or []
        operators = operators or {}

        # set join type
        default_join = 0
        if not kw.has_key("jointype") or kw.get("jointype")==u"inner":
            default_join = 1
            parameter["pool_type"] = pool_type

        if kw.get("showAll") == False and parameter == {}:
            parameter["id"] = 0

        # update result field list, search for special fields
        fields = self._GetFieldDefinitions(fields, pool_type)
        fldList = []
        groupcol = 0
        for f in fields:
            if f["id"][0] == u"-":
                groupcol += 1
            fldList.append(f["id"])

        # add id fld
        removeID = False
        # groupcol == 0 entfernt
        #if not "id" in fldList and kw.get("groupby") == None:
        if (not "id" in fldList and groupcol == 0 and kw.get("groupby") == None) or kw.get("addID")==1:
            fldList.append("id")
            fields.append(self.app.GetFld("id"))
            removeID = True

        #operators
        operators=kw.get("operators")
        if not operators:
            operators = {}
        if not operators.has_key("pool_type"):
            operators["pool_type"] = u"="
        if not default_join:
            operators["jointype"] = kw.get("jointype")

        items = []
        cnt = 0
        total = 0
        sql = ""

        typeInf = self.app.GetObjectConf(pool_type)
        if not typeInf:
            raise ConfigurationError, "Type not found (%s)" % (pool_type)

        db = self.db
        if not db:
            ct = 0
        else:

            sql, values = db.FmtSQLSelect(fldList, parameter=parameter, sort=sort, ascending=ascending, 
                                          dataTable=typeInf["dbparam"], start=start, max=max, operators=operators, 
                                          groupby=kw.get("groupby"), 
                                          logicalOperator=kw.get("logicalOperator"), 
                                          condition=kw.get("condition"), 
                                          join=kw.get("join"), 
                                          mapJoinFld=kw.get("mapJoinFld"))
            aL = db.Query(sql, values)
            
            # render
            converter = FieldRenderer(self)
            skipRender = kw.get("skipRender", False)
            if skipRender == True:
                skipRender = fldList
            elif not skipRender:
                skipRender = [u"pool_type", u"pool_wfa", u"pool_wfp"]

            # convert records
            p = 0
            for f in fldList:
                if f[0] == u"-" and f.find(u" as ") != -1:
                    a = f.split(u" as ")[-1]
                    a = a.replace(u" ", u"")
                    a = a.replace(u")", u"")
                    fldList[p] = a
                p += 1
            for aI in aL:
                cnt+=1
                # convert
                aI2 = []
                for p in range(len(fields)):
                    aI2.append(converter.Render(fields[p], aI[p], False, render = (fldList[p] not in skipRender), **kw))
                items.append(dict(zip(fldList, aI2)))

                if max > 0 and cnt == max:
                    break

            # total records
            if len(items) == max and kw.get("skipCount") != 1:
                if not kw.get("groupby"):
                    sql2, values = db.FmtSQLSelect([u"-count(*) as cnt"], parameter=parameter, sort=u"-cnt", ascending=ascending, 
                                                   dataTable=typeInf["dbparam"], start=None, max=None, operators=operators, 
                                                   logicalOperator=kw.get("logicalOperator"), 
                                                   condition=kw.get("condition"), 
                                                   join=kw.get("join"))
                    total = db.Query(sql2, values)[0][0]
                else:
                    sql2, values = db.FmtSQLSelect([u"-count(DISTINCT %s) as cnt" % (kw.get("groupby"))], parameter=parameter, sort="-cnt", 
                                                   ascending=ascending, dataTable=typeInf["dbparam"], start=None, max=None, 
                                                   operators=operators, 
                                                   logicalOperator=kw.get("logicalOperator"), 
                                                   condition=kw.get("condition"), 
                                                   join=kw.get("join"))
                    total = db.Query(sql2, values)[0][0]
            else:
                total = len(items) + start

        result = {}
        result["criteria"] = parameter
        result["count"] = cnt
        result["total"] = total
        result["items"] = items
        result["time"] = time.time() - t
        result["start"] = start
        result["max"] = max
        result["sql"] = sql
        
        next = start + max
        if next >= total:
            next = 0
        result["next"] = next
        nextend = next + max
        if nextend > total:
            nextend = total
        result["nextend"] = nextend

        prev = start - max
        if prev < 1:
            prev = 0
        result["prev"] = prev
        prevend = prev + max
        result["prevend"] = prevend

        return result


    def SearchData(self, pool_type, parameter, fields=None, operators=None, sort=u"id", ascending=1, start=0, max=100, **kw):
        """
        Extended data layer search function. Supports all keyword options and search result. 
        
        Example ::
        
            root.()SearchData("image", 
                              parameter={"text": "new"}, 
                              fields=["id", "text", "title"], 
                              start=0, max=50, 
                              operators={"text":"LIKE"})
        
        returns search result (See above)
        """
        t = time.time()

        # check parameter
        try:    ascending = int(ascending)
        except:    ascending = 1
        try:    start = int(start)
        except:    start = 0
        try:    max = int(max)
        except:    max = 100

        fields = fields or []
        operators = operators or {}

        if kw.get("showAll",True) == False and parameter == {}:
            parameter["id"] = 0

        # update result field list, search for special fields
        fields = self._GetFieldDefinitions(fields, pool_type)
        fldList = []
        groupcol = 0
        for f in fields:
            if f["id"][0] == u"-":
                groupcol += 1
            fldList.append(f["id"])

        # add id fld
        removeID = False
        # groupcol == 0 entfernt
        #if not "id" in fldList and kw.get("groupby") == None:
        if (not "id" in fldList and groupcol == 0 and kw.get("groupby") == None) or kw.get("addID")==1:
            fldList.append("id")
            fields.append(self.app.GetFld("id", pool_type))
            removeID = True

        #operators
        operators=kw.get("operators")
        if not operators:
            operators = {}

        items = []
        cnt = 0
        total = 0
        sql = ""

        typeInf = self.app.GetObjectConf(pool_type)
        if not typeInf:
            raise ConfigurationError, "Type not found (%s)" % (pool_type)

        db = self.db
        if not db:
            ct = 0
        else:
            sql, values = db.FmtSQLSelect(fldList, parameter=parameter, dataTable=typeInf["dbparam"], sort=sort, 
                                          ascending=ascending, start=start, max=max, operators=operators, 
                                          groupby=kw.get("groupby"), 
                                          logicalOperator=kw.get("logicalOperator"), 
                                          condition=kw.get("condition"), 
                                          singleTable=1)
            aL = db.Query(sql, values)
            
            # render
            converter = FieldRenderer(self)
            skipRender = kw.get("skipRender", False)
            if skipRender == True:
                skipRender = fldList
            else:
                skipRender = []

            # convert records
            p = 0
            for f in fldList:
                if f[0] == u"-" and f.find(u" as ") != -1:
                    a = f.split(u" as ")[-1]
                    a = a.replace(u" ", u"")
                    a = a.replace(u")", u"")
                    fldList[p] = a
                p += 1
            for aI in aL:
                cnt+=1
                # convert
                aI2 = []
                for p in range(len(fields)):
                    aI2.append(converter.Render(fields[p], aI[p], False, render = (fldList[p] not in skipRender), **kw))
                items.append(dict(zip(fldList, aI2)))

                if max > 0 and cnt == max:
                    break

            # total records
            if len(items) == max and kw.get("skipCount") != 1:
                if not kw.get("groupby"):
                    sql2, values = db.FmtSQLSelect([u"-count(*) as cnt"], parameter=parameter, dataTable=typeInf["dbparam"], sort=u"-cnt", 
                                                   ascending=ascending, start=None, max=None, operators=operators, 
                                                   logicalOperator=kw.get("logicalOperator"), 
                                                   condition=kw.get("condition"), 
                                                   singleTable=1)
                    total = db.Query(sql2, values)[0][0]
                else:
                    sql2, values = db.FmtSQLSelect([u"-count(DISTINCT %s) as cnt" % (kw.get("groupby"))], parameter=parameter, 
                                                   dataTable=typeInf["dbparam"], sort="-cnt", ascending=ascending, 
                                                   start=None, max=None, operators=operators, 
                                                   logicalOperator=kw.get("logicalOperator"), 
                                                   condition=kw.get("condition"), 
                                                   singleTable=1)
                    total = db.Query(sql2, values)[0][0]
            else:
                total = len(items) + start

        result = {}
        result["criteria"] = parameter
        result["count"] = cnt
        result["total"] = total
        result["items"] = items
        result["time"] = time.time() - t
        result["start"] = start
        result["max"] = max
        result["sql"] = sql

        next = start + max
        if next >= total:
            next = 0
        result["next"] = next
        nextend = next + max
        if nextend > total:
            nextend = total
        result["nextend"] = nextend

        prev = start - max
        if prev < 1:
            prev = 0
        result["prev"] = prev
        prevend = prev + max
        result["prevend"] = prevend

        return result


    def SearchFulltext(self, phrase, parameter=None, fields=None, operators=None, sort=u"id", ascending=1, start=0, max=300, **kw):
        """
        Fulltext search function. Searches all text fields marked for fulltext search. Uses *searchPhrase* 
        as parameter for text search. Supports all keyword options and search result. 
        
        Example ::
        
            root().SearchFulltext("new", parameter={}, 
                              fields=["id", "title"], 
                              start=0, max=50, 
                              operators={"text":"LIKE"})
        
        returns search result (See above)
        """
        t = time.time()

        fields = fields or ("id","title","pool_type","-pool_fulltext.text as fulltext")
        operators = operators or {}
        parameter = parameter or {}

        # check parameter
        if phrase==None:
            phrase = u""
        searchFor = phrase
        try:    ascending = int(ascending)
        except:    ascending = 1
        try:    start = int(start)
        except:    start = 0
        try:    max = int(max)
        except:    max = 100

        fields = self._GetFieldDefinitions(fields)

        fldList = []

        if kw.get("showAll",True) == False and parameter == {} and phrase == "":
            parameter["id"] = 0

        groupcol = 0
        for f in fields:
            if f["id"][0] == "-":
                groupcol += 1
            fldList.append(f["id"])

        # add id
        removeID = False
        if not "id" in fldList and groupcol == 0:
            fldList.append("id")
            fields.append(self.app.GetFld("id"))
            removeID = True

        if phrase.find(u"*") == -1:
            phrase = u"%%%s%%" % phrase
        else:
            phrase = phrase.replace(u"*", u"%")

        items = []
        cnt = 0
        total = 0
        db = self.db
        if not db:
            ct = 0
        else:
            sql, values = db.GetFulltextSQL(phrase, fldList, parameter, sort=sort, ascending=ascending, start=start, max=max, 
                                            operators=operators, 
                                            logicalOperator=kw.get("logicalOperator"), 
                                            condition=kw.get("condition"), 
                                            join=kw.get("join"))
            aL = db.Query(sql, values)
            
            # render
            converter = FieldRenderer(self)
            skipRender = kw.get("skipRender", False)
            if skipRender == True:
                skipRender = fldList
            elif not skipRender:
                skipRender = ["pool_type", "pool_wfa", "pool_wfp"]
            p = 0
            for f in fldList:
                if f[0] == "-" and f.find(u" as ") != -1:
                    a = f.split(u" as ")[-1]
                    a = a.replace(u" ", u"")
                    a = a.replace(u")", u"")
                    fldList[p] = a
                p += 1
            # convert records
            for aI in aL:
                cnt+=1
                aI2 = []
                for p in range(len(fields)):
                    aI2.append(converter.Render(fields[p], aI[p], False, render = (fldList[p] not in skipRender), **kw))
                items.append(dict(zip(fldList, aI2)))
                if max > 0 and cnt == max:
                    break

            # total records
            sql2, values = db.GetFulltextSQL(phrase, [u"-count(*)"], parameter, sort=sort, ascending=ascending, start=None, max=None, 
                                             operators=operators, 
                                             skipRang=1, 
                                             logicalOperator=kw.get("logicalOperator"), 
                                             condition=kw.get("condition"), 
                                             join=kw.get("join"))
            total = db.Query(sql2, values)[0][0]
            
        result = {}
        result["phrase"] = searchFor
        result["criteria"] = parameter
        result["count"] = cnt
        result["total"] = total
        result["items"] = items
        result["time"] = time.time() - t
        result["start"] = start
        result["max"] = max
        result["sql"] = sql

        next = start + max
        if next >= total:
            next = 0
        result["next"] = next
        nextend = next + max
        if nextend > total:
            nextend = total
        result["nextend"] = nextend

        prev = start - max
        if prev < 1:
            prev = 0
        result["prev"] = prev
        prevend = prev + max
        result["prevend"] = prevend

        return result


    def SearchFulltextType(self, pool_type, phrase, parameter=None, fields=None, operators=None, sort=u"id", ascending=1, start=0, max=300, **kw):
        """
        Fulltext search function. Searches all text fields marked for fulltext search of the given type. Uses *searchPhrase* 
        as parameter for text search. Supports all keyword options and search result. 
        
        Example ::
        
            root.()SearchFulltextType("text",
                              parameter={"searchPhrase": "new"}, 
                              fields=["id", "text", "title"], 
                              start=0, max=50, 
                              operators={"text":"LIKE"})
        
        returns search result (See above)
        """
        t = time.time()

        fields = fields or ("id","title","-pool_fulltext.text as fulltext")
        operators = operators or {}
        parameter = parameter or {}

        # check parameter
        if phrase==None:
            phrase = u""
        searchFor = phrase
        try:    ascending = int(ascending)
        except:    ascending = 1
        try:    start = int(start)
        except:    start = 0
        try:    max = int(max)
        except:    max = 100

        # set join type
        default_join = 0
        if not kw.has_key("jointype") or kw.get("jointype")==u"inner":
            default_join = 1
            parameter["pool_type"] = pool_type

        if kw.get("showAll",True) == False and parameter == {} and phrase == "":
            parameter["id"] = 0

        # update result field list, search for special fields
        fields = self._GetFieldDefinitions(fields, pool_type)
        fldList = []
        groupcol = 0
        for f in fields:
            if f["id"][0] == u"-":
                groupcol += 1
            fldList.append(f["id"])

        # add id
        removeID = False
        if (not "id" in fldList and groupcol == 0 and kw.get("groupby") == None) or kw.get("addID")==1:
            fldList.append(u"id")
            fields.append(self.app.GetFld("id", pool_type))
            removeID = True

        #operators
        operators=kw.get("operators")
        if not operators:
            operators = {}
        if not operators.has_key("pool_type"):
            operators["pool_type"] = u"="
        if not default_join:
            operators["jointype"] = kw.get("jointype")

        # fulltext wildcard
        if phrase.find(u"*") == -1:
            phrase = u"%%%s%%" % phrase
        else:
            phrase = phrase.replace(u"*", u"%")

        typeInf = self.app.GetObjectConf(pool_type)
        if not typeInf:
            raise ConfigurationError, "Type not found (%s)" % (pool_type)

        items = []
        cnt = 0
        total = 0
        sql = ""

        db = self.db
        if not db:
            ct = 0
        else:
            sql, values = db.GetFulltextSQL(phrase, fldList, parameter, dataTable=typeInf["dbparam"], sort=sort, ascending=ascending, 
                                            start=start, max=max, operators=operators, 
                                            groupby=kw.get("groupby"), 
                                            logicalOperator=kw.get("logicalOperator"), 
                                            condition=kw.get("condition"), 
                                            join=kw.get("join"), 
                                            mapJoinFld=kw.get("mapJoinFld"))
            aL = db.Query(sql, values)
            
            # render
            converter = FieldRenderer(self)
            skipRender = kw.get("skipRender", False)
            if skipRender == True:
                skipRender = fldList
            elif not skipRender:
                skipRender = ["pool_type", "pool_wfa", "pool_wfp"]

            # convert records
            p = 0
            for f in fldList:
                if f[0] == u"-" and f.find(u" as ") != -1:
                    a = f.split(u" as ")[-1]
                    a = a.replace(u" ", u"")
                    a = a.replace(u")", u"")
                    fldList[p] = a
                p += 1
            for aI in aL:
                cnt+=1
                aI2 = []
                for p in range(len(fields)):
                    aI2.append(converter.Render(fields[p], aI[p], False, render = (fldList[p] not in skipRender), **kw))
                items.append(dict(zip(fldList, aI2)))
                if max > 0 and cnt == max:
                    break

            # total records
            if len(items) == max and kw.get("skipCount") != 1:
                if not kw.get("groupby"):
                    sql2, values = db.GetFulltextSQL(phrase, [u"-count(*) as cnt"], parameter, dataTable=typeInf["dbparam"], 
                                                     ascending=ascending, start=None, max=None, operators=operators, skipRang=1, 
                                                     logicalOperator=kw.get("logicalOperator"), 
                                                     condition=kw.get("condition"), 
                                                     join=kw.get("join"))
                    total = db.Query(sql2, values)[0][0]
                else:
                    sql2, values = db.GetFulltextSQL(phrase, [u"-count(DISTINCT %s) as cnt" % (kw.get("groupby"))], parameter, 
                                                     dataTable=typeInf["dbparam"], ascending=ascending, start=None, max=None, 
                                                     operators=operators, skipRang=1, 
                                                     logicalOperator=kw.get("logicalOperator"), 
                                                     condition=kw.get("condition"), 
                                                     join=kw.get("join"))
                    total = db.Query(sql2, values)[0][0]
            else:
                total = len(items) + start
            
        result = {}
        result["phrase"] = searchFor
        result["criteria"] = parameter
        result["count"] = cnt
        result["total"] = total
        result["items"] = items
        result["time"] = time.time() - t
        result["start"] = start
        result["max"] = max
        result["sql"] = sql
        
        next = start + max
        if next >= total:
            next = 0
        result["next"] = next
        nextend = next + max
        if nextend > total:
            nextend = total
        result["nextend"] = nextend

        prev = start - max
        if prev < 1:
            prev = 0
        result["prev"] = prev
        prevend = prev + max
        result["prevend"] = prevend

        return result


    def SearchFilename(self, filename, parameter, fields=None, operators=None, sort=None, ascending=1, start=0, max=100, **kw):
        """
        Filename search function. Searches all physical file filenames (not url path names). Supports all 
        keyword options and search result. 
        
        Includes matchinng files as "result_files" in each record.
        
        Example ::
        
            root.()SearchFulltextType("text",
                              parameter={"searchPhrase": "new"}, 
                              fields=["id", "text", "title"], 
                              start=0, max=50, 
                              operators={"text":"LIKE"})
        
        returns search result (See above)
        """
        fields = fields or ()
        operators = operators or {}

        db = self.db
        if kw.get("showAll",True) == False and filename == "":
            files = []
        else:
            files = db.SearchFilename(filename)

        ids = []
        filesMapped = {}
        for f in files:
            if not f["id"] in ids:
                ids.append(f["id"])
            if not filesMapped.has_key(str(f["id"])):
                filesMapped[str(f["id"])] = []
            filesMapped[str(f["id"])].append(f)
        if len(ids)==0:
            ids.append(0)
        
        if not kw.has_key("operators"):
            kw["operators"] = {}
        parameter["id"] = ids
        kw["operators"].update({"id":u"IN"})
        result = self.Search(parameter=parameter, fields=fields, sort=sort, ascending=ascending, start=start, max=max, **kw)

        # merge result and files
        for rec in result["items"]:
            if not filesMapped.has_key(str(rec["id"])):
                continue
            rec["result_files"] = filesMapped[rec["id"]]
            # copy first file in list
            file = filesMapped[str(rec["id"])][0]
            rec["+size"] = file["size"]
            rec["+extension"] = file["extension"]
            rec["+filename"] = file["filename"]
            rec["+fileid"] = file["fileid"]
            rec["+key"] = file["filekey"]

        # update result
        del result["criteria"]["id"]
        result["criteria"]["filename"] = filename
        return result



    # Tree structure -----------------------------------------------------------

    def GetTree(self, flds=None, sort=u"id", base=0, parameter=u""):
        """
        Select list of all folders from db.
        
        returns the subtree
        {'items': [{u'id': 354956L, 'ref1': 354954L, 'ref2': 354952L, ..., 'ref10': None, 'items': [...]}]
        """
        if not flds:
            # lookup meta list default fields
            flds = self.app.configuration.listDefault
            if not flds:
                # bw: 0.9.12 fallback for backward compatibility
                flds = [u"id", u"pool_unitref", u"title", u"pool_filename", u"pool_type", u"pool_state", u"pool_wfa", u"pool_sort"]
        db = self.db
        return db.GetTree(flds=flds, sort=sort, base=base, parameter=parameter)


    def TreeParentIDs(self, id):
        """
        returns the parent ids for the object with id as list
        """
        db = self.db
        return db.GetParentPath(id)


    def TreeParentTitles(self, id):
        """
        returns the parent titles for the object with id as list
        """
        db = self.db
        return db.GetParentTitles(id)


    # Codelists representation for entries -----------------------------------------------------------------------------------------

    def GetEntriesAsCodeList(self, pool_type, name_field, parameter=None, operators=None, sort=None):
        """
        Search the database for entries of type *pool_type* and return matches as codelist ::
        
            [{"name": name_field, "id": object.id}, ... ]
        
        If the name_field is stored as data field, insert *data.* at the beginning of name_field 
        (e.g. ``data.header``)
        
        returns list
        """
        operators = operators or {}
        parameter = parameter or {}
        if not sort:
            sort = name_field
        if not parameter.has_key(u"pool_type"):
            parameter[u"pool_type"] = pool_type
        recs = self.SelectDict(pool_type=pool_type, parameter=parameter, 
                               fields=[u"id", u"pool_unitref", name_field+u" as name"], 
                               operators=operators, sort = sort)
        return recs


    def GetEntriesAsCodeList2(self, name_field, parameter=None, operators=None, sort=None):
        """
        Search the database and return matches as codelist ::
        
            [{"name": name_field, "id": object.id}, ... ]
        
        returns list
        """
        operators = operators or {}
        parameter = parameter or {}
        if not sort:
            sort = name_field
        recs = self.SelectDict(parameter=parameter, fields=[u"id", u"pool_unitref", name_field+u" as name"], 
                               operators=operators, sort = sort)
        return recs


    def GetGroupAsCodeList(self, pool_type, name_field, parameter=None, operators=None, sort=None):
        """
        Search the database for entries of type *pool_type* and return matches grouped by unique
        *name_field* values as codelist ::
        
            [{"name": name_field, "id": object.id}, ... ]
        
        If the name_field is stored as data field, insert *data.* at the beginning of name_field 
        (e.g. ``data.header``)
        
        returns list
        """
        operators = operators or {}
        parameter = parameter or {}
        if not sort:
            sort = name_field
        if not parameter.has_key(u"pool_type"):
            parameter[u"pool_type"] = pool_type
        recs = self.SelectDict(pool_type=pool_type, 
                               parameter=parameter, 
                               fields=[u"id", u"pool_unitref", name_field+u" as name"], 
                               operators=operators, 
                               groupby=name_field, 
                               sort=sort)
        return recs


    def GetGroupAsCodeList2(self, name_field, parameter=None, operators=None, sort=None):
        """
        Search the database and return matches grouped by unique *name_field* values as codelist ::
        
            [{"name": name_field, "id": object.id}, ... ]
        
        returns list
        """
        operators = operators or {}
        parameter = parameter or {}
        if not sort:
            sort = name_field
        recs = self.SelectDict(parameter=parameter, 
                               fields=[u"id", u"pool_unitref", name_field+u" as name"], 
                               operators=operators, 
                               groupby=name_field, 
                               sort=sort)
        return recs


    # Name / ID lookup -----------------------------------------------------------

    def FilenameToID(self, filename, unitref=None, parameter=None, firstResultOnly=True, operators=None):
        """
        Convert url path filename (meta.pool_filename) to id. This function does not lookup
        physical files and their filenames.

        returns id
        """
        operators = operators or {}
        parameter = parameter or {}
        if unitref != None:
            parameter[u"pool_unitref"] = unitref
        parameter[u"pool_filename"] = filename
        operators[u"pool_filename"] = u"="
        # lookup meta list default fields
        flds = self.app.configuration.listDefault
        if not flds:
            # bw: 0.9.12 fallback for backward compatibility
            flds = [u"id", u"pool_unitref", u"title", u"pool_filename", u"pool_type", u"pool_state", u"pool_wfa", u"pool_sort"]
        recs = self.Select(parameter=parameter, fields=flds, operators=operators)
        #print recs
        if firstResultOnly:
            if len(recs) == 0:
                return 0
            return recs[0][0]
        return l


    def IDToFilename(self, id):
        """
        Convert id to url path filename (meta.pool_filename). This function does not lookup
        physical files and their filenames.
        
        returns string
        """
        parameter={"id": id}
        recs = self.Select(parameter=parameter, fields=[u"pool_filename"])
        if len(recs) == 0:
            return u""
        return recs[0][0]


    def ConvertDatarefToID(self, pool_type, dataref):
        """
        Search for object id based on dataref and pool_type.

        returns id
        """
        parameter={u"pool_type": pool_type, u"pool_dataref": dataref}
        recs = self.Select(parameter=parameter, fields=[u"id"])
        if len(recs) == 0:
            return 0
        return recs[0][0]


    def GetMaxID(self):
        """
        Lookup id of the last created object.

        returns id
        """
        recs = self.Select(fields=[u"-max(id)"])
        if len(recs) == 0:
            return 0
        return recs[0][0]


    # References --------------------------------------------------------------------

    def GetReferences(self, unitID, types=None, sort=u"id"):
        """
        Search for references in unit or unitlist fields of all objects.
        
        returns id list
        """
        if not types:
            types = self.app.GetAllObjectConfs()
        else:
            l = []
            for t in types:
                l.append(self.app.GetObjectConf(t))
            types = l
        references = []
        ids = [unitID]

        db = self.db

        # lookup meta list default fields
        flds = self.app.configuration.listDefault
        if not flds:
            # bw: 0.9.12 fallback for backward compatibility
            flds = [u"id", u"pool_unitref", u"pool_filename", u"pool_type", u"pool_state"]
        else:
            flds = list(flds)
        # search unit flds
        for t in types:
            for f in t["data"]:
                if f["datatype"] != "unit":
                    continue
                l = self.Select(pool_type=t["id"], parameter={f["id"]:unitID}, fields=flds, sort=sort)
                for r in l:
                    if not r[0] in ids:
                        ids.append(r[0])
                        references.append(r)

        # search unitlist flds
        for t in types:
            for f in t["data"]:
                if f["datatype"] != "unitlist":
                    continue
                l = self.Select(pool_type=t["id"], parameter={f["id"]:str(unitID)}, fields=flds+[f["id"]], sort=sort, 
                                operators={f["id"]:"LIKE"})
                for r in l:
                    if not r[2] == t["id"]:
                        continue
                    unitRefs = ConvertToNumberList(r[3])
                    if not unitID in unitRefs:
                        continue
                    if not r[0] in ids:
                        ids.append(r[0])
                        references.append(r)

        return references



    # Field list items ------------------------------------------

    def LoadListItems(self, fieldconf, obj=None, pool_type=None, force=False):
        """
        Load field list items in correspondance to to field.id and field.settings.
        if force is false and fieldconf contains list items, the existing 
        field.listItems are returned. set force=true to reload.
        
        obj and pool_type only used for workflow lookup
        
        returns dict list
        """
        values = []
        if not fieldconf:
            return values

        if fieldconf.listItems and not force:
            # skip loading if list filled
            if hasattr(fieldconf.listItems, '__call__'):
                return fieldconf.listItems(fieldconf, obj or self)
            return fieldconf.listItems

        fld = fieldconf.id
        # load list items

        if fieldconf.settings:
            # settings dyn list
            dyn = fieldconf.settings.get("codelist")
            if not dyn:
                pass
            elif dyn == "users":
                return GetUsers(self.app)
            elif dyn == "groups":
                portal = self.app.portal
                if portal==None:
                    portal = self.app
                return portal.GetGroups(sort="name", visibleOnly=True)
            elif dyn == "localgroups":
                return self.app.GetGroups(sort="name", visibleOnly=True)
            elif dyn == "languages":
                return LanguageExtension().Codelist()
            elif dyn == "countries":
                return CountryExtension().Codelist()
            elif dyn == "types":
                return self.app.GetAllObjectConfs()
            elif dyn == "categories":
                return self.app.GetAllCategories()
            elif dyn[:5] == "type:":
                type = dyn[5:]
                return self.GetEntriesAsCodeList(type, "title", parameter= {}, operators = {}, sort = "title")
            elif dyn == "meta":
                return self.GetEntriesAsCodeList2("title", parameter= {}, operators = {}, sort = "title")

        if fld == "pool_type":
            values = self.app.GetAllObjectConfs()

        elif fld == "pool_category":
            values = self.app.GetAllCategories()

        elif fld == "pool_groups":
            local = fieldconf.settings.get("local")
            loader = self.app
            if not local:
                portal = self.app.portal
                if portal:
                    loader = portal
            values = loader.GetGroups(sort="name", visibleOnly=True)

        elif fld == "pool_language":
            values = self.app.GetLanguages()

        elif fld == "pool_wfa":
            # uses type object as param
            if obj:
                try:
                    aWfp = obj.meta.get("pool_wfp")
                    obj = self.app.GetWorkflow(aWfp)
                    if obj:
                        values = obj.GetActivities()
                except:
                    pass
            elif pool_type:
                aWfp = self.app.GetObjectConf(pool_type).get("workflowID")
                try:
                    obj = self.app.GetWorkflow(aWfp)
                    values = obj.GetActivities()
                except:
                    pass
            else:
                values = []

        elif fld == "pool_wfp":
            values = self.app.GetAllWorkflowConfs()

        return values





    # Internal functions--------------------------------------------------------------------

    def _GetFieldDefinitions(self, fields, pool_type = None):
        f = []
        for fld in fields:
            if IFieldConf.providedBy(fld):
                f.append(fld)
                continue
            if not isinstance(fld, basestring):
                continue
            if fld in ("__preview__",):
                continue
            # skip custom flds
            if fld[0] == "+":
                continue
            # Aggregate functions, custom flds
            if fld[0] == "-":
                f.append(FieldConf(**{"id": fld, "name": fld, "datatype": "string"}))
                continue

            fl = self.app.GetFld(fld, pool_type)
            if fl:
                f.append(fl)
        return f
