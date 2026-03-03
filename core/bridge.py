import httpx
import webbrowser
import re
import json
import time
from urllib.parse import quote

from core.logger import get_logger, log_exception
from core.exceptions import VPSConnectionError

logger = get_logger(__name__)

# Dados da sua VPS conforme sua análise
VPS_IP = "72.61.219.15"
URL_DADOS_BASE = f"http://{VPS_IP}:8000/data"
URL_DEBUG = f"http://{VPS_IP}:8000/debug"
URL_TRIGGER_SCAN = f"http://{VPS_IP}:8000/trigger_scan"
URL_SYNC_DISCORD = f"http://{VPS_IP}:8000/sync_from_discord"
# NÃO usar clean_test_items: o endpoint esvaziava o database.json (agora é no-op na VPS).
# Fallback: bot expõe /api/sync_from_discord na porta 8080 (quando vps_api retorna 404)
URL_SYNC_BOT_DIRECT = f"http://{VPS_IP}:8080/api/sync_from_discord"
DASHBOARD_URL = f"http://{VPS_IP}:1880/ui/#!/0?socketid=dPZBDv6FYRh9ZhZSAAAa"


def sync_from_discord() -> bool:
    """
    Sincroniza notícias do Discord para o database.json (via vps_api ou bot direto).
    Retorna True se ok, False em caso de erro.
    """
    def _do_sync(url: str) -> tuple[bool, int | None, str]:
        """Tenta sync na URL. Retorna (sucesso, added ou None, mensagem_erro)."""
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(url)
            if resp.status_code == 200:
                data = resp.json() if resp.content else {}
                if data.get("status") == "ok":
                    return True, data.get("added", 0), ""
            return False, None, f"HTTP {resp.status_code}"
        except httpx.ConnectError as e:
            return False, None, f"Conexão recusada: {e}"
        except httpx.TimeoutException:
            return False, None, "Timeout"
        except Exception as e:
            return False, None, str(e)

    # NÃO chamar clean_test_items aqui - ele esvazia o database.json antes do painel buscar.
    # O filtro de itens de teste é feito no bridge (_filter_test_items) ao exibir.
    # clean_test_items só deve ser chamado manualmente se o usuário quiser limpar.

    # 1. Tenta via vps_api (porta 8000)
    ok, added, err1 = _do_sync(URL_SYNC_DISCORD)
    if ok:
        logger.info(f"Sync do Discord concluído: {added} notícia(s) adicionada(s).")
        return True

    # 2. Fallback: tenta bot direto (porta 8080) - exige firewall aberto
    logger.info("Tentando sync via bot diretamente (porta 8080)...")
    ok, added, err2 = _do_sync(URL_SYNC_BOT_DIRECT)
    if ok:
        logger.info(f"Sync do Discord concluído (via bot): {added} notícia(s) adicionada(s).")
        return True

    logger.warning(
        f"Sync falhou. Porta 8000: {err1}. Porta 8080: {err2}. "
        "Atualize vps_api.py na VPS com /sync_from_discord e reinicie: sudo systemctl restart cyberbot-api"
    )
    return False


def _fetch_debug() -> dict | None:
    """Chama /debug na VPS para diagnóstico quando o feed vem vazio."""
    try:
        with httpx.Client(timeout=5) as client:
            r = client.get(URL_DEBUG)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.debug("Falha ao obter /debug: %s", e)
    return None


