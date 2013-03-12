#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/infoPanels/infoPanelMissions.py
import uicls
import uiconst
import util
import blue
import localization
import infoPanel
import uiutil

class InfoPanelMissions(uicls.InfoPanelBase):
    __guid__ = 'uicls.InfoPanelMissions'
    default_name = 'InfoPanelMissions'
    panelTypeID = infoPanel.PANEL_MISSIONS
    label = 'UI/PeopleAndPlaces/AgentMissions'
    default_iconTexturePath = 'res:/UI/Texture/Classes/InfoPanels/Missions.png'
    hasSettings = False

    def ApplyAttributes(self, attributes):
        uicls.InfoPanelBase.ApplyAttributes(self, attributes)
        agentHeader = self.headerCls(name='agentHeader', parent=self.headerCont, align=uiconst.CENTERLEFT, text='<color=white>' + localization.GetByLabel(self.label))

    @staticmethod
    def IsAvailable():
        return bool(sm.GetService('infoPanel').GetAgentMissions())

    def ConstructNormal(self):
        self.mainCont.Flush()
        top = 0
        for bmInfo in sm.GetService('infoPanel').GetAgentMissions():
            if isinstance(bmInfo.missionNameID, (int, long)):
                missionName = localization.GetByMessageID(bmInfo.missionNameID)
            else:
                missionName = bmInfo.missionNameID
            m = uicls.UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self.mainCont, align=uiconst.TOPLEFT, top=top, label=missionName, texturePath='res:/UI/Texture/Icons/38_16_229.png', closeTexturePath='res:/UI/Texture/Icons/38_16_230.png', GetUtilMenu=(self.MissionMenu, bmInfo), maxWidth=infoPanel.PANELWIDTH - infoPanel.LEFTPAD)
            top += 20

    def MissionMenu(self, menuParent, bmInfo, *args):
        missionNameID = bmInfo.missionNameID
        bookmarks = bmInfo.bookmarks
        agentID = bmInfo.agentID
        startInfoColorTag = '<color=-2039584>'
        endColorTag = '</color>'
        endInfoTag = '</url>'
        for bm in bookmarks:
            bmTypeID = bm.typeID
            headerText = ''
            systemName = cfg.evelocations.Get(bm.solarsystemID).name
            headerText = bm.hint.replace(systemName, '')
            headerText = headerText.strip(' ').strip('-').strip(' ')
            header = menuParent.AddHeader(text=headerText)
            menuCont = menuParent.AddContainer(name='menuCont', align=uiconst.TOTOP, height=40)
            menuCont.GetEntryWidth = lambda mc = menuCont: self.GetContainerEntryWidth(mc)
            startLocationInfoTag = '<url=showinfo:%d//%d>' % (bmTypeID, bm.itemID)
            locationName = self.GetColorCodedSecurityStringForLocation(bm.solarsystemID, cfg.evelocations.Get(bm.itemID).name)
            locationText = localization.GetByLabel('UI/Agents/InfoLink', startInfoTag=startLocationInfoTag, startColorTag=startInfoColorTag, objectName=locationName, endColorTag=endColorTag, endnfoTag=endInfoTag)
            locationLabel = uicls.EveLabelMedium(text=locationText, parent=menuCont, name='location', align=uiconst.TOTOP, padLeft=6, state=uiconst.UI_NORMAL, maxLines=1)
            locationLabel.GetMenu = (self.GetLocationMenu, bm)
            if bm.itemID != session.stationid2:
                actionText, actionFuncAndArgs, actionIcon = self.FindButtonAction(bm.itemID, bm.solarsystemID, bm)
                menuParent.AddIconEntry(icon=actionIcon, text=actionText, callback=actionFuncAndArgs)
            menuParent.AddSpace()

        menuParent.AddDivider()
        menuParent.AddIconEntry(icon='res:/UI/Texture/Icons/38_16_190.png', text=localization.GetByLabel('UI/Agents/Commands/ReadDetails'), callback=(self.ReadDetails, agentID))
        menuParent.AddIconEntry(icon='res:/UI/Texture/classes/Chat/AgentChat.png', text=localization.GetByLabel('UI/Chat/StartConversationAgent'), callback=(self.TalkToAgent, agentID))

    def FindButtonAction(self, itemID, solarsystemID, bookmark, *args):
        text = ''
        if solarsystemID != session.solarsystemid:
            text = localization.GetByLabel('UI/Inflight/SetDestination')
            funcAndArgs = (sm.StartService('starmap').SetWaypoint, itemID, True)
            icon = 'res:/UI/Texture/classes/LocationInfo/destination.png'
        elif util.IsStation(itemID):
            text = localization.GetByLabel('UI/Inflight/DockInStation')
            funcAndArgs = (sm.GetService('menu').Dock, itemID)
            icon = 'res:/ui/texture/icons/44_32_9.png'
        else:
            bp = sm.StartService('michelle').GetBallpark()
            ownBall = bp and bp.GetBall(session.shipid) or None
            dist = sm.GetService('menu').FindDist(0, bookmark, ownBall, bp)
            checkApproachDist = dist and dist < const.minWarpDistance
            if checkApproachDist:
                text = localization.GetByLabel('UI/Inflight/ApproachObject')
                funcAndArgs = (sm.GetService('menu').ApproachLocation, bookmark)
                icon = 'res:/ui/texture/icons/44_32_23.png'
            else:
                defaultWarpDist = sm.GetService('menu').GetDefaultActionDistance('WarpTo')
                text = localization.GetByLabel('UI/Inflight/WarpToBookmark')
                funcAndArgs = (sm.GetService('menu').WarpToBookmark, bookmark, defaultWarpDist)
                icon = 'res:/ui/texture/icons/44_32_18.png'
        return (text, funcAndArgs, icon)

    def GetColorCodedSecurityStringForLocation(self, solarsystemID, itemName):
        sec, col = util.FmtSystemSecStatus(sm.GetService('map').GetSecurityStatus(solarsystemID), 1)
        col.a = 1.0
        color = util.StrFromColor(col)
        text = '%s <color=%s>%s</color>' % (itemName, color, sec)
        return text

    def GetAgentMenu(self, agentID, *args):
        m = sm.GetService('menu').CharacterMenu(agentID)
        return m

    def GetLocationMenu(self, bm):
        m = sm.GetService('menu').CelestialMenu(bm.itemID, None, None, 0, None, None, bm)
        return m

    def ReadDetails(self, agentID, *args):
        sm.GetService('agents').PopupMissionJournal(agentID)

    def TalkToAgent(self, agentID, *args):
        sm.StartService('agents').InteractWith(agentID)

    def GetContainerEntryWidth(self, menuCont, *args):
        longestText = 0
        for child in menuCont.children:
            if isinstance(child, uicls.Label):
                if longestText < child.textwidth:
                    longestText = child.textwidth

        return longestText + 20