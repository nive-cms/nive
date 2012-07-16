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
__doc__ = """
Box
----
A box is a container to group elements on a page. It can be used as an
advanced styling element for web pages. The box itself only stores a title and a css class.
"""

from nive.i18n import _
from nive.definitions import StagPage, StagPageElement, ObjectConf, FieldConf
from nive.components.objects.base import PageElementContainerBase


class box(PageElementContainerBase):

    def IsContainer(self):
        #
        return True

    
    def GetPage(self):
        # return the current element container
        return self.GetParent()


    def GetElementContainer(self):
        # return the current element container
        return self #.GetParent()

    
    def GetContainer(self):
        # return the current element container
        return self.GetParent()




#@nive_module
configuration =  ObjectConf(
    id = "box",
    name = _(u"Box"),
    dbparam = "box",
    context = "nive.cms.box.box",
    template = "box.pt",
    selectTag = StagPageElement,
    container = True,
    description = _(u"A box is a container to group elements on a page. It can be used as an" 
                    u"advanced styling element for web pages. The box itself only stores a title and styling selector.")
)

# data definition ------------------------------------------------------------------
css =[  {'id': u'span2', 'name': _(u'1/6 width')},
        {'id': u'span4', 'name': _(u'1/3 width')},
        {'id': u'span6', 'name': _(u'1/2 width')},
        {'id': u'span8', 'name': _(u'2/3 width')},
        {'id': u'span10', 'name': _(u'5/6 width')},
        {'id': u'span12', 'name': _(u'100% width')},
        {'id': u'hero-unit', 'name': _(u'Top box')},
]
off =[  {'id': u'', 'name': _(u'none')},
        {'id': u'offset2', 'name': _(u'1/6 width')},
        {'id': u'offset4', 'name': _(u'1/3 width')},
        {'id': u'offset6', 'name': _(u'1/2 width')},
        {'id': u'offset8', 'name': _(u'2/3 width')},
        {'id': u'offset10', 'name': _(u'5/6 width')},
]        

configuration.data = [
    FieldConf(id="span", datatype="list", size=20, default=u"", listItems=css, 
              name=_(u"Block size"), description=u""),
    FieldConf(id="offset", datatype="list", size=20, default=u"", listItems=off, 
              name=_(u"Block empty offset left"), description=_(u"Please note: The blocksize and offset values added together can not be larger than 1. Adjust both fields accordingly.")),
    FieldConf(id="highlight", datatype="bool", size=2, default=False,  
              name=_(u"Highlight box contents"), description=_(u"This option will add a colored background to highlight the box and its contents.")),
    FieldConf(id="gallery", datatype="bool", size=2, default=False,  
              name=_(u"Use as image gallery"), description=_(u"Use this setting if you want to add floating image teasers to this box."))
]    


fields = ["title", "span", "offset", "highlight", "gallery", "pool_groups"]
configuration.forms = {"create": {"fields":fields}, "edit": {"fields":fields}}

configuration.views = []



    
