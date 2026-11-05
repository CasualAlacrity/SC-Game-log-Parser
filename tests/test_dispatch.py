from gamelog_samples import BUY, MOVE

from sc_gamelog.dispatch import GameLogEvents
from sc_gamelog.events import CommodityBuy, LocationChanged
from sc_gamelog.parser import parse_line


def test_listeners_get_only_their_event_type_and_any_gets_all():
    events = GameLogEvents()
    buys, everything = [], []
    events.on(CommodityBuy, buys.append)
    events.on_any(everything.append)
    events.publish(parse_line(BUY))
    events.publish(parse_line(MOVE))
    assert [type(event) for event in buys] == [CommodityBuy]
    assert [type(event) for event in everything] == [CommodityBuy, LocationChanged]


def test_a_failing_listener_does_not_stop_the_others(capsys):
    events = GameLogEvents()
    seen = []

    def broken(event):
        raise RuntimeError("nope")

    events.on(CommodityBuy, broken)
    events.on(CommodityBuy, seen.append)
    events.publish(parse_line(BUY))
    assert len(seen) == 1
    assert "broken failed on CommodityBuy" in capsys.readouterr().out


def test_a_listener_can_be_removed_and_removing_one_never_added_is_ignored():
    events = GameLogEvents()
    heard = []
    events.on_any(heard.append)

    events.remove_any(heard.append)
    events.remove_any(print)
    events.publish(parse_line(BUY))

    assert heard == []
