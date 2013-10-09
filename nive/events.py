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
Object based events
-------------------
Events are object based and registered with the object itself. So they will
only be called as long as the object exists and are meant in the first place 
to be used in conjunction with object extension. 

Events work quite simple: the signal representing the event is just a string
and is registered in combination with a function. If the event is fired 
somewhere, the linked function will be called with event specific paramaters.

*signals* have not to be registered. They are just fired by calling *Signal(signal)*.

Every object and root fires the *init* event linked to **Init()** on creation.
So it is not necessary to register for *init* yourself and but use it as plugin point to 
register your own events.

For example if you would like to get your function **Edit()** called if the object is 
updated, add this function to your objects class: ::
    
    class myObject:
    
        def Init(self):
            self.ListenEvent("update", "Edit")
        
    
        def Edit(self, data):
            # e.g. process data 
            return
            
Inventing custom events is quite easy: :: 

        def SomeEvent(self):
            self.Signal("some_event")
            
            
For non Object or Root derived classes initialize the event system by adding a signal
to the __init__ function: ::

    def __init__(self):
        self.Signal("init")
    
"""

import weakref

class Events(object):
    
    def ListenEvent(self, signal, function):
        """
        Register a function for an event. 
        
        - *signal*: the event to listen for
        - *function*: callback to be called if the event is fired

        """
        if not self._eventdispatch.has_key(signal):
            self._eventdispatch[signal] = [function]
        else:
            self._eventdispatch[signal].append(function)


    def RemoveListener(self, signal, function):
        """
        Remove the function from an event.

        - *signal*: the event to listen for
        - *function*: callback to be called if the event is fired

        """
        if not self._eventdispatch.has_key(signal):
            return
        try:
            self._eventdispatch[signal].remove(function)
        except:
            pass
    

    def Signal(self, signal, raiseExcp=True, **kw):
        """
        Fire an event *signal*. *kw* are the parameters passed to the callback.
        """
        if signal==u"init":
            self.InitEvents()
            #return
        if not self._eventdispatch.has_key(signal):
            return
        if raiseExcp:
            for fnc in self._eventdispatch[signal]:
                if isinstance(fnc, basestring):
                    for cls in self.__class__.__mro__:
                        f = cls.__dict__.get(fnc)
                        if f != None:
                            f(self, **kw)
                else:
                    try:
                        fnc(context=self,**kw)
                    except TypeError:
                        fnc(**kw)
        else:
            for fnc in self._eventdispatch[signal]:
                try:
                    if isinstance(fnc, basestring):
                        for cls in self.__class__.__mro__:
                            f = cls.__dict__.get(fnc)
                            if f != None:
                                f(self, **kw)
                    else:
                        try:
                            fnc(context=self,**kw)
                        except TypeError:
                            fnc(**kw)
                except Exception, e:
                    pass


    def InitEvents(self):
        """
        Call Init() for every super class
        """
        if not hasattr(self, "_eventdispatch"):
            self._eventdispatch = {}
        for cls in self.__class__.__mro__:
            f = cls.__dict__.get("Init")
            if f != None:
                f(self)



    # bw 0.9.9. renamed functions
    def RegisterEvent(self, signal, function):
        return self.ListenEvent(signal, function)

    def RemoveEvent(self, signal, function):
        return self.RemoveListener(signal, function)


