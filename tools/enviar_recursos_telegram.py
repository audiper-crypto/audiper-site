#!/usr/bin/env python3
"""Envia o catálogo de recursos web externos (agents/memory/recursos-web-externos.json)
para o Telegram, agrupado por recomendação.

Uso:
    export TELEGRAM_BOT_TOKEN="<token>"
    export TELEGRAM_CHAT_ID="<chat_id>"   # opcional; default abaixo
    python tools/enviar_recursos_telegram.py
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

MEMORY = Path(__file__).resolve().parent.parent / "agents" / "memory" / "recursos-web-externos.json"

GRUPOS = [
    ("usar",           "✅ <b>PODE USAR</b> (legal, uso livre)"),
    ("usar_com_trava", "\U0001f512 <b>USAR COM TRAVA</b> (não subir dado de cliente)"),
    ("condicional",    "⚠️ <b>CONDICIONAL</b>"),
    ("opcional",       "\U0001f7e1 <b>OPCIONAL</b> (uso pessoal / baixa aderência)"),
    ("nao_usar",       "⛔ <b>PROIBIDO</b> (ilegal — só registro)"),
]


def montar_mensagem() -> str:
    dados = json.loads(MEMORY.read_text(encoding="utf-8"))
    itens = dados["ferramentas"]
    linhas = [
        "\U0001f4d1 <b>Recursos web — análise dos 50 sites</b>",
        "<i>Catalogados na memory do ecossistema Audiper</i>",
        "",
    ]
    for chave, titulo in GRUPOS:
        grupo = [i for i in itens if i.get("recomendacao") == chave]
        if not grupo:
            continue
        linhas.append(f"{titulo} — {len(grupo)}")
        for i in grupo:
            nome = i["nome"]
            aviso = i.get("aviso")
            if chave in ("usar_com_trava", "condicional", "nao_usar") and aviso:
                linhas.append(f"  • <b>{nome}</b> — {aviso}")
            else:
                linhas.append(f"  • {nome}")
        linhas.append("")
    linhas.append("\U0001f4c2 Detalhes: agents/memory/recursos-web-externos.json")
    return "\n".join(linhas)


def enviar_telegram(mensagem: str, chat_id: str, bot_token: str) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "User-Agent": "AUDIPER-Recursos/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8")).get("ok", False)
    except Exception as e:
        print(f"  [ERRO] Telegram falhou: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    msg = montar_mensagem()
    print(msg)
    print(f"\n[info] {len(msg)} caracteres")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "62036868")
    if not bot_token:
        print("\n⚠️  TELEGRAM_BOT_TOKEN não definido — mensagem NÃO enviada.")
        print("    export TELEGRAM_BOT_TOKEN=... && python tools/enviar_recursos_telegram.py")
        sys.exit(1)
    print(f"\n\U0001f4e4 Enviando (chat_id: {chat_id})...")
    ok = enviar_telegram(msg, chat_id, bot_token)
    print("✅ Enviado!" if ok else "❌ Falhou.")
    sys.exit(0 if ok else 1)
