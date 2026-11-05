"""Game.log line -> event. Pure: no file access, no state.

A line that is not one of the documented shapes, or is missing a field we need, gives None
rather than an error: most of the log is engine noise and the format can drift between builds.
"""
import re
from datetime import datetime

from sc_gamelog.events import (
    CommodityBuy,
    CommoditySell,
    CommodityTransactionFailed,
    ContractEnded,
    ContractObjectiveMarked,
    ContractSharedWithYou,
    FreightGridOpened,
    FreightSent,
    GameLogEvent,
    GameModeSeen,
    GameQuit,
    HaulObjective,
    HudNotice,
    InventoryEnd,
    InventoryMoveListed,
    InventoryRequestCompleted,
    InventoryRequestQueued,
    ItemPurchaseRequested,
    ItemPurchaseResponse,
    KioskShipSelected,
    LocationChanged,
    LocationContainerReleased,
    LocationNamed,
    LogStarted,
    PersonalContainerAccessed,
    ShipClassNamed,
    ShipSeatLeft,
    ShipSpawning,
)

# <2026-10-19T21:51:11.123Z> [Notice] <EventName> rest of the line
_LINE = re.compile(r"^<(?P<ts>\d{4}-\d\d-\d\dT[\d:.]+Z)> \[\w+\] <(?P<name>[^>]+)> (?P<rest>.*)$")
_FIELD = re.compile(r"(\w+)\[([^\]]*)\]")
_LOCATION_MOVE = re.compile(r"Landing \[(\d+)\] -> \[(\d+)\]\. Location \[(\d+)\] -> \[(\d+)\]")

_BUY_NAME = "CEntityComponentCommodityUIProvider::SendCommodityBuyRequest"
_SELL_NAME = "CEntityComponentCommodityUIProvider::SendCommoditySellRequest"
_CENTI = 100

# Contract lines use "key [value]" with a space, unlike the shop lines' "key[value]".
_MARKER = re.compile(
    r"missionId \[([0-9a-f-]+)\], generator name \[([^\]]*)\], contract \[([^\]]*)\], "
    r"contractDefinitionId\[([0-9a-f-]+)\], objectiveId \[([^\]]*)\]"
)
# Same pattern as .claude/skills/game-log/scripts/resolve_contracts.py (the HUD notice's queue line).
_HAUL = re.compile(
    r'Deliver 0/(\d+) SCU of ([^"]+?) to ([^"]+?): " \[\d+\] to queue.*?MissionId: \[([0-9a-f-]+)\]'
)
_NOTICE = re.compile(
    r'Added notification "([^:"]+): (.*?)" \[\d+\] to queue.*?MissionId: \[([0-9a-f-]+)\]'
)
_ZERO_ID = "00000000-0000-0000-0000-000000000000"
_HEADER_LINE = re.compile(r"^<(?P<ts>\d{4}-\d\d-\d\dT[\d:.]+Z)> FileVersion: (?P<build>\S+)")
_GAMERULES = re.compile(r'gamerules="([^"]+)"')
_GAMEMODE_EVENTS = ("Channel Created", "Channel Disconnected", "ContextEstablisherTaskFinished")
_SHARE_PUSH = re.compile(r"Received share push message: ownerId\[[^\]]*\] - missionId\[([0-9a-f-]+)\]")
_CLEAR_DRIVER = re.compile(r"ClearDriver: .*releasing control token for '([^']+)' \[(\d+)\]")
_VEHICLE_SPAWNING = re.compile(r"VehicleEntityId: \[(\d+)\]")
_ATC_NAMED = re.compile(r"ATC_Reset_VehiclesBeingStoredCleared.*'(\w+?)_ShipATCDataManager_(\d+)'")
_FREIGHT_GRID = re.compile(
    r"Freight Inventory Grid InventoryDataRequest Successful for Player\[[^\]]*\] "
    r"Inventory\[\d+:Location:(\d+)\] Inventory Result Item Count:\[(\d+)\]"
)
_KIOSK_SHIP = re.compile(r"VehicleCargoDataRequest for vehicleEntityId\[(\d+)\]")
_QUIT = re.compile(r"reason=([^,]+), exitCode=(-?\d+)")
_FREIGHT = re.compile(r"Entities: (\d+), Location: (\d+)")
_TRAILING_ID = re.compile(r"^(.*)_(\d+)$")

