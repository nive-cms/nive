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

import string
from types import StringType, UnicodeType, IntType, LongType
from nive.utils.utils import ConvertToNumberList

from nive.i18n import _
from nive.definitions import StagPage, StagPageElement



class Sort:
    """
    Container sort functionality
    
    Objects can explicitly be sorted and moved up or down in sequence.
    Sort values are stored in meta.pool_sort.
    """

    def Init(self):
        self.RegisterEvent("beforeCreate", "NewSort")


    def NewSort(self, data, type, **kw):
        """    """
        request = kw.get("request")
        insertAfterID = None
        if request:
            #!!!
            insertAfterID = self.GetFormValue(u"pepos", request=request)
        if not insertAfterID:
            s = self.GetMaxSort()+10
            data["pool_sort"] = s
            return
        o = self.GetObj(insertAfterID)
        if not o:
            s = self.GetMaxSort()+10
        else:
            s = o.meta["pool_sort"] + 1
        data["pool_sort"] = s
        return


    def GetSort(self):
        """ default sort field for subobjects """
        return u"pool_sort"

    
    def GetSortElements(self, selection=None):
        """ returns the contents as sorted list """
        if selection=="pages":
            return self.GetPages()
        if selection=="elements":
            return self.GetPageElements()
        return self.GetObjs()
        

    def GetMaxSort(self):
        """ returns the maximum sort number """
        parameter={u"pool_unitref": self.GetID()}
        operators={u"pool_unitref": u"="}
        fields=[u"-max(pool_sort)"]
        root = self.root()
        parameter,operators = root.ObjQueryRestraints(self, parameter, operators)
        r = root.Select(parameter=parameter, fields=fields, operators=operators, sort=u"", max=1)
        if len(r):
            s = r[0][0]
            if s==None:
                s=0
            return s
        return 0


    def UpdateSort(self, objs, user):
        """    update pool_sort values according to list """
        if not objs:
            return False, _(u"List is empty")
        if type(objs) in (StringType, UnicodeType):
            objs = ConvertToNumberList(objs)
        ids = []
        for oi in objs:
            if type(oi) in (StringType, UnicodeType, IntType, LongType):
                ids.append(int(oi)) 
        if ids:
            objs2 = self.GetObjsBatch(ids)
        pos = 10
        for obj in objs:
            if type(obj) in (StringType, UnicodeType, IntType, LongType):
                for o in objs2:
                    if o.id == int(obj):
                        obj = o
                        break
            if type(obj) in (StringType, UnicodeType, IntType, LongType):
                continue
            obj.meta.set("pool_sort", pos)
            obj.Commit(user)
            pos += 10
        return True, _(u"OK")
        
        
    def InsertAtPosition(self, id, position, user, selection=None):
        """ position = 'first', 'last' or numer """
        if position == u"last":
            return self.MoveEnd(id)
        elif position == u"first":
            return self.MoveStart(id)
        try:
            position = int(position)
        except:
            position = 0
        if position == 0 or position == self.GetID():
            return self.MoveEnd(id)
        id=int(id)
        order = []
        objs = self.GetSortElements(selection)
        pos = 0
        for obj in objs:
            if position == pos:
                order.append(id)
            order.append(obj)
            pos += 1
        ok, msgs = self.UpdateSort(order, user=user)
        return ok, msgs


    def InsertBefore(self, id, newID, user, selection=None):
        """ insert newID after unitID """
        id=int(id)
        order = []
        objs = self.GetSortElements(selection)
        for obj in objs:
            if id == obj.id:
                order.append(newID)
            order.append(obj)
        ok, msgs = self.UpdateSort(order, user=user)
        return ok, msgs


    def InsertAfter(self, id, newID, user, selection=None):
        """ insert newID after unitID """
        id=int(id)
        order = []
        objs = self.GetSortElements(selection)
        for obj in objs:
            order.append(obj)
            if id == obj.id:
                order.append(newID)
        ok, msgs = self.UpdateSort(order, user=user)
        return ok, msgs


    def MoveUp(self, id, user, selection=None):
        """ move one position up in container """
        objs = self.GetSortElements(selection)
        order = []
        id=int(id)
        pos = 0
        for obj in objs:
            if obj.id == id:
                if len(order)==0:
                    return True, []
                order.insert(len(order)-1, obj)
            else:
                order.append(obj)
            
        ok, msgs = self.UpdateSort(order, user=user)
        return ok, msgs


    def MoveDown(self, id, user, selection=None):
        """ move one position down in container """
        objs = self.GetSortElements(selection)
        order = []
        id=int(id)
        insertID = None
        for obj in objs:
            if obj.id == id:
                insertID = obj
            else:
                order.append(obj)
                if insertID:
                    order.append(insertID)
                    insertID = None
        if insertID:
            order.append(insertID)
        ok, msgs = self.UpdateSort(order, user=user)
        return ok, msgs
    
    
    def MoveStart(self, id, user, selection=None):
        """ move to top in container """
        objs = self.GetSortElements(selection)
        id=int(id)
        order = [id]
        for obj in objs:
            if id == obj.id:
                order[1:].insert(0, obj)
            else:
                order.append(obj)
        ok, msgs = self.UpdateSort(order, user=user)
        return ok, msgs
    
    
    def MoveEnd(self, id, user, selection=None):
        """ move to bottom in container """
        objs = self.GetSortElements(selection)
        id=int(id)
        lastObj = None
        order = []
        for obj in objs:
            if id == obj.id:
                lastObj = obj
            else:
                order.append(obj)
        if lastObj:
            order.append(lastObj)
        else:
            order.append(id)
        ok, msgs = self.UpdateSort(order, user=user)
        return ok, msgs



