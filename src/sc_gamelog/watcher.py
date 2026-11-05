"""Follow Game.log and hand each flagged event to a callback.

LogTailer is the file-following part (testable with a temp file); GameLogWatcher runs it on a
daemon thread. The file is opened and closed on every poll rather than held open: the game
rewrites Game.log on each launch (moving the old one to logbackups\\), and an open handle on
Windows could get in the way of that rename.
"""
import os
import threading
from collections.abc import Callable
from pathlib import Path

from sc_gamelog.dispatch import GameLogEvents
from sc_gamelog.events import GameLogEvent, GameModeSeen
from sc_gamelog.parser import parse_line

POLL_SECONDS = 0.5


class LogTailer:
    """poll() returns the complete lines appended since the last call.

    The first time the file is seen at startup, reading begins at its end, so a watcher started
    mid-session doesn't treat history as news. That history is still available once, through
    read_history(), for state that only the past can tell (where the pilot landed). A file that
    later appears or is replaced (a game relaunch) is new content and is read from the start.
    """

    def __init__(self, path: Path):
        self.path = path
        self._position: int | None = None  # None until a file has been found
        self._file_id: tuple[int, int] | None = None
        self._partial = b""
        self._first_poll = True
        self._history_end: int | None = None  # where the log ended when the watcher started

    def poll(self) -> list[str]:
        first_poll = self._first_poll
        self._first_poll = False
        try:
            stat = self.path.stat()
        except OSError:
            self._position = None  # gone (mid-relaunch): whatever appears next is a new file
            return []

        file_id = (stat.st_dev, stat.st_ino)
        if self._position is None:
            if first_poll:
                self._history_end = stat.st_size
                self._start_at(file_id, stat.st_size)
            else:
                self._start_at(file_id, 0)
        elif file_id != self._file_id or stat.st_size < self._position:
            self._start_at(file_id, 0)  # replaced or truncated: a fresh log

        if stat.st_size <= self._position:
            return []
        try:
            with open(self.path, "rb") as handle:
                handle.seek(self._position)
                chunk = handle.read()
        except OSError:
            return []
        self._position += len(chunk)
        return self._split(chunk)

    def read_history(self) -> list[str]:
        """The complete lines that were already in the file when the watcher started, once;
        empty afterwards, or if there was no file at startup."""
        end = self._history_end
        self._history_end = None
        if not end:
            return []
        try:
            with open(self.path, "rb") as handle:
                data = handle.read(end)
        except OSError:
            return []
        lines = []
        for piece in data.split(b"\n")[:-1]:  # the last piece may be a line still being written
            lines.append(piece.decode("utf-8", errors="replace").rstrip("\r"))
        return lines

    def _start_at(self, file_id: tuple[int, int], position: int) -> None:
        self._file_id = file_id
        self._position = position
        self._partial = b""

    def _split(self, chunk: bytes) -> list[str]:
        data = self._partial + chunk
        pieces = data.split(b"\n")
        self._partial = pieces.pop()  # whatever follows the last newline is a line still being written
        lines = []
        for piece in pieces:
            lines.append(piece.decode("utf-8", errors="replace").rstrip("\r"))
        return lines


class GameLogWatcher:
    """on_event gets what happens from now on. on_history, if given, gets the events that were
    already in the log at startup, once, before any new ones: for rebuilding state such as the
    pilot's current place, never for acting on (a trade in the history was not made just now)."""

    def __init__(
            self, path: Path, on_event: Callable[[GameLogEvent], None], poll_seconds: float = POLL_SECONDS,
            on_history: Callable[[GameLogEvent], None] | None = None,
    ):
        self._tailer = LogTailer(path)
        self._on_event = on_event
        self._on_history = on_history
        self._poll_seconds = poll_seconds
        self._stop = threading.Event()
        self._game_mode: str | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="game-log-watcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def poll_once(self) -> None:
        lines = self._tailer.poll()
        if self._on_history is not None:
            for line in self._tailer.read_history():
                event = parse_line(line)
                if event is not None:
                    self._on_history(event)
        for line in lines:
            event = parse_line(line)
            if event is None:
                continue
            if isinstance(event, GameModeSeen):
                if event.gamerules == self._game_mode:
                    continue  # the log repeats gamerules on dozens of lines; only a change is news
                self._game_mode = event.gamerules
            self._on_event(event)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.poll_once()
            except Exception as exc:  # a bad callback or line must not kill the watcher
                print(f"Game.log watcher error: {type(exc).__name__}: {exc}", flush=True)
            self._stop.wait(self._poll_seconds)


def watch_main(path: str) -> None:
    """`python -m sc_gamelog.watcher <Game.log>`: print events as they arrive, for checking by eye."""
    events = GameLogEvents()
    events.on_any(lambda event: print(event, flush=True))
    watcher = GameLogWatcher(Path(path), events.publish)
    watcher.start()
    print(f"Watching {path} (Ctrl+C to stop)", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        watcher.stop()


if __name__ == "__main__":
    import sys

    watch_main(sys.argv[1] if len(sys.argv) > 1 else os.environ["GAME_LOG"])
