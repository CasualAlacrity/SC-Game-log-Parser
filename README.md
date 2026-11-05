# SC Game-log Parser

A Python 3.11+ library for reading typed observations from Star Citizen's Game.log. It runs locally and has no runtime dependencies.

Install from this checkout with `python -m pip install .`.

```python
from pathlib import Path

from sc_gamelog import parse_line

with Path("Game.log").open(encoding="utf-8", errors="replace") as log:
    for line in log:
        event = parse_line(line)
        if event is not None:
            print(event)
```

For live events, run `python -m sc_gamelog.watcher /path/to/Game.log` or pass a callback to
`sc_gamelog.watcher.GameLogWatcher`. The watcher starts at the end of an existing log. Supply
`on_history` separately to rebuild context. Live callbacks run on the watcher thread.

- [Game.log API reference](docs/event-reference.md) covers field types, Game.log examples, live tracking and suspected logging discrepancies.
- [Signal catalog](docs/signal-catalog.md) credits VerseKit and Bedrock and tracks formats awaiting verification.

The parser originates in ALICE. Licensed under the [MIT License](LICENSE). The line formats were recreated from observed Game.log output; the signal catalog credits VerseKit and Bedrock for what they documented, and no code from either is used.
