import customtkinter as ctk
import pystray
from PIL import Image, ImageTk
import threading
import os
import sys

from core.logger import get_logger, log_exception
from core.paths import get_icon_path
from ui.dashboard import Dashboard

logger = get_logger(__name__)


class CyberBotApp:
    def __init__(self):
        self.root = Dashboard()

        # Configuração do Ícone da Janela (Taskbar)
        self.setup_window_icon()

        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        # Minimizar para a bandeja quando o usuário minimizar a janela
        self.root.bind("<Unmap>", self._on_unmap)
        self.setup_tray()

    def setup_window_icon(self):
        """Define o ícone na barra de tarefas e janela (assets/icon.ico)"""
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path).convert("RGBA")
                photo = ImageTk.PhotoImage(img)
                self._icon_ref = photo  # mantém referência
                self.root.after(100, lambda: self.root.wm_iconphoto(True, photo))
                logger.debug(f"Ícone da janela configurado: {icon_path}")
            except Exception as e:
                logger.warning(f"Falha ao carregar ícone ({icon_path}): {e}")

    def hide_window(self):
        logger.debug("Janela minimizada para a bandeja do sistema (próximo ao relógio)")
        self.root.withdraw()

    def show_window(self):
        logger.debug("Janela restaurada (clique em «Abrir Dashboard» na bandeja para ver)")
        self.root.deiconify()
        self.root.focus_force()

    def _on_unmap(self, event):
        """
        Callback chamado quando a janela é minimizada.
        Se o estado for 'iconic', esconde a janela e mantém apenas o ícone na bandeja.
        """
        try:
            if self.root.state() == "iconic":
                logger.debug("Evento de minimização detectado; enviando janela para a bandeja.")
                self.hide_window()
        except Exception as e:
            log_exception(logger, e, "Erro ao processar evento de minimização para bandeja")

    def quit_app(self, icon):
        logger.info("Aplicação sendo encerrada. Até logo!")
        icon.stop()
        self.root.quit()
        os._exit(0)

    def setup_tray(self):
        """Configura o ícone na bandeja do sistema (assets/icon.ico)"""
        icon_path = get_icon_path()
        if not os.path.exists(icon_path):
            image = Image.new('RGB', (64, 64), color=(31, 31, 31))
            logger.warning(
                f"Ícone da bandeja não encontrado em {icon_path}. "
                "Usando ícone padrão. O app funciona normalmente."
            )
        else:
            image = Image.open(icon_path)
            logger.debug(f"Ícone da bandeja do sistema carregado: {icon_path}")

        menu = pystray.Menu(
            pystray.MenuItem("Abrir Dashboard", self.show_window, default=True),
            pystray.MenuItem("Sair do SOC", self.quit_app)
        )

        self.icon = pystray.Icon("CyberBot", image, "CyberBot GRC Monitor", menu)
        thread = threading.Thread(target=self.icon.run, daemon=True)
        thread.start()
        logger.info("Ícone na bandeja do sistema (system tray) configurado. O CyberBot está rodando em segundo plano.")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        # Tratamento de chamada via protocolo customizado (ex: cyberbot://alert/123)
        if len(sys.argv) > 1:
            protocol_call = sys.argv[1]
            logger.info(f"Aplicação chamada via protocolo customizado: {protocol_call}")

        logger.info("CyberBot GRC iniciando... Carregando painel de controle e preparando conexão com a VPS.")
        app = CyberBotApp()
        app.run()
    except Exception as e:
        log_exception(
            logger,
            e,
            "Erro crítico ao iniciar o CyberBot. Verifique o traceback abaixo e as dependências (requirements.txt).",
        )
        sys.exit(1)