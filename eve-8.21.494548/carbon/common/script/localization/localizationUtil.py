#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/localization/localizationUtil.py
import localization
import localizationInternalUtil
import telemetry
import const
import util
import uiutil
import re
import mathUtil
import eveLocalization
import stacklesslib.util
TIME_CATEGORY_YEAR = 'year'
TIME_CATEGORY_MONTH = 'month'
TIME_CATEGORY_DAY = 'day'
TIME_CATEGORY_HOUR = 'hour'
TIME_CATEGORY_MINUTE = 'minute'
TIME_CATEGORY_SECOND = 'second'
TIME_CATEGORY_MILLISECOND = 'millisecond'
QUANTITY_TIME_SHORT_MAP = {2: '/Carbon/UI/Common/DateTimeQuantity/DateTimeShort2Elements',
 3: '/Carbon/UI/Common/DateTimeQuantity/DateTimeShort3Elements',
 4: '/Carbon/UI/Common/DateTimeQuantity/DateTimeShort4Elements',
 5: '/Carbon/UI/Common/DateTimeQuantity/DateTimeShort5Elements',
 6: '/Carbon/UI/Common/DateTimeQuantity/DateTimeShort6Elements',
 7: '/Carbon/UI/Common/DateTimeQuantity/DateTimeShort7Elements'}
