#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/voucherCache.py
import service
import blue
import util
import uthread
import localization

class VoucherCache(service.Service):
    __exportedcalls__ = {'GetVoucher': [],
     'OnAdd': []}
    __guid__ = 'svc.voucherCache'
    __notifyevents__ = ['ProcessSessionChange']
    __servicename__ = 'voucherCache'
    __displayname__ = 'Voucher Cache Service'

    def __init__(self):
        service.Service.__init__(self)
        self.data = {}
        self.names = {}

    def Run(self, memStream = None):
        self.LogInfo('Starting Voucher Cache Service')
        self.data = {}
        self.names = {}
        self.ReleaseVoucherSvc()

    def Stop(self, memStream = None):
        self.ReleaseVoucherSvc()

    def ProcessSessionChange(self, isremote, session, change):
        if 'charid' in change:
            self.ReleaseVoucherSvc()

    def GetVoucherSvc(self):
        if hasattr(self, 'moniker') and self.moniker is not None:
            return self.moniker
        self.moniker = sm.RemoteSvc('voucher')
        return self.moniker

    def ReleaseVoucherSvc(self):
        if hasattr(self, 'moniker') and self.moniker is not None:
            self.moniker = None
            self.data = {}
            self.names = {}

    def GetVoucher(self, voucherID):
        while eve.session.mutating:
            self.LogInfo('GetVoucher - hang on session is mutating')
            blue.pyos.synchro.SleepWallclock(1)

        if not self.data.has_key(voucherID):
            voucher = self.GetVoucherSvc().GetObject(voucherID)
            if voucher is None:
                return
            self.data[voucherID] = voucher
            try:
                name, _desc = sm.GetService('addressbook').UnzipMemo(voucher.GetDescription())
                self.names[voucherID] = name
            except:
                self.LogWarn('Was trying to get a name from a voucher but I failed', voucherID)

        return self.data[voucherID]

    def OnAdd(self, vouchers):
        for voucher in vouchers:
            self.data[voucher.itemID] = voucher
            self.names[voucher.itemID] = voucher.text

    def PrimeVoucherNames(self, voucherIDs):
        uthread.Lock(self, 'PrimeVoucherNames')
        try:
            unprimed = []
            for voucherID in voucherIDs:
                if voucherID not in self.names:
                    unprimed.append(voucherID)

            if unprimed:
                vouchers = self.GetVoucherSvc().GetNames(unprimed)
                for voucher in vouchers:
                    unprimed.remove(voucher.voucherID)
                    self.names[voucher.voucherID] = voucher.text

                for voucherID in unprimed:
                    self.names[voucherID] = localization.GetByLabel('UI/Common/Bookmark')

        finally:
            uthread.UnLock(self, 'PrimeVoucherNames')

    def GetVoucherName(self, voucherID):
        if voucherID in self.names:
            return self.names[voucherID]
        row = self.GetVoucherSvc().GetNames([voucherID])
        if row:
            self.names[voucherID] = row[0].text
            return self.names[voucherID]