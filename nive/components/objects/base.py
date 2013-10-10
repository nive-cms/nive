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

# bw 0.9.11: select imports here for compatibility with previous versions
# This file has been split up :
#    -> first part is now in nive.components.baseobjects 
#    -> cms part is now in nive_cms.baseobjects 


from nive.components.baseobjects import (
        ApplicationBase,
        RootBase,
        RootReadOnlyBase,
        ObjectBase,
        ObjectReadOnlyBase,
        ObjectContainerBase,
        ObjectContainerReadOnlyBase
)

try:
    from nive_cms.baseobjects import (
            PageBase,
            PageRootBase,
            PageElementBase,
            PageElementFileBase,
            PageElementContainerBase,
            FolderBase
    )
except ImportError:
    pass