class SortView:
    """
    View functions for sorting objects
    """

    def sortpages(self):
        """
        display the sortview and editor
        """
        result = {u"msgs": [], u"content":"", u"cmsview": self, u"result": False, u"sortelements":[]}
        ids = self.GetFormValue(u"ids")
        sort = self.GetFormValue(u"sort")
        if sort != u"1":
            result[u"sortelements"] = self.context.GetSortElements("pages")
            return result
        ids = ConvertToNumberList(ids)
        if not ids:
            result[u"sortelements"] = self.context.GetSortElements("pages")
            result[u"msgs"] = [_(u"Nothing to sort.")]
            return result
        user = self.User()
        ok, msgs = self.context.UpdateSort(ids, user=user)
        result[u"msgs"] = msgs
        result[u"result"] = ok
        result[u"sortelements"] = self.context.GetSortElements("pages")
        return result


    def sortelements(self):
        """
        display the sortview and editor
        """
        result = {u"msgs": [], u"content":u"", u"cmsview": self, u"result": False, u"sortelements":[]}
        ids = self.GetFormValue(u"ids")
        sort = self.GetFormValue(u"sort")
        if sort != u"1":
            result[u"sortelements"] = self.context.GetSortElements("elements")
            return result
        ids = ConvertToNumberList(ids)
        if not ids:
            result[u"sortelements"] = self.context.GetSortElements("elements")
            result[u"msgs"] = [_(u"Nothing to sort.")]
            return result
        user = self.User()
        ok, msgs = self.context.UpdateSort(ids, user=user)
        result[u"msgs"] = msgs
        result[u"result"] = ok
        result[u"sortelements"] = self.context.GetSortElements("elements")
        return result


    def moveup(self):
        """
        move pageelement one position up in container
        redirect to request.url
        parameter: id, url in request
        """
        id = self.GetFormValue(u"id")
        ok, msgs = self.context.MoveUp(id, user= self.User())#, selection="elements")
        url = self.GetFormValue(u"url")
        if not url:
            url = self.PageUrl(self.context)
        return self.Redirect(url, [ok, msgs])


    def movedown(self):
        """
        move pageelement one position down in container
        redirect to request.url
        parameter: id, url in request
        """
        id = self.GetFormValue(u"id")
        ok, msgs = self.context.MoveDown(id, user=self.User())#, selection="elements")
        url = self.GetFormValue(u"url")
        if not url:
            url = self.PageUrl(self.context)
        return self.Redirect(url, [ok, msgs])

    
    def movetop(self):
        """
        move pageelement to top in container
        redirect to request.url
        parameter: id, url in request
        """
        id = self.GetFormValue(u"id")
        ok, msgs = self.context.MoveStart(id, user=self.User())#, selection="elements")
        url = self.GetFormValue(u"url")
        if not url:
            url = self.PageUrl(self.context)
        return self.Redirect(url, [ok, msgs])
    
    
    def movebottom(self):
        """
        move pageelement to bottom in container
        redirect to request.url
        parameter: id, url in request
        """
        id = self.GetFormValue(u"id")
        ok, msgs = self.context.MoveEnd(id, user=self.User())#, selection="elements")
        url = self.GetFormValue(u"url")
        if not url:
            url = self.PageUrl(self.context)
        return self.Redirect(url, [ok, msgs])



    