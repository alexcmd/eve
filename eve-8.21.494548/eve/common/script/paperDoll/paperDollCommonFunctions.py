#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/paperDoll/paperDollCommonFunctions.py
import sys
import blue
import yaml
import util
import telemetry
import log
import stackless

def WaitForAll(iterable, condition):
    while any(map(condition, iterable)):
        Yield(frameNice=False)

    BeFrameNice()


def Yield(frameNice = True, ms = 15):
    try:
        if not stackless.current.is_main:
            blue.synchro.Yield()
            if frameNice:
                return BeFrameNice(ms)
        else:
            return False
    except:
        raise 


def BeFrameNice(ms = 15):
    try:
        if not stackless.current.is_main:
            if ms < 1.0:
                ms = 1.0
            while blue.os.GetWallclockTimeNow() - blue.os.GetWallclockTime() > ms * 10000:
                blue.synchro.Yield()
                ms *= 1.02

            return True
        return False
    except:
        raise 


def AddToDictList(d, key, item):
    l = d.get(key, [])
    l.append(item)
    d[key] = l


def GetFromDictList(d, key):
    l = d.get(key, [])
    if type(l) != list:
        return []
    return l


@telemetry.ZONE_FUNCTION
def NastyYamlLoad(yamlStr):
    import paperDoll as PD
    sys.modules[PD.__name__] = PD
    instance = None
    try:
        blue.statistics.EnterZone('yaml.load')
        instance = yaml.load(yamlStr, Loader=yaml.CLoader)
    except Exception:
        log.LogError('PaperDoll: Yaml parsing failed for data', yamlStr)
    finally:
        blue.statistics.LeaveZone()
        del sys.modules[PD.__name__]

    return instance


exports = util.AutoExports('paperDoll', globals())