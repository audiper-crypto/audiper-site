#!/usr/bin/env python
"""
log_agent_task.py — Registra tarefa realizada por um agente.
Uso: python log_agent_task.py --agent "Backend Architect" --sector engineering
                               --task "Implementou endpoint /audit"
                               --status completed --duration 120
                               --output "FastAPI endpoint com validacao Pydantic"
                               --learnings "SQLAlchemy lazy load evitar N+1"
"""
import argparse, json, uuid, os
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR        = Path("D:/Site/audiper/agents/logs")
DASHBOARD_DATA = Path("D:/Site/audiper/agents/dashboard-data.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent",     required=True)
    parser.add_argument("--sector",    required=True)
    parser.add_argument("--task",      required=True)
    parser.add_argument("--status",    default="completed",
                        choices=["completed", "in_progress", "failed", "skipped"])
    parser.add_argument("--duration",  type=int, default=0)
    parser.add_argument("--output",    default="")
    parser.add_argument("--learnings", nargs="*", default=[])
    parser.add_argument("--quality",   type=float, default=8.0)
    parser.add_argument("--session",   default="")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "id":             str(uuid.uuid4()),
        "agent_id":       args.agent.lower().replace(" ", "-"),
        "agent_name":     args.agent,
        "sector":         args.sector,
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "task":           args.task,
        "status":         args.status,
        "duration_ms":    args.duration * 1000,
        "output_summary": args.output,
        "learnings":      args.learnings,
        "quality_score":  args.quality,
        "session_id":     args.session or str(uuid.uuid4())[:8],
    }

    # Arquivo de log: agents/logs/YYYY-MM-DD_<sector>.jsonl
    today    = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"{today}_{args.sector}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    update_dashboard(entry)
    print(f"[LOG] {args.agent} -> {args.task} [{args.status}]")


def update_dashboard(entry):
    if DASHBOARD_DATA.exists():
        with open(DASHBOARD_DATA, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "stats":              {"tasks_completed": 0, "active_today": 0, "total_learnings": 0},
            "recent_activity":    [],
            "sector_performance": {},
        }

    if entry["status"] == "completed":
        data["stats"]["tasks_completed"] = data["stats"].get("tasks_completed", 0) + 1
    data["stats"]["total_learnings"] = data["stats"].get("total_learnings", 0) + len(entry.get("learnings", []))
    data["generated_at"] = datetime.now(timezone.utc).isoformat()

    activity = {
        "agent":  entry["agent_name"],
        "sector": entry["sector"],
        "task":   entry["task"],
        "status": entry["status"],
        "time":   entry["timestamp"][:16].replace("T", " "),
    }
    data["recent_activity"].insert(0, activity)
    data["recent_activity"] = data["recent_activity"][:20]

    s = entry["sector"]
    if s not in data["sector_performance"]:
        data["sector_performance"][s] = {"tasks": 0, "avg_quality": 0.0, "learnings": 0}
    sp = data["sector_performance"][s]
    sp["tasks"]    += 1
    sp["learnings"] += len(entry.get("learnings", []))

    with open(DASHBOARD_DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