def run_diagnostic() -> dict:
    """
    Diagnóstico minucioso: chama /data e /debug e registra em log resposta bruta e contagens.
    Útil quando o painel mostra 0 vulnerabilidades para entender se o problema é na VPS ou no cliente.
    Retorna um dicionário com: data_keys, data_sent_news_count, data_raw_preview, debug_info, data_content_length.
    """
    result = {
        "data_keys": [],
        "data_sent_news_count": 0,
        "data_raw_preview": "",
        "data_content_length": 0,
        "debug_info": None,
        "data_status_code": None,
        "debug_status_code": None,
    }
    try:
        url_data = f"{URL_DADOS_BASE}?_={int(time.time() * 1000)}"
        with httpx.Client(timeout=15) as client:
            r_data = client.get(url_data, headers={"Cache-Control": "no-cache"})
        result["data_status_code"] = r_data.status_code
        result["data_content_length"] = len(r_data.content)
        raw_text = r_data.text
        if result["data_content_length"] > 2000:
            result["data_raw_preview"] = raw_text[:1000] + "\n... [truncado] ...\n" + raw_text[-500:]
        else:
            result["data_raw_preview"] = raw_text
        try:
            data = r_data.json()
            result["data_keys"] = list(data.keys()) if isinstance(data, dict) else []
            sent = data.get("sent_news", [])
            result["data_sent_news_count"] = len(sent) if isinstance(sent, list) else 0
        except json.JSONDecodeError:
            result["data_keys"] = ["(JSON inválido)"]

        with httpx.Client(timeout=5) as client:
            r_debug = client.get(URL_DEBUG)
        result["debug_status_code"] = r_debug.status_code
        if r_debug.status_code == 200:
            result["debug_info"] = r_debug.json()

        logger.info(
            "Diagnóstico VPS: /data status=%s len=%s keys=%s sent_news_count=%s | /debug status=%s sent_news_count=%s",
            result["data_status_code"],
            result["data_content_length"],
            result["data_keys"],
            result["data_sent_news_count"],
            result["debug_status_code"],
            (result["debug_info"] or {}).get("sent_news_count", "?"),
        )
        if result["data_sent_news_count"] == 0 and result["data_content_length"] < 500:
            logger.debug("Resposta /data (preview): %s", result["data_raw_preview"][:500])
    except httpx.ConnectError as e:
        logger.warning("Diagnóstico: não foi possível conectar à VPS: %s", e)
        raise VPSConnectionError(f"VPS inacessível: {e}", detail=str(e))
    except Exception as e:
        logger.exception("Erro durante diagnóstico VPS: %s", e)
        raise
    return result


