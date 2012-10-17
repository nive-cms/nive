# -*- coding: utf-8 -*-
#----------------------------------------------------------------------
# Nive cms
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
Receivers are looked up by user ids or roles. Sender name, receiver, title, and body can be set as values by call.

mails as list with [(email, name),...] ("name@mail.com","Name")
"""

import types, string
import time

from nive.utils.utils import LOG
from nive.utils.utils import ConvertToList

from nive.tools import Tool
from nive.definitions import ToolConf, FieldConf
from nive.i18n import _

configuration = ToolConf()
configuration.id = "sendMail"
configuration.context = "nive.components.tools.sendMail.sendMail"
configuration.name = _(u"Send mails to registered users")
configuration.description = __doc__
configuration.apply = None
configuration.data = [
    FieldConf(id="host",    name=_(u"SMTP host"),       datatype="string",       required=1,     readonly=1, default=u"",    description=u""),
    FieldConf(id="port",    name=_(u"SMTP port"),       datatype="number",       required=1,     readonly=1, default=21,     description=u""),
    FieldConf(id="sender",  name=_(u"SMTP sender mail"),datatype="email",        required=1,     readonly=1, default=u"",    description=u""),
    FieldConf(id="user",    name=_(u"SMTP user"),       datatype="string",       required=0,     readonly=1, default=u"",    description=u""),
    FieldConf(id="pass_",   name=_(u"SMTP password"),   datatype="password",     required=0,     readonly=1, default=u"",    description=u""),

    FieldConf(id="sendername",name=_(u"Sender name"),   datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
    FieldConf(id="fromMail",  name=_(u"Sender mail"),   datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
    FieldConf(id="replyTo",   name=_(u"Reply to"),      datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
    FieldConf(id="recvrole",  name=_(u"Receiver role"),    datatype="string",    required=1,     readonly=0, default=u"",    description=u""),
    FieldConf(id="recvids",   name=_(u"Receiver User IDs"),datatype="string",    required=1,     readonly=0, default=u"",    description=u""),
    FieldConf(id="recvmails", name=_(u"Receiver Mail"),    datatype="string",    required=1,     readonly=0, default=u"",    description=u""),
    FieldConf(id="force",     name=_(u"Ignore notify settings"),datatype="bool", required=0,     readonly=0, default=0,      description=u""),
    FieldConf(id="cc",        name=_(u"CC"),            datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
    FieldConf(id="bcc",       name=_(u"BCC"),           datatype="string",       required=0,     readonly=0, default=u"",    description=u""),

    FieldConf(id="title", name=_(u"Title"),             datatype="string",       required=1,     readonly=0, default=u"",    description=u""),
    FieldConf(id="body",  name=_(u"Text"),              datatype="htext",        required=0,     readonly=0, default=u"",    description=u""),
    FieldConf(id="html",  name=_(u"Html format"),       datatype="bool",         required=0,     readonly=0, default=1,      description=u""),
    FieldConf(id="utf8",  name=_(u"UTF-8 encoding"),    datatype="bool",         required=0,     readonly=0, default=1,      description=u""),
    FieldConf(id="ssl",   name=_(u"Use SSL"),           datatype="bool",         required=0,     readonly=0, default=0,      description=u""),
    FieldConf(id="maillog",  name=_(u"Log mails"),      datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
    FieldConf(id="showToListInHeader",name=_(u"Show all receivers in header"), datatype="bool", required=0, readonly=0, default=0,    description=u""),

    FieldConf(id="debug", name=_(u"Debug mode"),        datatype="bool",         required=0,     readonly=0, default=False, description=_(u"All mails are sent to 'Receiver role' or 'Receiver User IDs' field default values. No external mail address is used.")), 
]
configuration.mimetype = "text/html"



class sendMail(Tool):

    def _Run(self, **values):
        """
        """
        
        host = values.get("host")
        port = values.get("port")
        sender = values.get("sender")
        user = values.get("user")
        pass_ = values.get("pass_")

        sendername = values.get("sendername")
        fromMail = values.get("fromMail")
        replyTo = values.get("replyTo")

        recvids = values.get("recvids")
        recvrole = values.get("recvrole")
        recvmails = values.get("recvmails")
        cc = values.get("cc")
        bcc = values.get("bcc")

        title = values.get("title")
        body = values.get("body")
        html = values.get("html")
        utf8 = values.get("utf8")
        ssl = values.get("ssl")

        showToListInHeader = values.get("showToListInHeader")
        force = values.get("force")
        debug = values.get("debug")
        maillog = values.get("maillog")

        # lookup receivers
        recvs = self._GetRecv(recvids, recvrole, force, self.app)
        if recvmails:
            recvs += recvmails
        cc = self._GetRecv(cc, None, force, self.app)
        bcc = self._GetRecv(bcc, None, force, self.app)
        mails = recvs + cc + bcc
        
        if len(recvs) == 0:
            self.stream.write(_(u"No receiver for the e-mail! Aborting."))
            return 0

        temp = []
        for r in recvs:
            temp.append(self._GetMailStr(r))
        to = temp
        temp = []
        for r in cc:
            temp.append(self._GetMailStr(r))
        cc = temp
        temp = []
        for r in bcc:
            temp.append(self._GetMailStr(r))
        bcc = temp

        if fromMail and fromMail != u"":
            senderMail = sender
        else:
            fromMail = sender
            senderMail = u""

        #raise "1", mails
        mailer = DvSMTP(host, port)
        if ssl:
            mailer.ehlo()
            mailer.starttls()
            mailer.ehlo()
        if user != u"" and pass_ != u"":
            mailer.Login(user, str(pass_))
        contentType = u"text/plain"
        if html:
            contentType = u"text/html"
        if utf8:
            contentType += u"; charset=utf-8"

        if debug:
            recvs = self._GetRecv(values.get("recvids"), values.get("recvrole"), force, self.app)
            cc = []
            bcc = []
            mails_original = u""
            for m in mails:
                mails_original += (u" <").join(m) + u">\r\n<br/>"
            mails = recvs + cc + bcc
            body += u"""\r\n<br/><br/>\r\nDEBUG\r\n<br/> Original receiver: \r\n<br/>""" + mails_original

        result = 1
        if showToListInHeader:
            result = mailer.Send3(fromMail, mails, title, body, inFromName=sendername, inTo=to, inContentType=contentType, inCC=cc, inBCC=bcc, inSender=senderMail, inReplyTo=replyTo)
            self.stream.write((u", ").join(r))
            mailer.quit()
        else:
            for recv in mails:  #recvs:
                try:
                    if maillog:
                        logdata = u"-----------------------------------------------------------------------\r\n%s - %s - %s\r\n\r\n%s" % (recv[0], recv[1], title, body)
                        LOG(data = logdata, path=maillog, t=0)
                    mailer.Send2(fromMail, recv[0], title, body, sendername, recv[1], inContentType=contentType, inCC=cc, inBCC=bcc, inSender=senderMail, inReplyTo=replyTo)
                    self.stream.write(recv[0] + u" ok, ")
                    pass
                except Exception, e:
                    result = 0
                    if maillog:
                        LOG(data = "ERROR: "+str(e), path="log/mail.log", t=0)
                    self.stream.write(str(e))
            mailer.quit()
        return result


    def _GetMailStr(self, mail):
        if type(mail) in (types.StringType,types.UnicodeType):
            return mail
        if len(mail) > 1 and mail[1] != u"":
            return u'"%s" <%s>' % (mail[1], mail[0])
        return mail[0]
        

    def _GetRecv(self, recvids, recvrole, force, app):
        try:
            userdb = app.root()
            userdb.GetUsersWithRole
        except:
            try:
                userdb = app.portal.userdb.GetRoot()
            except:
                return []
        recvList = []
        # check roles
        recvids2 = []
        if recvrole:
            recvids2 = userdb.GetUsersWithRole(recvrole, activeOnly=not force)
        # get users
        if recvids:
            if type(recvids) == type("s"):
                recvids = ConvertToList(recvids)
            for user in userdb.GetUserInfos(recvids+recvids2, ["name", "email", "title"], activeOnly=not force):
                if user and user["email"] != u"":
                    if force or user.get("notify", 1):
                        recvList.append([user["email"], user["title"]])
        return recvList



from smtplib import SMTP


class DvSMTP(SMTP):
    """
    SMTP subclass
    """

    def Login(self, user, passw):
        """
        """
        return self.login(user, passw)


    def Send2(self, inFromMail, inToMail, inSubject, inBody, inFromName = u"", inToName = u"", inContentType = u"text/plain", inCC = u"", inBCC = u"", inSender = u"", inReplyTo = u""):
        """
        does not call quit after sending
        """
        aM = self.FormatStdMail(inFromMail, inToMail, inSubject, inBody, inFromName, inToName, inContentType, inCC, inBCC, inSender, inReplyTo)
        result = self.sendmail(inFromMail, inToMail, aM)
        return result


    def Send3(self, inFromMail, inToMail, inSubject, inBody, inFromName = u"", inContentType = u"text/plain", inTo = u"", inCC = u"", inBCC = u"", inSender = u"", inReplyTo = u""):
        """
        does not call quit after sending
        inToMail = mail recv list
        inTo = mail header To str
        """
        aM = self.FormatStdMail(inFromMail, inTo, inSubject, inBody, inFromName=inFromName, inContentType=inContentType, inCC=inCC, inBCC=inBCC, inSender=inSender, inReplyTo=inReplyTo)
        result = []
        for m in inToMail:
            if type(m) == type([]):
                m=m[0]
            try:
                self.sendmail(inFromMail, m, aM)
                result.append(m + u" ok")
            except Exception, e:
                result.append(str(e))
        return result


    def FormatStdMail(self, inFromMail, inToMail, inSubject, inBody, inFromName = u"", inToName = u"", inContentType = u"text/plain", inCC = u"", inBCC = u"", inSender = u"", inReplyTo = u""):
        """
        """
        aH = self.FormatStdMailHeader(inFromMail, inToMail, inSubject, inFromName, inToName, inContentType, inCC, inBCC, inSender, inReplyTo)
        aH += inBody + u"\r\n\r\n"
        return aH


    def FormatStdMailHeader(self, inFromMail, inToMail, inSubject, inFromName = u"", inToName = u"", inContentType = u"text/plain", inCC = u"", inBCC = u"", inSender = u"", inReplyTo = u""):
        """
        formats std mail header
        """
        aHeader = ""
        if inFromName == u"":
            aHeader += u"From: %s\r\n" % inFromMail
        else:
            aHeader += u"From: \"%s\" <%s>\r\n" % (inFromName, inFromMail)

        if type(inToMail) == type([]):
            inToMail = (u", ").join(inToMail)
            aHeader += u"To: %s\r\n" % inToMail
        elif inToName == u"":
            aHeader += u"To: %s\r\n" % inToMail
        else:
            aHeader += u"To: \"%s\" <%s>\r\n" % (inToName, inToMail)

        if inCC and inCC != u"" and inCC != []:
            if type(inCC) == type([]):
                inCC = (u", ").join(inCC)
            aHeader += u"Cc: %s\r\n" % inCC
        if inBCC and inBCC != u"" and inBCC != []:
            if type(inBCC) == type([]):
                inBCC = (u", ").join(inBCC)
            aHeader += u"Bcc: %s\r\n" % inBCC

        if inSender:
            aHeader += u"Sender: %s\r\n" % inSender
        if inReplyTo:
            aHeader += u"Reply-To: %s\r\n" % inReplyTo

        aHeader += u"Subject: %s\r\n" % inSubject
        aHeader += u"Date: %s\r\n" % self._FormatDate()
        aHeader += u"Content-Type: %s\r\n\r\n" % (inContentType)
        return aHeader


    def _FormatDate(self):
        """Return the current date and time formatted for a message header."""
        weekdayname = [u'Mon', u'Tue', u'Wed', u'Thu', u'Fri', u'Sat', u'Sun']
        monthname = [None, u'Jan', u'Feb', u'Mar', u'Apr', u'May', u'Jun', u'Jul', u'Aug', u'Sep', u'Oct', u'Nov', u'Dec']
        now = time.time()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(now)
        s = u"%s, %02d %3s %4d %02d:%02d:%02d GMT" % (weekdayname[wd], day, monthname[month], year, hh, mm, ss)
        return s

