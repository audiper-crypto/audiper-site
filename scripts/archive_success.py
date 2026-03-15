#!/usr/bin/env python
"""
archive_success.py — Arquiva tarefas completadas com sucesso (quality >= 7.5).
Cada entrada arquivada inclui contexto completo, abordagem usada, output e
aprendizados — formando a base de conhecimento para auto-melhoria dos agentes.

Uso:
  # Modo CLI (chamada direta)
  python archive_success.py --log agents/logs/2026-03-15_engineering.jsonl

  # Modo API (importável pelo sistema Agno)
  from scripts.archive_success import archive_task
  archive_task(task_entry, approach="...", context={})

Saída: agents/archive/YYYY-MM-DD_<sector>_<agent-id>_<uuid8>.json
       agents/archive/index.json (atualizado automaticamente)
"""
import argparse, json, uuid, os, hashlib
from datetime import datetime, timezone
from pathlib import Path

ARCHIVE_DIR    = Path("D:/Site/audiper/agents/archive")
INDEX_FILE     = ARCHIVE_DIR / "index.json"
QUALITY_MIN    = 7.5   # score mínimo para arquivar como "golden example"


# ─── Estrutura de um registro arquivado ────────────────────────────────────────
def build_archive_entry(task: dict, approach: str = "", context: dict = None) -> dict:
    """
    Transforma um log de tarefa em um registro de conhecimento arquivado.
    task: dict do JSONL (campos: agent_id, sector, task, status, output_summary,
          learnings, quality_score, timestamp, duration_ms, session_id)
    """
    return {
        # ── Identificação ──
        "archive_id":    str(uuid.uuid4()),
        "archived_at":   datetime.now(timezone.utc).isoformat(),

        # ── Contexto da tarefa ──
        "agent_id":      task.get("agent_id", "unknown"),
        "agent_name":    task.get("agent_name", task.get("agent_id", "unknown")),
        "sector":        task.get("sector", "unknown"),
        "task":          task.get("task", ""),
        "status":        task.get("status", "completed"),
        "quality_score": task.get("quality_score", 8.0),
        "duration_ms":   task.get("duration_ms", 0),
        "session_id":    task.get("session_id", ""),
        "original_ts":   task.get("timestamp", ""),

        # ── Conhecimento extraído ──
        "output_summary": task.get("output_summary", ""),
        "approach_used":  approach or task.get("approach", ""),
        "learnings":      task.get("learnings", []),

        # ── Contexto adicional (injeção externa) ──
        "context":       context or {},

        # ── Uso futuro: tags para busca semântica ──
        "tags": _extract_tags(task),

        # ── Hash de deduplicação ──
        "content_hash": _hash_task(task),
    }


def _extract_tags(task: dict) -> list:
    """Extrai tags relevantes da tarefa para facilitar busca posterior."""
    tags = [task.get("sector", ""), task.get("agent_id", "")]
    task_text = task.get("task", "").lower()

    keyword_map = {
        "api": ["api", "endpoint", "fastapi", "rest"],
        "database": ["sqlite", "sql", "banco", "query", "db"],
        "audit": ["auditoria", "nbc", "pta", "evidência", "achado"],
        "test": ["teste", "test", "pytest", "qa"],
        "deploy": ["deploy", "servidor", "docker", "nginx"],
        "memory": ["memória", "memory", "contexto", "vector", "embedding"],
        "agno": ["agno", "team", "agent", "llm"],
        "n8n": ["n8n", "workflow", "automação", "trigger"],
    }
    for tag, keywords in keyword_map.items():
        if any(kw in task_text for kw in keywords):
            tags.append(tag)

    for learning in task.get("learnings", []):
        if isinstance(learning, str) and len(learning) > 5:
            tags.append(learning.split()[0].lower().rstrip(":.,"))

    return list(set(t for t in tags if t))


def _hash_task(task: dict) -> str:
    """Hash para evitar duplicatas (mesmo agente + mesma tarefa)."""
    key = f"{task.get('agent_id','')}|{task.get('task','')}|{task.get('timestamp','')}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


# ─── Persistência ──────────────────────────────────────────────────────────────
def save_archive(entry: dict) -> Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    fname    = f"{date_str}_{entry['sector']}_{entry['agent_id']}_{entry['archive_id'][:8]}.json"
    fpath    = ARCHIVE_DIR / fname
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)
    return fpath


def update_index(entry: dict, fpath: Path):
    """Mantém index.json com metadados de todos os archives (sem o conteúdo completo)."""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"version": "1.0", "total": 0, "entries": []}

    # Verifica duplicata por hash
    existing_hashes = {e.get("content_hash") for e in index.get("entries", [])}
    if entry["content_hash"] in existing_hashes:
        print(f"[SKIP] Duplicata detectada: {entry['content_hash']}")
        return

    index["entries"].append({
        "archive_id":    entry["archive_id"],
        "agent_id":      entry["agent_id"],
        "sector":        entry["sector"],
        "task":          entry["task"][:80],
        "quality_score": entry["quality_score"],
        "tags":          entry["tags"],
        "content_hash":  entry["content_hash"],
        "archived_at":   entry["archived_at"],
        "file":          fpath.name,
    })
    index["total"] = len(index["entries"])
    index["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


# ─── API pública ───────────────────────────────────────────────────────────────
def archive_task(task: dict, approach: str = "", context: dict = None) -> dict | None:
    """
    Arquiva uma tarefa se quality_score >= QUALITY_MIN e status == 'completed'.
    Retorna o entry arquivado ou None se ignorado.
    """
    if task.get("status") != "completed":
        return None
    if float(task.get("quality_score", 0)) < QUALITY_MIN:
        return None

    entry = build_archive_entry(task, approach, context)
    fpath = save_archive(entry)
    update_index(entry, fpath)
    print(f"[ARCHIVE] {entry['agent_name']} -> {entry['task'][:60]} (q={entry['quality_score']}) -> {fpath.name}")
    return entry


# ─── Modo CLI: processa arquivo JSONL ─────────────────────────────────────────
def process_jsonl(log_path: str) -> int:
    archived = 0
    skipped  = 0
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                task = json.loads(line)
            except json.JSONDecodeError:
                continue
            result = archive_task(task)
            if result:
                archived += 1
            else:
                skipped += 1
    print(f"[DONE] Arquivadas: {archived} | Ignoradas (baixa qualidade/falha): {skipped}")
    return archived


def main():
    parser = argparse.ArgumentParser(description="Arquiva tarefas de sucesso")
    parser.add_argument("--log",   help="Arquivo JSONL de logs para processar")
    parser.add_argument("--all",   action="store_true",
                        help="Processa todos os logs do dia atual")
    parser.add_argument("--date",  default="",
                        help="Data no formato YYYY-MM-DD (default: hoje)")
    args = parser.parse_args()

    logs_dir = Path("D:/Site/audiper/agents/logs")
    today    = args.date or datetime.now().strftime("%Y-%m-%d")

    if args.log:
        process_jsonl(args.log)
    elif args.all:
        log_files = list(logs_dir.glob(f"{today}_*.jsonl"))
        if not log_files:
            print(f"[WARN] Nenhum log encontrado para {today}")
            return
        total = 0
        for lf in log_files:
            print(f"\n--- {lf.name} ---")
            total += process_jsonl(str(lf))
        print(f"\n[TOTAL] {total} tarefas arquivadas hoje")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
