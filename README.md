# Fiona

Fiona is a local host-control project inspired by JARVIS-style workstation control. It is not an AI agent yet. The current project is the software base around that future agent: local actions, encrypted device communication, and a simple 3D hologram viewer.

The installed command is intended to be:

```bash
fiona
```

In the current dev setup, use the module form from the repo instead:

```bash
cd /home/Dhruv/Documents/Projects/Fiona
python3 -m fiona.cli <command>
```

Examples:

```bash
python3 -m fiona.cli edit
python3 -m fiona.cli list
python3 -m fiona.cli camcoms smoke-test
```

## Current Architecture

Fiona is the umbrella package. It exposes three sibling subsystems:

- `QuikTieper`: local access layer for keyboard chords, app launching, shortcuts, pointer movement, clicks, and remote action execution.
- `CamComs`: communication layer for encoded/encrypted messages, currently focused on ESP32 sender to Fiona host receiver.
- `Vsee`: 3D coordinate hologram viewer for point/edge wireframe shapes.

Project layout:

```text
fiona/                 umbrella package and CLI entrypoint
QuikTieper/            local access/action layer
CamComs/               communication/encryption/host service layer
CamComs/esp32payload/  ESP32 sender payload template
Vsee/                  3D point/edge hologram model
scripts/               local launch wrappers
tests/                 Python tests
DEVELOPERNOTE.md       detailed project notes and latest verification log
pyproject.toml         package metadata and Python dependencies
```

## Install

The intended environment is the `quiktieper` Conda environment:

```bash
source ~/Applications/miniconda3/etc/profile.d/conda.sh
conda activate quiktieper
cd /home/Dhruv/Documents/Projects/Fiona
pip install -e .
```

Core Python dependencies are declared in `pyproject.toml`:

- `cryptography`
- `pynput`
- `numpy`
- `pandas`

System/runtime tools used by local control:

- `ydotool` for pointer/keyboard automation
- `kdotool` for KDE/Wayland active-window checks
- `xdotool` / `xprop` as fallback or legacy paths

## GUI

Open the shared GUI:

```bash
cd /home/Dhruv/Documents/Projects/Fiona
python3 -m fiona.cli edit
```

Current panel order:

```text
CamComs -> Vsee -> Bindings -> Raw Json -> Debug -> Host
```

Panel roles:

- `CamComs`: generate identities, export public keys, encrypt/decrypt messages, send encoded envelopes, and run a local smoke test.
- `Vsee`: edit 3D `points` and `edges` tables and render them as a connected wireframe hologram.
- `Bindings`: edit QuikTieper app launchers and shortcut bindings.
- `Raw Json`: edit the QuikTieper config JSON directly.
- `Debug`: restricted project file editor for `tests`, `scripts`, `QuikTieper`, and `CamComs`.
- `Host`: inspect host service config, trusted devices, key paths, and audit logs.

## QuikTieper

QuikTieper is the local access layer. It listens for simultaneous global key chords and runs configured actions.

Default config path:

```text
~/.config/fiona/bindings.json
```

Basic commands:

```bash
python3 -m fiona.cli init
python3 -m fiona.cli list
python3 -m fiona.cli run
python3 -m fiona.cli edit
```

Explicit layer commands:

```bash
python3 -m fiona.cli quiktieper list
python3 -m fiona.cli quiktieper run
python3 -m fiona.cli quiktieper edit
```

Current capabilities:

- app launching from chord bindings
- app-specific shortcuts gated by active-window matching
- shell command execution
- pointer movement and click helpers
- allowlisted remote actions for CamComs instructions
- structured macro instructions with nested steps

Example default bindings:

- `alt + b + r + v` opens Brave
- `alt + v + s + c` opens VS Code
- `alt + t + e + r` opens terminal

## CamComs

CamComs is the communication and encryption layer.

Current communication direction:

```text
ESP32 sender -> encoded encrypted HTTP POST -> Fiona host receiver
```

