# Game.log API reference

This reference describes the events emitted by sc-gamelog 0.1.0. The [combined signal catalog](signal-catalog.md) tracks additional formats from VerseKit and Bedrock as candidates for the standalone package.

Every event has a timezone-aware UTC `timestamp: datetime` parsed from the log. The tables list the name and Python type of every other field. Event objects carry no dedicated player handle or player ID. Free-text fields and entity IDs can still contain identifying information, so review them before sharing an export. The parser reads individual lines. The watcher separates startup history from live events and suppresses repeated observations of the same game mode. [Event models](../src/sc_gamelog/events.py) · [Parser](../src/sc_gamelog/parser.py) · [Watcher](../src/sc_gamelog/watcher.py)

## Parse a line

`parse_line(line: str) -> GameLogEvent | None` accepts a single log line with or without its
trailing newline. It returns a typed event or `None` when the line is unsupported or cannot
be parsed. Use `isinstance` to narrow the return value. For example, parsing the
[commodity buy line below](#commoditybuy) returns a `CommodityBuy` with
`quantity_scu == 640.0` and `autoload is True`.

## Track live buy requests

Save this as `track_buys.py` and run `python track_buys.py /path/to/Game.log`.
It prints new commodity buy requests as they appear. The `Queue` hands events from the
watcher thread to the main thread, where the application can display or process them.

```python
from argparse import ArgumentParser
from pathlib import Path
from queue import Queue

from sc_gamelog.dispatch import GameLogEvents
from sc_gamelog.events import CommodityBuy
from sc_gamelog.watcher import GameLogWatcher


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("game_log", type=Path)
    args = parser.parse_args()

    buys: Queue[CommodityBuy] = Queue()
    events = GameLogEvents()
    events.on(CommodityBuy, buys.put)

    watcher = GameLogWatcher(args.game_log, on_event=events.publish)
    watcher.start()
    try:
        while True:
            event = buys.get()
            print(
                f"{event.timestamp.isoformat()} BUY REQUEST "
                f"{event.quantity_scu:g} SCU for {event.total_auec:,} aUEC "
                f"(autoload requested: {event.autoload})",
                flush=True,
            )
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()


if __name__ == "__main__":
    main()
```

`GameLogEvents.on(EventType, callback)` subscribes to an exact event class.
`on_any(callback)` receives all event types. You can also pass a single callback directly as
`GameLogWatcher(..., on_event=callback)`. The watcher starts at the end of a file that already
exists when polling begins. Pass a separate `on_history` callback to read startup history for
state reconstruction. A buy request only reports what was requested.

## Session, place and ships

| Event | Captured fields | Omitted fields and interpretation limits |
| --- | --- | --- |
| [`LogStarted`](#logstarted) | `build: str` | The build comes from the startup header. The event carries no hardware details or account data. |
| [`GameModeSeen`](#gamemodeseen) | `gamerules: str` | Connection and context details are omitted. A mode observation supplies no shard identity. |
| [`GameQuit`](#gamequit) | `reason: str`, `exit_code: int` | An observed shutdown line. A session can end without this event. |
| [`LocationChanged`](#locationchanged) | `landing_id: int`, `location_id: int` | Keeps the new IDs, with zero used for transit in the landing field. Omits previous IDs, coordinates and place names. |
| [`LocationNamed`](#locationnamed) | `code: str` | Keeps the inventory location code. Opening inventory can emit the same signal as landing. |
| [`ShipSeatLeft`](#shipseatleft) | `ship_class: str`, `entity_id: str` | Control release supplies class and session entity ID. Ownership and loadout are outside its scope. |
| [`ShipSpawning`](#shipspawning) | `entity_id: str` | The event carries no ship class or ownership. |
| [`ShipClassNamed`](#shipclassnamed) | `ship_class: str`, `atc_id: str` | ATC can name nearby ships. The ATC ID and vehicle entity ID are distinct identifiers. |
| [`KioskShipSelected`](#kioskshipselected) | `vehicle_entity_id: str` | Kiosk selection supplies no ship class, delivery confirmation or hold contents. |

## Trade, inventory and freight

| Event | Captured fields | Omitted fields and interpretation limits |
| --- | --- | --- |
| [`CommodityBuy`](#commoditybuy) | `commodity_guid: str`, `quantity_scu: float`, `total_auec: int`, `price_per_scu: float`, `autoload: bool`, `box_size_scu: float`, `crate_count: int`, `shop_id: str`, `kiosk_id: str`, `shop_name: str` | A request. Quantity is divided by 100 and the price per centi-SCU is multiplied by 100. The total comes from the log and is rounded to whole aUEC. The request flag is `True` exactly when the log says `autoLoading[1]`. Other values are `False`. Shop and kiosk IDs are session-scoped and the shop name is a template. No confirmed delivery or separate autoload fee. |
| [`CommoditySell`](#commoditysell) | `commodity_guid: str`, `quantity_scu: float`, `total_auec: int`, `price_per_scu: float`, `autoload: bool`, `shop_id: str`, `kiosk_id: str`, `shop_name: str` | A request. Quantity is already in SCU. The unit price is calculated from the rounded total and quantity. The request flag is `True` exactly when the log says `autoLoading[1]`. Other values are `False`. Sell-side crate fields are omitted because the logged values have disagreed with observed sales. |
| [`CommodityTransactionFailed`](#commoditytransactionfailed) | `result: str`, `flow_type: str` | The failure code is logged. The line supplies no transaction ID, commodity, quantity or terminal to join it to a request. Observed examples are buy failures. |
| [`ItemPurchaseRequested`](#itempurchaserequested) | `item_class_guid: str`, `item_name: str`, `quantity: int`, `client_price: float`, `shop_name: str`, `at_kiosk: bool` | Shop and kiosk IDs are omitted. The line supplies no destination. The parser preserves the numeric price without interpreting whether it is per item or total. |
| [`ItemPurchaseResponse`](#itempurchaseresponse) | `result: str`, `flow_type: str` | Keeps response tokens such as Success and Buying. There is no order ID in the emitted event. Item-sale requests are still a candidate format. |
| [`InventoryRequestQueued`](#inventoryrequestqueued) | `request_id: int`, `kind: str`, `source: InventoryEnd`, `target: InventoryEnd`, `source_class: str`, `source_amount: int`, `item_class: str`, `action: str` | Captures Store, Move and Interaction. Queries and sorts are filtered. A zero source amount can occur when the count is unknown. |
| [`InventoryMoveListed`](#inventorymovelisted) | `request_id: int`, `kind: str`, `item_classes: tuple[str, ...]` | Keeps listed classes. The listing has no per-class counts and its endpoints are intentionally discarded. |
| [`InventoryRequestCompleted`](#inventoryrequestcompleted) | `request_id: int`, `kind: str`, `succeeded: bool` | Reduces the result token to a boolean. Correlate within the session on ID plus kind. |
| [`LocationContainerReleased`](#locationcontainerreleased) | `location_id: int` | Inventory cache release also occurs outside purchases. Delivery attribution depends on surrounding evidence. |
| [`PersonalContainerAccessed`](#personalcontaineraccessed) | `container_class: str`, `container_id: int` | Access also occurs at login and when inventory opens. The event supplies no purchase ID or changed item. |
| [`FreightSent`](#freightsent) | `entities: int`, `location_id: int` | Entity count only. The event supplies no item names, SCU or final manifest. |
| [`FreightGridOpened`](#freightgridopened) | `location_id: int`, `item_count: int` | First-page entry count, capped at 250. Omits pagination and contents. Opening the grid supplies no evidence that cargo moved. |

`InventoryEnd` is a nested value with `kind: str` and `id: int`. The kind is `"location"`, `"container"`, or `"none"`. The no-endpoint value uses ID zero. Location IDs and container IDs have different meanings.

## Contracts and HUD

| Event | Captured fields | Omitted fields and interpretation limits |
| --- | --- | --- |
| [`ContractObjectiveMarked`](#contractobjectivemarked) | `mission_id: str`, `contract: str`, `contract_definition_id: str`, `objective_id: str`, `objective_kind: str` | Omits the generator name and coordinates. The objective kind is derived from a recognized ID prefix and is empty otherwise. |
| [`HaulObjective`](#haulobjective) | `mission_id: str`, `commodity: str`, `scu: int`, `destination: str` | Keeps the required SCU from a supported objective notice. Carries no delivered quantity or payout. |
| [`ContractEnded`](#contractended) | `mission_id: str`, `completion_type: str`, `reason: str` | Preserves the reported outcome and reason. Carries no payout or reward attribution. |
| [`ContractSharedWithYou`](#contractsharedwithyou) | `mission_id: str` | Omits the sender. A share is an offer signal. |
| [`HudNotice`](#hudnotice) | `title: str`, `text: str`, `mission_id: str \| None` | An all-zero mission ID becomes `None`. Notices with required metadata on continuation lines are unsupported by the current single-line parser. |

## Game.log examples

Each block is one complete input line for `parse_line()`. These examples use redacted test fixtures. They illustrate individual formats and come from different sessions.

### LogStarted

```text
<2026-10-20T09:56:30.165Z> FileVersion: 4.10.197.2878
```

### GameModeSeen

```text
<2026-10-20T09:58:42.511Z> [Notice] <ContextEstablisherTaskFinished> establisher="CReplicationModel" message="CET completed" taskname="ModelWaitForViews" state=eCVS_ResetEntitySystem(1) status="Finished" runningTime=0.127991 timeoutOffset=0.000000 numRuns=7 map="megamap" gamerules="SC_Default" sessionId="x"
```

### GameQuit

```text
<2026-10-20T12:24:40.580Z> [Notice] <SystemQuit> CSystem::Quit invoked with - cause=30016, reason=Quit via console command, exitCode=0, thread id=38784, main thread id=38784 [Team_Unknown][System]
```

### LocationChanged

```text
<2026-10-19T22:05:17.000Z> [Notice] <Update Inventory Location> Player [Someone] is changing location. Landing [0] -> [1510935576]. Location [2537229937] -> [1510935576]. Pending [0] [Team_Inventory][Inventory]
```

### LocationNamed

```text
<2026-10-19T22:05:17.000Z> [Notice] <RequestLocationInventory> Player[Someone] requested inventory for Location[RR_CRU_L1] [Team_Inventory][Inventory]
```

### ShipSeatLeft

```text
<2026-10-18T20:30:00.000Z> [Notice] <Vehicle Control Flow> ClearDriver: Local client node [800000000001] releasing control token for 'AEGS_Reclaimer_800000000012' [800000000012] [Team_Vehicles][Vehicle]
```

### ShipSpawning

```text
<2026-10-20T08:20:28.000Z> [Notice] <CEntityComponentShipListProvider::SetVehicleSpawningInformations> SetVehicleSpawningInformations - VehicleEntityId: [800000000013], LandingArea: Someone's Large Hangar [Team_Vehicles]
```

### ShipClassNamed

```text
<2026-10-20T08:20:31.000Z> [Notice] <ATC_Reset_VehiclesBeingStoredCleared> ATC_Reset_VehiclesBeingStoredCleared ATC 'GAMA_Railen_ShipATCDataManager_800000000014' [Team_Vehicles]
```

### KioskShipSelected

```text
<2026-10-21T07:02:07.448Z> [Notice] <CEntityComponentCommodityUIProvider::LoadSelectedShipBindings> Sending VehicleCargoDataRequest for vehicleEntityId[800000000021] [Team_CoreGameplayFeatures][Shops][UI]
```

### CommodityBuy

```text
<2026-10-19T21:51:11.123Z> [Notice] <CEntityComponentCommodityUIProvider::SendCommodityBuyRequest> Sending SShopCommodityBuyRequest - playerId[800000000001] shopId[800000000003] shopName[SCShop_Admin_lt_base_g] kioskId[800000000004] price[4735584.000000] shopPricePerCentiSCU[73.993500] resourceGUID[7f4599b0-0000-0000-0000-800000000002] autoLoading[1] quantity[64000.000000 cSCU] Cargo Box Data: boxSize[32.000000] | unitAmount[20] [Team_Shops][Shops]
```

### CommoditySell

```text
<2026-10-19T22:10:41.500Z> [Notice] <CEntityComponentCommodityUIProvider::SendCommoditySellRequest> Sending SShopCommoditySellRequest - playerId[800000000001] shopId[800000000005] shopName[SCShop_Admin_lt_base_g] kioskId[800000000006] amount[5443200.000000] resourceGUID[7f4599b0-0000-0000-0000-800000000002] autoLoading[1] quantity[640] transactionMode[ResourceContainer] Cargo Box Data: [boxSize[32] | unitAmount[15]] [Team_Shops][Shops]
```

### CommodityTransactionFailed

```text
<2026-10-23T09:36:15.436Z> [Error] <CEntityComponentCommodityUIProvider::RmToken_CommodityTransactionResponse> Commodity Transaction Response Error - result[AutoLoadStartFailed] type[Buying] [Team_Shops][Shops]
```

### ItemPurchaseRequested

```text
<2026-10-20T08:05:00.000Z> [Notice] <CEntityComponentShopUIProvider::SendShopBuyRequest> Sending buy request - playerId[800000000001] shopId[800000000010] shopName[SCShop_LiveFire_Truckstop02-001] kioskId[800000000011] client_price[396.000000] itemClassGUID[0988e9ce-1111-2222-3333-800000000007] itemName[klwe_rifle_energy_01_mag] quantity[1] [Team_Shops][Shops]
```

### ItemPurchaseResponse

```text
<2026-10-20T08:05:00.500Z> [Notice] <CEntityComponentShopUIProvider::RmShopFlowResponse> shopId[800000000010] kioskId[800000000011] kioskState[BuyRequestProcessing] result[Success] type[Buying] [Team_Shops][Shops]
```

### InventoryRequestQueued

```text
<2026-11-03T10:23:38.989Z> [Notice] <Inventory Mgmt Request Queued> Queued Request[8] Type[Store] for 'Someone' [800000000001] Source Inventory[INVALID] Target Inventory[800000000001:Location:1547955914]. Source[NULL] amount[0] rank[]. Target[NULL] amount[0] rank[]. Item[rsi_deckcrew_armor_light_helmet_01_01_12_800000000020] action[None]. RequestInProgress[0] CurrentProcess[] [Team_CoreGameplayFeatures][Inventory]
```

### InventoryMoveListed

```text
<2026-11-03T10:23:38.985Z> [Notice] <Add Inventory Management Move> New Request[8] Player[Someone] Type[Store] SourceInventory[800000000001:Location:1547955914] TargetInventory[INVALID] ItemClass[rsi_deckcrew_armor_light_helmet_01_01_12] StoredEntity[NULL] LocallyDetached[No] LocalAttached[NULL, ] PendingMoves[1, ] Caller[CSCLocalPlayerPersonalThoughtComponent::HandleComponentEvent] [Team_CoreGameplayFeatures][Inventory]
```

### InventoryRequestCompleted

```text
<2026-11-03T10:23:41.140Z> [Notice] <Player Inventory Request Complete> Request[8] for 'Someone' [800000000001] Type[Store] Result[Succeed] Item[0] CanLockQueue[Yes]. [Team_CoreGameplayFeatures][Inventory]
```

### LocationContainerReleased

```text
<2026-11-03T10:48:04.164Z> [Notice] <Inventory Terminate Location Container> Player [Someone] removing location [800000000001:Location:3392323471] from cache [Team_CoreGameplayFeatures][Inventory]
```

### PersonalContainerAccessed

```text
<2026-11-03T11:03:32.353Z> [Notice] <Inventory Token Flow> Requesting access token for User[Someone, 800000000001] on Inventory[cds_combat_light_backpack_01_01_01_800000000017, 800000000017] [Team_CoreGameplayFeatures][Inventory]
```

### FreightSent

```text
<2026-10-20T08:34:00.000Z> [Notice] <CEntityComponentFreightElevatorUIProvider::FillUnstowRequest> [FreightElevatorKioskUIProvider] FreightElevatorKiosk_FreightElevator_Util_HangarLarge[800000000015] - Processed bindings into transfer request - Entities: 4, Location: 1510935576 - RequestId: 4, ItemBank: 0
```

### FreightGridOpened

```text
<2026-10-20T12:24:09.584Z> [Notice] <InventoryManagement> Freight Inventory Grid InventoryDataRequest Successful for Player[Someone] Inventory[800000000001:Location:1105811199] Inventory Result Item Count:[250]. [Team_CoreGameplayFeatures][Inventory][InventoryContainer]
```

### ContractObjectiveMarked

```text
<2026-10-18T20:07:15.307Z> [Notice] <CLocalMissionPhaseMarker::CreateMarker> Creating objective marker: missionId [9d33a156-1111-2222-3333-800000000007], generator name [VisitingIasi], contract [Iasi_Salvage_Small_2], contractDefinitionId[90ad94c4-1111-2222-3333-800000000007], objectiveId [dropoff_246aa48e-1111-2222-3333-800000000007_0], markerEntityId [2520], zoneHostId [800000000008], position [x: 1.0, y: 2.0, z: 3.0] [Team_MissionFeatures][Missions]
```

### HaulObjective

```text
<2026-10-18T20:07:16.000Z> [Notice] <SHUDEvent_OnNotification> Added notification "New Objective: Deliver 0/90 SCU of Distilled Spirits to Everus Harbor: " [12] to queue. New queue size: 1, MissionId: [9d33a156-1111-2222-3333-800000000007], ObjectiveId: [dropoff_x_0] [Team_UI][HUD]
```

### ContractEnded

```text
<2026-10-18T21:30:00.000Z> [Notice] <EndMission> Ending mission for player. MissionId[9d33a156-1111-2222-3333-800000000007] Player[Someone] PlayerId[800000000001] CompletionType[Complete] Reason[Mission Ended] [Team_MissionFeatures][Missions]
```

### ContractSharedWithYou

```text
<2026-10-18T20:00:00.000Z> [Notice] <MissionShared> Received share push message: ownerId[800000000009] - missionId[9d33a156-1111-2222-3333-800000000007] [Team_MissionFeatures][Missions]
```

### HudNotice

```text
<2026-10-20T09:59:23.546Z> [Notice] <SHUDEvent_OnNotification> Added notification "Entered Monitored Space: " [0] to queue. New queue size: 1, MissionId: [00000000-0000-0000-0000-000000000000], ObjectiveId: [] [Team_CoreGameplayFeatures][Missions][Comms]
```

## Known discrepancies and how to report them

| Status | Evidence | What the parser does |
| --- | --- | --- |
| **Suspected game-side logging discrepancy** | The raw sell request reported a `unitAmount` of 15 in an observed sale of 20 crates. The discrepancy was in the log before parsing. The purpose of that field on sells is still uncertain. | Leaves sell crate count out of the event. Buy crate fields are captured separately. |
| **Suspected game-side logging discrepancy** | For an observed Store request, the raw move-detail line reversed source and target relative to the queued line. VerseKit also reports reversed endpoints. · [VerseKit stock journal](https://github.com/Xharig/VerseKit/blob/8e102e2c86fa886f48154dc78867541b73395fcc/crates/versekit-core/src/stock_journal.rs) | Keeps endpoints from the queued line and classes from the move-detail line. |
| **Unobserved game signal** | Successful commodity trades in the reviewed samples had no positive response. Item shops have a separate response path. | Emits the request as evidence and any recognized failure separately. |
| **Parser limitation** | Some HUD notices carry mission metadata on a continuation line. [HUD event model](../src/sc_gamelog/events.py) | These notices can be skipped because the parser handles one line at a time. |
| **Consumer inference** | A delayed rejection has no unique link to a commodity request. | Publishes the failure evidence. ALICE correlates it separately. |

For a new report, record the game build, channel, language, player action and expected outcome. Include the smallest redacted raw excerpt and the parser version and output. If the raw data agrees with the game action but the emitted event differs, classify it as a parser issue. If the raw data itself conflicts with independent evidence, label it **suspected game-side logging discrepancy** and say what corroborates it. Use **unverified** when the evidence cannot place the fault. Reserve confirmed game-side bug language for cases with authoritative confirmation.
