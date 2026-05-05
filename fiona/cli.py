from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from CamComs import (
    DEFAULT_AUDIT_LOG_PATH,
    DEFAULT_CAMCOMS_DIR,
    DEFAULT_FIONA_CONFIG_PATH,
    DEFAULT_TRUSTED_DIR,
    AuditLog,
    CamComsIdentity,
    CamComsHttpClient,
    HostService,
    PublicKeyBundle,
    default_host_service_config,
    decode_envelope,
    decrypt_text,
    encode_envelope,
    encrypt_message,
    instruction_from_text,
    instruction_to_text,
    list_trusted_senders,
    remove_trusted_sender,
    press_instruction,
    private_key_path,
    public_key_path,
    run_host_receiver,
    save_host_service_config,
    save_trusted_sender,
    trusted_public_key_path,
)
from QuikTieper.remote import RemoteActionRunner


QUIKTIEPER_COMMANDS = {"init", "list", "edit", "run"}


def main() -> None:
    argv = sys.argv[1:]
    if _should_delegate_to_quiktieper(argv):
        _run_quiktieper(argv)
        return
    if argv and argv[0] in {"quiktieper", "qt"}:
        _run_quiktieper(argv[1:])
        return

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.layer in {"camcoms", "cc"}:
        _run_camcoms(args)
        return

    if args.layer == "host":
        _run_camcoms_service(args)
        return

    parser.print_help()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fiona",
        description="Fiona umbrella CLI for QuikTieper access and CamComs communication.",
    )
    subparsers = parser.add_subparsers(dest="layer")

    quiktieper = subparsers.add_parser(
        "quiktieper",
        aliases=["qt"],
        help="Run QuikTieper launcher/listener/editor commands.",
    )
    quiktieper.add_argument("quiktieper_args", nargs=argparse.REMAINDER)

    host = subparsers.add_parser("host", help="Manage the unified Fiona host service.")
    _add_service_subcommands(host)

    camcoms = subparsers.add_parser(
        "camcoms",
        aliases=["cc"],
        help="Run CamComs encryption and encoded IP message commands.",
    )
    camcoms_subparsers = camcoms.add_subparsers(dest="camcoms_command", required=True)

    keygen = camcoms_subparsers.add_parser("keygen", help="Create a CamComs device identity.")
    keygen.add_argument("--device-id", default="host")
    keygen.add_argument("--private-out", type=Path, default=None)
    keygen.add_argument("--public-out", type=Path, default=None)
    keygen.add_argument("--passphrase", default=None)

    public = camcoms_subparsers.add_parser("public", help="Export public keys from a private identity file.")
    public.add_argument("--private", type=Path, default=None)
    public.add_argument("--public-out", type=Path, default=None)
    public.add_argument("--passphrase", default=None)

    camcoms_subparsers.add_parser("paths", help="Show visible default CamComs key storage paths.")

    trust = camcoms_subparsers.add_parser("trust", help="List, add, or remove trusted sender public keys.")
    trust_action = trust.add_mutually_exclusive_group(required=True)
    trust_action.add_argument("--public", type=Path, help="Public key JSON to trust.")
    trust_action.add_argument("--list", action="store_true", help="List trusted sender public keys.")
    trust_action.add_argument("--remove", help="Remove a trusted sender by device id.")
    trust.add_argument("--trusted-dir", type=Path, default=DEFAULT_TRUSTED_DIR)

    encrypt = camcoms_subparsers.add_parser("encrypt", help="Encrypt a message for another device.")
    encrypt.add_argument("--sender-private", type=Path, default=None)
    encrypt.add_argument("--recipient-public", type=Path, default=None)
    encrypt.add_argument("--sender-passphrase", default=None)
    encrypt_input = encrypt.add_mutually_exclusive_group(required=True)
    encrypt_input.add_argument("--instruction-json")
    encrypt_input.add_argument("--press", nargs="+")
    encrypt.add_argument("--type", default="instruction", dest="message_type")
    encrypt.add_argument("--json", action="store_true", help="Print the envelope JSON instead of encoded text.")

    decrypt = camcoms_subparsers.add_parser("decrypt", help="Decrypt an encoded message or envelope JSON.")
    decrypt.add_argument("--recipient-private", type=Path, required=True)
    decrypt.add_argument("--recipient-passphrase", default=None)
    decrypt.add_argument("--sender-public", type=Path, default=None)
    decrypt_input = decrypt.add_mutually_exclusive_group(required=True)
    decrypt_input.add_argument("--encoded")
    decrypt_input.add_argument("--envelope", type=Path)

    send = camcoms_subparsers.add_parser("send", help="POST an encoded CamComs message to an IP endpoint.")
    send.add_argument("--host", required=True)
    send.add_argument("--port", type=int, default=8080)
    send.add_argument("--path", default="/")
    send.add_argument("--timeout", type=float, default=5.0)
    send_input = send.add_mutually_exclusive_group(required=True)
    send_input.add_argument("--encoded")
    send_input.add_argument("--envelope", type=Path)

    receive = camcoms_subparsers.add_parser("receive", help="Run the host receiver for ESP32 messages.")
    receive.add_argument("--host", default="0.0.0.0")
    receive.add_argument("--port", type=int, default=8080)
    receive.add_argument("--private", type=Path, default=None)
    receive.add_argument("--passphrase", default=None)
    receive.add_argument("--trusted-dir", type=Path, default=DEFAULT_TRUSTED_DIR)
    receive.add_argument("--execute", action="store_true", help="Execute approved QuikTieper actions instead of dry-run.")

    service = camcoms_subparsers.add_parser("service", help="Manage the CamComs host service.")
    _add_service_subcommands(service)

    audit = camcoms_subparsers.add_parser("audit", help="Show recent CamComs host audit log events.")
    audit.add_argument("--path", type=Path, default=DEFAULT_AUDIT_LOG_PATH)
    audit.add_argument("--limit", type=int, default=50)

    camcoms_subparsers.add_parser("smoke-test", help="Run a local encrypt/decrypt check.")
    return parser


