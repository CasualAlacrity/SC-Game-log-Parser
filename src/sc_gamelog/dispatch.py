"""Listeners for Game.log events: subscribe by event type, then pass `publish` to the watcher.

    events = GameLogEvents()
    events.on(CommodityBuy, reconcile_buy)
    events.on_any(print)
    GameLogWatcher(path, events.publish).start()

Listeners run on the watcher thread, in subscription order. One that raises is reported and
skipped; it does not stop the others or the watcher. A listener that needs the Qt or asyncio
side should hand the event over (a queue, Signal.emit, call_soon_threadsafe), not do the work here.
"""
from collections.abc import Callable

from sc_gamelog.events import GameLogEvent


class GameLogEvents:
    def __init__(self):
        self._by_type: dict[type, list[Callable]] = {}
        self._any: list[Callable] = []

    def on(self, event_type: type, listener: Callable) -> None:
        self._by_type.setdefault(event_type, []).append(listener)

    def on_any(self, listener: Callable[[GameLogEvent], None]) -> None:
        self._any.append(listener)

    def remove_any(self, listener: Callable[[GameLogEvent], None]) -> None:
        """Stops a listener added with on_any (a feature switched off); one that was not added is ignored."""
        if listener in self._any:
            self._any.remove(listener)

    def publish(self, event: GameLogEvent) -> None:
        listeners = list(self._by_type.get(type(event), [])) + self._any
        for listener in listeners:
            try:
                listener(event)
            except Exception as exc:
                name = getattr(listener, "__name__", repr(listener))
                print(f"Game.log listener {name} failed on {type(event).__name__}: "
                      f"{type(exc).__name__}: {exc}", flush=True)
