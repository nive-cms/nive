#----------------------------------------------------------------------
# Copyright (C) 2012 Arndt Droullier. All rights reserved.
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
from nive.definitions import ToolConf, FieldConf


configuration = ToolConf()
configuration.id = "exampletool"
configuration.context = "nive.components.tools.example.tool"
configuration.name = u"Empty tool for tests"
configuration.description = ""
configuration.apply = None  #(IApplication,)
configuration.data = [
    FieldConf(**{"id": "parameter1", "datatype": "bool",     "required": 0,     "readonly": 0, "default": 0, "name": u"Show 1",    "description": u"Display 1"}),
    FieldConf(**{"id": "parameter2", "datatype": "string",     "required": 0,     "readonly": 0, "default": 0, "name": u"Show 2",    "description": u"Display 2"})
]
configuration.mimetype = "text/html"



class tool(Tool):

    def _Run(self, **values):
        result = u"<h1>OK</h1>"
        return result

