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
Receivers are looked up by user ids or roles. Sender name, receiver, title, and body can be set as values by call.

mails as list with [(email, name),...] ("name@mail.com","Name")
"""

import types, string
import time
import logging

from smtplib import SMTPServerDisconnected, SMTPRecipientsRefused, SMTPHeloError, SMTPSenderRefused, SMTPDataError, SMTPException

from nive.utils.utils import ConvertToList
from nive.definitions import ConfigurationError
from nive.definitions import ToolConf, FieldConf
from nive.tools import Tool
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
    FieldConf(id="ssl",   name=_(u"Use SSL"),           datatype="bool",         required=0,     readonly=0, default=1,      description=u""),
    FieldConf(id="maillog",  name=_(u"Log mails"),      datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
    FieldConf(id="showToListInHeader",name=_(u"Show all receivers in header"), datatype="bool", required=0, readonly=0, default=0,    description=u""),

    FieldConf(id="debug", name=_(u"Debug mode"),        datatype="bool",         required=0,     readonly=0, default=False, description=_(u"All mails are sent to 'Receiver role' or 'Receiver User IDs' field default value. No external mail address is used.")), 
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
        log = logging.getLogger(maillog or "sendMail")


        # lookup receivers
        recvs = []
        if recvmails:
            if isinstance(recvmails, basestring):
                recvs.append((recvmails, u""))
            else:
                recvs.extend(recvmails)
        if recvids or recvrole:
            recvs.extend(self._GetRecv(recvids, recvrole, force, self.app))
        if cc:
            cc = self._GetRecv(cc, None, force, self.app)
            if cc:
                recvs.extend(cc)
        if bcc:
            bcc = self._GetRecv(bcc, None, force, self.app)
            if bcc:
                recvs.extend(bcc)
        
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
        if not host:
            raise ConfigurationError, "Empty mail host"
        mailer = DvSMTP(host, port)
        try:
            mailer.ehlo()
            if ssl:
                mailer.starttls()
                mailer.ehlo()
        except (SMTPServerDisconnected, SMTPHeloError, SMTPException), e:
            log.error(" %s", repr(e))
            return False

        if user != u"" and pass_ != u"":
            mailer.Login(user, str(pass_))
        contentType = u"text/plain"
        if html:
            contentType = u"text/html"
        if utf8:
            contentType += u"; charset=utf-8"

        if debug:
            mails_original = u""
            for m in recvs:
                mails_original += m + u"\r\n<br/>"
            body += u"""\r\n<br/><br/>\r\nDEBUG\r\n<br/> Original receiver: \r\n<br/>""" + mails_original
            # in debug mode use default receiver mail as receiving address for all mails
            recvs = [(recvmails, u"")]

        result = 1
        if showToListInHeader:
            result = mailer.Send3(fromMail, recvs, title, body, fromName=sendername, inTo=to, contentType=contentType, cc=cc, bcc=bcc, sender=senderMail, replyTo=replyTo)
            self.stream.write((u", ").join(r))
            mailer.quit()
        else:
            for recv in recvs:
                try:
                    mailer.Send2(fromMail, recv[0], title, body, sendername, recv[1], contentType=contentType, cc=cc, bcc=bcc, sender=senderMail, replyTo=replyTo)
                    self.stream.write(recv[0] + u" ok, ")
                    if maillog:
                        logdata = u"%s - %s - %s" % (recv[0], recv[1], title)
                        log.debug(u" %s", logdata)
                    pass
                except (SMTPServerDisconnected,), e:
                    result = 0
                    log.error(" %s", repr(e))
                    logdata = u"%s - %s - %s" % (recv[0], recv[1], title)
                    log.error(u"  ->  %s", logdata)
                    self.stream.write(str(e))
                    break
                except (SMTPSenderRefused, SMTPRecipientsRefused, SMTPDataError), e:
                    result = 0
                    log.error(" %s", repr(e))
                    logdata = u"%s - %s - %s" % (recv[0], recv[1], title)
                    log.error(u"  ->  %s", logdata)
                    self.stream.write(str(e))
            mailer.quit()
        return result


    def _GetMailStr(self, mail):
        if isinstance(mail, basestring):
            return mail
        if isinstance(mail, (list,tuple)) and len(mail) > 1:
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
            if isinstance(recvids, basestring):
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


    def Send2(self, fromMail, toMail, subject, body, fromName=u"", toName=u"", contentType=u"text/plain", cc=u"", bcc=u"", sender=u"", replyTo=u""):
        """
        does not call quit after sending
        """
        aM = self.FormatStdMail(fromMail, toMail, subject, body, fromName, toName, contentType, cc, bcc, sender, replyTo)
        result = self.sendmail(fromMail, toMail, aM)
        return result


    def Send3(self, fromMail, toMail, subject, body, fromName=u"", contentType=u"text/plain", inTo=u"", cc=u"", bcc=u"", sender=u"", replyTo=u""):
        """
        does not call quit after sending
        toMail = mail recv list
        inTo = mail header To str
        """
        aM = self.FormatStdMail(fromMail, inTo, subject, body, fromName=fromName, contentType=contentType, cc=cc, bcc=bcc, sender=sender, replyTo=replyTo)
        result = []
        for m in toMail:
            if isinstance(m, (list,tuple)):
                m=m[0]
            self.sendmail(fromMail, m, aM)
            result.append(m + u" ok")
        return result


    def FormatStdMail(self, fromMail, toMail, subject, body, fromName=u"", toName=u"", contentType=u"text/plain", cc=u"", bcc=u"", sender=u"", replyTo=u""):
        """
        """
        aH = self.FormatStdMailHeader(fromMail, toMail, subject, fromName, toName, contentType, cc, bcc, sender, replyTo)
        aH += body + u"\r\n\r\n"
        return aH


    def FormatStdMailHeader(self, fromMail, toMail, subject, fromName=u"", toName=u"", contentType=u"text/plain", cc=u"", bcc=u"", sender=u"", replyTo=u""):
        """
        formats std mail header
        """
        aHeader = ""
        if fromName == u"":
            aHeader += u"From: %s\r\n" % fromMail
        else:
            aHeader += u"From: \"%s\" <%s>\r\n" % (fromName, fromMail)

        if isinstance(toMail, (list,tuple)):
            toMail = (u", ").join(toMail)
            aHeader += u"To: %s\r\n" % toMail
        elif toName == u"":
            aHeader += u"To: %s\r\n" % toMail
        else:
            aHeader += u"To: \"%s\" <%s>\r\n" % (toName, toMail)

        if cc:
            if isinstance(cc, (list,tuple)):
                cc = (u", ").join(cc)
            aHeader += u"Cc: %s\r\n" % cc
        if bcc:
            if isinstance(bcc, (list,tuple)):
                bcc = (u", ").join(bcc)
            aHeader += u"Bcc: %s\r\n" % bcc

        if sender:
            aHeader += u"Sender: %s\r\n" % sender
        if replyTo:
            aHeader += u"Reply-To: %s\r\n" % replyTo

        aHeader += u"Subject: %s\r\n" % subject
        aHeader += u"Date: %s\r\n" % self._FormatDate()
        aHeader += u"Content-Type: %s\r\n\r\n" % (contentType)
        return aHeader


    def _FormatDate(self):
        """Return the current date and time formatted for a message header."""
        weekdayname = [u'Mon', u'Tue', u'Wed', u'Thu', u'Fri', u'Sat', u'Sun']
        monthname = [None, u'Jan', u'Feb', u'Mar', u'Apr', u'May', u'Jun', u'Jul', u'Aug', u'Sep', u'Oct', u'Nov', u'Dec']
        now = time.time()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(now)
        s = u"%s, %02d %3s %4d %02d:%02d:%02d GMT" % (weekdayname[wd], day, monthname[month], year, hh, mm, ss)
        return s