def _add_service_subcommands(parser: argparse.ArgumentParser) -> None:
    service_subparsers = parser.add_subparsers(dest="service_command", required=True)
    service_init = service_subparsers.add_parser("init", help="Write the default Fiona host service config.")
    service_init.add_argument("--config", type=Path, default=DEFAULT_FIONA_CONFIG_PATH)
    service_init.add_argument("--force", action="store_true")
    service_status = service_subparsers.add_parser("status", help="Show host service config and health checks.")
    service_status.add_argument("--config", type=Path, default=DEFAULT_FIONA_CONFIG_PATH)
    service_status.add_argument("--check-port", action="store_true")
    service_run = service_subparsers.add_parser("run", help="Run the Fiona host service.")
    service_run.add_argument("--config", type=Path, default=DEFAULT_FIONA_CONFIG_PATH)
    service_run.add_argument("--passphrase", default=None)


def _should_delegate_to_quiktieper(argv: list[str]) -> bool:
    if not argv:
        return True
    if argv[0] in QUIKTIEPER_COMMANDS:
        return True
    return argv[0].startswith("--")


def _run_quiktieper(args: list[str]) -> None:
    from QuikTieper.cli import main as quiktieper_main

    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0], *args]
        quiktieper_main()
    finally:
        sys.argv = original_argv


