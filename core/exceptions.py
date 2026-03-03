# -*- coding: utf-8 -*-
"""
Exceções do módulo de comunicação com a VPS (bridge).
Permitem tratamento específico e logs mais claros quando o painel não recebe dados.
"""


class VPSError(Exception):
    """Erro base em operações com a API da VPS."""

    def __init__(self, message: str, status_code: int | None = None, detail: str | None = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class VPSConnectionError(VPSError):
    """Não foi possível conectar à VPS (timeout, recusado, DNS)."""


class VPSEmptyResponseError(VPSError):
    """
    A API retornou 200 mas sent_news está vazio.
    Causas possíveis: database.json vazio na VPS, clean_test_items esvaziou, ou bot ainda não populou.
    """


class VPSInvalidResponseError(VPSError):
    """Resposta da API não é JSON válido ou não contém a estrutura esperada."""


class VPSSyncError(VPSError):
    """Falha ao sincronizar do Discord (sync_from_discord retornou erro ou timeout)."""
