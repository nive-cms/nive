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

import string, sys, binascii, re, htmlentitydefs
from types import *
from mimetypes import guess_type, guess_extension
import os, stat, tempfile

from strings import DvString
from dateTime import DvDateTime
from path import DvPath


def ConvertToBool(inData, inExcept = False):
    try:
        return int(inData)
    except:
        if type(inData) in (StringType,UnicodeType):
            if string.lower(inData) in (u"true", u"yes", u"checked", u"ja"):
                return True
            if string.lower(inData) in (u"false", u"no", u"nein"):
                return False
        if inExcept:
            raise "Conversion failure - Convert data to bool", str(inData) + "    " + EXCP()
        return False

def ConvertToInt(inData, inExcept = False):
    try:
        return int(inData)
    except:
        if type(inData) in (StringType,UnicodeType):
            if string.lower(inData) == u"true" or string.lower(inData) == u"yes" or string.lower(inData) == u"checked":
                return 1
            if string.lower(inData) == u"false" or string.lower(inData) == u"no":
                return 0
        if inExcept:
            raise "Conversion failure - Convert data to integer", str(inData) + "    " + EXCP()
        return 0

def ConvertToFloat(inData, inExcept = False):
    try:
        return float(inData)
    except:
        if type(inData) in (StringType,UnicodeType):
            if string.lower(inData) == u"true" or string.lower(inData) == u"yes" or string.lower(inData) == u"checked":
                return 1.0
            if string.lower(inData) == u"false" or string.lower(inData) == u"no":
                return 0.0
        if inExcept:
            raise "Conversion failure - Convert data to float", str(inData) + "    " + EXCP()
        return 0

def ConvertToLong(inData, inExcept = False):
    try:
        if type(inData) == LongType:
            return inData
        if  type(inData) == IntType:
            return long(inData)
        return string.atol(inData)
    except:
        if type(inData) in (StringType,UnicodeType):
            if string.lower(inData) == u"true" or string.lower(inData) == u"yes" or string.lower(inData) == u"checked":
                return 1
            if string.lower(inData) == u"false" or string.lower(inData) == u"no":
                return 0
        if inExcept:
            raise "Conversion failure - Convert data to long", str(inData) + "    " + EXCP()
        return 0

def ConvertToTuple(inData, inExcept = False):
    try:
        return tuple(inData)
    except:
        if inExcept:
            raise "Conversion failure - Convert data to tuple", str(inData) + "    " + EXCP()
        return ()

def ConvertToList(inData, inExcept = False):
    try:
        if not inData:
            return []
        return DvString(str(inData)).ConvertToList()
    except:
        if inExcept:
            raise "Conversion failure - Convert data to list", str(inData) + "    " + EXCP()
        return []

def ConvertToNumberList(inData, inExcept = False):
    try:
        l = DvString(str(inData)).ConvertToList()
        for i in range(len(l)):
            l[i] = ConvertToLong(l[i], inExcept)
        return l
    except:
        if inExcept:
            raise "Conversion failure - Convert data to number list", str(inData) + "    " + EXCP()
        return []

def ConvertToDict(inData, inExcept = False):
    try:
        return DvString(inData).ConvertToDict()
    except:
        if inExcept:
            raise "Conversion failure - Convert data to dictionary", str(inData) + "    " + EXCP()
        return {}

def ConvertKeyList(inData, inSep = u",", inExcept = False):
    try:
        return DvString(inData).ConvertKeyListToDict(inSep)
    except:
        if inExcept:
            raise "Conversion failure - Convert data to dictionary", str(inData) + "    " + EXCP()
        return {}

