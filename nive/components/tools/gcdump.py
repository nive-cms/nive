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
configuration.id = "gcdump"
configuration.context = "nive.components.tools.gcdump.gcdump"
configuration.name = _(u"Object dump")
configuration.description = _("This function dumps a list of all objects found in memory.")
configuration.apply = (IApplication,)
configuration.data = [
]
configuration.mimetype = "text/html"


import gc
from types import InstanceType

class gcdump(Tool):
    """
    """

    def _Run(self, **values):
        
        limit = 1

        # Recursively expand slist's objects
        # into olist, using seen to track
        # already processed objects.
        def _getr(slist, olist, seen):
            for e in slist:
                if id(e) in seen:
                    continue
                seen[id(e)] = None
                olist.append(e)
                tl = gc.get_referents(e)
                if tl:
                    _getr(tl, olist, seen)
    
        gcl = gc.get_objects()
        olist = []
        seen = {}
        # Just in case:
        seen[id(gcl)] = None
        seen[id(olist)] = None
        seen[id(seen)] = None
        # _getr does the real work.
        _getr(gcl, olist, seen)

        self.stream.write(u"Number of objects found: ")
        self.stream.write(unicode(len(olist)))
        self.stream.write(u"<br/>\n")
        #self.stream.write(olist[0].__dict__)
        trefs = {}
        instances = {}
        for o in olist:#[100000:100200]:
            t = type(o)
            ref = str(t)
            if not ref in trefs:
                trefs[ref]=1
            else:
                trefs[ref]+=1

            if t==InstanceType:
                ref = str(t.__class__)
                if not ref in instances:
                    instances[ref]=1
                else:
                    instances[ref]+=1
            
            #self.stream.write(type(o))
            #self.stream.write("<br/>\n")
        del olist
        
        self.stream.write("<table class='table-bordered table table-condensed pull-right' style='width:45%'>\n")
        sorted = []
        for r,v in instances.items():
            if v < limit:
                continue
            sorted.append((r,v))
        sorted.sort(key=lambda tup: tup[1])
        while sorted:
            i = sorted.pop()
            self.stream.write("<tr><td>%s</td><th>%d</th></tr>\n"%(i[0].replace("<","").replace(">",""),i[1]))
        self.stream.write("</table>\n")

        self.stream.write("<table class='table-bordered table table-condensed' style='width:50%'>\n")
        sorted = []
        for r,v in trefs.items():
            if v < limit:
                continue
            sorted.append((r,v))
        sorted.sort(key=lambda tup: tup[1])
        while sorted:
            i = sorted.pop()
            self.stream.write("<tr><td>%s</td><th>%d</th></tr>\n"%(i[0].replace("<","").replace(">",""),i[1]))
        self.stream.write("</table>\n")            

        return 1