Implemented pieces:

- X25519 key agreement
- HKDF-SHA256 key derivation
- AES-GCM encrypted payloads
- Ed25519 sender signatures
- base64url JSON envelope encoding/decoding
- trusted sender public-key storage
- replay protection for duplicate/stale messages
- host receiver and host service skeleton
- audit log for accepted/rejected message processing
- strict JSON instruction validation

Default CamComs storage paths:

```text
~/.config/fiona/camcoms/host.private.json
~/.config/fiona/camcoms/host.public.json
~/.config/fiona/camcoms/esp32.private.json
~/.config/fiona/camcoms/esp32.public.json
~/.config/fiona/camcoms/trusted/
~/.config/fiona/camcoms/audit.log
```

Useful commands:

```bash
python3 -m fiona.cli camcoms smoke-test
python3 -m fiona.cli camcoms paths
python3 -m fiona.cli camcoms keygen --device-id host
python3 -m fiona.cli camcoms keygen --device-id esp32
python3 -m fiona.cli camcoms trust --public ~/.config/fiona/camcoms/esp32.public.json
python3 -m fiona.cli camcoms trust --list
python3 -m fiona.cli camcoms audit
```

Encrypt a press instruction for the host:

```bash
python3 -m fiona.cli camcoms encrypt \
  --sender-private ~/.config/fiona/camcoms/esp32.private.json \
  --recipient-public ~/.config/fiona/camcoms/host.public.json \
  --press alt s
```

Run the receiver directly:

```bash
python3 -m fiona.cli camcoms receive --private ~/.config/fiona/camcoms/host.private.json --port 8080
```

Host service commands:

```bash
python3 -m fiona.cli host init
python3 -m fiona.cli host status
python3 -m fiona.cli host run
```

The older nested service commands also exist:

```bash
python3 -m fiona.cli camcoms service init
python3 -m fiona.cli camcoms service status
python3 -m fiona.cli camcoms service run
```

## Vsee

Vsee is the current holography software layer. It is intentionally simple right now: a point/edge model rendered as a 3D wireframe in the GUI.

Vsee input format:

```csv
id,x,y,z
A,-1,-1,-1
B,1,-1,-1
```

Edge format:

```csv
source,target
A,B
```

Current capabilities:

- load/edit point and edge tables in the GUI
- validate duplicate point IDs and missing edge references
- project 3D coordinates into a 2D canvas using `numpy`
- parse editable table data using `pandas`
- render connected wireframe shapes with rotation and scale controls

## Debug Mode

The GUI Debug tab is a restricted project editor. It can view and edit text/code files only under:

```text
tests/
scripts/
QuikTieper/
CamComs/
```

It intentionally does not expose the whole filesystem or every project directory. It also skips generated cache directories such as `__pycache__`.

## Wrapper Scripts

Local scripts are available:

```bash
./scripts/fiona-edit
./scripts/fiona-run
```

They are intended to activate the project environment, enter the repo, and launch Fiona.

## Current State

Working today:

- installable Fiona umbrella CLI
- shared Tkinter GUI
- QuikTieper binding editor/listener/action runner
- CamComs encryption/decryption/transport/receiver
- trusted sender lifecycle and audit logging
- host service config/status/run commands
- Vsee point/edge hologram viewer
- project-restricted GUI debug editor
- Python tests for the core model/crypto/transport/service/GUI handler paths

Still incomplete:

- no AI agent layer yet
- ESP32 firmware crypto adapter is still a template, not hardware-verified
- no ESP32 pairing flow yet
- no desktop tray/background autostart install yet
- no voice/speech layer yet
- no rich notification or spoken feedback layer yet
- Vsee is currently a wireframe coordinate viewer, not true optical holography

## Validation

Run all current tests:

```bash
python -m unittest discover -s tests -v
```

Compile the main packages:

```bash
python -m compileall CamComs QuikTieper Vsee fiona
```

Current latest known result:

```text
29 tests OK
compileall OK
```
