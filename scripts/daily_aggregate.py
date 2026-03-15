#!/usr/bin/env python
"""
daily_aggregate.py — Agrega logs do dia, gera resumo para Obsidian e Mission Control.
Uso: python daily_aggregate.py [--date YYYY-MM-DD]
     python daily_aggregate.py 2026-03-14
"""
import json, sys, os
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

LOG_DIR      = Path("D:/Site/audiper/agents/logs")
DASHBOARD    = Path("D:/Site/audiper/agents/dashboard-data.json")
OBSIDIAN_DIR = Path("D:/Site/obsidian-vault/research")
REGISTRY     = Path("D:/Site/audiper/agents/registry.json")


def load_day_logs(target_date: str) -> list:
    entries = []
    for f in LOG_DIR.glob(f"{target_date}_*.jsonl"):
        with open(f, encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    return entries


def aggregate(entries: list) -> dict:
    by_sector     = defaultdict(list)
    all_learnings = []
    completed = failed = 0

    for e in entries:
        by_sector[e["sector"]].append(e)
        all_learnings.extend(e.get("learnings", []))
        if e["status"] == "completed":
            completed += 1
        elif e["status"] == "failed":
            failed += 1

    sector_summary = {}
    for sec, tasks in by_sector.items():
        qualities = [t.get("quality_score", 8) for t in tasks if t.get("quality_score")]
        sector_summary[sec] = {
            "tasks":       len(tasks),
            "completed":   sum(1 for t in tasks if t["status"] == "completed"),
            "avg_quality": round(sum(qualities) / len(qualities), 1) if qualities else 0,
            "learnings":   sum(len(t.get("learnings", [])) for t in tasks),
            "top_agents":  list({t["agent_name"] for t in tasks})[:3],
        }

    return {
        "date":             target_date,
        "total_tasks":      len(entries),
        "completed":        completed,
        "failed":           failed,
        "success_rate":     round(completed / len(entries) * 100, 1) if entries else 0,
        "total_learnings":  len(all_learnings),
        "learnings":        list(set(all_learnings))[:20],
        "by_sector":        sector_summary,
        "agents_active":    len({e["agent_id"] for e in entries}),
    }


def write_obsidian_note(summary: dict):
    """Salva resumo diario no Obsidian vault como nota Periodic Notes."""
    note_dir = OBSIDIAN_DIR / "agentes"
    note_dir.mkdir(parents=True, exist_ok=True)

    d         = summary["date"]
    note_path = note_dir / f"daily-agents-{d}.md"

    sectors_md = ""
    for sec, data in summary["by_sector"].items():
        sectors_md += f"\n### {sec.title()}\n"
        sectors_md += f"- Tarefas: {data['tasks']} ({data['completed']} concluidas)\n"
        sectors_md += f"- Qualidade media: {data['avg_quality']}/10\n"
        sectors_md += f"- Aprendizados: {data['learnings']}\n"
        if data.get("top_agents"):
            sectors_md += f"- Agentes ativos: {', '.join(data['top_agents'])}\n"

    learnings_md = "\n".join(f"- {l}" for l in summary.get("learnings", []))

    content = f"""---
date: {d}
tags: [audiper/agentes, audiper/daily, agentes/performance]
type: daily-agents
---

# Resumo de Agentes -- {d}

## Stats do Dia
| Metrica | Valor |
|---------|-------|
| Total tarefas | {summary['total_tasks']} |
| Concluidas | {summary['completed']} |
| Taxa de sucesso | {summary['success_rate']}% |
| Aprendizados registrados | {summary['total_learnings']} |
| Agentes ativos | {summary['agents_active']} |

## Por Setor
{sectors_md}

## Aprendizados do Dia
{learnings_md if learnings_md else "- Nenhum aprendizado registrado"}

## Links
- [[mission-control]] - Dashboard Mission Control
- [[self-learning-system]] - Sistema de auto-aperfeicoamento
"""
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OBSIDIAN] Nota salva: {note_path}")


def update_dashboard_json(summary: dict):
    if DASHBOARD.exists():
        with open(DASHBOARD, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    data["last_daily_aggregate"] = summary["date"]
    data["stats"] = {
        "total_agents":   146,
        "active_today":   summary["agents_active"],
        "tasks_completed": summary["completed"],
        "tasks_failed":   summary["failed"],
        "success_rate":   summary["success_rate"],
        "total_learnings": summary["total_learnings"],
    }
    data["sector_performance"] = summary["by_sector"]
    data["generated_at"]       = datetime.utcnow().isoformat() + "Z"

    with open(DASHBOARD, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[DASHBOARD] Atualizado: {DASHBOARD}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime("%Y-%m-%d")
    print(f"[AGGREGATE] Processando logs de {target}...")

    entries = load_day_logs(target)
    print(f"[AGGREGATE] {len(entries)} entradas encontradas")

    if not entries:
        print("[AGGREGATE] Nenhum log encontrado para o dia.")
        return

    summary = aggregate(entries)
    write_obsidian_note(summary)
    update_dashboard_json(summary)

    print(f"[AGGREGATE] Concluido: {summary['total_tasks']} tarefas, {summary['total_learnings']} aprendizados")


if __name__ == "__main__":
    main()
