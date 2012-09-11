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

__doc__ = ""

import types


from nive.tools import Tool, ToolView
from nive.definitions import ToolConf, ViewConf, FieldConf, IApplication, Structure, MetaTbl
from nive.i18n import _
from nive.views import BaseView
from nive.helper import FakeLocalizer
from nive.utils.dataPool2.base import OperationalError

from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request

   
   
class dbView(BaseView):
    """
    """
    
    def view(self):
        """
        Run a tool by rendering the default form and execute on submit.
        This function does not return a valid Response object. This view is meant to
        be called from another view or template:
        ``view.RenderView(tool)``
        """
        tool = self.context
        values = {}
        result = tool.Run(**values)
        data = tool.stream
        if not isinstance(data, basestring):
            try:
                data = data.getvalue()
            except:
                data = str(data)
        return self.SendResponse(data, mime=self.context.mimetype, raiseException=False) 
    
            
configuration = ToolConf()
configuration.id = "dbStructureUpdater"
configuration.context = "nive.components.tools.dbStructureUpdater.dbStructureUpdater"
configuration.name = _(u"Database Structure")
configuration.description = _(u"Generate or update the database structure based on configuration settings.")
configuration.apply = (IApplication,)
configuration.data = [
    FieldConf(id="modify",     datatype="bool", default=0, name=_(u"Modify existing columns"),  description=_(u"Change existing database columns to new configuration. Depending on the changes, data may be lost!")),
    FieldConf(id="showSystem", datatype="bool", default=0, name=_(u"Show system columns"),      description=u"")
]
configuration.mimetype = "text/html"
configuration.views = [
    ViewConf(name="", view=dbView, attr="view", permission="system")
]

