# Scripts de Auto-Aperfeicoamento -- Audiper

## Visao Geral
Sistema de logging e otimizacao automatica de agentes IA do ecossistema Audiper.
Registra o que cada agente faz, aprende com os padroes e otimiza memoria/skills diariamente.

## Scripts

### log_agent_task.py
Registra uma tarefa realizada por qualquer agente. Atualiza `dashboard-data.json` em tempo real.

```bash
python log_agent_task.py \
  --agent "Backend Architect" \
  --sector engineering \
  --task "Implementou endpoint /audit/balance" \
  --status completed \
  --duration 120 \
  --output "FastAPI route com Pydantic v2" \
  --learnings "SQLAlchemy lazy vs eager load" "Pydantic v2 migration"
```

Parametros:
| Parametro | Obrigatorio | Descricao |
|-----------|-------------|-----------|
| --agent | sim | Nome do agente |
| --sector | sim | Setor (engineering, marketing, auditoria, etc.) |
| --task | sim | Descricao da tarefa executada |
| --status | nao | completed / in_progress / failed / skipped (padrao: completed) |
| --duration | nao | Duracao em segundos |
| --output | nao | Resumo do resultado gerado |
| --learnings | nao | Lista de aprendizados (multiplos valores) |
| --quality | nao | Score de qualidade 0-10 (padrao: 8.0) |
| --session | nao | ID da sessao |

---

### daily_aggregate.py
Consolida todos os logs do dia em nota Obsidian e atualiza `dashboard-data.json`.
Deve ser executado diariamente via n8n ou agendador.

```bash
python daily_aggregate.py              # processa hoje
python daily_aggregate.py 2026-03-14   # data especifica
```

Saidas geradas:
- `agents/dashboard-data.json` — atualizado com stats do dia
- `obsidian-vault/research/agentes/daily-agents-YYYY-MM-DD.md` — nota Obsidian

---

### optimize_memory.py
Analisa padroes dos ultimos N dias e gera relatorio com sugestoes de melhoria.

```bash
python optimize_memory.py        # ultimos 7 dias (padrao)
python optimize_memory.py 30     # ultimos 30 dias
```

Saidas geradas:
- `agents/optimization-report.json` — relatorio JSON completo
- Console: resumo com sugestoes priorizadas

Tipos de sugestao gerados:
- `skill_improvement` — setores com qualidade media abaixo de 7.0
- `error_pattern` — agentes com falhas recorrentes
- `memory_consolidation` — consolidacao de aprendizados no Obsidian

---

## Estrutura de Arquivos

```
D:/Site/audiper/
  agents/
    logs/
      YYYY-MM-DD_<sector>.jsonl   <- logs brutos por setor/dia
    registry.json                  <- catalogo de agentes
    dashboard-data.json            <- dados live do Mission Control
    optimization-report.json       <- ultimo relatorio de otimizacao
  scripts/
    log_agent_task.py
    daily_aggregate.py
    optimize_memory.py
    n8n-daily-aggregate-workflow.json
    _pending_hooks/               <- arquivos aguardando instalacao manual
      post_task_log.py            -> copiar para D:/Site/.claude/hooks/
      settings.json               -> merge em D:/Site/.claude/settings.json

D:/Site/obsidian-vault/
  research/agentes/
    daily-agents-YYYY-MM-DD.md    <- notas diarias geradas

D:/Site/.claude/
  hooks/
    post_task_log.py              <- INSTALACAO MANUAL (ver abaixo)
  settings.json                   <- INSTALACAO MANUAL (ver abaixo)
```

---

## Instalacao dos Hooks Claude Code (manual)

Os arquivos em `_pending_hooks/` precisam ser copiados manualmente porque
`D:/Site/.claude/` e protegido contra escrita direta durante sessoes Claude Code.

```bash
# 1. Criar pasta hooks se nao existir
mkdir -p "D:/Site/.claude/hooks"

# 2. Copiar hook
copy "D:/Site/audiper/scripts/_pending_hooks/post_task_log.py" "D:/Site/.claude/hooks/post_task_log.py"

# 3. Criar/atualizar settings.json
#    Se D:/Site/.claude/settings.json JA EXISTIR: adicionar apenas a secao "hooks"
#    Se NAO existir: copiar diretamente
copy "D:/Site/audiper/scripts/_pending_hooks/settings.json" "D:/Site/.claude/settings.json"
```

Depois de instalado, o hook registra automaticamente toda operacao Bash/Write/Edit
do Claude Code no sistema de logs com agent="Claude Code" e sector="orchestration".

---

## Integracao n8n

Importar `n8n-daily-aggregate-workflow.json` no n8n:
1. Abrir n8n (http://localhost:5678)
2. Menu > Import from File
3. Selecionar `n8n-daily-aggregate-workflow.json`
4. Configurar credencial Telegram (ja existente no n8n)
5. Ativar workflow

O workflow executa diariamente as 20h:
- `daily_aggregate.py` — consolida logs do dia
- `optimize_memory.py 7` — analisa ultimos 7 dias
- Envia resumo HTML no Telegram

---

## Exemplos de Uso por Setor

### Auditoria
```bash
python log_agent_task.py --agent "Auditor Fiscal" --sector auditoria \
  --task "Validou SPED ECD bloco J" --status completed \
  --learnings "Conta 1.1.01 requer saldo devedor" "Regime caixa vs competencia"
```

### Marketing
```bash
python log_agent_task.py --agent "Social Media Manager" --sector marketing \
  --task "Criou post LinkedIn sobre NBCT A 265" --status completed \
  --quality 9.0 --duration 45
```

### Engineering
```bash
python log_agent_task.py --agent "Backend Architect" --sector engineering \
  --task "Refatorou modelo SQLAlchemy Empresa" --status completed \
  --learnings "relationship lazy='select' causa N+1" "usar joinedload para relacoes 1:1"
```
