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


from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request

from nive.tools import Tool
from nive.helper import FakeLocalizer
from nive.definitions import *
from nive.i18n import _

from nive.utils.utils import FormatBytesForDisplay

configuration = ToolConf()
configuration.id = "cmsstatistics"
configuration.context = "nive.components.tools.cmsstatistics.cmsstatistics"
configuration.name = _(u"CMS Statistics")
configuration.description = _("This function provides a short summary of elements and data contained in the website.")
configuration.apply = (IApplication,)
configuration.data = [
]
configuration.mimetype = "text/html"



class cmsstatistics(Tool):
    """
    """

    def _Run(self, **values):

        try:
            localizer = get_localizer(get_current_request())
        except:
            localizer = FakeLocalizer()

        app = self.app
        datapool = app.db
        conn = datapool.connection
        c = conn.cursor()

        self.stream.write(u"<table>\n")

        sql = "select count(*) from pool_meta"
        c.execute(sql)
        rec = c.fetchall()
        self.stream.write(localizer.translate(_(u"<tr><th>Elements in total</th><td>${value}</td></tr>\n", mapping={u"value": rec[0][0]})))

        sql = "select count(*) from pool_files"
        c.execute(sql)
        rec = c.fetchall()
        self.stream.write(localizer.translate(_(u"<tr><th>Physical files</th><td>${value}</td></tr>\n", mapping={u"value": rec[0][0]})))

        sql = "select sum(size) from pool_files"
        c.execute(sql)
        rec = c.fetchall()
        self.stream.write(localizer.translate(_(u"<tr><th>Physical files size</th><td>${value}</td></tr>\n", mapping={u"value": FormatBytesForDisplay(rec[0][0])})))

        for t in app.GetAllObjectConfs():
            sql = "select count(*) from pool_meta where pool_type='%s'" % t.id
            c.execute(sql)
            rec = c.fetchall()
            self.stream.write(localizer.translate(_(u"<tr><th>${name}</th><td>${value}</td></tr>\n", mapping={u"name": t.name, u"value": rec[0][0]})))
        
        self.stream.write(u"</table>\n")

        c.close()
        return 1