def ConvertToType(inData, inType):
    if inType == "string" or inType == "str":
        if type(inData) in (StringType,UnicodeType):
            return inData
        return str(inData)
    elif inType == "int":
        return ConvertToInt(inData)
    elif inType in ("long", "unit", "number", "codelist"):
        return ConvertToLong(inData)
    elif inType == "float":
        return ConvertToFloat(inData)
    elif inType == "bool":
        return ConvertToBool(inData)
    elif inType == "date":
        if inData == "":
            return null
        if inData == "NOW":
            aD = DvDateTime()
            aD.Now()
            return aD
        if str(inData.__class__).find("DvDateTime") != -1:
            return inData
        aD = DvDateTime(inData)
        return aD
    elif inType == "datetime":
        if inData == "":
            return null
        if inData == "NOW":
            aD = DvDateTime()
            aD.Now()
            return aD
        if str(inData.__class__).find("DvDateTime") != -1:
            return inData
        aD = DvDateTime(inData)
        return aD
    elif inType == "dict":
        return ConvertToDict(inData)
    elif inType in ("list",):
        return ConvertToList(inData)
    elif inType in ("mselection", "unitlist", "mcodelist", "radio", "mcheckboxes"):
        if type(inData) == ListType or type(inData) == TupleType:
            return inData
        return DvString(unicode(inData)).ConvertToList()
    if type(inData) in (StringType,UnicodeType):
        return inData
    return str(inData)


def ConvertToStr(inData, inType=None):
    if not inType:
        if type(inData) in (ListType,TupleType):
            return ConvertListToStr(inData)
        elif type(inData) == DictType:
            return ConvertDictToStr(inData)
    if inType == "date":
        if inData == "NOW":
            aD = DvDateTime()
            aD.Now()
            return aD.GetDDMMYYYY()
        aD = DvDateTime(str(inData))
        return aD.GetDDMMYYYY()
    elif inType == "datetime":
        if inData == "NOW":
            aD = DvDateTime()
            aD.Now()
            return aD.GetDDMMYYYYHHMMSS()
        aD = DvDateTime(str(inData))
        return aD.GetDDMMYYYYHHMMSS()
    elif inType == "list":
        return ConvertListToStr(inData)
    return str(inData)



def ConvertListToStr(inList, inSep = u", ", inTextMarker = u"", keepType = False):
    """(inList) return string
    converts a python list to string. .
    the list items are seperated by ",". list items are converted to string
    """
    aStr = ""
    if not inList:
        return aStr
    if type(inList) == StringType:
        return inTextMarker + inList + inTextMarker
    for aI in inList:
        if len(aStr) > 0:
            aStr += inSep
        if inTextMarker != u"":
            if keepType:
                if type(aI) in (IntType, LongType, FloatType):
                    inTextMarker = u""
            aStr += inTextMarker + str(aI) + inTextMarker
        else:
            aStr += str(aI)
    return aStr


def ConvertDictToStr(inDict, inSep = u", "):
    """(inList) return string
    converts a python dictionary to key list string. .
    the list items are seperated by ",". list items are converted to string
    key=value,
    """
    aStr = u""
    for aK in inDict.keys():
        if len(aStr) > 0:
            aStr += inSep
        aStr += u"%s=%s" % (aK, str(inDict[aK]))
    return aStr


def ConvertListToDict(inList, inDictFields):
    """(list inList, list inDictFields) return dict
    """
    if(len(inList) != len(inDictFields)):
        return {}
    aDict = {}
    aCnt = 0
    for aI in inList:
        aDict[inDictFields[aCnt]] = aI
        aCnt += 1
    return aDict


def ConvertDictListToTuple(inList):
    """
    converts [{"id":"first","name":"Name"},...] to [("first","First"),...]
    """
    l=[]
    for d in inList:
        l.append((unicode(d["id"]),d["name"]))
    return l


def ConvertHexToBin(m):
    """
    """
    return u''.join(map(lambda x: chr(16*int(u'0x%s'%m[x*2],0)+int(u'0x%s'%m[x*2+1],0)),range(len(m)/2)))


def ConvertBinToHex(m):
    """
    """
    return u''.join(map(lambda x: hex(ord(x)/16)[-1]+hex(ord(x)%16)[-1],m))


