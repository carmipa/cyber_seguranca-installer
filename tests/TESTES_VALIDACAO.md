# 🛡️ Guia de Testes e Validação – CyberBot GRC

Este documento descreve os testes necessários para validar o funcionamento do ecossistema SOC e atender aos critérios de avaliação (ex.: FIAP).

---

## 1. Teste de Sincronização e Gatilho (NOW)

**Objetivo:** Comprovar que o botão dispara o motor de varredura na nuvem em tempo real.

### Ação

1. Abra o Dashboard do CyberBot GRC no Windows.
2. Clique no botão **🚀 Executar NOW (Scanner)** na sidebar.

### Validação

- **No terminal da VPS** (via `journalctl -f` ou logs da API):
  - Verifique se a requisição `POST /trigger_scan` foi recebida.
  - Confirme que o status retornado foi **200**.
- **No Dashboard Windows:**
  - Deve aparecer um toast verde: *"Varredura iniciada na VPS com sucesso!"*
  - Em caso de falha, toast vermelho: *"Falha ao iniciar varredura na VPS. Verifique os logs."*

### Resultado esperado

- Após alguns segundos, clique em **🔄 Sincronizar News**.
- Novos alertas (diferentes do "Test News CVE-9999") devem aparecer no feed, se o bot tiver gerado novas vulnerabilidades.

### Comandos úteis (VPS)

```bash
# Acompanhar logs da API em tempo real
journalctl -f -u cyberbot-api   # ou o nome do seu serviço

# Verificar se o serviço está rodando
systemctl status cyberbot-api
```

---

## 2. Teste de Persistência e System Tray

**Objetivo:** Validar se o SOC continua operacional quando a janela principal é fechada.

### Ação

1. Com o CyberBot GRC aberto, **minimize** a janela (botão `-` na barra de título).
2. Ou clique no **X** (fechar) da janela principal.

### Validação

- A janela deve **desaparecer da barra de tarefas**.
- O ícone do **CyberBot** deve permanecer visível na **barra de notificações** (system tray), próximo ao relógio.

### Resultado esperado

1. Clique com o **botão direito** no ícone da bandeja.
2. Selecione **"Abrir Dashboard"** (ou "Abrir Painel GRC").
3. A janela principal deve ser restaurada, confirmando que a aplicação **não foi encerrada** e continua em segundo plano.

---

## 3. Teste de GRC e Distribuição (Instalador)

**Objetivo:** Comprovar que o software segue padrões profissionais de entrega e licenciamento.

### Ação

1. Execute o arquivo **CyberBot_Setup.exe** gerado pelo Inno Setup (ou PyInstaller).
2. Siga o assistente de instalação (Next → Next → Finish).

### Validação

- Durante a instalação, verifique se:
  - A **Licença MIT** é exibida corretamente.
  - Os links do **GitHub** do projeto aparecem quando aplicável.
  - A opção de **iniciar com o Windows** (`{autostartup}`) está disponível, se configurada.

### Resultado esperado

- Após a instalação, **reinicie o computador**.
- Se o autostartup estiver configurado, o CyberBot deve **iniciar automaticamente** com o Windows e aparecer na bandeja do sistema.

---

## 4. Teste de Classificação de Severidade

**Objetivo:** Validar se o parsing extrai o risco corretamente do título enviado pelo bot.

### Ação

1. Observe as **cores das bordas** nos cards de vulnerabilidade no feed.
2. Verifique as **tags de severidade** (CRITICAL, HIGH, MEDIUM, INFO) em cada card.

### Validação

| Condição no título | Tag esperada | Cor da borda | Ícone |
|--------------------|--------------|--------------|-------|
| Emoji 🚨 presente  | CRITICAL     | Vermelho (#dc3545) | 🚨 |
| CVSS ≥ 9.0         | CRITICAL     | Vermelho (#dc3545) | 🚨 |
| CVSS ≥ 7.0         | HIGH         | Laranja (#e67e22)  | ⚠️ |
| CVSS ≥ 4.0         | MEDIUM       | Amarelo (#f1c40f)  | 🔶 |
| Demais casos       | INFO         | Verde (#00FF00)    | ℹ️ |

### Resultado esperado

- Alertas com **🚨** ou **CVSS ≥ 9.0** devem exibir a tag **CRITICAL** com borda vermelha (#dc3545).
- HIGH (laranja), MEDIUM (amarelo) e INFO (verde) conforme o CVSS no título; sem CVSS ou CVSS &lt; 4.0 = INFO.

---

## 🛡️ Checklist Técnico para o Avaliador

| Requisito | Validação esperada |
|-----------|--------------------|
| **Conectividade** | API na porta 8000 da VPS deve estar `active`/`running`. |
| **UX/UI** | Botões de compartilhamento (📖 Leia Mais, 🟢 WhatsApp, 📩 E-mail) devem abrir o link da CVE ou o cliente correto. |
| **Segurança** | O arquivo `database.json` não deve conter dados sensíveis, apenas o feed público de vulnerabilidades. |
| **Logs e auditoria** | Ações (NOW, Sincronizar, Encerrar) devem ser registradas em `logs/cyberbot.log`. |
| **Encerramento controlado** | O botão "Encerrar Sistema" deve exibir confirmação (Sim/Não) antes de finalizar. |
| **System Tray** | O app deve minimizar para a bandeja ao fechar ou minimizar a janela. |

---

## 🧪 Testes Automatizados (pasta `tests/`)

Execute a partir da **raiz do projeto** (`cyber_seguranca-installer/`), com o venv ativo:

```powershell
cd cyber_seguranca-installer
.venv\Scripts\Activate.ps1
python run_tests.py
```

Alternativa: `python -m tests.run_all` (com a raiz no `sys.path`).

### Estrutura da pasta `tests/`

| Arquivo | Descrição |
|---------|-----------|
| `run_tests.py` (raiz) | Ponto de entrada; delega para `tests/run_all.py` |
| `run_all.py` | Runner que descobre e executa todos os testes |
| `test_imports.py` | Verifica imports e estrutura dos módulos |
| `test_parse_severity.py` | Teste 4 – Classificação de severidade (🚨, CVSS, cores/ícones) |
| `test_bridge_fetch_data.py` | fetch_data, sync_from_discord, run_diagnostic (mocks) |
| `test_sync_and_trigger.py` | GET /data e POST /trigger_scan |

---

## 📋 Resumo Rápido

1. **NOW** → Clique no botão → Verifique POST na VPS → Sincronize e confira novos alertas.
2. **Tray** → Minimize ou feche → Ícone na bandeja → Clique direito → "Abrir Dashboard".
3. **Instalador** → Execute o .exe → Verifique licença e links → Reinicie e confira autostart (se houver).
4. **Severidade** → Observe bordas e tags → CRITICAL (preto), HIGH (vermelho), MEDIUM (amarelo), INFO (verde).
