"""paths.py -- the only module that knows where EE Calculator keeps its data.

Scaffolded by the `new-project` skill to the house layout (Tools/Project_Folder_Structure.md).
Nothing else in the package hard-codes a path; everything calls one of these.

* ``state_dir()``      %LOCALAPPDATA%\\Auterion\\EE_Calculator\\        settings, ledgers, run logs
* ``cache_dir()``      %LOCALAPPDATA%\\Auterion\\EE_Calculator\\Cache\\ downloaded runtimes and models; safe to delete
* ``documents_dir()``  ~\\Documents\\Auterion\\EE_Calculator\\           the user's outputs; changeable in the UI
* ``settings_path()``  state_dir()/settings.json

Every accessor creates its folder on first use, so there is no install step. The
``EE_CALCULATOR_HOME`` environment variable redirects state and cache together (tests,
portable use); the output folder is a setting the user changes in the UI. Nothing here
ever points inside the repository, which is Drive-synced.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import platformdirs

APP = "EE_Calculator"
AUTHOR = "Auterion"
ENV_HOME = "EE_CALCULATOR_HOME"

REPO: Path = Path(__file__).resolve().parents[2]


def _ensure(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def _home() -> Path | None:
    env = os.environ.get(ENV_HOME)
    return Path(env) if env else None


def state_dir() -> Path:
    home = _home()
    return _ensure(home if home else Path(platformdirs.user_data_dir(APP, AUTHOR, roaming=False)))


def cache_dir() -> Path:
    home = _home()
    return _ensure(home / "Cache" if home else Path(platformdirs.user_cache_dir(APP, AUTHOR)))


def settings_path() -> Path:
    return state_dir() / "settings.json"


def load_settings() -> dict:
    p = settings_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(settings: dict) -> None:
    settings_path().write_text(json.dumps(settings, indent=2), encoding="utf-8")


def documents_dir() -> Path:
    """Default ~/Documents/Auterion/<Title>; overridden by the ``output_dir`` setting."""
    custom = load_settings().get("output_dir")
    if custom:
        return _ensure(Path(custom))
    return _ensure(Path(platformdirs.user_documents_dir()) / AUTHOR / APP)


def describe() -> dict[str, str]:
    """Every resolved location, for `pixi run where` and the README."""
    return {
        "repo": str(REPO),
        "state": str(state_dir()),
        "cache": str(cache_dir()),
        "documents": str(documents_dir()),
        "settings": str(settings_path()),
        "home_override": os.environ.get(ENV_HOME, ""),
    }
