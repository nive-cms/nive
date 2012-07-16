# -*- coding: utf-8 -*-

__doc__ = ""


import types
from time import *
from string import *
import re, sys, os, math

kMonth = [u"", u"Januar",u"Februar",u"März",u"April",u"Mai",u"Juni",u"Juli",u"August",u"September",u"Oktober",u"November",u"Dezember"]
kDay = [u"Sonntag",u"Montag",u"Dienstag",u"Mittwoch",u"Donnerstag",u"Freitag",u"Samstag"]

class DvDateTime:
    """Universal Date/Time class"""

    def __init__(self, inDateTime = None):
        self.Set(inDateTime)

    def __str__(self):
        return self.GetDB()
    
    def Set(self, inDateTime):
        self._pTime = ()
        aT = type(inDateTime)
        if inDateTime == None:
            return
        elif aT == struct_time:
            self._pTime = inDateTime
        elif aT == types.IntType:
            if inDateTime > 0:
                self._pTime = localtime(inDateTime)
        elif aT == types.LongType:
            if inDateTime > 0:
                self._pTime = localtime(inDateTime)
        elif aT == types.FloatType:
            if inDateTime > 0:
                self._pTime = localtime(inDateTime)
        elif aT == types.TupleType:
            self._pTime = inDateTime
        elif aT in (types.StringType,types.UnicodeType):
            self.SetStr(inDateTime)
        elif aT == types.InstanceType:
            self.SetStr(str(inDateTime))
        else:
            self._pTime = localtime()

    def Now(self):
        self._pTime = localtime()
    
    # render date / time ------------------------------------------------------
    
    def Get(self):
        return self._pTime
    
    def GetFloat(self):
        if not self._pTime:
            return 0
        return mktime(self._pTime)
    
    def GetFormat(self, inFmtStr):
        try:
            if len(self._pTime):
                return strftime(inFmtStr, self._pTime)
        except:
            pass
        return ""
    
    def GetHHMM(self):                  return self.GetFormat(u"%H:%M")
    def GetHHMMSS(self):                return self.GetFormat(u"%H:%M:%S")
    def GetDDMMYY(self):                return self.GetFormat(u"%d.%m.%y")
    def GetDDMMYYYY(self):              return self.GetFormat(u"%d.%m.%Y")
    def GetHHMMSSDDMMYYYY(self):        return self.GetFormat(u"%H:%M:%S %d.%m.%Y")
    def GetYYYYMMDDHHMM(self):          return self.GetFormat(u"%Y.%m.%d %H:%M")
    def GetYYYYMMDDHHMMSS(self):        return self.GetFormat(u"%Y.%m.%d %H:%M:%S")
    def GetDDMMYYYYHHMM(self):          return self.GetFormat(u"%d.%m.%Y %H:%M")
    def GetDDMMYYYYHHMMSS(self):        return self.GetFormat(u"%d.%m.%Y %H:%M:%S")
    def GetYYMM(self):                  return self.GetFormat(u"%y%m")

    def GetSec(self):                    
        try:            return atoi(strftime(u"%S", self._pTime))
        except:            return 0
    
    def GetMin(self):
        try:            return atoi(strftime(u"%M", self._pTime))
        except:            return 0

    def GetHour(self):
        try:            return atoi(strftime(u"%H", self._pTime))
        except:            return 0
    
    def GetDay(self):
        try:            return atoi(strftime(u"%d", self._pTime))
        except:            return 0

    def GetMonth(self):
        try:            return atoi(strftime(u"%m", self._pTime))
        except:            return 0

    def GetYear(self):
        try:            return atoi(strftime(u"%Y", self._pTime))
        except:            return 0

    def GetWeek(self):
        try:            return atoi(strftime(u"%U", self._pTime))
        except:            return 0

    def GetDayOfWeek(self):
        try:            return atoi(strftime(u"%w", self._pTime))
        except:            return 0

    def GetDayOfYear(self):
        try:            return atoi(strftime(u"%j", self._pTime))
        except:            return 0

    def GetDB(self):                    return self.GetFormat(u"%d/%m/%Y %H:%M:%S")
    def GetDBMySql(self):               return self.GetFormat(u"%Y-%m-%d %H:%M:%S")
    def GetDBMySql2(self):              return self.GetFormat(u"%Y-%m-%d %H:%M")
    def GetDBDate(self):                return self.GetFormat(u"%d/%m/%Y")
    def GetDBTime(self):                return self.GetFormat(u"%H:%M:%S")
    
    def GetGMT(self):
        return u"%s, %02d %s %04d %02d:%02d:%02d +0200" % (
            [u"Mon", u"Tue", u"Wed", u"Thu", u"Fri", u"Sat", u"Sun"][self.GetDayOfWeek()],
            self.GetDay(),
            [u"Jan", u"Feb", u"Mar", u"Apr", u"May", u"Jun",
             u"Jul", u"Aug", u"Sep", u"Oct", u"Nov", u"Dec"][self.GetMonth()-1],
            self.GetYear(), self.GetHour(), self.GetMin(), self.GetSec())

    def GetTextGerman(self, addDay=False):
        wd = kDay[int(strftime(u"%w", self._pTime))]
        m = kMonth[int(strftime(u"%m", self._pTime))]
        d = int(strftime(u"%d", self._pTime))
        y = int(strftime(u"%Y", self._pTime))
        if addDay:
            return u"%s den %s. %s %s" % (wd, d, m, y)
        return u"%s. %s %s" % (d, m, y)

    def GetTextGermanNow(self):
        self.Now()
        return self.GetTextGerman()
        

    # set --------------------------------------------------------------------------------------------------------

    def SetStr(self, inStr):
        if inStr == "now":
            self.Now()
            return
        if inStr == "nowdate":
            self.Now()
            self._pTime = (self._pTime[0], self._pTime[1], self._pTime[2], 0, 0, 0, 0, 1, 1)
            return
        if inStr == "nowtime":
            self.Now()
            self._pTime = (0, 0, 0, self._pTime[3], self._pTime[4], 0, 0, 1, 1)
            return
        #inStr = inStr.replace("00:00:00", "")
        return self._parse(inStr)
    
    def ParseDB(self, inStr):
        try:
            l = inStr.split(u" ")
            l1 = l[0].split(u"-")
            l2 = l[1].split(u":")
            l3 = l2[2].split(u".")
            self._pTime = (int(l1[0]), int(l1[1]), int(l1[2]), int(l2[0]), int(l2[1]), int(l3[0]), 0, 0, 1)
            return True
        except:
            return False            
            

    # protected --------------------------------------------------------------------------------------------------------

    def _parse(self,st, **kw):
        """ zope datetime """
        if len(st) == 0:
            return False
            
        datefmt = kw.get('datefmt', 'international')
        #assert datefmt in ('us', 'international')

        DateTimeError='DateTimeError'
        SyntaxError  ='Invalid Date-Time String'
        DateError    ='Invalid Date Components'

        _month_len  =((0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31), 
                     (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31))
        _monthmap   ={'january': 1,   'jan': 1,
                      'february': 2,  'feb': 2,
                      'march': 3,     'mar': 3,
                      'april': 4,     'apr': 4,
                      'may': 5,
                      'june': 6,      'jun': 6,
                      'july': 7,      'jul': 7,
                      'august': 8,    'aug': 8,
                      'september': 9, 'sep': 9, 'sept': 9,
                      'october': 10,  'oct': 10,
                      'november': 11, 'nov': 11,
                      'december': 12, 'dec': 12}
        _days       =[u'Sunday',u'Monday',u'Tuesday',u'Wednesday',
                      u'Thursday',u'Friday',u'Saturday']
        _days_a     =[u'Sun',  u'Mon',  u'Tue',  u'Wed',  u'Thu',  u'Fri',  u'Sat' ]
        _days_p     =[u'Sun.', u'Mon.', u'Tue.', u'Wed.', u'Thu.', u'Fri.', u'Sat.']
        _daymap     ={'sunday': 1,    'sun': 1,
                      'monday': 2,    'mon': 2,
                      'tuesday': 3,   'tues': 3,  'tue': 3,
                      'wednesday': 4, 'wed': 4,
                      'thursday': 5,  'thurs': 5, 'thur': 5, 'thu': 5,
                      'friday': 6,    'fri': 6,
                      'saturday': 7,  'sat': 7}

        # Parse date-time components from a string
        month = year = tm = None
        spaces        = u' \t\n'
        intpat        = re.compile(r'([0-9]+)')
        fltpat        = re.compile(r':([0-9]+\.[0-9]+)')
        wordpat       = re.compile(r'([a-zA-Z]+)', re.I)
        delimiters    = u'-/.:,+'
        MonthNumbers  = _monthmap
        DayOfWeekNames= _daymap
        TimeModifiers = [u'am',u'pm']

        st= st.strip()
        sp=st.split()

        ints,dels=[],[]
        i,l=0,len(st)
        while i < l:
            while i < l and st[i] in spaces    : i=i+1
            if i < l and st[i] in delimiters:
                d=st[i]
                i=i+1
            else: d=''
            while i < l and st[i] in spaces    : i=i+1

            # The float pattern needs to look back 1 character, because it
            # actually looks for a preceding colon like ':33.33'. This is
            # needed to avoid accidentally matching the date part of a
            # dot-separated date string such as '1999.12.31'.
            if i > 0: b=i-1
            else: b=i

            ts_results = fltpat.match(st, b)
            if ts_results:
                s=ts_results.group(1)
                i=i+len(s)
                ints.append(float(s))
                continue
            
            #AJ
            ts_results = intpat.match(st, i)
            if ts_results: 
                s=ts_results.group(0)

                ls=len(s)
                i=i+ls
                if (ls==4 and d and d in u'+-' and
                    (len(ints) + (not not month) >= 3)):
                    tz=u'%s%s' % (d,s)
                else:
                    v=int(s)
                    ints.append(v)
                continue


            ts_results = wordpat.match(st, i)
            if ts_results:
                o,s=ts_results.group(0),ts_results.group(0).lower()
                i=i+len(s)
                if i < l and st[i]==u'.': i=i+1
                # Check for month name:
                if MonthNumbers.has_key(s):
                    v=MonthNumbers[s]
                    if month is None: month=v
                    else: 
                        return False
                    continue
                # Check for time modifier:
                if s in TimeModifiers:
                    if tm is None: tm=s
                    else: 
                        return False
                    continue
                # Check for and skip day of week:
                if DayOfWeekNames.has_key(s):
                    continue
                    
            return False

        day=None
        if ints[-1] > 60 and d not in [u'.',u':',u'/'] and len(ints) > 2:
            year=ints[-1]
            del ints[-1]
            if month:
                day=ints[0]
                del ints[:1]
            else:
                month=ints[0]
                day=ints[1]
                del ints[:2]
        elif month:
            if len(ints) > 1:
                if ints[0] > 31:
                    year=ints[0]
                    day=ints[1]
                else:
                    year=ints[1]
                    day=ints[0]
                del ints[:2]
        elif len(ints) > 2:
            if ints[0] > 31:
                year=ints[0]
                if ints[1] > 12:
                    day=ints[1]
                    month=ints[2]
                else:
                    day=ints[2]
                    month=ints[1]
            if ints[1] > 31:
                year=ints[1]
                if ints[0] > 12 and ints[2] <= 12:
                    day=ints[0]
                    month=ints[2]
                elif ints[2] > 12 and ints[0] <= 12:
                    day=ints[2]
                    month=ints[0]
            elif ints[2] > 31:
                year=ints[2]
                if ints[0] > 12:
                    day=ints[0]
                    month=ints[1]
                else:
                    if datefmt==u"us":
                        day=ints[1]
                        month=ints[0]
                    else:
                        day=ints[0]
                        month=ints[1]

            elif ints[0] <= 12:
                month=ints[1]
                day=ints[0]
                year=ints[2]
            del ints[:3]

        if day is None:
            # Use today's date.
            year,month,day = localtime(time())[:3]

        year = _correctYear(year)
        if year < 1000: 
            return ()
        
        leap = year%4==0 and (year%100!=0 or year%400==0)
        try:
            if not day or day > _month_len[leap][month]:
                return False
        except IndexError:
            return False
        tod=0
        if ints:
            i=ints[0]
            # Modify hour to reflect am/pm
            if tm and (tm==u'pm') and i<12:  i=i+12
            if tm and (tm==u'am') and i==12: i=0
            if i > 24: return False
            tod = tod + int(i) * 3600
            del ints[0]
            if ints:
                i=ints[0]
                if i > 60: return False
                tod = tod + int(i) * 60
                del ints[0]
                if ints:
                    i=ints[0]
                    if i > 60: return False
                    tod = tod + i
                    del ints[0]
                    if ints: return False

        
        tod_int = int(math.floor(tod))
        ms = tod - tod_int
        hr,mn,sc = _calcHMS(tod_int, ms)

        self._pTime = (year, month, day, hr, mn, sc, 0, 1, 1)
        return True


