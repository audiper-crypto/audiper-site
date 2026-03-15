#!/usr/bin/env python
"""
generate_briefing.py — Gera briefing matinal enriquecido com aprendizados dos archives.

Combina:
  - global_patterns.json  → o que funcionou bem no período
  - <sector>_patterns.json → destaques por área
  - dashboard-data.json    → stats ao vivo
  - logs recentes          → o que foi feito ontem

Saída:
  - agents/knowledge/briefing_YYYY-MM-DD.md   → nota Obsidian
  - stdout                                     → para o n8n enviar via Telegram

Uso:
  python generate_briefing.py              # hoje
  python generate_briefing.py --date 2026-03-15
  python generate_briefing.py --telegram   # output compacto para Telegram
"""
import argparse, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

KNOWLEDGE_DIR  = Path("D:/Site/audiper/agents/knowledge")
ARCHIVE_DIR    = Path("D:/Site/audiper/agents/archive")
LOGS_DIR       = Path("D:/Site/audiper/agents/logs")
DASHBOARD_DATA = Path("D:/Site/audiper/agents/dashboard-data.json")
OBSIDIAN_VAULT = Path("D:/Site/obsidian-vault")


def load_json(path: Path) -> dict | list:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_recent_archives(days: int = 1) -> list:
    """Carrega archives dos últimos N dias."""
    index_file = ARCHIVE_DIR / "index.json"
    if not index_file.exists():
        return []
    index = load_json(index_file)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    recent = []
    for meta in index.get("entries", []):
        if meta.get("archived_at", "") >= cutoff:
            fpath = ARCHIVE_DIR / meta["file"]
            if fpath.exists():
                recent.append(load_json(fpath))
    return recent