# The requests that put an item somewhere; the log also writes QueryInventory and Sort, which move nothing.
_INVENTORY_KINDS = ("Store", "Move", "Interaction")
_QUEUED = re.compile(
    r"Queued Request\[(\d+)\] Type\[(\w+)\] for .*? Source Inventory\[([^\]]*)\] Target Inventory\[([^\]]*)\]\. "
    r"Source\[([^\]]*)\] amount\[(-?\d+)\].*?Item\[([^\]]*)\] action\[(\w+)\]"
)
_MOVE_LISTED = re.compile(r"New Request\[(\d+)\] Player ?\[[^\]]*\] Type\[(\w+)\] .*?ItemClass\[(.*?)\] StoredEntity")
_REQUEST_COMPLETE = re.compile(r"Request\[(\d+)\] for .*? Type\[(\w+)\] Result\[(\w+)\]")
_LOCATION_RELEASED = re.compile(r"removing location \[\d+:Location:(\d+)\] from cache")
_TOKEN_FLOW = re.compile(r"on Inventory\[(.+?)_\d+, (\d+)\]")
_ENTITY_SUFFIX = re.compile(r"_\d{6,}$")
_CLASS_NAME = re.compile(r"\w+")
_NO_CLASS = ("", "NULL", "NONE", "none")


def _fields(text: str) -> dict[str, str]:
    # A key repeating (boxSize inside "Cargo Box Data") keeps its first value, which is the one we want.
    found = {}
    for key, value in _FIELD.findall(text):
        if key not in found:
            found[key] = value
    return found


def _number(text: str) -> float:
    # "64000.000000 cSCU" and "640" and "4735584.000000" are all read by their first token.
    return float(text.split()[0])


