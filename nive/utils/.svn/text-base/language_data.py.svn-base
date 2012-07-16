#
""" -*- coding: utf-8 -*-"""

from copy import deepcopy


# default ------------------------------------------------
empty = {}
empty["code"] = u""
empty["code2"] = u""
empty["name"] = u""
empty["articles_used"] = 0 # 1=article, 2=f+m, 3=f+m+n
empty["articles"] = {}
empty["article_abbr"] = ""
empty["verb_prefix"] = ""
empty["plural"] = ""
empty["codepage"] = ""
empty["remove_chars"] = "\t\r\n"
empty["special_chars"] = u""


#[s] languages -------------------------------------------

noArticle = "keine Zuordnung"
languages = ("ger", "eng", "ita", "spa", "fra", "por", "lat", "dan", "dut", "pol", "swe", "cze", "tur", "epo",
             "rus", "fin", "gre", "grc", "hrv", "rum", "afr", "ara", "alb", "amh", "arm", "aze", "bel", "ben",
             "tib", "bos", "bul", "cat", "zho", "hrv", "esp", "est", "fil", "fin", "kat", "ell", "hau",
             "heb", "hin", "hun", "isi", "ind", "jpn", "kor", "lav", "lit", "mon", "nep", "nor", "per", "pol",
             "ron", "san", "srp", "slk", "swa", "tha", "ukr", "vie")

# ger ---------------------------------------------------
ger = deepcopy(empty)
ger["code"] = u"ger"
ger["code2"] = u"de"
ger["name"] = u"Deutsch"
ger["articles_used"] = 3
ger["articles"] = {"m": "der", "f": "die", "n": "das"}
ger["verb_prefix"] = ""
ger["plural"] = "s"
ger["codepage"] = "iso-8859-15"
ger["special_chars"] = u"äöüÄÖÜß"

# eng ---------------------------------------------------
eng = deepcopy(empty)
eng["code"] = u"eng"
eng["code2"] = u"en"
eng["name"] = u"English"
eng["articles_used"] = 1
eng["articles"] = {"a": "the"}
eng["verb_prefix"] = "to"
eng["plural"] = "s"
eng["codepage"] = "iso-8859-1"
eng["special_chars"] = u""

# ita ---------------------------------------------------
ita = deepcopy(empty)
ita["code"] = u"ita"
ita["code2"] = u"it"
ita["name"] = u"Italiano"
ita["articles_used"] = 2
ita["articles"] = {"m": "il", "f": "la"}
ita["article_abbr"] = "l'"
ita["verb_prefix"] = ""
ita["plural"] = ""
ita["codepage"] = "iso-8859-3"
ita["special_chars"] = u"ÀÈÉÌÒÙàèéìòù"

# spa ---------------------------------------------------
spa = deepcopy(empty)
spa["code"] = u"spa"
spa["code2"] = u"es"
spa["name"] = u"Español"
spa["articles_used"] = 2
spa["articles"] = {"m": "el", "f": "la"}
spa["article_abbr"] = ""
spa["verb_prefix"] = ""
spa["plural"] = "s"
spa["codepage"] = "iso-8859-3"
spa["special_chars"] = u"ÁÉÍÑÓÚÜáéíñóúü"


# fra ---------------------------------------------------
fra = deepcopy(empty)
fra["code"] = u"fra"
fra["code2"] = u"fr"
fra["name"] = u"Français"
fra["articles_used"] = 2
fra["articles"] = {"m": "le", "f": "la"}
fra["article_abbr"] = "l’"
fra["verb_prefix"] = ""
fra["plural"] = ""
fra["codepage"] = "iso-8859-3"
fra["special_chars"] = u"ÀÂÇÈÉÊËÎÏÔŒÙÛÜŸàâçèéêëîïôœùûüÿ"


# por ---------------------------------------------------
por = deepcopy(empty)
por["code"] = u"por"
por["code2"] = u"pt"
por["name"] = u" Português"
por["articles_used"] = 2
por["articles"] = {"m": "o", "f": "a"}
por["article_abbr"] = ""
por["verb_prefix"] = ""
por["plural"] = ""
por["codepage"] = "iso-8859-3"
por["special_chars"] = u"ÀÁÂÃÇÉÊÍÓÔÕÚÜàáâãçéêíóôõúü"


# lat ---------------------------------------------------
lat = deepcopy(empty)
lat["code"] = u"lat"
lat["code2"] = u"la"
lat["name"] = u"Lingua Latina"
lat["articles_used"] = 0
lat["articles"] = {}
lat["article_abbr"] = ""
lat["verb_prefix"] = ""
lat["plural"] = ""
lat["codepage"] = "iso-8859-3"
lat["special_chars"] = u"ÆŒæœ"

