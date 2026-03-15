#!/usr/bin/env python
"""
inject_memory.py — Prepara e injeta memórias nos agentes Agno via MemoryV2.

Fluxo:
  1. Lê archives de sucesso do período
  2. Formata como entradas compatíveis com Agno AgentMemory (SqliteMemoryDb)
  3. Injeta diretamente na tabela SQLite que o Agno usa
  4. Os agentes automaticamente buscam essa memória ao executar novas tarefas

Por que direto no SQLite:
  - Agno MemoryV2 usa SqliteMemoryDb: tabela `agent_memory` no DB especificado
  - Injetar externamente permite "seed" de conhecimento sem precisar rodar o agente
  - Na inicialização, o agente faz `memory.search(query)` que retorna as entradas injetadas

Uso:
  python inject_memory.py                     # injeta últimos 7 dias
  python inject_memory.py --agent backend-architect
  python inject_memory.py --sector engineering
  python inject_memory.py --days 30 --dry-run
"""
import argparse, json, sqlite3, uuid, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

ARCHIVE_DIR  = Path("D:/Site/audiper/agents/archive")
KNOWLEDGE_DIR = Path("D:/Site/audiper/agents/knowledge")
MEMORY_DIR   = Path("D:/Site/audiper/agents/memory")

# Agno MemoryV2 usa este path por padrão (configurável em .env)
AGNO_DB_PATH = Path("D:/Site/agno/data/agno.db")


# ─── Compatibilidade com Agno MemoryV2 ────────────────────────────────────────
# Agno SqliteMemoryDb cria tabela: agent_memory(id TEXT, memory TEXT, created_at INTEGER)
# Opcionalmente: agent_id TEXT para filtrar por agente
# MemoryV2 entry format: {"memory": "texto livre", "topics": ["tag1", "tag2"]}

def format_as_agno_memory(archive: dict) -> dict:
    """
    Formata um archive como entrada de memória Agno MemoryV2.
    O campo `memory` é o texto livre que o agente irá buscar semanticamente.
    """
    learnings_text = ""
    if archive.get("learnings"):
        learnings_text = " | ".join(str(l) for l in archive["learnings"][:5])

    memory_text = (
        f"Tarefa bem-sucedida: {archive.get('task', '')}. "
        f"Agente: {archive.get('agent_name', archive.get('agent_id', ''))} ({archive.get('sector', '')}). "
    )
    if archive.get("output_summary"):
        memory_text += f"Output: {archive['output_summary'][:200]}. "
    if archive.get("approach_used"):
        memory_text += f"Abordagem: {archive['approach_used'][:200]}. "
    if learnings_text:
        memory_text += f"Aprendizados: {learnings_text}."

    return {
        "id":         _memory_id(archive),
        "agent_id":   archive.get("agent_id", "global"),
        "memory":     memory_text.strip(),
        "topics":     json.dumps(archive.get("tags", []), ensure_ascii=False),
        "quality":    archive.get("quality_score", 8.0),
        "source":     "archive",
        "archive_id": archive.get("archive_id", ""),
        "created_at": int(datetime.now(timezone.utc).timestamp()),
    }


def _memory_id(archive: dict) -> str:
    """ID determinístico baseado no archive_id para evitar duplicatas."""
    key = archive.get("archive_id", "") or archive.get("content_hash", str(uuid.uuid4()))
    return hashlib.md5(f"mem_{key}".encode()).hexdigest()


# ─── SQLite local (per-agent memory cache) ───────────────────────────────────
def init_local_db(agent_id: str) -> sqlite3.Connection:
    """Cria/abre DB local de memória por agente (fallback quando Agno não está rodando)."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    db_path = MEMORY_DIR / f"{agent_id}_memory.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_memory (
            id TEXT PRIMARY KEY,
            agent_id TEXT,
            memory TEXT NOT NULL,
            topics TEXT,
            quality REAL DEFAULT 8.0,
            source TEXT DEFAULT 'archive',
            archive_id TEXT,
            created_at INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agent ON agent_memory(agent_id)")
    conn.commit()
    return conn


def inject_into_local_db(memories: list, agent_id: str, dry_run: bool = False) -> int:
    """Injeta memórias no DB local do agente."""
    conn = init_local_db(agent_id)
    injected = 0
    skipped  = 0
    for mem in memories:
        try:
            if not dry_run:
                conn.execute(
                    """INSERT OR IGNORE INTO agent_memory
                       (id, agent_id, memory, topics, quality, source, archive_id, created_at)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (mem["id"], mem["agent_id"], mem["memory"], mem["topics"],
                     mem["quality"], mem["source"], mem["archive_id"], mem["created_at"])
                )
            injected += 1
        except sqlite3.IntegrityError:
            skipped += 1
    if not dry_run:
        conn.commit()
    conn.close()
    return injected


