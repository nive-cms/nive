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

__doc__ = ""

import types


from nive.tools import Tool
from nive.definitions import ToolConf, IApplication
from nive.i18n import _

configuration = ToolConf(
    id = "gcdump",
    context = "nive.components.tools.gcdump.gcdump",
    name = _(u"Object dump"),
    description = _("This function dumps a list of all objects found in memory."),
    apply = (IApplication,),
    data = [],
    mimetype = "text/html"
)


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
        for o in olist:#[100000:100200]:
            t = type(o)
            ref = str(t)
            if ref.find("weakref")!=-1:
                try:
                    t2 = type(o())
                    ref = "%s &gt; %s" %(ref, str(t2))
                except:
                    pass
            elif t==InstanceType:
                try:
                    ref = "%s &gt; %s" %(ref, str(o.__class__))
                except:
                    pass

            if not ref in trefs:
                trefs[ref]=1
            else:
                trefs[ref]+=1
            del o
        del olist
        del gcl
        del seen
        
        self.stream.write("<table class='table-bordered table table-condensed' style='width:70%'>\n")
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

