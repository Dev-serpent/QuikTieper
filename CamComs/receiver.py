from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from CamComs.audit import AuditLog
from CamComs.codec import decode_envelope
from CamComs.encryption import CamComsCryptoError, CamComsIdentity, decrypt_text
from CamComs.instructions import instruction_from_text
from CamComs.replay import ReplayGuard
from CamComs.trust import DEFAULT_TRUSTED_DIR, find_trusted_sender
from QuikTieper.remote import RemoteActionRunner


class CamComsReceiverError(ValueError):
    """Raised when the host receiver cannot accept a message."""


class HostMessageProcessor:
    def __init__(
        self,
        *,
        host_identity: CamComsIdentity,
        trusted_dir: Path = DEFAULT_TRUSTED_DIR,
        replay_guard: ReplayGuard | None = None,
        action_runner: RemoteActionRunner | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self.host_identity = host_identity
        self.trusted_dir = trusted_dir
        self.replay_guard = replay_guard or ReplayGuard()
        self.action_runner = action_runner or RemoteActionRunner(dry_run=True)
        self.audit_log = audit_log

    def process_encoded(self, encoded_message: str) -> dict[str, Any]:
        envelope: dict[str, Any] = {}
        try:
            envelope = decode_envelope(encoded_message.strip())
            trusted_sender = find_trusted_sender(str(envelope.get("sender", "")), self.trusted_dir)
            if trusted_sender is None:
                raise CamComsReceiverError("sender is not trusted")
            self.replay_guard.check_and_record(envelope)
            plaintext = decrypt_text(envelope, recipient=self.host_identity, expected_sender=trusted_sender)
            instruction = instruction_from_text(plaintext)
            result = self.action_runner.run(instruction)
            response = {
                "ok": True,
                "sender": envelope["sender"],
                "message_id": envelope["message_id"],
                "action": result.action,
                "detail": result.detail,
                "executed": result.executed,
            }
            self._record({**response, "instruction": instruction})
            return response
        except (CamComsCryptoError, CamComsReceiverError, ValueError) as exc:
            self._record(
                {
                    "ok": False,
                    "sender": envelope.get("sender"),
                    "message_id": envelope.get("message_id"),
                    "error": str(exc),
                }
            )
            raise

    def _record(self, event: dict[str, Any]) -> None:
        if self.audit_log is not None:
            self.audit_log.record(event)


def run_host_receiver(
    *,
    host: str,
    port: int,
    host_identity: CamComsIdentity,
    trusted_dir: Path = DEFAULT_TRUSTED_DIR,
    replay_guard: ReplayGuard | None = None,
    action_runner: RemoteActionRunner | None = None,
    audit_log: AuditLog | None = None,
) -> None:
    processor = HostMessageProcessor(
        host_identity=host_identity,
        trusted_dir=trusted_dir,
        replay_guard=replay_guard,
        action_runner=action_runner,
        audit_log=audit_log,
    )

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length).decode("ascii")
            try:
                response = processor.process_encoded(payload)
                self.send_response(200)
            except (CamComsCryptoError, CamComsReceiverError, ValueError) as exc:
                response = {"ok": False, "error": str(exc)}
                self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, sort_keys=True).encode("utf-8"))

        def log_message(self, _format: str, *_args: object) -> None:
            return

    ThreadingHTTPServer((host, port), Handler).serve_forever()
