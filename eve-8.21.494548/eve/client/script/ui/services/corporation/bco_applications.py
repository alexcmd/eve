#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/corporation/bco_applications.py
import corpObject
import locks

class ApplicationsO(corpObject.base):
    __guid__ = 'corpObject.applications'

    def __init__(self, boundObject):
        corpObject.base.__init__(self, boundObject)
        self.corpApplications = None
        self.myApplications = None
        self.corpWelcomeMail = None

    def DoSessionChanging(self, isRemote, session, change):
        if 'charid' in change:
            self.myApplications = None
        if 'corpid' in change:
            self.corpApplications = None

    def Reset(self):
        self.corpApplications = None
        self.myApplications = None

    def OnCorporationApplicationChanged(self, corpID, applicantID, applicationID, newApplication):
        if applicantID == eve.session.charid:
            self.UpdateMyApplications(corpID, applicationID, newApplication)
        else:
            self.UpdateApplications(applicantID, applicationID, newApplication)
        sm.GetService('corpui').OnCorporationApplicationChanged(corpID, applicantID, applicationID, newApplication)

    def UpdateMyApplications(self, corporationID, applicationID, newApplication):
        applications = self.GetMyApplications(corporationID)
        self.myApplications[corporationID] = self.UpdateApplicationSet(applicationID, newApplication, applications)

    def UpdateApplications(self, applicantID, applicationID, newApplication):
        applications = self.GetApplications(applicantID)
        self.corpApplications[applicantID] = self.UpdateApplicationSet(applicationID, newApplication, applications)

    def UpdateApplicationSet(self, applicationID, newApplication, applications):
        newSet = []
        if newApplication is None:
            for application in applications:
                if application.applicationID != applicationID:
                    newSet.append(newApplication)

        else:
            isAdd = True
            for application in applications:
                if application.applicationID == applicationID:
                    isAdd = False
                    newSet.append(newApplication)
                else:
                    newSet.append(application)

            if isAdd:
                newSet.append(newApplication)
        return newSet

    def GetMyApplications(self, corporationID = -1, forceUpdate = False):
        if self.myApplications is None or forceUpdate:
            self.myApplications = self.GetCorpRegistry().GetMyApplications()
        if corporationID != -1:
            if corporationID not in self.myApplications:
                self.myApplications[corporationID] = []
            return self.myApplications[corporationID]
        else:
            return self.myApplications

    def GetMyApplicationsWithStatus(self, status):
        applications = self.GetMyApplications()
        if 0 == len(applications):
            return applications
        res = []
        for corporationID in applications:
            for application in applications[corporationID]:
                if status is None or application.status in status:
                    res.append(application)

        return res

    def GetMyOldApplicationsWithStatus(self, status):
        applications = self.GetCorpRegistry().GetMyOldApplications()
        res = []
        for application in applications:
            if status is None or application.status in status:
                res.append(application)

        return res

    def GetApplications(self, characterID = -1, forceUpdate = False):
        if eve.session.corprole & const.corpRolePersonnelManager != const.corpRolePersonnelManager:
            return {}
        else:
            if self.corpApplications is None or forceUpdate:
                self.corpApplications = self.GetCorpRegistry().GetApplications()
            if characterID == -1:
                return self.corpApplications
            if characterID not in self.corpApplications:
                self.corpApplications[characterID] = []
            return self.corpApplications[characterID]

    def GetApplicationsWithStatus(self, status):
        applications = self.GetApplications()
        if 0 == len(applications):
            return applications
        res = []
        for characterID in applications:
            for application in applications[characterID]:
                if status is None or application.status in status:
                    res.append(application)

        return res

    def GetOldApplicationsWithStatus(self, status):
        applications = self.GetCorpRegistry().GetOldApplications()
        res = []
        for application in applications:
            if status is None or application.status in status:
                res.append(application)

        return res

    def InsertApplication(self, corporationID, applicationText):
        return self.GetCorpRegistry().InsertApplication(corporationID, applicationText)

    def UpdateApplicationOffer(self, applicationID, characterID, corporationID, applicationText, status, applicationDateTime = None):
        with locks.TempLock('UpdateApplicationOffer', lockClass=locks.Lock):
            return self.GetCorpRegistry().UpdateApplicationOffer(applicationID, characterID, corporationID, applicationText, status, applicationDateTime)

    def SetCorpWelcomeMail(self, welcomeMail):
        self.corpWelcomeMail = welcomeMail

    def GetCorpWelcomeMail(self):
        if self.corpWelcomeMail is None:
            self.corpWelcomeMail = self.GetCorpRegistry().GetCorpWelcomeMail()
        return self.corpWelcomeMail