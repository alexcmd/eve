#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/eveAudioService.py
import audio2
import svc
import blue
import sys
import log
import trinity
import util
import ccConst
import const
SHIPS_DESTROYED_TO_CHANGE_MUSIC = 10
PILOTS_IN_SPACE_TO_CHANGE_MUSIC = 100
MUSIC_LOCATION_SPACE = 'music_eve_dynamic'
MUSIC_LOCATION_LOGIN = 'music_login'
MUSIC_LOCATION_CHARACTER_CREATION = 'music_character_creation'
MUSIC_STATE_EMPIRE = 'music_switch_empire'
MUSIC_STATE_EMPIRE_POPULATED = 'music_switch_famous'
MUSIC_STATE_LOWSEC = 'music_switch_danger'
MUSIC_STATE_NULLSEC = 'music_switch_zero'
MUSIC_STATE_NULLSEC_DEATHS = 'music_switch_zero_danger'
MUSIC_STATE_RACE_AMARR = 'music_switch_race_amarr'
MUSIC_STATE_RACE_CALDARI = 'music_switch_race_caldari'
MUSIC_STATE_RACE_GALLENTE = 'music_switch_race_gallente'
MUSIC_STATE_RACE_MINMATAR = 'music_switch_race_minmatar'
MUSIC_STATE_RACE_NORACE = 'music_switch_race_norace'
MUSIC_STATE_FULL = 'music_switch_full'
MUSIC_STATE_AMBIENT = 'music_switch_ambient'
RACIALMUSICDICT = {const.raceCaldari: MUSIC_STATE_RACE_CALDARI,
 const.raceMinmatar: MUSIC_STATE_RACE_MINMATAR,
 const.raceAmarr: MUSIC_STATE_RACE_AMARR,
 const.raceGallente: MUSIC_STATE_RACE_GALLENTE,
 None: MUSIC_STATE_RACE_NORACE}