def ConvertHTMLToText(html, url="", removeReST=True):
    try:
        import html2text
        #text = html2text.html2text(html, url)
        h = html2text.HTML2Text()
        h.ignore_links = True
        if removeReST:
            h.ignore_emphasis = True
        return h.handle(html)
    except:
        return html


def ConvertTextToHTML(html):
    return html.replace(u"\n", u"\n<br/>")


def XssEscape(html, permitted_tags=None, requires_no_close=None, allowed_attributes=None):
    """
    http://code.activestate.com/recipes/496942-cross-site-scripting-xss-defense/
    
    A list of the only tags allowed.  Be careful adding to this.  Adding
    "script," for example, would not be smart.  'img' is out by default 
    because of the danger of IMG embedded commands, and/or web bugs.
    permitted_tags = ['a', 'b', 'blockquote', 'br', 'i', 
                      'li', 'ol', 'ul', 'p', 'cite', 'strong', 'em', 'pre', 'h3', 'h4']

    A list of tags that require no closing tag.
    requires_no_close = ['img', 'br']

    A dictionary showing the only attributes allowed for particular tags.
    If a tag is not listed here, it is allowed no attributes.  Adding
    "on" tags, like "onhover," would not be smart.  Also be very careful
    of "background" and "style."
    allowed_attributes = \
            {'a':['href','title'],
             'img':['src','alt'],
             'blockquote':['type']}
    """
    import xssescape
    xss = xssescape.XssCleaner()
    if permitted_tags:
        xss.permitted_tags = permitted_tags
    if requires_no_close:
        xss.requires_no_close = requires_no_close
    if allowed_attributes:
        xss.allowed_attributes = allowed_attributes
    return xss.strip(html)


def ConvertToPyFile(data, codepage="utf-8", header=""):
    """
    data = dictionary. keys are converted to variables, lists and dictionaries are included in valid 
    python syntax
    """
    file = "# -*- coding: %s -*-\r\n" % (codepage)
    file += '"""\r\n'
    file += header
    file += '\r\n"""\r\n\r\n'
    for k in data.keys():
        value = data[k]
        t = type(value)
        
        # convert types to string
        if t in (LongType, IntType, FloatType):
            value = str(value)
        
        elif t in (StringType, UnicodeType):
            if t == StringType:
                value = unicode(value, codepage)
            if value.find(u'"')==-1 and value.find(u'\n')==-1:
                value = u'u"'+value+u'"'
            elif value.find(u"'")==-1 and value.find(u'\n')==-1:
                value = u"u'"+value+u"'"
            elif value.find(u'"""')==-1:
                value = u'u"""'+value+u'"""'
            else:
                raise TypeError, "Found long comment in string."
            
        elif t == ListType:
            if len(value)>1:
                value2 = u""
                value2 += u"["
                for li in value:
                    value2 += str(li)+u",\r\n\t\t"
                value2 += u"]"
                value = value2
            else:
                value = unicode(str(value), codepage)

        elif t == TupleType:
            if len(value)>1:
                value2 = u""
                value2 += u"("
                for li in value:
                    value2 += str(li)+u",\r\n\t\t"
                value2 += u")"
                value = value2
            else:
                value = unicode(str(value), codepage)

        elif t == DictType:
            value = unicode(str(value), codepage)

        elif t == InstanceType and str(value.__class__).find("DvDateTime") != -1:
            value = u'"'+unicode(value.GetDB())+u'"'
            
        file += u"%s = %s\r\n" % (k, value)
    return file


def CutText(text, textlen, cutchars=[" ", ",", ".", "\r"]):
    """
    For text preview. cut the text at the last found char in cutchars.
    """
    pos = len(text)-1
    for c in cutchars:
        p = text.find(c, textlen)
        if p!=-1 and p<pos:
            pos=p
    return text[:pos]    


