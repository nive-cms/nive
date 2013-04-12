
import time
import unittest

from nive.definitions import *
from nive.workflow import *
from nive.security import User

from nive.tests.db_app import app_db



def wftestfunction(transition, context, user, values):
    context.testvalue = "huh"

def wfcallbackfunction(transition, context, user, values):
    return True
def wfcallbackfunction0(transition, context, user, values):
    return False



s1 = WfStateConf(
    id = "start",
    name = "Entry point",
    actions = ["create", "delete"]
)
s2 = WfStateConf(
    id = "edit",
    name = "Edit",
    actions = ["edit", "delete"]
)
s3 = WfStateConf(
    id = "end",
    name = "End",
    actions = []
)


t1 = WfTransitionConf(
    id = "create",
    name = "Create",
    fromstate = "start",
    tostate = "edit",
    roles = ("Authenticated",),
    actions = ("create",),
    conditions = (wfcallbackfunction,),
)
t2 = WfTransitionConf(
    id = "edit",
    name = "Edit",
    fromstate = "end",
    tostate = "edit",
    roles = ("Authenticated",),
    actions = ("edit",),
    conditions = (wfcallbackfunction,),
)
t3 = WfTransitionConf(
    id = "commit",
    name = "Commit",
    fromstate = "edit",
    tostate = "end",
    roles = (),
    actions = ("commit",),
    execute = (wftestfunction,)
)
t4 = WfTransitionConf(
    id = "error",
    name = "Error",
    fromstate = "edit",
    tostate = "end",
    roles = (),
    actions = ("error",),
    conditions = (wfcallbackfunction0,),
    execute = (wftestfunction,)
)
t5 = WfTransitionConf(
    id = "multiple1",
    name = "M 1",
    fromstate = "start",
    tostate = "edit",
    roles = ("Authenticated",),
    actions = ("multiple",),
)
t6 = WfTransitionConf(
    id = "multiple2",
    name = "M 2",
    fromstate = "start",
    tostate = "end",
    roles = ("Authenticated",),
    actions = ("multiple",),
)

tx1 = WfTransitionConf(
    id = "error",
    name = "Error",
    fromstate = "edit",
    tostate = "end",
    roles = "*",
    actions = ("error",),
    conditions = ("nive.tests.test_workflow.wfcallbackfunction",wfcallbackfunction,wfcallbackfunction0),
    execute = (wftestfunction,)
)
tx2 = WfTransitionConf(
    id = "error",
    name = "Error",
    fromstate = "edit",
    tostate = "end",
    roles = "*",
    actions = ("error",),
)
tx3 = WfTransitionConf(
    id = "error",
    name = "Error",
    fromstate = "edit",
    tostate = "end",
    roles = (),
    actions = ("error",),
    execute = (wftestfunction,)
)


wf1 = WfProcessConf(
    id = "wf1",
    name = "Workflow 1",
    states = [s1,s2,s3],
    transitions = [t1,t2,t3,t4,t5,t6],
    apply=(IObject,)
)
wf2 = WfProcessConf(
    id = "wf2",
    name = "Workflow 2",
    states = [s1,s2,s3],
    transitions = [t1,t2,t3,t4],
    apply=None
)



class Tmeta(object):
    pool_wfa=""
    pool_wfp = "wf1"
    
class TestO(object):
    implements(IObject)
    def __init__(self):
        self.meta=Tmeta()
        self.id=123
        self.testvalue = ""

    def GetWfState(self):
        return self.meta.pool_wfa
    def SetWfState(self, stateID):
        self.meta.pool_wfa = stateID

class TApp(object):
    def __init__(self):
        self.reloadExtensions=False

class TestU1(object):
    def GetGroups(self, o):
        return ["Authenticated"]
class TestU2(object):
    def GetGroups(self, o):
        return ["group:admin"]