def inject_into_agno_db(memories: list, dry_run: bool = False) -> int:
    """
    Injeta memórias no banco Agno principal (agno.db).
    Só executa se o DB existir (Agno já foi inicializado).
    """
    if not AGNO_DB_PATH.exists():
        print(f"[SKIP] Agno DB não encontrado em {AGNO_DB_PATH}. Use --local para forçar DB local.")
        return 0

    conn = sqlite3.connect(str(AGNO_DB_PATH))

    # Agno MemoryV2 cria tabela automaticamente — verifica existência
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "agent_memory" not in tables:
        print("[SKIP] Tabela agent_memory não existe no Agno DB. Execute o Agno pelo menos uma vez.")
        conn.close()
        return 0

    injected = 0
    for mem in memories:
        try:
            if not dry_run:
                conn.execute(
                    "INSERT OR IGNORE INTO agent_memory (id, memory, created_at) VALUES (?,?,?)",
                    (mem["id"], mem["memory"], mem["created_at"])
                )
            injected += 1
        except Exception as e:
            print(f"[WARN] {e}")
    if not dry_run:
        conn.commit()
    conn.close()
    return injected


# ─── Exportação JSON (para injeção via Agno Python API) ───────────────────────
def export_memory_json(memories: list, agent_id: str):
    """
    Exporta memórias como JSON para injeção programática via Agno Python API:
      from agno.memory.v2 import Memory
      memory = Memory(db=SqliteMemoryDb(table_name="agent_memory", db_file=...))
      # O arquivo exportado aqui é lido pelo agno/apex/agent.py na inicialização
    """
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    out = MEMORY_DIR / f"{agent_id}_seed.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"agent_id": agent_id, "memories": memories, "count": len(memories),
                   "exported_at": datetime.now(timezone.utc).isoformat()},
                  f, indent=2, ensure_ascii=False)
    print(f"[EXPORT] {out.name} ({len(memories)} memórias)")


# ─── Carregamento de archives ─────────────────────────────────────────────────
def load_archives(agent_filter: str, sector_filter: str, days: int) -> list:
    index_file = ARCHIVE_DIR / "index.json"
    if not index_file.exists():
        return []
    with open(index_file, encoding="utf-8") as f:
        index = json.load(f)

    cutoff = None
    if days > 0:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    archives = []
    for meta in index.get("entries", []):
        if agent_filter and meta.get("agent_id") != agent_filter:
            continue
        if sector_filter and meta.get("sector") != sector_filter:
            continue
        if cutoff and meta.get("archived_at", "") < cutoff:
            continue
        fpath = ARCHIVE_DIR / meta["file"]
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                archives.append(json.load(f))
    return archives


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Injeta archives como memória Agno MemoryV2")
    parser.add_argument("--agent",   default="", help="Filtrar por agent_id")
    parser.add_argument("--sector",  default="", help="Filtrar por setor")
    parser.add_argument("--days",    type=int, default=7, help="Últimos N dias")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem escrever")
    parser.add_argument("--local",   action="store_true",
                        help="Usar DB local por agente (não requer Agno rodando)")
    parser.add_argument("--export",  action="store_true",
                        help="Exportar JSON para injeção via Agno Python API")
    args = parser.parse_args()

    print(f"[INJECT] Carregando archives (agent={args.agent or 'todos'}, "
          f"sector={args.sector or 'todos'}, dias={args.days})...")

    archives = load_archives(args.agent, args.sector, args.days)
    if not archives:
        print("[WARN] Nenhum archive encontrado.")
        return

    print(f"[INJECT] {len(archives)} archives carregados")
    memories = [format_as_agno_memory(a) for a in archives]

    if args.dry_run:
        print(f"[DRY-RUN] {len(memories)} memórias seriam injetadas:")
        for m in memories[:3]:
            print(f"  [{m['agent_id']}] {m['memory'][:100]}...")
        return

    if args.export:
        agent_id = args.agent or "global"
        export_memory_json(memories, agent_id)
        return

    if args.local:
        # Agrupa por agent_id e injeta em DBs separados
        from collections import defaultdict
        by_agent = defaultdict(list)
        for mem in memories:
            by_agent[mem["agent_id"]].append(mem)
        for agent_id, agent_mems in by_agent.items():
            n = inject_into_local_db(agent_mems, agent_id)
            print(f"[LOCAL DB] {agent_id}: {n} memórias injetadas")
    else:
        n = inject_into_agno_db(memories)
        print(f"[AGNO DB] {n} memórias injetadas em {AGNO_DB_PATH}")

    # Sempre exporta JSON também (para uso programático)
    export_memory_json(memories, args.agent or "global")

    print(f"[DONE] {len(memories)} memórias processadas")


if __name__ == "__main__":
    main()