# dan ---------------------------------------------------
dan = deepcopy(empty)
dan["code"] = u"dan"
dan["code2"] = u"da"
dan["name"] = u"Dansk"
dan["articles_used"] = 0
dan["articles"] = {}
dan["article_abbr"] = ""
dan["verb_prefix"] = ""
dan["plural"] = "r, e"
dan["codepage"] = "iso-8859-10"
dan["special_chars"] = u"ÅÆØåæø"

# dut ---------------------------------------------------
dut = deepcopy(empty)
dut["code"] = u"dut"
dut["code2"] = u"nl"
dut["name"] = u"Nederlands"
dut["articles_used"] = 3
dut["articles"] = {"m": "de",  "f": "de", "n": "het"}
dut["article_abbr"] = ""
dut["verb_prefix"] = ""
dut["plural"] = ""
dut["codepage"] = "iso-8859-10"
dut["special_chars"] = u"ÄÈÉËÏĲÖÜäèéëïĳöü"

# pol ---------------------------------------------------
pol = deepcopy(empty)
pol["code"] = u"pol"
pol["code2"] = u"pl"
pol["name"] = u"Polski"
pol["articles_used"] = 4
pol["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
pol["article_abbr"] = ""
pol["verb_prefix"] = ""
pol["plural"] = ""
pol["codepage"] = "iso-8859-2"
pol["special_chars"] = u"ĄĆĘŁŃÓŚŹŻąćęłłńóśźż "

# swe ---------------------------------------------------
swe = deepcopy(empty)
swe["code"] = u"swe"
swe["code2"] = u"sv"
swe["name"] = u"Svenska"
swe["articles_used"] = 2
swe["articles"] = {"u": "en", "n": "ett"}
swe["article_abbr"] = ""
swe["verb_prefix"] = ""
swe["plural"] = ""
swe["codepage"] = "iso-8859-10"
swe["special_chars"] = u"ÄÅÖäåö "

# cze ---------------------------------------------------
cze = deepcopy(empty)
cze["code"] = u"cze"
cze["code2"] = u"cs"
cze["name"] = u" Čeština"
cze["articles_used"] = 4
cze["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
cze["article_abbr"] = ""
cze["verb_prefix"] = ""
cze["plural"] = ""
cze["codepage"] = "iso-8859-2"
cze["special_chars"] = u"ÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéĕíňóřšťúŭýž"

# tur ---------------------------------------------------
tur = deepcopy(empty)
tur["code"] = u"tur"
tur["code2"] = u"tr"
tur["name"] = u" Türkçe"
tur["articles_used"] = 0
tur["articles"] = { }
tur["article_abbr"] = ""
tur["verb_prefix"] = ""
tur["plural"] = ""
tur["codepage"] = "iso-8859-9"
tur["special_chars"] = u"ÂÇĞİÖŞÜâçğıöşü"

# epo ---------------------------------------------------
epo = deepcopy(empty)
epo["code"] = u"epo"
epo["code2"] = u"eo"
epo["name"] = u"Esperanto"
epo["articles_used"] = 0
epo["articles"] = { }
epo["article_abbr"] = ""
epo["verb_prefix"] = ""
epo["plural"] = ""
epo["codepage"] = "iso-8859-3"
epo["special_chars"] = u"ĈĜĤĴŜŬĉĝĥĵŝǔ"

# fin ---------------------------------------------------
fin = deepcopy(empty)
fin["code"] = u"fin"
fin["code2"] = u"fi"
fin["name"] = u"Suomi"
fin["articles_used"] = 0
fin["articles"] = { }
fin["article_abbr"] = ""
fin["verb_prefix"] = ""
fin["plural"] = ""
fin["codepage"] = "iso-8859-10"
fin["special_chars"] = u"ÄÅÖŠŽäåöšž"

# rus ---------------------------------------------------
rus = deepcopy(empty)
rus["code"] = u"rus"
rus["code2"] = u"ru"
rus["name"] = u"Ру́сский"
rus["articles_used"] = 4
rus["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
rus["article_abbr"] = ""
rus["verb_prefix"] = ""
rus["plural"] = ""
rus["codepage"] = "iso-8859-5"
rus["special_chars"] = u"АаБбВвЃѓДдЂђЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтЌќЋћУуЎўФфЦцЧчШшЬьѢѣ"

# gre ---------------------------------------------------
gre = deepcopy(empty)
gre["code"] = u"gre"
gre["code2"] = u"el"
gre["name"] = u"Ελληνικα"
gre["articles_used"] = 3
gre["articles"] = {"m": "o", "f": "η", "n": "το"}
gre["article_abbr"] = ""
gre["verb_prefix"] = ""
gre["plural"] = ""
gre["codepage"] = "iso-8859-7"
gre["special_chars"] = u"ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψως"

# grc ---------------------------------------------------
grc = deepcopy(empty)
grc["code"] = u"grc"
grc["code2"] = u""
grc["name"] = u"ἡ Ἑλληνικὴ γλῶσσα"
grc["articles_used"] = 3
grc["articles"] = {"m": "o", "f": "η", "n": "το"}
grc["article_abbr"] = ""
grc["verb_prefix"] = ""
grc["plural"] = ""
grc["codepage"] = "iso-8859-7"
grc["special_chars"] = u"ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψως"

# hrv ---------------------------------------------------
hrv = deepcopy(empty)
hrv["code"] = u"hrv"
hrv["code2"] = u"hr"
hrv["name"] = u" Hrvatski"
hrv["articles_used"] = 0
hrv["articles"] = {}
hrv["article_abbr"] = ""
hrv["verb_prefix"] = ""
hrv["plural"] = ""
hrv["codepage"] = "iso-8859-2"
hrv["special_chars"] = u"ĆČĐŠŽćčđšž"

# rum ---------------------------------------------------
rum = deepcopy(empty)
rum["code"] = u"rum"
rum["code2"] = u"ro"
rum["name"] = u"Română"
rum["articles_used"] = 3
rum["articles"] = {"m": "m", "f": "f"}
rum["article_abbr"] = "l'"
rum["verb_prefix"] = ""
rum["plural"] = ""
rum["codepage"] = "iso-8859-3"
rum["special_chars"] = u"ÂĂÎȘȚâăîșț"

# afr ---------------------------------------------------
afr = deepcopy(empty)
afr["code"] = u"afr"
afr["code2"] = u"af"
afr["name"] = u"Afrikaans"
afr["codepage"] = "iso-8859-10"
afr["special_chars"] = u"ÈèÉéÊêËëÎîÏïÔôÛû"

# ara ---------------------------------------------------
ara = deepcopy(empty)
ara["code"] = u"ara"
ara["code2"] = u"ar"
ara["name"] = u"للغة العربية‎"
ara["codepage"] = "iso-8859-6"
ara["special_chars"] = u""

# alb ---------------------------------------------------
alb = deepcopy(empty)
alb["code"] = u"alb"
alb["code2"] = u"sq"
alb["name"] = u"Gjuha Shqipe"
alb["codepage"] = "iso-8859-3"
alb["special_chars"] = u"ËëÇç"

# amh ---------------------------------------------------
amh = deepcopy(empty)
amh["code"] = u"amh"
amh["code2"] = u"am"
amh["name"] = u"Amarəñña"
amh["codepage"] = ""
amh["special_chars"] = u""

# arm -------------------------------------------------
arm = deepcopy(empty)
arm["code"] = u"arm"
arm["code2"] = u"hy"
arm["name"] = u"Hajeren lesu"
arm["codepage"] = ""
arm["special_chars"] = u""

# aze ---------------------------------------------------
aze = deepcopy(empty)
aze["code"] = u" aze "
aze["code2"] = u"tr"
aze["name"] = u"Azərbaycan dili"
aze["codepage"] = "iso-8859-9"
aze["special_chars"] = u"ƏəÂÇĞİÖŞÜâçğıöşü"

# bel ---------------------------------------------------
bel = deepcopy(empty)
bel["code"] = u"bel"
bel["code2"] = u"be"
bel["name"] = u"беларуская мова"
bel["articles_used"] = 4
bel["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
bel["article_abbr"] = ""
bel["verb_prefix"] = ""
bel["plural"] = ""
bel["codepage"] = "iso-8859-5"
bel["special_chars"] = u"АаБбВвЃѓДдЂђЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтЌќЋћУуЎўФфЦцЧчШшЬьѢѣ"

# ben---------------------------------------------------
ben = deepcopy(empty)
ben["code"] = u"ben"
ben["code2"] = u"bn"
ben["name"] = u"Bangla bhasha"
ben["codepage"] = ""
ben["special_chars"] = u""

# tib------------------------------------------------
tib = deepcopy(empty)
tib["code"] = u" tib "
tib["code2"] = u"bo"
tib["name"] = u"Bod yig"
tib["codepage"] = ""
tib["special_chars"] = u""

# bos---------------------------------------------------
bos = deepcopy(empty)
bos["code"] = u"bos"
bos["code2"] = u"bs"
bos["name"] = u"Bosanski jezik"
bos["codepage"] = "iso-8859-2"
bos["special_chars"] = u"čćžšž"

# bul ---------------------------------------------------
bul = deepcopy(empty)
bul["code"] = u"bul"
bul["code2"] = u"bg"
bul["name"] = u"Български език"
bul["articles_used"] = 4
bul["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
bul["article_abbr"] = ""
bul["verb_prefix"] = ""
bul["plural"] = ""
bul["codepage"] = "iso-8859-5"
bul["special_chars"] = u"АаБбВвЃѓДдЂђЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтЌќЋћУуЎўФфЦцЧчШшЬьѢѣ"

# cat ---------------------------------------------------
cat = deepcopy(empty)
cat["code"] = u"cat"
cat["code2"] = u"ca"
cat["name"] = u"Catalán"
cat["articles_used"] = 2
cat["articles"] = {"m": "el", "f": "la"}
cat["article_abbr"] = ""
cat["verb_prefix"] = ""
cat["plural"] = "s"
cat["codepage"] = "iso-8859-3"
cat["special_chars"] = u"ÁÉÍÑÓÚÜáéíñóúü"

# zho ------------------------------------------------
zho = deepcopy(empty)
zho["code"] = u"zho"
zho["code2"] = u"zh"
zho["name"] = u"中文"
zho["codepage"] = ""
zho["special_chars"] = u""

# hrv ---------------------------------------------------
hrv = deepcopy(empty)
hrv["code"] = u"hrv"
hrv["code2"] = u"sh"
hrv["name"] = u"Hrvatski jezik"
hrv["codepage"] = "iso-8859-2"
hrv["special_chars"] = u"čćžšž"

# esp ---------------------------------------------------
esp = deepcopy(empty)
esp["code"] = u"esp"
esp["code2"] = u"ep"
esp["name"] = u"Esperanto"
esp["codepage"] = "iso-8859-3"

# est ---------------------------------------------------
est = deepcopy(empty)
est["code"] = u"est"
est["code2"] = u"et"
est["name"] = u"Eesti keel"
est["codepage"] = "iso-8859-1"

# fil ---------------------------------------------------
fil = deepcopy(empty)
fil["code"] = u"fil"
fil["code2"] = u"fl"
fil["name"] = u"Filipino"
fil["codepage"] = "iso-8859-1"

# fin ---------------------------------------------------
fin = deepcopy(empty)
fin["code"] = u"fin"
fin["code2"] = u"fi"
fin["name"] = u"Suomi"
fin["codepage"] = "iso-8859-1"
fin["special_chars"] = u"öÖäÄåÅ"

# kat ---------------------------------------------------
kat = deepcopy(empty)
kat["code"] = u"kat"
kat["code2"] = u"ka"
kat["name"] = u"Kartuli Ena"
kat["codepage"] = ""

# ell ---------------------------------------------------
ell = deepcopy(empty)
ell["code"] = u"ell"
ell["code2"] = u"el"
ell["name"] = u"ελληνική γλώσσα"
ell["codepage"] = "iso-8859-7"

# hau ---------------------------------------------------
hau = deepcopy(empty)
hau["code"] = u"hau"
hau["code2"] = u"ha"
hau["name"] = u"Hausa"
hau["codepage"] = "iso-8859-1"

# heb ---------------------------------------------------
heb = deepcopy(empty)
heb["code"] = u"heb"
heb["code2"] = u"iw"
heb["name"] = u" עברית"
heb["codepage"] = "iso-8859-8"

# hin ---------------------------------------------------
hin = deepcopy(empty)
hin["code"] = u"hin"
hin["code2"] = u"hi"
hin["name"] = u"Hindi"
hin["codepage"] = ""

# hun ---------------------------------------------------
hun = deepcopy(empty)
hun["code"] = u"hun"
hun["code2"] = u"hu"
hun["name"] = u"Magyar nyelv"
hun["codepage"] = "iso-8859-1"

# isi ---------------------------------------------------
isi = deepcopy(empty)
isi["code"] = u"isi"
isi["code2"] = u"is"
isi["name"] = u"Íslenska"
isi["codepage"] = "iso-8859-1"

# ind ---------------------------------------------------
ind = deepcopy(empty)
ind["code"] = u"ind"
ind["code2"] = u"in"
ind["name"] = u"Bahasa Indonesia"
ind["codepage"] = "iso-8859-1"

# jpn ---------------------------------------------------
jpn = deepcopy(empty)
jpn["code"] = u"jpn"
jpn["code2"] = u"ja"
jpn["name"] = u"日本語"
jpn["codepage"] = ""

# kor ---------------------------------------------------
kor = deepcopy(empty)
kor["code"] = u"kor"
kor["code2"] = u"ko"
kor["name"] = u"韓國語"
kor["codepage"] = ""

# lav ---------------------------------------------------
lav = deepcopy(empty)
lav["code"] = u"lav"
lav["code2"] = u"lv"
lav["name"] = u"Latviešu valoda"
lav["codepage"] = "iso-8859-4"

# lit ---------------------------------------------------
lit = deepcopy(empty)
lit["code"] = u"lit"
lit["code2"] = u"lt"
lit["name"] = u"Lietuvių kalba"
lit["codepage"] = "iso-8859-4"

# mon ---------------------------------------------------
mon = deepcopy(empty)
mon["code"] = u"mon"
mon["code2"] = u"mn"
mon["name"] = u"халх монгол хэл"
mon["codepage"] = "iso-8859-5"

# nep ---------------------------------------------------
nep = deepcopy(empty)
nep["code"] = u"nep"
nep["code2"] = u"ne"
nep["name"] = u"Nepali"
nep["codepage"] = ""

# nor ---------------------------------------------------
nor = deepcopy(empty)
nor["code"] = u"nor"
nor["code2"] = u"no"
nor["name"] = u"Norsk"
nor["codepage"] = "iso-8859-1"

# per ---------------------------------------------------
per = deepcopy(empty)
per["code"] = u"per"
per["code2"] = u"fa"
per["name"] = u"فارسی"
per["codepage"] = "iso-8859-6"

# pol ---------------------------------------------------
pol = deepcopy(empty)
pol["code"] = u"pol"
pol["code2"] = u"pl"
pol["name"] = u"Język polski"
pol["codepage"] = "iso-8859-2"

# ron ---------------------------------------------------
ron = deepcopy(empty)
ron["code"] = u"ron"
ron["code2"] = u"ro"
ron["name"] = u"Limba româna"
ron["codepage"] = "iso-8859-1"

# san ---------------------------------------------------
san = deepcopy(empty)
san["code"] = u"san"
san["code2"] = u"sa"
san["name"] = u"Sanskrit"
san["codepage"] = ""

# srp ---------------------------------------------------
srp = deepcopy(empty)
srp["code"] = u"srp"
srp["code2"] = u"sr"
srp["name"] = u"Srpski jezik"
srp["codepage"] = "iso-8859-2"

# slk ---------------------------------------------------
slk = deepcopy(empty)
slk["code"] = u"slk"
slk["code2"] = u"sk"
slk["name"] = u"slovenčina"
slk["codepage"] = "iso-8859-2"

# swa ---------------------------------------------------
swa = deepcopy(empty)
swa["code"] = u"swa"
swa["code2"] = u"sw"
swa["name"] = u"Kiswahili"
swa["codepage"] = "iso-8859-1"

# tha ---------------------------------------------------
tha = deepcopy(empty)
tha["code"] = u"tha"
tha["code2"] = u"th"
tha["name"] = u"ภาษาไทย"
tha["codepage"] = "iso-8859-11"

# ukr ---------------------------------------------------
ukr = deepcopy(empty)
ukr["code"] = u"ukr"
ukr["code2"] = u"uk"
ukr["name"] = u"українська"
ukr["codepage"] = "iso-8859-5"

# vie ---------------------------------------------------
vie = deepcopy(empty)
vie["code"] = u"vie"
vie["code2"] = u"vi"
vie["name"] = u"Tiếng Việt"
vie["codepage"] = "iso-8859-1"



#[s] functions -------------------------------------------

global _cl
_cl = []
for l in languages:
    lang = globals().get(l)
    _cl.append({"id": lang["code"], "name": lang["name"]})

def GetConf(langcode):
    """
    Load language configuration by code (3 letters)
    """
    if langcode in languages:
        return globals().get(langcode)
    if len(langcode)==2:
        for l in languages:
            c = globals().get(l["code"])
            if c["code2"] == langcode:
                return c
    return empty


def GetLanguages():
    """
    load codelist of languages and cache
    """
    return _cl
    #cl = []
    #for l in languages:
    #    cl.append({"id": l["code"], "name": l["name"]})
    #_cl = cl
    #return cl
