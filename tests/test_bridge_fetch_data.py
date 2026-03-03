# -*- coding: utf-8 -*-
"""
Testes do bridge: fetch_data, sync_from_discord, run_diagnostic com respostas mockadas.
Não requer VPS ativa.
"""
import unittest
import sys
import os
import json
import logging

logging.disable(logging.CRITICAL)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestFetchDataMocked(unittest.TestCase):
    """Testes de fetch_data com httpx mockado."""

    def test_fetch_data_returns_list_on_connection_error(self):
        """Em erro de conexão, fetch_data retorna lista com um item de fallback."""
        import httpx
        from core import bridge

        def mock_get(*args, **kwargs):
            raise httpx.ConnectError("Connection refused")

        original_get = httpx.Client.get
        httpx.Client.get = mock_get
        try:
            result = bridge.fetch_data()
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertIn("title", result[0])
            self.assertIn("link", result[0])
        finally:
            httpx.Client.get = original_get

    def test_fetch_data_returns_list_on_empty_sent_news(self):
        """Quando API retorna sent_news=[], fetch_data retorna lista vazia normalizada."""
        import httpx
        from core import bridge

        def mock_get(self, url, headers=None, timeout=None):
            r = type("R", (), {})()
            r.status_code = 200
            if "debug" in url:
                body = {"sent_news_count": 0}
            else:
                body = {"sent_news": []}
            r.content = json.dumps(body).encode()
            r.text = json.dumps(body)
            r.json = lambda: body
            return r

        original_get = httpx.Client.get
        httpx.Client.get = mock_get
        try:
            result = bridge.fetch_data()
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 0)
        finally:
            httpx.Client.get = original_get

    def test_fetch_data_returns_items_when_api_has_data(self):
        """Quando API retorna sent_news com itens, fetch_data retorna lista com itens normalizados."""
        import httpx
        from core import bridge

        payload = {
            "sent_news": [
                {"title": "CVE-2025-0001", "link": "https://nvd.nist.gov/1", "timestamp": "2025-01-01T00:00:00Z"},
                {"title": "CVE-2025-0002", "link": "https://nvd.nist.gov/2", "timestamp": "2025-01-02T00:00:00Z"},
            ]
        }

        def mock_get(self, url, headers=None, timeout=None):
            r = type("R", (), {})()
            r.status_code = 200
            body = payload if "debug" not in url else {"sent_news_count": 2}
            r.content = json.dumps(body).encode()
            r.text = json.dumps(body)
            r.json = lambda: body
            return r

        original_get = httpx.Client.get
        httpx.Client.get = mock_get
        try:
            result = bridge.fetch_data()
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 2)
            for item in result:
                self.assertIn("title", item)
                self.assertIn("link", item)
                self.assertIn("timestamp", item)
                self.assertIn("description", item)
        finally:
            httpx.Client.get = original_get

    def test_fetch_data_filters_test_items(self):
        """Itens com 'test news' ou 'cve-9999' são filtrados e não aparecem no resultado."""
        import httpx
        from core import bridge

        payload = {
            "sent_news": [
                {"title": "Test News CVE-9999", "link": "https://example.com", "timestamp": "2025-01-01"},
                {"title": "CVE-2025-0001 Real", "link": "https://nvd.nist.gov/1", "timestamp": "2025-01-01"},
            ]
        }

        def mock_get(self, url, headers=None, timeout=None):
            r = type("R", (), {})()
            r.status_code = 200
            body = payload if "debug" not in url else {"sent_news_count": 2}
            r.content = json.dumps(body).encode()
            r.text = json.dumps(body)
            r.json = lambda: body
            return r

        original_get = httpx.Client.get
        httpx.Client.get = mock_get
        try:
            result = bridge.fetch_data()
            self.assertEqual(len(result), 1)
            self.assertIn("CVE-2025-0001", result[0]["title"])
        finally:
            httpx.Client.get = original_get


