 # -*- coding: utf-8 -*-
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

__doc__ = ""


import re

from string import *


# /////////////////////////////////////////////////////////////////////////////
# // DvString

class DvString:
    """String class (not static)"""

    def __init__(self, str = u""):
        self._pStr = u""
        if str:
            self._pStr = str

    def __str__(self):
        return self._pStr

    def __len__(self):
        return len(self._pStr)

    def Int(self):
        """
        convert string to int
        """
        try:
            return atoi(self._pStr)
        except:
            if self._pStr:
                if lower(self._pStr) == u"true" or lower(self._pStr) == u"yes" or lower(self._pStr) == u"checked":
                    return 1
                if lower(self._pStr) == u"false" or lower(self._pStr) == u"no":
                    return 0
        return 0

    def Set(self, str):
        if str:
            self._pStr = str

    def Get(self):
        return self._pStr

    def IsEmpty(self):
        return self._pStr == u""


    def Find(self, subStr, startPos = 0):
        """(string, int) return integer
        """
        return find(self._pStr, subStr, startPos)


    def FindCnt(self, subStr, startPos = 0):
        """(string, int) return integer
        """
        aCnt = -1
        aPos = startPos
        while(aPos > -1):
            aCnt += 1
            aPos = find(self._pStr, subStr, aPos + 1)
        return aCnt


    def Insert(self, insStr, position = 0):
        """(string, int) return void
        Inserts insStr at position.
        """
        s1 = self._pStr[:position]
        s2 = self._pStr[position:]
        self._pStr = s1 + insStr + s2


    def Replace(self, subStr, replaceStr):
        """(string, string) return bool
        Replaces string 'subStr' with 'replaceStr'.
        """
        if self._pStr == u"" or subStr == u"":
            return False
        if find(self._pStr, subStr) == -1:
            return False
        self._pStr = replace(self._pStr, subStr, replaceStr)
        return True


    def ReplaceNoCase(self, subStr, replaceStr):
        """(string, string) return bool
        Replaces string 'subStr' with 'replaceStr'.
        """
        # get lower copy
        aS = lower(self._pStr)
        aPos = find(aS, lower(subStr))
        if aPos == -1:
            return False
        aS = self._pStr[0:aPos] + replaceStr + self._pStr[aPos + len(subStr):]
        self._pStr = aS
        return True


    def ReplaceFromTo(self, fromSubStr, toSubStr, replaceStr, replaceFromTo):
        """(string, string, string, bool) return void
        Replaces string between 'fromSubStr' and 'toSubStr' with 'replaceStr'.
        'replaceFromTo' = True to replace from/to str also
        """
        aFrom = find(self._pStr, fromSubStr)
        if aFrom == -1:
            aFrom = 0
        elif not replaceFromTo:
            aFrom += len(fromSubStr)
        aStr = self._pStr[0:aFrom]
        aStr += replaceStr
        aTo = find(self._pStr, toSubStr, aFrom)
        if aTo == -1:
            aTo = len(self._pStr)
        elif replaceFromTo:
            aTo += len(toSubStr)
        aStr += self._pStr[aTo:]
        self._pStr = aStr


    def ReplaceFromToReverse(self, fromSubStr, toSubStr, replaceStr, replaceFromTo):
        """(string, string, string, bool) return void
        Replaces string between reverse 'fromSubStr' and 'toSubStr' with 'replaceStr'.
        'replaceFromTo' = True to replace from/to str also
        """
        aFrom = rfind(self._pStr, fromSubStr)
        if aFrom == -1:
            aFrom = 0
        elif not replaceFromTo:
            aFrom += len(fromSubStr)
        aStr = self._pStr[0:aFrom]
        aStr += replaceStr
        aTo = rfind(self._pStr, toSubStr)
        if aTo == -1:
            aTo = len(self._pStr)
        elif replaceFromTo:
            aTo += len(toSubStr)
        aStr += self._pStr[aTo:]
        self._pStr = aStr


    def ReplaceNoCase(self, subStr, replaceStr):
        """(string, string) return bool
        Replaces string 'subStr' with 'replaceStr'.
        """
        # get lower copy
        aS = lower(self._pStr)
        aPos = find(aS, lower(subStr))
        if aPos == -1:
            return False
        aS = self._pStr[0:aPos] + replaceStr + self._pStr[aPos + len(subStr):]
        self._pStr = aS
        return True


    def ReplaceContext(self, subStr, replaceStr, skipContextLike = u"\W"):
        """(string, string, string) return bool
        Replaces string 'subStr' with 'replaceStr' if next char or
        previous char in text in skipContextNotLike.
        """
        if self._pStr == "" or subStr == "":
            return False

        aRe = re.compile(skipContextLike + subStr + skipContextLike, re.IGNORECASE)
        aMatch = aRe.findall(self._pStr)

        # loop to check context
        while len(aMatch):
            aSub = aMatch[0]
            aRep = aSub[0] + replaceStr + aSub[len(aSub) - 1]
            self._pStr = replace(self._pStr, aSub, aRep)
            del aMatch[0]
        return True


    def LeftStr(self, toStr):
        """(string toStr) return string
        return string left of toStr. toStr is not included
        """
        aPos = find(self._pStr, toStr)
        if aPos == -1:
            aPos = len(self._pStr)
        return self._pStr[:aPos]


    def RightStr(self, fromStr):
        """(string fromStr) return string
        return string right of fromStr. fromStr is not included
        """
        aPos = find(self._pStr, fromStr)
        if aPos == -1:
            aPos = 0
        else:
            aPos += len(fromStr)
        return self._pStr[aPos:]


    def MidStr(self, fromSubStr, toSubStr, includeFromTo = True):
        """(string, string, bool) return string
        returns string between 'fromSubStr' and 'toSubStr'.
        'includeFromTo' = True to include from/to str also
        """
        aFrom = find(self._pStr, fromSubStr)
        if aFrom == -1:
            return ""
        elif not includeFromTo:
            aFrom += len(fromSubStr)
        aTo = find(self._pStr, toSubStr, aFrom)
        if aTo == -1:
            aTo = len(self._pStr)
        elif includeFromTo:
            aTo += len(toSubStr)
        return self._pStr[aFrom : aTo]


    def LeftStrEnd(self, toStr):
        """(string toStr) return string
        return string left of last occurence of toStr. toStr is not included
        """
        aPos = rfind(self._pStr, toStr)
        if aPos == -1:
            aPos = len(self._pStr)
        return self._pStr[0:aPos]


    def RightStrEnd(self, fromStr):
        """(string fromStr) return string
        return string right of last occurence of fromStr. fromStr is not included
        """
        aPos = rfind(self._pStr, fromStr)
        if aPos == -1:
            aPos = 0
        else:
            aPos += len(fromStr)
        return self._pStr[aPos:]


    def AsciiLowercase(self, additionalchars = u"0123456789_."):
        """return string
        removes all non lowercase ascii chars + (0123456789_.) and returns result
        """
        return filter(lambda x: x in string.ascii_lowercase + additionalchars, s.lower())


    def SplitToDict(self, dictFlds, sepChar):
        """(stringList dictFlds, string sepChar) return dictionary
        returns dictionary with with dictFlds and strings between sepchar pairs
        """
        aDict = {}
        if not self._pStr:
            return aDict
        aL = split(self._pStr, sepChar)
        for i in range(0, len(dictFlds)):
            if i >= len(aL):
                break
            aDict[dictFlds[i]] = aL[i]
        return aDict


    def CopyFromDict(self, dict, seqList, sepChar):
        """(dictionary dict, list seqList, string sepChar) return void
        creates string from dictionary values ordered by sequenz seqList and seperated
        by sepChar
        """
        aL = []
        for aFld in seqList:
            aL.append(str(dict[aFld]))
        self._pStr = join(aL, sepChar)


    def ConvertToList(self):
        """() return list
        converts a string to list.
        the list items can be seperated by "," or "\n"
        """
        aList = []
        if not self._pStr:
            return aList

        aStr = self._TrimInternal(self._pStr)
        if not len(aStr):
            return aList
        if aStr[0] == u"[" or aStr[0] ==u"(":
            aStr = aStr[1:-1]

        aSep = u","
        if find(self._pStr, u"\n") != -1:
            aSep = u"\n"

        aL = split(aStr, aSep)
        for aStr in aL:
            aDat = self._TrimInternal(aStr)
            if(len(aDat) == 0):
                continue
            if aDat[0] == u"'" or aDat[0] == u"\"":
                aDat = aDat[1:-1]
            aList.append(aDat)
        return aList


    def ConvertToNumberList(self):
        """() return list
        converts a string to list. numbers are converted to long.
        the list items can be seperated by "," or "\n"
        """
        aList = []
        if not self._pStr or self._pStr == u"":
            return aList

        aStr = self._TrimInternal(self._pStr)
        if len(aStr) == 0:
            return aList
        if aStr[0] == u"[" or aStr[0] ==u"(":
            aStr = aStr[1:-1]

        aSep = u","
        if find(self._pStr, u"\n") != -1:
            aSep = u"\n"

        aL = split(aStr, aSep)
        for aStr in aL:
            aDat = self._TrimInternal(aStr)
            if(len(aDat) == 0):
                continue
            if aDat[0] == u"'" or aDat[0] == u"\"":
                aDat = aDat[1:-1]
            try:    aList.append(long(aDat))
            except: pass
        return aList


    def ConvertToDict(self):
        """() return dict
        creates a dict from str.
        src string = "{"field1":"data1",...}
        supported data types : string ,long
        """
        if(self._pStr == u""):
            return {}
        return self._ConvertToDictInternal(self._pStr)


    def ConvertKeyListToDict(self, inSep = u","):
        """() return dict
        creates a dict from str.
        src string = "field1=data,field2=data"...
        filed data pairs can be seperated by , or line break
        supported data types : string, long
        """
        aDict = {}
        if(self._pStr == u""):
            return aDict

        # if
        if find(self._pStr, u"\n") != -1:
            aL = split(self._pStr, u"\n")
        else:
            aL = split(self._pStr, inSep)
        for aStr in aL:
            aL2 = split(aStr, u"=")
            if(len(aL2) != 2):
                continue
            aDat = self._TrimInternal(aL2[1])
            if(len(aDat)):
                if aDat[-1] == "'" or aDat == "\"":
                    aDat = aDat[1:-1]
            #else:
            #    aDat = DvUtil.ConvertToLong(aDat)
            aKey = self._TrimInternal(aL2[0])
            if(aKey[-1] == u"'" or aDat == u"\""):
                aKey = aKey[1:-1]
            aDict[aKey] = aDat
        return aDict


    def ConvertKeyListToDictList(self, inSep = u","):
        """() return list
        creates a list with dictionaries {"id": ..., "name": ...} from str.
        src string = "field1=data,field2=data"...
        filed data pairs can be seperated by , or line break
        supported data types : string, long
        """
        aList = []
        if(self._pStr == u""):
            return aList

        # if
        if find(self._pStr, u"\n") != -1:
            aL = split(self._pStr, u"\n")
        else:
            aL = split(self._pStr, inSep)
        for aStr in aL:
            aL2 = split(aStr, u"=")
            if(len(aL2) != 2):
                continue
            aDat = self._TrimInternal(aL2[1])
            if(len(aDat)):
                if aDat[-1] == u"'" or aDat == u"\"":
                    aDat = aDat[1:-1]
            #else:
            #    aDat = DvUtil.ConvertToLong(aDat)
            aKey = self._TrimInternal(aL2[0])
            if(aKey[-1] == u"'" or aDat == u"\""):
                aKey = aKey[1:-1]
            aList.append({"id": aKey, "name": aDat})
        return aList


    def Trim(self):
        """() return void
        Trim Whitespace and CRLF and Tab from Start and End
        """
        self._pStr = self._TrimInternal(self._pStr)


    def TrimChars(self, inChars):
        """() return void
        Trim every char in inChars list
        """
        aStr = self._pStr
        while(len(aStr) > 0):
            aSkip = True
            for aC in inChars:
                if(aStr[0] == aC):
                    aStr = aStr[1:]
                    aSkip = False
                    break
            if aSkip:
                break
        while(len(aStr) > 0):
            aSkip = True
            for aC in inChars:
                if(aStr[-1] == aC):
                    aStr = aStr[:-1]
                    aSkip = False
                    break
            if aSkip:
                break
        self._pStr = aStr


    def LoadFromFile(self, inPath):
        """(string inPath) return bool
        """
        aF = open(inPath)
        if not aF:
            return False
        self._pStr = aF.read()
        aF.close()
        return True


    def WriteToFile(self, inPath, inAppend = False):
        """(string inPath, bool inAppend) return bool
        """
        if inAppend:
            file = open(inPath, "ab+")
            if not file:
                return False
        else:
            file = open(inPath, "wb")
            if not file:
                return False
        file.write(self._pStr)
        file.close()
        return True


    # ---------------------------------------------------------------------------------
    def _TrimInternal(self, inStr):
        while(len(inStr) > 0):
            if(inStr[0] == u" " or inStr[0] == u"\r" or inStr[0] == u"\n" or inStr[0] == u"\t"):
                inStr = inStr[1:]
            else:
                break
        while(len(inStr) > 0):
            if(inStr[-1] == u" " or inStr[-1] == u"\r" or inStr[-1] == u"\n" or inStr[-1] == u"\t"):
                inStr = inStr[:-1]
            else:
                break
        return inStr

    def _ConvertToDictInternal(self, inStr):
        aDict = {}

        aStr = self._TrimInternal(inStr)
        if not len(aStr):
            return aDict
        if aStr[0] == u"{":
            aStr = aStr[1:-1]

        aSplitChar = u","
        #if find(aStr, "\n") != -1:
        #    aSplitChar = "\n"

        aL = split(aStr, aSplitChar)
        for aStr in aL:
            aL2 = split(aStr, u":")
            if(len(aL2) != 2):
                continue
            aDat = self._TrimInternal(aL2[1])
            if aDat[0] == u"'" or aDat[0] == u"\"":
                aDat = aDat[1:-1]
            else:
                aDat = atol(aDat)   #DvUtil.ConvertToLong(aDat)
            aKey = self._TrimInternal(aL2[0])
            if(aKey[0] == u"'" or aKey[0] == u"\""):
                aKey = aKey[1:-1]
            aDict[aKey] = aDat
        return aDict


