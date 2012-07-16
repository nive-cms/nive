# -*- coding: utf-8 -*-
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
Root for context to run adminview 
"""

from nive.definitions import RootConf
from nive.userdb.root import root
from nive.i18n import _

class adminroot(root):
	"""
	"""



# Root definition ------------------------------------------------------------------
#@nive_module
configuration = RootConf(
	id = "usermanagement",
	context = "nive.userdb.useradmin.adminroot.adminroot",
    views = ["nive.userdb.useradmin.view"],
	default = False,
	subtypes = "*",
	name = _(u"User listing"),
	description = ""
)
