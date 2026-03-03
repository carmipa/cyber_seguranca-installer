"""
Módulo centralizado de logging para CyberBot GRC.
Fornece logs robustos para monitoramento de toda a aplicação.
Usa caminhos dinâmicos: em instalação (Program Files), logs vão para %LOCALAPPDATA%.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from core.paths import get_logs_dir

# Diretório de logs (dinâmico: dev=./logs, instalado=%LOCALAPPDATA%\\CyberBotGRC\\logs)
LOGS_DIR = get_logs_dir()
DEFAULT_LOG_FILE = os.path.join(LOGS_DIR, "cyberbot.log")
ERROR_LOG_FILE = os.path.join(LOGS_DIR, "cyberbot_errors.log")

# Garante que o diretório existe
os.makedirs(LOGS_DIR, exist_ok=True)


def _enable_windows_ansi():
    """Habilita suporte a cores ANSI no console do Windows."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


_enable_windows_ansi()

# ANSI escape codes para cores (funciona em Windows 10+, PowerShell, Terminal)
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RED = "\033[91m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_BLUE = "\033[94m"
_CYAN = "\033[96m"
_MAGENTA = "\033[95m"
_GRAY = "\033[90m"

# Ícones por nível
_ICONS = {
    logging.DEBUG: "🔍",
    logging.INFO: "📌",
    logging.WARNING: "⚠️",
    logging.ERROR: "🚨",
    logging.CRITICAL: "❌",
}

# Cores por nível
_COLORS = {
    logging.DEBUG: _GRAY,
    logging.INFO: _CYAN,
    logging.WARNING: _YELLOW,
    logging.ERROR: _RED,
    logging.CRITICAL: _BOLD + _RED,
}


class ColorConsoleFormatter(logging.Formatter):
    """Formatador colorido com ícones para saída no console."""

    def format(self, record: logging.LogRecord) -> str:
        levelno = record.levelno
        icon = _ICONS.get(levelno, "•")
        color = _COLORS.get(levelno, _RESET)

        levelname = f"{color}{icon} {record.levelname:8}{_RESET}"
        time_str = f"{_DIM}{self.formatTime(record, self.datefmt)}{_RESET}"
        location = f"{_GRAY}{record.name}:{record.funcName}:{record.lineno}{_RESET}"
        msg = record.getMessage()

        result = f"{time_str} | {levelname} | {location} | {msg}"
        if record.exc_info:
            result += "\n" + self.formatException(record.exc_info)
        return result


def _create_formatter():
    """Formato detalhado para facilitar monitoramento (arquivos)."""
    return logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _create_console_handler(level=logging.INFO):
    """Handler colorido com ícones para saída no console."""
    # Usa UTF-8 para suportar emojis no Windows
    try:
        stream = sys.stdout
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(ColorConsoleFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
    return handler


def _create_file_handler(log_file, level=logging.DEBUG, max_bytes=5_000_000, backup_count=5):
    """Handler com rotação de arquivo para evitar arquivos enormes."""
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(_create_formatter())
    return handler


def _create_error_handler():
    """Handler separado apenas para erros (arquivo dedicado)."""
    handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(logging.ERROR)
    handler.setFormatter(_create_formatter())
    return handler


def get_logger(name: str, level: int = None) -> logging.Logger:
    """
    Retorna um logger configurado para o módulo.
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        level: Nível de log opcional (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evita duplicar handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level or logging.DEBUG)
    
    # Console: INFO+
    logger.addHandler(_create_console_handler(logging.INFO))
    
    # Arquivo principal: DEBUG+
    logger.addHandler(_create_file_handler(DEFAULT_LOG_FILE, logging.DEBUG))
    
    # Arquivo de erros: apenas ERROR+
    logger.addHandler(_create_error_handler())
    
    return logger


def log_exception(logger: logging.Logger, exc: BaseException, context: str = ""):
    """
    Registra uma exceção com traceback completo.
    
    Args:
        logger: Logger a ser usado
        exc: A exceção capturada
        context: Descrição opcional do contexto onde ocorreu
    """
    msg = f"{context} - {type(exc).__name__}: {exc}" if context else f"{type(exc).__name__}: {exc}"
    logger.error(msg, exc_info=True)
