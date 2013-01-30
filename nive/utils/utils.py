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

__doc__ = ""

import re, htmlentitydefs
import iso8601
import os, tempfile, json
from datetime import datetime
from mimetypes import guess_type, guess_extension
from operator import itemgetter, attrgetter
from types import StringType

from path import DvPath


def ConvertHTMLToText(html, url="", removeReST=True):
    # requires html2text module
    try:
        import html2text
    except ImportError:
        return html
    h = html2text.HTML2Text()
    h.ignore_links = True
    if removeReST:
        h.ignore_emphasis = True
        text = h.handle(html)
        # replace markdown #
        text = text.replace(u"# ","")
        return text
    return h.handle(html)


def ConvertTextToHTML(html):
    # replaces lines breaks with br's
    return html.replace(u"\n", u"\n<br/>")


def ConvertToDateTime(date):
    if isinstance(date, datetime):
        return date
    elif isinstance(date, float):
        return datetime.fromtimestamp(date)
    elif not date:
        return None
    try:
        return iso8601.parse_date(date)
    except (iso8601.ParseError, TypeError), e:
        pass
    # try other string format versions
    try: # 2011-12-23
        return datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        pass
    try: # 2011/12/23
        return datetime.strptime(date, "%Y/%m/%d")
    except ValueError:
        pass
    try: # 2011/12/23 13:22
        return datetime.strptime(date, "%Y/%m/%d %H:%M")
    except ValueError:
        pass
    try: # 2011/12/23 13:22:11
        return datetime.strptime(date, "%Y/%m/%d %H:%M:%S")
    except ValueError:
        pass



