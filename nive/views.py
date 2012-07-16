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
Basic view class for nive object views. 

Use this class as base for custom view definitions for file download support,
data rendering, url generation, http headers and user lookup. 
"""


import os
from time import time
from datetime import datetime
from nive.utils.utils import *
from nive.utils.dateTime import DvDateTime, FmtSeconds

from nive.definitions import *

from pyramid.response import Response
from pyramid.renderers import render_to_response, get_renderer, render
from pyramid.url import static_url, resource_url
from pyramid.view import render_view
from pyramid.security import authenticated_userid
from pyramid.security import has_permission
from pyramid.i18n import get_localizer

from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPOk, HTTPForbidden
from pyramid.exceptions import NotFound



class Unauthorized(Exception):
    """
    Raised by failed logins or insufficient permissions
    """
    


class BaseView(object):
    """    """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.viewModule = None
        self.appRequestKeys = []
        self._t = time()
        self.fileExpires = 3600


    # main document ---------------------------------------------------------

    def index_tmpl(self, path=None):
        if path:
            return get_renderer(path).implementation()
        if not self.viewModule or not self.viewModule.mainTemplate:
            return None
        return get_renderer(self.viewModule.mainTemplate).implementation()
    

    # url handling ----------------------------------------------------------------

    def Url(self, resource=None):
        """
        Generates the default url for the resource. Includes the file extension if one specified 
        for the object.
        
        If resource is None the current context object is used as resource.

        returns url
        """
        if not resource:
            resource=self.context
        if hasattr(resource, "extension"):
            return u"%s.%s" % (resource_url(resource, self.request)[:-1], resource.extension)
        return resource_url(resource, self.request)

    def FolderUrl(self, resource=None):
        """
        Generates the default url for the resource without extension and trailing '/'. 
        
        If resource is None the current context object is used as resource.

        returns url
        """
        if not resource:
            resource=self.context
        return resource_url(resource, self.request)

    def StaticUrl(self, file):
        """
        Generates the url for a static file.
        *file* is the filename to look the url up for. E.g. for the default static directory use ::
        
            <link tal:attributes="href view.StaticUrl('layout2.css')" 
                  rel="stylesheet" type="text/css" media="all" />
                  
         to reference a file in a different directory you must include the python module like ::

            <link tal:attributes="href view.StaticUrl('nive.cms.design:static/layout2.css')" 
                  rel="stylesheet" type="text/css" media="all" />
                  
        returns url
        """
        if not u":" in file and self.viewModule and self.viewModule.static:
            file = u"%s/%s" % (self.viewModule.static, file)
        return static_url(file, self.request)

    def FileUrl(self, fieldID, resource=None):
        """
        Generates the file url for the file contained in resource. The resource must have the 'file'
        view included (IFile). If the url is called the download is mapped to ``View.file``. 
        
        If resource is None the current context object is used as resource.

        returns url
        """
        if not resource:
            resource=self.context
        file = resource.files.get(fieldID)
        if not file:
            return u""
        return u"%sfile/%s" % (self.Url(resource), file.filename)

    def PageUrl(self, resource=None, usePageLink=0):
        """
        Generates the default page url for the resource with extension. If resource is a page element
        the page containing this element is used for the url. 
        
        If resource is None the current context object is used as resource.

        returns url
        """
        if not resource:
            resource=self.context
        try:
            page = resource.GetPage()
        except:
            page = self.context
        link = page.data.get("pagelink")
        if usePageLink and link:
            return link
        if hasattr(page, "extension"):
            return u"%s.%s" % (resource_url(page, self.request)[:-1], page.extension)
        return resource_url(page, self.request)

    def ResolveUrl(self, url, object=None):
        """
        Resolve a string to url for object or the current context.

        Possible values:
        
        - page_url
        - obj_url
        - obj_folder_url
        - parent_url
        """
        if not object:
            object = self.context
        if url == "page_url":
            url = self.PageUrl(object)
        elif url == "obj_url":
            url = self.Url(object)
        elif url.find("obj_folder_url")!=-1:
            url = url.replace("obj_folder_url", self.FolderUrl(object))
        elif url == "parent_url":
            url = self.Url(object.parent)
        return url
    
    
    def ResolveLink(self, link):
        """
        Resolve the link to a valid (page) URL. If the link is an existing object.id the url to the 
        page containing this object is returned.
        
        returns url
        """
        try:
            i = int(link)
            o = self.context.GetRoot().LookupObj(i)
            if not o:
                return link
            try:
                return self.PageUrl(o)
            except:
                return self.Url(o)
        except:
            return link


    def Redirect(self, url, messages=None, slot=""):
        """
        Redirect to the given URL. Messages are stored in session and can be accessed
        by calling ``request.session.pop_flash()``. Messages are added by calling
        ``request.session.flash(m, slot)``.
        """
        if messages:
            for m in messages:
                self.request.session.flash(m, slot)
        headers = None
        if hasattr(self.request.response, "headerlist"):
            headers = self.request.response.headerlist
        raise HTTPFound(location=url, headers=headers)
    

    def SendResponse(self, data, mime="text/html", raiseException=False, filename=None):
        """
        Creates a response with data as body. If ``raiseException`` is true the function
        will raise a HTTPOk Exception with data as body.
        
        If filename is not none the response will extended with a ``attachment; filename=filename``
        header.
        """
        cd = None
        if filename:
            cd = 'attachment; filename=%s'%(filename)
        if raiseException:
            raise HTTPOk(content_type=mime, body=data, content_disposition=cd)
        return Response(content_type=mime, body=data, content_disposition=cd)
        
        
    def AjaxRelocate(self, url, messages=None, slot="", raiseException=False):
        """
        Returns messages and X-Relocate header in response.
        If raiseException is True HTTPOk is raised with empty body.
        """
        if messages:
            for m in messages:
                self.request.session.flash(m, slot)
        headers = [('X-Relocate', str(url))]
        if hasattr(self.request.response, "headerlist"):
            headers += list(self.request.response.headerlist)
        self.request.response.headerlist = headers    
        if raiseException:
            raise HTTPOk(headers=headers, body_template="redirect "+url)
        return u""
    

    def Relocated(self):
        """
        Search current response headers for X-Relocate header
        and return it.
        """
        if not hasattr(self.request.response, "headerlist"):
            return u""
        for h in self.request.response.headerlist:
            if h[0].lower()== "x-relocate":
                return h[1]
        return u""
    

    def ResetFlashMessages(self, slot=None):
        """
        Removes all messages stored in session.
        """
        while self.request.session.pop_flash(slot):
            continue

    
    # render other elements and objects ---------------------------------------------
    
    def RenderView(self, obj, name="", secure=True, raiseUnauthorized=False, codepage="utf-8"):
        """
        Render a view for the object.
        
        *name* is the name of the view to be looked up.
        
        If *secure* is true permissions of the current user are checked against the view. If the
        user lacks the necessary permissions and empty string is returned or if *raiseUnauthorized*
        is True HTTPForbidden is raised. 
        
        returns rendered result
        """
        if not raiseUnauthorized:
            try:
                value = render_view(obj, self.request, name, secure)
            except HTTPForbidden:
                return u""
        else:
            value = render_view(obj, self.request, name, secure)
        if not value:
            return u""
        return unicode(value, codepage)

    
    def IsPage(self, object):
        """
        Check if object is a page.
        
        returns bool
        """
        return IPage.providedBy(object)
    
    def tmpl(self):
        """
        Default function for template rendering.
        """
        return {}
    
    # file handling ------------------------------------------------------------------
    
    def file(self):
        return self.File()

    def File(self):
        """
        Used by "file" view for the current context. 
        
        Calls SendFile() for the file matching the filename of the current url.
        """
        if not len(self.request.subpath):
            raise NotFound
        file = self.context.GetFileByName(self.request.subpath[0])
        if not file:
            return self.FileByID(self.request.subpath[0])
        return self.SendFile(file)


    def FileByID(self, fieldID):
        """
        Returns the file by id of the current context.
        """
        file = self.context.files.get(fieldID)
        if not file:
            raise NotFound
        return self.SendFile(file)


    def SendFile(self, file):
        """
        Creates the response and sends the file back. Uses the FileIterator.
        """
        try:
            last_mod = os.path.getmtime(file.path)
        except:
            return HTTPNotFound()
        r = Response(content_type=str(GetMimeTypeExtension(file.extension)), conditional_response=True)
        r.app_iter = FileIterable(file.path)
        r.content_length = file.size
        r.last_modified = last_mod
        r.etag = '%s-%s-%s' % (last_mod, file.size, hash(file.path))
        r.cache_expires(self.fileExpires)
        return r    


    # http caching ----------------------------------------------------------------

    def CacheHeader(self, response, user=None):
        """
        Adds a http cache header to the response. If user is not None *NoCache()* is called, otherwise
        *Modified()*.
        
        returns response
        """
        if user:
            return self.NoCache(response)
        return self.Modified(response, user)

    def NoCache(self, response, user=None):
        """
        Adds a no-cache header to the response.
        
        returns response
        """
        response.cache_control = u"no-cache"
        response.etag = '%s-%s-%s' % (response.last_modified, response.content_length, str(self.context.id))
        return response

    def Modified(self, response, user=None):
        """
        Adds a last modified header to the response. meta.pool_change is used as date.

        returns response
        """
        if user:
            d = DvDateTime()
            d.Now()
            response.last_modified = d.GetGMT()
        else:
            response.last_modified = self.context.meta.get("pool_change")
        response.etag = '%s-%s-%s' % (response.last_modified, response.content_length, str(self.context.id))
        return response


    # user and security -------------------------------------------------
    
    def User(self):
        """
        returns the *Authenticated User Object* or None
        """
        name = authenticated_userid(self.request)    
        if not name:
            return None
        return self.context.GetApp().GetPortal().userdb.GetRoot().GetUserByName(name)
    
    def UserName(self):
        """
        returns the *Authenticated User Name* or None
        """
        return authenticated_userid(self.request)    

    def Allowed(self, permission, context=None):
        """
        Check if the current user has the *permission* for the *context*.
        If context is none the current context is used
        
        returns True / False
        """
        if not context:
            context = self.context
        return has_permission(permission, context, self.request)
    
    def InGroups(self, groups):
        """
        Check if current user is in one of the groups.
        """
        user = self.User()
        return user.InGroups(groups)
    

    # render helper ---------------------------------------------------------
    
    def RenderFld(self, fld, data=None):
        """
        Render the data field for html display. Rendering depends on the datatype defined
        in the field configuration.
        
        If data is None the current context is used.
        
        returns string
        """        
        if isinstance(fld, basestring):
            fld = self.context.GetFieldConf(fld)
        if data == None:
            data = self.context.data.get(fld['id'], self.context.meta.get(fld['id']))
        if fld['datatype']=='file':
            url = self.FileUrl(fld['id'])
            if not url:
                return u""
            url2 = url.lower()
            if url2.find(u".jpg")!=-1 or url2.find(u".jpeg")!=-1 or url2.find(u".png")!=-1 or url2.find(u".gif")!=-1:
                return u"""<img src="%s" />""" % (url)
            return u"""<a href="%s">download</a>""" % (url)
        listItems = self.context.root().LoadListItems(fld, obj=self.context, pool_type=self.context.GetTypeID())
        return FieldRenderer().Render(fld, data, listItems = listItems)
    
    def HtmlTitle(self):
        t = self.request.environ.get(u"htmltitle")
        if t:
            return t
        return self.context.GetTitle()
    
    
    def Translate(self, text):
        """
        Tranlate a translation string. Extracts language from request.
        """
        localizer = get_localizer(self.request)
        return localizer.translate(text)
        
    
    def FmtTextAsHTML(self, text):
        """
        Converts newlines to <br/>.
        
        returns string
        """
        if not text:
            return u""
        if text.find(u"\r\n")!=-1:
            text = text.replace(u"\r\n",u"<br/>\r\n")
        else:
            text = text.replace(u"\n",u"<br/>\n")
        return text

    def FmtDateText(self, date, language=None):
        """
        Formats dates as readable text in conventional format.
        
        returns string
        """
        if not date:
            return u""
        d = DvDateTime(str(date))
        return d.GetTextGerman()

    def FmtDateNumbers(self, date, language=None):
        """
        Formats dates as numbers e.g 13.12.2011.
        
        returns string
        """
        if not date:
            return u""
        d = DvDateTime(str(date))
        return d.GetDDMMYYYY()

    def FmtSeconds(self, secs):
        """ seconds to readable text """
        return FmtSeconds(secs)

    def FmtBytes(self, size):
        """ bytes to readable text """
        return FormatBytesForDisplay(size)


    # parameter handling ------------------------------------------------------------

    def GetFormValue(self, key, default=None, request=None, method=None):
        """
        Extract a form field from request. 
        Works with webob requests and simple dictionaries.
        
        returns the value or *default*
        """
        if not request:
            request = self.request
        try:
            if method == "POST":
                value = request.POST.getall(key)
            elif method == "GET":
                value = request.GET.getall(key)
            else:
                value = request.POST.getall(key)
                if not value:
                    value = request.GET.getall(key)
            if isinstance(value, basestring):
                value = unicode(value, self.context.app.configuration.frontendCodepage)
        except (AttributeError,KeyError):
            if method == "POST":
                value = request.POST.get(key)
            elif method == "GET":
                value = request.GET.get(key)
            else:
                value = request.POST.get(key)
                if not value:
                    value = request.GET.get(key)
            if isinstance(value, basestring):
                value = unicode(value, self.context.app.configuration.frontendCodepage)
            if value==None:
                return default
            return value
        if not len(value):
            return default
        elif len(value)==1:
            if value==None:
                return default
            return value[0]
        if value==None:
            return default
        return value            


    def GetFormValues(self, request=None, method=None):
        """
        Extract all form fields from request. 
        Works with webob requests and simple dictionaries.
        
        returns dictionary
        """
        if not request:
            request = self.request
        try:
            if method == "POST":
                values = request.POST.mixed()
            elif method == "GET":
                values = request.GET.mixed()
            else:
                values = request.GET.mixed()
                values.update(request.POST.mixed())
        except AttributeError:
            try:
                if method == "POST":
                    values = request.POST
                elif method == "GET":
                    values = request.GET
                else:
                    values = request.GET
                    values.update(request.POST)
            except AttributeError:
                values = request
        return values    
    
    def ExtractAppKeys(self, **kw):
        param = kw
        keys = kw.keys()
        # extract request properties
        for k in self.appRequestKeys:
            if not k in keys:
                value = self.GetFormValue(k)
                if value:
                    param[k] = value
        return param

    
    def FmtURLParam(self, **kw):
        """
        Format all kw items as url parameter. 
        
        returns string
        """
        url = []
        params = self.ExtractAppKeys(**kw)
        #opt
        for p in params.keys():
            if len(url):
                url.append(u"&")
            url.append(u"%s=%s" % (p, params[p]))
        return u"".join(url)    #urllib.quote_plus()
    

    def FmtFormParam(self, **kw):
        """    
        Format all kw items as hidden input fields for forms.
        
        returns string 
        """
        form = []
        params = self.ExtractAppKeys(**kw)
        for p in params.keys():
            value = ConvertToStr(params[p])
            form.append(u"<input type='hidden' name='%s' value='%s' />" % (p, value))
        return "".join(form)


    def _LookupTemplate(self, tmplfile):
        if not self.viewModule or u":" in tmplfile:
            return tmplfile
        fn = self.viewModule.templates + u"/" + tmplfile
        try:
            if get_renderer(fn):
                return fn
        except ValueError:
            pass
        if not self.viewModule.parent:
            return tmplfile
        return u"%s/%s" % (self.viewModule.parent.templates, tmplfile)


    def mark(self):
        return time() - self._t

    def mark2(self):
        return time() - self.request.environ.get("START_TIME", self._t)



class FieldRenderer(object):
    
    def Render(self, fieldConf, value, useDefault = False, listItems = {}, render = True):
        """
        fieldConf = FieldConf of field to be rendered
        value = the value to be rendered
        useDefault = use default values from fieldConf if not found in value
        """
        data = ""
        if useDefault:
            data = fieldConf["default"]
        if value != None:
            data = value
        if not render:
            return data

        # format for output
        fType = fieldConf["datatype"]

        if fType == "bool":
            if data:
                data = u"Yes"
            else:
                data = u"No"

        elif fType == "date":
            if isinstance(data, datetime):
                return data.strftime(u"%d.%m.%Y %H:%M")
            aD = DvDateTime(str(data))
            data = aD.GetDDMMYYYY()

        elif fType in ("datetime", "timestamp"):
            fmt = GetDL(fieldConf.get("settings",[]), "format")
            if fmt:
                aD = DvDateTime(str(data))
                data = aD.GetFormat(fmt)
            else:
                if isinstance(data, datetime):
                    return data.strftime(u"%d.%m.%Y %H:%M")
                elif isinstance(data, basestring):
                    aD = DvDateTime(str(data))
                    if aD.GetHour() == 0 and aD.GetMin() == 0 and aD.GetSec() == 0:
                        data = aD.GetDDMMYYYY()
                    else:
                        if GetDL(fieldConf.get("settings",[]), "seconds")=="1":
                            data = aD.GetDDMMYYYYHHMMSS()
                        else:
                            data = aD.GetDDMMYYYYHHMM()

        elif fType == "bytesize":
            data = FormatBytesForDisplay(data)

        elif fType == "unit":
            if data == 0 or data == "0":
                return ""
            return data

        elif fType == "unitlist":
            if(type(data) == ListType):
                return ConvertListToStr(data)
            return str(data)

        elif fType == "list" or fType == "radio":
            aOpt = listItems
            if not aOpt or aOpt == []:
                aOpt = fieldConf.get("listItems", [])
                if aOpt == None:
                    aOpt = []

            if type(aOpt) == DictType:
                for aItem in aOpt.keys():
                    if aItem == data:
                        data = aOpt[aItem]
                        break
            else:
                for aItem in aOpt:
                    if type(aItem) == StringType:
                        if aItem == data:
                            data = aItem
                            break
                    else:
                        if aItem["id"] == data:
                            data = aItem["name"]
                            break

        elif fType == "mselection" or fType == "mcheckboxes":
            if(type(data) == ListType):
                aL = data    # value
            else:
                aL = DvString(str(data)).ConvertToList()
            aStr = []
            aOpt = listItems
            if not aOpt or aOpt == []:
                aOpt = fieldConf.get("listItems", [])
            for aRef in aL:
                if aOpt:
                    for aItem in aOpt:
                        if type(aItem) == StringType:
                            if aItem == aRef:
                                if len(aStr) > 0:
                                     aStr.append(u"<br />")
                                aStr += aItem
                        else:
                            if aItem["id"] == aRef:
                                if len(aStr) > 0:
                                     aStr.append(u"<br />")
                                aStr += aItem["name"]
                    if aOpt == [] or aOpt == {}:
                        if len(aStr) > 0:
                             aStr.append(u"<br />")
                        aStr += aRef

            data = u"".join(aStr)

        elif fType == "codelist":
            if type(data) == ListType or type(data) == TupleType:
                data = ConvertListToStr(data)
            if type(data) == StringType:
                data = ConvertToLong(data)
            aOpt = listItems
            if aOpt == [] or aOpt == {}:
                aOpt = fieldConf.get("listItems", [])
            if type(aOpt) == DictType:
                for aItem in aOpt.keys():
                    if aItem == data:
                        data = aOpt[aItem]
                        break
            else:
                for aItem in aOpt:
                    if type(aItem) == DictType:
                        if aItem["id"] == data:
                            data = aItem["name"]
                            break
                    else:
                        if aItem == data:
                            data = aItem
                            break

        elif fType == "mcodelist":
            if(type(data) == ListType):
                #aL = value
                for i in value:
                    if type(i) == StringType:
                        aL.append(int(i))
                    else:
                        aL.append(i)
            else:
                aL = DvString(str(data)).ConvertToNumberList()
            aStr = []
            aOpt = listItems
            if aOpt == [] or aOpt == {}:
                aOpt = fieldConf.get("listItems", [])
            for aRef in aL:
                for aItem in aOpt:
                    if type(aItem) == DictType:
                        if aItem["id"] == aRef:
                            if len(aStr) > 0:
                                 aStr.append(u"<br />")
                            aStr += aItem["name"]
                    else:
                        if aItem == aRef:
                            if len(aStr) > 0:
                                 aStr.append(u"<br />")
                            aStr += str(aItem)
            data = u"".join(aStr)

        elif fType == "text":
            data = data.replace(u"\r\n", u"\r\n<br />")

        elif fType == "url":
            if render:
                if data != u"" and data.find(u"http://") == -1:
                    data = u"http://" + data
                l = data[7:50]
                if len(data) > 50:
                    l += u"..."
                data = u"<a alt='%s' href='%s' target='_blank'>%s</a>" % (data, data, l)

        elif fType == "urllist":
            urllist = data
            data = []
            if len(urllist) and urllist[0] == u"[":
                urllist = urllist[1:-1]
                ul = urllist.split(u"', u'")
                ul[0] = ul[0][1:]
                ul[len(ul)-1] = ul[len(ul)-1][:-1]
            else:
                ul = urllist.replace(u"\r",u"")
                ul = ul.split(u"\n")
            links = []
            for l in ul:
                t = l.split(u"|||")
                title = u""
                url = t[0]
                if len(t) > 1:
                    title = t[1]
                if title != u"":
                    title = u'%s (%s)' % (title, url)
                else:
                    title = url
                links.append({"id": l, "name": title})
                data.append(u"<a alt='%s' title='%s' href='%s' target='_blank'>%s</a><br/>" % (title, title, url, title))
            data = u"".join(data)

        elif fType == "password":
            data = u"*****"

        elif fType == "_separator":
            data = u"<hr/>"

        elif fType == "_captcha":
            data = u""

        elif fType == "_csrf":
            data = u""

        return data
    

# Mail template mapper -------------------------------------------------

class Mail(object):
    """
    Mail template object with template link and title. ::
    
        mail = Mail(title="New mail", tmpl="mypackage:templates/foo.pt")
        body = mail(value1=1, value2=2)
        
    the body of the mail is generated by calling the mail object. *kw* parameters
    are passed on in template.render()
    """
    title = u""
    tmpl = None     # 'mypackage:templates/foo.pt'
    
    def __init__(self, title=u"", tmpl=None):
        self.title = title
        self.tmpl = tmpl
    
    def __call__(self, **kws):
        mail = render(self.tmpl, kws)
        return mail



# file download iterators --------------------------------------------------------

class FileIterable(object):
    def __init__(self, filename, start=None, stop=None):
        self.filename = filename
        self.start = start
        self.stop = stop

    def __iter__(self):
        return FileIterator(self.filename, self.start, self.stop)
    
    def app_iter_range(self, start, stop):
        return self.__class__(self.filename, start, stop)


class FileIterator(object):
    chunk_size = 4096*20

    def __init__(self, filename, start, stop):
        self.filename = filename
        self.fileobj = open(self.filename, 'rb')
        if start:
            self.fileobj.seek(start)
        if stop is not None:
            self.length = stop - start
        else:
            self.length = None
    
    def __iter__(self):
        return self
    
    def next(self):
        if self.length is not None and self.length <= 0:
            raise StopIteration
        chunk = self.fileobj.read(self.chunk_size)
        if not chunk:
            raise StopIteration
        if self.length is not None:
            self.length -= len(chunk)
            if self.length < 0:
                # Chop off the extra:
                chunk = chunk[:self.length]
        return chunk

# Configuration -------------------------------------------------
"""
???
"""
def Redirect(url, request, messages=None):
    headers = None
    if hasattr(request.response, "headerlist"):
        headers = request.response.headerlist
    return HTTPFound(location=url, headers=headers)

def AuthenticatedUserName(request):
    return authenticated_userid(request)

def forbidden_view(request):
    return Response('forbidden')


