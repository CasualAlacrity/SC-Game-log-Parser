"""The contract, item-shop, ship and freight events. Sample lines in gamelog_samples.py."""
from gamelog_samples import (
    ATC_NAMED,
    CLEAR_DRIVER,
    DEFINITION,
    END,
    FAILED_BUY_AUTOLOAD,
    FAILED_BUY_CARGO,
    FREIGHT,
    HAUL,
    ITEM_RESPONSE,
    KIOSK_ITEM_BUY,
    MARKER,
    MISSION,
    SHARE,
    SPAWNING,
    WALL_ITEM_BUY,
)

from sc_gamelog.events import (
    CommodityTransactionFailed,
    ContractEnded,
    ContractObjectiveMarked,
    ContractSharedWithYou,
    FreightSent,
    HaulObjective,
    ItemPurchaseRequested,
    ItemPurchaseResponse,
    ShipClassNamed,
    ShipSeatLeft,
    ShipSpawning,
)
from sc_gamelog.parser import parse_line


def test_contract_marker():
    event = parse_line(MARKER)
    assert isinstance(event, ContractObjectiveMarked)
    assert (event.mission_id, event.contract) == (MISSION, "Iasi_Salvage_Small_2")
    assert event.contract_definition_id == DEFINITION
    assert (event.objective_kind, event.objective_id.endswith("_0")) == ("dropoff", True)


def test_haul_objective():
    event = parse_line(HAUL)
    assert event == HaulObjective(
        timestamp=event.timestamp, mission_id=MISSION, commodity="Distilled Spirits", scu=90,
        destination="Everus Harbor")


def test_progress_notices_are_not_new_haul_objectives():
    assert not isinstance(parse_line(HAUL.replace("Deliver 0/90", "Deliver 45/90")), HaulObjective)


def test_contract_ended():
    event = parse_line(END)
    assert event == ContractEnded(
        timestamp=event.timestamp, mission_id=MISSION, completion_type="Complete", reason="Mission Ended")


def test_share_push_carries_only_the_mission():
    event = parse_line(SHARE)
    assert event == ContractSharedWithYou(timestamp=event.timestamp, mission_id=MISSION)


def test_item_buys_kiosk_and_wall():
    kiosk = parse_line(KIOSK_ITEM_BUY)
    wall = parse_line(WALL_ITEM_BUY)
    assert isinstance(kiosk, ItemPurchaseRequested) and isinstance(wall, ItemPurchaseRequested)
    assert (kiosk.item_name, kiosk.client_price, kiosk.quantity, kiosk.at_kiosk) == (
        "klwe_rifle_energy_01_mag", 396.0, 1, True)
    assert (wall.item_name, wall.client_price, wall.at_kiosk) == ("klwe_rifle_energy_01", 4699.0, False)
    assert kiosk.shop_name == "SCShop_LiveFire_Truckstop02-001"


def test_a_refused_commodity_trade_is_a_failure_with_its_reason():
    autoload = parse_line(FAILED_BUY_AUTOLOAD)
    cargo = parse_line(FAILED_BUY_CARGO)
    assert autoload == CommodityTransactionFailed(
        timestamp=autoload.timestamp, result="AutoLoadStartFailed", flow_type="Buying")
    assert cargo.result == "CargoCreationFailed" and cargo.flow_type == "Buying"


def test_a_transaction_response_that_is_not_an_error_is_not_a_failure():
    success = FAILED_BUY_CARGO.replace("Response Error - result[CargoCreationFailed]", "Response - result[Success]")
    assert parse_line(success) is None
    assert parse_line(FAILED_BUY_CARGO.replace(" result[CargoCreationFailed]", "")) is None


def test_item_response():
    event = parse_line(ITEM_RESPONSE)
    assert event == ItemPurchaseResponse(timestamp=event.timestamp, result="Success", flow_type="Buying")


def test_ship_seat_left_splits_class_from_entity_id():
    event = parse_line(CLEAR_DRIVER)
    assert event == ShipSeatLeft(timestamp=event.timestamp, ship_class="AEGS_Reclaimer", entity_id="800000000012")


def test_ship_spawning_drops_the_hangar_owner():
    event = parse_line(SPAWNING)
    assert event == ShipSpawning(timestamp=event.timestamp, entity_id="800000000013")


