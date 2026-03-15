#!/usr/bin/env python
"""
build_knowledge.py — Extrai padrões e conhecimento acumulado dos archives.

Lê todos os archives de success e agrupa por setor e agente para produzir:
  - agents/knowledge/<sector>_patterns.json  → padrões de abordagem por setor
  - agents/knowledge/agent_<id>_profile.json → perfil de excelência por agente
  - agents/knowledge/global_patterns.json    → top learnings cross-sector

Esses arquivos são injetados nos prompts dos agentes Agno como "knowledge"
e usados pelo generate_briefing.py para criar o briefing matinal.

Uso:
  python build_knowledge.py            # processa todos os archives
  python build_knowledge.py --sector engineering  # só um setor
  python build_knowledge.py --days 7   # últimos N dias
"""
import argparse, json, os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict, Counter

ARCHIVE_DIR    = Path("D:/Site/audiper/agents/archive")
INDEX_FILE     = ARCHIVE_DIR / "index.json"
KNOWLEDGE_DIR  = Path("D:/Site/audiper/agents/knowledge")


# ─── Carregamento ──────────────────────────────────────────────────────────────
def load_archives(sector_filter: str = "", days: int = 0) -> list:
    """Carrega todos os archives (ou filtrado por setor/dias)."""
    if not INDEX_FILE.exists():
        return []
    with open(INDEX_FILE, encoding="utf-8") as f:
        index = json.load(f)

    cutoff = None
    if days > 0:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    entries = []
    for meta in index.get("entries", []):
        if sector_filter and meta.get("sector") != sector_filter:
            continue
        if cutoff and meta.get("archived_at", "") < cutoff:
            continue
        fpath = ARCHIVE_DIR / meta["file"]
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                entries.append(json.load(f))
    return entries


# ─── Análise por setor ─────────────────────────────────────────────────────────
def build_sector_patterns(archives: list) -> dict:
    """
    Para um conjunto de archives (mesmo setor), extrai:
    - top_tasks: tarefas mais realizadas com sucesso
    - top_learnings: aprendizados mais recorrentes
    - top_agents: agentes com mais sucesso
    - avg_quality: qualidade média
    - approach_patterns: abordagens que funcionaram
    """
    if not archives:
        return {}

    sector    = archives[0].get("sector", "unknown")
    all_tags  = Counter()
    all_learn = Counter()
    agents    = defaultdict(lambda: {"tasks": 0, "total_quality": 0.0, "learnings": []})
    task_types = Counter()

    for a in archives:
        for tag in a.get("tags", []):
            all_tags[tag] += 1
        for l in a.get("learnings", []):
            if isinstance(l, str) and len(l) > 8:
                all_learn[l.strip()] += 1
        ag_id = a.get("agent_id", "unknown")
        agents[ag_id]["tasks"] += 1
        agents[ag_id]["total_quality"] += a.get("quality_score", 8.0)
        agents[ag_id]["agent_name"] = a.get("agent_name", ag_id)
        agents[ag_id]["learnings"].extend(a.get("learnings", []))

        # Classifica tipo de tarefa pela primeira palavra-chave
        task_words = a.get("task", "").lower().split()
        if task_words:
            task_types[task_words[0]] += 1

    avg_quality = sum(a.get("quality_score", 8.0) for a in archives) / len(archives)

    top_agents = []
    for aid, data in sorted(agents.items(),
                            key=lambda x: x[1]["total_quality"] / max(x[1]["tasks"], 1),
                            reverse=True)[:5]:
        top_agents.append({
            "agent_id":    aid,
            "agent_name":  data["agent_name"],
            "tasks":       data["tasks"],
            "avg_quality": round(data["total_quality"] / max(data["tasks"], 1), 2),
        })

    return {
        "sector":          sector,
        "total_archives":  len(archives),
        "avg_quality":     round(avg_quality, 2),
        "updated_at":      datetime.now(timezone.utc).isoformat(),
        "top_agents":      top_agents,
        "top_learnings":   [l for l, _ in all_learn.most_common(15) if l],
        "top_task_types":  [t for t, _ in task_types.most_common(10)],
        "top_tags":        [t for t, _ in all_tags.most_common(10) if t not in ("", sector)],
        "recent_successes": [
            {
                "agent":   a.get("agent_name", a.get("agent_id")),
                "task":    a.get("task", "")[:100],
                "quality": a.get("quality_score"),
                "key_learning": a.get("learnings", [""])[0] if a.get("learnings") else "",
            }
            for a in sorted(archives, key=lambda x: x.get("quality_score", 0), reverse=True)[:5]
        ],
    }


