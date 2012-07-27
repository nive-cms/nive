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


from nive.tools import Tool
from nive.definitions import *
from nive.i18n import _

configuration = ToolConf()
configuration.id = "dbSqldataDump"
configuration.context = "nive.components.tools.dbSqldataDump.dbSqldataDump"
configuration.name = _(u"Database sql dump")
configuration.description = _("This function only dumps table contents and skips 'create table' statements.")
configuration.apply = (IApplication,)
configuration.data = [
    FieldConf(id="excludeSystem", datatype="mcheckboxes", default=[], listItems=[{"id":"pool_sys", "name":"pool_sys"},{"id":"pool_fulltext","name":"pool_fulltext"}], 
              name=_(u"Exclude system columns"))
]
configuration.mimetype = "text/sql"



class dbSqldataDump(Tool):
    """
    """

    def _Run(self, **values):

        result = 1
        codepage="utf-8"
    
        app = self.app
        datapool = app.db
        conf = app.dbConfiguration
        conn = datapool.GetConnection()
        conn.Connect()
        db = conn.DB()
        system = values.get("excludeSystem")
        self.filename = app.configuration.id + ".sql"

        if not db:
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.poolTag}))
            return 0
        
        if not conn.IsConnected():
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.poolTag}))
            return 0
        
        def mapfields(fields):
            a=[]
            for f in fields:
                a.append(f.id)
            return a
        
        export = [(MetaTbl,mapfields(app.GetAllMetaFlds(ignoreSystem=False)))]
        for t in app.GetAllObjectConfs():
            export.append((t.dbparam, ["id"]+mapfields(t.data)))
        for t in Structure.items():
            export.append((t[0], mapfields(t[1]["fields"])))

        for table in export:
            #tablename
            tablename=table[0]
            if system and tablename in system:
                continue 
            #fields
            fields=table[1]
            columns = (",").join(fields)
            sql="select %s from %s" % (columns, tablename)
            c = db.cursor()
            c.execute(sql)
            for rec in c.fetchall():
                data = []
                for col in rec:
                    data.append(conn.FmtParam(col))
                data = (",").join(data)
                value = u"INSERT INTO %s (%s) VALUES (%s);\n"%(tablename, columns, data)
                value = value.encode(codepage)
                self.stream.write(value)        
        
        return 1

