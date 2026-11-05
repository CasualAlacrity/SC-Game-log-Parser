import os

from gamelog_samples import BUY, MOVE

from sc_gamelog.events import CommodityBuy, LocationChanged
from sc_gamelog.locate import candidate_paths, find_game_log
from sc_gamelog.watcher import GameLogWatcher, LogTailer


def _append(path, text):
    with open(path, "ab") as handle:
        handle.write(text.encode())


def test_starts_at_end_so_history_is_ignored(tmp_path):
    log = tmp_path / "Game.log"
    log.write_text("old line\n")
    tailer = LogTailer(log)
    assert tailer.poll() == []
    _append(log, "new line\n")
    assert tailer.poll() == ["new line"]
    assert tailer.poll() == []


def test_partial_line_waits_for_its_newline(tmp_path):
    log = tmp_path / "Game.log"
    log.write_text("")
    tailer = LogTailer(log)
    tailer.poll()
    _append(log, "half a li")
    assert tailer.poll() == []
    _append(log, "ne\r\nnext\n")
    assert tailer.poll() == ["half a line", "next"]


def test_replaced_file_is_read_from_the_start(tmp_path):
    log = tmp_path / "Game.log"
    log.write_text("a long first session line\n" * 5)
    tailer = LogTailer(log)
    tailer.poll()
    os.replace(log, tmp_path / "Game.log.bak")  # the game moves it to logbackups
    log.write_text("fresh\n")
    assert tailer.poll() == ["fresh"]
    _append(log, "more\n")
    assert tailer.poll() == ["more"]


def test_truncated_file_is_read_from_the_start(tmp_path):
    log = tmp_path / "Game.log"
    log.write_text("x" * 100 + "\n")
    tailer = LogTailer(log)
    tailer.poll()
    log.write_text("short\n")
    assert tailer.poll() == ["short"]


def test_file_that_appears_after_start_is_read_whole(tmp_path):
    log = tmp_path / "Game.log"
    tailer = LogTailer(log)
    assert tailer.poll() == []
    log.write_text("first\nsecond\n")
    assert tailer.poll() == ["first", "second"]


def test_file_that_vanishes_and_returns_is_read_whole(tmp_path):
    log = tmp_path / "Game.log"
    log.write_text("old\n")
    tailer = LogTailer(log)
    tailer.poll()
    log.unlink()
    assert tailer.poll() == []
    log.write_text("reborn\n")
    assert tailer.poll() == ["reborn"]


def test_watcher_flags_only_known_events(tmp_path):
    log = tmp_path / "Game.log"
    log.write_text("")
    seen = []
    watcher = GameLogWatcher(log, seen.append)
    watcher.poll_once()
    _append(log, "engine noise\n" + BUY + "\n" + "<2026-10-19T21:51:11.123Z> [Notice] <StatObjLoad> x\n" + MOVE + "\n")
    watcher.poll_once()
    assert [type(event) for event in seen] == [CommodityBuy, LocationChanged]


def test_watcher_survives_a_failing_callback(tmp_path):
    log = tmp_path / "Game.log"
    log.write_text("")
    calls = []

    def flaky(event):
        calls.append(event)
        raise RuntimeError("boom")

    watcher = GameLogWatcher(log, flaky, poll_seconds=0.01)
    watcher.poll_once()
    watcher.start()
    _append(log, BUY + "\n")
    for _ in range(100):
        if calls:
            break
        watcher._stop.wait(0.02)
    watcher.stop()
    assert len(calls) == 1


def test_candidate_paths_check_setting_first_then_every_drive(tmp_path):
    paths = candidate_paths(setting="X:/custom/Game.log", drives=["D:\\", "E:\\"])
    assert str(paths[0]).replace("\\", "/") == "X:/custom/Game.log"
    text = [str(path).replace("\\", "/") for path in paths]
    assert any(path.startswith("E:/") and path.endswith("StarCitizen/LIVE/Game.log") for path in text)
    assert any("Program Files" in path for path in text)


def test_find_game_log_returns_first_existing(tmp_path):
    log = tmp_path / "StarCitizen" / "LIVE" / "Game.log"
    log.parent.mkdir(parents=True)
    log.write_text("")
    assert find_game_log(drives=[str(tmp_path)]) == log
    assert find_game_log(drives=[str(tmp_path / "nowhere")]) is None


def test_game_mode_is_forwarded_only_when_it_changes(tmp_path):
    from gamelog_samples import CONTEXT_PU

    from sc_gamelog.events import GameModeSeen
    log = tmp_path / "Game.log"
    log.write_text("")
    seen = []
    watcher = GameLogWatcher(log, seen.append)
    watcher.poll_once()
    other = CONTEXT_PU.replace("SC_Default", "EA_FreeFlight")
    _append(log, "\n".join([CONTEXT_PU, CONTEXT_PU, other, other, CONTEXT_PU]) + "\n")
    watcher.poll_once()
    assert [event.gamerules for event in seen if isinstance(event, GameModeSeen)] == [
        "SC_Default", "EA_FreeFlight", "SC_Default"]


def test_history_is_available_once_and_only_complete_lines(tmp_path):
    log = tmp_path / "Game.log"
    log.write_text("before one\nbefore two\nhalf a li")
    tailer = LogTailer(log)
    assert tailer.poll() == []
    assert tailer.read_history() == ["before one", "before two"]
    assert tailer.read_history() == []


def test_no_history_when_the_file_appears_later(tmp_path):
    log = tmp_path / "Game.log"
    tailer = LogTailer(log)
    tailer.poll()
    log.write_text("new\n")
    assert tailer.poll() == ["new"]
    assert tailer.read_history() == []


def test_history_goes_to_on_history_and_is_never_acted_on(tmp_path):
    from gamelog_samples import NAMED

    from sc_gamelog.events import LocationNamed
    log = tmp_path / "Game.log"
    log.write_text(MOVE + "\n" + NAMED + "\n" + BUY + "\n")  # a landing, its name, and an old trade
    live, history = [], []
    watcher = GameLogWatcher(log, live.append, on_history=history.append)
    watcher.poll_once()
    assert [type(event) for event in history] == [LocationChanged, LocationNamed, CommodityBuy]
    assert live == []
    _append(log, BUY + "\n")
    watcher.poll_once()
    assert [type(event) for event in live] == [CommodityBuy]
    assert len(history) == 3