def _parse_timestamp(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _parse_buy(timestamp: datetime, rest: str) -> CommodityBuy:
    fields = _fields(rest)
    quantity_scu = _number(fields["quantity"]) / _CENTI
    box_size = _number(fields["boxSize"])
    return CommodityBuy(
        timestamp=timestamp,
        commodity_guid=fields["resourceGUID"],
        quantity_scu=quantity_scu,
        total_auec=round(_number(fields["price"])),
        price_per_scu=_number(fields["shopPricePerCentiSCU"]) * _CENTI,
        autoload=fields["autoLoading"] == "1",
        box_size_scu=box_size,
        crate_count=int(_number(fields["unitAmount"])),
        shop_id=fields["shopId"],
        kiosk_id=fields["kioskId"],
        shop_name=fields.get("shopName", ""),
    )


def _parse_sell(timestamp: datetime, rest: str) -> CommoditySell:
    fields = _fields(rest)
    quantity_scu = _number(fields["quantity"])
    total = round(_number(fields["amount"]))
    return CommoditySell(
        timestamp=timestamp,
        commodity_guid=fields["resourceGUID"],
        quantity_scu=quantity_scu,
        total_auec=total,
        price_per_scu=total / quantity_scu,
        autoload=fields["autoLoading"] == "1",
        shop_id=fields["shopId"],
        kiosk_id=fields["kioskId"],
        shop_name=fields.get("shopName", ""),
    )


def _parse_transaction_failed(timestamp: datetime, rest: str) -> CommodityTransactionFailed | None:
    fields = _fields(rest)
    result = fields.get("result")
    if result is None or result == "Success" or "Error" not in rest:
        return None  # only the failure shape has been seen; anything else is not a failed trade
    return CommodityTransactionFailed(timestamp=timestamp, result=result, flow_type=fields.get("type", ""))


def _parse_location_move(timestamp: datetime, rest: str) -> LocationChanged | None:
    match = _LOCATION_MOVE.search(rest)
    if match is None:
        return None
    return LocationChanged(timestamp=timestamp, landing_id=int(match.group(2)), location_id=int(match.group(4)))


def _parse_location_name(timestamp: datetime, rest: str) -> LocationNamed:
    return LocationNamed(timestamp=timestamp, code=_fields(rest)["Location"])


def _parse_marker(timestamp: datetime, rest: str) -> ContractObjectiveMarked | None:
    match = _MARKER.search(rest)
    if match is None:
        return None
    objective_id = match.group(5)
    kind = objective_id.split("_", 1)[0]
    return ContractObjectiveMarked(
        timestamp=timestamp, mission_id=match.group(1), contract=match.group(3),
        contract_definition_id=match.group(4), objective_id=objective_id,
        objective_kind=kind if kind in ("pickup", "dropoff") else "",
    )


def _parse_haul(timestamp: datetime, rest: str) -> HaulObjective | None:
    match = _HAUL.search(rest)
    if match is None:
        return None
    return HaulObjective(
        timestamp=timestamp, mission_id=match.group(4), commodity=match.group(2),
        scu=int(match.group(1)), destination=match.group(3),
    )


def _parse_notice(timestamp: datetime, rest: str) -> HudNotice | None:
    match = _NOTICE.search(rest)
    if match is None:
        return None
    mission_id = match.group(3)
    return HudNotice(
        timestamp=timestamp, title=match.group(1), text=match.group(2).strip().rstrip(":").strip(),
        mission_id=None if mission_id == _ZERO_ID else mission_id,
    )


def _parse_game_mode(timestamp: datetime, rest: str) -> GameModeSeen | None:
    match = _GAMERULES.search(rest)
    if match is None:
        return None
    return GameModeSeen(timestamp=timestamp, gamerules=match.group(1))


def _parse_end_mission(timestamp: datetime, rest: str) -> ContractEnded:
    fields = _fields(rest)
    return ContractEnded(
        timestamp=timestamp, mission_id=fields["MissionId"],
        completion_type=fields["CompletionType"], reason=fields["Reason"],
    )


def _parse_share_push(timestamp: datetime, rest: str) -> ContractSharedWithYou | None:
    match = _SHARE_PUSH.search(rest)
    if match is None:
        return None
    return ContractSharedWithYou(timestamp=timestamp, mission_id=match.group(1))


def _parse_item_buy(timestamp: datetime, rest: str, at_kiosk: bool) -> ItemPurchaseRequested:
    fields = _fields(rest)
    return ItemPurchaseRequested(
        timestamp=timestamp, item_class_guid=fields["itemClassGUID"], item_name=fields["itemName"],
        quantity=int(_number(fields["quantity"])), client_price=_number(fields["client_price"]),
        shop_name=fields["shopName"] if "shopName" in fields else "", at_kiosk=at_kiosk,
    )


def _parse_item_response(timestamp: datetime, rest: str) -> ItemPurchaseResponse:
    fields = _fields(rest)
    return ItemPurchaseResponse(timestamp=timestamp, result=fields["result"], flow_type=fields.get("type", ""))


def _parse_clear_driver(timestamp: datetime, rest: str) -> ShipSeatLeft | None:
    match = _CLEAR_DRIVER.search(rest)
    if match is None:
        return None
    ship_class = match.group(1)
    split = _TRAILING_ID.match(ship_class)
    if split is not None:
        ship_class = split.group(1)  # 'AEGS_Reclaimer_889041885423' -> AEGS_Reclaimer
    return ShipSeatLeft(timestamp=timestamp, ship_class=ship_class, entity_id=match.group(2))


def _parse_vehicle_spawning(timestamp: datetime, rest: str) -> ShipSpawning | None:
    match = _VEHICLE_SPAWNING.search(rest)
    if match is None:
        return None
    return ShipSpawning(timestamp=timestamp, entity_id=match.group(1))


def _parse_atc_named(timestamp: datetime, text: str) -> ShipClassNamed | None:
    match = _ATC_NAMED.search(text)
    if match is None:
        return None
    return ShipClassNamed(timestamp=timestamp, ship_class=match.group(1), atc_id=match.group(2))


def _parse_freight_grid(timestamp: datetime, rest: str) -> FreightGridOpened | None:
    match = _FREIGHT_GRID.search(rest)
    if match is None:
        return None
    return FreightGridOpened(timestamp=timestamp, location_id=int(match.group(1)), item_count=int(match.group(2)))


def _parse_kiosk_ship(timestamp: datetime, rest: str) -> KioskShipSelected | None:
    match = _KIOSK_SHIP.search(rest)
    if match is None:
        return None  # the companion line naming the kiosk entity
    return KioskShipSelected(timestamp=timestamp, vehicle_entity_id=match.group(1))


def _parse_quit(timestamp: datetime, rest: str) -> GameQuit | None:
    match = _QUIT.search(rest)
    if match is None:
        return None
    return GameQuit(timestamp=timestamp, reason=match.group(1), exit_code=int(match.group(2)))


def _parse_freight(timestamp: datetime, rest: str) -> FreightSent | None:
    match = _FREIGHT.search(rest)
    if match is None:
        return None
    return FreightSent(timestamp=timestamp, entities=int(match.group(1)), location_id=int(match.group(2)))


def _item_class(text: str) -> str:
    """A class from an inventory line, without the entity ID a single item carries:
    'Drink_bottle_cruz_01_lux_a_914959236451' -> Drink_bottle_cruz_01_lux_a. The log's own placeholders give ''."""
    return "" if text in _NO_CLASS else _ENTITY_SUFFIX.sub("", text)


def _inventory_end(text: str) -> InventoryEnd:
    """`INVALID`, `<playerId>:Location:<placeId>` or `<containerId>:Container:0`. Any other shape is not guessed."""
    if text == "INVALID":
        return InventoryEnd("none")
    parts = text.split(":")
    if len(parts) == 3 and parts[1] == "Location" and parts[2].isdigit():
        return InventoryEnd("location", int(parts[2]))
    if len(parts) == 3 and parts[1] == "Container" and parts[0].isdigit():
        return InventoryEnd("container", int(parts[0]))
    raise ValueError(f"unknown inventory shape: {text}")


def _parse_inventory_queued(timestamp: datetime, rest: str) -> InventoryRequestQueued | None:
    match = _QUEUED.search(rest)
    if match is None or match.group(2) not in _INVENTORY_KINDS:
        return None
    return InventoryRequestQueued(
        timestamp=timestamp, request_id=int(match.group(1)), kind=match.group(2),
        source=_inventory_end(match.group(3)), target=_inventory_end(match.group(4)),
        source_class=_item_class(match.group(5)), source_amount=int(match.group(6)),
        item_class=_item_class(match.group(7)), action=match.group(8),
    )


def _parse_move_listed(timestamp: datetime, rest: str) -> InventoryMoveListed | None:
    match = _MOVE_LISTED.search(rest)
    if match is None or match.group(2) not in _INVENTORY_KINDS:
        return None
    classes = []
    for name in _CLASS_NAME.findall(match.group(3)):
        item_class = _item_class(name)
        if item_class:
            classes.append(item_class)
    return InventoryMoveListed(
        timestamp=timestamp, request_id=int(match.group(1)), kind=match.group(2), item_classes=tuple(classes))


def _parse_request_complete(timestamp: datetime, rest: str) -> InventoryRequestCompleted | None:
    match = _REQUEST_COMPLETE.search(rest)
    if match is None or match.group(2) not in _INVENTORY_KINDS:
        return None
    return InventoryRequestCompleted(
        timestamp=timestamp, request_id=int(match.group(1)), kind=match.group(2),
        succeeded=match.group(3).lower() == "succeed")


def _parse_location_released(timestamp: datetime, rest: str) -> LocationContainerReleased | None:
    match = _LOCATION_RELEASED.search(rest)
    if match is None:
        return None
    return LocationContainerReleased(timestamp=timestamp, location_id=int(match.group(1)))


def _parse_token_flow(timestamp: datetime, rest: str) -> PersonalContainerAccessed | None:
    match = _TOKEN_FLOW.search(rest)
    if match is None:
        return None
    return PersonalContainerAccessed(
        timestamp=timestamp, container_class=match.group(1), container_id=int(match.group(2)))


def parse_line(line: str) -> GameLogEvent | None:
    line = line.rstrip("\r\n")
    match = _LINE.match(line)
    if match is None:
        header = _HEADER_LINE.match(line)  # the unbracketed header lines at the top of a fresh log
        if header is None:
            return None
        return LogStarted(timestamp=_parse_timestamp(header.group("ts")), build=header.group("build"))
    name = match.group("name")
    rest = match.group("rest")
    try:
        timestamp = _parse_timestamp(match.group("ts"))
        if name == _BUY_NAME:
            return _parse_buy(timestamp, rest)
        if name == _SELL_NAME:
            return _parse_sell(timestamp, rest)
        if name.endswith("::RmToken_CommodityTransactionResponse"):
            return _parse_transaction_failed(timestamp, rest)
        if name == "Update Inventory Location":
            return _parse_location_move(timestamp, rest)
        if name == "RequestLocationInventory":
            return _parse_location_name(timestamp, rest)
        if name == "CLocalMissionPhaseMarker::CreateMarker":
            return _parse_marker(timestamp, rest)
        if name == "SHUDEvent_OnNotification":
            return _parse_haul(timestamp, rest) or _parse_notice(timestamp, rest)
        if name in _GAMEMODE_EVENTS:
            return _parse_game_mode(timestamp, rest)
        if name == "EndMission":
            return _parse_end_mission(timestamp, rest)
        if name == "MissionShared" or "Received share push message" in rest:
            return _parse_share_push(timestamp, rest)
        if name == "CEntityComponentShopUIProvider::SendShopBuyRequest":
            return _parse_item_buy(timestamp, rest, at_kiosk=True)
        if name == "CEntityComponentShoppingProvider::SendStandardItemBuyRequest":
            return _parse_item_buy(timestamp, rest, at_kiosk=False)
        if name.endswith("::RmShopFlowResponse"):
            return _parse_item_response(timestamp, rest)
        if name == "Inventory Mgmt Request Queued":
            return _parse_inventory_queued(timestamp, rest)
        if name == "Add Inventory Management Move":
            return _parse_move_listed(timestamp, rest)
        if name == "Player Inventory Request Complete":
            return _parse_request_complete(timestamp, rest)
        if name == "Inventory Terminate Location Container":
            return _parse_location_released(timestamp, rest)
        if name == "Inventory Token Flow":
            return _parse_token_flow(timestamp, rest)
        if name == "Vehicle Control Flow":
            return _parse_clear_driver(timestamp, rest)
        if name.endswith("::SetVehicleSpawningInformations"):
            return _parse_vehicle_spawning(timestamp, rest)
        if "ATC_Reset_VehiclesBeingStoredCleared" in name or "ATC_Reset_VehiclesBeingStoredCleared" in rest:
            return _parse_atc_named(timestamp, f"{name} {rest}")
        if name == "InventoryManagement" and "Freight Inventory Grid InventoryDataRequest Successful" in rest:
            return _parse_freight_grid(timestamp, rest)
        if name == "CEntityComponentCommodityUIProvider::LoadSelectedShipBindings":
            return _parse_kiosk_ship(timestamp, rest)
        if name == "SystemQuit":
            return _parse_quit(timestamp, rest)
        if name.endswith("::FillUnstowRequest") or "FillUnstowRequest" in name:
            return _parse_freight(timestamp, rest)
    except (KeyError, ValueError, ZeroDivisionError):
        return None  # a documented event with a missing or garbled field: skip, don't crash the watcher
    return None
