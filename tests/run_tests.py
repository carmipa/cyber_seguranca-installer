#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ponto de entrada para executar todos os testes do CyberBot GRC.
Delega para tests/run_all.py.
Uso: python run_tests.py
"""
import sys
import os

# Garante execução a partir da raiz do projeto
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Executa o runner de testes
from tests.run_all import main
sys.exit(main())
