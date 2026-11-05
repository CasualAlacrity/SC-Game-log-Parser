"""Inventory and item-shop lines, shaped like the 2026-11-03 test log (docs/event-reference.md,
Session 8). The handle and player ID are synthetic; place IDs, classes, prices and gaps between lines are the real
ones. The builders keep a case readable; the literal lines pin the exact shapes."""

PLAYER = "800000000001"
HOME = 1547955914  # a station inventory
SHOP = 3392323471  # another one (ARC-L5 in the real log)
BACKPACK = 800000000017
TEAM = "[Team_CoreGameplayFeatures][Inventory]"
SHOPS = "[Team_CoreGameplayFeatures][Shops][UI]"


def at(clock: str) -> str:
    return f"<2026-11-03T{clock}Z>"


def place(place_id: int) -> str:
    return f"{PLAYER}:Location:{place_id}"


def container(container_id: int = BACKPACK) -> str:
    return f"{container_id}:Container:0"


def queued(clock, request, kind, source, target, *, source_class="NULL", amount=0, item="NONE", action="None"):
    return (
        f"{at(clock)} [Notice] <Inventory Mgmt Request Queued> Queued Request[{request}] Type[{kind}] "
        f"for 'Someone' [{PLAYER}] Source Inventory[{source}] Target Inventory[{target}]. "
        f"Source[{source_class}] amount[{amount}] rank[]. Target[NULL] amount[0] rank[]. "
        f"Item[{item}] action[{action}]. RequestInProgress[0] CurrentProcess[] {TEAM}"
    )


def listed(clock, request, kind, source, target, item_classes):
    return (
        f"{at(clock)} [Notice] <Add Inventory Management Move> New Request[{request}] Player[Someone] "
        f"Type[{kind}] SourceInventory[{source}] TargetInventory[{target}] ItemClass[{item_classes}] "
        f"StoredEntity[NULL] LocallyDetached[No] LocalAttached[NULL, ] PendingMoves[1, ] "
        f"Caller[CSCLocalPlayerPersonalThoughtComponent::HandleComponentEvent] {TEAM}"
    )


def completed(clock, request, kind, result="Succeed"):
    return (
        f"{at(clock)} [Notice] <Player Inventory Request Complete> Request[{request}] for 'Someone' [{PLAYER}] "
        f"Type[{kind}] Result[{result}] Item[0] CanLockQueue[Yes]. {TEAM}"
    )


def buy(clock, item, quantity=1, price=7.0, shop="SCShop_lt_a_casaba_small_base_a", entry="SendShopBuyRequest"):
    provider = "CEntityComponentShopUIProvider" if entry == "SendShopBuyRequest" else "CEntityComponentShoppingProvider"
    return (
        f"{at(clock)} [Notice] <{provider}::{entry}> Sending SShopBuyRequest - playerId[{PLAYER}] "
        f"shopId[800000000018] shopName[{shop}] kioskId[800000000019] client_price[{price:.6f}] "
        f"itemClassGUID[72b91153-5a3e-4d71-af5c-f6c57ea2891a] itemName[{item}] quantity[{quantity}]  {SHOPS}"
    )


def shop_answer(clock, result="Success"):
    return (
        f"{at(clock)} [Notice] <CEntityComponentShopUIProvider::RmShopFlowResponse> Received ShopFlowResponse - "
        f"playerId[{PLAYER}] shopId[800000000018] shopName[SCShop_lt_a_casaba_small_base_a] "
        f"kioskId[800000000019] kioskState[BuyRequestProcessing] result[{result}] type[Buying] {SHOPS}"
    )


def station_released(clock, place_id=SHOP):
    return (
        f"{at(clock)} [Notice] <Inventory Terminate Location Container> Player [Someone] removing location "
        f"[{place(place_id)}] from cache {TEAM}"
    )


def personal_accessed(clock, container_class="cds_combat_light_backpack_01_01_01", container_id=BACKPACK):
    return (
        f"{at(clock)} [Notice] <Inventory Token Flow> Requesting access token for User[Someone, {PLAYER}] "
        f"on Inventory[{container_class}_{container_id}, {container_id}] {TEAM}"
    )


# A Store into a station, three lines of one request (10:23:38 in the real log).
STORE_LISTED = listed(
    "10:23:38.985", 8, "Store", place(HOME), "INVALID", "rsi_deckcrew_armor_light_helmet_01_01_12")
STORE_QUEUED = queued(
    "10:23:38.989", 8, "Store", "INVALID", place(HOME),
    item="rsi_deckcrew_armor_light_helmet_01_01_12_800000000020")
STORE_DONE = completed("10:23:41.140", 8, "Store")

# A single item moved out of a station (Source names the class, amount 1), and the same move back (no class, no count).
MOVE_OUT_LISTED = listed(
    "10:28:49.281", 22, "Move", place(HOME), container(), "rsi_deckcrew_armor_light_helmet_01_01_12")
MOVE_OUT_QUEUED = queued(
    "10:28:49.284", 22, "Move", place(HOME), container(),
    source_class="rsi_deckcrew_armor_light_helmet_01_01_12", amount=1)
MOVE_BACK_LISTED = listed(
    "10:30:49.219", 23, "Move", container(), place(HOME), "[rsi_deckcrew_armor_light_helmet_01_01_12] ")
MOVE_BACK_QUEUED = queued("10:30:49.223", 23, "Move", container(), place(HOME))

# Two classes moved at once: the Queued line has no class and no count (11:00:45 in the real log).
BULK_LISTED = listed(
    "11:00:45.029", 53, "Move", place(SHOP), container(), "[nrs_shoes_03_01_20] [Drink_bottle_cruz_01_lux_a] ")
BULK_QUEUED = queued("11:00:45.030", 53, "Move", place(SHOP), container())

# Taking an item out of a station to wear or carry it.
TAKE_LISTED = listed(
    "10:27:53.902", 18, "Interaction", place(HOME), "INVALID", "vgl_armor_light_core_01_01_10")
TAKE_QUEUED = queued(
    "10:27:53.905", 18, "Interaction", place(HOME), "INVALID",
    source_class="vgl_armor_light_core_01_01_10", amount=1)

# Noise the log writes next to the above and that moves nothing.
QUERY_QUEUED = queued("10:19:52.490", 1, "QueryInventory", container(), "INVALID")
SORT_LISTED = listed("10:59:23.480", 51, "Sort", place(SHOP), "INVALID", "none")
