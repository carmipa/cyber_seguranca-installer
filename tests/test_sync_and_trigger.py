# -*- coding: utf-8 -*-
"""
Teste 1: Sincronização e Gatilho (NOW).
Valida GET /data e POST /trigger_scan (requer VPS ativa).
"""
import unittest
import sys
import os
import logging

# Desabilita logs durante os testes
logging.disable(logging.CRITICAL)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestFetchData(unittest.TestCase):
    """Testes da função fetch_data (GET /data)."""

    def setUp(self):
        from core.bridge import fetch_data
        self.fetch_data = fetch_data

    def test_fetch_returns_list(self):
        """fetch_data deve retornar uma lista."""
        data = self.fetch_data()
        self.assertIsInstance(data, list)

    def test_fetch_items_have_required_keys(self):
        """Cada item deve ter title, link, timestamp."""
        data = self.fetch_data()
        for item in data:
            self.assertIn("title", item)
            self.assertIn("link", item)
            self.assertIn("timestamp", item)


class TestTriggerScan(unittest.TestCase):
    """Testes da função trigger_scan_now (POST /trigger_scan)."""

    def setUp(self):
        from core.bridge import trigger_scan_now
        self.trigger_scan_now = trigger_scan_now

    def test_trigger_returns_bool(self):
        """trigger_scan_now deve retornar True ou False."""
        result = self.trigger_scan_now()
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
