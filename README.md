<div align="center">

# 🛡️ CyberBot GRC – Painel de Controle & SOC

<img src="assets/icon.png" alt="Ícone do CyberBot GRC" width="180" />

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Platform](https://img.shields.io/badge/Plataforma-Windows%20%7C%20Linux-2C3E50)](#)
[![Status](https://img.shields.io/badge/Status-Ativo-success)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#)

Dashboard Windows para monitorar ameaças de cibersegurança em tempo real, integrado ao bot do Discord e à sua VPS.

</div>

---

## 📥 Download rápido do instalador

- **Windows (instalador completo)**: [Baixar `CyberBot_Setup.exe`](dist_installer/CyberBot_Setup.exe?raw=1)

---

## 📁 Navegação da documentação

| Arquivo | Conteúdo |
|---------|----------|
| **[README.md](README.md)** (este arquivo) | Visão geral, arquitetura, componentes, como rodar, build e instalador |
| **[tests/TESTES_VALIDACAO.md](tests/TESTES_VALIDACAO.md)** | Checklist de validação (NOW, System Tray, instalador, severidade) e testes automatizados |
| **[docs/ANALISE_FEED_VAZIO.md](docs/ANALISE_FEED_VAZIO.md)** | Diagnóstico quando o feed exibe 0 vulnerabilidades (causas, exceções, `run_diagnostic`) |

---

## 📌 Visão Geral

O **CyberBot GRC** é um ecossistema de monitoramento de segurança composto por:

- 🤖 **Bot do Discord** – coleta alertas de fontes externas, gera Embeds e grava o `database.json` na VPS.
- 🌐 **API FastAPI (VPS)** – expõe os dados de segurança via HTTP e recebe comandos de varredura (`/trigger_scan`).
- 💻 **App Desktop Windows (CustomTkinter)** – painel gráfico que:
  - Exibe os alertas em cards no estilo **Embed do Discord**;
  - Usa cores por severidade (CRITICAL / HIGH / MEDIUM / INFO);
  - Possui botões de ação (Leia Mais, WhatsApp, E-mail, NOW, Encerrar);
  - Mantém **logs estruturados** em arquivos rotativos.

Todo o fluxo foi pensado para **GRC (Governança, Risco e Conformidade)**, com foco em:

- Disponibilidade ✅
- Integridade dos dados ✅
- Confidencialidade (via VPS) ✅
- Auditabilidade (logs detalhados) ✅

---

## 🏗️ Arquitetura

O diagrama abaixo usa [Mermaid](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams) e é renderizado pelo próprio GitHub na visualização do README.

```mermaid
flowchart LR
    subgraph Discord
        B[Bot cyberseguranca_bot]
    end

    subgraph VPS
        D[database.json sent_news]
        A[FastAPI vps_api]
    end

    subgraph Windows
        W[CyberBot GRC CustomTkinter]
        L[Logs cyberbot.log]
    end

    B -->|Gera alerts e grava| D
    W <-->|GET /data POST /trigger_scan| A
    W -->|Logs| L
```

### Visão de componentes

```mermaid
flowchart TB
    subgraph windowsApp [WindowsApp]
        ui["UI CustomTkinter (ui/dashboard.py)"]
        bridge["core.bridge (HTTP, compartilhamento)"]
        logger["core.logger (logs locais)"]
        paths["core.paths (assets, logs)"]
    end

    subgraph vpsSide [VPS]
        fastapi["FastAPI vps_api.py (/data, /trigger_scan, /debug, /sync_from_discord)"]
        bot["Bot Discord (projeto principal)"]
        dbFile["database.json (sent_news)"]
    end

    subgraph externalServices [ServicosExternos]
        discord["Discord (canal de alertas)"]
        dashboardWeb["Dashboard Web (Node-RED)"]
    end

    ui --> bridge
    bridge -->|GET/POST| fastapi
    fastapi --> dbFile
    bot --> dbFile
    bot --> discord
    ui --> logger
    ui -->|Abre| dashboardWeb
```

### Fluxo do botão NOW (Scanner)

```mermaid
sequenceDiagram
    actor Usuario
    participant UI as DashboardWindows
    participant Bridge as core.bridge
    participant API as FastAPI_VPS
    participant Bot as DiscordBot
    participant JSON as database.json

    Usuario->>UI: Clica em "Executar NOW (Scanner)"
    UI->>Bridge: trigger_scan_now()
    Bridge->>API: POST /trigger_scan
    API-->>Bridge: 200 Accepted
    Bridge-->>UI: True (sucesso)
    UI->>UI: Agenda recargas do feed (45s, 75s)

    API->>Bot: (futuro) Disparar rotina /now
    Bot->>JSON: Grava novas entradas em sent_news

    UI->>Bridge: fetch_data() (após delay)
    Bridge->>API: GET /data
    API->>JSON: Ler sent_news
    API-->>Bridge: JSON com novas vulnerabilidades
    Bridge-->>UI: Lista normalizada
    UI->>UI: Atualiza cards no painel
```

### Fluxos principais

1. **Coleta de inteligência**
   - O bot do Discord consome feeds, calcula CVSS, gera Embeds e salva tudo em `data/database.json` na VPS.
2. **Monitoramento no Windows**
   - O app desktop consome `GET /data` periodicamente (30 em 30 minutos) e exibe os cards no painel.
3. **Varredura manual (NOW)**
   - Botão **🚀 Executar NOW (Scanner)** chama `POST /trigger_scan` na VPS.
   - A VPS registra o pedido (e futuramente aciona o bot para rodar `/now`).
   - Após sucesso, o painel atualiza o feed imediatamente.
4. **Encerramento controlado**
   - Botão **⛔ Encerrar Sistema** abre um diálogo de confirmação (Sim/Não) e encerra todas as threads (UI + tray).

---

## 📂 Estrutura de Pastas (resumida)

```text
cyber_seguranca-installer/
├── main.py               # Entrada do app desktop (Windows)
├── main.spec             # Especificação PyInstaller (gera dist/main.exe)
├── installer_config.iss  # Script Inno Setup (gera dist_installer/CyberBot_Setup.exe)
├── vps_api.py            # API FastAPI na VPS (porta 8000)
├── requirements.txt      # Dependências do projeto
├── run_tests.py          # Entrada para rodar todos os testes (raiz do projeto)
├── assets/
│   ├── icon.ico          # Ícone do app / executável
│   └── icon.png          # Ícone em PNG (fallback)
├── core/
│   ├── bridge.py         # Ponte HTTP: API, sync, NOW, compartilhamento, diagnóstico
│   ├── logger.py         # Logging centralizado (console + arquivos rotativos)
│   ├── exceptions.py     # Exceções do domínio VPS (VPSError, VPSConnectionError, etc.)
│   └── paths.py          # Caminhos dinâmicos: assets, logs (dev vs instalado)
├── ui/
│   └── dashboard.py      # Interface gráfica (CustomTkinter)
├── tests/                # Testes automatizados
│   ├── run_all.py        # Runner que descobre e executa todos os testes
│   ├── test_parse_severity.py
│   ├── test_bridge_fetch_data.py
│   └── TESTES_VALIDACAO.md
└── docs/
    └── ANALISE_FEED_VAZIO.md   # Diagnóstico quando o feed vem vazio
```

---

## 🧩 Componentes Principais

### 1. `vps_api.py` – API de Dados e Comandos

- **Endpoints:**
  - `GET /data`
    - Lê `data/database.json` (gerado pelo bot do Discord);
    - Retorna o JSON completo (incluindo `sent_news[]`);
    - Trata erros de:
      - Arquivo inexistente;
      - JSON corrompido;
      - Permissão de leitura;
      - Erros inesperados (todos logados).
  - `POST /trigger_scan`
    - Ponto único para disparar a varredura manual **NOW**;
    - Atualmente registra o pedido em log e retorna:
      - `{ "status": "accepted", "detail": "..." }`;
    - A integração com o bot do Discord pode ser plugada aqui (chamada da função `/now`).
- **Middleware de logs**:
  - Loga toda requisição (`method`, `path`, `client_ip`, `status`).
- **Eventos de ciclo de vida**:
  - `startup` / `shutdown` logam a subida e parada da API.

### 2. `core/bridge.py` – Ponte Windows ↔ VPS

- **Constantes:**
  - `VPS_IP`, `URL_DADOS_BASE` (GET /data), `URL_DEBUG`, `URL_TRIGGER_SCAN`, `URL_SYNC_DISCORD`, `URL_SYNC_BOT_DIRECT` (fallback porta 8080), `DASHBOARD_URL`.
- **Funções:**
  - `fetch_data()` – consome `GET /data` (com cache-busting e headers anti-cache).
    - Trata: status ≠ 200, JSON inválido, `sent_news` não lista, timeouts e erros de conexão.
    - Quando `sent_news` vem vazio, consulta `/debug` e registra diagnóstico em log.
    - Itens de teste são filtrados em `_filter_test_items` (ex.: "test news", "cve-9999"); em caso de erro retorna card de fallback.
  - `sync_from_discord()` – sincroniza notícias do Discord para o `database.json` (tenta porta 8000, depois 8080).
  - `run_diagnostic()` – chama `/data` e `/debug`, retorna dicionário com status, contagens e preview; em falha de conexão levanta `VPSConnectionError`.
  - `parse_severity(title)` – alinhado ao bot (emoji 🚨 e CVSS):
    - `CRITICAL` – vermelho (#dc3545), ícone 🚨;
    - `HIGH` – laranja (#e67e22), ícone ⚠️;
    - `MEDIUM` – amarelo (#f1c40f), ícone 🔶;
    - `INFO` – verde (#00FF00), ícone ℹ️.
  - `open_url(url)` – abre URLs no navegador padrão.
  - `share_whatsapp(title, link)` – monta `wa.me` e abre no navegador.
  - `share_email(title, description, link)` – monta `mailto:` com assunto e corpo.
  - `trigger_scan_now()` – chama `POST /trigger_scan` na VPS e retorna `True/False`.

### 3. `ui/dashboard.py` – Painel SOC no Windows

- Baseado em **CustomTkinter**:
  - Sidebar com comandos SOC;
  - Área principal com feed de vulnerabilidades;
  - Janela auxiliar para análise de URL (VirusTotal / URLScan);
  - Toasts (popups) de status.

#### Sidebar – Comandos SOC

Cada botão é estilizado com cor e ícone:

| Botão                        | Cor            | Ação                                                                 |
|-----------------------------|----------------|----------------------------------------------------------------------|
| 🔄 **Sincronizar News**     | Azul           | Força a leitura imediata de `GET /data` e recarrega o feed          |
| 📊 **Dashboard Web**        | Azul escuro    | Abre o dashboard Node-RED na VPS (`DASHBOARD_URL`)                  |
| 🧬 **Buscar CVE (NVD)**     | Verde/teal     | Abre a página da CVE digitada no campo (`https://nvd.nist.gov/...`) |
| 🕵️ **Analisar URL (SOC)**  | Laranja        | Abre janela para analisar URL em URLScan + VirusTotal               |
| 🚀 **Executar NOW (Scanner)** | Roxo          | Chama `trigger_scan_now()` → `POST /trigger_scan` → `load_feed()`   |
| ⛔ **Encerrar Sistema**     | Vermelho       | Abre diálogo de confirmação e encerra o app por completo            |

#### Cards no estilo Discord Embed

Cada item de `sent_news[]` é exibido por `create_discord_style_card`:

- Borda colorida pela severidade (`sev_color`).
- Header:
  - Ícone do projeto (a partir de `assets/icon.ico` ou `.png`);
  - Nome do bot: `cyberseguranca_bot`;
  - Badge **APP** (azul Discord);
  - Badge de severidade (CRITICAL/HIGH/MEDIUM/INFO).
- Corpo:
  - Título clicável (abre a fonte/NVD);
  - Descrição da vulnerabilidade (texto truncado, estilo embed).
- Rodapé:
  - Timestamp humanizado (ex: `Hoje às 13:01` se esse formato vier do JSON).
- Barra de ações:
  - 📖 **Leia Mais** – abre o link no navegador;
  - 🟢 **WhatsApp** – abre WhatsApp Web com mensagem pronta;
  - 📩 **E-mail** – abre cliente de e-mail com assunto/corpo preparados.

#### Feedback visual e encerramento

- `show_status(message, variant)` – exibe um **toast**:
  - `variant="success"` – verde;
  - `variant="error"` – vermelho;
  - `variant="info"` – cinza escuro.
  - Usado, por exemplo, após o botão NOW.
- `confirm_quit()`:
  - Abre diálogo `CTkToplevel` com:
    - ✅ **Sim, encerrar**
    - ↩️ **Não, voltar**
  - Em caso de **Sim**:
    - Fecha diálogo, chama `self.quit()` e depois `os._exit(0)` para matar todas as threads (inclusive tray).

### 4. `main.py` – Entrada do App Desktop

- Cria a instância `CyberBotApp`, que:
  - Carrega o `Dashboard`;
  - Configura o ícone de janela (taskbar) via `icon.ico`;
  - Configura o ícone de bandeja (system tray) com **PyStray**:
    - Menu:
      - **Abrir Dashboard**
      - **Sair do SOC** (encerra app e threads).
- Também trata a chamada via protocolo customizado (ex.: `cyberbot://alert/...`):
  - Se `sys.argv[1]` existir, loga `"Aplicação chamada via protocolo customizado: ..."`.

### 5. `core/logger.py` – Logging Centralizado

- Usa **`core.paths.get_logs_dir()`** para o diretório de logs:
  - **Desenvolvimento:** `logs/` na raiz do projeto.
  - **Instalado (PyInstaller):** `%LOCALAPPDATA%\CyberBotGRC\logs` (persistente, não em temp).
- Saídas:
  - Console colorido (ícones e cores por nível, UTF-8 no Windows);
  - Arquivo principal: `cyberbot.log` (DEBUG+, rotação 5 MB, 5 backups);
  - Arquivo de erros: `cyberbot_errors.log` (ERROR+, rotação 2 MB, 3 backups).
- `log_exception(logger, exc, context)` – registra exceção com stack trace e contexto.

### 6. `core/exceptions.py` – Exceções do Domínio VPS

- **`VPSError`** – base para erros da API (message, status_code, detail opcionais).
- **`VPSConnectionError`** – não foi possível conectar (timeout, recusado, DNS).
- **`VPSEmptyResponseError`** – API retornou 200 mas `sent_news` vazio.
- **`VPSInvalidResponseError`** – resposta não é JSON válido ou estrutura inesperada.
- **`VPSSyncError`** – falha ao sincronizar do Discord (sync retornou erro ou timeout).

### 7. `core/paths.py` – Caminhos Dinâmicos

- **`get_base_path()`** – em frozen (PyInstaller) retorna `_MEIPASS`; em dev, raiz do projeto.
- **`get_assets_dir()`** / **`get_icon_path()`** – diretório de assets e caminho do ícone (icon.ico ou icon.png).
- **`get_logs_dir()`** – em frozen usa `%LOCALAPPDATA%\CyberBotGRC\logs`; em dev usa `logs/` na raiz.

---

## 🛠️ Como Rodar (Dev)

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/projeto-cyberseguranca-bot.git
cd projeto-cyberseguranca-bot/cyber_seguranca-installer
```

### 2. Criar e ativar o ambiente virtual (Windows – PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Subir Bot + API na VPS (Linux)

**São necessários dois processos:**

1. **Bot** (porta 8080): `python main.py`
2. **API** (porta 8000): `uvicorn vps_api:app --host 0.0.0.0 --port 8000`

```bash
# Terminal 1 - Bot
cd projeto-cyberseguranca-bot-python
python main.py

# Terminal 2 - API (mesmo diretório)
cd projeto-cyberseguranca-bot-python
uvicorn vps_api:app --host 0.0.0.0 --port 8000
```

> O arquivo `vps_api.py` está no projeto do bot. Use `pip install fastapi uvicorn httpx` se necessário.

### 4. Rodar o Dashboard no Windows

```powershell
cd cyber_seguranca-installer
.venv\Scripts\Activate.ps1  # se ainda não estiver ativo
python main.py
```

---

## 🧪 Testes

### Automatizados (raiz do projeto)

```powershell
cd cyber_seguranca-installer
.venv\Scripts\Activate.ps1
python run_tests.py
```

Ou: `python -m tests.run_all`. Os testes incluem: imports, `parse_severity`, fetch/sync/trigger e diagnóstico (mocks).

### Manuais rápidos

- Com a API ligada e `database.json` válido:
  - Abra o app (`python main.py`);
  - Verifique se:
    - O ícone aparece na barra de título e na bandeja;
    - O feed é carregado sem erros;
    - Botões de ação abrem as URLs corretas.
- Clique em:
  - **🚀 Executar NOW (Scanner)**:
    - Veja no log que o `POST /trigger_scan` foi chamado;
    - Confirme o toast verde de sucesso.
  - **⛔ Encerrar Sistema**:
    - Confirme o diálogo de confirmação;
    - Ao clicar em **Sim**, o app deve fechar por completo.

📋 **[Guia completo de testes e validação](tests/TESTES_VALIDACAO.md)** – Checklist para avaliadores: NOW, System Tray, instalador e classificação de severidade.

📋 **[Análise: feed vazio](docs/ANALISE_FEED_VAZIO.md)** – Diagnóstico quando o painel exibe 0 vulnerabilidades (causas, exceções, `run_diagnostic`).

---

## 📥 Download e instalação (instalador pronto)

Quem quiser **apenas instalar** o painel, sem buildar do código-fonte, pode usar o instalador publicado no repositório:

- **Pasta `dist_installer/`** – contém **`CyberBot_Setup.exe`** (gerado pelo Inno Setup).
- Baixe o instalador, execute e siga o assistente. A instalação cria atalho no Menu Iniciar e opção de **iniciar com o Windows** (autostartup).
- Após a instalação, os logs ficam em **`%LOCALAPPDATA%\CyberBotGRC\logs`**. Configure o IP da VPS no código (ou em configurações, se disponível) e tenha o bot e a API rodando na VPS para o feed funcionar.

> A pasta `dist_installer/` pode estar no histórico do Git ou nas [Releases](https://github.com/pacarminati/cyber_seguranca-installer/releases) do projeto.

---

## 📦 Gerando o Executável e o Instalador

**Pré-requisito:** ambiente virtual ativo no Windows.

### 1. Gerar o executável com PyInstaller (main.spec)

```powershell
cd cyber_seguranca-installer
pyinstaller main.spec
```

- Saída: **`dist/main.exe`** (onefile, sem console, com ícone e assets no bundle).

### 2. Gerar o instalador com Inno Setup

Com **`dist/main.exe`** já gerado, abra **`installer_config.iss`** no Inno Setup e compile, ou use a linha de comando:

```powershell
# Caminho típico do Inno Setup
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_config.iss
```

- Saída: **`dist_installer/CyberBot_Setup.exe`**.
- O instalador copia `dist/main.exe` para `{autopf}\CyberBotGRC` como **CyberBot.exe**, inclui assets, atalho no Menu Iniciar e entrada em **Inicialização automática com o Windows**.

---

## 🔌 (Opcional) Protocolo Customizado `cyberbot://`

Para abrir o app a partir de links no Discord, você pode registrar um protocolo customizado no Windows:

1. Crie um arquivo `cyberbot.reg`:

```reg
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\cyberbot]
@="URL:CyberBot Protocol"
"URL Protocol"=""

[HKEY_CLASSES_ROOT\cyberbot\shell]
[HKEY_CLASSES_ROOT\cyberbot\shell\open]
[HKEY_CLASSES_ROOT\cyberbot\shell\open\command]
@="\"C:\\Caminho\\para\\CyberBot-GRC.exe\" \"%1\""
```

2. Dê duplo clique no `.reg` para importar.
3. No Discord, use links como:
   - `cyberbot://alert/CVE-2025-1234`

O app será aberto e o parâmetro estará em `sys.argv[1]`, já logado no início da execução.

---

## 🤝 Contribuição

1. Abra uma issue com a melhoria ou bug encontrado.
2. Faça um fork do repositório.
3. Crie uma branch descritiva:

```bash
git checkout -b feature/melhoria-logs
```

4. Envie um Pull Request com:
   - Descrição clara da mudança;
   - Prints do dashboard (quando for mudança visual);
   - Referência às issues relacionadas.

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Sinta-se livre para usar, adaptar e evoluir o CyberBot GRC em outros contextos de SOC, estudo ou produção.

