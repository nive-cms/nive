# -*- coding: utf-8 -*-

countries=(
(u"DE", u"DEU", u"276", u"Deutschland", u"Federal Republic of Germany"),
(u"AT", u"AUT", u"040", u"Österreich", u"Republic of Austria"),
(u"CH", u"CHE", u"756", u"Schweiz", u"Swiss Confederation"),
(u"AF", u"AFG", u"004", u"Afghanistan", u"Islamic Republic of Afghanistan"),
(u"AX", u"ALA", u"248", u"Åland Islands"),
(u"AL", u"ALB", u"008", u"Albania", u"Republic of Albania"),
(u"DZ", u"DZA", u"012", u"Algeria", u"People's Democratic Republic of Algeria"),
(u"AS", u"ASM", u"016", u"American Samoa"),
(u"AD", u"AND", u"020", u"Andorra", u"Principality of Andorra"),
(u"AO", u"AGO", u"024", u"Angola", u"Republic of Angola"),
(u"AI", u"AIA", u"660", u"Anguilla"),
(u"AQ", u"ATA", u"010", u"Antarctica"),
(u"AG", u"ATG", u"028", u"Antigua and Barbuda"),
(u"AR", u"ARG", u"032", u"Argentina", u"Argentine Republic"),
(u"AM", u"ARM", u"051", u"Armenia", u"Republic of Armenia"),
(u"AW", u"ABW", u"533", u"Aruba"),
(u"AU", u"AUS", u"036", u"Australia"),
(u"AZ", u"AZE", u"031", u"Azerbaijan", u"Republic of Azerbaijan"),
(u"BS", u"BHS", u"044", u"Bahamas", u"Commonwealth of the Bahamas"),
(u"BH", u"BHR", u"048", u"Bahrain", u"Kingdom of Bahrain"),
(u"BD", u"BGD", u"050", u"Bangladesh", u"People's Republic of Bangladesh"),
(u"BB", u"BRB", u"052", u"Barbados"),
(u"BY", u"BLR", u"112", u"Belarus", u"Republic of Belarus"),
(u"BE", u"BEL", u"056", u"Belgium", u"Kingdom of Belgium"),
(u"BZ", u"BLZ", u"084", u"Belize"),
(u"BJ", u"BEN", u"204", u"Benin", u"Republic of Benin"),
(u"BM", u"BMU", u"060", u"Bermuda"),
(u"BT", u"BTN", u"064", u"Bhutan", u"Kingdom of Bhutan"),
(u"BO", u"BOL", u"068", u"Bolivia", u"Republic of Bolivia"),
(u"BA", u"BIH", u"070", u"Bosnia and Herzegovina", u"Republic of Bosnia and Herzegovina"),
(u"BW", u"BWA", u"072", u"Botswana", u"Republic of Botswana"),
(u"BV", u"BVT", u"074", u"Bouvet Island"),
(u"BR", u"BRA", u"076", u"Brazil", u"Federative Republic of Brazil"),
(u"IO", u"IOT", u"086", u"British Indian Ocean Territory"),
(u"BN", u"BRN", u"096", u"Brunei Darussalam"),
(u"BG", u"BGR", u"100", u"Bulgaria", u"Republic of Bulgaria"),
(u"BF", u"BFA", u"854", u"Burkina Faso"),
(u"BI", u"BDI", u"108", u"Burundi", u"Republic of Burundi"),
(u"KH", u"KHM", u"116", u"Cambodia", u"Kingdom of Cambodia"),
(u"CM", u"CMR", u"120", u"Cameroon", u"Republic of Cameroon"),
(u"CA", u"CAN", u"124", u"Canada"),
(u"CV", u"CPV", u"132", u"Cape Verde", u"Republic of Cape Verde"),
(u"KY", u"CYM", u"136", u"Cayman Islands"),
(u"CF", u"CAF", u"140", u"Central African Republic"),
(u"TD", u"TCD", u"148", u"Chad", u"Republic of Chad"),
(u"CL", u"CHL", u"152", u"Chile", u"Republic of Chile"),
(u"CN", u"CHN", u"156", u"China", u"People's Republic of China"),
(u"CX", u"CXR", u"162", u"Christmas Island"),
(u"CC", u"CCK", u"166", u"Cocos (Keeling) Islands"),
(u"CO", u"COL", u"170", u"Colombia", u"Republic of Colombia"),
(u"KM", u"COM", u"174", u"Comoros", u"Union of the Comoros"),
(u"CG", u"COG", u"178", u"Congo", u"Republic of the Congo"),
(u"CD", u"COD", u"180", u"Congo, The Democratic Republic of the"),
(u"CK", u"COK", u"184", u"Cook Islands"),
(u"CR", u"CRI", u"188", u"Costa Rica", u"Republic of Costa Rica"),
(u"CI", u"CIV", u"384", u"Côte d'Ivoire", u"Republic of Côte d'Ivoire"),
(u"HR", u"HRV", u"191", u"Croatia", u"Republic of Croatia"),
(u"CU", u"CUB", u"192", u"Cuba", u"Republic of Cuba"),
(u"CY", u"CYP", u"196", u"Cyprus", u"Republic of Cyprus"),
(u"CZ", u"CZE", u"203", u"Czech Republic"),
(u"DK", u"DNK", u"208", u"Denmark", u"Kingdom of Denmark"),
(u"DJ", u"DJI", u"262", u"Djibouti", u"Republic of Djibouti"),
(u"DM", u"DMA", u"212", u"Dominica", u"Commonwealth of Dominica"),
(u"DO", u"DOM", u"214", u"Dominican Republic"),
(u"EC", u"ECU", u"218", u"Ecuador", u"Republic of Ecuador"),
(u"EG", u"EGY", u"818", u"Egypt", u"Arab Republic of Egypt"),
(u"SV", u"SLV", u"222", u"El Salvador", u"Republic of El Salvador"),
(u"GQ", u"GNQ", u"226", u"Equatorial Guinea", u"Republic of Equatorial Guinea"),
(u"ER", u"ERI", u"232", u"Eritrea"),
(u"EE", u"EST", u"233", u"Estonia", u"Republic of Estonia"),
(u"ET", u"ETH", u"231", u"Ethiopia", u"Federal Democratic Republic of Ethiopia"),
(u"FK", u"FLK", u"238", u"Falkland Islands (Malvinas)"),
(u"FO", u"FRO", u"234", u"Faroe Islands"),
(u"FJ", u"FJI", u"242", u"Fiji", u"Republic of the Fiji Islands"),
(u"FI", u"FIN", u"246", u"Finland", u"Republic of Finland"),
(u"FR", u"FRA", u"250", u"France", u"French Republic"),
(u"GF", u"GUF", u"254", u"French Guiana"),
(u"PF", u"PYF", u"258", u"French Polynesia"),
(u"TF", u"ATF", u"260", u"French Southern Territories"),
(u"GA", u"GAB", u"266", u"Gabon", u"Gabonese Republic"),
(u"GM", u"GMB", u"270", u"Gambia", u"Republic of the Gambia"),
(u"GE", u"GEO", u"268", u"Georgia"),
(u"GH", u"GHA", u"288", u"Ghana", u"Republic of Ghana"),
(u"GI", u"GIB", u"292", u"Gibraltar"),
(u"GR", u"GRC", u"300", u"Greece", u"Hellenic Republic"),
(u"GL", u"GRL", u"304", u"Greenland"),
(u"GD", u"GRD", u"308", u"Grenada"),
(u"GP", u"GLP", u"312", u"Guadeloupe"),
(u"GU", u"GUM", u"316", u"Guam"),
(u"GT", u"GTM", u"320", u"Guatemala", u"Republic of Guatemala"),
(u"GG", u"GGY", u"831", u"Guernsey"),
(u"GN", u"GIN", u"324", u"Guinea", u"Republic of Guinea"),
(u"GW", u"GNB", u"624", u"Guinea-Bissau", u"Republic of Guinea-Bissau"),
(u"GY", u"GUY", u"328", u"Guyana", u"Republic of Guyana"),
(u"HT", u"HTI", u"332", u"Haiti", u"Republic of Haiti"),
(u"HM", u"HMD", u"334", u"Heard Island and McDonald Islands"),
(u"VA", u"VAT", u"336", u"Holy See (Vatican City State)"),
(u"HN", u"HND", u"340", u"Honduras", u"Republic of Honduras"),
(u"HK", u"HKG", u"344", u"Hong Kong", u"Hong Kong Special Administrative Region of China"),
(u"HU", u"HUN", u"348", u"Hungary", u"Republic of Hungary"),
(u"IS", u"ISL", u"352", u"Iceland", u"Republic of Iceland"),
(u"IN", u"IND", u"356", u"India", u"Republic of India"),
(u"ID", u"IDN", u"360", u"Indonesia", u"Republic of Indonesia"),
(u"IR", u"IRN", u"364", u"Iran, Islamic Republic of", u"Islamic Republic of Iran"),
(u"IQ", u"IRQ", u"368", u"Iraq", u"Republic of Iraq"),
(u"IE", u"IRL", u"372", u"Ireland"),
(u"IM", u"IMN", u"833", u"Isle of Man"),
(u"IL", u"ISR", u"376", u"Israel", u"State of Israel"),
(u"IT", u"ITA", u"380", u"Italy", u"Italian Republic"),
(u"JM", u"JAM", u"388", u"Jamaica"),
(u"JP", u"JPN", u"392", u"Japan"),
(u"JE", u"JEY", u"832", u"Jersey"),
(u"JO", u"JOR", u"400", u"Jordan", u"Hashemite Kingdom of Jordan"),
(u"KZ", u"KAZ", u"398", u"Kazakhstan", u"Republic of Kazakhstan"),
(u"KE", u"KEN", u"404", u"Kenya", u"Republic of Kenya"),
(u"KI", u"KIR", u"296", u"Kiribati", u"Republic of Kiribati"),
(u"KP", u"PRK", u"408", u"Korea, Democratic People's Republic of", u"Democratic People's Republic of Korea"),
(u"KR", u"KOR", u"410", u"Korea, Republic of"),
(u"KW", u"KWT", u"414", u"Kuwait", u"State of Kuwait"),
(u"KG", u"KGZ", u"417", u"Kyrgyzstan", u"Kyrgyz Republic"),
(u"LA", u"LAO", u"418", u"Lao People's Democratic Republic"),
(u"LV", u"LVA", u"428", u"Latvia", u"Republic of Latvia"),
(u"LB", u"LBN", u"422", u"Lebanon", u"Lebanese Republic"),
(u"LS", u"LSO", u"426", u"Lesotho", u"Kingdom of Lesotho"),
(u"LR", u"LBR", u"430", u"Liberia", u"Republic of Liberia"),
(u"LY", u"LBY", u"434", u"Libyan Arab Jamahiriya", u"Socialist People's Libyan Arab Jamahiriya"),
(u"LI", u"LIE", u"438", u"Liechtenstein", u"Principality of Liechtenstein"),
(u"LT", u"LTU", u"440", u"Lithuania", u"Republic of Lithuania"),
(u"LU", u"LUX", u"442", u"Luxembourg", u"Grand Duchy of Luxembourg"),
(u"MO", u"MAC", u"446", u"Macao", u"Macao Special Administrative Region of China"),
(u"MK", u"MKD", u"807", u"Macedonia, Republic of", u"The Former Yugoslav Republic of Macedonia"),
(u"MG", u"MDG", u"450", u"Madagascar", u"Republic of Madagascar"),
(u"MW", u"MWI", u"454", u"Malawi", u"Republic of Malawi"),
(u"MY", u"MYS", u"458", u"Malaysia"),
(u"MV", u"MDV", u"462", u"Maldives", u"Republic of Maldives"),
(u"ML", u"MLI", u"466", u"Mali", u"Republic of Mali"),
(u"MT", u"MLT", u"470", u"Malta", u"Republic of Malta"),
(u"MH", u"MHL", u"584", u"Marshall Islands", u"Republic of the Marshall Islands"),
(u"MQ", u"MTQ", u"474", u"Martinique"),
(u"MR", u"MRT", u"478", u"Mauritania", u"Islamic Republic of Mauritania"),
(u"MU", u"MUS", u"480", u"Mauritius", u"Republic of Mauritius"),
(u"YT", u"MYT", u"175", u"Mayotte"),
(u"MX", u"MEX", u"484", u"Mexico", u"United Mexican States"),
(u"FM", u"FSM", u"583", u"Micronesia, Federated States of", u"Federated States of Micronesia"),
(u"MD", u"MDA", u"498", u"Moldova", u"Republic of Moldova"),
(u"MC", u"MCO", u"492", u"Monaco", u"Principality of Monaco"),
(u"MN", u"MNG", u"496", u"Mongolia"),
(u"ME", u"MNE", u"499", u"Montenegro", u"Montenegro"),
(u"MS", u"MSR", u"500", u"Montserrat"),
(u"MA", u"MAR", u"504", u"Morocco", u"Kingdom of Morocco"),
(u"MZ", u"MOZ", u"508", u"Mozambique", u"Republic of Mozambique"),
(u"MM", u"MMR", u"104", u"Myanmar", u"Union of Myanmar"),
(u"NA", u"NAM", u"516", u"Namibia", u"Republic of Namibia"),
(u"NR", u"NRU", u"520", u"Nauru", u"Republic of Nauru"),
(u"NP", u"NPL", u"524", u"Nepal", u"Federal Democratic Republic of Nepal"),
(u"NL", u"NLD", u"528", u"Netherlands", u"Kingdom of the Netherlands"),
(u"AN", u"ANT", u"530", u"Netherlands Antilles"),
(u"NC", u"NCL", u"540", u"New Caledonia"),
(u"NZ", u"NZL", u"554", u"New Zealand"),
(u"NI", u"NIC", u"558", u"Nicaragua", u"Republic of Nicaragua"),
(u"NE", u"NER", u"562", u"Niger", u"Republic of the Niger"),
(u"NG", u"NGA", u"566", u"Nigeria", u"Federal Republic of Nigeria"),
(u"NU", u"NIU", u"570", u"Niue", u"Republic of Niue"),
(u"NF", u"NFK", u"574", u"Norfolk Island"),
(u"MP", u"MNP", u"580", u"Northern Mariana Islands", u"Commonwealth of the Northern Mariana Islands"),
(u"NO", u"NOR", u"578", u"Norway", u"Kingdom of Norway"),
(u"OM", u"OMN", u"512", u"Oman", u"Sultanate of Oman"),
(u"PK", u"PAK", u"586", u"Pakistan", u"Islamic Republic of Pakistan"),
(u"PW", u"PLW", u"585", u"Palau", u"Republic of Palau"),
(u"PS", u"PSE", u"275", u"Palestinian Territory, Occupied", u"Occupied Palestinian Territory"),
(u"PA", u"PAN", u"591", u"Panama", u"Republic of Panama"),
(u"PG", u"PNG", u"598", u"Papua New Guinea"),
(u"PY", u"PRY", u"600", u"Paraguay", u"Republic of Paraguay"),
(u"PE", u"PER", u"604", u"Peru", u"Republic of Peru"),
(u"PH", u"PHL", u"608", u"Philippines", u"Republic of the Philippines"),
(u"PN", u"PCN", u"612", u"Pitcairn"),
(u"PL", u"POL", u"616", u"Poland", u"Republic of Poland"),
(u"PT", u"PRT", u"620", u"Portugal", u"Portuguese Republic"),
(u"PR", u"PRI", u"630", u"Puerto Rico"),
(u"QA", u"QAT", u"634", u"Qatar", u"State of Qatar"),
(u"RE", u"REU", u"638", u"Reunion"),
(u"RO", u"ROU", u"642", u"Romania"),
(u"RU", u"RUS", u"643", u"Russian Federation"),
(u"RW", u"RWA", u"646", u"Rwanda", u"Rwandese Republic"),
(u"BL", u"BLM", u"652", u"Saint Barthélemy"),
(u"SH", u"SHN", u"654", u"Saint Helena"),
(u"KN", u"KNA", u"659", u"Saint Kitts and Nevis"),
(u"LC", u"LCA", u"662", u"Saint Lucia"),
(u"MF", u"MAF", u"663", u"Saint Martin (French part)"),
(u"PM", u"SPM", u"666", u"Saint Pierre and Miquelon"),
(u"VC", u"VCT", u"670", u"Saint Vincent and the Grenadines"),
(u"WS", u"WSM", u"882", u"Samoa", u"Independent State of Samoa"),
(u"SM", u"SMR", u"674", u"San Marino", u"Republic of San Marino"),
(u"ST", u"STP", u"678", u"Sao Tome and Principe", u"Democratic Republic of Sao Tome and Principe"),
(u"SA", u"SAU", u"682", u"Saudi Arabia", u"Kingdom of Saudi Arabia"),
(u"SN", u"SEN", u"686", u"Senegal", u"Republic of Senegal"),
(u"RS", u"SRB", u"688", u"Serbia", u"Republic of Serbia"),
(u"SC", u"SYC", u"690", u"Seychelles", u"Republic of Seychelles"),
(u"SL", u"SLE", u"694", u"Sierra Leone", u"Republic of Sierra Leone"),
(u"SG", u"SGP", u"702", u"Singapore", u"Republic of Singapore"),
(u"SK", u"SVK", u"703", u"Slovakia", u"Slovak Republic"),
(u"SI", u"SVN", u"705", u"Slovenia", u"Republic of Slovenia"),
(u"SB", u"SLB", u"090", u"Solomon Islands"),
(u"SO", u"SOM", u"706", u"Somalia", u"Somali Republic"),
(u"ZA", u"ZAF", u"710", u"South Africa", u"Republic of South Africa"),
(u"GS", u"SGS", u"239", u"South Georgia and the South Sandwich Islands"),
(u"ES", u"ESP", u"724", u"Spain", u"Kingdom of Spain"),
(u"LK", u"LKA", u"144", u"Sri Lanka", u"Democratic Socialist Republic of Sri Lanka"),
(u"SD", u"SDN", u"736", u"Sudan", u"Republic of the Sudan"),
(u"SR", u"SUR", u"740", u"Suriname", u"Republic of Suriname"),
(u"SJ", u"SJM", u"744", u"Svalbard and Jan Mayen"),
(u"SZ", u"SWZ", u"748", u"Swaziland", u"Kingdom of Swaziland"),
(u"SE", u"SWE", u"752", u"Sweden", u"Kingdom of Sweden"),
(u"SY", u"SYR", u"760", u"Syrian Arab Republic"),
(u"TW", u"TWN", u"158", u"Taiwan", u"Taiwan, Province of China", u"Taiwan, Province of China"),
(u"TJ", u"TJK", u"762", u"Tajikistan", u"Republic of Tajikistan"),
(u"TZ", u"TZA", u"834", u"Tanzania, United Republic of", u"United Republic of Tanzania"),
(u"TH", u"THA", u"764", u"Thailand", u"Kingdom of Thailand"),
(u"TL", u"TLS", u"626", u"Timor-Leste", u"Democratic Republic of Timor-Leste"),
(u"TG", u"TGO", u"768", u"Togo", u"Togolese Republic"),
(u"TK", u"TKL", u"772", u"Tokelau"),
(u"TO", u"TON", u"776", u"Tonga", u"Kingdom of Tonga"),
(u"TT", u"TTO", u"780", u"Trinidad and Tobago", u"Republic of Trinidad and Tobago"),
(u"TN", u"TUN", u"788", u"Tunisia", u"Republic of Tunisia"),
(u"TR", u"TUR", u"792", u"Turkey", u"Republic of Turkey"),
(u"TM", u"TKM", u"795", u"Turkmenistan"),
(u"TC", u"TCA", u"796", u"Turks and Caicos Islands"),
(u"TV", u"TUV", u"798", u"Tuvalu"),
(u"UG", u"UGA", u"800", u"Uganda", u"Republic of Uganda"),
(u"UA", u"UKR", u"804", u"Ukraine"),
(u"AE", u"ARE", u"784", u"United Arab Emirates"),
(u"GB", u"GBR", u"826", u"United Kingdom", u"United Kingdom of Great Britain and Northern Ireland"),
(u"US", u"USA", u"840", u"United States", u"United States of America"),
(u"UM", u"UMI", u"581", u"United States Minor Outlying Islands"),
(u"UY", u"URY", u"858", u"Uruguay", u"Eastern Republic of Uruguay"),
(u"UZ", u"UZB", u"860", u"Uzbekistan", u"Republic of Uzbekistan"),
(u"VU", u"VUT", u"548", u"Vanuatu", u"Republic of Vanuatu"),
(u"VE", u"VEN", u"862", u"Venezuela", u"Bolivarian Republic of Venezuela"),
(u"VN", u"VNM", u"704", u"Viet Nam", u"Socialist Republic of Viet Nam"),
(u"VG", u"VGB", u"092", u"Virgin Islands, British", u"British Virgin Islands"),
(u"VI", u"VIR", u"850", u"Virgin Islands, U.S.", u"Virgin Islands of the United States"),
(u"WF", u"WLF", u"876", u"Wallis and Futuna"),
(u"EH", u"ESH", u"732", u"Western Sahara"),
(u"YE", u"YEM", u"887", u"Yemen", u"Republic of Yemen"),
(u"ZM", u"ZMB", u"894", u"Zambia", u"Republic of Zambia"),
(u"ZW", u"ZWE", u"716", u"Zimbabwe", u"Republic of Zimbabwe"),
)
_cl = []

def GetConf(code):
    """
    Load country by code
    """
    code = code.upper()
    if len(code)==2:
        for c in countries:
            if c[0] == code:
                return _GetDict(c)
    if len(code)==3:
        for c in countries:
            if c[1] == code:
                return _GetDict(c)
    return {}


def GetCountries():
    """
    load codelist of countries and cache
    """
    if len(_cl) == 0:
        for c in countries:
            _cl.append({"id": c[1], "name": c[3]})
    return _cl


def _GetDict(c):
    d = {"code": c[1], "code2": c[0], "numeric": c[2], "name": c[3]}
    if len(c) > 4:
        d["name2"] = c[4]
    return d