def FormatBytesForDisplay(size):
    """Return the size of a file or directory formatted for display."""
    if size in (None,-1,0):
        return u""
    if size == 1:
        return u"1 byte"
    for factor, suffix in ((1<<30L, u"GB"),(1<<20L, u"MB"),(1<<10L, u"kB"),(1, u"bytes")):
        if size >= factor:
            break
    return u"%d %s" % (size / factor, suffix)

def FmtSeconds(seconds):
    # Format seconds for display
    #[$] seconds: seconds to convert
    if seconds is None: return '-' * 5
    if seconds == -1: return '-'

    minutesSingular = u'%d&nbsp;Minute '
    minutesPlural = u'%d&nbsp;Minuten '
    hoursSingular = u'%d&nbsp;Stunde '
    hoursPlural = u'%d&nbsp;Stunden '

    k = 60
    if (seconds > k):
        t2 = seconds / k
        if (t2 > k):
            t3 = t2 / k
            s = u""
            if t3 == 1:
                s += hoursSingular % t3
            else:
                s += hoursPlural % t3
            m = t2%k
            if m==1:
                s += minutesSingular % m
            else:
                s += minutesPlural % m
            return s
        else:
            if t2 == 1:
                return minutesSingular % t2
            return minutesPlural % t2
    else:
        return u'%d&nbsp;Sekunden' % seconds


def _SortDictListFunc(x, y, fld):
    if type(x.get(fld)) == StringType and type(y.get(fld)) == StringType:
        return cmp(string.lower(x.get(fld)), string.lower(y.get(fld)))
    return cmp(x.get(fld), y.get(fld))


def SortDictList(ioList, inFld, inSort = ">"):
    """Sorts the dict list.
    inSort = > or <
    """
    if type(ioList) == TupleType:
        return ioList
    ioList.sort(lambda x, y, fld = inFld: _SortDictListFunc(x, y, fld))
    if inSort == "<":
        ioList.reverse()
    return ioList


def GetDL(li, key, default=None):
    """
    """
    if type(li)==DictType:
        return li.get(key, default)
    for l in li:
        if l["id"] == key:
            return l["name"]
    return default

def GetDLItem(li, key):
    """
    """
    for l in li:
        if l["id"] == key:
            return l
    return None


def GetMimeTypeExtension(inExt):
    if inExt.find(".") != -1:
        inExt = DvPath(inExt).GetExtension()
    # custom and uncommeon
    if inExt == u"fla":        return u"application/flash"
    # standard
    elif inExt == u"html":        return u"text/html"
    elif inExt == u"txt":        return u"text/plain"
    elif inExt == u"dtml":        return u"text/html"
    elif inExt == u"jpg":        return u"image/jpeg"
    elif inExt == u"gif":        return u"image/gif"
    elif inExt == u"png":        return u"image/png"
    elif inExt == u"jpeg":        return u"image/jpeg"
    elif inExt == u"psd":        return u"image/psd"
    elif inExt == u"pdf":        return u"application/pdf"
    elif inExt == u"swf":        return u"application/x-shockwave-flash"
    elif inExt == u"flv":        return u"application/x-shockwave-flash"
    elif inExt == u"dcr":        return u"application/x-director"
    elif inExt == u"doc":        return u"application/msword"
    elif inExt == u"xls":        return u"application/vnd.ms-excel"
    elif inExt == u"ppt":        return u"application/vnd.ms-powerpoint"
    elif inExt == u"mpp":        return u"application/vnd.ms-project"
    elif inExt == u"rtf":        return u"text/rtf"
    elif inExt == u"dat":        return u"application/octet-stream"
    elif inExt == u"flv":        return u"video/flv"
    elif inExt == u"ogv":        return u"video/ogg"
    elif inExt == u"webm":        return u"video/webm"
    elif inExt == u"mp4":        return u"video/mp4"
    elif inExt == u"mp3":        return u"audio/mp3"
    elif inExt == u"ogg":        return u"audio/ogg"
    e = guess_type(u"x." + inExt)
    if e[0]:                return e[0]
    return u""

