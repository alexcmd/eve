#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/windowsvc.py
import service
import uiutil
import localization
import uthread
import form
import trinity
import util
import sys
import types
import uicls
import uiconst
import invCont
import blue
import telemetry
import invCtrl

class WindowMgr(service.Service):
    __guid__ = 'svc.window'
    __servicename__ = 'window'
    __displayname__ = 'Window Service'
    __dependencies__ = ['form']
    __exportedcalls__ = {'LoadUIColors': [],
     'CloseContainer': [],
     'OpenWindows': []}
    __notifyevents__ = ['DoSessionChanging',
     'OnSessionChanged',
     'ProcessRookieStateChange',
     'OnEndChangeDevice',
     'OnUIScalingChange',
     'ProcessDeviceChange']
    __startupdependencies__ = ['settings']

    def Run(self, memStream = None):
        self.LogInfo('Starting Window Service')
        self.LoadUIColors()

    def Stop(self, memStream = None):
        self.LogInfo('Stopping Window Service')
        service.Service.Stop(self)

    def ProcessRookieStateChange(self, state):
        if sm.GetService('connection').IsConnected():
            self.OpenWindows()

    def ProcessDeviceChange(self, *args):
        self.PreDeviceChange_DesktopLayout = uicls.Window.GetDesktopWindowLayout()

    def OnEndChangeDevice(self, change, *args):
        if 'BackBufferHeight' in change or 'BackBufferWidth' in change:
            self.RealignWindows()
            sm.GetService('device').SetupUIScaling()

    def OnUIScalingChange(self, change, *args):
        pass

    def ValidateWindows(self):
        d = uicore.desktop
        all = uicore.registry.GetValidWindows(1, floatingOnly=True)
        for wnd in all:
            if wnd.align != uiconst.RELATIVE:
                continue
            wnd.left = max(-wnd.width + 64, min(d.width - 64, wnd.left))
            wnd.top = max(0, min(d.height - wnd.GetCollapsedHeight(), wnd.top))

    def DoSessionChanging(self, isRemote, session, change):
        if not eve.session.charid:
            for layer in (uicore.layer.starmap,):
                for each in layer.children:
                    each.Close()

    def OnSessionChanged(self, isRemote, session, change):
        if sm.GetService('connection').IsConnected() and 'locationid' in change:
            self.OpenWindows()

    def ResetWindowSettings(self):
        closeStacks = []
        triggerUpdate = []
        for each in uicore.registry.GetWindows():
            if not isinstance(each, uicls.WindowCore):
                continue
            if each.isDialog:
                continue
            if each.parent != uicore.layer.main:
                uiutil.Transplant(each, uicore.layer.main)
            if isinstance(each, uicls.WindowStackCore):
                closeStacks.append(each)
            else:
                triggerUpdate.append(each)
                each.sr.stack = None
                each.state = uiconst.UI_HIDDEN
                each.align = uiconst.TOPLEFT
                each.ShowHeader()
                each.ShowBackground()

        for each in closeStacks:
            each.Close()

        uicls.Window.ResetAllWindowSettings()
        favorClasses = [form.LSCChannel,
         form.ActiveItem,
         form.OverView,
         form.DroneView,
         form.WatchListPanel]
        done = []
        for cls in favorClasses:
            for each in triggerUpdate:
                if each not in done and isinstance(each, cls):
                    each.InitializeSize()
                    each.InitializeStatesAndPosition()
                    done.append(each)

        for each in triggerUpdate:
            if each not in done:
                each.InitializeSize()
                each.InitializeStatesAndPosition()

        settings.user.ui.Delete('targetOrigin')
        sm.GetService('target').ArrangeTargets()

    def RealignWindows(self):
        desktopLayout = getattr(self, 'PreDeviceChange_DesktopLayout', None)
        if desktopLayout:
            uicls.Window.LoadDesktopWindowLayout(desktopLayout)
        self.PreDeviceChange_DesktopLayout = None
        sm.GetService('target').ArrangeTargets()

    @telemetry.ZONE_METHOD
    def OpenWindows(self):
        if not (eve.rookieState and eve.rookieState < 10):
            wndsToCheck = [util.KeyVal(cls=form.MailWindow, cmd=uicore.cmd.OpenMail),
             util.KeyVal(cls=form.Wallet, cmd=uicore.cmd.OpenWallet),
             util.KeyVal(cls=form.Corporation, cmd=uicore.cmd.OpenCorporationPanel),
             util.KeyVal(cls=form.AssetsWindow, cmd=uicore.cmd.OpenAssets),
             util.KeyVal(cls=form.Channels, cmd=uicore.cmd.OpenChannels),
             util.KeyVal(cls=form.Journal, cmd=uicore.cmd.OpenJournal),
             util.KeyVal(cls=form.Logger, cmd=uicore.cmd.OpenLog),
             util.KeyVal(cls=form.CharacterSheet, cmd=uicore.cmd.OpenCharactersheet),
             util.KeyVal(cls=form.AddressBook, cmd=uicore.cmd.OpenPeopleAndPlaces),
             util.KeyVal(cls=form.RegionalMarket, cmd=uicore.cmd.OpenMarket),
             util.KeyVal(cls=form.Notepad, cmd=uicore.cmd.OpenNotepad)]
            if session.stationid2:
                sm.GetService('gameui').ScopeCheck(['station', 'station_inflight'])
                wndsToCheck += [util.KeyVal(cls=form.Inventory, cmd=uicore.cmd.OpenInventory, windowID='InventoryStation'), util.KeyVal(cls=form.StationItems, cmd=uicore.cmd.OpenHangarFloor), util.KeyVal(cls=form.StationShips, cmd=uicore.cmd.OpenShipHangar)]
                if session.corpid:
                    wndsToCheck.append(util.KeyVal(cls=form.StationCorpDeliveries, cmd=uicore.cmd.OpenCorpDeliveries, windowID=form.Inventory.GetWindowIDFromInvID(('StationCorpDeliveries', session.stationid2))))
                    office = sm.GetService('corp').GetOffice()
                    if office:
                        wndsToCheck.append(util.KeyVal(cls=form.StationCorpHangars, cmd=uicore.cmd.OpenCorpHangar, windowID=form.Inventory.GetWindowIDFromInvID(('StationCorpHangars', office.itemID))))
                        for i in xrange(7):
                            invID = ('StationCorpHangar', office.itemID, i)
                            wndsToCheck.append(util.KeyVal(cls=form.Inventory, cmd=self._OpenCorpHangarDivision, windowID=form.Inventory.GetWindowIDFromInvID(invID), args=(invID,)))

            elif session.solarsystemid and session.shipid:
                sm.GetService('gameui').ScopeCheck(['inflight', 'station_inflight'])
                wndsToCheck += [util.KeyVal(cls=form.Inventory, cmd=uicore.cmd.OpenInventory, windowID='InventorySpace'), util.KeyVal(cls=form.Scanner, cmd=uicore.cmd.OpenScanner)]
            else:
                sm.GetService('gameui').ScopeCheck()
            for checkWnd in wndsToCheck:
                cls = checkWnd.cls
                cmd = checkWnd.cmd
                windowID = getattr(checkWnd, 'windowID', cls.default_windowID)
                args = getattr(checkWnd, 'args', ())
                stackID = cls.GetRegisteredOrDefaultStackID()
                wnd = uicls.Window.GetIfOpen(windowID)
                if type(windowID) == tuple:
                    windowID = windowID[0]
                isOpen = uicore.registry.GetRegisteredWindowState(windowID, 'open', False)
                isMinimized = uicore.registry.GetRegisteredWindowState(windowID, 'minimized', False)
                if isOpen and (stackID or not isMinimized) and not wnd:
                    cmd(*args)

        form.Lobby.CloseIfOpen()
        if session.stationid2:
            if not (eve.rookieState and eve.rookieState < 5):
                form.Lobby.Open()

    def _OpenCorpHangarDivision(self, invID):
        form.Inventory.OpenOrShow(invID=invID, usePrimary=False, toggle=False)

    def SetWindowColor(self, r, g, b, a, what = 'color'):
        settings.char.windows.Set('wnd%s' % what.capitalize(), (r,
         g,
         b,
         a))
        sm.ScatterEvent('OnUIColorsChanged')

    def GetWindowColors(self):
        return (settings.char.windows.Get('wndColor', eve.themeColor),
         settings.char.windows.Get('wndBackgroundcolor', eve.themeBgColor),
         settings.char.windows.Get('wndComponent', eve.themeCompColor),
         settings.char.windows.Get('wndComponentsub', eve.themeCompSubColor))

    def ResetWindowColors(self, *args):
        self.LoadUIColors(reset=True)

    def LoadUIColors(self, reset = 0):
        reset = reset or eve.session.userid is None
        if reset:
            self.SetWindowColor(what='Color', *eve.themeColor)
            self.SetWindowColor(what='Background', *eve.themeBgColor)
            self.SetWindowColor(what='Component', *eve.themeCompColor)
            self.SetWindowColor(what='Componentsub', *eve.themeCompSubColor)
        sm.ScatterEvent('OnUIColorsChanged')

    def CheckControlAppearance(self, control):
        wnd = uiutil.GetWindowAbove(control)
        if wnd:
            self.ChangeControlAppearance(wnd, control)

    def ChangeControlAppearance(self, wnd, control = None):
        haveLiteFunction = [ w for w in (control or wnd).Find('trinity.Tr2Sprite2dContainer') if hasattr(w, 'LiteMode') ]
        haveLiteFunction += [ w for w in (control or wnd).Find('trinity.Tr2Sprite2dFrame') if hasattr(w, 'LiteMode') ]
        for obj in haveLiteFunction:
            obj.LiteMode(wnd.IsPinned())

        wnds = [ w for w in (control or wnd).Find('trinity.Tr2Sprite2dContainer') if w.name == '_underlay' and w not in haveLiteFunction ]
        wnd = getattr(wnd.sr, 'stack', None) or wnd
        for w in wnds:
            uiutil.Flush(w)
            if wnd.IsPinned():
                uicls.Frame(parent=w, color=(1.0, 1.0, 1.0, 0.2), padding=(-1, -1, -1, -1))
                uicls.Fill(parent=w, color=(0.0, 0.0, 0.0, 0.3))
            else:
                uicls.BumpedUnderlay(parent=w)

        frames = [ w for w in (control or wnd).Find('trinity.Tr2Sprite2dFrame') if w.name == '__underlay' and w not in haveLiteFunction ]
        for f in frames:
            self.CheckFrames(f, wnd)

    def CheckFrames(self, underlay, wnd):
        underlayParent = getattr(underlay, 'parent', None)
        if underlayParent is None:
            return
        noBackground = getattr(underlayParent, 'noBackground', 0)
        if noBackground:
            return
        underlayFrame = underlayParent.FindChild('underlayFrame')
        underlayFill = underlayParent.FindChild('underlayFill')
        if wnd.IsPinned():
            underlay.state = uiconst.UI_HIDDEN
            if not underlayFill:
                underlayFill = uicls.Frame(name='underlayFill', color=(0.0, 0.0, 0.0, 0.3), frameConst=uiconst.FRAME_FILLED_CORNER0, parent=underlayParent)
            else:
                underlayFill.state = uiconst.UI_DISABLED
            if not underlayFrame:
                underlayFrame = uicls.Frame(name='underlayFrame', color=(1.0, 1.0, 1.0, 0.2), frameConst=uiconst.FRAME_BORDER1_CORNER0, parent=underlayParent, pos=(-1, -1, -1, -1))
            else:
                underlayFrame.state = uiconst.UI_DISABLED
        else:
            if not noBackground:
                underlay.state = uiconst.UI_DISABLED
            if underlayFrame:
                underlayFrame.state = uiconst.UI_HIDDEN
            if underlayFill:
                underlayFill.state = uiconst.UI_HIDDEN

    def ToggleLiteWindowAppearance(self, wnd, forceLiteState = None):
        if forceLiteState is not None:
            wnd._SetPinned(forceLiteState)
        state = uiconst.UI_DISABLED
        for each in wnd.children[:]:
            if each.name.startswith('_lite'):
                each.Close()

        if wnd.IsPinned():
            for align in (uiconst.TOLEFT,
             uiconst.TOTOP,
             uiconst.TORIGHT,
             uiconst.TOBOTTOM):
                uicls.Line(parent=wnd, align=align, color=(0.0, 0.0, 0.0, 0.3), idx=0, name='_liteline')

            uicls.Frame(parent=wnd, color=(1.0, 1.0, 1.0, 0.2), name='_liteframe')
            uicls.Fill(parent=wnd, color=(0.0, 0.0, 0.0, 0.3), name='_litefill')
            state = uiconst.UI_HIDDEN
        for each in wnd.children:
            for _each in wnd.sr.underlay.background:
                if _each.name in ('base', 'color', 'shadow', 'solidBackground'):
                    _each.state = state

        m = wnd.sr.maincontainer
        if state == uiconst.UI_DISABLED:
            m.left = m.top = m.width = m.height = 1
        else:
            m.left = m.top = m.width = m.height = 0
        self.ChangeControlAppearance(wnd)

    def CloseContainer(self, invID):
        self.LogInfo('WindowSvc.CloseContainer request for id:', invID)
        checkIDs = (('loot', invID),
         ('lootCargoContainer', invID),
         'shipCargo_%s' % invID,
         'drones_%s' % invID,
         'containerWindow_%s' % invID)
        for windowID in checkIDs:
            wnd = uicls.Window.GetIfOpen(windowID=windowID)
            if wnd:
                wnd.Close()
                self.LogInfo('  WindowSvc.CloseContainer closing:', windowID)

    def GetCameraLeftOffset(self, width, align = None, left = 0, *args):
        if not settings.user.ui.Get('offsetUIwithCamera', False):
            return 0
        offset = int(settings.user.ui.Get('cameraOffset', 0))
        if not offset:
            return 0
        if align in [uiconst.CENTER, uiconst.CENTERTOP, uiconst.CENTERBOTTOM]:
            camerapush = int(offset / 100.0 * uicore.desktop.width / 3.0)
            allowedOffset = int((uicore.desktop.width - width) / 2) - 10
            if camerapush < 0:
                return max(camerapush, -allowedOffset - left)
            if camerapush > 0:
                return min(camerapush, allowedOffset + left)
        return 0