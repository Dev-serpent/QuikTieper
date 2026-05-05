## Fiona Developer Notes

This file records the current Fiona project structure, runtime setup, and latest verification results.

## Project Structure

Fiona is the umbrella project. It exposes three sibling subsystems:

- `QuikTieper`: the local access layer for keyboard, mouse, app launch, clicks, and shortcuts
- `CamComs`: the communication layer for encoded/encrypted host communication
- `Vsee`: the 3D coordinate hologram viewer

Current file structure:

```text
Fiona/
├── fiona/                  umbrella package and CLI entrypoint
├── QuikTieper/             local access layer implementation
├── CamComs/                communication/encryption layer implementation
│   └── esp32payload/       ESP32 sender payload template
├── Vsee/                   3D point/edge hologram viewer model
├── tests/                  Python tests
├── scripts/                local launch wrappers
├── .backups/               timestamped backup snapshots
├── backup-20260430-185502/ older backup snapshot
├── fiona.egg-info/         editable-install metadata
├── .git/                   Git metadata
├── .agents/                agent metadata
├── .codex                  Codex metadata
├── README.md
├── DEVELOPERNOTE.md
├── pyproject.toml
└── .gitignore
```

Current direction for communication:

- ESP32 is the sender.
- The host running Fiona is the receiver.
- ESP32 sends encoded encrypted envelopes to a host IP endpoint.
- The host decodes and decrypts using its CamComs private identity.

Important directories:

```text
fiona/                 umbrella package and CLI entrypoint
QuikTieper/            access layer implementation
CamComs/               communication/encryption layer implementation
CamComs/esp32payload/  ESP32 sender payload template
Vsee/                  3D coordinate hologram viewer implementation
tests/                 Python verification tests
```

The installable command is:

```bash
fiona
```

The umbrella CLI supports both layers:

```bash
fiona edit
fiona run
fiona list
fiona quiktieper edit
fiona quiktieper run
fiona quiktieper list
fiona camcoms smoke-test
fiona camcoms keygen
fiona camcoms paths
fiona camcoms encrypt
fiona camcoms decrypt
fiona camcoms send
fiona camcoms trust
fiona camcoms trust --list
fiona camcoms trust --remove esp32
fiona camcoms audit
fiona camcoms receive
fiona camcoms service init
fiona camcoms service status
fiona camcoms service run
fiona host init
fiona host status
fiona host run
```

## Missing Issues

These are known project gaps that still need implementation. Manual GUI/workflow roughness is intentionally not listed here.

- The ESP32 payload still needs a real ESP32 crypto adapter implementation for X25519, HKDF-SHA256, AES-GCM, Ed25519, and base64url decode.
- The ESP32 path still needs hardware validation, Wi-Fi provisioning, retries, acknowledgements, reconnection behavior, queueing, and pairing.
- Voice, speech output, desktop tray/background status, and rich desktop notifications are still not implemented.

Recently fixed:

- CamComs host service skeleton exists through `fiona camcoms service init/status/run`.
- Fiona now also exposes the host service directly through `fiona host init/status/run`.
- CamComs host receiver/server exists through `fiona camcoms receive`.
- Decrypted CamComs messages route into an allowlisted QuikTieper remote-action runner.
- Host service config now controls receiver host/port, replay path, audit path, trusted directory, listener startup, dry-run execution, and allowed remote actions.
- Host service status now reports system/session info, QuikTieper app/binding summary, import checks, command checks, key/trust paths, audit path, replay path, and receiver port availability when requested.
- Host service can optionally own the QuikTieper listener and CamComs receiver in one process.
- Trusted sender public keys are stored under `~/.config/fiona/camcoms/trusted`.
- Trusted sender lifecycle now includes list/add/remove helpers and CLI access.
- CamComs audit logging records accepted/rejected host message processing and can be read through `fiona camcoms audit`.
- Replay protection rejects duplicate or stale `message_id` / `created_at` envelopes.
- Remote instruction payloads use strict JSON.
- Remote instruction payloads now support a structured `macro` instruction with nested validated steps.
- Private key files support optional passphrase encryption.
- The GUI now includes a Host tab for config init/status, trusted device inspection/removal, audit log viewing, and host path visibility.
- The GUI now includes a Debug tab that can view/edit project text files, restricted to `tests`, `scripts`, `QuikTieper`, and `CamComs`.
- The project now includes `Vsee`, a separate sibling package for point/edge 3D hologram viewing.
- The GUI now includes a Vsee tab with editable point and edge tables, a dark grid canvas, and rotation/scale controls for rendering connected 3D wireframe shapes.
- Launcher scripts point at `/home/Dhruv/Documents/Projects/Fiona`.
- README matches the current Fiona / QuikTieper / CamComs structure.
- GUI handler coverage exists for the CamComs smoke-test handler without requiring a display.

