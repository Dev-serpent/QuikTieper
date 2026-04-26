from __future__ import annotations

import json
import shlex
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "quiktieper" / "bindings.json"

DEFAULT_CONFIG = {
    "apps": [
        {
            "name": "brave",
            "window_match": "brave-browser",
            "launch": {
                "name": "launch",
                "keys": ["alt", "b", "r", "v"],
                "cmd": "brave-browser",
            },
            "shortcuts": [
                {
                    "name": "focus-url-bar",
                    "keys": ["alt", "s"],
                    "cmd": "xdotool key ctrl+l",
                    "instruction": "",
                    "quiktieper_cmds": [],
                }
            ],
        },
        {
            "name": "vs-code",
            "window_match": "code",
            "launch": {
                "name": "launch",
                "keys": ["alt", "v", "s", "c"],
                "cmd": "code",
            },
            "shortcuts": [],
        },
        {
            "name": "terminal",
            "window_match": "gnome-terminal",
            "launch": {
                "name": "launch",
                "keys": ["alt", "t", "e", "r"],
                "cmd": "gnome-terminal",
            },
            "shortcuts": [],
        },
    ]
}


def ensure_config(path: Path = DEFAULT_CONFIG_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
    return path


def infer_window_match(command: str) -> str:
    parts = shlex.split(command)
    if not parts:
        return ""
    return Path(parts[0]).name.lower()


def normalize_binding(binding: dict, default_name: str) -> dict:
    quiktieper_cmds = binding.get("quiktieper_cmds", [])
    if isinstance(quiktieper_cmds, str):
        quiktieper_cmds = [item.strip() for item in quiktieper_cmds.split(",") if item.strip()]
    return {
        "name": binding.get("name", default_name),
        "keys": [key.lower() for key in binding.get("keys", [])],
        "cmd": binding.get("cmd") or binding.get("command", ""),
        "instruction": binding.get("instruction", "").strip(),
        "quiktieper_cmds": quiktieper_cmds,
        "cooldown_seconds": float(binding.get("cooldown_seconds", 0.8)),
    }


def normalize_config(config: dict) -> dict:
    if "apps" not in config and "bindings" in config:
        apps: list[dict] = []
        for binding in config.get("bindings", []):
            normalized_launch = normalize_binding(binding, "launch")
            apps.append(
                {
                    "name": binding.get("name", "app"),
                    "window_match": infer_window_match(normalized_launch["cmd"]),
                    "launch": normalized_launch,
                    "shortcuts": [],
                }
            )
        config = {"apps": apps}

    apps: list[dict] = []
    for app in config.get("apps", []):
        name = app.get("name", "app")
        launch = normalize_binding(app.get("launch", {}), "launch")
        shortcuts = [
            normalize_binding(shortcut, shortcut.get("name", "shortcut"))
            for shortcut in app.get("shortcuts", [])
        ]
        window_match = app.get("window_match", "").strip().lower() or infer_window_match(launch["cmd"])
        apps.append(
            {
                "name": name,
                "window_match": window_match,
                "launch": launch,
                "shortcuts": shortcuts,
            }
        )

    return {"apps": apps}


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    config_path = ensure_config(path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return normalize_config(config)


def save_config(config: dict, path: Path = DEFAULT_CONFIG_PATH) -> Path:
    config_path = ensure_config(path)
    normalized = normalize_config(config)
    config_path.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
    return config_path
