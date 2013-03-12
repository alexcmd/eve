#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/shipconfig.py
import listentry
import localization
import util
import moniker
import uicls
import uiconst
import uix
import uthread
import blue

class ShipConfig(uicls.Window):
    __guid__ = 'form.ShipConfig'
    __notifyevents__ = ['ProcessSessionChange', 'OnShipCloneJumpUpdate']
    default_windowID = 'shipconfig'
    shipmodules = [('CloneFacility', 'canReceiveCloneJumps')]

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.shipid = util.GetActiveShip()
        self.shipItem = self.GetShipItem()
        self.SetCaption(localization.GetByLabel('UI/Ship/ShipConfig/ShipConfig'))
        self.SetTopparentHeight(72)
        self.SetWndIcon()
        self.SetMinSize([300, 200])
        self.sr.top = uicls.Container(name='top', align=uiconst.TOTOP, parent=self.sr.topParent, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         64))
        icon = uicls.Icon(parent=self.sr.top, align=uiconst.TOLEFT, left=const.defaultPadding, size=64, state=uiconst.UI_NORMAL, typeID=self.shipItem.typeID)
        icon.GetMenu = self.ShipMenu
        uicls.Container(name='push', align=uiconst.TOLEFT, pos=(5, 0, 5, 0), parent=self.sr.top)
        uicls.EveHeaderMedium(name='label', text=cfg.evelocations.Get(self.shipItem.itemID).name, parent=self.sr.top, align=uiconst.TOTOP, bold=True, state=uiconst.UI_NORMAL)
        uicls.EveLabelMedium(name='label', text=cfg.invtypes.Get(self.shipItem.typeID).name, parent=self.sr.top, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        self.ship = moniker.GetShipAccess()
        self.conf = self.ship.GetShipConfiguration(self.shipid)
        modules = self.GetShipModules()
        for module in modules:
            self.sr.Set('%sPanel' % module.lower(), uicls.Container(name=module, align=uiconst.TOALL, state=uiconst.UI_HIDDEN, parent=self.sr.main, pos=(0, 0, 0, 0)))

        tabs = [ [name,
         self.sr.Get('%sPanel' % module.lower(), None),
         self,
         module] for module, name in modules.iteritems() if self.sr.Get('%sPanel' % module.lower()) ]
        if tabs:
            self.sr.maintabs = uicls.TabGroup(name='tabparent', align=uiconst.TOTOP, height=18, parent=self.sr.main, idx=0, tabs=tabs, groupID='pospanel')
        else:
            uicls.CaptionLabel(text=localization.GetByLabel('UI/Ship/ShipConfig/ShipConfig'), parent=self.sr.main, size=18, uppercase=0, left=const.defaultPadding, width=const.defaultPadding, top=const.defaultPadding)

    def _OnClose(self, *args):
        self.shipid = None
        self.shipItem = None
        self.capacity = None
        self.tower = None

    def Load(self, key):
        eval('self.Show%s()' % key)

    def ShowCloneFacility(self):
        if not getattr(self, 'cloneinited', 0):
            self.InitCloneFacilityPanel()
        godmaSM = sm.GetService('godma').GetStateManager()
        self.panelsetup = 1
        cloneRS = sm.GetService('clonejump').GetShipClones()
        scrolllist = []
        for each in cloneRS:
            charinfo = cfg.eveowners.Get(each['ownerID'])
            scrolllist.append(listentry.Get('User', {'charID': each['ownerID'],
             'info': charinfo,
             'cloneID': each['jumpCloneID']}))

        self.sr.clonescroll.Load(contentList=scrolllist, headers=[localization.GetByLabel('UI/Common/Name')])
        self.sr.clonescroll.ShowHint([localization.GetByLabel('UI/Ship/ShipConfig/NoClonesInstalledAtShip'), None][bool(scrolllist)])
        numClones = int(len(cloneRS))
        totalClones = int(getattr(godmaSM.GetItem(self.shipItem.itemID), 'maxJumpClones', 0))
        self.sr.cloneInfo.text = localization.GetByLabel('UI/Ship/ShipConfig/NumJumpClones', numClones=numClones, totalClones=totalClones)
        self.panelsetup = 0

    def InitCloneFacilityPanel(self):
        panel = self.sr.clonefacilityPanel
        btns = [(localization.GetByLabel('UI/Ship/ShipConfig/Invite'),
          self.InviteClone,
          (),
          84), (localization.GetByLabel('UI/Ship/ShipConfig/Destroy'),
          self.DestroyClone,
          (),
          84)]
        self.cloneFacilityButtons = uicls.ButtonGroup(btns=btns, parent=panel)
        if not session.solarsystemid:
            self.cloneFacilityButtons.GetBtnByIdx(0).Disable()
        numClones = int(0)
        totalClones = int(getattr(sm.GetService('godma').GetItem(self.shipItem.itemID), 'maxJumpClones', 0))
        text = localization.GetByLabel('UI/Ship/ShipConfig/NumJumpClones', numClones=numClones, totalClones=totalClones)
        self.sr.cloneInfo = uicls.EveLabelSmall(text=text, parent=panel, align=uiconst.TOTOP, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         0), state=uiconst.UI_NORMAL)
        self.sr.clonescroll = uicls.Scroll(name='clonescroll', parent=panel, padding=const.defaultPadding)
        self.cloneinited = 1

    def InviteClone(self, *args):
        if not sm.GetService('clonejump').HasCloneReceivingBay():
            eve.Message('InviteClone1')
            return
        godmaSM = sm.GetService('godma').GetStateManager()
        opDist = getattr(godmaSM.GetType(self.shipItem.typeID), 'maxOperationalDistance', 0)
        bp = sm.GetService('michelle').GetBallpark()
        if not bp:
            return
        charIDs = [ slimItem.charID for slimItem in bp.slimItems.itervalues() if slimItem.charID and slimItem.charID != eve.session.charid and not util.IsNPC(slimItem.charID) and slimItem.surfaceDist <= opDist ]
        if not charIDs:
            eve.Message('InviteClone2')
            return
        lst = []
        for charID in charIDs:
            char = cfg.eveowners.Get(charID)
            lst.append((char.name, charID, char.typeID))

        chosen = uix.ListWnd(lst, 'character', localization.GetByLabel('UI/Ship/ShipConfig/SelectAPilot'), None, 1, minChoices=1, isModal=1)
        if chosen:
            sm.GetService('clonejump').OfferShipCloneInstallation(chosen[1])

    def DestroyClone(self, *args):
        for each in self.sr.clonescroll.GetSelected():
            sm.GetService('clonejump').DestroyInstalledClone(each.cloneID)

    def GetShipItem(self):
        if session.solarsystemid:
            bp = sm.GetService('michelle').GetBallpark()
            if bp and self.shipid in bp.slimItems:
                return bp.slimItems[self.shipid]
        elif session.stationid:
            return sm.GetService('clientDogmaIM').GetDogmaLocation().GetShip()

    def GetShipModules(self):
        typeID = self.shipItem.typeID
        godmaSM = sm.GetService('godma').GetStateManager()
        hasModules = {}
        for module in self.shipmodules:
            if getattr(godmaSM.GetType(typeID), module[1], 0):
                nameString = ''
                if module[0] == 'CloneFacility':
                    nameString = localization.GetByLabel('UI/Ship/ShipConfig/CloneFacility')
                hasModules[module[0]] = nameString

        return hasModules

    def ShipMenu(self):
        return sm.GetService('menu').GetMenuFormItemIDTypeID(self.shipItem.itemID, self.shipItem.typeID)

    def ProcessSessionChange(self, isRemote, session, change):
        if session.shipid and 'shipid' in change:
            self.CloseByUser()
        elif 'solarsystemid' in change:
            self.CloseByUser()

    def OnShipCloneJumpUpdate(self):
        if self.sr.maintabs.GetSelectedArgs() == 'CloneFacility':
            self.ShowCloneFacility()