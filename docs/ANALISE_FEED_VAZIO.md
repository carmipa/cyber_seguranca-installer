# Análise: Feed de vulnerabilidades vazio no painel

## Sintoma

O **CyberBot GRC - Painel de Controle** exibe "Nenhuma vulnerabilidade no momento" mesmo quando:

- O bot na VPS está rodando e publicando no Discord.
- Os logs da VPS mostram "database.json atualizado (total=N)" e "Sync do Discord: N notícias".
- O endpoint `/data` na VPS (vps_api, porta 8000) existe e responde HTTP 200.

Nos logs do instalador aparecem:

- `API retornou 0 itens, mas /debug reporta sent_news_count=0`
- `Sync do Discord concluído: 0 notícia(s) adicionada(s).`

## Arquitetura relevante

| Componente | Função |
|------------|--------|
| **Bot (VPS)** | Coleta feeds RSS/NVD, publica no Discord e grava em `data/database.json`. |
| **vps_api (VPS, porta 8000)** | Lê `data/database.json` (volume compartilhado com o bot) e expõe `/data`, `/sync_from_discord`, `/trigger_scan`, `/debug`, `/clean_test_items`. |
| **Painel (instalador)** | Consome `GET http://VPS:8000/data` e exibe o feed; pode chamar sync e trigger_scan. |

O feed do painel vem **só** do que a API retorna em `/data`, que por sua vez lê o **mesmo** `database.json` que o bot atualiza.

## Causa raiz identificada

1. **`clean_test_items` esvaziando o arquivo**  
   O endpoint `/clean_test_items` **removia itens** do `database.json` na VPS. Em algum momento esse endpoint foi chamado (pelo painel ou por outro cliente). Depois disso, quando o painel pedia `/data`, a API lia um arquivo já esvaziado e devolvia `sent_news: []` e `/debug` reportava `sent_news_count=0`.

2. **Sync retorna 0 adicionados**  
   O sync (`/sync_from_discord`) **repopula** o `database.json` a partir das mensagens do Discord. Se o bot já tiver escrito as notícias no arquivo, o sync não adiciona nada ("0 adicionados"). O problema não é o sync em si, e sim o fato de o **arquivo estar vazio (ou ser lido vazio)** quando a API responde ao painel.

3. **Versão da VPS**  
   Se a VPS ainda estiver com uma versão antiga do `vps_api` em que `/clean_test_items` **realmente remove** itens, qualquer chamada a esse endpoint (ou um instalador antigo que ainda o chame) pode esvaziar de novo o `database.json`.

## O que foi feito no código

### projeto-cyberseguranca-bot-python (VPS)

- **vps_api.py**: `/clean_test_items` foi **desativado** (no-op: não remove mais itens; retorna `removed: 0`, `remaining: count`).
- **vps_api.py**: Uso de `logging` padrão (correção de `ModuleNotFoundError` na VPS).
- **utils/discord_sync.py**: `channel_id` como `int`, fallback com `fetch_channel`, logs quando muitas mensagens mas 0 adicionados.

### cyber_seguranca-installer (painel)

- **core/bridge.py**: **Removida** a chamada a `clean_test_items` no fluxo de sync. O filtro de itens de teste é feito no bridge (`_filter_test_items`) na exibição.
- **core/bridge.py**: Logs mais detalhados: `body_len`, `keys` da resposta, mensagens de aviso quando 0 itens com possíveis causas (database vazio, clean_test_items, bot não populou).
- **core/bridge.py**: Função **`run_diagnostic()`**: chama `/data` e `/debug`, registra em log status, tamanho, keys e contagem; em falha de conexão levanta `VPSConnectionError`.
- **core/exceptions.py**: Novas exceções `VPSError`, `VPSConnectionError`, `VPSEmptyResponseError`, `VPSInvalidResponseError`, `VPSSyncError` para tratamento e logs específicos.
- **ui/dashboard.py**: Ajustes de delay após "Executar NOW" e chamada a `sync_from_discord` antes de recarregar o feed.
- **tests/test_bridge_fetch_data.py**: Testes com mocks para `fetch_data`, `sync_from_discord`, `run_diagnostic` (respostas vazias, com dados, erro de conexão, filtro de itens de teste).

## Como diagnosticar quando o feed continua vazio

1. **Logs do painel**  
   - **Desenvolvimento:** `cyber_seguranca-installer/logs/cyberbot.log`
   - **Instalado (Windows):** `%LOCALAPPDATA%\CyberBotGRC\logs\cyberbot.log` (ver `core.paths.get_logs_dir()`).
   Com nível DEBUG (se disponível), o bridge passa a registrar:
   - `Resposta /data: status=... body_len=... keys=...`
   - Quando há 0 itens: `Preview da resposta /data (quando 0 itens): ...`

2. **Diagnóstico explícito**  
   No código ou por um botão/menu "Diagnóstico":
   - Chamar `core.bridge.run_diagnostic()`.
   - Isso faz GET em `/data` e `/debug` e loga: `Diagnóstico VPS: /data status=... len=... keys=... sent_news_count=... | /debug status=... sent_news_count=...`.
   - Em caso de conexão recusada, `run_diagnostic()` levanta `VPSConnectionError`.

3. **Na VPS (Docker)**
   - Confirmar que **cyber-bot** e **cyber-vps-api** estão rodando: `docker ps`.
   - Bot e vps_api devem usar o **mesmo volume** `./data:/app/data`; o bot usa `DATA_DIR=/app/data` para gravar `database.json`.
   - Ver o que a API realmente lê:
     ```bash
     docker exec cyber-vps-api cat /app/data/database.json | head -c 800
     ```
   - Ver diagnóstico da API: `curl -s http://127.0.0.1:8000/debug`.
   - Se `sent_news_count=0`, repovoar um item de teste: `curl -X POST http://127.0.0.1:8000/debug_seed`. Em seguida abrir o painel e clicar em Sincronizar; se aparecer 1 item, o fluxo está ok e o problema era o arquivo vazio.
   - Confirmar que a versão do **vps_api** tem **`/clean_test_items` em modo no-op** (não remove itens).

## Resumo

O feed fica vazio quando a API devolve `sent_news` vazio, ou seja, quando o `database.json` na VPS está vazio ou é lido vazio. A causa que foi corrigida no código foi o **uso de `clean_test_items`**, que chegou a esvaziar esse arquivo. Com o endpoint desativado no servidor e a remoção da chamada no instalador, mais logs, exceções, testes e esta documentação, fica mais fácil manter e diagnosticar o problema se ele voltar a ocorrer.

---

## Documentação relacionada

- **[README.md](../README.md)** – Visão geral, arquitetura, `core/bridge`, `core/logger`, `core/exceptions`, `core/paths`, build e instalador.
- **[tests/TESTES_VALIDACAO.md](../tests/TESTES_VALIDACAO.md)** – Checklist de validação (NOW, System Tray, instalador, severidade) e testes automatizados.