# ─── Perfil por agente ─────────────────────────────────────────────────────────
def build_agent_profile(archives: list, agent_id: str) -> dict:
    """Perfil de excelência de um agente específico."""
    agent_archives = [a for a in archives if a.get("agent_id") == agent_id]
    if not agent_archives:
        return {}

    all_learnings = []
    all_approaches = []
    task_history = []

    for a in sorted(agent_archives, key=lambda x: x.get("archived_at", ""), reverse=True):
        all_learnings.extend(a.get("learnings", []))
        if a.get("approach_used"):
            all_approaches.append(a["approach_used"])
        task_history.append({
            "task":    a.get("task", "")[:80],
            "quality": a.get("quality_score"),
            "date":    a.get("archived_at", "")[:10],
            "tags":    a.get("tags", [])[:4],
        })

    # Deduplica learnings mantendo mais frequentes
    learn_counts = Counter(l.strip() for l in all_learnings if isinstance(l, str) and l.strip())
    avg_quality  = sum(a.get("quality_score", 0) for a in agent_archives) / len(agent_archives)

    return {
        "agent_id":       agent_id,
        "agent_name":     agent_archives[0].get("agent_name", agent_id),
        "sector":         agent_archives[0].get("sector", "unknown"),
        "total_successes": len(agent_archives),
        "avg_quality":    round(avg_quality, 2),
        "updated_at":     datetime.now(timezone.utc).isoformat(),
        "core_learnings": [l for l, _ in learn_counts.most_common(10)],
        "best_approaches": list(set(all_approaches))[:5],
        "task_history":   task_history[:20],
        "strengths":      _infer_strengths(agent_archives),
    }


def _infer_strengths(archives: list) -> list:
    """Infere pontos fortes do agente com base nas tags das tarefas bem avaliadas."""
    top = [a for a in archives if a.get("quality_score", 0) >= 9.0]
    tag_counter = Counter()
    for a in top:
        for tag in a.get("tags", []):
            tag_counter[tag] += 1
    return [t for t, _ in tag_counter.most_common(5) if t]


# ─── Padrões globais ───────────────────────────────────────────────────────────
def build_global_patterns(all_archives: list) -> dict:
    """Cross-sector: top learnings, melhores agentes, tendências."""
    if not all_archives:
        return {}

    learn_counter  = Counter()
    sector_quality = defaultdict(list)
    agent_scores   = defaultdict(list)

    for a in all_archives:
        for l in a.get("learnings", []):
            if isinstance(l, str) and l.strip():
                learn_counter[l.strip()] += 1
        sector_quality[a.get("sector", "unknown")].append(a.get("quality_score", 8.0))
        agent_scores[a.get("agent_id", "unknown")].append(a.get("quality_score", 8.0))

    sector_avgs = {
        s: round(sum(scores) / len(scores), 2)
        for s, scores in sector_quality.items()
    }

    top_agents = sorted(
        [
            {"agent_id": aid, "avg": round(sum(scores)/len(scores), 2), "count": len(scores)}
            for aid, scores in agent_scores.items() if len(scores) >= 2
        ],
        key=lambda x: x["avg"],
        reverse=True,
    )[:10]

    return {
        "total_archives":   len(all_archives),
        "updated_at":       datetime.now(timezone.utc).isoformat(),
        "top_learnings":    [l for l, _ in learn_counter.most_common(20)],
        "sector_quality":   sector_avgs,
        "top_agents":       top_agents,
        "best_sector":      max(sector_avgs, key=sector_avgs.get) if sector_avgs else "",
    }


# ─── Persistência ──────────────────────────────────────────────────────────────
def save_knowledge(data: dict, fname: str):
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    fpath = KNOWLEDGE_DIR / fname
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[KNOWLEDGE] Salvo: {fpath.name} ({data.get('total_archives', data.get('total_successes', '?'))} items)")


# ─── Orquestrador ─────────────────────────────────────────────────────────────
def run(sector_filter: str = "", days: int = 0):
    print(f"[BUILD] Carregando archives (setor={sector_filter or 'todos'}, dias={days or 'todos'})...")
    archives = load_archives(sector_filter, days)
    if not archives:
        print("[WARN] Nenhum archive encontrado. Execute archive_success.py primeiro.")
        return

    print(f"[BUILD] {len(archives)} archives carregados")

    # ── Padrões por setor ──
    sectors = set(a.get("sector") for a in archives)
    for sector in sectors:
        sector_archives = [a for a in archives if a.get("sector") == sector]
        patterns = build_sector_patterns(sector_archives)
        if patterns:
            save_knowledge(patterns, f"{sector}_patterns.json")

    # ── Perfis por agente ──
    agents = set(a.get("agent_id") for a in archives)
    for agent_id in agents:
        profile = build_agent_profile(archives, agent_id)
        if profile and profile.get("total_successes", 0) >= 2:
            save_knowledge(profile, f"agent_{agent_id}_profile.json")

    # ── Padrões globais ──
    if not sector_filter:
        global_patterns = build_global_patterns(archives)
        save_knowledge(global_patterns, "global_patterns.json")

    print(f"[BUILD] Concluido. Arquivos em {KNOWLEDGE_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="Extrai padrões de conhecimento dos archives")
    parser.add_argument("--sector", default="", help="Filtrar por setor")
    parser.add_argument("--days",   type=int, default=0, help="Últimos N dias")
    args = parser.parse_args()
    run(args.sector, args.days)


if __name__ == "__main__":
    main()
