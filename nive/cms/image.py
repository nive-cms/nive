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
Image
-----
The image element inserts images into the web page.

It uses the thumbnailviewer javascript library for image pop ups. Images uploaded as fullsize
will be be linked as pop ups.

If the Python Image Library (PIL) is installed automated image conversion on upload is activated.

"""

from nive.i18n import _
from nive.definitions import StagPageElement, ObjectConf, FieldConf, Conf
from nive.components.objects.base import PageElementFileBase

from nive.components.extensions.images import ImageProcessor, PILloaded

class image(PageElementFileBase, ImageProcessor):
    
    def Span(self):
        # css class span for the css selection
        if self.data.cssClass=="teaserl":
            return u"span4"
        elif self.data.cssClass=="teasers":
            return u"span2"
        return u"span3"
    


# image type definition ------------------------------------------------------------------
#@nive_module
configuration = ObjectConf(
    id = "image",
    name = _(u"Image"),
    dbparam = "images",
    context = "nive.cms.image.image",
    template = "image.pt",
    selectTag = StagPageElement,
    description = _(u"The image element inserts images into the web page.")
)

css = [{"id": u"default", "name": _(u"Simple")}, 
       {"id": u"left",    "name": _(u"Float right")}, 
       {"id": u"teaser",  "name": _(u"Teaser")},
       {"id": u"teaserl", "name": _(u"Teaser large")},
       {"id": u"teasers", "name": _(u"Teaser small")},
]

configuration.data = [
    FieldConf(id="image",     datatype="file", size=0,     default=u"", name=_(u"Imagefile")),
    FieldConf(id="imagefull", datatype="file", size=0,     default=u"", name=_(u"Imagefile fullsize")),
    FieldConf(id="textblock", datatype="htext",size=10000, default=u"", name=_(u"Text"), fulltext=1, required=0),
    FieldConf(id="cssClass",  datatype="list", size=10,    default=u"", name=_(u"Styling"), listItems=css),
    FieldConf(id="link",      datatype="url",  size=1000,  default=u"", name=_(u"Link"))
]

if PILloaded:
    fields = ["title", "imagefull", "textblock", "cssClass", "link", "pool_groups"]
else:
    fields = ["title", "image", "imagefull", "textblock", "cssClass", "link", "pool_groups"]
configuration.forms = {"create": {"fields":fields}, "edit": {"fields":fields}}

configuration.views = []


# image profiles
def CheckDeafult(imageObject):
    return imageObject.data.cssClass in (u'', u'default', u'left', u'teaserl')

def CheckTeaser(imageObject):
    return imageObject.data.cssClass == u'teaser'

def CheckTeaserSmall(imageObject):
    return imageObject.data.cssClass == u'teasers'

ProfileImage = Conf(source="imagefull", dest="image", format="JPEG", quality="85", width=360, height=0, extension="jpg", condition=CheckDeafult)
ProfileTeaser = Conf(source="imagefull", dest="image", format="JPEG", quality="85", width=260, height=0, extension="jpg", condition=CheckTeaser)
ProfileTeaserSmall = Conf(source="imagefull", dest="image", format="JPEG", quality="90", width=160, height=0, extension="jpg", condition=CheckTeaserSmall)

configuration.imageProfiles = [ProfileImage, ProfileTeaser, ProfileTeaserSmall]


