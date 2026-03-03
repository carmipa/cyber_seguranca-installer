# -*- coding: utf-8 -*-
"""
Teste 0: Estrutura e Imports.
Verifica se todos os módulos e dependências carregam corretamente.
"""
import unittest
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestImports(unittest.TestCase):
    """Testes de imports dos módulos do projeto."""

    def test_core_bridge_imports(self):
        """core.bridge deve exportar as funções principais."""
        from core.bridge import (
            fetch_data,
            parse_severity,
            open_url,
            share_whatsapp,
            share_email,
            trigger_scan_now,
        )
        self.assertTrue(callable(fetch_data))
        self.assertTrue(callable(parse_severity))
        self.assertTrue(callable(open_url))
        self.assertTrue(callable(share_whatsapp))
        self.assertTrue(callable(share_email))
        self.assertTrue(callable(trigger_scan_now))

    def test_core_logger_import(self):
        """core.logger deve exportar get_logger e log_exception."""
        from core.logger import get_logger, log_exception
        self.assertTrue(callable(get_logger))
        self.assertTrue(callable(log_exception))

    def test_ui_dashboard_import(self):
        """ui.dashboard deve exportar a classe Dashboard."""
        from ui.dashboard import Dashboard
        self.assertTrue(hasattr(Dashboard, "load_feed"))
        self.assertTrue(hasattr(Dashboard, "create_discord_style_card"))

    def test_dependencies_available(self):
        """Dependências externas devem estar instaladas."""
        import customtkinter as ctk
        import pystray
        from PIL import Image
        self.assertTrue(ctk is not None)
        self.assertTrue(pystray is not None)
        self.assertTrue(Image is not None)


if __name__ == "__main__":
    unittest.main()
