from __future__ import annotations

import argparse
import os
from pathlib import Path

from fiona.bindings import parse_bindings
from fiona.config import DEFAULT_CONFIG_PATH, ensure_config, load_config
from fiona.launcher import ensure_ydotoold_running


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fiona",
        description="Launch apps and focused-app shortcuts using simultaneous key chords.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the bindings JSON file.",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("init", help="Create the default config if it does not exist.")
    subparsers.add_parser("list", help="List configured app chords.")
    subparsers.add_parser("edit", help="Open the GUI config editor.")
    subparsers.add_parser("run", help="Start the global listener.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    command = args.command or "run"
    if command == "init":
        config_path = ensure_config(args.config)
        print(f"Config ready at {config_path}")
        return

    config = load_config(args.config)
    bindings = parse_bindings(config.get("apps", []))

    # On Wayland, bootstrap ydotoold up front so auth happens at app start
    # instead of during the first click action.
    if os.environ.get("WAYLAND_DISPLAY"):
        ensure_ydotoold_running()

    if command == "list":
        for app in config.get("apps", []):
            launch = app["launch"]
            launch_keys = " + ".join(sorted(key.lower() for key in launch.get("keys", [])))
            print(f"{app['name']} launch: {launch_keys} -> {launch.get('cmd', '')}")
            for shortcut in app.get("shortcuts", []):
                shortcut_keys = " + ".join(sorted(key.lower() for key in shortcut.get("keys", [])))
                print(f"{app['name']} shortcut {shortcut['name']}: {shortcut_keys} -> {shortcut.get('cmd', '')}")
        return

    if command == "edit":
        from fiona.gui import launch_editor

        launch_editor(args.config)
        return

    from fiona.listener import ChordListener

    print(f"Listening for {len(bindings)} launch and shortcut chords from {args.config}")
    ChordListener(bindings).run()


if __name__ == "__main__":
    main()