def _calcDependentSecond(tz, t):
    # Calculates the timezone-dependent second (integer part only)
    # from the timezone-independent second.
    fset = _tzoffset(tz, t)
    return fset + long(math.floor(t)) + long(EPOCH) - 86400L

def _calcYMDHMS(x, ms):
    # x is a timezone-dependent integer of seconds.
    # Produces yr,mo,dy,hr,mn,sc.
    yr,mo,dy=_calendarday(x / 86400 + jd1901)
    x = int(x - (x / 86400) * 86400)
    hr = x / 3600
    x = x - hr * 3600
    mn = x / 60
    sc = x - mn * 60 + ms
    return yr,mo,dy,hr,mn,sc

def _calcHMS(x, ms):
    # hours, minutes, seconds from integer and float.
    hr = x / 3600
    x = x - hr * 3600
    mn = x / 60
    sc = x - mn * 60 + int(ms)
    return hr,mn,sc

def _correctYear(year):
    # Y2K patch.
    if year >= 0 and year < 100:
        # 00-69 means 2000-2069, 70-99 means 1970-1999.
        if year < 70:
            year = 2000 + year
        else:
            year = 1900 + year
    return year



def FmtSeconds(seconds):
    # Format seconds for display
    #[$] seconds: seconds to convert
    if seconds is None: return u'-' * 5
    if seconds == -1: return u'-'

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


