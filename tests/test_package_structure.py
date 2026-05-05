from __future__ import annotations

import importlib
import unittest


class PackageStructureTests(unittest.TestCase):
    def test_fiona_exposes_subsystems(self) -> None:
        import fiona

        self.assertIs(importlib.import_module("fiona.QuikTieper"), fiona.QuikTieper)
        self.assertIs(importlib.import_module("fiona.CamComs"), fiona.CamComs)
        self.assertIs(importlib.import_module("fiona.Vsee"), fiona.Vsee)

    def test_subsystems_are_directly_importable(self) -> None:
        import CamComs
        import QuikTieper
        import Vsee

        self.assertTrue(hasattr(CamComs, "encrypt_message"))
        self.assertTrue(hasattr(CamComs, "CamComsHttpClient"))
        self.assertTrue(hasattr(QuikTieper, "AppLauncher"))
        self.assertIn("ChordListener", QuikTieper.__all__)
        self.assertTrue(hasattr(Vsee, "HologramModel"))


if __name__ == "__main__":
    unittest.main()
