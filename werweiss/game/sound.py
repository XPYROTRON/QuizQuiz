from pathlib import Path
import subprocess

PACKAGE_SOUND_DIR = Path(__file__).resolve().parents[1] / "assets" / "sounds"
SOURCE_SOUND_DIR = Path(__file__).resolve().parents[2] / "assets" / "sounds"
_muted = False


def _sound_path(name: str) -> Path | None:
    sound = PACKAGE_SOUND_DIR / f"{name}.wav"
    if sound.exists():
        return sound
    sound = SOURCE_SOUND_DIR / f"{name}.wav"
    if sound.exists():
        return sound
    return None


def set_muted(value: bool):
    global _muted
    _muted = bool(value)


def is_muted() -> bool:
    return _muted


def play(name: str):
    if _muted:
        return
    sound = _sound_path(name)
    if not sound:
        return
    for cmd in (["paplay", str(sound)], ["aplay", str(sound)]):
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception:
            continue
