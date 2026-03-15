#!/usr/bin/env python
"""
post_task_log.py — Claude Code hook: registra tarefa apos conclusao.
Ativado via .claude/settings.json hooks.PostToolUse
Le stdin JSON do Claude Code hooks API.

INSTALACAO:
  Copiar para: D:/Site/.claude/hooks/post_task_log.py
"""
import json, sys, subprocess
from pathlib import Path

SCRIPT = Path("D:/Site/audiper/scripts/log_agent_task.py")


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        event = json.loads(raw)
    except Exception:
        return

    tool_name  = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    session_id = event.get("session_id", "")

    # Apenas opera sobre escritas e execucoes relevantes
    RELEVANT = {"Write", "Edit", "Bash", "Agent"}
    if tool_name not in RELEVANT:
        return

    description = (
        tool_input.get("description", "")
        or tool_input.get("command", "")[:80]
        or tool_input.get("file_path", "")
    )
    if not description:
        return

    cmd = [
        sys.executable, str(SCRIPT),
        "--agent",   "Claude Code",
        "--sector",  "orchestration",
        "--task",    description[:120],
        "--status",  "completed",
        "--session", session_id[:8] if session_id else "hook",
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=5)
    except Exception:
        pass  # hook nunca deve bloquear o Claude


if __name__ == "__main__":
    main()
