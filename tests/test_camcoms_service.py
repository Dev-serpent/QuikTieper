from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from CamComs import HostService, HostServiceConfig, load_host_service_config, save_host_service_config


class CamComsServiceTests(unittest.TestCase):
    def test_config_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config = HostServiceConfig(
                quiktieper_config_path=Path(tmp) / "bindings.json",
                host_private_path=Path(tmp) / "host.private.json",
                trusted_dir=Path(tmp) / "trusted",
                replay_path=Path(tmp) / "seen.json",
                receiver_host="127.0.0.1",
                receiver_port=9090,
                execute_remote_actions=True,
                start_quiktieper_listener=True,
                allowed_remote_actions=("press", "macro"),
                audit_log_path=Path(tmp) / "audit.log",
            )

            save_host_service_config(config, config_path)
            restored = load_host_service_config(config_path)

            self.assertEqual(restored, config)

    def test_status_reports_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = HostService(
                HostServiceConfig(
                    quiktieper_config_path=Path(tmp) / "missing-bindings.json",
                    host_private_path=Path(tmp) / "missing-host.private.json",
                    trusted_dir=Path(tmp) / "missing-trusted",
                    replay_path=Path(tmp) / "state" / "seen.json",
                    audit_log_path=Path(tmp) / "state" / "audit.log",
                )
            )

            status = service.status()

            self.assertFalse(status["ready"])
            check_names = {check["name"] for check in status["checks"]}
            self.assertIn("quiktieper_config", check_names)
            self.assertIn("host_private_key", check_names)
            self.assertIn("trusted_dir", check_names)
            self.assertIn("audit_log_dir", check_names)


if __name__ == "__main__":
    unittest.main()
