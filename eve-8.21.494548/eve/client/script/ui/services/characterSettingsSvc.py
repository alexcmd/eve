#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/characterSettingsSvc.py
import service
import svc

class CharacerSettingsSvc(service.Service):
    __guid__ = 'svc.characterSettings'
    __update_on_reload__ = 1

    def Run(self, *args):
        self.settings = {}
        self.charMgr = session.ConnectToRemoteService('charMgr')
        self.settings = self.charMgr.GetCharacterSettings()

    def Get(self, settingKey):
        try:
            return self.settings[settingKey]
        except KeyError:
            return None

    def Save(self, settingKey, value):
        if value is None:
            self.Delete(settingKey)
        if len(value) > 102400:
            raise RuntimeError("I don't wan't to send so large character setting to the server", _charid, settingKey, len(value))
        self.charMgr.SaveCharacterSetting(settingKey, value)
        self.settings[settingKey] = value

    def Delete(self, settingKey):
        if settingKey in self.settings:
            self.charMgr.DeleteCharacterSetting(settingKey)
            del self.settings[settingKey]