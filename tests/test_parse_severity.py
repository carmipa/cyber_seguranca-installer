# -*- coding: utf-8 -*-
"""
Teste 4: Classificação de Severidade.
Valida se parse_severity extrai corretamente do título (emoji 🚨 e CVSS).
"""
import unittest
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestParseSeverity(unittest.TestCase):
    """Testes da função parse_severity em core.bridge."""

    def setUp(self):
        from core.bridge import parse_severity
        self.parse_severity = parse_severity

    def test_emoji_critical(self):
        """Emoji 🚨 no título = CRITICAL, vermelho, ícone 🚨."""
        label, color, icon = self.parse_severity("🚨 CVE-2025-1234 RCE crítico")
        self.assertEqual(label, "CRITICAL")
        self.assertEqual(color, "#dc3545")
        self.assertEqual(icon, "🚨")

    def test_cvss_9_critical(self):
        """CVSS >= 9.0 = CRITICAL."""
        label, color, icon = self.parse_severity("CVE-2025-0001 (CVSS 9.8) - Critical")
        self.assertEqual(label, "CRITICAL")
        self.assertEqual(color, "#dc3545")
        self.assertEqual(icon, "🚨")

    def test_cvss_7_high(self):
        """CVSS >= 7.0 = HIGH, laranja, ícone ⚠️."""
        label, color, icon = self.parse_severity("CVE-2025-0002 (CVSS 7.5) - High")
        self.assertEqual(label, "HIGH")
        self.assertEqual(color, "#e67e22")
        self.assertEqual(icon, "⚠️")

    def test_cvss_4_medium(self):
        """CVSS >= 4.0 = MEDIUM, amarelo, ícone 🔶."""
        label, color, icon = self.parse_severity("CVE-2025-0003 (CVSS 5.2) - Medium")
        self.assertEqual(label, "MEDIUM")
        self.assertEqual(color, "#f1c40f")
        self.assertEqual(icon, "🔶")

    def test_no_cvss_info(self):
        """Sem CVSS = INFO."""
        label, color, icon = self.parse_severity("Test News CVE-9999")
        self.assertEqual(label, "INFO")
        self.assertEqual(color, "#00FF00")
        self.assertEqual(icon, "ℹ️")

    def test_cvss_low_info(self):
        """CVSS < 4.0 = INFO."""
        label, color, icon = self.parse_severity("CVE-2025-0004 (CVSS 3.1)")
        self.assertEqual(label, "INFO")
        self.assertEqual(color, "#00FF00")
        self.assertEqual(icon, "ℹ️")


if __name__ == "__main__":
    unittest.main()
