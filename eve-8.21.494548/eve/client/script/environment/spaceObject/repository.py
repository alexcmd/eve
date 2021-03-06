#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/repository.py
import spaceObject

def GetGroupDict():
    d = {const.groupAsteroidBelt: spaceObject.AsteroidBelt,
     const.groupBillboard: spaceObject.Billboard,
     const.groupBiomass: spaceObject.Corpse,
     const.groupCapsule: spaceObject.Capsule,
     const.groupCargoContainer: spaceObject.Cargo,
     const.groupWreck: spaceObject.Wreck,
     const.groupCloud: spaceObject.Cloud,
     const.groupCombatDrone: spaceObject.CombatDroneLight,
     const.groupComet: spaceObject.Comet,
     const.groupFighterDrone: spaceObject.CombatDroneLight,
     const.groupFighterBomber: spaceObject.CombatDroneLight,
     const.groupLCODrone: spaceObject.CombatDrone,
     const.groupElectronicWarfareDrone: spaceObject.CombatDroneLight,
     const.groupStasisWebifyingDrone: spaceObject.CombatDroneLight,
     const.groupSalvageDrone: spaceObject.CombatDroneLight,
     const.groupUnanchoringDrone: spaceObject.CombatDroneLight,
     const.groupRepairDrone: spaceObject.CombatDroneLight,
     const.groupWarpScramblingDrone: spaceObject.CombatDroneLight,
     const.groupCapDrainDrone: spaceObject.CombatDroneLight,
     const.groupLargeCollidableObject: spaceObject.LargeCollidableObject,
     const.groupLargeCollidableStructure: spaceObject.LargeCollidableStructure,
     const.groupDeadspaceOverseersStructure: spaceObject.LargeCollidableStructure,
     const.groupMiningDrone: spaceObject.MiningDrone,
     const.groupLogisticDrone: spaceObject.CombatDroneLight,
     const.groupMoon: spaceObject.Planet,
     const.groupPlanet: spaceObject.Planet,
     const.groupRogueDrone: spaceObject.CombatDrone,
     const.groupSecureCargoContainer: spaceObject.Cargo,
     const.groupAuditLogSecureContainer: spaceObject.Cargo,
     const.groupSpawnContainer: spaceObject.Cargo,
     const.groupDeadspaceOverseersBelongings: spaceObject.Cargo,
     const.groupFreightContainer: spaceObject.Cargo,
     const.groupStargate: spaceObject.Stargate,
     const.groupStation: spaceObject.Station,
     const.groupDestructibleStationServices: spaceObject.Station,
     const.groupSun: spaceObject.Sun,
     const.groupSecondarySun: spaceObject.BackgroundObject,
     const.groupTemporaryCloud: spaceObject.Cloud,
     const.groupMobileWarpDisruptor: spaceObject.MobileWarpDisruptor,
     const.groupMobileMicroJumpDisruptor: spaceObject.MobileWarpDisruptor,
     const.groupWarpGate: spaceObject.WarpGate,
     const.groupForceField: spaceObject.ForceField,
     const.groupDestructibleSentryGun: spaceObject.SentryGun,
     const.groupDeadspaceOverseersSentry: spaceObject.SentryGun,
     const.groupMobileLaserSentry: spaceObject.StructureSentryGun,
     const.groupMobileHybridSentry: spaceObject.StructureSentryGun,
     const.groupMobileProjectileSentry: spaceObject.StructureSentryGun,
     const.groupMobileSentryGun: spaceObject.SentryGun,
     const.groupProtectiveSentryGun: spaceObject.SentryGun,
     const.groupSentryGun: spaceObject.SentryGun,
     const.groupConcordDrone: spaceObject.EntityShip,
     const.groupConvoy: spaceObject.EntityShip,
     const.groupConvoyDrone: spaceObject.EntityShip,
     const.groupCustomsOfficial: spaceObject.EntityShip,
     const.groupFactionDrone: spaceObject.EntityShip,
     const.groupMissionDrone: spaceObject.EntityShip,
     const.groupPirateDrone: spaceObject.EntityShip,
     const.groupPoliceDrone: spaceObject.EntityShip,
     const.groupTutorialDrone: spaceObject.EntityShip,
     const.groupStorylineMissionBattleship: spaceObject.EntityShip,
     const.groupStorylineMissionCruiser: spaceObject.EntityShip,
     const.groupStorylineMissionFrigate: spaceObject.EntityShip,
     const.groupStorylineBattleship: spaceObject.EntityShip,
     const.groupStorylineCruiser: spaceObject.EntityShip,
     const.groupStorylineFrigate: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelBattleship: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelCruiser: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelDestroyer: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelFrigate: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelHauler: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelOfficer: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersBattleship: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersCruiser: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersDestroyer: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersFrigate: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersHauler: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersOfficer: spaceObject.EntityShip,
     const.groupAsteroidGuristasBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidGuristasBattleship: spaceObject.EntityShip,
     const.groupAsteroidGuristasCruiser: spaceObject.EntityShip,
     const.groupAsteroidGuristasDestroyer: spaceObject.EntityShip,
     const.groupAsteroidGuristasFrigate: spaceObject.EntityShip,
     const.groupAsteroidGuristasHauler: spaceObject.EntityShip,
     const.groupAsteroidGuristasOfficer: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationBattleship: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationCruiser: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationDestroyer: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationFrigate: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationHauler: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationOfficer: spaceObject.EntityShip,
     const.groupAsteroidSerpentisBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidSerpentisBattleship: spaceObject.EntityShip,
     const.groupAsteroidSerpentisCruiser: spaceObject.EntityShip,
     const.groupAsteroidSerpentisDestroyer: spaceObject.EntityShip,
     const.groupAsteroidSerpentisFrigate: spaceObject.EntityShip,
     const.groupAsteroidSerpentisHauler: spaceObject.EntityShip,
     const.groupAsteroidSerpentisOfficer: spaceObject.EntityShip,
     const.groupDeadspaceAngelCartelBattleCruiser: spaceObject.EntityShip,
     const.groupDeadspaceAngelCartelBattleship: spaceObject.EntityShip,
     const.groupDeadspaceAngelCartelCruiser: spaceObject.EntityShip,
     const.groupDeadspaceAngelCartelDestroyer: spaceObject.EntityShip,
     const.groupDeadspaceAngelCartelFrigate: spaceObject.EntityShip,
     const.groupDeadspaceBloodRaidersBattleCruiser: spaceObject.EntityShip,
     const.groupDeadspaceBloodRaidersBattleship: spaceObject.EntityShip,
     const.groupDeadspaceBloodRaidersCruiser: spaceObject.EntityShip,
     const.groupDeadspaceBloodRaidersDestroyer: spaceObject.EntityShip,
     const.groupDeadspaceBloodRaidersFrigate: spaceObject.EntityShip,
     const.groupDeadspaceGuristasBattleCruiser: spaceObject.EntityShip,
     const.groupDeadspaceGuristasBattleship: spaceObject.EntityShip,
     const.groupDeadspaceGuristasCruiser: spaceObject.EntityShip,
     const.groupDeadspaceGuristasDestroyer: spaceObject.EntityShip,
     const.groupDeadspaceGuristasFrigate: spaceObject.EntityShip,
     const.groupDeadspaceSanshasNationBattleCruiser: spaceObject.EntityShip,
     const.groupDeadspaceSanshasNationBattleship: spaceObject.EntityShip,
     const.groupDeadspaceSanshasNationCruiser: spaceObject.EntityShip,
     const.groupDeadspaceSanshasNationDestroyer: spaceObject.EntityShip,
     const.groupDeadspaceSanshasNationFrigate: spaceObject.EntityShip,
     const.groupDeadspaceSerpentisBattleCruiser: spaceObject.EntityShip,
     const.groupDeadspaceSerpentisBattleship: spaceObject.EntityShip,
     const.groupDeadspaceSerpentisCruiser: spaceObject.EntityShip,
     const.groupDeadspaceSerpentisDestroyer: spaceObject.EntityShip,
     const.groupDeadspaceSerpentisFrigate: spaceObject.EntityShip,
     const.groupDeadspaceSleeperSleeplessPatroller: spaceObject.EntitySleeper,
     const.groupDeadspaceSleeperSleeplessSentinel: spaceObject.EntitySleeper,
     const.groupDeadspaceSleeperSleeplessDefender: spaceObject.EntitySleeper,
     const.groupDeadspaceSleeperAwakenedPatroller: spaceObject.EntitySleeper,
     const.groupDeadspaceSleeperAwakenedSentinel: spaceObject.EntitySleeper,
     const.groupDeadspaceSleeperAwakenedDefender: spaceObject.EntitySleeper,
     const.groupDeadspaceSleeperEmergentPatroller: spaceObject.EntitySleeper,
     const.groupDeadspaceSleeperEmergentSentinel: spaceObject.EntitySleeper,
     const.groupDeadspaceSleeperEmergentDefender: spaceObject.EntitySleeper,
     const.groupWarpDisruptionProbe: spaceObject.SpaceObject,
     const.groupBomb: spaceObject.Bomb,
     const.groupBombECM: spaceObject.Bomb,
     const.groupBombEnergy: spaceObject.Bomb,
     const.groupHarvestableCloud: spaceObject.HarvestableGasCloud,
     const.groupAsteroidAngelCartelCommanderBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelCommanderCruiser: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelCommanderDestroyer: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelCommanderFrigate: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersCommanderBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersCommanderCruiser: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersCommanderDestroyer: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersCommanderFrigate: spaceObject.EntityShip,
     const.groupAsteroidGuristasCommanderBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidGuristasCommanderCruiser: spaceObject.EntityShip,
     const.groupAsteroidGuristasCommanderDestroyer: spaceObject.EntityShip,
     const.groupAsteroidGuristasCommanderFrigate: spaceObject.EntityShip,
     const.groupAsteroidRogueDroneBattleCruiser: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneBattleship: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneCruiser: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneDestroyer: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneFrigate: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneHauler: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneSwarm: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneOfficer: spaceObject.CombatDrone,
     const.groupAsteroidSanshasNationCommanderBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationCommanderCruiser: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationCommanderDestroyer: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationCommanderFrigate: spaceObject.EntityShip,
     const.groupAsteroidSerpentisCommanderBattleCruiser: spaceObject.EntityShip,
     const.groupAsteroidSerpentisCommanderCruiser: spaceObject.EntityShip,
     const.groupAsteroidSerpentisCommanderDestroyer: spaceObject.EntityShip,
     const.groupAsteroidSerpentisCommanderFrigate: spaceObject.EntityShip,
     const.groupDeadspaceRogueDroneBattleCruiser: spaceObject.CombatDrone,
     const.groupDeadspaceRogueDroneBattleship: spaceObject.CombatDrone,
     const.groupDeadspaceRogueDroneCruiser: spaceObject.CombatDrone,
     const.groupDeadspaceRogueDroneDestroyer: spaceObject.CombatDrone,
     const.groupDeadspaceRogueDroneFrigate: spaceObject.CombatDrone,
     const.groupDeadspaceRogueDroneSwarm: spaceObject.CombatDrone,
     const.groupInvasionSanshaNationBattleship: spaceObject.EntityShip,
     const.groupInvasionSanshaNationCapital: spaceObject.EntityShip,
     const.groupInvasionSanshaNationCruiser: spaceObject.EntityShip,
     const.groupInvasionSanshaNationFrigate: spaceObject.EntityShip,
     const.groupInvasionSanshaNationIndustrial: spaceObject.EntityShip,
     const.groupMissionGenericBattleships: spaceObject.EntityShip,
     const.groupMissionGenericCruisers: spaceObject.EntityShip,
     const.groupMissionGenericFrigates: spaceObject.EntityShip,
     const.groupDeadspaceOverseerFrigate: spaceObject.EntityShip,
     const.groupDeadspaceOverseerCruiser: spaceObject.EntityShip,
     const.groupDeadspaceOverseerBattleship: spaceObject.EntityShip,
     const.groupMissionThukkerBattlecruiser: spaceObject.EntityShip,
     const.groupMissionThukkerBattleship: spaceObject.EntityShip,
     const.groupMissionThukkerCruiser: spaceObject.EntityShip,
     const.groupMissionThukkerDestroyer: spaceObject.EntityShip,
     const.groupMissionThukkerFrigate: spaceObject.EntityShip,
     const.groupMissionThukkerOther: spaceObject.EntityShip,
     const.groupMissionGenericBattleCruisers: spaceObject.EntityShip,
     const.groupMissionGenericDestroyers: spaceObject.EntityShip,
     const.groupAsteroidRogueDroneCommanderFrigate: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneCommanderDestroyer: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneCommanderCruiser: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneCommanderBattleCruiser: spaceObject.CombatDrone,
     const.groupAsteroidRogueDroneCommanderBattleship: spaceObject.EntityShip,
     const.groupAsteroidAngelCartelCommanderBattleship: spaceObject.EntityShip,
     const.groupAsteroidBloodRaidersCommanderBattleship: spaceObject.EntityShip,
     const.groupAsteroidGuristasCommanderBattleship: spaceObject.EntityShip,
     const.groupAsteroidSanshasNationCommanderBattleship: spaceObject.EntityShip,
     const.groupAsteroidSerpentisCommanderBattleship: spaceObject.EntityShip,
     const.groupMissionAmarrEmpireCarrier: spaceObject.EntityShip,
     const.groupMissionCaldariStateCarrier: spaceObject.EntityShip,
     const.groupMissionGallenteFederationCarrier: spaceObject.EntityShip,
     const.groupMissionMinmatarRepublicCarrier: spaceObject.EntityShip,
     const.groupMissionFighterDrone: spaceObject.CombatDrone,
     const.groupMissionGenericFreighters: spaceObject.EntityShip,
     const.groupMissionAmarrEmpireFrigate: spaceObject.EntityShip,
     const.groupMissionAmarrEmpireDestroyer: spaceObject.EntityShip,
     const.groupMissionAmarrEmpireBattlecruiser: spaceObject.EntityShip,
     const.groupMissionAmarrEmpireBattleship: spaceObject.EntityShip,
     const.groupMissionAmarrEmpireCruiser: spaceObject.EntityShip,
     const.groupMissionAmarrEmpireOther: spaceObject.EntityShip,
     const.groupMissionCaldariStateFrigate: spaceObject.EntityShip,
     const.groupMissionCaldariStateDestroyer: spaceObject.EntityShip,
     const.groupMissionCaldariStateBattlecruiser: spaceObject.EntityShip,
     const.groupMissionCaldariStateCruiser: spaceObject.EntityShip,
     const.groupMissionCaldariStateBattleship: spaceObject.EntityShip,
     const.groupMissionGallenteFederationFrigate: spaceObject.EntityShip,
     const.groupMissionGallenteFederationDestroyer: spaceObject.EntityShip,
     const.groupMissionGallenteFederationCruiser: spaceObject.EntityShip,
     const.groupMissionGallenteFederationBattleship: spaceObject.EntityShip,
     const.groupMissionGallenteFederationBattlecruiser: spaceObject.EntityShip,
     const.groupMissionMinmatarRepublicFrigate: spaceObject.EntityShip,
     const.groupMissionMinmatarRepublicDestroyer: spaceObject.EntityShip,
     const.groupMissionMinmatarRepublicBattlecruiser: spaceObject.EntityShip,
     const.groupMissionMinmatarRepublicCruiser: spaceObject.EntityShip,
     const.groupMissionMinmatarRepublicBattleship: spaceObject.EntityShip,
     const.groupFWMinmatarRepublicFrigate: spaceObject.EntityShip,
     const.groupFWMinmatarRepublicDestroyer: spaceObject.EntityShip,
     const.groupFWMinmatarRepublicCruiser: spaceObject.EntityShip,
     const.groupFWMinmatarRepublicBattlecruiser: spaceObject.EntityShip,
     const.groupFWGallenteFederationFrigate: spaceObject.EntityShip,
     const.groupFWGallenteFederationDestroyer: spaceObject.EntityShip,
     const.groupFWGallenteFederationCruiser: spaceObject.EntityShip,
     const.groupFWGallenteFederationBattlecruiser: spaceObject.EntityShip,
     const.groupFWCaldariStateFrigate: spaceObject.EntityShip,
     const.groupFWCaldariStateDestroyer: spaceObject.EntityShip,
     const.groupFWCaldariStateCruiser: spaceObject.EntityShip,
     const.groupFWCaldariStateBattlecruiser: spaceObject.EntityShip,
     const.groupFWAmarrEmpireFrigate: spaceObject.EntityShip,
     const.groupFWAmarrEmpireDestroyer: spaceObject.EntityShip,
     const.groupFWAmarrEmpireCruiser: spaceObject.EntityShip,
     const.groupFWAmarrEmpireBattlecruiser: spaceObject.EntityShip,
     const.groupMissionCONCORDFrigate: spaceObject.EntityShip,
     const.groupMissionCONCORDCruiser: spaceObject.EntityShip,
     const.groupMissionCONCORDBattleship: spaceObject.EntityShip,
     const.groupMissionKhanidFrigate: spaceObject.EntityShip,
     const.groupMissionKhanidCruiser: spaceObject.EntityShip,
     const.groupMissionKhanidBattleship: spaceObject.EntityShip,
     const.groupMissionMorduFrigate: spaceObject.EntityShip,
     const.groupMissionMorduCruiser: spaceObject.EntityShip,
     const.groupMissionMorduBattleship: spaceObject.EntityShip,
     const.groupMissionFactionFrigates: spaceObject.EntityShip,
     const.groupMissionFactionCruisers: spaceObject.EntityShip,
     const.groupMissionFactionBattleships: spaceObject.EntityShip,
     const.groupDestructibleAgentsInSpace: spaceObject.EntityShip,
     const.groupScannerProbe: spaceObject.ScannerProbe,
     const.groupWormhole: spaceObject.Wormhole,
     const.groupStationImprovementPlatform: spaceObject.PlayerOwnedStructure,
     const.groupConstructionPlatform: spaceObject.PlayerOwnedStructure,
     const.groupSovereigntyClaimMarkers: spaceObject.SovereigntyClaimMarker,
     const.groupInfrastructureHub: spaceObject.SovereigntyInfrastructueHub,
     const.groupBeacon: spaceObject.LargeCollidableObject,
     const.groupSatellite: spaceObject.Satellite,
     const.groupPlanetaryCustomsOffices: spaceObject.CustomsOffice}
    for group in cfg.invgroups:
        if group.fittableNonSingleton and not d.has_key(group.groupID):
            d[group.groupID] = spaceObject.Missile

    return d


def GetCategoryDict():
    return {const.categoryShip: spaceObject.Ship,
     const.categoryDeployable: spaceObject.PlayerOwnedStructure,
     const.categoryStructure: spaceObject.PlayerOwnedStructure,
     const.categorySovereigntyStructure: spaceObject.PlayerOwnedStructure,
     const.categoryAsteroid: spaceObject.Asteroid,
     const.categoryOrbital: spaceObject.BasicOrbital}


exports = {'spaceObject.GetGroupDict': GetGroupDict,
 'spaceObject.GetCategoryDict': GetCategoryDict}