def GetExtensionMimeType(inMime):
    # custom and uncommeon
    if inMime == u"application/flash":        return u"fla"
    # standard
    elif inMime == u"text/html":        return u"html"
    elif inMime == u"text/plain":        return u"txt"
    elif inMime == u"text/html":        return u"dtml"
    elif inMime == u"image/jpeg":        return u"jpg"
    elif inMime == u"image/gif":        return u"gif"
    elif inMime == u"image/png":        return u"png"
    elif inMime == u"image/jpeg":        return u"jpeg"
    elif inMime == u"image/psd":        return u"psd"
    elif inMime == u"application/pdf":                    return u"pdf"
    elif inMime == u"application/x-shockwave-flash":    return u"swf"
    elif inMime == u"application/x-director":            return u"dcr"
    elif inMime == u"application/msword":                return u"doc"
    elif inMime == u"application/vnd.ms-excel":        return u"xls"
    elif inMime == u"application/vnd.ms-word":            return u"doc"
    elif inMime == u"application/vnd.ms-powerpoint":    return u"ppt"
    elif inMime == u"application/vnd.ms-project":        return u"mpp"
    elif inMime == u"text/rtf":                        return u"rtf"
    elif inMime == u"application/octet-stream":        return u"dat"
    elif inMime == u"video/flv":        return u"flv"
    elif inMime == u"video/ogg":        return u"ogv"
    elif inMime == u"video/webm":        return u"webm"
    elif inMime == u"video/mp4":        return u"mp4"
    elif inMime == u"audio/mp3":        return u"mp3"
    elif inMime == u"audio/ogg":        return u"ogg"

    m = guess_extension(inMime)
    if m:                            return m[1:]
    return u""



def TidyHtml(data, options=None):
    """
    clean up html by calling tidy
    """
    if not options:
        options = { 'output-xhtml'       : '1',
                    'add-xml-decl'       : '1',
                    'indent'             : 'auto',
                    'tidy-mark'          : '0',
                    'char-encoding'      : 'utf8',
                    'clean'              : '0',
                    'drop-font-tags'     : '1',
                    'enclose-block-text' : '0',
                    'logical-emphasis'   : '1',
                    'word-2000'          : '1',
                    'wrap'               : '65',
                    'write-back'         : '0'}

    cmds = ""
    for k in options.keys():
        cmds += " --"+k+" "+options[k]

    # write file
    file, filename = tempfile.mkstemp(suffix='.html', prefix='tidy')
    os.write(file, data)
    os.close(file)

    # call tidy
    out = filename + "_tidy"
    cmd = """%(cmds)s -o %(out)s %(file)s""" %{"cmds": cmds, "out": out, "file": filename}

    s = os.popen("tidy " + cmd, "r")
    r = ""
    while 1:
        d = s.readline()
        if not d or d == ".\n" or d == ".\r":
            break
        r += d

    # delete file
    try:
        os.remove(filename)
    except:
        pass

    # return output
    try:
        file = open(out, "r+b")
        data2 = file.read()
        file.close()
        os.remove(out)
    except:
        return data
    return data2


def ReplaceHTMLEntities(text, codepage = None):
    ##
    # Removes HTML or XML character references and entities from a text string.
    #
    # @param text The HTML (or XML) source text.
    # @return The plain text, as a Unicode string, if necessary.
    def _fixup(m):
        text = m.group(0)
        if text[:2] == u"&#":
            # character reference
            try:
                if text[:3] == u"&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is

    if codepage:
        text = unicode(text, codepage)
    result = re.sub(u"&#?\w+;", _fixup, text)
    if codepage:
        result = result.encode(codepage)
    return result



# Logging --------------------------------------------------------------------------


def ASSERT(inCondition, inMsg=""):
    if not inCondition:
        if inMsg=="":
            inMsg = "False"
        raise "ASSERT", inMsg
        