def test_ship_class_named_by_atc():
    event = parse_line(ATC_NAMED)
    assert event == ShipClassNamed(timestamp=event.timestamp, ship_class="GAMA_Railen", atc_id="800000000014")


def test_freight_sent():
    event = parse_line(FREIGHT)
    assert event == FreightSent(timestamp=event.timestamp, entities=4, location_id=1510935576)


def test_lookalikes_with_missing_fields_are_none():
    assert parse_line(MARKER.replace("objectiveId [", "other [")) is None
    assert parse_line(END.replace("Reason[Mission Ended]", "")) is None
    assert parse_line(KIOSK_ITEM_BUY.replace("itemName[klwe_rifle_energy_01_mag] ", "")) is None
    assert parse_line(CLEAR_DRIVER.replace("releasing control token", "something else")) is None


def test_hud_notice_with_a_contract():
    from gamelog_samples import NOTICE_ACCEPTED

    from sc_gamelog.events import HudNotice
    event = parse_line(NOTICE_ACCEPTED)
    assert event == HudNotice(
        timestamp=event.timestamp, title="Contract Accepted", text="RSI Disc. Month: UCM Order (S)",
        mission_id="e07f1e76-3897-4082-a7b6-f5b81372cead")


def test_hud_notice_without_a_contract_has_no_mission_id():
    from gamelog_samples import NOTICE_ZONE

    from sc_gamelog.events import HudNotice
    event = parse_line(NOTICE_ZONE)
    assert event == HudNotice(timestamp=event.timestamp, title="Entered Monitored Space", text="", mission_id=None)


def test_a_notice_wrapped_onto_a_second_line_is_not_caught():
    from gamelog_samples import NOTICE_WRAPPED_FIRST_LINE
    assert parse_line(NOTICE_WRAPPED_FIRST_LINE) is None
    assert parse_line('<2026-10-20T10:13:39.653Z> : " [13] to queue. New queue size: 1') is None


def test_new_haul_objective_is_not_also_a_plain_notice():
    assert isinstance(parse_line(HAUL), HaulObjective)


def test_log_header_gives_the_build():
    from gamelog_samples import HEADER

    from sc_gamelog.events import LogStarted
    assert parse_line(HEADER) == LogStarted(timestamp=parse_line(HEADER).timestamp, build="4.10.197.2878")


def test_game_mode_from_context_lines():
    from gamelog_samples import CONTEXT_PU

    from sc_gamelog.events import GameModeSeen
    assert parse_line(CONTEXT_PU).gamerules == "SC_Default"
    assert isinstance(parse_line(CONTEXT_PU), GameModeSeen)


def test_real_atc_line_parses_but_means_nothing_alone():
    from gamelog_samples import ATC_REAL
    event = parse_line(ATC_REAL)
    assert (event.ship_class, event.atc_id) == ("AEGS_Sabre", "800000000016")


def test_freight_grid_opened():
    from gamelog_samples import FREIGHT_GRID

    from sc_gamelog.events import FreightGridOpened
    event = parse_line(FREIGHT_GRID)
    assert event == FreightGridOpened(timestamp=event.timestamp, location_id=1105811199, item_count=250)


def test_game_quit():
    from gamelog_samples import QUIT

    from sc_gamelog.events import GameQuit
    event = parse_line(QUIT)
    assert event == GameQuit(timestamp=event.timestamp, reason="Quit via console command", exit_code=0)


def test_kiosk_ship_selection():
    from sc_gamelog.events import KioskShipSelected
    line = ("<2026-10-21T07:02:07.448Z> [Notice] <CEntityComponentCommodityUIProvider::LoadSelectedShipBindings> "
            "Sending VehicleCargoDataRequest for vehicleEntityId[800000000021] [Team_CoreGameplayFeatures][Shops][UI]")
    assert parse_line(line) == KioskShipSelected(timestamp=parse_line(line).timestamp, vehicle_entity_id="800000000021")
    companion = ("<2026-10-21T07:02:07.448Z> [Notice] <CEntityComponentCommodityUIProvider::LoadSelectedShipBindings> "
                 "CEntityComponentCommodityUIProvider::LoadSelectedShipBindings SoftLock_Terminal_Standard_LowTech_"
                 "CommodityKiosk_kiosk_newbab_1_a-003 [800000000022]: Getting location manager")
    assert parse_line(companion) is None
