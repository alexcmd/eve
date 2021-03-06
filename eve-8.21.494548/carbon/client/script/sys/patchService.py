#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/sys/patchService.py
import blue
import service
import sys
import os
import urllib
import urlparse
from hashlib import sha1
import uiconst
import util
import uthread
import base64
from nasty import nasty
import log
import urllib2
import appUtils
import localization
import bluepy
import trinity
WIN_VERSIONS = {(2, 4, 0): 'Windows NT 4',
 (2, 5, 0): 'Windows 2000',
 (2, 5, 1): 'Windows XP',
 (2, 5, 2): 'Windows XP',
 (2, 6, 0): 'Windows Vista',
 (2, 6, 1): 'Windows 7',
 (2, 6, 2): 'Windows 8'}
DEBUG_LEVEL = 2
FILE_CHUNK_SIZE = 131072
AFFILIATE_FILE_PATH = blue.paths.ResolvePathForWriting(u'root:/affiliate.txt')

def SetDownloadProgress(progress, msg = None, callback = None):
    hdr = localization.GetByLabel('/Carbon/UI/Patch/Downloading')
    m = msg
    if m == None:
        m = hdr
    try:
        sm.GetService('loading').ProgressWnd(hdr, m, progress, 1000, 0, callback, useMorph=0, autoTick=0)
    except:
        sys.exc_clear()


def SetProgress(progress, hdr, msg = None, callback = None):
    try:
        sm.GetService('loading').ProgressWnd(hdr, msg, progress, 1000, 0, callback, useMorph=0, autoTick=0)
    except:
        sys.exc_clear()


class coreURLOpener(urllib.FancyURLopener):

    def __init__(self, *args):
        versionInfo = os.sys.getwindowsversion()
        win_version = ''
        try:
            win_version = WIN_VERSIONS[versionInfo[3], versionInfo[0], versionInfo[1]]
        except:
            sys.exc_clear()
            try:
                win_version = 'Windows %s.%s' % (versionInfo[0], versionInfo[1])
            except:
                sys.exc_clear()

        from appPatch import appName
        self.version = '%s-%s PatchService (%s %s)' % (appName,
         boot.build,
         win_version,
         versionInfo)
        apply(urllib.FancyURLopener.__init__, (self,) + args)

    def http_error_206(self, url, fp, errcode, errmsg, headers, data = None):
        pass

    def open(self, fullurl, data = None):
        return urllib.FancyURLopener.open(self, fullurl.replace(' ', '%20'), data)

    def http_error_404(self, url, fp, errcode, errmsg, headers, data = None):
        raise RuntimeError('url %s not found' % url)

    def http_error_500(self, url, fp, errcode, errmsg, headers, data = None):
        raise RuntimeError('Internal Server Error')


class HttpFileGrabber():

    def __init__(self, url, filename, statusCallback = None):
        self.url = 'http://' + url.encode('ascii')
        self.localFile = os.path.join(blue.paths.ResolvePath(u'cache:/'), filename.split('/')[-1])
        self.filename = filename
        self.statusCallback = statusCallback
        self.headers = None
        self.file = None
        self.patchFileSize = 0
        self.fileSize = 0
        import log
        self.logChannel = log.GetChannel('svc.patchGrabber')
        self.cancel = 0

    def LogInfo(self, *args, **keywords):
        if self.logChannel.IsOpen(1):
            try:
                self.logChannel.Log(' '.join(map(strx, args)), 1, keywords.get('backtrace', 1))
            except TypeError:
                self.logChannel.Log('[X]'.join(map(strx, args)).replace('\x00', '\\0'), 1, keywords.get('backtrace', 1))
                sys.exc_clear()

    def Grab(self):
        try:
            self.LogInfo('Starting file download of %s...' % urlparse.urljoin(self.url, self.filename))
            myUrlClass = coreURLOpener()
            if os.path.exists(self.localFile):
                self.file = file(self.localFile, 'ab')
                self.fileSize = os.path.getsize(self.localFile)
                myUrlClass.addheader('Range', 'bytes=%d-' % self.fileSize)
                self.LogInfo('file has been partially downloaded, %d bytes already read' % self.fileSize)
            else:
                self.file = file(self.localFile, 'wb')
            patch = myUrlClass.open(urlparse.urljoin(self.url, self.filename))
            s = 0
            if patch.headers.has_key('Content-Length'):
                s = int(patch.headers['Content-Length'])
                if s == self.fileSize:
                    self.LogInfo('think I have already downloaded the patch file')
                    return
            self.patchFileSize = self.fileSize + s
            self.LogInfo('%d : %d : %d' % (s, self.patchFileSize, self.fileSize))
            numBytes = self.fileSize
            while numBytes < self.patchFileSize:
                data = patch.read(FILE_CHUNK_SIZE)
                if not data:
                    break
                self.file.write(data)
                numBytes += len(data)
                if self.cancel:
                    if DEBUG_LEVEL:
                        self.LogInfo('Download cancelled by user')
                    raise RuntimeError('Download cancelled')
                if self.statusCallback:
                    self.statusCallback(self.patchFileSize, numBytes)

        finally:
            if DEBUG_LEVEL > 1:
                self.LogInfo('Closing file and connection')
            if self.file:
                self.file.close()
                del self.file
            myUrlClass.close()
            del myUrlClass

    def Cancel(self):
        self.cancel = 1