def BREAK(inParam):
    raise "BREAK", inParam


def EXCP():
    import sys, traceback, string
    type, val, tb = sys.exc_info()
    return string.join(traceback.format_exception(type, val, tb), "")


def EXCP_HTML():
    import sys, traceback, string
    type, val, tb = sys.exc_info()
    s = "<pre>"
    s += string.join(traceback.format_exception(type, val, tb), "")
    s += "</pre>"
    return s
    
    
def DUMP(inData, inPath = "dump.txt", addTime=False):
    from nive.utils.strings import DvString
    if addTime:
        from nive.utils.dateTime import DvDateTime
        aD = DvDateTime()
        aD.Now()
        aS = DvString("\r\n\r\n" + aD.GetHHMMSSDDMMYYYY() + "\r\n" + str(inData))
    else:
        aS = DvString("\r\n\r\n" + str(inData))
    aS.WriteToFile(inPath, True)


# Benchmark -----------------------------------------------------------

def START():
    import time
    return time.time()
    
def STACK(t=0, label = "", limit = 15):
    import time
    import traceback
    n = time.time() - t
    print label, n, traceback.print_stack(limit=limit)

def STACKF(t=0, label = "", limit = 15, path = "_stackf.txt", name=""):
    import time
    import traceback
    n = time.time() - t
    from nive.utils.dateTime import DvDateTime
    aD = DvDateTime()
    aD.Now()
    h = "%s: %f (%s)" % (aD.GetHHMMSSDDMMYYYY(),n,name)
    if limit<2:
        DUMP("%s\r\n%s\r\n" % (h, label), path)
        return
    import StringIO
    s = StringIO.StringIO()
    traceback.print_stack(limit=limit, file=s)
    DUMP("%s\r\n%s\r\n%s" % (h, label, s.getvalue()), path)

def MARK(t, label = ""):
    import time
    n = time.time() - t
    print label, n

def LOG(data = "", path="/work/instances/nive/_log.txt", t=0):
    import time
    n = time.time() - t
    try:
        fd = open(path, "ab+")
        fd.write("%f %s\r\n" % (n, data))
        fd.close()
    except:
        try:
            fd.close()
        except:
            pass



class logdata:
    _data = ""
    _maxsize = 1024 * 512
    _path = ""
    
    def __del__(self):
        self.write("", 1)

    def write(self, data="", flush=0):
        import thread
        if flush or len(self._data)>self._maxsize:
            try:
                lock = thread.allocate_lock()
                lock.acquire(1)
                fd = open(self._path, "ab+")
                fd.write(self._data + data)
                self._data = ""
                fd.close()
                if lock.locked():
                    lock.release()
                return True
            except:
                try:
                    fd.close()
                except:
                    pass
                try:
                    if lock.locked():
                        lock.release()
                except:
                    pass
                return False
        else:
            try:
                lock = thread.allocate_lock()
                lock.acquire(1)
                self._data += data
                if lock.locked():
                    lock.release()
                return True
            except:
                return False

# global log
_log = None

def LOGHTTP(client="-", user="-", t=0, action="GET", url="-", state="200", referrer="-", agent="-", path="http.log", logObj=None):
    import time
    if t != 0:
        t = time.localtime(t)
    else:
        t = time.localtime()
    t = time.strftime(u"[%d/%m/%Y:%H:%M:%S", t)
    ms = ("%f"%(time.time())).split(".")[-1]
    t += ".%s]"%(ms)
    referrer = referrer.replace('"', '')
    agent = agent.replace('"', '')
    log = u"""%s - "%s" %s "%s %s" %s - "%s" "%s"\r\n""" % (client, user, t, action, url, str(state), referrer, agent)
    if not logObj:
        logObj = _log
    if not logObj:
        logObj = logdata()
        logObj._path = path
    return logObj.write(log)
    
