# Fiona-Quiktiper

Fiona-QuikTieper is a mouse-free app launcher built around simultaneous key chords, focused-app shortcuts, and pointer actions.

The core idea is simple:
- instead of clicking icons, you hold 3-5 keys together at once
- each launch chord maps to one app
- app-specific chords can trigger actions inside the focused app
- a binding can move the pointer, click, and then run a shell command
- the letters inside the chord can represent the app name
- the launcher listens globally and opens what you need immediately

This is not a TUI. It is a background launcher daemon for people who want the keyboard to be the entire navigation layer.

Example:
- press `alt + b + r + v` -> open Brave
- press `alt + v + s + c` -> open VS Code
- press `alt + t + e + r` -> open terminal
- in Brave, press `alt + s` -> focus the URL bar

## MVP

The current project provides:
- a Python CLI daemon
- a JSON config for app launch bindings and app-specific shortcuts
- a GUI editor with an app tree and per-app shortcut entries
- simultaneous key chord detection
- command launching with a small cooldown to avoid accidental repeats
- focused-app shortcut matching using `xprop`
- pointer actions using recorded mouse positions and built-in click commands

Example bindings:
- `alt + b + r + v` -> Brave
- `alt + v + s + c` -> VS Code
- `alt + t + e + r` -> terminal
- when Brave is focused, `alt + s` -> focus URL bar

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

Create the default config:

```bash
fiona init
```

List bindings:

```bash
fiona list
```

Run the listener:

```bash
fiona run
```

Open the GUI editor:

```bash
fiona edit
```

Inside the GUI:
- use `Start Listener` to enable the background hotkey hook
- the footer shows `Listener: running` or `Listener: stopped`
- saving config while the listener is active restarts it with the new bindings

The default config is written to:

```text
~/.config/fiona/bindings.json
```

Example config:

```json
{
  "apps": [
    {
      "name": "brave",
      "window_match": "brave-browser",
      "launch": {
        "name": "launch",
        "keys": ["alt", "b", "r", "v"],
        "cmd": "brave-browser"
      },
      "shortcuts": [
        {
          "name": "focus-url-bar",
          "keys": ["alt", "s"],
          "cmd": "xdotool key ctrl+l",
          "instruction": "",
          "fiona_cmds": []
        }
      ]
    },
    {
      "name": "vs-code",
      "window_match": "code",
      "launch": {
        "name": "launch",
        "keys": ["alt", "v", "s", "c"],
        "cmd": "code"
      },
      "shortcuts": []
    }
  ]
}
```

## Notes

- The listener uses `pynput` for global keyboard capture.
- The GUI uses `tkinter`, so you can edit app records, launch bindings, shortcuts, and the raw JSON from inside the app.
- App launch commands run through `bash -lc`, so bindings can use normal shell command strings.
- Each launch binding or shortcut stores its runnable shell command in `cmd`, alongside editable `name`, `keys`, and `cooldown_seconds` values.
- `instruction` can store a recorded pointer target like `mouse:1200,420`.
- `fiona_cmds` can store built-in actions like `mouse-left-click` or `mouse-right-click`.
- A binding can use any combination of `instruction`, `fiona_cmds`, and `cmd`, but at least one of them must be filled.
- App-specific shortcuts are matched only when the focused window matches the app's `window_match`, using `xprop`.
- The default Brave shortcut uses `xdotool key ctrl+l` to focus the URL bar.
- Global keyboard hooks are OS-dependent. Linux may require X11 support or desktop-specific permissions.
- The background listener is controlled from the GUI and exposes a visible running/stopped indicator.
- The current version is an MVP focused on simultaneous app chords, not window switching, fuzzy search, or macro layers.

## Next logical steps

- Fiona Is going to go into advanced terittory later on the inclusion of voice control so this is the base layer built for it.
- The Fiona Project's name is based on M2 (FNF secret of mimic's fiona)
