from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from CamComs import (
    AuditLog,
    CamComsCryptoError,
    CamComsIdentity,
    HostMessageProcessor,
    ReplayGuard,
    encode_envelope,
    encrypt_message,
    instruction_to_text,
    press_instruction,
    save_trusted_sender,
)
from QuikTieper.remote import RemoteActionRunner


class CamComsReceiverTests(unittest.TestCase):
    def test_processes_trusted_sender_message_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            esp32 = CamComsIdentity.generate("esp32")
            host = CamComsIdentity.generate("host")
            save_trusted_sender(esp32.public_bundle, tmp_path / "trusted")
            processor = HostMessageProcessor(
                host_identity=host,
                trusted_dir=tmp_path / "trusted",
                replay_guard=ReplayGuard(tmp_path / "seen.json", max_age_seconds=300),
                action_runner=RemoteActionRunner(dry_run=True),
                audit_log=AuditLog(tmp_path / "audit.log"),
            )
            envelope = encrypt_message(
                instruction_to_text(press_instruction(["alt", "s"])),
                sender=esp32,
                recipient=host.public_bundle,
            )

            result = processor.process_encoded(encode_envelope(envelope))

            self.assertTrue(result["ok"])
            self.assertEqual(result["sender"], "esp32")
            self.assertEqual(result["action"], "press")
            self.assertFalse(result["executed"])
            audit_events = AuditLog(tmp_path / "audit.log").read_recent()
            self.assertEqual(audit_events[-1]["sender"], "esp32")
            self.assertTrue(audit_events[-1]["ok"])
            with self.assertRaises(CamComsCryptoError):
                processor.process_encoded(encode_envelope(envelope))

    def test_rejects_untrusted_sender(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            esp32 = CamComsIdentity.generate("esp32")
            host = CamComsIdentity.generate("host")
            processor = HostMessageProcessor(
                host_identity=host,
                trusted_dir=Path(tmp) / "trusted",
                replay_guard=ReplayGuard(Path(tmp) / "seen.json"),
                action_runner=RemoteActionRunner(dry_run=True),
                audit_log=AuditLog(Path(tmp) / "audit.log"),
            )
            envelope = encrypt_message(
                instruction_to_text(press_instruction(["alt", "s"])),
                sender=esp32,
                recipient=host.public_bundle,
            )

            with self.assertRaises(ValueError):
                processor.process_encoded(encode_envelope(envelope))
            audit_events = AuditLog(Path(tmp) / "audit.log").read_recent()
            self.assertFalse(audit_events[-1]["ok"])
            self.assertEqual(audit_events[-1]["sender"], "esp32")
            self.assertEqual(audit_events[-1]["error"], "sender is not trusted")

    def test_rejects_stale_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = ReplayGuard(Path(tmp) / "seen.json", max_age_seconds=10)
            envelope = {
                "message_id": "old",
                "created_at": int(time.time()) - 20,
            }

            with self.assertRaises(CamComsCryptoError):
                guard.check_and_record(envelope)


if __name__ == "__main__":
    unittest.main()
