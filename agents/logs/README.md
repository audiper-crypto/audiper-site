# Logs de Execução de Agentes

Esta pasta armazena os logs de execução de todos os agentes do ecossistema Audiper.

## Nomenclatura dos Arquivos

```
YYYY-MM-DD_<sector>_<agent-id>.jsonl
```

**Exemplos:**
- `2026-03-15_auditoria_fase-b-planejamento.jsonl`
- `2026-03-15_engineering_backend-architect.jsonl`
- `2026-03-15_orchestration_master-orchestrator.jsonl`

## Formato

Cada arquivo é um **JSONL** (JSON Lines) — uma entrada de log por linha, sem separadores.
Cada linha segue o schema definido em `../schema/log-entry.json`.

**Exemplo de linha:**
```json
{"id":"550e8400-e29b-41d4-a716-446655440000","agent_id":"backend-architect","sector":"engineering","timestamp":"2026-03-15T10:30:00Z","task":"Implementar endpoint de listagem de auditorias","status":"completed","duration_ms":4200,"input_summary":"Requisito de paginação com filtros por status e setor","output_summary":"Endpoint GET /auditorias implementado com paginação, filtros e documentação OpenAPI","learnings":["SQLAlchemy lazy loading inadequado para listagens grandes - usar joinedload"],"memory_updates":["notas-tecnicas.md: SQLAlchemy performance tip"],"skill_updates":[],"quality_score":9.2,"session_id":"session-abc-123"}
```

## Campos Principais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único da entrada |
| `agent_id` | string | ID do agente (kebab-case) |
| `sector` | string | Setor do agente |
| `timestamp` | ISO 8601 | Momento de início da execução |
| `task` | string | Descrição da tarefa realizada |
| `status` | enum | `completed`, `in_progress`, `failed`, `skipped` |
| `duration_ms` | int | Duração em milissegundos |
| `input_summary` | string | Resumo dos dados de entrada |
| `output_summary` | string | Resumo do entregável produzido |
| `learnings` | array | Aprendizados extraídos |
| `memory_updates` | array | Arquivos de memória atualizados |
| `skill_updates` | array | Skills criadas ou atualizadas |
| `quality_score` | float 0-10 | Qualidade do output |
| `session_id` | string | ID da sessão Claude Code ou n8n |

## Como Analisar os Logs

### Python — leitura básica
```python
import json
from pathlib import Path

log_file = Path("2026-03-15_auditoria_fase-b-planejamento.jsonl")
entries = [json.loads(line) for line in log_file.read_text().splitlines() if line.strip()]

# Filtrar por status
completed = [e for e in entries if e["status"] == "completed"]
failed = [e for e in entries if e["status"] == "failed"]

# Calcular score médio
avg_quality = sum(e.get("quality_score", 0) for e in completed) / len(completed)
```

### Agregar todos os logs do dia
```python
import json
from pathlib import Path

logs_dir = Path(".")
today = "2026-03-15"

all_entries = []
for f in logs_dir.glob(f"{today}_*.jsonl"):
    all_entries += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]

# Agrupar por setor
from collections import defaultdict
by_sector = defaultdict(list)
for e in all_entries:
    by_sector[e["sector"]].append(e)
```

### Extrair aprendizados do dia
```python
learnings = []
for entry in all_entries:
    for learning in entry.get("learnings", []):
        learnings.append({"agent": entry["agent_id"], "learning": learning})
```

## Retenção

- Logs individuais: mantidos por **90 dias**
- Consolidados mensais: mantidos por **1 ano**
- Após retenção: arquivar em `../logs/archive/`

## Integração com Obsidian

O agente `memory-manager` processa os logs diariamente às 20h00 e consolida os aprendizados no Obsidian Vault em `D:/Site/obsidian-vault/pesquisa/`.
