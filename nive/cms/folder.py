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
Folder
------
The folder is a simple container to store resources. 
"""

from nive.i18n import _
from nive.definitions import StagContainer, ObjectConf, FieldConf, IObject
from nive.components.objects.base import FolderBase


class folder(FolderBase):

    extension = u"html"
    


# folder type definition ------------------------------------------------------------------
#@nive_module
configuration = ObjectConf(
    id = "folder",
    name = _(u"Folder"),
    dbparam = "folder",
    context = "nive.cms.folder.folder",
    template = "folder.pt",
    subtypes = [IObject],
    selectTag = StagContainer,
    container = True,
    description = _(u"The folder is a simple container to store resources.")
)

configuration.data = [
    FieldConf(id="description", datatype="htext", size=10000, default=u"", name=_(u"Description"), description=u"")
]

configuration.forms = {
        "create": {"fields": ["title", "summary", "pool_groups"]},
        "edit":   {"fields": ["title", "summary", "pool_groups"]}
}

configuration.views = []

