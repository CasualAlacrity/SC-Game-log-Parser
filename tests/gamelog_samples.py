"""Line shapes are from docs/event-reference.md. Player handles and IDs are
synthetic; the numbers (prices, quantities, location IDs) are the real ones from the logs."""

PLAYER = "playerId[800000000001]"
GUID = "7f4599b0-0000-0000-0000-800000000002"

BUY = (
    "<2026-10-19T21:51:11.123Z> [Notice] <CEntityComponentCommodityUIProvider::SendCommodityBuyRequest> "
    f"Sending SShopCommodityBuyRequest - {PLAYER} shopId[800000000003] shopName[SCShop_Admin_lt_base_g] "
    "kioskId[800000000004] price[4735584.000000] shopPricePerCentiSCU[73.993500] "
    f"resourceGUID[{GUID}] autoLoading[1] quantity[64000.000000 cSCU] "
    "Cargo Box Data: boxSize[32.000000] | unitAmount[20] [Team_Shops][Shops]"
)
SELL = (
    "<2026-10-19T22:10:41.500Z> [Notice] <CEntityComponentCommodityUIProvider::SendCommoditySellRequest> "
    f"Sending SShopCommoditySellRequest - {PLAYER} shopId[800000000005] shopName[SCShop_Admin_lt_base_g] "
    f"kioskId[800000000006] amount[5443200.000000] resourceGUID[{GUID}] autoLoading[1] quantity[640] "
    "transactionMode[ResourceContainer] Cargo Box Data: [boxSize[32] | unitAmount[15]] [Team_Shops][Shops]"
)
MOVE = (
    "<2026-10-19T22:05:17.000Z> [Notice] <Update Inventory Location> Player [Someone] is changing location. "
    "Landing [0] -> [1510935576]. Location [2537229937] -> [1510935576]. Pending [0] [Team_Inventory][Inventory]"
)
NAMED = (
    "<2026-10-19T22:05:17.000Z> [Notice] <RequestLocationInventory> "
    "Player[Someone] requested inventory for Location[RR_CRU_L1] [Team_Inventory][Inventory]"
)

MISSION = "9d33a156-1111-2222-3333-800000000007"
DEFINITION = "90ad94c4-1111-2222-3333-800000000007"
MARKER = (
    "<2026-10-18T20:07:15.307Z> [Notice] <CLocalMissionPhaseMarker::CreateMarker> Creating objective marker: "
    f"missionId [{MISSION}], generator name [VisitingIasi], contract [Iasi_Salvage_Small_2], "
    f"contractDefinitionId[{DEFINITION}], objectiveId [dropoff_246aa48e-1111-2222-3333-800000000007_0], "
    "markerEntityId [2520], zoneHostId [800000000008], position [x: 1.0, y: 2.0, z: 3.0] "
    "[Team_MissionFeatures][Missions]"
)
HAUL = (
    '<2026-10-18T20:07:16.000Z> [Notice] <SHUDEvent_OnNotification> Added notification "New Objective: '
    'Deliver 0/90 SCU of Distilled Spirits to Everus Harbor: " [12] to queue. New queue size: 1, '
    f"MissionId: [{MISSION}], ObjectiveId: [dropoff_x_0] [Team_UI][HUD]"
)
END = (
    "<2026-10-18T21:30:00.000Z> [Notice] <EndMission> Ending mission for player. "
    f"MissionId[{MISSION}] Player[Someone] PlayerId[800000000001] CompletionType[Complete] "
    "Reason[Mission Ended] [Team_MissionFeatures][Missions]"
)
SHARE = (
    "<2026-10-18T20:00:00.000Z> [Notice] <MissionShared> Received share push message: "
    f"ownerId[800000000009] - missionId[{MISSION}] [Team_MissionFeatures][Missions]"
)
KIOSK_ITEM_BUY = (
    "<2026-10-20T08:05:00.000Z> [Notice] <CEntityComponentShopUIProvider::SendShopBuyRequest> "
    "Sending buy request - playerId[800000000001] shopId[800000000010] shopName[SCShop_LiveFire_Truckstop02-001] "
    "kioskId[800000000011] client_price[396.000000] itemClassGUID[0988e9ce-1111-2222-3333-800000000007] "
    "itemName[klwe_rifle_energy_01_mag] quantity[1] [Team_Shops][Shops]"
)
WALL_ITEM_BUY = (
    "<2026-10-20T08:06:00.000Z> [Notice] <CEntityComponentShoppingProvider::SendStandardItemBuyRequest> "
    "Sending buy request - playerId[800000000001] shopId[800000000010] shopName[SCShop_LiveFire_Truckstop02-001] "
    "kioskId[0] client_price[4699.000000] itemClassGUID[8bc41f99-1111-2222-3333-800000000007] "
    "itemName[klwe_rifle_energy_01] quantity[1] currencyType[UEC] [Team_Shops][Shops]"
)
FAILED_BUY_AUTOLOAD = (
    "<2026-10-23T09:36:15.436Z> [Error] <CEntityComponentCommodityUIProvider::RmToken_CommodityTransactionResponse> "
    "Commodity Transaction Response Error - result[AutoLoadStartFailed] type[Buying] [Team_Shops][Shops]"
)
FAILED_BUY_CARGO = (
    "<2026-10-23T09:42:29.290Z> [Error] <CEntityComponentCommodityUIProvider::RmToken_CommodityTransactionResponse> "
    "Commodity Transaction Response Error - result[CargoCreationFailed] type[Buying] [Team_Shops][Shops]"
)
ITEM_RESPONSE = (
    "<2026-10-20T08:05:00.500Z> [Notice] <CEntityComponentShopUIProvider::RmShopFlowResponse> "
    "shopId[800000000010] kioskId[800000000011] kioskState[BuyRequestProcessing] result[Success] type[Buying] "
    "[Team_Shops][Shops]"
)
CLEAR_DRIVER = (
    "<2026-10-18T20:30:00.000Z> [Notice] <Vehicle Control Flow> ClearDriver: Local client node [800000000001] "
    "releasing control token for 'AEGS_Reclaimer_800000000012' [800000000012] [Team_Vehicles][Vehicle]"
)
SPAWNING = (
    "<2026-10-20T08:20:28.000Z> [Notice] <CEntityComponentShipListProvider::SetVehicleSpawningInformations> "
    "SetVehicleSpawningInformations - VehicleEntityId: [800000000013], LandingArea: Someone's Large Hangar "
    "[Team_Vehicles]"
)
ATC_NAMED = (
    "<2026-10-20T08:20:31.000Z> [Notice] <ATC_Reset_VehiclesBeingStoredCleared> "
    "ATC_Reset_VehiclesBeingStoredCleared ATC 'GAMA_Railen_ShipATCDataManager_800000000014' [Team_Vehicles]"
)
FREIGHT = (
    "<2026-10-20T08:34:00.000Z> [Notice] <CEntityComponentFreightElevatorUIProvider::FillUnstowRequest> "
    "[FreightElevatorKioskUIProvider] FreightElevatorKiosk_FreightElevator_Util_HangarLarge[800000000015] - "
    "Processed bindings into transfer request - Entities: 4, Location: 1510935576 - RequestId: 4, ItemBank: 0"
)