class dbStructureUpdater(Tool):

    def _Run(self, **values):

        result = 1
        importWf = 1
        importSecurity = 0
        showSystem = values.get("showSystem")
        modify = values.get("modify")
        request = values.get("request", {})
        
        try:
            localizer = get_localizer(get_current_request())
        except:
            localizer = FakeLocalizer()
        #localizer.translate(term) 

        text = _(u""" <div class="well">
This tool compares the physically existing database structure (tables, columns) with the current configuration settings.
The database structure is shown on the left, configuration settings on the right. <br/><br/>
Existing database columns will only be altered if manually selected in the 'Modify' column. Modifying a table may destroy the data
stored (e.g if converted from string to integer), so don't forget to create backups of the database before modifying anything.<br/>
By default this tool will only create new tables and columns and never delete any column.
 </div>       """)
        self.stream.write(localizer.translate(_(text)))

        self.stream.write(u"""<form action="" method="post">
                     <input type="hidden" name="tag" value="dbStructureUpdater">
                     <input type="hidden" name="modify" value="1">""")
        app = self.app
        try:
            conf = app.dbConfiguration
            connection = app.NewDBConnection()
            if not connection:
                self.stream.write(localizer.translate(_(u"""<div class="alert alert-error">No database connection configured</div>""")))
                return 0
        except OperationalError, e:
            self.stream.write(localizer.translate(_(u"""<div class="alert alert-error">No database connection configured</div>""")))
            return 0
        db = connection.GetDBManager()
        self.stream.write(localizer.translate(_(u"<h4>Database '${name}' ${host} </h4><br/>", mapping={"host":conf.host, "name":conf.dbName})))

        if not db:
            self.stream.write(localizer.translate(_(u"<div class='alert alert-error'>Database connection error (${name})</div>", mapping={"name": app.dbConfiguration.context})))
            return 0
        
        if not connection.IsConnected():
            connection.connect()
            if not connection.IsConnected():
                self.stream.write(localizer.translate(_(u"<div class='alert alert-error'>Database connection error (${name})</div>", mapping={"name": app.dbConfiguration.context})))
                return 0

        # check database exists
        if not db.IsDatabase(conf.get("dbName")):
            db.CreateDatabase(conf.get("dbName"))
            self.stream.write(u"")
            self.stream.write(u"")
            self.stream.write(localizer.translate(_(u"<div class='alert alert-success'>Database created: '${name}'</div>", mapping={"name": conf.dbName})))
            db.dbConn.commit()
        db.UseDatabase(conf.get("dbName"))
        
        
        # check types for data tables -------------------------------------------------------------
        aTypes = app.GetAllObjectConfs()
        
        for aT in aTypes:
            fmt = aT["data"]
            if(fmt == []):
                continue

            m = None
            if modify:
                m = request.get(aT["dbparam"])
                if type(m) == type(""):
                    m = [m]
            if not db.UpdateStructure(aT["dbparam"], fmt, m):
                self.stream.write(u"")
                self.stream.write(localizer.translate(_(u"<div class='alert alert-error'>Table update failed: ${dbparam} (type: ${name})</div>", mapping=aT)))
                result = 0
                continue
            db.dbConn.commit()
                
            self.printStructure(db.GetColumns(aT["dbparam"], fmt), aT["dbparam"], fmt, db, localizer)

        # check meta table exists and update ---------------------------------------------------------------
        meta = app.GetAllMetaFlds(ignoreSystem=False)
        tableName = MetaTbl

        if not db.IsTable(tableName):
            if not db.CreateTable(tableName, inColumns=meta):
                self.stream.write(localizer.translate(_(u"<div class='alert alert-error'>Table creation failed (pool_meta)</div>")))
                return 0
            db.dbConn.commit()

        # create and check modified fields
        m = None
        if modify:
            m = request.get(tableName)
            if type(m) == type(""):
                m = [m]
        if not db.UpdateStructure(tableName, meta, m):
            self.stream.write(localizer.translate(_(u"<div class='alert alert-error'>Table update failed (pool_meta)</div>")))
            result = 0
        db.dbConn.commit()
        
        self.printStructure(db.GetColumns(tableName, meta), tableName, meta, db, localizer)


        # check structure tables exist and update ------------------------------------------------------------
        for table in Structure.items():
            tableName = table[0]
            fields = table[1]["fields"]
            identity = table[1]["identity"]
            if not db.IsTable(tableName):
                if not db.CreateTable(tableName, inColumns=fields, inCreateIdentity = bool(identity), primaryKeyName = identity):
                    self.stream.write(localizer.translate(_(u"<div class='alert alert-error'>Table creation failed (${name})</div>",mapping={"name":tableName})))
                    return 0
                db.dbConn.commit()
        
            # create and check modified fields
            m = None
            if modify:
                m = request.get(tableName)
                if type(m) == type(""):
                    m = [m]
            if not db.UpdateStructure(tableName, fields, m):
                self.stream.write(localizer.translate(_(u"<div class='alert alert-error'>Table creation failed (${name})</div>",mapping={"name":tableName})))
                result = 0
            db.dbConn.commit()

            if showSystem:
                self.printStructure(db.GetColumns(tableName, fields), tableName, fields, db, localizer)



        if db.modifyColumns:
            self.stream.write(u"""<div class="alert alert-error"><input class="btn" type="submit" name="submit" value=" %s "/><br/>%s</div>""" % (
                localizer.translate(_(u"Modify selected columns")), 
                localizer.translate(_(u"Changes on existing columns have to be applied manually. This will write selected 'Configuration settings' to the database.<br/> <b>Warning: This may destroy something!</b>"))))
        self.stream.write(localizer.translate(u"</form>"))

        return result

    
    def printStructure(self, structure, table, fmt, db, localizer):
        header = u"""
<h4>%(Table)s: %(tablename)s</h4>
<table class="table"><tbody>
<tr><td colspan="5">%(Db Columns)s</td>                                        <td colspan="2">%(Configuration settings)s</td></tr>
<tr><td>%(ID)s</td><td>%(Type)s</td><td>%(Default)s</td><td>%(Settings)s</td>  <td>%(Modify?)s</td><td></td></tr>
"""  % {"tablename":table, 
        "Table": localizer.translate(_(u"Table")), 
        "Db Columns": localizer.translate(_(u"Database settings")), 
        "Configuration settings": localizer.translate(_(u"Configuration settings")),
        "ID":localizer.translate(_(u"ID")),
        "Type":localizer.translate(_(u"Type")),
        "Default":localizer.translate(_(u"Default")),
        "Settings":localizer.translate(_(u"Settings")),
        "Modify?":localizer.translate(_(u"Modify?"))
       }

        row = u"""
<tr><td>%(id)s</td><td>%(type)s</td><td>%(default)s</td><td>Not null: %(null)s, Identity: %(identity)s</td>        <td>%(Modify)s</td><td>%(Conf)s</td></tr>
"""

        cb = u"""
<input type="checkbox" name="%s" value="%s">""" 

        footer = u"""
</tbody></table> <br/>"""


        self.stream.write(header)
        for col in structure:
            id = col
            col = structure[col].get("db")
            if not col:
                col = {"id":id, "type": u"", "default": u"", "null": u"", "identity": u""}
            conf = u""
            for d in fmt:
                if col and d["id"].upper() == col["id"].upper():
                    conf = db.ConvertConfToColumnOptions(d)
                    break
            col["Modify"] = cb % (table, id)
            col["Conf"] = conf
            self.stream.write(row % col)

        self.stream.write(footer)

        return 
    
    
