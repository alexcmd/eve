#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/station/fitting/minihangar.py
import uix
import xtriui
import uthread
import util
import uicls
import uiconst
import localization
import invCtrl

class CargoSlots(uicls.Container):
    __guid__ = 'xtriui.CargoSlots'

    def Startup(self, name, iconpath, flag, dogmaLocation):
        self.flag = flag
        self.sr.icon = uicls.Icon(parent=self, size=32, state=uiconst.UI_DISABLED, ignoreSize=True, icon=iconpath)
        self.sr.hint = name
        self.sr.hilite = uicls.Fill(parent=self, name='hilite', align=uiconst.RELATIVE, state=uiconst.UI_HIDDEN, idx=-1, width=32, height=self.height)
        self.sr.icon.color.a = 0.8
        uicls.Container(name='push', parent=self, align=uiconst.TOLEFT, width=32)
        self.sr.statusCont = uicls.Container(name='statusCont', parent=self, align=uiconst.TOLEFT, width=50)
        self.sr.statustext1 = uicls.EveLabelMedium(text='status', parent=self.sr.statusCont, name='cargo_statustext', left=0, top=2, idx=0, state=uiconst.UI_DISABLED, align=uiconst.TOPRIGHT)
        self.sr.statustext2 = uicls.EveLabelMedium(text='status', parent=self.sr.statusCont, name='cargo_statustext', left=0, top=14, idx=0, state=uiconst.UI_DISABLED, align=uiconst.TOPRIGHT)
        m3TextCont = uicls.Container(name='m3Cont', parent=self, align=uiconst.TOLEFT, width=12)
        self.sr.m3Text = uicls.EveLabelMedium(text=localization.GetByLabel('UI/Fitting/FittingWindow/CubicMeters'), parent=m3TextCont, name='m3', left=4, top=14, idx=0, state=uiconst.UI_NORMAL)
        self.dogmaLocation = dogmaLocation
        sm.GetService('inv').Register(self)
        self.invReady = 1

    def IsItemHere(self, item):
        return item.flagID == self.flag and item.locationID == eve.session.shipid

    def AddItem(self, item):
        self.Update()

    def UpdateItem(self, item, *etc):
        self.Update()

    def RemoveItem(self, item):
        self.Update()

    def OnMouseEnter(self, *args):
        self.DoMouseEntering()

    def OnMouseEnterDrone(self, *args):
        if eve.session.stationid:
            self.DoMouseEntering()

    def DoMouseEntering(self):
        self.Hilite(1)
        self.sr.statustext1.OnMouseEnter()
        self.sr.statustext2.OnMouseEnter()
        self.sr.m3Text.OnMouseEnter()

    def OnMouseExit(self, *args):
        self.Hilite(0)
        self.sr.statustext1.OnMouseExit()
        self.sr.statustext2.OnMouseExit()
        self.sr.m3Text.OnMouseExit()
        uthread.new(self.Update)

    def Hilite(self, state):
        self.sr.icon.color.a = [0.8, 1.0][state]

    def SetStatusText(self, text1, text2, color):
        self.sr.statustext1.text = text1
        self.sr.statustext2.text = localization.GetByLabel('UI/Fitting/FittingWindow/CargoUsage', color=color, text=text2)
        self.sr.statusCont.width = max(0, self.sr.statustext1.textwidth, self.sr.statustext2.textwidth)

    def GetCapacity(self, flag = None):
        ship = sm.StartService('godma').GetItem(eve.session.shipid)
        if not ship:
            self.sr.status.text = '-'
            return
        return ship.GetCapacity(flag)

    def OnDropData(self, dragObj, nodes):
        self.Hilite(0)

    def Update(self, multiplier = 1.0):
        cap = self.GetCapacity(self.flag)
        if not cap:
            return
        if not self or self.destroyed:
            return
        cap2 = cap.capacity * multiplier
        color = '<color=0xc0ffffff>'
        if multiplier != 1.0:
            color = '<color=0xffffff00>'
        used = util.FmtAmt(cap.used, showFraction=1)
        cap2 = util.FmtAmt(cap2, showFraction=1)
        self.SetStatusText(used, cap2, color)


class CargoDroneSlots(CargoSlots):
    __guid__ = 'xtriui.CargoDroneSlots'

    def GetCapacity(self, flag = None):
        return self.dogmaLocation.GetCapacity(util.GetActiveShip(), const.attributeDroneCapacity, const.flagDroneBay)

    def OnDropData(self, dragObj, nodes):
        invCtrl.ShipDroneBay(util.GetActiveShip()).OnDropData(nodes)
        CargoSlots.OnDropData(self, dragObj, nodes)


class CargoCargoSlots(CargoSlots):
    __guid__ = 'xtriui.CargoCargoSlots'

    def OnDropData(self, dragObj, nodes):
        self.Hilite(0)
        if len(nodes) == 1:
            item = nodes[0].item
            if cfg.IsShipFittingFlag(item.flagID):
                dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
                shipID = util.GetActiveShip()
                if cfg.IsFittableCategory(item.categoryID):
                    dogmaLocation.UnloadModuleToContainer(shipID, item.itemID, (shipID,), flag=const.flagCargo)
                    return
                if item.categoryID == const.categoryCharge:
                    dogmaLocation.UnloadChargeToContainer(shipID, item.itemID, (shipID,), const.flagCargo)
                    return
        invCtrl.ShipCargo(util.GetActiveShip()).OnDropData(nodes)
        CargoSlots.OnDropData(self, dragObj, nodes)

    def GetCapacity(self, flag = None):
        return self.dogmaLocation.GetCapacity(util.GetActiveShip(), const.attributeCapacity, const.flagCargo)