# Real lines from the 2026-10-20 salvage session (build 4.10.197.2878); no handles in them.
NOTICE_ACCEPTED = (
    '<2026-10-20T10:09:53.241Z> [Notice] <SHUDEvent_OnNotification> Added notification '
    '"Contract Accepted:  RSI Disc. Month: UCM Order (S): " [9] to queue. New queue size: 1, '
    "MissionId: [e07f1e76-3897-4082-a7b6-f5b81372cead], ObjectiveId: [] [Team_CoreGameplayFeatures][Missions][Comms]"
)
NOTICE_ZONE = (
    '<2026-10-20T09:59:23.546Z> [Notice] <SHUDEvent_OnNotification> Added notification "Entered Monitored Space: " '
    "[0] to queue. New queue size: 1, MissionId: [00000000-0000-0000-0000-000000000000], ObjectiveId: [] "
    "[Team_CoreGameplayFeatures][Missions][Comms]"
)
NOTICE_WRAPPED_FIRST_LINE = (
    '<2026-10-20T10:13:39.653Z> [Notice] <SHUDEvent_OnNotification> Added notification '
    '"Objective Complete: Locate Salvage Claim #67011'
)
HEADER = "<2026-10-20T09:56:30.165Z> FileVersion: 4.10.197.2878"
CONTEXT_PU = (
    '<2026-10-20T09:58:42.511Z> [Notice] <ContextEstablisherTaskFinished> establisher="CReplicationModel" '
    'message="CET completed" taskname="ModelWaitForViews" state=eCVS_ResetEntitySystem(1) status="Finished" '
    'runningTime=0.127991 timeoutOffset=0.000000 numRuns=7 map="megamap" gamerules="SC_Default" sessionId="x"'
)
ATC_REAL = (
    "<2026-10-20T09:59:17.934Z> [Notice] <ATC_Reset_VehiclesBeingStoredCleared> ATC "
    "'AEGS_Sabre_ShipATCDataManager_800000000016' [800000000016] clearing 0 entries from vehicles-being-stored "
    "list on Reset [Team_MissionFeatures][ATC]"
)

# Real lines, 2026-10-20 12:24Z (Orison): handle and player ID replaced.
FREIGHT_GRID = (
    "<2026-10-20T12:24:09.584Z> [Notice] <InventoryManagement> Freight Inventory Grid InventoryDataRequest "
    "Successful for Player[Someone] Inventory[800000000001:Location:1105811199] Inventory Result Item Count:[250]. "
    "[Team_CoreGameplayFeatures][Inventory][InventoryContainer]"
)
QUIT = (
    "<2026-10-20T12:24:40.580Z> [Notice] <SystemQuit> CSystem::Quit invoked with - cause=30016, "
    "reason=Quit via console command, exitCode=0, thread id=38784, main thread id=38784 [Team_Unknown][System]"
)