def load_logs_yesterday() -> list:
    """Carrega todos os logs de ontem."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    entries = []
    for log_file in LOGS_DIR.glob(f"{yesterday}_*.jsonl"):
        with open(log_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entries


def load_sector_patterns() -> dict:
    """Carrega todos os patterns de setor disponíveis."""
    patterns = {}
    for f in KNOWLEDGE_DIR.glob("*_patterns.json"):
        if f.name == "global_patterns.json":
            continue
        sector = f.name.replace("_patterns.json", "")
        patterns[sector] = load_json(f)
    return patterns


# ─── Formatação Markdown (Obsidian) ───────────────────────────────────────────
def generate_markdown(date_str: str, recent: list, logs: list,
                      global_p: dict, sector_patterns: dict, dash: dict) -> str:
    today = datetime.now().strftime("%d/%m/%Y")
    stats = dash.get("stats", {})

    # Header
    lines = [
        f"# Briefing Matinal — {today}",
        "",
        f"**Status do Sistema:** {len(recent)} tarefas arquivadas ontem | "
        f"Score médio: {_avg_quality(recent):.1f}/10",
        "",
        "---",
        "",
    ]

    # ── 1. Destaques de ontem ──
    lines += ["## Destaques de Ontem", ""]
    if recent:
        top_5 = sorted(recent, key=lambda x: x.get("quality_score", 0), reverse=True)[:5]
        for a in top_5:
            lines.append(f"- **{a.get('agent_name', a.get('agent_id'))}** ({a.get('sector')}) "
                         f"— {a.get('task', '')[:80]} `q={a.get('quality_score')}`")
        lines.append("")
    else:
        lines += ["_Nenhum archive disponível para ontem._", ""]

    # ── 2. Aprendizados consolidados ──
    lines += ["## Aprendizados Consolidados", ""]
    all_learnings = []
    for a in recent:
        all_learnings.extend(a.get("learnings", []))
    if all_learnings:
        from collections import Counter
        top_learn = [l for l, _ in Counter(
            l.strip() for l in all_learnings if isinstance(l, str) and l.strip()
        ).most_common(10)]
        for l in top_learn:
            lines.append(f"- {l}")
        lines.append("")
    elif global_p.get("top_learnings"):
        for l in global_p["top_learnings"][:8]:
            lines.append(f"- {l}")
        lines.append("")
    else:
        lines += ["_Base de conhecimento ainda sendo construída._", ""]

    # ── 3. Saúde por setor ──
    lines += ["## Saúde por Setor", ""]
    sector_q = global_p.get("sector_quality", {})
    if sector_q:
        for sector, avg in sorted(sector_q.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(avg) + "░" * (10 - int(avg))
            lines.append(f"- **{sector.title()}**: {bar} {avg:.1f}/10")
        lines.append("")
    else:
        lines += ["_Aguardando dados suficientes._", ""]

    # ── 4. Top agentes globais ──
    lines += ["## Top Agentes", ""]
    top_agents = global_p.get("top_agents", [])[:5]
    if top_agents:
        for ag in top_agents:
            lines.append(f"- `{ag['agent_id']}` — {ag['avg']}/10 média ({ag['count']} tarefas)")
        lines.append("")

    # ── 5. Destaques por setor ──
    lines += ["## Padrões por Setor", ""]
    for sector, patterns in list(sector_patterns.items())[:4]:
        if not patterns:
            continue
        lines.append(f"### {sector.title()}")
        for l in patterns.get("top_learnings", [])[:3]:
            lines.append(f"  - {l}")
        lines.append("")

    # ── 6. Stats do sistema ──
    lines += [
        "## Stats do Sistema",
        "",
        f"- Tarefas completadas: {stats.get('tasks_completed', 0)}",
        f"- Aprendizados registrados: {stats.get('total_learnings', 0)}",
        f"- Logs ontem: {len(logs)}",
        f"- Archives total: {global_p.get('total_archives', 0)}",
        "",
        "---",
        "",
        f"_Gerado automaticamente em {datetime.now().strftime('%H:%M')} · "
        f"[[{date_str}-briefing|Próximo]] · [[{_yesterday()}-briefing|Anterior]]_",
        "",
        "## Tags",
        "#briefing #audiper #agentes #auto-melhoria",
    ]

    return "\n".join(lines)


# ─── Formatação Telegram ──────────────────────────────────────────────────────
def generate_telegram(recent: list, global_p: dict, dash: dict) -> str:
    stats  = dash.get("stats", {})
    today  = datetime.now().strftime("%d/%m/%Y")
    lines  = [
        f"<b>Briefing Matinal — {today}</b>",
        "",
    ]

    # Destaques de ontem
    if recent:
        lines.append(f"<b>Ontem: {len(recent)} tarefas arquivadas</b> (score medio {_avg_quality(recent):.1f}/10)")
        top3 = sorted(recent, key=lambda x: x.get("quality_score", 0), reverse=True)[:3]
        for a in top3:
            lines.append(f"  {a.get('agent_name', '?')} — {a.get('task', '')[:55]}... q={a.get('quality_score')}")
        lines.append("")

    # Top learnings do período
    all_learnings = []
    for a in recent:
        all_learnings.extend(a.get("learnings", []))
    if not all_learnings:
        all_learnings = global_p.get("top_learnings", [])[:5]

    if all_learnings:
        from collections import Counter
        top = [l for l, _ in Counter(
            l.strip() for l in all_learnings if isinstance(l, str) and l.strip()
        ).most_common(5)]
        lines.append("<b>Principais aprendizados:</b>")
        for l in top:
            lines.append(f"  {l[:70]}")
        lines.append("")

    # Stats
    lines += [
        f"<b>Stats:</b> {stats.get('tasks_completed', 0)} tarefas | "
        f"{stats.get('total_learnings', 0)} aprendizados | "
        f"{global_p.get('total_archives', 0)} archives",
    ]

    return "\n".join(lines)


# ─── Utils ────────────────────────────────────────────────────────────────────
def _avg_quality(archives: list) -> float:
    if not archives:
        return 0.0
    return sum(a.get("quality_score", 0) for a in archives) / len(archives)


def _yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Gera briefing matinal dos agentes")
    parser.add_argument("--date",     default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--telegram", action="store_true", help="Output compacto para Telegram")
    parser.add_argument("--days",     type=int, default=1, help="Janela de archives (dias)")
    args = parser.parse_args()

    # Carregar dados
    recent          = load_recent_archives(args.days)
    logs            = load_logs_yesterday()
    global_patterns = load_json(KNOWLEDGE_DIR / "global_patterns.json")
    sector_patterns = load_sector_patterns()
    dash            = load_json(DASHBOARD_DATA)

    if args.telegram:
        print(generate_telegram(recent, global_patterns, dash))
    else:
        md = generate_markdown(args.date, recent, logs, global_patterns, sector_patterns, dash)
        print(md)

        # Salvar em knowledge/
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        out_file = KNOWLEDGE_DIR / f"briefing_{args.date}.md"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n[SAVED] {out_file}", flush=True)

        # Salvar no Obsidian vault se existir
        vault_dir = OBSIDIAN_VAULT / "pesquisa" / "briefings"
        if OBSIDIAN_VAULT.exists():
            vault_dir.mkdir(parents=True, exist_ok=True)
            vault_file = vault_dir / f"{args.date}-briefing.md"
            with open(vault_file, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"[VAULT] {vault_file}", flush=True)


if __name__ == "__main__":
    main()
