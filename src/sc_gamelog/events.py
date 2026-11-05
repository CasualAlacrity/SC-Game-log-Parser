"""The events the Game.log watcher flags, as plain immutable data.

Only shapes documented in docs/event-reference.md exist here. Player
handles and IDs are deliberately not carried: nothing downstream needs them and they are
personal data. shop_id and kiosk_id are session entity IDs (not stable across sessions), so
they identify a terminal only within one run of the game; use the location code for a place.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CommodityBuy:
    timestamp: datetime
    commodity_guid: str  # resolve to a name via the wiki's /commodities
    quantity_scu: float  # the log says cSCU on a buy; already divided by 100 here
    total_auec: int  # the log's own total, as logged (not recomputed from the unit price)
    price_per_scu: float  # shopPricePerCentiSCU x 100
    autoload: bool  # autoLoading[1]: the cargo went to the ship; [0]: the station inventory
    box_size_scu: float
    crate_count: int
    shop_id: str
    kiosk_id: str
    # A shop template name, not a place: Orison's Providence Platform logged
    # SCShop_AdminOffice_NewBabbage-002 (2026-10-21). Kept as evidence only.
    shop_name: str = ""


@dataclass(frozen=True)
class CommoditySell:
    timestamp: datetime
    commodity_guid: str
    quantity_scu: float  # whole SCU on a sell
    total_auec: int
    price_per_scu: float  # total / quantity
    autoload: bool
    shop_id: str
    kiosk_id: str
    shop_name: str = ""
    # No crate count: a sell's `unitAmount` has read 15 for 20 crates, so it is not trusted.


@dataclass(frozen=True)
class CommodityTransactionFailed:
    """`RmToken_CommodityTransactionResponse` with an error: the game refused a kiosk trade whose request
    line it had already logged. Seen only for failures (0 of 9 successful trades logged it; all three failed
    buys did), 0.8 to 19 s after the request, with the reason never given: `result` is e.g. AutoLoadStartFailed
    or CargoCreationFailed. It names no shop, quantity or commodity (a 2026-10-24 line does carry an optional
    playerId before result), so it can only be paired with the latest request before it."""
    timestamp: datetime
    result: str
    flow_type: str  # "Buying" for a buy; a sell's value has not been seen


@dataclass(frozen=True)
class LocationChanged:
    """`Update Inventory Location`. Numeric IDs only, no names. In transit `landing_id` is 0."""
    timestamp: datetime
    landing_id: int
    location_id: int


@dataclass(frozen=True)
class LocationNamed:
    """`RequestLocationInventory`: a place code such as RR_CRU_L1. Also fires when the pilot opens
    the inventory UI while standing somewhere, so it is not a landing signal on its own."""
    timestamp: datetime
    code: str



@dataclass(frozen=True)
class ContractObjectiveMarked:
    """`CreateMarker`: a contract objective appeared for you, so the contract is active for you.
    `mission_id` is a per-player instance ID; `contract_definition_id` is the stable ID the wiki knows."""
    timestamp: datetime
    mission_id: str
    contract: str  # the wiki's debug_name, e.g. Iasi_Salvage_Small_2 (trailing _N is a variant)
    contract_definition_id: str
    objective_id: str  # dropoff_<uuid>_<n> for delivery objectives; a plain GUID for others (salvage, locate)
    objective_kind: str  # "pickup" / "dropoff" from the objective_id prefix, else ""


@dataclass(frozen=True)
class HaulObjective:
    """The 'New Objective: Deliver 0/N SCU of X to Y' HUD notice."""
    timestamp: datetime
    mission_id: str
    commodity: str
    scu: int
    destination: str


@dataclass(frozen=True)
class ContractEnded:
    """`EndMission` for the player. `completion_type` is e.g. "Complete"; `reason` e.g. "Mission Ended"."""
    timestamp: datetime
    mission_id: str
    completion_type: str
    reason: str


@dataclass(frozen=True)
class ContractSharedWithYou:
    """A party member has this contract. Not an acceptance: only ContractObjectiveMarked means active for you."""
    timestamp: datetime
    mission_id: str


@dataclass(frozen=True)
class ItemPurchaseRequested:
    """A non-commodity shop buy (gear, weapons). `client_price` is the raw logged figure, not interpreted:
    how it relates to `quantity` is not settled. The request has no destination field."""
    timestamp: datetime
    item_class_guid: str  # the wiki's item uuid
    item_name: str  # the wiki's class_name
    quantity: int
    client_price: float
    shop_name: str
    at_kiosk: bool  # False for a wall display


@dataclass(frozen=True)
class ItemPurchaseResponse:
    """`RmShopFlowResponse`. Kiosk buys log it but no 'Transaction Complete' notice; wall buys log both."""
    timestamp: datetime
    result: str  # e.g. "Success"
    flow_type: str  # e.g. "Buying"


@dataclass(frozen=True)
class InventoryEnd:
    """One end of an inventory request: `INVALID` (nowhere), a station's `Location` inventory (`id` is the
    place's inventory ID, the one `Update Inventory Location` uses), or one of the pilot's own containers
    (backpack, armor slot; `id` is that container's entity ID, not stable)."""
    kind: str  # "none", "location" or "container"
    id: int = 0


@dataclass(frozen=True)
class InventoryRequestQueued:
    """`Inventory Mgmt Request Queued` for a Store, Move or Interaction (queries and sorts move nothing).
    The request counter is not unique by itself: a result belongs to the same id AND type. `source_class` is
    what the request moves from `source`; it is empty on a move back into a place, and `source_amount` is
    then 0, so a count is unknown. A Store names its item (`item_class`) and moves one entity."""
    timestamp: datetime
    request_id: int
    kind: str  # "Store", "Move" or "Interaction"
    source: InventoryEnd
    target: InventoryEnd
    source_class: str
    source_amount: int
    item_class: str
    action: str  # e.g. "Carry", "Equip", "None"


@dataclass(frozen=True)
class InventoryMoveListed:
    """`Add Inventory Management Move`: the only place a multi-item move names its classes
    (`ItemClass[[a] [b] ]`, each class once, no counts). Its source and target are not carried: on a Store they
    are swapped, so the Queued line is the one to read."""
    timestamp: datetime
    request_id: int
    kind: str
    item_classes: tuple[str, ...]


@dataclass(frozen=True)
class InventoryRequestCompleted:
    """`Player Inventory Request Complete` for a Store, Move or Interaction."""
    timestamp: datetime
    request_id: int
    kind: str
    succeeded: bool


@dataclass(frozen=True)
class LocationContainerReleased:
    """`Inventory Terminate Location Container`: a station's inventory dropped from the cache. Written just after
    an item-shop purchase that was delivered to that station (events.md Session 8), and at other times too."""
    timestamp: datetime
    location_id: int


@dataclass(frozen=True)
class PersonalContainerAccessed:
    """`Inventory Token Flow`: access to one of the pilot's own containers, named by its class
    (`cds_combat_light_backpack_01_01_01`). Written just after an item-shop purchase delivered to the pilot, and
    at login and whenever an inventory opens, so only the timing after a purchase means anything."""
    timestamp: datetime
    container_class: str
    container_id: int


@dataclass(frozen=True)
class ShipSeatLeft:
    """`ClearDriver`: the pilot released the controls of this ship (class and entity ID)."""
    timestamp: datetime
    ship_class: str  # e.g. AEGS_Reclaimer
    entity_id: str


@dataclass(frozen=True)
class ShipSpawning:
    """`SetVehicleSpawningInformations`: a ship is being spawned from a hangar request."""
    timestamp: datetime
    entity_id: str


@dataclass(frozen=True)
class ShipClassNamed:
    """`ATC_Reset_VehiclesBeingStoredCleared`: an ATC manager reset for a ship. It fires for EVERY ship in
    range (380 times in a 5h session, almost all other players' ships), so on its own it says nothing about
    your ship. It only names yours when it follows a ShipSpawning by 2 to 5 s. Its ID is near but not equal
    to the vehicle's entity ID."""
    timestamp: datetime
    ship_class: str  # e.g. GAMA_Railen
    atc_id: str


@dataclass(frozen=True)
class FreightSent:
    """`FillUnstowRequest`: items were sent up the freight elevator. Only a count; no names or quantities."""
    timestamp: datetime
    entities: int
    location_id: int  # the station inventory's location ID


@dataclass(frozen=True)
class HudNotice:
    """A single-line `SHUDEvent_OnNotification`: title is e.g. "Contract Accepted", "Contract Complete",
    "Hangar Request Completed", "Entered Monitored Space", "Leaving Armistice Zone - Caution Advised".
    `text` is what follows the title (a contract name, an objective). `mission_id` is None when the notice
    isn't about a contract (the log writes an all-zero ID). Notices whose text wraps onto a second log line
    ("Objective Complete: Locate Salvage Claim #...") are not caught: the ID is on the continuation line."""
    timestamp: datetime
    title: str
    text: str
    mission_id: str | None


@dataclass(frozen=True)
class LogStarted:
    """The header of a fresh Game.log: the game build. Seen only when the game (re)launches."""
    timestamp: datetime
    build: str  # e.g. 4.10.197.2878


@dataclass(frozen=True)
class GameModeSeen:
    """`gamerules` from a connection/context line: SC_Default is the PU, EA_FreeFlight is Free Flight /
    Arena Commander, SC_Frontend is the menus. The watcher only forwards it when the mode changes."""
    timestamp: datetime
    gamerules: str


@dataclass(frozen=True)
class FreightGridOpened:
    """The freight elevator terminal listed a station's inventory. `item_count` is entries on the first page,
    capped at 250 (the log also says HasNextPage[1] then), so 250 means "at least 250". 0 on an empty
    station, 6 for a few items. Says nothing about commodity names or SCU, and cannot tell whether the
    pilot stored or retrieved anything afterwards (the platform cycle that follows is identical every time)."""
    timestamp: datetime
    location_id: int  # the place's inventory ID, the same one Update Inventory Location uses
    item_count: int


@dataclass(frozen=True)
class KioskShipSelected:
    """`LoadSelectedShipBindings ... VehicleCargoDataRequest`: a commodity kiosk has this ship selected as
    the cargo inventory. Logged when the kiosk opens with a ship nearby or the pilot picks it, so it is the
    ship an autoload trade right after it goes into, but not proof by itself (a station-inventory buy can
    follow it). The class is not on this line; see ShipSeatLeft / ShipClassNamed."""
    timestamp: datetime
    vehicle_entity_id: str


@dataclass(frozen=True)
class GameQuit:
    """`SystemQuit`: the game is closing (logout / quit). The last meaningful line of a log."""
    timestamp: datetime
    reason: str  # e.g. "Quit via console command"
    exit_code: int


GameLogEvent = (
    CommodityBuy | CommoditySell | CommodityTransactionFailed | LocationChanged | LocationNamed
    | ContractObjectiveMarked | HaulObjective | ContractEnded | ContractSharedWithYou
    | ItemPurchaseRequested | ItemPurchaseResponse
    | InventoryRequestQueued | InventoryMoveListed | InventoryRequestCompleted
    | LocationContainerReleased | PersonalContainerAccessed
    | ShipSeatLeft | ShipSpawning | ShipClassNamed | FreightSent
    | HudNotice | LogStarted | GameModeSeen
    | FreightGridOpened | GameQuit | KioskShipSelected
)