QUANTITY_TIME_SHORT_WRITTEN_MAP = {2: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/DateTimeShortWritten2Elements',
 3: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/DateTimeShortWritten3Elements',
 4: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/DateTimeShortWritten4Elements',
 5: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/DateTimeShortWritten5Elements',
 6: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/DateTimeShortWritten6Elements',
 7: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/DateTimeShortWritten7Elements'}
SMALL_WRITTEN_QUANTITY_TIME_MAP = {TIME_CATEGORY_YEAR: '/Carbon/UI/Common/WrittenDateTimeQuantity/LessThanOneYear',
 TIME_CATEGORY_MONTH: '/Carbon/UI/Common/WrittenDateTimeQuantity/LessThanOneMonth',
 TIME_CATEGORY_DAY: '/Carbon/UI/Common/WrittenDateTimeQuantity/LessThanOneDay',
 TIME_CATEGORY_HOUR: '/Carbon/UI/Common/WrittenDateTimeQuantity/LessThanOneHour',
 TIME_CATEGORY_MINUTE: '/Carbon/UI/Common/WrittenDateTimeQuantity/LessThanOneMinute',
 TIME_CATEGORY_SECOND: '/Carbon/UI/Common/WrittenDateTimeQuantity/LessThanOneSecond',
 TIME_CATEGORY_MILLISECOND: '/Carbon/UI/Common/WrittenDateTimeQuantity/LessThanOneMillisecond'}
TIME_CATEGORY = {TIME_CATEGORY_YEAR: 7,
 TIME_CATEGORY_MONTH: 6,
 TIME_CATEGORY_DAY: 5,
 TIME_CATEGORY_HOUR: 4,
 TIME_CATEGORY_MINUTE: 3,
 TIME_CATEGORY_SECOND: 2,
 TIME_CATEGORY_MILLISECOND: 1}
QUANTITY_TIME_SHORT_WRITTEN_UNITS_MAP = {TIME_CATEGORY[TIME_CATEGORY_YEAR]: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/Year',
 TIME_CATEGORY[TIME_CATEGORY_MONTH]: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/Month',
 TIME_CATEGORY[TIME_CATEGORY_DAY]: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/Day',
 TIME_CATEGORY[TIME_CATEGORY_HOUR]: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/Hour',
 TIME_CATEGORY[TIME_CATEGORY_MINUTE]: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/Minute',
 TIME_CATEGORY[TIME_CATEGORY_SECOND]: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/Second',
 TIME_CATEGORY[TIME_CATEGORY_MILLISECOND]: '/Carbon/UI/Common/WrittenDateTimeQuantityShort/Millisecond'}
TIME_INTERVAL_UNITS_VALUE_MAP = {TIME_CATEGORY_YEAR: const.YEAR365,
 TIME_CATEGORY_MONTH: const.MONTH30,
 TIME_CATEGORY_DAY: const.DAY,
 TIME_CATEGORY_HOUR: const.HOUR,
 TIME_CATEGORY_MINUTE: const.MIN,
 TIME_CATEGORY_SECOND: const.SEC,
 TIME_CATEGORY_MILLISECOND: const.MSEC}
IMPORTANT_NAME_AUTO_OVERRIDE = 1
IMPORTANT_NAME_MANUAL_OVERRIDE = 2
IMPORTANT_NAME_CATEGORY = {IMPORTANT_NAME_AUTO_OVERRIDE: 'Automatic override',
 IMPORTANT_NAME_MANUAL_OVERRIDE: 'Manual override'}

class LocalizationSafeString(unicode):
    pass


COLOR_HARDCODED = mathUtil.LtoI(2868838655L)
COLOR_NESTED = mathUtil.LtoI(2852192255L)
COLOR_ERROR = mathUtil.LtoI(2868838400L)
LOCALIZEDREGEX = re.compile('(<.*?>)')
WHITELIST = ['<t>',
 '<br>',
 '<b>',
 '</b>',
 '<i>',
 '</i>',
 '<center>',
 '<right>',
 '<left>']
WHITELISTREGEX = re.compile('(\\r\\n|<br>|<t>|<center>|</center>|<right>|</right>|<left>|</left>|<color.*?>|</color>|<b>|</b>|<i>|</i>|<url.*?>|</url>|<a href.*?>|</a>)')
_cachedLanguageId = None
_languageCodesDict = None
_localizationTLS = stacklesslib.util.local()

def ResetTLSMarker():
    _localizationTLS.wasLocalized = False


def WasCurrentLocalized():
    return _localizationTLS.wasLocalized


@telemetry.ZONE_FUNCTION
def CheckForLocalizationErrors(text):
    parts = LOCALIZEDREGEX.split(text)

    def GetHashFromTag(tag):
        hashIndex = tag.find('textHash=')
        if hashIndex != -1:
            searchHash = tag[hashIndex + 9:]
            hashString = ''
            for sh in searchHash:
                if sh.isdigit() or sh == '-':
                    hashString += sh
                else:
                    break

            return hashString

    def FindLocalizedText(fromIndex):
        retText = ''
        localizedTagCount = 0
        for tagOrText in parts[fromIndex:]:
            if tagOrText.startswith('<localized'):
                localizedTagCount += 1
            elif tagOrText.startswith('</localized'):
                if localizedTagCount:
                    localizedTagCount -= 1
                else:
                    break
            else:
                retText += tagOrText

        return retText

    returnText = ''
    tagStack = []
    processedLocTag = False
    localizationError = False
    for partIndex, each in enumerate(parts):
        if not each:
            continue
        if each.startswith('<localized'):
            if len(tagStack) == 0 and processedLocTag:
                localizationError = True
            hashString = GetHashFromTag(each)
            inBetween = FindLocalizedText(partIndex + 1)
            hashBetween = unicode(hash(inBetween))
            if hashString != hashBetween:
                each = each.replace('>', ' hashError=%s>' % hashBetween)
            tagStack.append(each)
            returnText += each
        elif each.startswith('</localized'):
            processedLocTag = True
            returnText += each
            if len(tagStack):
                tagStack.pop()
            else:
                localizationError = True
        elif not WHITELISTREGEX.subn('', each)[0] or len(tagStack):
            returnText += each
            if len(tagStack) == 0 and (each == '<br>' or each == '<t>'):
                processedLocTag = False
        else:
            if len(tagStack) == 0:
                localizationError = True
            returnText += each

    if len(tagStack):
        localizationError = True
    return (returnText, localizationError)


def SetHardcodedStringDetection(isEnabled):
    localization.hardcodedStringDetectionIsEnabled = isEnabled
    prefs.showHardcodedStrings = 1 if isEnabled else 0


def IsHardcodedStringDetectionEnabled():
    return getattr(localization, 'hardcodedStringDetectionIsEnabled', False)


def IsWrapModeOn():
    return localizationInternalUtil.IsWrapModeOn()


def SetPseudolocalization(isEnabled):
    localization.pseudolocalizationIsEnabled = isEnabled
    prefs.pseudolocalizationIsEnabled = 1 if isEnabled else 0


def IsPseudolocalizationEnabled():
    return getattr(localization, 'pseudolocalizationIsEnabled', False)


def GetLanguageIDClient():
    global _cachedLanguageId
    if _cachedLanguageId:
        return _cachedLanguageId
    try:
        _cachedLanguageId = localizationInternalUtil.ConvertToLanguageSet('MLS', 'languageID', prefs.languageID) or prefs.languageID
        return _cachedLanguageId
    except (KeyError, AttributeError):
        return localization.LOCALE_SHORT_ENGLISH


def GetLanguageID():
    try:
        ret = None
        try:
            ls = GetLocalStorage()
            ret = ls['languageID']
            _localizationTLS.wasLocalized = True
        except KeyError:
            pass

        if ret is None:
            ret = localizationInternalUtil.ConvertToLanguageSet('MLS', 'languageID', session.languageID) or localization.LOCALE_SHORT_ENGLISH
        return ret
    except (KeyError, AttributeError):
        return localization.LOCALE_SHORT_ENGLISH


if boot.role == 'client':
    GetLanguageID = GetLanguageIDClient

def ClearLanguageID():
    global _cachedLanguageId
    _cachedLanguageId = None


@telemetry.ZONE_FUNCTION
def ConvertToLanguageSet(fromSetName, toSetName, fromLanguageID):
    return localizationInternalUtil.ConvertToLanguageSet(fromSetName, toSetName, fromLanguageID)


@telemetry.ZONE_FUNCTION
def FormatNumeric(value, useGrouping = False, decimalPlaces = None, leadingZeroes = None):
    result = eveLocalization.FormatNumeric(value, GetLanguageID(), useGrouping=useGrouping, decimalPlaces=decimalPlaces, leadingZeroes=leadingZeroes)
    return localizationInternalUtil.PrepareLocalizationSafeString(result, messageID='numeric')


@telemetry.ZONE_FUNCTION
def FormatTimeIntervalShort(value, showFrom = 'year', showTo = 'second'):
    timeParts = _FormatTimeIntervalGetParts(value, showFrom, showTo)[:-1]
    startShowing = TIME_CATEGORY[showFrom]
    stopShowing = TIME_CATEGORY[showTo]
    usableParts = timeParts[TIME_CATEGORY['year'] - startShowing:TIME_CATEGORY['year'] - stopShowing + 1]
    kwargs = {}
    for i, part in enumerate(usableParts):
        key = 'value%s' % (i + 1)
        if i == len(usableParts) - 1 and showTo == 'millisecond':
            kwargs[key] = FormatNumeric(part, leadingZeroes=3)
        else:
            kwargs[key] = FormatNumeric(part, leadingZeroes=2)

    if len(usableParts) == 1:
        return kwargs['value1']
    else:
        return localization.GetByLabel(QUANTITY_TIME_SHORT_MAP[len(usableParts)], **kwargs)


@telemetry.ZONE_FUNCTION
def FormatTimeIntervalShortWritten(value, showFrom = 'year', showTo = 'second'):
    timeParts = _FormatTimeIntervalGetParts(value, showFrom, showTo, roundUp=True)
    stopShowing = TIME_CATEGORY[showTo]
    kwargs = {}
    timeParts = timeParts[:-1]
    for i, part in enumerate(timeParts):
        key = 'value%s' % (len(kwargs) + 1)
        if part > 0 or TIME_CATEGORY['year'] - i == stopShowing:
            kwargs[key] = localization.GetByLabel(QUANTITY_TIME_SHORT_WRITTEN_UNITS_MAP[TIME_CATEGORY['year'] - i], value=part)

    length = len(kwargs)
    if length == 1:
        return kwargs['value1']
    else:
        return localization.GetByLabel(QUANTITY_TIME_SHORT_WRITTEN_MAP[length], **kwargs)


@telemetry.ZONE_FUNCTION
def FormatTimeIntervalWritten(value, showFrom = 'year', showTo = 'second', languageID = None):
    timeParts = _FormatTimeIntervalGetParts(value, showFrom, showTo)
    if timeParts:
        year, month, day, hour, minute, second, millisecond, remainder = timeParts
    else:
        return None
    timeList = []
    if year > 0:
        timeList.append(localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Year', languageID=languageID, years=year))
    if month > 0:
        timeList.append(localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Month', languageID=languageID, months=month))
    if day > 0:
        timeList.append(localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Day', languageID=languageID, days=day))
    if hour > 0:
        timeList.append(localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Hour', languageID=languageID, hours=hour))
    if minute > 0:
        timeList.append(localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Minute', languageID=languageID, minutes=minute))
    if second > 0:
        timeList.append(localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Second', languageID=languageID, seconds=second))
    if millisecond > 0:
        timeList.append(localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Millisecond', languageID=languageID, milliseconds=millisecond))
    length = len(timeList)
    if length == 0:
        dateTimeQuantityLabel = SMALL_WRITTEN_QUANTITY_TIME_MAP[showTo]
        return localization.GetByLabel(dateTimeQuantityLabel, languageID=languageID)
    elif length == 1:
        return timeList[0]
    else:
        firstPart = FormatGenericList(timeList[:-1], languageID=languageID)
        lastPart = timeList[-1]
        return localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/ListForm', languageID=languageID, firstPart=firstPart, secondPart=lastPart)


@telemetry.ZONE_FUNCTION
def _FormatTimeIntervalGetParts(value, showFrom, showTo, roundUp = False):
    if value < 0:
        raise ValueError('Time value must be a positive number. value = %s' % value)
    if isinstance(value, float):
        import log
        log.LogTraceback('float value passed in for time interval')
        value = long(value) * const.SEC
    if not isinstance(value, long):
        raise ValueError('TimeInterval accepts blue time (long) or python time (float), recieved ', type(value).__name__, '.')
    startShowing = TIME_CATEGORY[showFrom]
    stopShowing = TIME_CATEGORY[showTo]
    if stopShowing > startShowing:
        raise ValueError('The from/to pair %s/%s is not a valid combination for TimeInterval.' % (showFrom, showTo))
    year = month = day = hour = minute = second = millisecond = remainder = 0
    if roundUp:
        roundUnit = TIME_INTERVAL_UNITS_VALUE_MAP[showTo]
        value += roundUnit if value % roundUnit > 0 else 0
    if startShowing >= TIME_CATEGORY['year'] and stopShowing <= TIME_CATEGORY['year']:
        year = value / const.YEAR365
        value -= const.YEAR365 * year
    if startShowing >= TIME_CATEGORY['month'] and stopShowing <= TIME_CATEGORY['month']:
        month = value / const.MONTH30
        value -= const.MONTH30 * month
    if startShowing >= TIME_CATEGORY['day'] and stopShowing <= TIME_CATEGORY['day']:
        day = value / const.DAY
        value -= const.DAY * day
    if startShowing >= TIME_CATEGORY['hour'] and stopShowing <= TIME_CATEGORY['hour']:
        hour = value / const.HOUR
        value -= const.HOUR * hour
    if startShowing >= TIME_CATEGORY['minute'] and stopShowing <= TIME_CATEGORY['minute']:
        minute = value / const.MIN
        value -= const.MIN * minute
    if startShowing >= TIME_CATEGORY['second'] and stopShowing <= TIME_CATEGORY['second']:
        second = value / const.SEC
        value -= const.SEC * second
    if startShowing >= TIME_CATEGORY['millisecond'] and stopShowing <= TIME_CATEGORY['millisecond']:
        millisecond = value / const.MSEC
        value -= const.MSEC * millisecond
    remainder = value
    if roundUp:
        remainder = 0
    return (year,
     month,
     day,
     hour,
     minute,
     second,
     millisecond,
     remainder)


@telemetry.ZONE_FUNCTION
def FormatGenericList(iterable, languageID = None):
    if languageID is not None:
        languageID = localizationInternalUtil.StandardizeLanguageID(languageID)
    if languageID is None:
        languageID = GetLanguageID()
    delimiterDict = {'en-us': u', ',
     'ja': u'\u3001',
     'zh-cn': u'\uff0c'}
    stringList = [ unicode(each) for each in iterable ]
    delimeter = delimiterDict.get(languageID, delimiterDict['en-us'])
    return localizationInternalUtil.PrepareLocalizationSafeString(delimeter.join(stringList), messageID='genericlist')


@telemetry.ZONE_FUNCTION
def Sort(iterable, cmp = None, key = lambda x: x, reverse = False, languageID = None):
    if cmp:
        raise ValueError("Passing a compare function into Sort defeats the purpose of using a language-aware sort.  You probably want to use the 'key' parameter instead.")
    languageID = languageID or localizationInternalUtil.StandardizeLanguageID(languageID) or GetLanguageID()
    collator = eveLocalization.Collator()
    collator.locale = str(languageID)

    def caseSensitiveSubsort(left, right):
        if left.lower() == right.lower():
            return collator.Compare(unicode(right), unicode(left))
        return collator.Compare(unicode(left.lower()), unicode(right.lower()))

    if all([ isinstance(key(each), (int, type(None))) for each in iterable ]):

        def getPronunciation(messageID):
            if not messageID:
                return ''
            ret = ''
            try:
                ret = localization.GetMetaData(messageID, 'pronounciation', languageID=languageID)
            except KeyError:
                ret = localization.GetByMessageID(messageID, languageID)

            return ret

        return sorted(iterable, cmp=caseSensitiveSubsort, key=lambda x: uiutil.StripTags(getPronunciation(key(x))), reverse=reverse)
    return sorted(iterable, cmp=caseSensitiveSubsort, key=lambda x: uiutil.StripTags(key(x)), reverse=reverse)


def GetEnabledLanguages():
    global _languageCodesDict
    if _languageCodesDict is None:
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        resultSet = dbzlocalization.Languages_Select()
        _languageCodesDict = localizationInternalUtil.MakeRowDicts(resultSet, resultSet.columns, localization.COLUMN_LANGUAGE_ID)
    return _languageCodesDict


def GetLocaleIDFromLocaleShortCode(languageID):
    languageCodesDict = GetEnabledLanguages()
    if languageCodesDict and languageID in languageCodesDict:
        return languageCodesDict[languageID][localization.COLUMN_LANGUAGE_KEY]
    import log
    log.LogError('Get an apparently invalid languageID of', languageID, ', which is not in ', languageCodesDict.keys(), 'calling code is probably about to break!')


def GetDisplayLanguageName(inLanguageID, languageID):
    mlsToDisplayNameLabel = {'JA': localization.GetByLabel('UI/SystemMenu/Language/LanguageJapanese'),
     'DE': localization.GetByLabel('UI/SystemMenu/Language/LanguageGerman'),
     'EN': localization.GetByLabel('UI/SystemMenu/Language/LanguageEnglish'),
     'RU': localization.GetByLabel('UI/SystemMenu/Language/LanguageRussian'),
     'ZH': localization.GetByLabel('UI/SystemMenu/Language/LanguageChinese')}
    langName = ''
    convertedID = ConvertToLanguageSet('languageID', 'MLS', languageID)
    if convertedID:
        langName = mlsToDisplayNameLabel[convertedID]
    return langName


def IsSearchTextIdeographic(languageID, textString):
    languageID = localizationInternalUtil.StandardizeLanguageID(languageID)
    if languageID in (localization.LOCALE_SHORT_JAPANESE, localization.LOCALE_SHORT_CHINESE):
        try:
            textString.encode('ascii')
        except UnicodeEncodeError:
            return True

    return False


class LocalizationSystemError(Exception):
    pass


exports = util.AutoExports('localizationUtil', locals())