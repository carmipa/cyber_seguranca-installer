import customtkinter as ctk
from core.paths import get_icon_path
from core.bridge import (
    fetch_data,
    sync_from_discord,
    parse_severity,
    open_url,
    share_whatsapp,
    share_email,
    trigger_scan_now,
    run_diagnostic,
    DASHBOARD_URL,
)
from core.exceptions import VPSConnectionError
from core.logger import get_logger, log_exception
import os
from PIL import Image, ImageTk

logger = get_logger(__name__)


class Dashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CyberBot GRC - Painel de Controle")
        self.geometry("900x600")

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="🛠️ COMANDOS SOC", font=("Arial", 16, "bold")).pack(pady=10)

        # Botões de Comando
        ctk.CTkButton(
            self.sidebar,
            text="🔄 Sincronizar News",
            width=180,
            height=32,
            corner_radius=8,
            fg_color="#3498db",
            hover_color="#2980b9",
            text_color="white",
            command=self.load_feed,
        ).pack(fill="x", pady=5, padx=10)

        ctk.CTkButton(
            self.sidebar,
            text="🔍 Diagnóstico VPS",
            width=180,
            height=32,
            corner_radius=8,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            text_color="white",
            command=self.run_diagnostic_ui,
        ).pack(fill="x", pady=5, padx=10)

        ctk.CTkButton(
            self.sidebar,
            text="📊 Dashboard Web",
            width=180,
            height=32,
            corner_radius=8,
            fg_color="#2c3e50",
            hover_color="#34495e",
            text_color="white",
            command=lambda: open_url(DASHBOARD_URL),
        ).pack(fill="x", pady=5, padx=10)

        # Busca CVE Direta
        self.cve_entry = ctk.CTkEntry(self.sidebar, placeholder_text="CVE-YYYY-NNNN", width=180)
        self.cve_entry.pack(pady=(20, 0), padx=10)
        ctk.CTkButton(
            self.sidebar,
            text="🧬 Buscar CVE (NVD)",
            width=180,
            height=32,
            corner_radius=8,
            fg_color="#1abc9c",
            hover_color="#16a085",
            text_color="white",
            command=lambda: open_url(f"https://nvd.nist.gov/vuln/detail/{self.cve_entry.get()}"),
        ).pack(fill="x", pady=5, padx=10)

        # Botão de Análise
        self.btn_scan = ctk.CTkButton(
            self.sidebar,
            text="🕵️ Analisar URL (SOC)",
            width=180,
            height=32,
            corner_radius=8,
            fg_color="#d35400",
            hover_color="#e67e22",
            text_color="white",
            command=self.show_scan_tool,
        )
        self.btn_scan.pack(fill="x", pady=5, padx=10)

        # Botão de Varredura Manual (NOW)
        self.btn_now = ctk.CTkButton(
            self.sidebar,
            text="🚀 Executar NOW (Scanner)",
            width=180,
            height=32,
            corner_radius=8,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            text_color="white",
            command=self.trigger_vps_now,
        )
        self.btn_now.pack(fill="x", pady=5, padx=10)

        # Botão de Encerramento Total (vermelho, base da sidebar)
        self.btn_quit = ctk.CTkButton(
            self.sidebar,
            text="⛔ Encerrar Sistema",
            width=180,
            height=32,
            corner_radius=8,
            fg_color="#c0392b",
            hover_color="#a93226",
            text_color="white",
            command=self.confirm_quit,
        )
        self.btn_quit.pack(fill="x", pady=20, padx=10)

        # --- Main Feed ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Feed de Vulnerabilidades (Sent News)")
        self.scroll_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # --- SOLUÇÃO DO ÍCONE E PERFORMANCE ---
        # 1. Define o ícone da janela imediatamente
        self.init_icon()

        # 2. Agenda a carga de dados para 200ms após abrir a janela (Resolve a demora)
        self.after(200, self.start_up_logic)

    def init_icon(self):
        """Define o ícone da barra de título e cards (assets/icon.ico)"""
        self.bot_header_icon = None
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.img_icon = ImageTk.PhotoImage(Image.open(icon_path))
                self.wm_iconphoto(True, self.img_icon)
                # Ícone pequeno para os cards do feed (estilo Discord), via CTkImage
                pil_icon = Image.open(icon_path).convert("RGBA").resize((48, 48), Image.Resampling.LANCZOS)
                self._pil_header_icon = pil_icon  # mantém referência
                self.bot_header_icon = ctk.CTkImage(light_image=pil_icon, size=(24, 24))
                logger.debug(f"Ícone da janela carregado corretamente: {icon_path}")
            else:
                self.bot_header_icon = None
                logger.warning(
                    f"O ícone não foi encontrado em {icon_path}. "
                    "Coloque icon.ico na pasta assets/."
                )
        except Exception as e:
            self.bot_header_icon = None
            log_exception(logger, e, "Falha ao carregar ícone na barra de título. A janela funcionará, mas sem ícone personalizado.")

    # Intervalo em ms: 30 minutos = 30 * 60 * 1000 = 1.800.000
    _INTERVALO_ATUALIZACAO_MS = 30 * 60 * 1000

    def start_up_logic(self):
        """Inicia a carga de dados e o loop de atualização periódica"""
        self.load_feed()
        self.after(self._INTERVALO_ATUALIZACAO_MS, self.auto_update)

    def auto_update(self):
        """Monitoramento periódico alinhado com a política de GRC (evita sobrecarga na VPS)"""
        self.load_feed()
        self.after(self._INTERVALO_ATUALIZACAO_MS, self.auto_update)
        logger.info("Próxima sincronização automática agendada para daqui a 30 minutos.")

    def _render_news(self, news_list: list):
        """Exibe a lista de notícias ou mensagem de vazio no scroll_frame."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        if not news_list:
            msg = (
                "Nenhuma vulnerabilidade no momento.\n\n"
                "1. Clique em «Executar NOW» para disparar uma varredura na VPS.\n"
                "2. Aguarde ~45 segundos (a varredura leva 30-60s).\n"
                "3. O feed será atualizado automaticamente, ou clique em «Sincronizar News».\n\n"
                "Verifique na VPS: bot e vps_api rodando, config.json com channel_id."
            )
            ctk.CTkLabel(
                self.scroll_frame,
                text=msg,
                font=("Arial", 11),
                text_color="#949ba4",
                justify="center",
            ).pack(expand=True, pady=40)
            return
        for i, item in enumerate(news_list):
            try:
                self.create_discord_style_card(self.scroll_frame, item)
            except Exception as e:
                log_exception(
                    logger,
                    e,
                    f"Erro ao exibir o item {i+1} do feed (dados incompletos ou formato inesperado). Os demais itens continuam visíveis.",
                )

    def _fetch_after_sync(self):
        """Chamado após sync; busca dados novamente e renderiza (com delay para o bot gravar)."""
        try:
            if not self.winfo_exists():
                return
            news_list = fetch_data()
            self._render_news(news_list)
        except Exception as e:
            log_exception(logger, e, "Falha ao buscar dados após sync.")
            try:
                self._render_news([])
            except Exception:
                pass

    def load_feed(self):
        """Limpa e recarrega as notícias da VPS. Sincroniza do Discord se necessário."""
        if getattr(self, "_load_feed_running", False):
            return
        self._load_feed_running = True
        try:
            logger.info("Atualizando o painel de vulnerabilidades com os dados mais recentes da VPS...")
            for widget in self.scroll_frame.winfo_children():
                widget.destroy()
            news_list = fetch_data()
            # Se vazio, sincroniza do Discord (notícias já publicadas no canal)
            if not news_list:
                logger.info("Feed vazio. Sincronizando notícias do Discord...")
                if sync_from_discord():
                    # Mensagem de espera enquanto o bot grava no database.json
                    ctk.CTkLabel(
                        self.scroll_frame,
                        text="Sincronizando... Aguarde 2 segundos e os dados serão carregados.",
                        font=("Arial", 11),
                        text_color="#5865f2",
                    ).pack(expand=True, pady=40)
                    self.after(2000, self._fetch_after_sync)
                    return
            self._render_news(news_list)
        except Exception as e:
            log_exception(
                logger,
                e,
                "Falha ao buscar dados do feed. A conexão com a VPS pode ter falhado. Veja as mensagens anteriores para detalhes.",
            )
            self._render_news([])
        finally:
            self._load_feed_running = False

    def create_discord_style_card(self, parent, item):
        """Cria um card no estilo de Embed do Discord, com severidade por cor."""
        title = item.get("title", "(sem título)")
        link = item.get("link", "#")
        timestamp = item.get("timestamp", "Agora")
        description = item.get(
            "description",
            "Nenhuma descrição detalhada disponível para esta vulnerabilidade.",
        )

        # Cor, severidade e ícone de alerta vindos do título (CVSS / 🚨)
        sev_label, sev_color, sev_icon = parse_severity(str(title))

        # Container com barra lateral colorida (estilo Discord: barra à esquerda)
        card_wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        card_wrapper.pack(fill="x", pady=5, padx=10)

        # Barra vertical à esquerda (cor por severidade)
        left_bar = ctk.CTkFrame(
            card_wrapper,
            width=6,
            fg_color=sev_color,
            corner_radius=3,
        )
        left_bar.pack(side="left", fill="y", padx=(0, 0))
        left_bar.pack_propagate(False)

        border_w = 3 if sev_label == "CRITICAL" else 2
        embed_frame = ctk.CTkFrame(
            card_wrapper,
            fg_color="#2b2d31",  # cinza escuro estilo Discord
            border_width=border_w,
            border_color=sev_color,
            corner_radius=6,
        )
        embed_frame.pack(side="left", fill="both", expand=True)

        # Header com nome do bot e badge APP
        header = ctk.CTkFrame(embed_frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(6, 0))

        # Ícone do bot (assets) ou fallback emoji
        if getattr(self, "bot_header_icon", None):
            ctk.CTkLabel(
                header,
                image=self.bot_header_icon,
                text="cyberseguranca_bot",
                font=("Arial", 12, "bold"),
                text_color="#ffffff",
                compound="left",
            ).pack(side="left")
        else:
            ctk.CTkLabel(
                header,
                text="🛡️ cyberseguranca_bot",
                font=("Arial", 12, "bold"),
                text_color="#ffffff",
            ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="APP",
            fg_color="#5865f2",
            text_color="white",
            corner_radius=4,
            font=("Arial", 9, "bold"),
            width=36,
        ).pack(side="left", padx=6)

        # Badge de severidade (CRITICAL / HIGH / MEDIUM / INFO)
        ctk.CTkLabel(
            header,
            text=sev_label,
            fg_color=sev_color,
            text_color="white",
            corner_radius=4,
            font=("Arial", 9, "bold"),
        ).pack(side="right")

        # Linha do título: ícone de alerta + título clicável (estilo Discord)
        title_row = ctk.CTkFrame(embed_frame, fg_color="transparent")
        title_row.pack(fill="x", padx=15, pady=(8, 4))
        ctk.CTkLabel(
            title_row,
            text=sev_icon,
            font=("Segoe UI Emoji", 14),
            text_color=sev_color,
        ).pack(side="left", padx=(0, 6))
        display_title = str(title)[:120] + "..." if len(str(title)) > 120 else str(title)
        ctk.CTkButton(
            title_row,
            text=display_title,
            fg_color="transparent",
            hover_color="#383a40",
            anchor="w",
            text_color="#b9bbbe",
            font=("Arial", 12, "bold"),
            command=lambda u=link: open_url(u),
        ).pack(side="left", fill="x", expand=True)

        # Descrição do problema (corpo do Embed)
        desc_truncated = str(description)[:400] + "..." if len(str(description)) > 400 else str(description)
        ctk.CTkLabel(
            embed_frame,
            text=desc_truncated,
            justify="left",
            wraplength=550,
            font=("Arial", 11),
            text_color="#dbdee1",
        ).pack(fill="x", padx=15, pady=(2, 10))

        # Barra de botões de ação (Leia Mais, WhatsApp, E-mail) — cada um com cor própria
        actions_frame = ctk.CTkFrame(embed_frame, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(
            actions_frame,
            text="📖 Leia Mais",
            width=110,
            height=28,
            fg_color="#5865f2",
            hover_color="#4752c4",
            font=("Arial", 10, "bold"),
            text_color="white",
            command=lambda u=link: open_url(u),
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            actions_frame,
            text="🟢 WhatsApp",
            width=110,
            height=28,
            fg_color="#25d366",
            hover_color="#20bd5a",
            font=("Arial", 10, "bold"),
            text_color="white",
            command=lambda t=title, u=link: share_whatsapp(str(t), u),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame,
            text="📩 E-mail",
            width=110,
            height=28,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=("Arial", 10, "bold"),
            text_color="white",
            command=lambda t=title, d=description, u=link: share_email(str(t), str(d), u),
        ).pack(side="left", padx=5)

        # Rodapé com timestamp
        ctk.CTkLabel(
            embed_frame,
            text=timestamp,
            font=("Arial", 9),
            text_color="#949ba4",
        ).pack(anchor="e", padx=12, pady=(0, 6))

    def show_scan_tool(self):
        """Janela flutuante para análise de IOCs"""
        scan_win = ctk.CTkToplevel(self)
        scan_win.title("SOC Scan Analysis")
        scan_win.geometry("500x250")
        scan_win.attributes('-topmost', True)

        ctk.CTkLabel(scan_win, text="URL para análise (VirusTotal/URLScan):").pack(pady=10)
        url_input = ctk.CTkEntry(scan_win, width=400)
        url_input.pack(pady=10)

        ctk.CTkButton(scan_win, text="Disparar Scanners",
                      command=lambda: self.execute_scans(url_input.get())).pack(pady=10)

    def execute_scans(self, url):
        if url:
            logger.info(f"Abrindo VirusTotal e URLScan para analisar a URL: «{url}»")
            try:
                open_url(f"https://urlscan.io/search/#{url}")
                open_url(f"https://www.virustotal.com/gui/search/{url}")
            except Exception as e:
                log_exception(logger, e, "Não foi possível abrir as ferramentas de análise. Verifique se um navegador está configurado como padrão.")

    def run_diagnostic_ui(self):
        """
        Executa diagnóstico completo da VPS (/data e /debug) e exibe resumo.
        O detalhe completo é registrado nos logs. Útil quando o feed está vazio.
        """
        try:
            diag = run_diagnostic()
            n = diag.get("data_sent_news_count", 0)
            debug_count = (diag.get("debug_info") or {}).get("sent_news_count", "?")
            msg = f"Diagnóstico: /data → {n} itens | /debug → {debug_count}. Veja os logs para detalhes."
            self.show_status(msg, variant="info")
        except VPSConnectionError as e:
            logger.warning("Diagnóstico: %s", e)
            self.show_status(f"VPS inacessível: {e.message}", variant="error")
        except Exception as e:
            log_exception(logger, e, "Erro ao executar diagnóstico VPS.")
            self.show_status(f"Erro no diagnóstico: {e}", variant="error")

    def trigger_vps_now(self):
        """
        Dispara a varredura manual 'NOW' na VPS. A varredura leva ~30-60s.
        Agenda recargas automáticas e mostra instrução ao usuário.
        """
        logger.info("Botão NOW acionado no dashboard. Enviando comando de varredura manual para a VPS...")
        ok = trigger_scan_now()
        if ok:
            self.show_status("Varredura iniciada! Aguarde ~45s e o feed será atualizado automaticamente.", variant="success")
            self.after(45000, self._reload_after_now)   # 1ª recarga após 45s (scan leva ~30-60s)
            self.after(75000, self._reload_after_now)  # 2ª recarga após 75s (caso o scan demore)
        else:
            logger.warning(
                "Não foi possível disparar a varredura 'NOW' na VPS. "
                "Verifique: bot rodando na VPS? vps_api na porta 8000?"
            )
            self.show_status("Falha ao iniciar varredura. Verifique se o bot está rodando na VPS.", variant="error")

    def _reload_after_now(self):
        """
        Recarrega o feed após o NOW (varredura leva ~30-60s).
        Força sync do Discord antes de buscar, para garantir que itens recém-postados apareçam.
        """
        try:
            if not self.winfo_exists():
                return
            logger.info("Recarregando feed após varredura NOW...")
            # Sync do Discord primeiro (itens recém-postados pelo NOW vão para database.json)
            from core.bridge import sync_from_discord
            sync_from_discord()
            self.load_feed()
        except Exception as e:
            log_exception(logger, e, "Erro ao recarregar feed após NOW.")

    def confirm_quit(self):
        """Janela de confirmação antes de encerrar toda a aplicação."""
        logger.info("Usuário pediu encerramento pelo botão 'Encerrar Sistema'. Abrindo diálogo de confirmação.")

        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirmar encerramento")
        dialog.geometry("380x160")
        dialog.transient(self)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(
            dialog,
            text="Deseja realmente encerrar o CyberBot GRC?",
            font=("Arial", 12, "bold"),
            wraplength=340,
            justify="center",
        ).pack(pady=(20, 10), padx=20)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(
            btn_frame,
            text="✅ Sim, encerrar",
            width=130,
            fg_color="#c0392b",
            hover_color="#a93226",
            text_color="white",
            command=lambda: self._confirm_quit_yes(dialog),
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame,
            text="↩️ Não, voltar",
            width=130,
            fg_color="#4e5058",
            hover_color="#6d6f78",
            text_color="white",
            command=dialog.destroy,
        ).pack(side="left", padx=8)

    def _confirm_quit_yes(self, dialog: ctk.CTkToplevel):
        """Confirma o encerramento total após o usuário escolher 'Sim'."""
        logger.info("Usuário confirmou encerramento total. Finalizando aplicação.")
        try:
            dialog.destroy()
        except Exception:
            pass

        try:
            self.quit()
        finally:
            os._exit(0)

    def show_status(self, message: str, variant: str = "info"):
        """Mostra um pequeno popup (toast) no canto da janela com mensagem de status."""
        try:
            self.update_idletasks()
            width, height = 320, 60
            x = self.winfo_x() + 230
            y = self.winfo_y() + 40
        except Exception:
            width, height = 320, 60
            x, y = 200, 200

        color = "#27ae60" if variant == "success" else "#e74c3c" if variant == "error" else "#34495e"

        toast = ctk.CTkToplevel(self)
        toast.title("")
        toast.overrideredirect(True)
        toast.geometry(f"{width}x{height}+{x}+{y}")
        toast.attributes("-topmost", True)

        frame = ctk.CTkFrame(toast, fg_color=color, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(
            frame,
            text=message,
            text_color="white",
            font=("Arial", 11, "bold"),
            justify="center",
            wraplength=width - 20,
        ).pack(expand=True, padx=10, pady=10)

        toast.after(2500, toast.destroy)