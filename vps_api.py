from fastapi import FastAPI, Request
import json
import os
import httpx

# Logging deve ser configurado antes de outros imports que o usem
from core.logger import get_logger, log_exception

logger = get_logger(__name__)

app = FastAPI()

# Nome do arquivo que seu bot de Discord já gera
NOME_ARQUIVO_JSON = "data/database.json"

# URL do bot na mesma VPS (web server porta 8080)
BOT_TRIGGER_URL = "http://127.0.0.1:8080/api/trigger_scan"
BOT_SYNC_URL = "http://127.0.0.1:8080/api/sync_from_discord"


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Registra todas as requisições HTTP recebidas."""
    client_ip = request.client.host if request.client else "desconhecido"
    logger.info(
        f"Cliente {client_ip} solicitou {request.method} {request.url.path}. "
        "Processando requisição..."
    )
    try:
        response = await call_next(request)
        logger.info(
            f"Requisição {request.method} {request.url.path} atendida com sucesso (status {response.status_code})."
        )
        return response
    except Exception as e:
        log_exception(logger, e, f"Falha ao processar {request.method} {request.url.path}. O servidor encontrou um erro inesperado.")
        raise


@app.get("/data")
def get_security_data():
    """Retorna dados de segurança do JSON gerado pelo bot."""
    try:
        if not os.path.exists(NOME_ARQUIVO_JSON):
            logger.warning(
                f"O arquivo de dados não foi encontrado em {os.path.abspath(NOME_ARQUIVO_JSON)}. "
                "Certifique-se de que o bot de Discord está gerando o database.json ou crie o arquivo manualmente."
            )
            return {"error": "Arquivo JSON não encontrado na VPS"}

        with open(NOME_ARQUIVO_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = len(data.get("sent_news", []))
        logger.debug(f"Dados lidos com sucesso: {items} vulnerabilidade(s) no arquivo, prontas para envio ao cliente.")
        return data

    except json.JSONDecodeError as e:
        log_exception(logger, e, f"O arquivo {NOME_ARQUIVO_JSON} contém JSON inválido (corrompido ou sintaxe incorreta). Corrija o arquivo ou regenere-o.")
        return {"error": f"Erro ao ler JSON: arquivo corrompido ou formato inválido - {e}"}

    except PermissionError as e:
        log_exception(logger, e, f"Sem permissão para ler {NOME_ARQUIVO_JSON}. Verifique as permissões do arquivo e do usuário que executa a API.")
        return {"error": "Sem permissão para acessar o arquivo de dados"}

    except OSError as e:
        log_exception(logger, e, f"Erro ao acessar o disco (arquivo em uso, deletado ou caminho incorreto): {NOME_ARQUIVO_JSON}")
        return {"error": f"Erro ao ler arquivo: {e}"}

    except Exception as e:
        log_exception(logger, e, "Erro inesperado ao buscar dados de segurança. Consulte o traceback para diagnóstico.")
        return {"error": f"Erro interno: {e}"}


@app.post("/sync_from_discord")
def sync_from_discord():
    """
    Sincroniza notícias já no Discord para database.json.
    Chama o bot (porta 8080) para buscar o histórico do canal.
    """
    try:
        logger.info("Solicitação de sync do Discord recebida. Acionando bot...")
        with httpx.Client(timeout=60) as client:
            resp = client.post(BOT_SYNC_URL)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                added = data.get("added", 0)
                logger.info(f"Sync do Discord concluído: {added} item(ns) adicionado(s).")
                return {"status": "ok", "added": added}
            return {"status": "error", "detail": data.get("detail", "Erro no bot")}
        return {"status": "error", "detail": f"Bot retornou {resp.status_code}"}
    except httpx.ConnectError as e:
        logger.warning(f"Bot inacessível em {BOT_SYNC_URL}: {e}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": "Bot não está rodando na VPS."}
        )
    except Exception as e:
        log_exception(logger, e, "Erro ao sincronizar do Discord")
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


@app.post("/trigger_scan")
def trigger_scan():
    """
    Dispara varredura manual no bot. Chama o web server do bot (porta 8080)
    que executa run_scan_once. O painel Windows usa este endpoint.
    """
    try:
        logger.info("Requisição de varredura manual 'NOW' recebida. Acionando bot...")
        with httpx.Client(timeout=60) as client:
            resp = client.post(BOT_TRIGGER_URL)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                logger.info("Varredura iniciada com sucesso no bot.")
                return {"status": "accepted", "detail": "Varredura iniciada. Aguarde alguns segundos e clique em Sincronizar News."}
            return {"status": "accepted", "detail": data.get("detail", "Solicitação enviada.")}
        logger.warning(f"Bot retornou status {resp.status_code}: {resp.text[:200]}")
        return {"status": "accepted", "detail": f"Bot respondeu com {resp.status_code}. Verifique se o bot está rodando na porta 8080."}
    except httpx.ConnectError as e:
        logger.warning(f"Bot inacessível em {BOT_TRIGGER_URL}: {e}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": "Bot não está rodando ou inacessível na porta 8080. Inicie o bot na VPS."}
        )
    except Exception as e:
        log_exception(logger, e, "Erro ao acionar varredura manual 'NOW'.")
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


@app.on_event("startup")
def startup_event():
    logger.info("API da VPS iniciada e pronta para receber requisições na porta 8000.")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("API da VPS encerrada. Servidor parado.")


# Para rodar na VPS: uvicorn vps_api:app --host 0.0.0.0 --port 8000

