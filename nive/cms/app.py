# -*- coding: utf-8 -*-
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
Nive cms default configuration

This file links together all modules included in a default nive installation.

Minimal local system configuration (sqlite example) and usage
------------------------------------------------------
::
    
    from nive.definitions import AppConf, DatabaseConf

    app = AppConf("nive.cms.app",
                  id = "website",
                  title = "My website",
                  dbConfiguration = DatabaseConf(
                       fileRoot="/var/opt/website",
                       context=u"Sqlite3",
                       dbName="/var/opt/website/website.db")
    )
    design = ViewModuleConf("nive.cms.design.view")
    app.modules.append(design)

- Groups: *group:editor, group:author, group:admin*
- Additional meta fields: *Permission (pool_groups)* Object only displayed to users in 
  the selected group

A design is not included by default. The default can simply be included with the 
following line ::

    app.modules.append("nive.cms.design.view")

To include a customized copy of the design use ::

    design = ViewModuleConf("nive.cms.design.view")
    # design customizations here
    design.static = "mywebsite:static" 
    # add to website
    app.modules.append(design)

This will replace the static directory of the design with your own directory. However, now you will
have to add the required css, images and javascript used by the templates to the new folder.
(For a start just copy the contents of ``nive.cms.design:static``.)
"""

from nive.i18n import _
from nive.definitions import implements, IWebsite
from nive.definitions import AppConf, FieldConf, GroupConf
from nive.security import ALL_PERMISSIONS, Allow, Everyone, Deny
from nive.components.objects.base import ApplicationBase

#@nive_module
configuration = AppConf(
    id = "website",
    title = u"Nive cms",
    context = "nive.cms.app.WebsitePublisher",
    workflowEnabled = True,
    columns=[u"footer"]
)
configuration.modules = [
    # objects
    "nive.cms.box", "nive.cms.column", "nive.cms.menublock", "nive.cms.file", 
    "nive.cms.image", "nive.cms.media", "nive.cms.note", "nive.cms.text",
    "nive.cms.news", "nive.cms.spacer", "nive.cms.link", "nive.cms.code", 
    # page, root
    "nive.cms.root", "nive.cms.page", 
    # cms editor
    "nive.cms.cmsview.cmsroot",
    # design: not included by default
    #"nive.cms.design.view"
    # workflow
    "nive.cms.workflow.wf.wfProcess", "nive.cms.workflow.view",
    #extensions
    "nive.components.extensions.fulltextpage", 
    #"nive.components.extensions.localgroups",
    # tools
    "nive.components.tools.dbStructureUpdater", "nive.components.tools.dbSqldataDump", "nive.components.tools.cmsstatistics",
    "nive.components.tools.gcdump",
    # administration and persistence
    "nive.adminview.view",
    "nive.components.extensions.persistence.dbPersistenceConfiguration"
]

configuration.meta = [
    FieldConf(id="pool_groups", datatype="mcheckboxes", size=250, default="", 
              name=_(u"Permission"), description=_(u"Only displayed to users in the selected group"))
]

configuration.acl = [
    (Allow, Everyone, 'view'),
    (Allow, 'group:editor', 'read'),
    (Allow, 'group:editor', 'add'),
    (Allow, 'group:editor', 'edit'), 
    (Allow, 'group:editor', 'delete'), 
    (Allow, 'group:editor', 'publish'), 
    (Allow, 'group:editor', 'revoke'), 
    (Allow, 'group:author', 'read'),
    (Allow, 'group:author', 'add'),
    (Allow, 'group:author', 'edit'), 
    (Allow, 'group:author', 'delete'), 
    (Allow, 'group:reviewer', 'read'),
    (Allow, 'group:reviewer', 'publish'),
    (Allow, 'group:reviewer', 'revoke'), 
    (Allow, 'group:reader', 'read'),
    (Allow, 'group:admin', ALL_PERMISSIONS), 
    (Deny, Everyone, ALL_PERMISSIONS),
]

configuration.groups = [ 
    GroupConf(id="group:editor", name="group:editor"),
    GroupConf(id="group:author", name="group:author"),
    GroupConf(id="group:reviewer", name="group:reviewer"),
    GroupConf(id="group:reader", name="group:reader"),
    GroupConf(id="group:admin",  name="group:admin"),
]


class WebsitePublisher(ApplicationBase):
    """ the main cms application class """
    implements(IWebsite)
    
    