class PatchService(service.Service):
    __exportedcalls__ = {'Patch': []}
    __guid__ = 'svc.patch'
    __notifyevents__ = []
    __startupdependencies__ = ['settings']

    def __init__(self):
        service.Service.__init__(self)
        self.downloading = 0
        self.patchChecksum = ''
        self.patchFileName = ''
        self.patchGrabber = None
        self.cancel = 0
        self.userName = ''
        self.queryString = ''
        self.verifyFailedNum = 0
        self.affiliateID = None
        patchInfoHost = [ arg.split(':', 1)[1] for arg in blue.pyos.GetArg() if arg.lower().startswith('/patchinfourl:') ]
        if patchInfoHost:
            self.patchInfoUrl = patchInfoHost[0]
            if not self.patchInfoUrl.endswith('/'):
                self.patchInfoUrl += '/'
        else:
            try:
                from appPatch import patchInfoURLs
                self.patchInfoUrl = prefs.GetValue('patchInfoUrl', patchInfoURLs[boot.region])
            except ImportError as e:
                self.LogError('Could not import patchInfoURLs from appPatch module')
                self.patchInfoUrl = prefs.GetValue('patchInfoUrl', '')
                sys.exc_clear()

        self.cntUpgradeStatusSemaphore = uthread.Semaphore()
        self.cntDoNotAskAgain = False
        self.patchInfoResponses = {}
        self.upgradeInfo = None
        self.upgradeOffered = None

    def Run(self, memStream = None):
        if prefs.GetValue('bitsCancelled', 0):
            return
        prefs.SetValue('bitsCancelled', 1)
        try:
            if not blue.win32.IsTransgaming() and blue.win32.GetWindowsServiceStatus('BITS') != 4:
                self.BitsAction('cancel')
        except Exception as e:
            sys.exc_clear()

    def GetClientAffiliateID(self):
        if self.affiliateID is None:
            self.affiliateID = ''
            try:
                if os.path.exists(AFFILIATE_FILE_PATH):
                    affiliateFile = blue.ResFile()
                    if affiliateFile.Open(AFFILIATE_FILE_PATH):
                        self.affiliateID = filter(lambda x: x in '0123456789', affiliateFile.Read())
            except Exception as e:
                self.LogError('Error reading affiliate ID: %s' % e)
                sys.exc_clear()

        return self.affiliateID

    def BitsAction(self, action):
        try:
            self.LogInfo('BITS: Calling ', action, '...')
            blue.win32.InitializeCom()
            ret = blue.win32.BitsAction(u'EveContentUpgrade', unicode(action))
            self.LogInfo('Success! return value:', ret)
            return ret
        except Exception as e:
            self.LogError('Error calling BitsAction %s. %s' % (action, e))
            sys.exc_clear()
        finally:
            try:
                blue.win32.UnInitializeCom()
            except Exception as e:
                self.LogError('Error calling UnInitializeCom: %s' % e)
                sys.exc_clear()

    def GetFileHash(self, filepath, showProgress = True):
        if not hasattr(self, 'fileHashCache'):
            self.fileHashCache = {}
        filesha = sha1()
        filesha.update(buffer(filepath))
        filestat = os.stat(filepath)
        filesha.update(str(filestat.st_mtime))
        size = filestat.st_size
        filesha.update(str(size))
        fileCacheKey = filesha.hexdigest()
        if self.fileHashCache.has_key(fileCacheKey):
            return self.fileHashCache[fileCacheKey]
        f = open(filepath, 'rb')
        s = sha1()
        readBytes = 8192
        totalBytes = 0
        if showProgress:
            SetProgress(0, localization.GetByLabel('/Carbon/UI/Patch/Checking'), '', None)
        loopIndex = 0
        while readBytes:
            readString = f.read(readBytes)
            s.update(readString)
            readBytes = len(readString)
            totalBytes += readBytes
            loopIndex += 1
            if showProgress and loopIndex % 5000 == 0:
                progress = float(min(1000, int(float(totalBytes) / float(size) * 1000)))
                txt = localization.GetByLabel('/Carbon/UI/Patch/DownloadProgress', progress=progress / 10.0, total=size / 1024)
                SetProgress(progress, localization.GetByLabel('/Carbon/UI/Patch/Checking'), txt, None)
            blue.pyos.BeNice()

        f.close()
        if showProgress:
            SetProgress(1000, localization.GetByLabel('/Carbon/UI/Patch/Checking'), '', None)
        checksum = s.hexdigest()
        self.fileHashCache[fileCacheKey] = checksum
        return checksum

    def DoManualPatch(self, msg, param):
        if uicore.Message(msg, {'text': param}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            msg = '%spatches.asp%s&e=%s' % (self.patchInfoUrl, self.queryString, param)
            blue.os.ShellExecute(msg)
            bluepy.Terminate('Manual patch close')

    def GetWebRequestParameters(self):
        details = {}
        try:
            details['n'] = boot.build
            details['s'] = util.GetServerName()
            details['u'] = settings.public.ui.Get('username', '')
            details['language_id'] = prefs.GetValue('languageID', 'EN')
            details['edition'] = getattr(boot, 'edition', 'classic')
            details['protocol'] = 2
            details['intended_platform'] = 'win'
            details['client_bitcount'] = 32
            details['client_fullversion'] = '%s.%s' % (boot.keyval['version'].split('=', 1)[1], boot.build)
            if not blue.win32.IsTransgaming():
                versionEx = blue.win32.GetVersionEx()
                details['actual_platform'] = 'win'
                details['platform_version'] = str(blue.os.osMajor) + '.' + str(blue.os.osMinor)
                details['platform_extra'] = str(versionEx.get('wServicePackMajor', 0))
                if versionEx.get('wProductType', 1) > 1:
                    details['platform_type'] = 'server'
                else:
                    details['platform_type'] = ['workstation', 'desktop'][versionEx.get('wSuiteMask', 512) & 512 > 0]
                if blue.win32.GetNativeSystemInfo().get('ProcessorArchitecture', '') == 'PROCESSOR_ARCHITECTURE_AMD64':
                    details['platform_bitcount'] = 64
                else:
                    details['platform_bitcount'] = 32
            else:
                versionEx = blue.win32.TGGetSystemInfo()
                details['actual_platform'] = ['mac', 'linux'][blue.win32.TGGetOS() == 'Linux']
                details['platform_type'] = versionEx.get('platform_type', 'desktop')
                details['platform_version'] = str(versionEx.get('platform_major_version', 0)) + '.' + str(versionEx.get('platform_minor_version', 0))
                details['platform_extra'] = versionEx.get('platform_extra', '0')
                details['platform_bitcount'] = versionEx.get('platform_bitcount', 32)
            cardName = ''
            ident = trinity.adapters.GetAdapterInfo(trinity.adapters.DEFAULT_ADAPTER)
            cardName = str(ident.description)
            cardName = cardName[0:64]
            details['card_name'] = cardName
            details['affiliate_id'] = self.GetClientAffiliateID()
        except:
            log.LogException(toAlertSvc=0)
            sys.exc_clear()

        queryString = urllib.urlencode(details)
        return queryString

    def GetPatchInfo(self, userName = '', server = None):
        import hashlib
        hasher = hashlib.md5()
        hasher.update(userName)
        hasher.update(str(server))
        hasher.update(str(self.patchInfoUrl))
        parameterHash = hasher.hexdigest()
        if parameterHash in self.patchInfoResponses:
            return self.patchInfoResponses[parameterHash]
        if server == None:
            server = util.GetServerName()
        isTransgaming = blue.win32.IsTransgaming()
        details = util.KeyVal()
        details.protocolVersion = 2
        details.intendedPlatform = 'win'
        details.clientBitCount = 32
        details.clientFullVersion = '%s.%s' % (boot.keyval['version'].split('=', 1)[1], boot.build)
        if not isTransgaming:
            versionEx = blue.win32.GetVersionEx()
            details.actualPlatform = 'win'
            details.platformVersion = str(blue.os.osMajor) + '.' + str(blue.os.osMinor)
            details.platformExtra = str(versionEx.get('wServicePackMajor', 0))
            if versionEx.get('wProductType', 1) > 1:
                details.platformType = 'server'
            else:
                details.platformType = ['workstation', 'desktop'][versionEx.get('wSuiteMask', 512) & 512 > 0]
            if blue.win32.GetNativeSystemInfo().get('ProcessorArchitecture', '') == 'PROCESSOR_ARCHITECTURE_AMD64':
                details.platformBitCount = 64
            else:
                details.platformBitCount = 32
        else:
            versionEx = blue.win32.TGGetSystemInfo()
            details.actualPlatform = ['mac', 'linux'][blue.win32.TGGetOS() == 'Linux']
            details.platformType = versionEx.get('platform_type', 'desktop')
            details.platformVersion = str(versionEx.get('platform_major_version', 0)) + '.' + str(versionEx.get('platform_minor_version', 0))
            details.platformExtra = versionEx.get('platform_extra', '0')
            details.platformBitCount = versionEx.get('platform_bitcount', 32)
        self.clientVersion = int(boot.build)
        self.userName = userName
        if hasattr(boot, 'edition'):
            self.edition = boot.edition
        else:
            self.edition = 'classic'
        self.queryString = '?n=%s&u=%s&s=%s&protocol=%s&intended_platform=%s&client_bitcount=%s&actual_platform=%s&platform_type=%s&platform_version=%s&platform_extra=%s&platform_bitcount=%s&client_fullversion=%s&edition=%s'
        self.queryString = self.queryString % (boot.build,
         userName,
         server,
         details.protocolVersion,
         details.intendedPlatform,
         details.clientBitCount,
         details.actualPlatform,
         details.platformType,
         details.platformVersion,
         details.platformExtra,
         details.platformBitCount,
         details.clientFullVersion,
         self.edition)
        url = '%spatchinfo.asp%s' % (self.patchInfoUrl, self.queryString)
        opener = coreURLOpener()
        self.LogInfo('opening %s' % url)
        try:
            buf = opener.open(url).read()
        except IOError as e:
            raise UserError('PatchVersionCheckFailed', {'error': str(e)})

        self.patchInfoResponses[parameterHash] = buf
        return buf

    def Patch(self, userName, server, isForce = False):
        try:
            buf = self.GetPatchInfo(userName, server)
            if buf == 'ok' or buf == 'OK':
                self.LogInfo('PatchInfo request succeeded. Build numbers match')
                return
            if buf.find('ERROR') >= 0:
                self.LogError('Server Error occured looking for patch files: %s' % buf)
                s = ''
                if len(buf) > 8:
                    err = buf[5:]
                if isForce:
                    self.DoManualPatch('PatchStatusCheckFailed', localization.GetByLabel('/Carbon/UI/Patch/ServerError', error=err))
                    return
            else:
                if buf.find('NOT_FOUND') >= 0:
                    self.LogError('No patch file for this build found on server.')
                    self.DoManualPatch('PatchStatusCheckFailed', localization.GetByLabel('/Carbon/UI/Patch/NoUpdate'))
                    return
                if buf.find('TOO_NEW') >= 0:
                    self.LogError('The current build number (%s) is newer than the one returned by the web server.' % self.clientVersion)
                    return
        except Exception as e:
            sys.exc_clear()
            if isForce:
                self.DoManualPatch('PatchStatusCheckFailed', e)
                return
            else:
                self.LogError('Could not connect to server. Error: %s' % e)
                return

        if buf.find('#END') < 0:
            if isForce:
                self.DoManualPatch('PatchStatusCheckFailed', localization.GetByLabel('/Carbon/UI/Patch/UnexpectedResponse'))
            self.LogError('Unexpected response from server: %s' % buf)
            return
        lst = buf.replace('#END', '').replace('\r\n', '').split(',')
        url = lst[0].strip()
        patchFileName = url.split('/')[-1]
        patchChecksum = lst[1].strip()
        ok = False
        isInstall = patchFileName.lower().find('setup') > -1
        msgAutomaticUpdate = 'InstallAutomaticUpdate' if isInstall else 'PatchAutomaticUpdate'
        try:
            ok = self.IsExistingPatchFileCorrect(patchFileName, patchChecksum)
        except Exception:
            sys.exc_clear()

        if ok:
            self.LogInfo('Found a patch that had already been downloaded. Executing it.')
            uicore.Message('PatchStartPatch')
            self.ApplyPatch(patchFileName)
        else:
            self.LogInfo('Patch has not already been downloaded. Asking user if he wants to download it.')
        if uicore.Message(msgAutomaticUpdate, {'size': float(lst[2])}, uiconst.YESNO) == uiconst.ID_YES:
            self.DownloadPatch(url, patchChecksum)

    def CancelPatchDownload(self, *args):
        self.LogInfo('CancelPatchDownload')
        self.Cancel(args)
        SetDownloadProgress(1000)

    def PatchStatusCallback(self, totalBytes, currentBytes):
        progress = float(min(1000, int(float(currentBytes) / float(totalBytes) * 1000)))
        txt = localization.GetByLabel('/Carbon/UI/Patch/DownloadProgress', progress=progress / 10.0, total=totalBytes / 1024)
        SetDownloadProgress(progress, txt, self.CancelPatchDownload)

    def DownloadPatch(self, _fileName, checksum):
        import httplib

        def ReturnFalse(self):
            return False

        httplib.HTTPResponse._check_close = ReturnFalse
        self.patchChecksum = checksum
        url, fileName = urlparse.urlsplit(_fileName)[1:3]
        self.patchFileName = fileName.split('/')[-1]
        SetDownloadProgress(1)
        self.cancel = 0
        statusCallback = None
        try:
            if DEBUG_LEVEL:
                self.LogInfo('downloading %s from %s' % (fileName, url))
            if fileName[0] == '/':
                fileName = fileName[1:]
            self.patchGrabber = HttpFileGrabber(url, fileName, self.PatchStatusCallback)
            self.downloading = 1
            self.patchGrabber.Grab()
            SetDownloadProgress(1000)
            if DEBUG_LEVEL:
                self.LogInfo('patchfile %s downloaded' % fileName)
            self.downloading = 0
            self.patchGrabber = None
            if not self.VerifyPatchFile():
                if self.verifyFailedNum > 1:
                    self.DoManualPatch('PatchVerifyFailed', '')
                elif uicore.Message('PatchVerifyFailedTryAgain', {}, uiconst.YESNO) == uiconst.ID_YES:
                    self.DownloadPatch(_fileName, checksum)
            else:
                uicore.Message('PatchStartPatch')
                self.ApplyPatch(self.patchFileName)
        except Exception as e:
            SetDownloadProgress(1000)
            self.DoManualPatch('PatchStatusCheckFailed', localization.GetByLabel('/Carbon/UI/Patch/DownloadError', fileName=fileName, error=e))
            self.patchGrabber = None
            self.downloading = 0
            log.LogException(toConsole=3)

    def VerifyPatchFile(self):
        try:
            ok = self.IsExistingPatchFileCorrect(self.patchFileName, self.patchChecksum)
            if not ok:
                fullFileName = os.path.join(blue.paths.ResolvePath(u'cache:/'), self.patchFileName)
                self.LogWarn('Invalid checksum, deleting file %s' % fullFileName)
                try:
                    os.remove(fullFileName)
                except:
                    self.LogWarn('Error removing %s' % fullFileName)
                    sys.exc_clear()

                return False
        except Exception:
            self.verifyFailedNum += 1
            log.LogException(toConsole=3)
            sys.exc_clear()
            return False

        return True

    def IsExistingPatchFileCorrect(self, patchFileName, patchChecksum):
        fullFileName = os.path.join(blue.paths.ResolvePath(u'cache:/'), patchFileName)
        checksum = self.GetFileHash(fullFileName)
        self.LogInfo('file: %s checksums: should be %s, is %s' % (patchFileName, patchChecksum, checksum))
        return patchChecksum.strip() == checksum.strip()

    def Cancel(self, *args):
        self.LogInfo('patchService.Cancel(%d,%d)' % (self.downloading, self.cancel))
        if not self.downloading or self.cancel:
            return
        if self.patchGrabber:
            self.patchGrabber.Cancel()
        self.cancel = 1

    def ApplyPatch(self, patchFileName):
        fullFileName = os.path.join(blue.paths.ResolvePath(u'cache:/'), patchFileName)
        parameter = '%s /path="%s"' % (fullFileName, blue.paths.ResolvePath(u'root:/'))
        self.LogInfo('applying patchfile: "%s" with parameter "%s". Client will shut down' % (fullFileName, parameter))
        blue.os.ApplyPatch(fullFileName, parameter)

    def HandleProtocolMismatch(self):
        if nasty.IsRunningWithOptionalUpgrade():
            if uicore.Message('CompiledCodeMachoNetVersionMismatch', {}, uiconst.YESNO, default=uiconst.ID_NO) == uiconst.ID_YES:
                nasty.CleanupAppDataCodeFiles()
                appUtils.Reboot('MachoNet Version Mismatch using optional upgrade')

    def GetServerUpgradeInfo(self):
        return self.upgradeInfo

    def HandleObsoleteUpgrade(self):
        uicore.Message('CompiledCodeUpgradeNoLongerValid')
        self.CleanupOptionalUpgrades()

    def CleanupOptionalUpgrades(self):
        deleted = nasty.CleanupAppDataCodeFiles()
        if deleted < 1:
            self.LogError("CleanupAppDataCodeFiles didn't delete anything")
            uicore.Message('CompiledCodeCantCleanup', {'folder': nasty.GetCompiledCodePath()})
        self.LogNotice('Restarting client after updates cleanup')
        settings.public.ui.Set('DeniedClientUpgrades', [])
        appUtils.Reboot('Compiled.Code Cleanup')

    def CheckServerUpgradeInfo(self, upgradeInfo):
        self.upgradeInfo = upgradeInfo
        if upgradeInfo is None:
            if nasty.IsRunningWithOptionalUpgrade():
                self.HandleObsoleteUpgrade()
                return
            else:
                return
        localHash = nasty.GetCompiledCodeHash()
        if upgradeInfo.hash == localHash:
            return
        if nasty.IsRunningWithOptionalUpgrade():
            currentCode = nasty.GetAppDataCompiledCodePath()
            currentBuild = currentCode.build
            if currentBuild > upgradeInfo.build:
                self.HandleObsoleteUpgrade()
        else:
            currentBuild = boot.build
        self.LogInfo('Currently running', currentBuild, 'with hash', localHash, 'but server is', upgradeInfo.build, 'with hash', upgradeInfo.hash)
        PFHash = nasty.GetCompiledCodeHash(blue.paths.ResolvePath('script:/compiled.code'))
        if PFHash == upgradeInfo.hash:
            self.LogInfo('Installation directory file matches hash, reverting to that one')
            self.HandleObsoleteUpgrade()
            return
        if upgradeInfo.build > boot.build:
            url = self.OptionalUpgradeGetDetailsURL()
            if not url:
                return
            description = self.OptionalUpgradeGetDescription().strip()
            if not description:
                return
            if description == 'ERROR':
                self.LogError('There was an error getting the update description: ERROR')
                uicore.Message('CompiledCodeUpgradeDescriptionError')
            elif description == 'NOT_FOUND':
                self.LogError('There was no description found for the client update: NOT_FOUND')
                uicore.Message('CompiledCodeUpgradeDescriptionError')
            elif description == '':
                self.LogError('There was no description found for the client update: Empty Response')
                uicore.Message('CompiledCodeUpgradeDescriptionError')
            else:
                description = description.replace('\n', '<br>')
                self.PromptForOptionalUpgrade(description, url)

    def PromptForOptionalUpgrade(self, description, url):
        urlTag = '<a href=%s>' % url
        install = uicore.Message('ClientUpdateAvailable', {'description': description,
         'urlTag': urlTag}) == uiconst.ID_OK
        self.LogInfo('Client update - Prompt', install)
        if install:
            self.LogInfo('Downloading client update', self.upgradeInfo)
            self.DownloadOptionalUpgrade(self.upgradeInfo)
        elif nasty.IsRunningWithOptionalUpgrade():
            if uicore.Message('CompiledCodeUpgradeAvailableOrRevert', {}, uiconst.YESNO) == uiconst.ID_YES:
                self.LogInfo('Client update uninstall confirmed')
                self.CleanupOptionalUpgrades()
            else:
                self.LogInfo('Client update uninstall cancelled')
                self.PromptForOptionalUpgrade(description, url)

    def OptionalUpgradeGetDetailsURL(self):
        n = nasty.GetAppDataCompiledCodePath()
        fromversion = n.build or boot.build
        if self.upgradeInfo is None:
            return
        toversion = self.upgradeInfo.build
        from appPatch import optionalPatchInfoURLs
        url = '%s?from=%s&to=%s' % (optionalPatchInfoURLs[boot.region], fromversion, toversion)
        return url

    def OptionalUpgradeGetDescription(self):
        try:
            n = nasty.GetAppDataCompiledCodePath()
            fromversion = n.build or boot.build
            if self.upgradeInfo is None:
                return
            toversion = self.upgradeInfo.build
            from appPatch import optionalPatchInfoURLs
            url = '%snoformat.asp?from=%s&to=%s' % (optionalPatchInfoURLs[boot.region], fromversion, toversion)
            socket = urllib2.urlopen(url)
            response = socket.read()
            socket.close()
            return response
        except:
            log.LogException()
            sys.exc_clear()
            return

    def DownloadOptionalUpgrade(self, upgradeInfo):
        try:
            downloadDirectory = nasty.GetAppDataCompiledCodePath().path
            filename = unicode(upgradeInfo.build) + u'.code'
            destination = os.path.join(downloadDirectory, filename)
            destination = os.path.normcase(destination)
            tempfile = 'temp_%s_dl.tmp' % upgradeInfo.hash
            tempfile = os.path.normcase(os.path.join(downloadDirectory, tempfile))
            if os.path.exists(tempfile):
                os.remove(tempfile)
            if not os.path.exists(downloadDirectory):
                os.makedirs(downloadDirectory)
            self.LogInfo('Starting download of new compiled.code file')
            SetDownloadProgress(0, localization.GetByLabel('/Carbon/UI/Patch/Downloading'))
            try:
                urllib.urlretrieve(upgradeInfo.fileurl, tempfile, CodeDownLookHook)
                self.LogInfo('Completed downloading compiled.code file to: ' + tempfile)
                readBytes = blue.win32.AtomicFileRead(tempfile)[0]
                cp = blue.crypto.GetVerContext()
                hasher = blue.crypto.CryptCreateHash(cp, blue.crypto.CALG_MD5, None)
                blue.crypto.CryptHashData(hasher, readBytes)
                thehash = blue.crypto.CryptGetHashParam(hasher, blue.crypto.HP_HASHVAL)
                hasher.Destroy()
                tempfilehash = base64.b64encode(thehash).strip().replace('/', '_')
                if tempfilehash == upgradeInfo.hash:
                    if os.path.exists(destination):
                        os.remove(destination)
                    self.LogInfo('Renaming tempfile: %s to final location: %s' % (tempfile, destination))
                    os.rename(tempfile, destination)
                    uicore.Message('CodePatchApplied')
                    appUtils.Reboot('Compiled.Code Update')
                else:
                    self.LogError('Error getting new .code file: hash mismatch. Got %s expected %s' % (tempfilehash, upgradeInfo.hash))
                    uicore.Message('CompiledCodeDownloadFailed')
            finally:
                SetDownloadProgress(1000, localization.GetByLabel('/Carbon/UI/Patch/Downloading'))

        except Exception as e:
            self.LogError('Error getting new .code file: ', e)
            uicore.Message('CompiledCodeDownloadFailed')
            if nasty.IsRunningWithOptionalUpgrade():
                self.HandleObsoleteUpgrade()


def CodeDownLookHook(transfered, blockSize, totalBytes):
    currentBytes = transfered * blockSize
    progress = float(min(1000, int(float(currentBytes) / float(totalBytes) * 1000)))
    txt = localization.GetByLabel('/Carbon/UI/Patch/DownloadProgress', progress=progress / 10.0, total=totalBytes / 1024)
    SetDownloadProgress(progress, txt)