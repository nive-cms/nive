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
Root for public user functions
-------------------------------------------
Provides functionality to safely add users with several activation and 
mailing options.
"""

import types, base64, random, string
from time import time
import uuid

from nive.definitions import RootConf, Conf, StagUser
from nive.security import User
from nive.components.objects.base import RootBase
from nive.i18n import _


class Unauthorized(Exception):
    """
    failed login
    """


import thread

class UserCache(object):
    """
    User caching support. Caches users including data as attributes. 
    
    Options: ::

        useCache = enable or disable caching
        cacheTypes = a list of pool_types to be cached. not matching types are not cached
        expires = objs are reloaded or purged after this many seconds. 0 = never expires 
    """
    useCache = True
    cacheTypes = (u"user",)
    expires = 0 

    def Cache(self, obj, id):
        """
        """
        if not self.useCache:
            return 
        try:
            t = obj.GetTypeID()
            if self.cacheTypes and not t in self.cacheTypes:
                return
        except:
            if self.cacheTypes:
                return 
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            setattr(self, self._Cachename(id), (obj, time()))
            if lock.locked():
                lock.release()
        except:
            if lock and lock.locked():
                lock.release()

    def GetFromCache(self, id):
        """
        returns the cached object
        """
        if not self.useCache:
            return None
        n = self._Cachename(id)
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            if hasattr(self, n):
                o = getattr(self, n)
                if lock.locked():
                    lock.release()
                return o[0]
        except:
            if lock and lock.locked():
                lock.release()
        return None

    def GetAllFromCache(self):
        """
        returns all cached objects
        """
        objs = []
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            for v in self.__dict__.keys():
                if v[:5] == "__c__":
                    objs.append(getattr(self, v)[0])
            if lock.locked():
                lock.release()
        except:
            if lock and lock.locked():
                lock.release()
        return objs

    def RemoveCache(self, id):
        """
        """
        if not self.useCache:
            return 
        try:
            lock = thread.allocate_lock()
            lock.acquire(1)
            try:
                delattr(self, self._Cachename(id))
            except:
                pass
            if lock.locked():
                lock.release()
        except:
            if lock and lock.locked():
                lock.release()

    def _Cachename(self, id):
        return "__c__" + str(hash(str(id)))





class root(UserCache, RootBase):
    """
    """
    
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
        if self.LookupUser(name=name, activeOnly=0):
            report.append(_(u"Username '${name}' already in use. Please choose a different name.", mapping={u"name":name}))
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
                result, value = tool(body=body, title=title, recvids=[name], force=1)
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


    def MailUserPass(self, email = None, mailtmpl = None):
        """
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
                report.append(_(u"No account found with that email address. Please try again."))
                return False, report

        email = obj.data.get("email")
        title = obj.meta.get("title")
        name = obj.data.get("name")
        if email == "":
            report.append(_("No email address found."))
            return False, report
        recv = [(email, title)]

        if mailtmpl:
            title = mailtmpl.title
            body = mailtmpl(user=obj,password=obj.data.get("password"))
        else:
            title = _("Password")
            body = obj.data.get("password")
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


    def MailResetPass(self, currentUser, email = None, mailtmpl = None):
        """
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
                report.append(_(u"No account found with that email address. Please try again."))
                return False, report

        email = obj.data.get("email")
        title = obj.meta.get("title")
        name = obj.data.get("name")
        if email == "":
            report.append(_("No email address found."))
            return False, report
        recv = [(email, title)]

        passwd = self.GenerateID(6)
        obj.data["password"] = passwd
        obj.Commit(user=currentUser)
        if mailtmpl:
            title = mailtmpl.title
            body = mailtmpl(user=obj,password=passwd)
        else:
            title = _("Password")
            body = passwd
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
        report.append(_(u"The password has been sent to your email address."))
        return True, report
   

    def GenerateID(self, length=20, repl="-"):
        # generates a id
        return str(uuid.uuid4()).replace(repl,"")[:length]
        

    def DeleteUser(self, name):
        """
        returns status and report list
        """
        report = []
        # check email exists
        if name == "" or not name:
            report.append(_(u"Invalid username."))
            return False, report

        user = self.LookupUser(name=name, activeOnly=0)
        if not user:
            report.append(_(u"Invalid username."))
            return False, report

        self.RemoveCache(name)
        if not self.Delete(user.GetID(), obj=user, user=user):
            report.append(_(u"Sorry. An error occured."))
            return False, report

        report.append(_(u"User deleted."))
        return True, report


    # Login/logout and user sessions ------------------------------------------------------------------------------------------------------

    def Login(self, name, password, raiseUnauthorized = 1):
        """
        returns status and report list
        """
        report = []

        # session login
        user = self.GetUserByName(name)
        if not user and self.app.configuration.get("loginByEmail"): 
            user = self.GetUserByMail(name)
        if not user:
            if raiseUnauthorized:
                raise Unauthorized, "Login failed"
        
        if not user.Authenticate(password):
            if raiseUnauthorized:
                raise Unauthorized, "Login failed"
            report.append(_(u"Login failed. Please check your username and password."))
            return False, report

        # call user
        user.Login()
        report.append(_(u"Logged in."))
        return True, report


    def Logout(self, name):
        """
        Logout and delete session data
        """
        user = self.GetUserByName(name)
        if not user:
            return False
        user.Logout()
        return True


    # Password, activationID ------------------------------------------------------------------------------------------------------

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


    # User ------------------------------------------------------------------------------------------------------

    def GetUserByName(self, name, activeOnly=1):
        """
        """
        return self.LookupUser(name=name, activeOnly=activeOnly)


    def GetUserByID(self, id, activeOnly=1):
        """
        """
        user = self.GetObj(id)
        if not user or (activeOnly and not user.meta.get("pool_state")==1):
            return None
        return user


    def GetUserByMail(self, email, activeOnly=1):
        """
        """
        user = self.Select(pool_type=u"user", parameter={u"email":email}, fields=[u"id",u"name",u"email"], max=2, operators={u"email":u"="})
        if len(user) != 1:
            return None
        if user[0][2] != email:
            return None
        return self.LookupUser(name=user[0][1], activeOnly=activeOnly)


    def GetUserGroups(self, name, activeOnly=1):
        """
        """
        user = self.LookupUser(name=name, activeOnly=activeOnly)
        if not user:
            return None
        return user.data.groups


    def LookupUser(self, name=None, id=None, activeOnly=1, reloadFromDB=0):
        """
        """
        if id:
            user = self.GetObj(id)
            if not user or (activeOnly and not user.meta.get("pool_state")==1):
                return None
            return user
        elif name:
            user = self.GetFromCache(name)
            if user:
                return user
            # load admin user from configuration
            try:
                app = self.app
                if app.configuration.admin["name"] == name:
                    return adminuser(app.configuration.admin)
            except:
                pass
            
            user =  self.Select(pool_type=u"user", parameter={u"name":name}, fields=[u"id"], max=2, operators={u"name":u"="})
            if len(user)==0:
                return None
            id = user[0][0]
            if id:
                user = self.GetObj(id)
                if not user or (activeOnly and not user.meta.get("pool_state")==1):
                    return None
                self.Cache(user, name)
                return user
        return None


    def GetUserInfos(self, userids, fields=["name", "email", "title"], activeOnly=True):
        """
        """
        param = {u"name":userids}
        if activeOnly:
            param[u"pool_state"] = 1
        users = self.SelectDict(pool_type=u"user", parameter=param, fields=fields, operators={u"name":u"IN"})
        return users
    
    
    def GetUsersWithGroup(self, group, fields=[u"name"], activeOnly=True):
        """
        """
        param = {u"groups":group}
        if activeOnly:
            param[u"pool_state"] = 1
        users = self.SelectDict(pool_type=u"user", parameter=param, fields=fields)
        return users


    def GetUsers(self, **kw):
        """
        """
        users = self.SearchType(u"user", {u"pool_state":1}, [u"id",u"title",u"name",u"groups",u"lastlogin"])
        return users


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
        """
        events: login()
        """
        self.AddToCache()

    def Logout(self):
        """
        events: logout()
        """
        self.RemoveFromCache()

    def GetGroups(self, context=None):
        """
        groups
        """
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
    
    # System ------------------------------------------------

    def AddToCache(self):
        pass
        #self.GetParent().Cache(self, self.id)

    def RemoveFromCache(self):
        pass
        #self.GetParent().RemoveCache(self.id)



from nive.components.reform.schema import Invalid
from nive.components.reform.schema import Email

def UsernameValidator(node, value):
    """ 
    Validator which succeeds if the username does not exist.
    Can be used for the name input field in a sign up form.
    """
    # lookup name in database
    r = node.widget.form.context.root()
    u = r.Select(pool_type=u"user", parameter={u"name": value}, fields=[u"id",u"name",u"email"], max=2, operators={u"name":u"="})
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
    u = r.Select(pool_type=u"user", parameter={u"email": value}, fields=[u"id",u"name",u"email"], max=2, operators={u"email":u"="})
    if u:
        # check if its the current user
        ctx = node.widget.form.context
        if len(u)==1 and ctx.id == u[0][0]:
            return
        err = _(u"Email '${name}' already in use. Please use the login form if you already have a account.", mapping={'name':value})
        raise Invalid(node, err)

