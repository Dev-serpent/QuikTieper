## Fiona Developer Notes

This file records the environment, tools, and runtime assumptions currently required for the project to work on the target machine.

### Required Python packages

- `python` 3.11+
- `pynput`
- `wayland-automation`

These are required for:

- the global key listener
- the GUI/editor runtime
- optional Wayland pointer automation backend support

### Required system tools

- `bash`
- `kdotool`
- `ydotool`
- `ydotoold`
- `tk` / `tkinter`

These are used for:

- running binding commands through `bash -lc`
- Plasma Wayland active-window detection via `kdotool`
- Wayland pointer / click injection via `ydotool`
- `ydotool` daemon socket support via `ydotoold`
- the Tk GUI editor

### Example app commands used in config

If these bindings are kept, the corresponding programs must exist on the machine:

- `brave`
- `gedit`
- `code`
- `gnome-terminal`

### Desktop/session assumptions

Current working target:

- KDE Plasma
- Wayland session

Important note:

- app-specific shortcut routing currently depends on `kdotool`
- mouse and click actions currently prefer `ydotool`

### Conda environment

The project is currently expected to run from the `quiktieper` Conda environment.

Do not assume plain `python3` outside that environment will have the required packages.

### Correct startup command

Use this exact command sequence:

```bash
source ~/Applications/miniconda3/etc/profile.d/conda.sh
conda activate quiktieper
python3 -m fiona.cli edit
```

Preferred launcher wrappers:

```bash
./scripts/fiona-edit
./scripts/fiona-run
```

These wrappers:

- activate the `quiktieper` Conda environment
- request privilege up front for `ydotoold` with `pkexec` if needed
- then start Fiona normally as the desktop user

### Listener / runtime notes

- `python3 -m fiona.cli edit` opens the GUI editor
- `python3 -m fiona.cli run` starts the global listener
- app-specific shortcuts require active-window detection to succeed
- on Plasma Wayland, Fiona now prefers `kdotool` over `xprop`

### Debugging files

Primary debug log:

- `~/.config/fiona/debug.log`

Fallback debug log:

- `/tmp/fiona-debug.log`

These logs may contain:

- key press / release traces
- binding match / skip reasons
- active window detection results
- pointer backend success / failure
- shell command launch events

### Permission / privilege notes

- `ydotoold` may need privileged startup depending on the machine setup
- Fiona may attempt daemon startup using:
  - `pkexec ydotoold`
  - `sudo -n ydotoold`
  - `ydotoold`

### Fallback / legacy tools still present in code

- `xprop`
- `xdotool`

These still exist as fallback paths, but they are not the intended primary runtime path on Plasma Wayland.
