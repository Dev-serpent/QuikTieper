from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Binding:
    name: str
    keys: frozenset[str]
    command: str
    instruction: str = ""
    quiktieper_cmds: tuple[str, ...] = ()
    cooldown_seconds: float = 0.8
    app_name: str | None = None
    window_match: str | None = None
    binding_type: str = "launch"


def get_mouse_location() -> tuple[int, int] | None:
    try:
        result = subprocess.run(
            ["xdotool", "getmouselocation"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    x_match = re.search(r"x:(\d+)", result.stdout)
    y_match = re.search(r"y:(\d+)", result.stdout)
    if x_match is None or y_match is None:
        return None
    return int(x_match.group(1)), int(y_match.group(1))


def run_instruction(instruction: str) -> None:
    raw = instruction.strip()
    if not raw:
        return

    if raw.startswith("mouse:"):
        coords = raw.removeprefix("mouse:").split(",")
        if len(coords) != 2:
            return
        x_text, y_text = coords
        subprocess.run(["xdotool", "mousemove", x_text.strip(), y_text.strip()], check=False)


def run_quiktieper_command(command: str) -> None:
    normalized = command.strip().lower()
    if normalized == "mouse-left-click":
        subprocess.run(["xdotool", "click", "1"], check=False)
    elif normalized == "mouse-right-click":
        subprocess.run(["xdotool", "click", "3"], check=False)


def get_active_window_classes() -> set[str]:
    try:
        active_window = subprocess.run(
            ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return set()

    match = re.search(r"window id # (0x[0-9a-fA-F]+)", active_window.stdout)
    if match is None:
        return set()

    window_id = match.group(1)
    try:
        window_props = subprocess.run(
            ["xprop", "-id", window_id, "WM_CLASS"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return set()

    values = re.findall(r'"([^"]+)"', window_props.stdout)
    return {value.lower() for value in values}


class AppLauncher:
    def __init__(self, bindings: list[Binding]) -> None:
        self.bindings = bindings
        self._last_triggered: dict[str, float] = {}

    def trigger_matches(self, pressed_keys: set[str]) -> list[Binding]:
        matches: list[Binding] = []
        active_classes: set[str] | None = None
        for binding in self.bindings:
            if not binding.keys.issubset(pressed_keys) or not self._ready(binding):
                continue
            if binding.window_match:
                if active_classes is None:
                    active_classes = get_active_window_classes()
                expected = binding.window_match.lower()
                if not any(expected in value for value in active_classes):
                    continue
            matches.append(binding)
        return matches

    def launch(self, binding: Binding) -> None:
        if binding.instruction:
            run_instruction(binding.instruction)
        for internal_command in binding.quiktieper_cmds:
            run_quiktieper_command(internal_command)
        if binding.command.strip():
            subprocess.Popen(["bash", "-lc", binding.command])
        self._last_triggered[binding.name] = time.monotonic()

    def _ready(self, binding: Binding) -> bool:
        last_seen = self._last_triggered.get(binding.name, 0.0)
        return (time.monotonic() - last_seen) >= binding.cooldown_seconds