class TestSyncFromDiscordMocked(unittest.TestCase):
    """Testes de sync_from_discord com httpx mockado."""

    def test_sync_returns_true_when_vps_api_ok(self):
        """Quando vps_api retorna 200 e status=ok, sync_from_discord retorna True."""
        import httpx
        from core import bridge

        ok_body = {"status": "ok", "added": 5}

        def mock_post(self, url, **kwargs):
            r = type("R", (), {})()
            r.status_code = 200
            r.content = json.dumps(ok_body).encode()
            r.json = lambda: ok_body
            return r

        original_post = httpx.Client.post
        httpx.Client.post = mock_post
        try:
            out = bridge.sync_from_discord()
            self.assertTrue(out)
        finally:
            httpx.Client.post = original_post

    def test_sync_returns_false_when_both_endpoints_fail(self):
        """Quando porta 8000 e 8080 falham, sync_from_discord retorna False."""
        import httpx
        from core import bridge

        def mock_post(self, url, **kwargs):
            raise httpx.ConnectError("Connection refused")

        original_post = httpx.Client.post
        httpx.Client.post = mock_post
        try:
            out = bridge.sync_from_discord()
            self.assertFalse(out)
        finally:
            httpx.Client.post = original_post


class TestRunDiagnosticMocked(unittest.TestCase):
    """Testes de run_diagnostic com httpx mockado."""

    def test_run_diagnostic_returns_dict_with_expected_keys(self):
        """run_diagnostic retorna dict com data_keys, data_sent_news_count, debug_info, etc."""
        import httpx
        from core import bridge

        data_payload = {"sent_news": [{"title": "CVE-1"}]}
        debug_payload = {"sent_news_count": 10}

        def mock_get(self, url, headers=None, timeout=None):
            r = type("R", (), {})()
            r.status_code = 200
            if "debug" in url:
                r.content = json.dumps(debug_payload).encode()
                r.json = lambda: debug_payload
            else:
                r.content = json.dumps(data_payload).encode()
                r.text = json.dumps(data_payload)
                r.json = lambda: data_payload
            return r

        original_get = httpx.Client.get
        httpx.Client.get = mock_get
        try:
            diag = bridge.run_diagnostic()
            self.assertIn("data_keys", diag)
            self.assertIn("data_sent_news_count", diag)
            self.assertIn("data_content_length", diag)
            self.assertIn("debug_info", diag)
            self.assertEqual(diag["data_sent_news_count"], 1)
        finally:
            httpx.Client.get = original_get

    def test_run_diagnostic_raises_vps_connection_error_on_connect_error(self):
        """run_diagnostic levanta VPSConnectionError quando não consegue conectar."""
        import httpx
        from core import bridge
        from core.exceptions import VPSConnectionError

        def mock_get(self, url, headers=None, timeout=None):
            raise httpx.ConnectError("Connection refused")

        original_get = httpx.Client.get
        httpx.Client.get = mock_get
        try:
            with self.assertRaises(VPSConnectionError):
                bridge.run_diagnostic()
        finally:
            httpx.Client.get = original_get


class TestParseSeverityFromBridge(unittest.TestCase):
    """Garante que parse_severity está acessível e se comporta como esperado."""

    def test_parse_severity_emoji_critical(self):
        from core.bridge import parse_severity
        label, color, icon = parse_severity("🚨 CVE-2025-1234")
        self.assertEqual(label, "CRITICAL")
        self.assertEqual(color, "#dc3545")
        self.assertEqual(icon, "🚨")

    def test_parse_severity_cvss_high(self):
        from core.bridge import parse_severity
        label, color, icon = parse_severity("CVE-2025-0001 (CVSS 7.5)")
        self.assertEqual(label, "HIGH")
        self.assertEqual(color, "#e67e22")
        self.assertEqual(icon, "⚠️")


if __name__ == "__main__":
    unittest.main()
