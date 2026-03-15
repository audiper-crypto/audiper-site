#!/usr/bin/env python
"""
optimize_memory.py — Analisa logs historicos e sugere otimizacoes de memoria e skills.
Uso: python optimize_memory.py [--days 7]
     python optimize_memory.py 30
"""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date

LOG_DIR      = Path("D:/Site/audiper/agents/logs")
MEMORY_DIR   = Path("C:/Users/IBYTE/.claude/projects/D--Site/memory")
SKILLS_DIR   = Path("D:/Site/.claude/skills")
OBSIDIAN_DIR = Path("D:/Site/obsidian-vault/research/agentes")
OUTPUT       = Path("D:/Site/audiper/agents/optimization-report.json")


def load_recent_logs(days: int) -> list:
    entries = []
    for i in range(days):
        d = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        for f in LOG_DIR.glob(f"{d}_*.jsonl"):
            with open(f, encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
    return entries


def analyze_patterns(entries: list) -> dict:
    if not entries:
        return {"error": "Sem logs para analisar"}

    agent_counts  = Counter(e["agent_name"] for e in entries)
    sector_counts = Counter(e["sector"] for e in entries)

    all_words = []
    for e in entries:
        for learning in e.get("learnings", []):
            words = re.findall(r'\b[a-zA-Z\u00C0-\u00FF]{4,}\b', learning.lower())
            all_words.extend(words)
    top_topics = Counter(all_words).most_common(20)

    low_quality = [
        {
            "agent": e["agent_name"],
            "task":  e["task"],
            "score": e.get("quality_score", 8),
        }
        for e in entries if e.get("quality_score", 8) < 7.0
    ]

    failures = [
        {
            "agent":  e["agent_name"],
            "task":   e["task"],
            "sector": e["sector"],
        }
        for e in entries if e["status"] == "failed"
    ]

    return {
        "period_days":      len(set(e["timestamp"][:10] for e in entries)),
        "total_tasks":      len(entries),
        "top_agents":       dict(agent_counts.most_common(10)),
        "busiest_sectors":  dict(sector_counts.most_common(5)),
        "hot_topics":       [{"topic": t, "count": c} for t, c in top_topics],
        "low_quality_tasks": low_quality[:10],
        "failures":         failures[:10],
        "suggestions":      generate_suggestions(entries, low_quality, failures),
    }


def generate_suggestions(entries, low_quality, failures) -> list:
    suggestions = []

    if low_quality:
        sectors = Counter(t["agent"].split("-")[0] for t in low_quality)
        for sec, count in sectors.most_common(3):
            suggestions.append({
                "type":     "skill_improvement",
                "target":   sec,
                "action":   f"Revisar skill do setor {sec} -- {count} tarefas com qualidade < 7.0",
                "priority": "high" if count > 3 else "medium",
            })

    if failures:
        for f in failures[:3]:
            suggestions.append({
                "type":     "error_pattern",
                "target":   f["agent"],
                "action":   f"Investigar falhas recorrentes em {f['agent']} -- {f['task'][:50]}",
                "priority": "high",
            })

    if len(entries) > 10:
        suggestions.append({
            "type":     "memory_consolidation",
            "target":   "obsidian_vault",
            "action":   "Consolidar aprendizados da semana em nota sintese no Obsidian",
            "priority": "low",
        })

    return suggestions


def write_report(analysis: dict):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    analysis["generated_at"] = datetime.utcnow().isoformat() + "Z"
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"[OPTIMIZE] Relatorio salvo: {OUTPUT}")

    print(f"\n=== RESUMO DE OTIMIZACAO ===")
    print(f"Periodo: {analysis.get('period_days', 0)} dias")
    print(f"Total tarefas: {analysis.get('total_tasks', 0)}")
    print(f"\nSugestoes ({len(analysis.get('suggestions', []))}):")
    for s in analysis.get("suggestions", []):
        print(f"  [{s['priority'].upper()}] {s['action']}")


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    print(f"[OPTIMIZE] Analisando {days} dias de logs...")
    entries  = load_recent_logs(days)
    analysis = analyze_patterns(entries)
    write_report(analysis)


if __name__ == "__main__":
    main()