class WfTest(unittest.TestCase):

    def setUp(self):
        self.wf = Process(wf1, TApp())
        self.obj = TestO()
        self.user1 = TestU1()
        self.user2 = TestU2()
    
    def tearDown(self):
        pass
    

    def test_proc1(self):
        self.assert_(self.wf.Allow("create", self.obj, self.user1, transition=None))
        self.assert_(self.wf.Action("create", self.obj, self.user1, transition=None))
        self.assert_(self.obj.meta.pool_wfa=="edit")
        # based on users
        self.assertFalse(self.wf.PossibleTransitions("edit", action="", transition="", context=self.obj, user=self.user1))
        self.assert_(self.wf.PossibleTransitions("edit", action="", transition="", context=self.obj, user=self.user2))

        self.assert_(self.wf.GetObjInfo(self.obj, self.user1, extended = True).get("name")=="Workflow 1")
        self.assert_(self.wf.GetObjState(self.obj).id=="edit")
        self.assert_(self.wf.GetTransition("commit").id=="commit")
        self.assert_(self.wf.GetState("edit").name=="Edit")


    def test_proc2(self):
        self.assert_(self.wf.Allow("create", self.obj, self.user1, transition=None))
        a = self.obj.meta.pool_wfa
        self.obj.meta.pool_wfa = "aaaaa"
        self.assertFalse(self.wf.Allow("create", self.obj, self.user1, transition=None))
        self.obj.meta.pool_wfa = a
        self.assertFalse(self.wf.Allow("ohno", self.obj, self.user1, transition=None))
        self.assert_(self.wf.Action("create", self.obj, self.user1, transition=None))
        try:
            self.wf.Action("commit", self.obj, self.user1, transition=None)
            self.assert_(False, "WorkflowNotAllowed not raised")
        except WorkflowNotAllowed:
            pass
        self.wf.Action("commit", self.obj, self.user2, transition=None)
        self.assert_(self.obj.meta.pool_wfa=="end")
        try:
            self.wf.Action("commit", self.obj, self.user2, transition=None)
            self.assert_(False, "WorkflowNotAllowed not raised")
        except WorkflowNotAllowed:
            pass
        self.wf.Action("edit", self.obj, self.user1, transition=None)
        try:
            self.wf.Action("commit", self.obj, self.user2, transition="edit")
            self.assert_(False, "WorkflowNotAllowed not raised")
        except WorkflowNotAllowed:
            pass
        self.wf.Action("commit", self.obj, self.user2, transition="commit")

    
    def test_multiple(self):
        self.assert_(self.wf.Action("multiple", self.obj, self.user1, transition=None))

    
    def test_wfstates(self):
        self.assert_(self.wf.GetObjState(self.obj).id=="start")
        self.assert_(self.wf.GetObjState(None).id=="start")
        self.assertFalse(self.wf.GetState("ohno"))
        self.assertFalse(self.wf._LoadStates(None))
        self.assertRaises(ConfigurationError, self.wf._LoadStates, [s1,t1])
        

    def test_wftransition(self):
        self.assert_(self.wf.Action("create", self.obj, self.user1, transition=None))
        self.assert_(self.obj.testvalue=="")
        self.assert_(self.wf.Action("commit", self.obj, self.user2, transition=None))
        self.assert_(self.obj.testvalue=="huh")
        self.assert_(self.wf.Action("edit", self.obj, self.user2, transition=None))
        
        self.assertFalse(self.wf.GetTransition("ohno"))
        self.assertFalse(self.wf.GetTransition("commit").IsInteractive())
        self.assertFalse(self.wf.GetTransition("commit").GetInteractiveFunctions())
        try:
            self.wf.Action("error", self.obj, self.user2, transition=None)
            self.assert_(False, "WorkflowNotAllowed not raised")
        except WorkflowNotAllowed:
            pass

        self.assertFalse(self.wf._LoadTransitions(None))
        self.assertRaises(ConfigurationError, self.wf._LoadTransitions, [s1,t1])


    def test_include_app(self):
        a = app_db()
        a.Register(wf1)
        a.Register(wf2)
        self.assert_(a.GetWorkflowConf(wf1.id, self.obj)[0].id==wf1.id)
        self.assert_(a.GetWorkflowConf(wf2.id)[0].id==wf2.id)


class TransisiotnTest(unittest.TestCase):

    def setUp(self):
        self.wf = Process(wf1, TApp())
        self.obj = TestO()
        self.user1 = TestU1()
        self.user2 = TestU2()
    
    def tearDown(self):
        pass
    
    def test_calls1(self):
        trans = Transition("t", tx1, self.wf)
        trans.Allow(self.obj, self.user1)
        trans.IsInteractive()
        trans.GetInteractiveFunctions()
        trans.Execute(self.obj, self.user1, {"a":1})

    def test_calls2(self):
        trans = Transition("t", tx2, self.wf)
        trans.Allow(self.obj, self.user1)
        trans.IsInteractive()
        trans.GetInteractiveFunctions()
        trans.Execute(self.obj, None)
        
    def test_calls3(self):
        trans = Transition("t", tx3, self.wf)
        trans.Allow(self.obj, None)
        trans.IsInteractive()
        trans.GetInteractiveFunctions()
        trans.Execute(self.obj, self.user2)


class ConfTest(unittest.TestCase):

    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    

    def test_conf(self):
        self.assertFalse(len(wf1.test()))
        self.assertFalse(len(s1.test()))
        self.assertFalse(len(s2.test()))
        self.assertFalse(len(s3.test()))
        self.assertFalse(len(t1.test()))
        self.assertFalse(len(t2.test()))
        self.assertFalse(len(t3.test()))
        self.assertFalse(len(t4.test()))
    
    
    def test_obj1(self):
        testconf = WfProcessConf(
            id = "aadd",
            name = "Aadd",
            description = "",
            states = [],
            transitions = []
        )
        self.assert_(len(testconf.test())==0)

    def test_err1(self):
        testconf = WfProcessConf(
            id = "",
            context = "ohno",
            name = "Aadd",
            description = "",
            states = [WfTransitionConf()],
            transitions = [WfStateConf()]
        )
        self.assert_(len(testconf.test())==4)
        self.assert_(str(testconf))
        testconf(self)



    def test_obj2(self):
        testconf = WfTransitionConf(
            id = "ddaa",
            name = "Ddaa",
            description = "",
            fromstate = "here",
            tostate = "there",
            roles = ["master","slave"],
            actions = ["go"],
            execute = ["nive.tests.tworkflow.wftestfunction"],
            conditions = ["nive.tests.tworkflow.wftestfunction"]
        )
        self.assert_(len(testconf.test())==0)

    def test_err2(self):
        testconf = WfTransitionConf(
            id = "",
            context = "ohno",
            name = "Ddaa",
            description = "",
            fromstate = "",
            tostate = "",
            roles = ["master","slave"],
            actions = ["go"],
            execute = ["ohno"],
            conditions = ["ohno"]
        )
        self.assert_(len(testconf.test())==6)
        self.assert_(str(testconf))


    def test_obj3(self):
        testconf = WfStateConf(
            id = "qqqq",
            name = "Qqqq",
            description = "",
            actions = ["stay"]
        )
        self.assert_(len(testconf.test())==0)

    def test_err3(self):
        testconf = WfStateConf(
            id = "",
            context = "ohno",
            name = "Qqqq",
            description = "",
            actions = ["stay"]
        )
        self.assert_(len(testconf.test())==2)
        self.assert_(str(testconf))




if __name__ == '__main__':
    unittest.main()