def fetch_data():
    """
    Busca dados da API da VPS.
    Retorna lista vazia ou item de erro em caso de falha (para não quebrar a UI).
    Usa cache-busting para evitar respostas em cache de proxies.
    """
    # Cache-busting: evita que proxies/CDNs retornem resposta antiga vazia
    url = f"{URL_DADOS_BASE}?_={int(time.time() * 1000)}"
    headers = {"Cache-Control": "no-cache, no-store", "Pragma": "no-cache"}

    try:
        logger.info(
            f"Buscando notícias de vulnerabilidades no servidor VPS ({URL_DADOS_BASE}). "
            "Isso pode levar alguns segundos..."
        )

        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.error(
                    f"O servidor respondeu com código {response.status_code} em vez de 200 (sucesso). "
                    f"Verifique se a API está configurada corretamente em {URL_DADOS_BASE}"
                )
                return [_error_fallback_item(f"API retornou status {response.status_code}")]

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                log_exception(logger, e, "O servidor retornou dados que não são JSON válido. Pode haver erro no backend.")
                return [_error_fallback_item(f"Resposta da API com JSON inválido: {e}")]

            # Log detalhado da estrutura recebida (ajuda a debugar feed vazio)
            resp_keys = list(data.keys()) if isinstance(data, dict) else []
            body_len = len(response.content)
            logger.debug(
                "Resposta /data: status=%s body_len=%s keys=%s",
                response.status_code,
                body_len,
                resp_keys,
            )

            sent_news = data.get("sent_news", [])
            raw_count = len(sent_news) if isinstance(sent_news, list) else 0
            if raw_count > 0:
                logger.info(f"API retornou {raw_count} itens em sent_news (antes do filtro).")
            elif raw_count == 0:
                # Diagnóstico: verifica o que o servidor reporta (evita cache/proxy)
                debug_info = _fetch_debug()
                if debug_info:
                    svc_count = debug_info.get("sent_news_count", "?")
                    logger.warning(
                        "API retornou 0 itens, mas /debug reporta sent_news_count=%s. "
                        "Possíveis causas: database.json vazio na VPS, clean_test_items esvaziou o arquivo, "
                        "ou bot ainda não populou. Keys em /data: %s. Tente Sincronizar News ou Executar NOW.",
                        svc_count,
                        resp_keys,
                    )
                else:
                    logger.warning(
                        "API retornou 0 itens. Servidor pode estar vazio ou indisponível. Keys em /data: %s",
                        resp_keys,
                    )
                # Preview da resposta para diagnóstico (evita segunda requisição)
                try:
                    raw_preview = json.dumps(data)[:400]
                    logger.debug("Preview da resposta /data (quando 0 itens): %s", raw_preview)
                except Exception:
                    pass

            if "error" in data:
                logger.warning(
                    f"O servidor indicou um problema: «{data['error']}». "
                    "Verifique os logs da API na VPS para mais detalhes."
                )
                return [_error_fallback_item(data["error"])]

            if not isinstance(sent_news, list):
                logger.error(
                    f"O servidor deveria retornar uma lista de notícias, mas retornou {type(sent_news).__name__}. "
                    "O formato do database.json pode estar incorreto."
                )
                return [_error_fallback_item("Formato de dados inválido")]

            filtered = _filter_test_items(sent_news)
            if len(sent_news) > 0 and len(filtered) == 0:
                logger.warning(
                    f"API retornou {len(sent_news)} itens, mas todos foram filtrados (teste). "
                    "Verifique se database.json tem notícias reais."
                )
            logger.info(
                f"Conectado com sucesso! {len(filtered)} vulnerabilidade(s) carregada(s) e exibidas no painel."
            )
            return _normalize_items(filtered)

    except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
        logger.warning(
            f"Tempo limite excedido (10s) ao conectar na VPS. Possíveis causas: "
            "servidor offline, firewall bloqueando, rede lenta ou IP/porta incorretos. "
            f"Detalhe: {e}"
        )
        return [_error_fallback_item(f"Timeout de conexão: {e}")]

    except httpx.ConnectError as e:
        logger.warning(
            f"Não foi possível alcançar o servidor VPS. Verifique: "
            "1) A API está rodando na VPS? 2) Firewall permite conexões na porta 8000? "
            "3) O IP está correto? "
            f"Detalhe: {e}"
        )
        return [_error_fallback_item(f"Servidor VPS inacessível: {e}")]

    except httpx.HTTPStatusError as e:
        log_exception(logger, e, "Resposta HTTP com erro (4xx/5xx). O servidor encontrou um problema ao processar a requisição.")
        return [_error_fallback_item(f"Erro HTTP: {e}")]

    except Exception as e:
        log_exception(logger, e, "Erro inesperado ao buscar dados. Consulte o traceback abaixo para detalhes.")
        return [_error_fallback_item(f"Erro de conexão: {e}")]


def _error_fallback_item(message: str):
    """Item de fallback exibido na UI quando há erro."""
    return {"title": message, "link": "#", "timestamp": "", "description": message}


def _filter_test_items(items: list) -> list:
    """
    Remove entradas de teste do feed (ex.: Test News CVE-9999, example.com).
    Exceção: o item do debug_seed (CVE-2024-1234 - Verificação do painel) é mantido quando
    é o único item, para o usuário confirmar que o pipeline VPS → painel funciona.
    """
    result = []
    test_patterns = (
        "test news",
        "teste",
        "cve-9999",
        "example.com",
    )
    for item in items:
        if not isinstance(item, dict):
            continue
        title = item.get("title", "").lower()
        link = item.get("link", "").lower()
        if any(p in title or p in link for p in test_patterns):
            # Manter item de diagnóstico do debug_seed se for o único (ajuda a confirmar pipeline)
            if len(items) == 1 and "cve-2024-1234" in link and "verificação do painel" in title:
                logger.info("Exibindo item de diagnóstico (debug_seed) para confirmar que o pipeline está ok.")
                result.append(item)
                break
            logger.debug(f"Item de teste filtrado: {item.get('title', '')[:50]}...")
            continue
        result.append(item)
    return result