## Jarvis-Like Missing Layers

Ignoring the AI agent itself, Fiona still needs these system layers to feel like a Jarvis-style host:

1. Always-on host service: implemented as `fiona host run`; login autostart/systemd user setup is still not installed.
2. Real device link: tested ESP32 path with crypto adapter, Wi-Fi provisioning, host discovery or static IP config, retries, acknowledgements, reconnection behavior, and message queueing.
3. Command router: basic allowlisted decrypted-instruction routing exists; sender-specific policy and richer result semantics still need expansion.
4. System awareness: basic service status, session info, available apps/bindings, health checks, and command history exist; active app/window and process registry APIs still need expansion.
5. Voice/input layer: wake-word or push-to-talk input, speech-to-text, text command surface, and confirmation prompts for risky actions.
6. Feedback layer: local result objects and audit records exist; spoken responses, desktop notifications, status overlay/tray, and encrypted replies to ESP32 still need implementation.
7. Security hardening: trusted-device lifecycle, passphrase private keys, replay protection, and audit log exist; key rotation, permission checks, replay cleanup policy, and secure pairing still need implementation.
8. Persistence and config: unified host config exists at `~/.config/fiona/config.json`; module enablement and startup installation still need expansion.
9. GUI control center: Host tab exists for config/status/trusted devices/audit/path visibility; receiver process controls, connected-device live state, and test command buttons still need expansion.
10. Automation/macro layer: basic structured multi-step macro actions exist; waits, condition checks, window targeting, reusable named sequences, and per-step failure policy still need expansion.

## Build Order

Most basic to most advanced:

1. Done: unified Fiona config at `~/.config/fiona/config.json` for QuikTieper path, CamComs key paths, trusted directory, receiver host/port, dry-run mode, allowed actions, replay path, and audit log.
2. Done: host service skeleton through `fiona host init/status/run`.
3. Done: service health checks verify config, key files, trusted dir, `ydotool`, `kdotool`, listener import, audit/replay dirs, and receiver port binding when requested.
4. Done: CamComs receiver integration is owned by `HostService.run`.
5. Done: QuikTieper listener can be owned by the host service through `start_quiktieper_listener`.
6. Done: remote action router connects decrypted CamComs instructions to configured QuikTieper actions with `execute_remote_actions` and `allowed_remote_actions`.
7. Partial: GUI Host tab shows config, health status, trusted keys, logs, and paths; live receiver process controls still need expansion.
8. Done: command history / audit log records accepted/rejected host message processing and is visible through CLI/GUI.
9. Done: trusted device manager can list, add, remove, and inspect stored sender public key JSON.
10. Partial: configurable macro layer supports structured multi-step remote actions; waits, conditions, window targeting, named macros, and per-step failure handling remain.
11. Partial: local structured success/failure result objects exist; response messages to sender and local notifications still remain.
12. Not started: desktop tray / background status.
13. Blocked by ESP32 work: real crypto adapter for X25519, HKDF-SHA256, AES-GCM, Ed25519, and base64url decode in firmware.
14. Not started: ESP32 pairing flow.
15. Not started: voice / speech interface.

## Setup

The project is currently expected to run from the `quiktieper` Conda environment.

```bash
source ~/Applications/miniconda3/etc/profile.d/conda.sh
conda activate quiktieper
cd /home/Dhruv/Documents/Projects/Fiona
```

Install the project in editable mode after dependency changes:

```bash
pip install -e .
```

Required Python packages:

- `python` 3.11+
- `pynput`
- `cryptography`
- `numpy`
- `pandas`
- `wayland-automation` for optional Wayland pointer automation fallback

Required system tools for the launcher:

- `bash`
- `kdotool`
- `ydotool`
- `ydotoold`
- `tk` / `tkinter`
- optional fallback tools: `xprop`, `xdotool`

## Part 1: QuikTieper Launcher

QuikTieper is Fiona's keyboard control layer. It listens for global simultaneous key chords and launches apps or app-specific shortcuts.

Create the default config:

```bash
python3 -m fiona.cli init
```

List configured bindings:

```bash
python3 -m fiona.cli list
```

Start the global listener:

```bash
python3 -m fiona.cli run
```

Open the GUI editor:

```bash
python3 -m fiona.cli edit
```

Equivalent umbrella CLI commands:

```bash
fiona edit
fiona quiktieper edit
```

Preferred launcher wrappers:

```bash
./scripts/fiona-edit
./scripts/fiona-run
```

These wrappers:

- activate the `quiktieper` Conda environment
- request privilege up front for `ydotoold` with `pkexec` if needed
- start Fiona normally as the desktop user

The default config path is:

```text
~/.config/fiona/bindings.json
```

Example app commands used in the default config:

