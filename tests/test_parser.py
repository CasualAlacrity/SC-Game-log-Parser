"""Parser tests; sample lines live in gamelog_samples.py."""
from datetime import UTC, datetime

import pytest
from gamelog_samples import BUY, GUID, MOVE, NAMED, SELL

from sc_gamelog.events import CommodityBuy, CommoditySell, LocationChanged, LocationNamed
from sc_gamelog.parser import parse_line


def test_buy_parses_units_and_destination():
    event = parse_line(BUY)
    assert isinstance(event, CommodityBuy)
    assert event.timestamp == datetime(2026, 10, 19, 21, 51, 11, 123000, tzinfo=UTC)
    assert (event.commodity_guid, event.quantity_scu, event.total_auec) == (GUID, 640.0, 4735584)
    assert event.price_per_scu == pytest.approx(7399.35)
    assert (event.autoload, event.box_size_scu, event.crate_count) == (True, 32.0, 20)
    assert (event.shop_id, event.kiosk_id) == ("800000000003", "800000000004")


def test_buy_without_autoload_is_the_station_inventory():
    assert parse_line(BUY.replace("autoLoading[1]", "autoLoading[0]")).autoload is False


def test_small_buy_keeps_the_logged_rounded_total():
    # 1 SCU of Waste: 2.285 x 100 = 228.5, but the log says 229 and that is what we keep.
    line = BUY.replace("price[4735584.000000]", "price[229.000000]").replace("73.993500", "2.285000")
    line = line.replace("quantity[64000.000000 cSCU]", "quantity[100.000000 cSCU]")
    line = line.replace("boxSize[32.000000] | unitAmount[20]", "boxSize[1.000000] | unitAmount[1]")
    event = parse_line(line)
    assert (event.quantity_scu, event.total_auec, event.crate_count) == (1.0, 229, 1)


def test_sell_quantity_is_whole_scu_and_ignores_unit_amount():
    event = parse_line(SELL)
    assert isinstance(event, CommoditySell)
    assert (event.quantity_scu, event.total_auec, event.price_per_scu) == (640.0, 5443200, 8505.0)
    assert event.autoload is True and not hasattr(event, "crate_count")


def test_location_change():
    event = parse_line(MOVE)
    assert event == LocationChanged(
        timestamp=datetime(2026, 10, 19, 22, 5, 17, tzinfo=UTC), landing_id=1510935576, location_id=1510935576)


def test_in_transit_move_has_zero_landing():
    line = MOVE.replace("Landing [0] -> [1510935576]", "Landing [0] -> [0]")
    line = line.replace("-> [1510935576]. Pending", "-> [2493660041]. Pending")
    event = parse_line(line)
    assert (event.landing_id, event.location_id) == (0, 2493660041)


def test_location_name():
    assert parse_line(NAMED) == LocationNamed(
        timestamp=datetime(2026, 10, 19, 22, 5, 17, tzinfo=UTC), code="RR_CRU_L1")


def test_noise_and_other_events_are_none():
    assert parse_line("") is None
    assert parse_line("not a log line") is None
    assert parse_line("<2026-10-19T21:51:11.123Z> [Notice] <StatObjLoad> Loading something [Team_X]") is None
    # item shop buys use different events and are out of scope
    item_buy = "<2026-10-19T21:51:11.123Z> [Notice] <CEntityComponentShopUIProvider::SendShopBuyRequest> x[1]"
    assert parse_line(item_buy) is None


def test_documented_event_missing_a_field_is_none_not_an_error():
    assert parse_line(BUY.replace("autoLoading[1] ", "")) is None
    assert parse_line(SELL.replace("quantity[640]", "quantity[0]")) is None  # would divide by zero
    assert parse_line(MOVE.replace("Landing [0] -> [1510935576]. ", "")) is None


def test_trailing_newline_is_fine():
    assert isinstance(parse_line(BUY + "\r\n"), CommodityBuy)