def _run_camcoms(args: argparse.Namespace) -> None:
    command = args.camcoms_command
    if command == "keygen":
        identity = CamComsIdentity.generate(args.device_id)
        private_out = args.private_out or private_key_path(identity.device_id)
        public_out = args.public_out or public_key_path(identity.device_id)
        _write_or_print(identity.to_private_dict(args.passphrase), private_out, label="private")
        _write_or_print(identity.public_bundle.to_dict(), public_out, label="public")
        return

    if command == "public":
        private_path = args.private or private_key_path("host")
        identity = CamComsIdentity.from_private_dict(_read_json(private_path), passphrase=args.passphrase)
        public_out = args.public_out or public_key_path(identity.device_id)
        _write_or_print(identity.public_bundle.to_dict(), public_out, label="public")
        return

    if command == "paths":
        print(
            _pretty_json(
                {
                    "camcoms_dir": str(DEFAULT_CAMCOMS_DIR),
                    "host_private": str(private_key_path("host")),
                    "host_public": str(public_key_path("host")),
                    "esp32_private": str(private_key_path("esp32")),
                    "esp32_public": str(public_key_path("esp32")),
                    "trusted_dir": str(DEFAULT_TRUSTED_DIR),
                    "esp32_trusted_public": str(trusted_public_key_path("esp32")),
                }
            )
        )
        return

    if command == "trust":
        if args.list:
            trusted = [bundle.to_dict() for bundle in list_trusted_senders(args.trusted_dir)]
            print(_pretty_json({"trusted_dir": str(args.trusted_dir), "senders": trusted}))
            return
        if args.remove:
            removed = remove_trusted_sender(args.remove, args.trusted_dir)
            print(f"{'Removed' if removed else 'No trusted sender found for'} {args.remove}")
            return
        bundle = PublicKeyBundle.from_dict(_read_json(args.public))
        path = save_trusted_sender(bundle, args.trusted_dir)
        print(f"Trusted sender {bundle.device_id} at {path}")
        return

    if command == "encrypt":
        sender_private = args.sender_private or private_key_path("esp32")
        recipient_public = args.recipient_public or public_key_path("host")
        sender = CamComsIdentity.from_private_dict(_read_json(sender_private), passphrase=args.sender_passphrase)
        recipient = PublicKeyBundle.from_dict(_read_json(recipient_public))
        instruction_text = _instruction_text_from_args(args)
        envelope = encrypt_message(
            instruction_text,
            sender=sender,
            recipient=recipient,
            message_type=args.message_type,
        )
        print(_pretty_json(envelope) if args.json else encode_envelope(envelope))
        return

    if command == "decrypt":
        recipient = CamComsIdentity.from_private_dict(
            _read_json(args.recipient_private),
            passphrase=args.recipient_passphrase,
        )
        expected_sender = PublicKeyBundle.from_dict(_read_json(args.sender_public)) if args.sender_public else None
        envelope = decode_envelope(args.encoded) if args.encoded else _read_json(args.envelope)
        print(decrypt_text(envelope, recipient=recipient, expected_sender=expected_sender))
        return

    if command == "send":
        encoded_message = args.encoded or encode_envelope(_read_json(args.envelope))
        client = CamComsHttpClient(
            host=args.host,
            port=args.port,
            path=args.path,
            timeout_seconds=args.timeout,
        )
        print(client.send_encoded(encoded_message))
        return

    if command == "receive":
        private_path = args.private or private_key_path("host")
        host_identity = CamComsIdentity.from_private_dict(_read_json(private_path), passphrase=args.passphrase)
        print(f"Listening for CamComs messages on {args.host}:{args.port}")
        print(f"Trusted sender keys: {args.trusted_dir}")
        run_host_receiver(
            host=args.host,
            port=args.port,
            host_identity=host_identity,
            trusted_dir=args.trusted_dir,
            action_runner=RemoteActionRunner(dry_run=not args.execute),
        )
        return

    if command == "service":
        _run_camcoms_service(args)
        return

    if command == "audit":
        print(_pretty_json({"path": str(args.path), "events": AuditLog(args.path).read_recent(args.limit)}))
        return

    if command == "smoke-test":
        esp32_sender = CamComsIdentity.generate("esp32")
        host_receiver = CamComsIdentity.generate("host")
        instruction_text = instruction_to_text(press_instruction(["alt", "s"]))
        envelope = encrypt_message(
            instruction_text,
            sender=esp32_sender,
            recipient=host_receiver.public_bundle,
        )
        print(decrypt_text(envelope, recipient=host_receiver, expected_sender=esp32_sender.public_bundle))
        return

    raise SystemExit(f"unknown CamComs command: {command}")


def _run_camcoms_service(args: argparse.Namespace) -> None:
    service_command = args.service_command
    if service_command == "init":
        if args.config.exists() and not args.force:
            raise SystemExit(f"{args.config} already exists; pass --force to overwrite it")
        path = save_host_service_config(default_host_service_config(), args.config)
        print(f"Wrote host service config to {path}")
        return

    if service_command == "status":
        service = HostService.load(args.config)
        print(_pretty_json(service.status(check_port=args.check_port)))
        return

    if service_command == "run":
        service = HostService.load(args.config, host_passphrase=args.passphrase)
        print(f"Starting CamComs host service from {args.config}")
        service.run()
        return

    raise SystemExit(f"unknown CamComs service command: {service_command}")


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return data


def _instruction_text_from_args(args: argparse.Namespace) -> str:
    if args.press:
        return instruction_to_text(press_instruction(args.press))
    return instruction_to_text(instruction_from_text(args.instruction_json))


def _write_or_print(data: dict[str, Any], path: Path | None, *, label: str) -> None:
    if path is None:
        print(_pretty_json(data))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_pretty_json(data) + "\n", encoding="utf-8")
    print(f"Wrote {label} keys to {path}")


def _pretty_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
