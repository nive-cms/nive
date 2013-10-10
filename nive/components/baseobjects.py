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
This file contains all base classes for subclassing your own objects. All required components
are already included as parent classes.
"""

from nive.application import Application, AppFactory, Configuration, Registration
from nive.container import Root, Container, ContainerEdit, ContainerSecurity, ContainerFactory, RootWorkflow
from nive.objects import Object, ObjectEdit, ObjectWorkflow
from nive.events import Events
from nive.search import Search
from nive.definitions import implements
from nive.definitions import IApplication, IContainer, IRoot, IReadonly, INonContainer, IObject
from nive.definitions import IPage, IPageContainer, IPageElement, IFile, IPageElementContainer, IFolder


class ApplicationBase(Application, AppFactory, Configuration, Registration, Events):
    """
    *Nive cms application* 
    
    The application manages module registration, module configuration, root dispatching
    and basic application events.
    """
    implements(IApplication)


class RootBase(Root, Container, Search, ContainerEdit, ContainerSecurity, Events, ContainerFactory, RootWorkflow):
    """
    *Root Edit*
    
    Default root class with add and delete support for subobjects. 
    """
    implements(IContainer, IRoot)
    
class RootReadOnlyBase(Root, Container, Search, Events, ContainerFactory, RootWorkflow):
    """
    *Root with readonly access and cache*
    
    Root class without add and delete support for subobjects. Objects are cached in memory.
    """
    implements(IRoot, IContainer, IReadonly)

    
    
class ObjectBase(Object, ObjectEdit, Events, ObjectWorkflow):
    """
    *Default non-container object with write access*
    
    This one does not support subobjects. 
    """
    implements(INonContainer, IObject)
    
class ObjectReadOnlyBase(Object, Events, ObjectWorkflow):
    """
    *Non-container object with read only access*
    
    This one does not support subobjects. 
    """
    implements(INonContainer, IObject, IReadonly)

class ObjectContainerBase(Object, ObjectEdit, ObjectWorkflow, Container, ContainerEdit,ContainerSecurity,  Events, ContainerFactory):
    """
    *Default container object with write access*
    
    This one supports subobjects. 
    """
    implements(IContainer, IObject)
    
class ObjectContainerReadOnlyBase(Object, ObjectWorkflow, Container, Events, ContainerFactory):
    """
    *Container object with read only access and cache*
    
    This one supports subobjects and caches them in memory. 
    """
    implements(IObject, IContainer, IReadonly)