def _normalize_items(items: list) -> list:
    """
    Garante que cada item tenha 'description'.
    O database.json do bot pode ter apenas title/link/timestamp.
    """
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        desc = item.get("description") or item.get("summary") or ""
        if not desc.strip():
            link = item.get("link", "#")
            if link and link != "#":
                desc = "Clique em 'Leia Mais' para acessar os detalhes completos da vulnerabilidade."
            else:
                desc = "Nenhuma descrição detalhada disponível para esta vulnerabilidade."
        result.append({**item, "description": desc})
    return result

def parse_severity(title: str):
    """
    Classificação de severidade alinhada ao bot da VPS (utils.storage + scanner.classify_severity).
    Retorna (label, cor_borda, emoji_icone) para o painel exibir como no Discord (barra lateral + ícone).
    - CRITICAL: vermelho (#dc3545), ícone 🚨
    - HIGH: laranja (#e67e22), ícone ⚠️
    - MEDIUM: amarelo (#f1c40f), ícone 🔶
    - INFO: verde/azul (#00FF00), ícone ℹ️
    """
    title_str = str(title)
    if "🚨" in title_str:
        return "CRITICAL", "#dc3545", "🚨"
    match = re.search(r"CVSS (\d+\.\d+)", title_str)
    if match:
        score = float(match.group(1))
        if score >= 9.0:
            return "CRITICAL", "#dc3545", "🚨"
        if score >= 7.0:
            return "HIGH", "#e67e22", "⚠️"
        if score >= 4.0:
            return "MEDIUM", "#f1c40f", "🔶"
    return "INFO", "#00FF00", "ℹ️"

def open_url(url):
    """Abre URL no navegador padrão."""
    try:
        webbrowser.open(url)
        logger.debug(f"Navegador abriu a URL com sucesso: {url}")
    except Exception as e:
        log_exception(logger, e, f"Não foi possível abrir o navegador. Verifique se um navegador padrão está configurado no sistema. URL: {url}")
        raise


def share_whatsapp(title: str, link: str):
    """Abre WhatsApp Web com o texto pré-preenchido para compartilhar o alerta."""
    text = f"{title}\n\nLeia mais: {link}"
    url = f"https://wa.me/?text={quote(text, safe='')}"
    try:
        webbrowser.open(url)
        logger.info(f"Compartilhamento via WhatsApp iniciado: {title[:50]}...")
    except Exception as e:
        log_exception(logger, e, "Falha ao abrir WhatsApp para compartilhamento.")


def share_email(title: str, description: str, link: str = ""):
    """Abre o cliente de e-mail padrão com assunto e corpo pré-preenchidos."""
    subject = quote(f"[CyberIntel SOC] {title}", safe="")
    body_parts = [description]
    if link:
        body_parts.append(f"\n\nLeia mais: {link}")
    body = quote("\n".join(body_parts), safe="")
    url = f"mailto:?subject={subject}&body={body}"
    try:
        webbrowser.open(url)
        logger.info(f"Envio de e-mail iniciado: {title[:50]}...")
    except Exception as e:
        log_exception(logger, e, "Falha ao abrir cliente de e-mail.")


def trigger_scan_now() -> bool:
    """
    Dispara uma varredura manual "NOW" na VPS.
    Retorna True em caso de sucesso (status 200), False caso contrário.
    """
    try:
        logger.info(f"Solicitando varredura manual 'NOW' na VPS em {URL_TRIGGER_SCAN}...")
        with httpx.Client() as client:
            response = client.post(URL_TRIGGER_SCAN, timeout=30)

        if response.status_code == 200:
            logger.info("Scan manual 'NOW' aceito pela VPS. Atualize o painel para ver os novos dados.")
            return True

        logger.error(
            f"A VPS respondeu com status {response.status_code} ao tentar disparar o scan manual."
        )
        return False

    except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
        logger.warning(
            f"Timeout ao chamar o endpoint de varredura 'NOW' na VPS. "
            f"Verifique conectividade e se a API está rodando. Detalhe: {e}"
        )
        return False

    except httpx.ConnectError as e:
        logger.warning(
            f"Não foi possível conectar ao endpoint de varredura 'NOW' na VPS ({URL_TRIGGER_SCAN}). Detalhe: {e}"
        )
        return False

    except Exception as e:
        log_exception(logger, e, "Erro inesperado ao disparar varredura 'NOW' na VPS.")
        return False