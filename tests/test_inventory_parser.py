"""The inventory lines, as events. Shapes: events.md Session 8; samples in inventory_samples.py."""
from datetime import UTC, datetime

import pytest
from inventory_samples import (
    BULK_LISTED,
    BULK_QUEUED,
    HOME,
    MOVE_BACK_LISTED,
    MOVE_BACK_QUEUED,
    MOVE_OUT_QUEUED,
    QUERY_QUEUED,
    SHOP,
    SORT_LISTED,
    STORE_DONE,
    STORE_LISTED,
    STORE_QUEUED,
    TAKE_QUEUED,
    completed,
    container,
    personal_accessed,
    place,
    queued,
    station_released,
)

from sc_gamelog.events import (
    InventoryEnd,
    InventoryMoveListed,
    InventoryRequestCompleted,
    InventoryRequestQueued,
    LocationContainerReleased,
    PersonalContainerAccessed,
)
from sc_gamelog.parser import parse_line


def test_a_store_names_its_item_without_the_entity_id_and_its_place_as_target():
    event = parse_line(STORE_QUEUED)
    assert event == InventoryRequestQueued(
        timestamp=datetime(2026, 11, 3, 10, 23, 38, 989000, tzinfo=UTC), request_id=8, kind="Store",
        source=InventoryEnd("none"), target=InventoryEnd("location", HOME), source_class="", source_amount=0,
        item_class="rsi_deckcrew_armor_light_helmet_01_01_12", action="None")


def test_a_move_out_names_the_class_and_amount_and_both_ends():
    event = parse_line(MOVE_OUT_QUEUED)
    assert (event.kind, event.source, event.target) == (
        "Move", InventoryEnd("location", HOME), InventoryEnd("container", 800000000017))
    assert (event.source_class, event.source_amount) == ("rsi_deckcrew_armor_light_helmet_01_01_12", 1)


def test_a_move_back_has_no_class_and_no_count_on_the_queued_line():
    event = parse_line(MOVE_BACK_QUEUED)
    assert (event.source_class, event.source_amount, event.target) == ("", 0, InventoryEnd("location", HOME))


def test_an_interaction_from_a_place_is_a_take():
    event = parse_line(TAKE_QUEUED)
    assert (event.kind, event.source, event.target, event.source_amount) == (
        "Interaction", InventoryEnd("location", HOME), InventoryEnd("none"), 1)


def test_the_add_line_lists_one_class_or_several_without_counts():
    single = parse_line(MOVE_BACK_LISTED)
    several = parse_line(BULK_LISTED)
    assert single == InventoryMoveListed(single.timestamp, 23, "Move", ("rsi_deckcrew_armor_light_helmet_01_01_12",))
    assert several.item_classes == ("nrs_shoes_03_01_20", "Drink_bottle_cruz_01_lux_a")
    assert parse_line(STORE_LISTED).item_classes == ("rsi_deckcrew_armor_light_helmet_01_01_12",)


def test_a_bulk_move_has_no_count_on_its_queued_line():
    event = parse_line(BULK_QUEUED)
    assert (event.source_class, event.source_amount, event.source) == ("", 0, InventoryEnd("location", SHOP))


def test_the_result_says_whether_it_succeeded_and_for_which_request_and_type():
    assert parse_line(STORE_DONE) == InventoryRequestCompleted(
        datetime(2026, 11, 3, 10, 23, 41, 140000, tzinfo=UTC), 8, "Store", True)
    assert parse_line(completed("10:25:42.290", 9, "Move", result="Failed")).succeeded is False


def test_a_station_dropped_from_the_cache_names_its_inventory_id():
    event = parse_line(station_released("10:48:04.164"))
    assert event == LocationContainerReleased(datetime(2026, 11, 3, 10, 48, 4, 164000, tzinfo=UTC), SHOP)


def test_a_personal_container_access_names_its_class_and_not_the_user():
    event = parse_line(personal_accessed("11:03:32.353"))
    assert event == PersonalContainerAccessed(
        datetime(2026, 11, 3, 11, 3, 32, 353000, tzinfo=UTC), "cds_combat_light_backpack_01_01_01", 800000000017)
    assert "Someone" not in repr(event) and "800000000001" not in repr(event)


def test_queries_and_sorts_move_nothing_so_they_are_not_events():
    assert parse_line(QUERY_QUEUED) is None
    assert parse_line(SORT_LISTED) is None
    assert parse_line(completed("10:19:52.710", 1, "QueryInventory")) is None
    assert parse_line(completed("10:59:23.947", 51, "Sort")) is None


def test_an_inventory_shape_nobody_documented_is_not_guessed():
    odd = queued("10:30:00.000", 40, "Move", f"{place(HOME)}", "7:Vault:3", source_class="x_y", amount=1)
    assert parse_line(odd) is None
    assert parse_line(queued("10:30:00.000", 41, "Move", container(), place(HOME)).replace("amount[0]", "amount[x]")
                      ) is None


@pytest.mark.parametrize("name", ["Inventory Mgmt Request Queued", "Add Inventory Management Move",
                                  "Player Inventory Request Complete", "Inventory Terminate Location Container",
                                  "Inventory Token Flow"])
def test_a_documented_name_with_a_garbled_body_is_none_not_an_error(name):
    line = f"<2026-11-03T10:30:00.000Z> [Notice] <{name}> something else entirely [Team_X][Inventory]"
    assert parse_line(line) is None
