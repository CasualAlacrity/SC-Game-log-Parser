"""Finding Game.log. Windows only in practice; the candidates are just paths, so it runs anywhere."""
import string
from pathlib import Path

_SUFFIXES = (
    Path("StarCitizen") / "LIVE" / "Game.log",
    Path("Roberts Space Industries") / "StarCitizen" / "LIVE" / "Game.log",
)


def candidate_paths(setting: str | None = None, drives: list[str] | None = None) -> list[Path]:
    """In order: the user's setting, Program Files, then every drive root (the sample logs came
    from D:\\ and E:\\ installs, so a C:-only check would miss them)."""
    candidates = []
    if setting:
        candidates.append(Path(setting))
    candidates.append(Path(r"C:\Program Files") / _SUFFIXES[1])
    letters = drives if drives is not None else [f"{letter}:\\" for letter in string.ascii_uppercase]
    for drive in letters:
        for suffix in _SUFFIXES:
            candidates.append(Path(drive) / suffix)
    return candidates


def find_game_log(setting: str | None = None, drives: list[str] | None = None) -> Path | None:
    for path in candidate_paths(setting, drives):
        if path.is_file():
            return path
    return None
