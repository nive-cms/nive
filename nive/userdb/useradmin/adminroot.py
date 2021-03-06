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
    default = False,
	subtypes = "*",
	name = _(u"User listing"),
	description = ""
)