def XssEscape(html, permitted_tags=None, requires_no_close=None, allowed_attributes=None):
    """
    source: http://code.activestate.com/recipes/496942-cross-site-scripting-xss-defense/
    
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


def CutText(text, textlen, cutchars=" ;:,.\r\n", postfix=u" ..."):
    """
    For text preview. cut the text at the last found char in cutchars.
    """
    if len(text)<textlen:
        return text
    pos = len(text)-1
    for c in cutchars:
        p = text.find(c, textlen)
        if p!=-1 and p<pos:
            pos=p
    return text[:pos] + postfix


def ConvertHexToBin(m):
    return u''.join(map(lambda x: chr(16*int(u'0x%s'%m[x*2],0)+int(u'0x%s'%m[x*2+1],0)),range(len(m)/2)))

def ConvertBinToHex(m):
    return u''.join(map(lambda x: hex(ord(x)/16)[-1]+hex(ord(x)%16)[-1],m))


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

    minutesSingular = u'%d minute '
    minutesPlural = u'%d minutes '
    hoursSingular = u'%d hour '
    hoursPlural = u'%d hours '

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
        return u'%d seconds' % seconds


def SortConfigurationList(values, sort, ascending=True):
    """
    Sorts the dictionary list `values` by attribute or key `sort`. This works for definitions.Conf() objects 
    and simple dictionaries. 
    Results can be ordered ascending or descending.
    """
    if not sort:
        return values
    try:
        values = sorted(values, key=attrgetter(sort))   
    except AttributeError:
        values = sorted(values, key=itemgetter(sort))   
    if not ascending:
        values.reverse()
    return values


def GetMimeTypeExtension(extension):
    if extension.find(".") != -1:
        extension = DvPath(extension).GetExtension()
    # custom and uncommeon
    if extension == u"fla":          return u"application/flash"
    # standard
    elif extension == u"html":       return u"text/html"
    elif extension == u"txt":        return u"text/plain"
    elif extension == u"dtml":       return u"text/html"
    elif extension == u"jpg":        return u"image/jpeg"
    elif extension == u"gif":        return u"image/gif"
    elif extension == u"png":        return u"image/png"
    elif extension == u"jpeg":       return u"image/jpeg"
    elif extension == u"psd":        return u"image/psd"
    elif extension == u"pdf":        return u"application/pdf"
    elif extension == u"swf":        return u"application/x-shockwave-flash"
    elif extension == u"flv":        return u"application/x-shockwave-flash"
    elif extension == u"dcr":        return u"application/x-director"
    elif extension == u"doc":        return u"application/msword"
    elif extension == u"xls":        return u"application/vnd.ms-excel"
    elif extension == u"ppt":        return u"application/vnd.ms-powerpoint"
    elif extension == u"mpp":        return u"application/vnd.ms-project"
    elif extension == u"rtf":        return u"text/rtf"
    elif extension == u"dat":        return u"application/octet-stream"
    elif extension == u"flv":        return u"video/flv"
    elif extension == u"ogv":        return u"video/ogg"
    elif extension == u"webm":       return u"video/webm"
    elif extension == u"mp4":        return u"video/mp4"
    elif extension == u"mp3":        return u"audio/mp3"
    elif extension == u"ogg":        return u"audio/ogg"
    e = guess_type(u"x." + extension)
    if e[0]:                return e[0]
    return u""

def GetExtensionMimeType(mime):
    # custom and uncommeon
    if mime == u"application/flash":  return u"fla"
    # standard
    elif mime == u"text/html":        return u"html"
    elif mime == u"text/plain":       return u"txt"
    elif mime == u"text/html":        return u"dtml"
    elif mime == u"image/jpeg":       return u"jpg"
    elif mime == u"image/gif":        return u"gif"
    elif mime == u"image/png":        return u"png"
    elif mime == u"image/jpeg":       return u"jpeg"
    elif mime == u"image/psd":        return u"psd"
    elif mime == u"application/pdf":                  return u"pdf"
    elif mime == u"application/x-shockwave-flash":    return u"swf"
    elif mime == u"application/x-director":           return u"dcr"
    elif mime == u"application/msword":               return u"doc"
    elif mime == u"application/vnd.ms-excel":         return u"xls"
    elif mime == u"application/vnd.ms-word":          return u"doc"
    elif mime == u"application/vnd.ms-powerpoint":    return u"ppt"
    elif mime == u"application/vnd.ms-project":       return u"mpp"
    elif mime == u"text/rtf":                         return u"rtf"
    elif mime == u"application/octet-stream":         return u"dat"
    elif mime == u"video/flv":        return u"flv"
    elif mime == u"video/ogg":        return u"ogv"
    elif mime == u"video/webm":       return u"webm"
    elif mime == u"video/mp4":        return u"mp4"
    elif mime == u"audio/mp3":        return u"mp3"
    elif mime == u"audio/ogg":        return u"ogg"

    m = guess_extension(mime)
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


def LoadFromFile(path):
    file = open(path)
    if not file:
        return None
    value = file.read()
    file.close()
    return value


def WriteToFile(path, value, append = False):
    if append:
        file = open(path, "ab+")
        if not file:
            return False
    else:
        file = open(path, "wb")
        if not file:
            return False
    file.write(value)
    file.close()
    return True


# failsafe type conversion ---------------------------------------------------------------------------------------

def ConvertToStr(data, sep=u"\n"):
    if isinstance(data, (list, tuple)):
        return ConvertListToStr(data)
    elif isinstance(data, dict):
        v = []
        for key, value in data.items():
            v.append(u"%s: %s"%(unicode(key), ConvertToStr(value, sep)))
        return sep.join(v)
    return unicode(data)

def ConvertToBool(data, raiseExcp = False):
    try:
        return int(data)
    except:
        if isinstance(data, basestring):
            if data.lower() in (u"true", u"yes", u"checked", u"ja", u"qui", u"si"):
                return True
            if data.lower() in (u"false", u"no", u"nein", u"non"):
                return False
        if raiseExcp:
            raise
        return False

def ConvertToInt(data, raiseExcp = False):
    try:
        return int(data)
    except:
        if ConvertToBool(data, raiseExcp):
            return 1
        else:
            return 0
        if raiseExcp:
            raise 
        return 0

def ConvertToFloat(data, raiseExcp = False):
    try:
        return float(data)
    except:
        if ConvertToBool(data, raiseExcp):
            return 1.0
        else:
            return 0.0
        if raiseExcp:
            raise 
        return 0.0

def ConvertToLong(data, raiseExcp = False):
    try:
        return long(data)
    except:
        if ConvertToBool(data, raiseExcp):
            return 1L
        else:
            return 0L
        if raiseExcp:
            raise 
        return 0L

def ConvertToList(data, raiseExcp = False):
    """
    converts a string to list.
    the list items can be seperated by "," or "\n"
    """
    try:
        if not data:
            return []
        if isinstance(data, (list,tuple)):
            return data
        data = data.strip()
        if not len(data):
            return []
        if data[0] in (u"[", u"("):
            data = data[1:-1]

        sep = u","
        if data.find(u"\n") != -1:
            sep = u"\n"

        result = []
        l = data.split(sep)
        for value in l:
            value = value.strip()
            if not len(value):
                continue
            if value[0] in (u"'", u"\""):
                value = value[1:-1]
            result.append(value)
        return result
    except:
        if raiseExcp:
            raise 
        return []

def ConvertToNumberList(data, raiseExcp = False):
    try:
        l = ConvertToList(data, raiseExcp)
        for i in range(len(l)):
            l[i] = ConvertToLong(l[i], raiseExcp)
        return l
    except:
        if raiseExcp:
            raise 
        return []


def ConvertListToStr(values, sep = u", ", textMarker = u"", keepType = False):
    """
    converts a python list to string. .
    the list items are seperated by ",". list items are converted to string
    """
    if not values:
        return u""
    if isinstance(values, basestring):
        return u"%s%s%s" % (textMarker, values, textMarker)
    s = []
    for v in values:
        if textMarker != u"":
            tm = textMarker
            if keepType:
                if isinstance(v, (int, long, float)):
                    tm = u""
            s.append(u"%s%s%s" % (textMarker, unicode(v), textMarker))
        else:
            s.append(unicode(v))
    return sep.join(s)


def ConvertDictToStr(values, sep = u"\n"):
    """
    converts a python dictionary to key list string.
    the list items are seperated by ",". list items are converted to string
    
    ::
        key1: value1
        key2: value2
        
    result string
    """
    s = [u"%s: %s" % (key, ConvertToStr(value, sep)) for key, value in values.items()]
    return sep.join(s)



# Logging --------------------------------------------------------------------------


def DUMP(data, path = "dump.txt", addTime=False):
    if addTime:
        date = datetime.now()
        aS = "\r\n\r\n" + date.strftime("%Y-%m-%d %H:%M:%S") + "\r\n" + str(data)
    else:
        aS = "\r\n\r\n" + str(data)
    WriteToFile(path, True)

def STACKF(t=0, label = "", limit = 15, path = "_stackf.txt", name=""):
    import time
    import traceback
    n = time.time() - t
    date = datetime.now()
    h = "%s: %f (%s)" % (date.strftime("%Y-%m-%d %H:%M:%S"),n,name)
    if limit<2:
        DUMP("%s\r\n%s\r\n" % (h, label), path)
        return
    import StringIO
    s = StringIO.StringIO()
    traceback.print_stack(limit=limit, file=s)
    DUMP("%s\r\n%s\r\n%s" % (h, label, s.getvalue()), path)

def LOG(data = "", path="_log.txt", t=0):
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
    

