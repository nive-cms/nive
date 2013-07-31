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
nive Workflow implementation
------------------------------
Workflows can be used to define application specific constraints based upon context,
users and groups, states and actions. 

Process
+++++++
The workflow process includes the states and transitions and provides most the api. It is
possible to define more than one process in the system.

The process is stored as context.meta.pool_wfp.

State
+++++
Describes the current contexts state in the workflow process. Each state defines possible
actions without calling transitions and is used to define the start and end point of a 
transition. (In some workflow systems the state is called `activity`)

The process is stored as context.meta.pool_wfa.

Transition
++++++++++
Links two states and defines the triggering action and security restraints. A transition is 
looked up and processed by calling process.Action().

Action
++++++
An application defined string to describe an action.
Default actions used in the cms are: add, remove, create, duplicate, edit, delete, commit, reject


"""

import weakref

from nive.definitions import baseConf, ConfigurationError, TryResolveName
from nive.definitions import IWfProcessConf, IWfStateConf, IWfTransitionConf, IProcess, ILocalGroups
from nive.helper import ResolveName, ResolveConfiguration, GetClassRef
from nive.security import effective_principals 
from zope.interface import implements



WfAllRoles = "*"
WfAllActions = "*"
WfEntryActions = ("create", "duplicate")


class WfProcessConf(baseConf):
    """
    Workflow process configuration class. The workflow process configuration defines
    a single workflow to be linked to objects. The `WfProcessConf` has to be registered
    as module with the application. Each application can handle any number of workflows.
    
    Values ::

        *id :          Ascii used as name to load this process
        *context :     Dotted python name or class reference used as factory.
        states :       workflow states
        entryPoint :   state id of entry point. default `start`.
        transitions :  workflow transitions to connect states 
        apply   :      List of interfaces the workflow is registered for. 

        name :         Title (optional).
        description :  Description (optional).
        
    Call ``WfConf().test()`` to verify configuration values.
    
    Interface: IWfProcessConf
    """
    implements(IWfProcessConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.description = u""
        self.states = []
        self.transitions = []
        self.entryPoint = "start"
        self.apply = None
        self.context = Process

        baseConf.__init__(self, copyFrom, **values)
 

    def __call__(self, context):
        # for adapter registration
        return self, context
    
    
    def __str__(self):
        return "%(id)s used for %(apply)s" % self

    def test(self):
        report = []
        #check id
        if not self.id:
            report.append((ConfigurationError, " WfProcessConf.id is empty", self))
        # check context
        o = TryResolveName(self.context)
        if not o:
            report.append((ImportError, " for WfProcessConf.context", self))
        
        for s in self.states:
            iface, conf = ResolveConfiguration(s)
            if iface != IWfStateConf:
                report.append((ConfigurationError, " for WfProcessConf.states (not a state configuration)", self))
    
        for t in self.transitions:
            iface, conf = ResolveConfiguration(t)
            if iface != IWfTransitionConf:
                report.append((ConfigurationError, " for WfProcessConf.states (not a transition configuration)", self))
        
        return report



class WfStateConf(baseConf):
    """
    Workflow state configuration class. A workflow state defines the current elements 
    position in the workflow process. States are used as start and endpoint for transitions 
    but can also have a list of actions (`state.actions`) enabled without calling transitions.
    By default the startpoint in a workflow process is a state with id = 'start'.
    
    Workflow state configurations are handled by the 
    workflow process they are linked to, not by the cms application. To include states
    use workflowConf.states and not applicationConf.modules.

    Values ::

        *id :          Ascii used as name to load this process
        *context :     Dotted python name or class reference used as factory.
        actions :      list of allowed actions without calling transitions

        name :         Title (optional).
        description :  Description (optional).
            
    Call ``WfStateConf().test()`` to verify configuration values.
    
    Interface: IWfStateConf
    """
    implements(IWfStateConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.description = u""
        self.actions = []
        self.context = State

        baseConf.__init__(self, copyFrom, **values)
 

    def __str__(self):
        return "%(id)s: allowed actions %(actions)s" % self

    def test(self):
        report = []
        #check id
        if not self.id:
            report.append((ConfigurationError, " WfStateConf.id is empty", self))
        # check context
        o = TryResolveName(self.context)
        if not o:
            report.append((ImportError, " for WfStateConf.context", self))
        return report


class WfTransitionConf(baseConf):
    """
    Workflow transition configuration class. Use transitions to define possible
    actions connecting states including security restraints, triggering action(s), and
    callable fuctions to be executed with the transition.
    
    Workflow transition configurations are handled by the 
    workflow process they are linked to, not by the cms application. To include transistions
    use workflowConf.transistions and not applicationConf.modules.
    
    Values ::

        *id :          Ascii used as name to load this process
        *context :     Dotted python name or class reference used as factory.
        fromstate :    state id startpoint of this transition
        tostate :      state id endpoint of this transition
        roles :        allow the following roles
        actions :      actions initiating the transition
        conditions :   callables to be called with transition, obj, user on Allowed()
        execute :      callables to be executed with this transition
            
        values :       custom configuration values passed to callables
        name :         Title (optional).
        description :  Description (optional).
        
        
    Callables to be included as condition or execute use the following parameters:
    
        def function_name(transition, context, user, values):
            result = True
            return result
        
        function_name(transition=self, context=context, user=user)
        
    Call ``WfTransitionConf().test()`` to verify configuration values.
    
    Interface: IWfTransitionConf
    """
    implements(IWfTransitionConf)
    
    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = u""
        self.description = u""
        self.fromstate = ""
        self.tostate = ""
        self.roles = []
        self.actions = []
        self.execute = []
        self.conditions = []
        self.context = Transition
        self.values = None
        
        baseConf.__init__(self, copyFrom, **values)
 

    def __str__(self):
        return "%(id)s: %(fromstate)s => %(tostate)s %(roles)s" % self

    def test(self):
        report = []
        #check id
        if not self.id:
            report.append((ConfigurationError, " WfTransitionConf.id is empty", self))
        # check context
        o = TryResolveName(self.context)
        if not o:
            report.append((ImportError, " for WfTransitionConf.context", self))
        #check from state
        if not self.fromstate:
            report.append((ConfigurationError, " WfTransitionConf.fromstate is empty", self))
        #check to state
        if not self.tostate:
            report.append((ConfigurationError, " WfTransitionConf.tostate is empty", self))
        for c in self.conditions:
            if isinstance(c, basestring):
                o=TryResolveName(c)
                if not o:
                    report.append((ConfigurationError, " WfTransitionConf.conditions not found: "+c, self))
        for c in self.execute:
            if isinstance(c, basestring):
                o=TryResolveName(c)
                if not o:
                    report.append((ConfigurationError, " WfTransitionConf.execute not found: "+c, self))
        return report




class WorkflowNotAllowed(Exception):
    """
    """
    

class Process(object):
    """
    Workflow process implementation

    """
    implements(IProcess)

    def __init__(self, configuration, app):
        self.configuration = configuration
        self.app_ = app
        self.renderTools = True
        self.adminGroups = (u"group:admin",)  # always allowed
        for k in configuration:
            if k in ("states", "transitions"):
                continue
            setattr(self, k, configuration[k])
        self._LoadStates(configuration.states)
        self._LoadTransitions(configuration.transitions)


    def Allow(self, action, context, user, transition=None):
        """
        Checks if the action can be executed. Unlike Action() this function does 
        raise an exception.

        parameters ::
        
            action: the action as string to be executed
            context: the context object
            user: the current user
            transition: transition id. checks this transition only.

        returns True/False
        """
        # check state and allowed actions
        state = self.GetObjState(context)
        if not state:
            # State could not be loaded
            return False

        # check for possible transitions
        ptrans = self.PossibleTransitions(state.id, action, context = context, transition = transition, user = user)
        if len(ptrans):
            return True
        
        # check if action allowed in current state
        if not transition and (action in state.actions):
            return True
        return False


    def Action(self, action, context, user, transition=None):
        """
        Execute the action for current state, context and user. 

        parameters ::
        
            action: the action as string to be executed
            context: the context object
            user: the current user
            transition: transition id. checks this transition only.

        raises WorkflowNotAllowed
        """
        # set start as default
        if action in WfEntryActions:
            context.SetWfState(self.entryPoint)

        # get state
        state = self.GetObjState(context)

        # check for possible transitions
        ptrans = self.PossibleTransitions(state.id, action, user = user, transition = transition, context = context)

        # check application and action
        if not ptrans:
            # check if action allowed in current state
            if not transition and (action in state.actions):
                return True

            raise WorkflowNotAllowed, "Workflow: Not allowed (%s)"%(action)

        if len(ptrans) > 1:
            transition = ptrans[0]
            # !!! better selection based on roles
            #if action in t.actions:
            #    if t.Allow(context, user):
            #        transition = t
            #        break
        else:
            transition = ptrans[0]

        # execute transition
        transition.Execute(context, user)

        # set next state
        transition.Finish(action, context, user)

        return True


    def PossibleTransitions(self, state, action = "", transition = "", context = None, user = None):
        """
        Returns a list of possible transitions

        - if user is set, only transitions for the user are returned
        - if action is set, only transitions for the action are returned
        - if transition is set, only this transition is returned if multiple found for action
        
        parameters ::

            state: state id
            action: action name or empty string
            transition: transition id or empty string
            context: obj to check the transitions
            user: check for user name
        
        returns list
        """
        trans = []
        for t in self.transitions:
            if t.fromstate == state:
                if user:
                    if not t.Allow(context, user):
                        continue
                if action != "":
                    if not action in t.actions:
                        continue
                if not transition:
                    trans.append(t)
                elif t.id == transition:
                    trans.append(t)
        return trans



    # Object information ---------------------------------------------------------------

    def GetObjInfo(self, context, user, extended = True):
        """
        Returns workflow information for the current context. If extended = True state and
        transitions are included too. Otherwise they will be None.
        
        Included values: id, name, process, context, user, state, transitions
    
        parameters ::
        
             context: the context object
             user: the current user
             extended: lookup and include state and transitions
        
        returns dict
        """
        state = transition = None
        if extended:
            wfa = context.GetWfState()
            state = self.GetState(wfa)
            transitions = self.PossibleTransitions(wfa, user=user, context=context)
        return {"id": self.id,
                "name": self.name,
                "state": state,
                "transitions": transitions,
                "process": self,
                "context": weakref.ref(context)(),
                "user": user}


    def GetObjState(self, context):
        """
        Returns contexts state as object.
        """
        if not context:
            return self.GetState(self.entryPoint)
        state = context.GetWfState()
        if not state:
            return self.GetState(self.entryPoint)
        return self.GetState(state)


    def GetTransition(self, transitionID):
        """
        Look up the transition with given id.
        
        returns transition object or None.
        """
        for t in self.transitions:
            if t.id==transitionID:
                return t
        return None

    
    def GetState(self, stateID):
        """
        Look up the state with given id.
        
        returns state object or None.
        """
        for t in self.states:
            if t.id==stateID:
                return t
        return None


    def _LoadStates(self, stateConfs):
        # resolve state configurations and load state objects
        if not stateConfs:
            return []
        self.states = []
        for s in stateConfs:
            iface, conf = ResolveConfiguration(s)
            if iface != IWfStateConf:
                raise ConfigurationError, "Not a state configuration"
            self.states.append(self._GetObj(conf))


    def _LoadTransitions(self, transistionConfs):
        # resolve transitions configurations and load objects
        if not transistionConfs:
            return []
        self.transitions = []
        for s in transistionConfs:
            iface, conf = ResolveConfiguration(s)
            if iface != IWfTransitionConf:
                raise ConfigurationError, "Not a transition configuration"
            self.transitions.append(self._GetObj(conf))


    def _GetObj(self, conf):
        # creates state and transition objects
        name = conf["id"]
        tag = conf["context"]
        wfObj = GetClassRef(tag, self.app_.reloadExtensions, True, None)
        wfObj = wfObj(name, conf, self)
        return wfObj





class Transition(object):
    
    def __init__(self, name, configuration, process):
        self.id = name
        self.configuration = configuration
        self.process = process
        for k in configuration.keys():
            setattr(self, k, configuration[k])
        
        
    def Allow(self, context, user):
        """
        Checks if the transition can be executed in the current context.

        parameters ::
        
            context: the context object
            user: the current user

        returns True/False        
        """
        # condition
        if self.conditions:
            for c in self.conditions:
                if isinstance(c, basestring):
                    c = ResolveName(c)
                if not c(transition=self, context=context, user=user, values=self.values):
                    return False
        # roles
        if self.roles == WfAllRoles:
            return True
        if user:
            # call registered authentication policy
            groups = effective_principals()
            if groups==None:
                # no pyramid authentication policy activated
                # use custom user lookup
                groups = user.GetGroups(context)
                if context and ILocalGroups.providedBy(context):
                    local = context.GetLocalGroups(unicode(user))
                    groups = list(groups)+list(local)
        else:
            groups = (u"system.Everyone",)
        for r in groups:
            if r in self.process.adminGroups:
                return True
            if r in self.roles:
                return True
        return False


    def Finish(self, action, context, user):
        """
        Finish transitio and update contexts state.
        
        returns the new state id
        """
        nextState = self.tostate
        context.SetWfState(nextState)
        return nextState
    

    def IsInteractive(self):
        """
        Returns if this transition has callables marked as interactive.
        """
        if not self.execute:
            return False
        for c in self.execute:
            if hasattr(c, "interactive"):
                return True
        return False


    def Execute(self, context, user, values=None):
        """
        Execute all functions for this transition.
        
        parameters ::
        
            context: the context object
            user: the current user
            values: custom values passed to the callable. if none 
                    transition.configuration.values is used.
            
        """
        if not self.execute:
            return True

        # execute function
        for c in self.execute:
            func = ResolveName(c)
            func(context=context, transition=self, user=user, values=values or self.configuration.values)
        return True


    def GetInteractiveFunctions(self):
        """
        Returns a list of interactive callables.
        
        returns callables
        """
        fncs = []
        for f in self.execute:
            f = ResolveName(f)
            if hasattr(f, "interactive"):
                fncs.append(f)
        return fncs


class State(object):
    
    def __init__(self, name, configuration, process):
        self.id = name
        self.configuration = configuration
        self.process = process
        for k in configuration:
            setattr(self, k, configuration[k])
            
            

