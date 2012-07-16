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

__version__ = "0.9.5b"
__doc__ = """nive"""


# interfaces and configurations
from nive.definitions import *

# interface imports
from nive.userdb.app import IUserDatabase
from nive.cms.app import IWebsite
from nive.cms.app import IWebsiteRoot
from nive.cms.app import ICMSRoot

from nive.cms.cmsview.view import IToolboxWidgetConf, IEditorWidgetConf
from nive.adminview.view import IAdminWidgetConf

# exceptions
from nive.utils.dataPool2.base import OperationalError, ProgrammingError, Warning
