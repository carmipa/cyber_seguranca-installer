# -*- coding: utf-8 -*-
"""
Configuração para execução dos testes.
Garante que o diretório raiz do projeto esteja no sys.path.
"""
import sys
import os

# Adiciona a raiz do projeto ao path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
