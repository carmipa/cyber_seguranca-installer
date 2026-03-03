"""
Utilitário de caminhos para CyberBot GRC.
Garante que assets e logs funcionem tanto em desenvolvimento quanto após
instalação em C:\\Program Files\\CyberBotGRC (PyInstaller frozen).
"""
import os
import sys


def get_base_path() -> str:
    """
    Retorna o diretório base do aplicativo.
    - Frozen (PyInstaller): diretório de extração temporária (_MEIPASS)
    - Desenvolvimento: raiz do projeto (core/paths.py -> ..)
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_assets_dir() -> str:
    """
    Retorna o diretório de assets (ícones).
    Em frozen: assets estão em _MEIPASS/assets (dentro do exe).
    O instalador também copia assets para {app}\\assets; usamos _MEIPASS
    pois no onefile os assets vêm do bundle.
    """
    base = get_base_path()
    return os.path.join(base, "assets")


def get_icon_path() -> str:
    """
    Retorna o caminho completo do ícone do projeto.
    Prioridade: assets/icon.ico (formato correto para Windows), fallback assets/icon.png.
    """
    assets = get_assets_dir()
    ico = os.path.join(assets, "icon.ico")
    if os.path.exists(ico):
        return ico
    return os.path.join(assets, "icon.png")


def get_logs_dir() -> str:
    """
    Retorna o diretório de logs (persistente).
    Em frozen: usa %LOCALAPPDATA%\\CyberBotGRC\\logs para persistência
    (evita logs em temp que seriam perdidos).
    Em desenvolvimento: usa logs/ na raiz do projeto.
    """
    if getattr(sys, "frozen", False):
        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        logs = os.path.join(appdata, "CyberBotGRC", "logs")
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs = os.path.join(base, "logs")
    return os.path.abspath(logs)
