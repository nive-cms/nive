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
Root for public user functions
-------------------------------------------
Provides functionality to safely add users with several activation and 
mailing options.
"""

import types, base64, random, string
from time import time
import uuid
import json

from nive.definitions import RootConf, Conf, StagUser, IUser
from nive.security import User
from nive.components.objects.base import RootBase
from nive.i18n import _


class Unauthorized(Exception):
    """
    failed login
    """

class UserFound(Exception):
    """
    Can be used in *getuser* listeners to break user lookup and
    pass a session user to LookupUser. The second argument is the session
    user 
    """
    def __init__(self, user):
        self.user = user

class root(RootBase):
    """
    """
    
    # field used as unique user identity in sessions and acache
    identityField = u"name"
    
    # User account handling ------------------------------------------------------------------------------------------------------

    def AddUser(self, data, activate=1, generatePW=0, mail=None, notify=False, notifyMail=None, groups="", currentUser=None, **kw):
        """
        Create a new user with groups for login with name/password ::

            data: user data as dictionary. groups and pool_state are removed. 
            activate: directly activate the user for login (pool_state=1)
            generatePW: generate a random password to be send by mail
            mail: mail object template for confirmation mail
            notify: notify user admin on new registrations by mail
            notifyMail: mail object template for notify mail
            groups: initially assign groups to the user
            currentUser: the currently logged in user for pool_createdby and workflow
    
        returns tuple: the user object if succeeds and report list
        """
        report = []
        name = data.get("name")
        
        if not name or name == "":
            report.append(_(u"Please enter your username"))
            return None, report

        # check user with name exists
        user = self.GetUserByName(name, activeOnly=0)
        if user:
            report.append(_(u"Username '${name}' already in use. Please choose a different name.", mapping={u"name":name}))
            return None, report
        email = data.get("email")
        if email and self.app.configuration.get("loginByEmail"):
            user = self.GetUserByMail(email, activeOnly=0)
            if user:
                report.append(_(u"Email '${name}' already in use. ", mapping={'name':email}))
                return None, report
        
        if generatePW:
            pw = self.GeneratePassword()
            data["password"] = pw

        if groups:
            data["groups"] = groups

        data["pool_type"] = u"user"
        data["pool_state"] = int(activate)
        data["pool_stag"] = StagUser

        if not currentUser:
            currentUser = User(name)
        obj = self.Create("user", data=data, user=currentUser)
        if not obj:
            report.append(_(u"Sorry. Account could not be created."))
            return None, report
        #obj.Commit(currentUser)
        
        app = self.app
        if mail:
            title = mail.title
            body = mail(user=obj, **kw)
            tool = app.GetTool("sendMail")
            try:
                result, value = tool(body=body, title=title, recvids=[str(obj)], force=1)
                if not result:
                    report.append(_(u"The email could not be sent."))
                    return None, report
            except Exception, e:
                report.append(_(u"The email could not be sent."))
                report.append(str(e))
                #report.append(_("Send Mail Error: ")+str(e))
                return None, report

        sysadmin = app.configuration.get("systemAdmin")
        if notify and sysadmin:
            if notifyMail:
                title = notifyMail.title
                body = notifyMail(user=obj)
            else:
                title = app.configuration.title + u" - New user"
                body = u"""
                User: %s<br/>
                Mail: %s<br/>
                Name: %s %s<br/>
                Groups: %s<br/>
                Active: %s<br/>
                <br/>%s<br/>
                """ % (data.get("name",u""), data.get("email",u""), data.get("surname",u""), data.get("lastname",u""), 
                       data.get("groups",u""), data.get("pool_state",u""), data.get("comment",u""))
            tool = app.GetTool("sendMail")
            try:
                result, value = tool(body=body, title=title, recvmails=[sysadmin], force=1)
            except Exception, e:
                pass

        report.append(_(u"Account created."))
        return obj, report


    def MailUserPass(self, email=None, mailtmpl=None, createNewPasswd=True, currentUser=None):
        """
        Mails a new password or the current password in plain text.
        
        returns status and report list
        """
        report=[]

        if not email:
            report.append(_(u"Please enter your email address or username."))
            return False, report

        obj = self.GetUserByMail(email)
        if not obj:
            obj = self.GetUserByName(email)
            if not obj:
                report.append(_(u"No matching account found. Please try again."))
                return False, report

        email = obj.data.get("email")
        title = obj.meta.get("title")
        name = obj.data.get("name")
        if email == "":
            report.append(_("No email address found."))
            return False, report
        recv = [(email, title)]

        if createNewPasswd:
            pwd = self.GenerateID(5)
            obj.data["password"] = pwd
            obj.Commit(user=currentUser)
        else:
            pwd = obj.data.get("password")
        if mailtmpl:
            title = mailtmpl.title
            body = mailtmpl(user=obj, password=pwd)
        else:
            title = _("Password")
            body = pwd
        tool = self.app.GetTool("sendMail")
        try:
            result, value = tool(body=body, title=title, recvmails=recv, force=1)
            if not result:
                report.append(_(u"The email could not be sent."))
                return False, report
        except Exception, e:
            report.append(_(u"The email could not be sent."))
            #report.append("Send Mail Error: "+str(e))
            return False, report
        report.append(_(u"The new password has been sent to your email address. Please sign in and change it."))
        return True, report


    # Login/logout and user sessions ------------------------------------------------------------------------------------------------------

    def Login(self, name, password, raiseUnauthorized = 1):
        """
        returns user/none and report list
        """
        report = []

        # session login
        user = self.GetUserByName(name)
        if not user:
            if raiseUnauthorized:
                raise Unauthorized, "Login failed"
            report.append(_(u"Sign in failed. Please check your username and password."))
            return None, report
            
        if not user.Authenticate(password):
            if raiseUnauthorized:
                raise Unauthorized, "Login failed"
            report.append(_(u"Sign in failed. Please check your username and password."))
            return None, report

        # call user
        user.Login()
        report.append(_(u"You are now signed in."))
        return user, report


    def Logout(self, ident):
        """
        Logout and delete session data
        """
        user = self.GetUser(ident)
        if not user:
            return False
        if not IUser.providedBy(user):
            user = self.LookupUser(id=user.id)
        if user:
            user.Logout()
        return True


    # Password, activationID ------------------------------------------------------------------------------------------------------

    def GenerateID(self, length=20, repl="-"):
        # generates a id
        return str(uuid.uuid4()).replace(repl,"")[:length]
        

    def GeneratePassword(self, mincount=5, maxcount=5):
        # generates a password
        vowels = u"aeiou0123456789#*"
        consonants = u"bcdfghjklmnpqrstvwxyz"
        password = u""

        for x in range(1,random.randint(mincount+1,maxcount+1)):
            if random.choice([1,0]):
                consonant = consonants[random.randint(1,len(consonants)-1)]
                if random.choice([1,0]):
                    consonant = consonant.upper()
                password=password + consonant
            else:
                vowel = vowels[random.randint(1,len(vowels)-1)]
                password=password + vowel

        return password


    # User ------------------------------------------------------------------------------------------------------

    def GetUser(self, ident, activeOnly=1):
        """
        Lookup user by *user identity* as used in session cookies for example
        
        events: 
        - getuser(ident, activeOnly)
        - loaduser(user)
        """
        try:
            self.Signal("getuser", ident=ident, activeOnly=activeOnly)
        except UserFound, user:
            return user.user
        user = self.LookupUser(ident=ident, activeOnly=activeOnly)
        if user:
            self.Signal("loaduser", user=user)
        return user
    

    def GetUserByName(self, name, activeOnly=1):
        """ """
        return self.LookupUser(name=name, activeOnly=activeOnly)


    def GetUserByMail(self, email, activeOnly=1):
        """ """
        return self.LookupUser(email=email, activeOnly=activeOnly)


    def GetUserByID(self, id, activeOnly=1):
        """ """
        return self.LookupUser(id=id, activeOnly=activeOnly)


    def LookupUser(self, id=None, ident=None, name=None, email=None, activeOnly=1, reloadFromDB=0):
        """ 
        reloadFromDB deprecated. will be removed in the future
        """
        if not id:
            # lookup id for name, email or ident
            loginByEmail = self.app.configuration.get("loginByEmail")
            param = {}
            if activeOnly:
                param[u"pool_state"] = 1
            if name:
                param[u"name"] = name
            elif email:
                param[u"email"] = email
            elif ident:
                if not self.identityField:
                    raise ValueError, "user identity filed not set"
                param[self.identityField] = ident
                
            user = self.Select(pool_type=u"user", parameter=param, fields=[u"id"], max=2)
            
            # check multiple identity fields
            if len(user)==0 and loginByEmail:
                if name:
                    del param["name"]
                    param["email"] = name
                    user = self.Select(pool_type=u"user", parameter=param, fields=[u"id"], max=2)
                elif email:
                    del param["email"]
                    param["name"] = email
                    user = self.Select(pool_type=u"user", parameter=param, fields=[u"id"], max=2)
                return None
            
            if len(user)!=1:
                return None
            id = user[0][0]
            
        user = self.GetObj(id)
        if not user or (activeOnly and not user.meta.get("pool_state")==1):
            return None
        return user
     

    def GetUsers(self, **kw):
        """
        """
        return self.SearchType(u"user", {u"pool_state":1}, [u"id",u"title",u"name",u"groups",u"lastlogin"])


    def GetUserInfos(self, userids, fields=None, activeOnly=True):
        """
        """
        param = {self.identityField:userids}
        if activeOnly:
            param[u"pool_state"] = 1
        if not fields:
            fields = [u"id", u"name", u"email", u"title", u"groups", self.identityField]
        return self.SelectDict(pool_type=u"user", parameter=param, fields=fields, operators={self.identityField:u"IN"})
    
    
    def GetUsersWithGroup(self, group, fields=None, activeOnly=True):
        """
        """
        param = {u"groups":group}
        if activeOnly:
            param[u"pool_state"] = 1
        operators = {u"groups": "LIKE"}
        if not fields:
            fields = [u"name",u"groups"]
        elif not u"groups" in fields:
            fields = list(fields)
            fields.append(u"groups")
        users = self.SelectDict(pool_type=u"user", parameter=param, fields=fields, operators=operators)
        # verify groups
        verified = []
        for u in users:
            try:
                g = json.loads(u["groups"])
            except:
                continue
            if group in g:
                verified.append(u)
        return verified


    def DeleteUser(self, ident, currentUser=None):
        """
        returns status and report list
        """
        report = []
        if isinstance(ident, basestring):
            if not ident:
                report.append(_(u"Invalid user."))
                return False, report
    
            user = self.LookupUser(ident=ident, activeOnly=0)
            if not user:
                report.append(_(u"Invalid username."))
                return False, report
        else:
            user = ident

        if not self.Delete(user.id, obj=user, user=currentUser):
            report.append(_(u"Sorry. An error occured."))
            return False, report

        report.append(_(u"User deleted."))
        return True, report


    # to be removed ------------------------------------------------------
    def GetUserGroups(self, name, activeOnly=1):
        """
        """
        user = self.GetUser(name, activeOnly=activeOnly)
        if not user:
            return None
        return user.data.groups


    def Encrypt(self, string):
        try:
            return base64.encodestring(string)
        except:
            return string

    def Decrypt(self, string):
        try:
            return base64.decodestring(string)
        except:
            return string




# Root definition ------------------------------------------------------------------

#@nive_module
configuration = RootConf(
    id = "udb",
    context = "nive.userdb.root.root",
    template = "root.pt",
    views = ["nive.userdb.userview.view"],
    default = 1,
    subtypes = "*",
    name = _(u"User account"),
    description = __doc__
)



class adminuser(object):
    """
    Admin User object with groups and login possibility. 
    """
    
    def __init__(self, values):
        self.id = 0
        self.data = Conf(**values)
        self.meta = Conf()
        self.groups = self.data.groups = (u"group:admin",)

    def __str__(self):
        return self.data.get("name",str(self.id))

    def Authenticate(self, password):
        return password == self.data["password"]
    
    def Login(self):
        """ """

    def Logout(self):
        """ """

    def GetGroups(self, context=None):
        """ """
        return self.groups

    def InGroups(self, groups):
        """
        check if user has one of these groups
        """
        if isinstance(groups, basestring):
            return groups in self.groups
        for g in groups:
            if g in self.groups:
                return True
        return False
    


from nive.components.reform.schema import Invalid
from nive.components.reform.schema import Email

def UsernameValidator(node, value):
    """ 
    Validator which succeeds if the username does not exist.
    Can be used for the name input field in a sign up form.
    """
    # lookup name in database
    r = node.widget.form.context.root()
    u = r.LookupUser(name=value, activeOnly=0)
    if u:
        # check if its the current user
        ctx = node.widget.form.context
        if len(u)==1 and ctx.id == u[0][0]:
            return
        err = _(u"Username '${name}' already in use. Please choose a different name.", mapping={'name':value})
        raise Invalid(node, err)

def EmailValidator(node, value):
    """ 
    Validator which succeeds if the email does not exist.
    Can be used for the email input field in a sign up form.
    """
    # validate email format
    Email()(node, value)
    # lookup email in database
    r = node.widget.form.context.root()
    u = r.LookupUser(email=value, activeOnly=0)
    if u:
        # check if its the current user
        ctx = node.widget.form.context
        if len(u)==1 and ctx.id == u[0][0]:
            return
        err = _(u"Email '${name}' already in use. Please use the login form if you already have a account.", mapping={'name':value})
        raise Invalid(node, err)