- `brave-browser`
- `code`
- `gnome-terminal`
- `dolphin`

Runtime assumptions:

- Current target desktop is KDE Plasma on Wayland.
- App-specific shortcut routing prefers `kdotool`.
- Mouse movement and click actions prefer `ydotool`.
- `xprop` and `xdotool` are fallback / legacy paths.

## Part 2: CamComs Communication

CamComs is Fiona's communications layer. The current implemented parts are:

- `CamComs/encryption.py`: public/private encryption and signing
- `CamComs/codec.py`: base64url JSON envelope encoding/decoding
- `CamComs/transport.py`: HTTP POST client for encoded messages
- `CamComs/esp32payload/`: ESP32 sender payload template

The current model is ESP32 sender to host receiver.

Run the CamComs tests:

```bash
python3 -m unittest tests.test_camcoms_encryption tests.test_camcoms_transport
```

Minimal ESP32-to-host smoke test:

```bash
fiona camcoms smoke-test
```

Expected output:

```text
{"keys":["alt","s"],"type":"press","version":1}
```

What the CamComs encrypter currently provides:

- `CamComsIdentity.generate()` creates a device identity.
- Each identity has an X25519 encryption keypair.
- Each identity has an Ed25519 signing keypair.
- `identity.public_bundle` is safe to share with another device.
- `encrypt_message(...)` encrypts a payload to the recipient public key.
- `decrypt_message(...)` decrypts using the recipient private key.
- `decrypt_text(...)` is a UTF-8 text helper around `decrypt_message(...)`.
- Sender signatures are verified during decrypt when `expected_sender` is provided.
- Tampered messages and wrong-recipient messages raise `CamComsCryptoError`.
- Remote instruction payloads use strict JSON objects, for example `{"keys":["alt","s"],"type":"press","version":1}`.

The encrypted envelope uses:

- X25519 for public/private key agreement
- HKDF-SHA256 for message key derivation
- AES-GCM for authenticated encryption
- Ed25519 for sender signatures

### ESP32 Payload

ESP32 payload files:

```text
CamComs/esp32payload/README.md
CamComs/esp32payload/esp32payload.ino
```

Host receiver identity:

```bash
fiona camcoms keygen --device-id host
```

ESP32 sender identity for provisioning:

```bash
fiona camcoms keygen --device-id esp32
```

The ESP32 payload needs:

- host device id
- host encryption public key
- ESP32 device id
- ESP32 signing private key

The ESP32 static encryption private key is not needed for the current one-way sender-to-host direction. It becomes relevant once the host also encrypts replies back to the ESP32.

Default visible key paths:

```text
~/.config/fiona/camcoms/host.private.json
~/.config/fiona/camcoms/host.public.json
~/.config/fiona/camcoms/esp32.private.json
~/.config/fiona/camcoms/esp32.public.json
```

## Validation Commands

Run the launcher CLI check:

```bash
fiona list
```

Run all current tests:

```bash
python -m unittest discover -s tests -v
```

Latest result, run on 2026-05-05:

```text
Ran 29 tests in 0.320s

OK
```

Note: `python -m unittest discover -v` from the repository root currently discovers 0 tests in this layout. Use `python -m unittest discover -s tests -v`.

Direct host-service CLI smoke checks, run on 2026-05-05:

```bash
python -m fiona.cli host init --config /tmp/fiona-host-test.json --force
python -m fiona.cli host status --config /tmp/fiona-host-test.json
python -m fiona.cli camcoms audit --path /tmp/fiona-audit-missing.log --limit 5
python -m fiona.cli camcoms trust --list --trusted-dir /tmp/fiona-trusted-missing
```

Latest direct CLI result:

```text
host init wrote /tmp/fiona-host-test.json
host status returned config, checks, system summary, and QuikTieper app/binding summary
camcoms audit returned an empty event list for a missing audit log
camcoms trust --list returned an empty sender list for a missing trusted directory
```

Run the CamComs ESP32-to-host smoke test:

```bash
fiona camcoms smoke-test
```

Latest output:

```text
{"keys":["alt","s"],"type":"press","version":1}
```

Compile the main packages:

```bash
python -m compileall CamComs QuikTieper fiona
```

Latest result, run on 2026-05-05:

```text
Compiled without syntax errors.
```

## Debugging Files

Primary debug log:

```text
~/.config/fiona/debug.log
```

Fallback debug log:

```text
/tmp/fiona-debug.log
```

These logs may contain:

- key press / release traces
- binding match / skip reasons
- active window detection results
- pointer backend success / failure
- shell command launch events

## Permission Notes

`ydotoold` may need privileged startup depending on the machine setup.

Fiona may attempt daemon startup using:

```text
pkexec ydotoold
sudo -n ydotoold
ydotoold
```