class EveAudioService(svc.audio):
    __guid__ = 'svc.eveAudio'
    __replaceservice__ = 'audio'
    __exportedcalls__ = svc.audio.__exportedcalls__.copy()
    __exportedcalls__.update({'PlaySound': [],
     'AudioMessage': [],
     'SendUIEvent': [],
     'SendJukeboxEvent': [],
     'StartSoundLoop': [],
     'StopSoundLoop': [],
     'GetTurretSuppression': [],
     'SetTurretSuppression': [],
     'GetVoiceVolume': [],
     'SetVoiceVolume': [],
     'MuteSounds': [],
     'UnmuteSounds': []})
    __notifyevents__ = ['OnDamageStateChange',
     'OnSessionChanged',
     'OnCapacitorChange',
     'OnChannelsJoined']

    def AppInit(self):
        self.soundLoops = {}
        self.lastLookedAt = None
        self.capacitorAlreadyAlerted = False
        self.soundNotificationSent = [False,
         False,
         False,
         False]
        self.loginMusicPaused = False
        self.musicPlaying = False
        self.musicOn = True
        self.musicLocation = None
        self.musicState = None
        self.lastPlaying = None

    def AppRun(self):
        if self.AppGetSetting('forceEnglishVoice', False):
            aPath = blue.paths.ResolvePath(u'res:/Audio')
            io = audio2.AudLowLevelIO(aPath)
            self.manager.config.lowLevelIO = io

    def AppStop(self):
        if blue.win32 and trinity.device:
            try:
                blue.win32.WTSUnRegisterSessionNotification(trinity.device.GetWindow())
            except:
                sys.exc_clear()

        if uicore.uilib:
            uicore.uilib.SessionChangeHandler = None

    def AppLoadBanks(self):
        self.manager.LoadBank(u'Effects.bnk')
        self.manager.LoadBank(u'Interface.bnk')
        self.manager.LoadBank(u'Modules.bnk')
        self.manager.LoadBank(u'ShipEffects.bnk')
        self.manager.LoadBank(u'Turrets.bnk')
        self.manager.LoadBank(u'Atmos.bnk')
        self.manager.LoadBank(u'Boosters.bnk')
        self.manager.LoadBank(u'Music.bnk')
        self.manager.LoadBank(u'Placeables.bnk')
        self.manager.LoadBank(u'Voice.bnk')
        self.manager.LoadBank(u'CharacterCreation.bnk')
        self.manager.LoadBank(u'Hangar.bnk')
        self.manager.LoadBank(u'Planets.bnk')
        self.manager.LoadBank(u'Incarna.bnk')
        self.manager.LoadBank(u'Dungeons.bnk')

    def AppSetListener(self, listener):
        sm.GetService('sceneManager').GetRegisteredCamera(None, defaultOnActiveCamera=True).audio2Listener = listener
        sm.GetService('cameraClient').SetAudioListener(listener)

    def AppActivate(self):
        self.SetMasterVolume(self.GetMasterVolume())
        self.SetUIVolume(self.GetUIVolume())
        self.SetWorldVolume(self.GetWorldVolume())
        self.SetVoiceVolume(self.GetVoiceVolume())
        self.SetAmpVolume(self.GetMusicVolume())
        self.SetTurretSuppression(self.GetTurretSuppression())

    def AppDeactivate(self):
        self.capacitorAlreadyAlerted = False
        self.loginMusicPaused = False
        self.musicPlaying = False
        self.musicOn = False
        self.musicState = None
        self.lastPlaying = None

    def PlayFootfallForEntity(self, entity):
        import materialTypes
        namesByID = {}
        for name, ID in materialTypes.MATERIAL_NAMES.iteritems():
            namesByID[ID] = name

        if not entity:
            return
        positionComponent = entity.GetComponent('position')
        audioEmitterComponent = entity.GetComponent('audioEmitter')
        if not positionComponent or not audioEmitterComponent:
            return
        gameWorld = sm.GetService('gameWorldClient').GetGameWorld(session.worldspaceid)
        if not gameWorld:
            return
        topPosition = (positionComponent.position[0], positionComponent.position[1] + 0.1, positionComponent.position[2])
        bottomPosition = (positionComponent.position[0], positionComponent.position[1] - 0.2, positionComponent.position[2])
        hitResult = gameWorld.MultiHitLineTestWithMaterials(topPosition, bottomPosition)
        if hitResult:
            audioEmitterComponent.emitter.SetSwitch(u'Materials', namesByID[hitResult[0][2]])
            audioEmitterComponent.emitter.SendEvent(u'footfall_loud_play')
        else:
            audioEmitterComponent.emitter.SetSwitch(u'Materials', u'Invalid')
            audioEmitterComponent.emitter.SendEvent(u'footfall_loud_play')

    def PlaySound(self, audioFile, streamed = False, loop = False, gain = -1, pan = -1, fadeInStart = 0, fadeInTime = 0, fadeOutStart = 0, fadeOutTime = 0, cookie = 0, callback = None, early = 0):
        if not self.IsActivated():
            return
        if audioFile.startswith('wise:/'):
            self.SendUIEvent(audioFile[6:])
        else:
            self.LogError('REPORT THIS DEFECT: Audio Service ignoring a non-Wise event:', audioFile)
            log.LogTraceback('Non-wise event received: %s' % audioFile)

    def AudioMessage(self, msg):
        if not self.IsActivated():
            return
        if msg.audio:
            audiomsg = msg.audio
        else:
            return
        if audiomsg.startswith('wise:/'):
            audiomsg = audiomsg[6:]
            self.SendUIEvent(audiomsg)
        else:
            self.LogError('REPORT THIS DEFECT: Old UI sound being played, msg:', msg)
            log.LogTraceback('OLD UI SOUND BEING PLAYED: %s' % msg)

    def StartSoundLoop(self, rootLoopMsg):
        if not self.IsActivated():
            return
        try:
            if rootLoopMsg not in self.soundLoops:
                self.LogInfo('StartSoundLoop starting loop with root %s' % rootLoopMsg)
                self.soundLoops[rootLoopMsg] = 1
                self.SendUIEvent('wise:/msg_%s_play' % rootLoopMsg)
            else:
                self.soundLoops[rootLoopMsg] += 1
                self.LogInfo('StartSoundLoop incrementing %s loop to %d' % (rootLoopMsg, self.soundLoops[rootLoopMsg]))
        except:
            self.LogWarn('StartSoundLoop failed - halting loop with root', rootLoopMsg)
            self.SendUIEvent('wise:/msg_%s_stop' % rootLoopMsg)
            sys.exc_clear()

    def StopSoundLoop(self, rootLoopMsg, eventMsg = None):
        if rootLoopMsg not in self.soundLoops:
            self.LogWarn('StopSoundLoop told to halt', rootLoopMsg, 'but that message is not playing!')
            return
        try:
            self.soundLoops[rootLoopMsg] -= 1
            if self.soundLoops[rootLoopMsg] <= 0:
                self.LogInfo('StopSoundLoop halting message with root', rootLoopMsg)
                del self.soundLoops[rootLoopMsg]
                self.SendUIEvent('wise:/msg_%s_stop' % rootLoopMsg)
            else:
                self.LogInfo('StopSoundLoop decremented count of loop with root %s to %d' % (rootLoopMsg, self.soundLoops[rootLoopMsg]))
        except:
            self.LogWarn('StopSoundLoop failed due to an exception - forcibly halting', rootLoopMsg)
            self.SendUIEvent('wise:/msg_%s_stop' % rootLoopMsg)
            sys.exc_clear()

        if eventMsg is not None:
            self.SendUIEvent(eventMsg)

    def SetVoiceVolume(self, vol = 1.0, persist = True):
        if vol < 0.0 or vol > 1.0:
            raise RuntimeError('Erroneous value received for volume')
        if not self.IsActivated():
            return
        self.SetGlobalRTPC('volume_voice', vol)
        if persist:
            self.AppSetSetting('evevoiceGain', vol)

    def GetVoiceVolume(self):
        return self.AppGetSetting('evevoiceGain', 0.9)

    def SetAmpVolume(self, volume = 0.25, persist = True):
        if volume < 0.0 or volume > 1.0:
            raise RuntimeError('Erroneous value received for volume')
        if not self.IsActivated():
            return
        self.SetGlobalRTPC('volume_music', volume)
        if persist:
            self.AppSetSetting('eveampGain', volume)
        if volume == 0.0 and self.lastPlaying:
            self.StopLocationMusic(self.lastPlaying)
            self.musicOn = False
        elif volume != 0.0 and not self.musicOn:
            self.musicOn = True
            self.SetDynamicMusicSwitchPopularity()
            self.UpdateDynamicMusic()

    def GetMusicVolume(self):
        return self.AppGetSetting('eveampGain', 0.25)

    def GetTurretSuppression(self):
        return self.AppGetSetting('suppressTurret', 0)

    def SetTurretSuppression(self, suppress, persist = True):
        if not self.IsActivated():
            return
        if suppress:
            self.SetGlobalRTPC('turret_muffler', 0.0)
            suppress = 1
        else:
            self.SetGlobalRTPC('turret_muffler', 1.0)
            suppress = 0
        if persist:
            self.AppSetSetting('suppressTurret', suppress)

    def AppMessage(self, message, **kwargs):
        eve.Message(message, **kwargs)

    def AppGetSetting(self, setting, default):
        try:
            return settings.public.audio.Get(setting, default)
        except (AttributeError, NameError):
            return default

    def AppSetSetting(self, setting, value):
        try:
            settings.public.audio.Set(setting, value)
        except (AttributeError, NameError):
            pass

    def MuteSounds(self):
        self.SetMasterVolume(0.0, False)

    def UnmuteSounds(self):
        self.SetMasterVolume(self.GetMasterVolume(), False)

    def SendWiseEvent(self, event):
        if event:
            self.SendUIEvent(event)

    def OnDamageStateChange(self, shipID, damageState):
        if session.shipid != shipID:
            return
        for i in xrange(0, 3):
            soundEvent = None
            enabled = settings.user.notifications.Get(const.soundNotificationVars[i][0], 1)
            if not enabled:
                continue
            shouldNotify = damageState[i] <= settings.user.notifications.Get(const.soundNotificationVars[i][1], const.soundNotificationVars[i][2])
            alreadyNotified = self.soundNotificationSent[i]
            if shouldNotify and not alreadyNotified:
                self.soundNotificationSent[i] = True
                soundEvent = const.damageSoundNotifications[i]
            if alreadyNotified:
                self.soundNotificationSent[i] = shouldNotify
                continue
            if soundEvent is not None:
                self.SendUIEvent(soundEvent)

    def OnCapacitorChange(self, currentCharge, maxCharge, percentageLoaded):
        CAPACITOR = 3
        soundEvent = None
        enabled = settings.user.notifications.Get(const.soundNotificationVars[CAPACITOR][0], 1)
        if not enabled:
            return
        shouldNotify = percentageLoaded <= settings.user.notifications.Get(const.soundNotificationVars[CAPACITOR][1], const.soundNotificationVars[CAPACITOR][2])
        alreadyNotified = self.soundNotificationSent[CAPACITOR]
        if shouldNotify and not alreadyNotified:
            self.soundNotificationSent[CAPACITOR] = True
            soundEvent = const.damageSoundNotifications[CAPACITOR]
        if alreadyNotified:
            self.soundNotificationSent[CAPACITOR] = shouldNotify
            return
        if soundEvent is not None:
            self.SendUIEvent(soundEvent)

    def OnSessionChanged(self, *args):
        if not session.solarsystemid2:
            self.UpdateDynamicMusic()

    def UpdateDynamicMusic(self):
        if not self.active or not self.musicOn:
            return
        self.musicLocation = self.GetMusicLocation()
        if self.musicLocation is None or self.lastPlaying == self.musicLocation:
            return
        self.PlayLocationMusic(self.musicLocation)

    def OnChannelsJoined(self, channelIDs):
        if (('solarsystemid2', session.solarsystemid2),) in channelIDs:
            self.SetDynamicMusicSwitchPopularity()
            self.UpdateDynamicMusic()

    def PlayLocationMusic(self, location):
        if self.lastPlaying is not None:
            self.StopLocationMusic(self.lastPlaying)
        if location == MUSIC_LOCATION_LOGIN and self.loginMusicPaused:
            self.ResumeLocationMusic(location)
            return
        self.SendWiseEvent(location + '_play')
        self.musicPlaying = True
        self.lastPlaying = location
        if location == MUSIC_LOCATION_SPACE and self.loginMusicPaused:
            self.StopLocationMusic(MUSIC_LOCATION_LOGIN)
            self.loginMusicPaused = False

    def StopLocationMusic(self, location):
        if location == MUSIC_LOCATION_LOGIN and self.musicLocation != MUSIC_LOCATION_SPACE:
            self.PauseLocationMusic(location)
            return
        self.SendWiseEvent(location + '_stop')
        self.lastPlaying = None
        self.musicPlaying = False

    def PauseLocationMusic(self, location):
        self.SendWiseEvent(location + '_pause')
        self.musicPlaying = False
        self.lastPlaying = None
        if location == MUSIC_LOCATION_LOGIN:
            self.loginMusicPaused = True

    def ResumeLocationMusic(self, location):
        self.SendWiseEvent(location + '_resume')
        self.musicPlaying = True
        self.lastPlaying = location
        if location == MUSIC_LOCATION_LOGIN:
            self.loginMusicPaused = False

    def GetMusicLocation(self):
        if getattr(uicore.layer.login, 'isopen', None) or getattr(uicore.layer.charsel, 'isopen', None) or getattr(uicore.layer.charsel, 'isopening', None):
            return MUSIC_LOCATION_LOGIN
        if getattr(uicore.layer.charactercreation, 'isopen', None) or getattr(uicore.layer.charactercreation, 'isopening', None):
            self.SetCharacterCreationMusicState()
            return MUSIC_LOCATION_CHARACTER_CREATION
        if session.solarsystemid2:
            self.SetSpaceMusicState()
            return MUSIC_LOCATION_SPACE

    def SetCharacterCreationMusicState(self):
        raceID = uicore.layer.charactercreation.raceID
        stepID = uicore.layer.charactercreation.stepID
        if not raceID:
            self.SendWiseEvent(MUSIC_STATE_FULL)
            self.SendWiseEvent(MUSIC_STATE_RACE_NORACE)
        elif stepID == ccConst.RACESTEP:
            raceState = RACIALMUSICDICT.get(raceID, None)
            self.SendWiseEvent(raceState)
            self.SendWiseEvent(MUSIC_STATE_FULL)
        else:
            raceState = RACIALMUSICDICT.get(raceID, None)
            self.SendWiseEvent(raceState)
            self.SendWiseEvent(MUSIC_STATE_AMBIENT)

    def SetSpaceMusicState(self):
        self.musicState = self.GetSpaceMusicState()
        if self.musicState:
            self.SendWiseEvent(self.musicState)

    def GetSpaceMusicState(self):
        sec = sm.GetService('map').GetSecurityClass(session.solarsystemid2)
        if sec == const.securityClassZeroSec:
            if self.ShipsDestroyedInLast24H() > SHIPS_DESTROYED_TO_CHANGE_MUSIC:
                self.LogInfo('Setting dynamic music - dangerous null-sec system')
                return MUSIC_STATE_NULLSEC_DEATHS
            else:
                self.LogInfo('Setting dynamic music - normal null-sec system')
                return MUSIC_STATE_NULLSEC
        elif sec == const.securityClassLowSec:
            self.LogInfo('Setting dynamic music - low sec')
            return MUSIC_STATE_LOWSEC

    def SetDynamicMusicSwitchPopularity(self):
        if not session.solarsystemid2:
            return
        state = self.GetDynamicMusicSwitchPopularity()
        if state is not None and session.solarsystemid2:
            self.SendWiseEvent(state)

    def GetDynamicMusicSwitchPopularity(self):
        sec = sm.GetService('map').GetSecurityClass(session.solarsystemid2)
        if sec != const.securityClassHighSec:
            return
        else:
            pilots = self.GetPilotsInSystem()
            if pilots > PILOTS_IN_SPACE_TO_CHANGE_MUSIC:
                self.LogInfo('Setting dynamic music - popular system')
                return MUSIC_STATE_EMPIRE_POPULATED
            self.LogInfo('Setting dynamic music - unpopular system')
            return MUSIC_STATE_EMPIRE

    def GetPilotsInSystem(self):
        channelID = (('solarsystemid2', session.solarsystemid2),)
        with util.ExceptionEater('SetDynamicMusicSwitch - Getting channel membercount'):
            return sm.GetService('LSC').GetMemberCount(channelID)
        return 0

    def ShipsDestroyedInLast24H(self):
        return 0
        historyDB = sm.RemoteSvc('map').GetHistory(const.mapHistoryStatKills, 24)
        for entry in historyDB:
            if entry[0] == session.solarsystemid2:
                kills = entry.value1 - entry.value2
                return kills

        return 0

    def TurnOffShipSound(self, ship):
        if ship.generalAudioEntity:
            ship.generalAudioEntity.SendEvent(unicode('shipsounds_stop'))

    def GetSoundUrlForType(self, slimItem):
        soundUrl = sm.GetService('incursion').GetSoundUrlByKey(slimItem.groupID)
        if soundUrl is None:
            soundID = cfg.invtypes.Get(slimItem.typeID).soundID
            if soundID is not None:
                soundUrl = cfg.sounds.Get(soundID).soundFile
            self.LogInfo('Return default sound for ', slimItem.typeID, '=', soundUrl)
        else:
            self.LogInfo('Incursion overriding sound for typeID', slimItem.typeID, 'to', soundUrl)
        return soundUrl