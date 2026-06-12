"""
update_dashboard.py — Gera dashboard-data.json 100% do banco PostgreSQL.
Executar: python update_dashboard.py
Agendado: n8n / Windows Task Scheduler a cada 10 min.

Cada item do JSON inclui links para modulos:
  - auditoria_id: link para /auditorias/{id}
  - cliente_id: link para /clientes/{id}
  - tipo: classifica para roteamento no frontend (prazo, achado, email, tarefa)
"""
import os
import json
from datetime import datetime
from pathlib import Path

AUDIT_ROOT = Path("D:/AUDITORIAS")
DB_URL = os.environ.get("AUDIPER_DB_URL", "postgresql://postgres@localhost:5432/audiper")
OUT = Path(__file__).parent / "dashboard-data.json"

# Mapeamento pasta filesystem -> codigo auditoria
FOLDER_MAP = {
    "OIG 2026": "OIGGAM",
    "UNIMED FLORIANO": "UNIMED",
    "JAPANVEICULOS": "JAPANV",
    "VIAPARIS": "VIAPAR",
    "VIASHANGHAI": "VIASHA",
    "RESOLVE": "RESOLV",
    "FAPEC": "FAPEC",
    "MEGALINK": "MEGALI",
    "CARITAS TERESINA": "CÁRITA",
}

FASE_LABEL = {
    "aceitacao": "Inicio (A)",
    "planejamento": "Planejamento",
    "execucao": "Execucao",
    "relatorios": "Entregue (G)",
}

FASE_STATUS = {
    "aceitacao": "prop",
    "planejamento": "plan",
    "execucao": "exec",
    "relatorios": "done",
}

SETOR_ICON = {
    "veiculos": "\U0001f697", "automoveis": "\U0001f697",
    "saude": "\U0001f3e5", "medico": "\U0001f3e5", "cooperativa": "\U0001f3e5",
    "telecom": "\U0001f4e1", "informatica": "\U0001f4e1",
    "gaming": "\U0001f3b2", "apostas": "\U0001f3b2",
    "educacao": "\U0001f393", "pesquisa": "\U0001f393",
    "social": "\U0001f91d", "caritas": "\U0001f91d", "diocesan": "\U0001f91d",
    "administra": "\U0001f4d0", "beneficio": "\U0001f4d0",
    "roupas": "\U0001f457", "confeccao": "\U0001f457",
}


def get_icon(texto: str) -> str:
    t = (texto or "").lower()
    for k, v in SETOR_ICON.items():
        if k in t:
            return v
    return "\U0001f4c1"


def count_docs(folder_name: str) -> int:
    path = AUDIT_ROOT / folder_name
    if not path.exists():
        return 0
    try:
        return sum(1 for f in path.rglob("*") if f.is_file())
    except Exception:
        return 0


def build_from_db() -> dict:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary", "-q"])
        import psycopg2
        from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ── 1. Auditorias com clientes ───────────────────────────────────
    cur.execute("""
        SELECT a.id AS auditoria_id, a.codigo, a.exercicio, a.status, a.fase_atual,
               a.contexto_atual, a.created_at AS inicio,
               c.id AS cliente_id, c.razao_social, c.nome_fantasia, c.cnpj,
               c.cnae_descricao, c.cor,
               (SELECT count(*) FROM achados ac WHERE ac.auditoria_id = a.id) AS total_achados,
               (SELECT count(*) FROM ptas p WHERE p.auditoria_id = a.id) AS total_ptas,
               (SELECT count(*) FROM ptas p WHERE p.auditoria_id = a.id AND p.status IN ('concluido','aprovado')) AS ptas_ok
        FROM auditorias a
        JOIN clientes c ON a.cliente_id = c.id
        ORDER BY a.created_at DESC
    """)
    rows = cur.fetchall()

    auditorias = []
    total_docs = 0
    total_achados = 0
    conclusoes = []

    for r in rows:
        codigo = r["codigo"] or ""
        cod_prefix = codigo.split("-")[0] if "-" in codigo else codigo

        # Achar pasta no filesystem
        folder = None
        for fname, cpfx in FOLDER_MAP.items():
            if cpfx in cod_prefix:
                folder = fname
                break

        docs = count_docs(folder) if folder else 0
        total_docs += docs
        total_achados += r["total_achados"] or 0

        nome = r["nome_fantasia"] or r["razao_social"] or "N/A"
        fase = r["fase_atual"] or "aceitacao"
        status_visual = FASE_STATUS.get(fase, "plan")

        # Se concluida no banco, marcar como done
        if r["status"] == "concluida":
            status_visual = "done"
            fase = "relatorios"

        icon = get_icon(r["cnae_descricao"] or nome)

        aud = {
            "id": str(r["auditoria_id"]),
            "label": nome,
            "codigo": codigo,
            "folder": folder or "",
            "fase": FASE_LABEL.get(fase, fase.title()),
            "status": status_visual,
            "icon": icon,
            "color": r["cor"] or "#64748B",
            "achados": r["total_achados"] or 0,
            "docs": docs,
            "ptas_total": r["total_ptas"] or 0,
            "ptas_ok": r["ptas_ok"] or 0,
            "exercicio": str(r["exercicio"] or ""),
            "cnpj": r["cnpj"] or "",
            # Links para modulos
            "link_cliente": f"/clientes/{r['cliente_id']}",
            "link_auditoria": f"/auditorias/{r['auditoria_id']}",
            "link_achados": f"/auditorias/{r['auditoria_id']}/achados",
            "link_ptas": f"/auditorias/{r['auditoria_id']}/ptas",
            "contexto": r["contexto_atual"],
        }
        auditorias.append(aud)

        # Conclusoes (auditorias entregues)
        if status_visual == "done":
            conclusoes.append({
                "cliente": nome,
                "codigo": codigo,
                "exercicio": str(r["exercicio"] or ""),
                "achados": r["total_achados"] or 0,
                "ptas_ok": r["ptas_ok"] or 0,
                "ptas_total": r["total_ptas"] or 0,
                "link_auditoria": f"/auditorias/{r['auditoria_id']}",
                "link_cliente": f"/clientes/{r['cliente_id']}",
            })

    # ── 2. Achados recentes ──────────────────────────────────────────
    cur.execute("""
        SELECT ac.id, ac.titulo, ac.severidade, ac.status, ac.norma_referencia,
               ac.created_at, c.razao_social AS cliente, a.codigo,
               a.id AS auditoria_id
        FROM achados ac
        JOIN auditorias a ON ac.auditoria_id = a.id
        JOIN clientes c ON a.cliente_id = c.id
        ORDER BY ac.created_at DESC LIMIT 10
    """)
    achados_recentes = []
    for r in cur.fetchall():
        nivel = {"critica": "alto", "alta": "alto", "media": "medio", "baixa": "baixo"}.get(
            (r["severidade"] or "").lower(), "medio"
        )
        achados_recentes.append({
            "titulo": r["titulo"],
            "cliente": r["cliente"] or r["codigo"],
            "risco": (r["severidade"] or "MEDIO").upper(),
            "status": (r["status"] or "aberto").title(),
            "nivel": nivel,
            "norma": r["norma_referencia"] or "",
            "link_auditoria": f"/auditorias/{r['auditoria_id']}",
            "link_achado": f"/achados/{r['id']}",
        })

    # ── 3. Atividade recente (audit_logs) ────────────────────────────
    cur.execute("""
        SELECT al.acao, al.entidade, al.created_at, al.dados_depois,
               al.auditoria_id,
               COALESCE(au.nome, 'Sistema') AS auditor_nome
        FROM audit_logs al
        LEFT JOIN auditores au ON al.auditor_id = au.id
        ORDER BY al.created_at DESC LIMIT 15
    """)
    activity = []
    for r in cur.fetchall():
        ts = r["created_at"]
        time_str = ts.strftime("%H:%M") if ts and ts.date() == datetime.now().date() else (
            "Ontem" if ts and (datetime.now() - ts).days == 1 else ts.strftime("%d/%m") if ts else ""
        )
        action_map = {
            "INSERT": "Criou", "UPDATE": "Atualizou", "DELETE": "Removeu",
            "email_recebido": "Email recebido de", "briefing_enviado": "Briefing enviado",
        }
        acao = action_map.get(r["acao"], r["acao"] or "Acao")
        target = r["entidade"] or ""
        dados = r["dados_depois"] or {}
        if isinstance(dados, dict) and dados.get("descricao"):
            target = dados["descricao"][:60]

        activity.append({
            "name": r["auditor_nome"],
            "action": acao,
            "target": target,
            "time": time_str,
            "color": "#C8262D" if "Vitor" in (r["auditor_nome"] or "") else "#1d4ed8",
            "link_auditoria": f"/auditorias/{r['auditoria_id']}" if r["auditoria_id"] else None,
        })

    # ── 4. Pendencias / Tarefas ──────────────────────────────────────
    cur.execute("""
        SELECT p.id, p.titulo, p.prioridade, p.categoria, p.status, p.created_at,
               a.codigo, c.razao_social AS cliente, a.id AS auditoria_id
        FROM pendencias p
        JOIN auditorias a ON p.auditoria_id = a.id
        JOIN clientes c ON a.cliente_id = c.id
        WHERE p.status IN ('aberta', 'em_tratamento')
        ORDER BY
            CASE p.prioridade WHEN 'critica' THEN 0 WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END,
            p.created_at ASC
        LIMIT 20
    """)
    tarefas = []
    for r in cur.fetchall():
        tarefas.append({
            "titulo": r["titulo"],
            "prioridade": r["prioridade"] or "media",
            "categoria": r["categoria"] or "",
            "prazo": r["created_at"].strftime("%d/%m/%Y") if r["created_at"] else "",
            "status": r["status"],
            "cliente": r["cliente"],
            "link_auditoria": f"/auditorias/{r['auditoria_id']}",
            "link_tarefa": f"/pendencias/{r['id']}",
        })

    # ── 5. Emails (audit_logs com acao='email_recebido') ─────────────
    cur.execute("""
        SELECT al.created_at, al.dados_depois, c.razao_social AS cliente
        FROM audit_logs al
        LEFT JOIN auditorias a ON al.auditoria_id = a.id
        LEFT JOIN clientes c ON a.cliente_id = c.id
        WHERE al.acao = 'email_recebido'
        ORDER BY al.created_at DESC LIMIT 10
    """)
    emails = []
    for r in cur.fetchall():
        dados = r["dados_depois"] or {}
        emails.append({
            "de": dados.get("cliente_email", r["cliente"] or "Desconhecido"),
            "assunto": (dados.get("descricao", "") or "")[:80],
            "data": r["created_at"].strftime("%d/%m") if r["created_at"] else "",
            "lido": True,
            "link_calendario": "/calendario",
        })

    # ── 6. Briefing mais recente ─────────────────────────────────────
    cur.execute("""
        SELECT conteudo, turno, gerado_em FROM briefings
        ORDER BY gerado_em DESC LIMIT 1
    """)
    briefing_row = cur.fetchone()
    briefing = None
    if briefing_row:
        briefing = {
            "data": briefing_row["gerado_em"].strftime("%d/%m/%Y") if briefing_row["gerado_em"] else "",
            "resumo": (briefing_row["conteudo"] or "")[:200],
            "turno": briefing_row["turno"] or "manha",
            "link_briefings": "/briefings",
        }

    # ── 7. PTAs globais ──────────────────────────────────────────────
    cur.execute("SELECT status, COUNT(*) FROM ptas GROUP BY status")
    ptas_stats = {r["status"]: r["count"] for r in cur.fetchall()}

    # ── 8. Equipe ────────────────────────────────────────────────────
    cur.execute("SELECT nome, email, cargo FROM auditores ORDER BY nivel_acesso DESC")
    equipe = [{"nome": r["nome"], "email": r["email"], "cargo": r["cargo"]} for r in cur.fetchall()]

    cur.close()
    conn.close()

    # ── Montar KPIs ──────────────────────────────────────────────────
    exec_count = sum(1 for a in auditorias if a["status"] == "exec")
    done_count = sum(1 for a in auditorias if a["status"] == "done")
    plan_count = sum(1 for a in auditorias if a["status"] in ("plan", "prop"))
    ptas_total = sum(ptas_stats.values())
    ptas_concluidos = ptas_stats.get("concluido", 0) + ptas_stats.get("aprovado", 0)

    # ── Briefing fallback (se nao tem no banco) ──────────────────────
    if not briefing:
        destaques = []
        if tarefas:
            urgentes = [t for t in tarefas if t["prioridade"] in ("critica", "alta")]
            if urgentes:
                destaques.append({"tipo": "tarefa", "texto": f"{len(urgentes)} tarefas urgentes pendentes"})
        if exec_count:
            destaques.append({"tipo": "prazo", "texto": f"{exec_count} auditorias em execucao"})
        if done_count:
            destaques.append({"tipo": "email", "texto": f"{done_count} auditorias concluidas — verificar pagamentos"})
        if not destaques:
            destaques.append({"tipo": "info", "texto": "Nenhuma pendencia urgente no momento."})

        briefing = {
            "data": datetime.now().strftime("%d/%m/%Y"),
            "resumo": f"{len(auditorias)} auditorias ativas. {exec_count} em execucao, {done_count} entregues.",
            "destaques": destaques,
        }

    return {
        "gerado_em": datetime.now().isoformat(),
        "kpis": {
            "auditorias_ativas": len(auditorias),
            "em_execucao": exec_count,
            "entregues": done_count,
            "planejamento": plan_count,
            "achados_confirmados": total_achados,
            "documentos_indexados": total_docs,
            "relatorios_emitidos": done_count,
            "ptas_total": ptas_total,
            "ptas_concluidos": ptas_concluidos,
            "ptas_em_andamento": ptas_stats.get("em_andamento", 0),
            "clientes_cadastrados": len(set(a["cnpj"] for a in auditorias)),
        },
        "auditorias": auditorias,
        "conclusoes": conclusoes,
        "achados_recentes": achados_recentes,
        "activity": activity,
        "tarefas": tarefas,
        "emails": emails,
        "briefing": briefing,
        "equipe": equipe,
        # Links globais para modulos
        "links": {
            "calendario": "/calendario",
            "clientes": "/clientes",
            "auditorias": "/auditorias",
            "achados": "/achados",
            "tarefas": "/tarefas",
            "qualidade": "/api/dashboard/qualidade",
            "mission_control": "/mission-control.html",
        },
    }


if __name__ == "__main__":
    print("[update_dashboard] Gerando dashboard-data.json do banco...")
    try:
        data = build_from_db()
    except Exception as e:
        print(f"[ERRO] Falha ao ler banco: {e}")
        print("[FALLBACK] Usando dados existentes")
        raise

    # Mesclar gcal_events se existirem no JSON anterior
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
            if "gcal_events" in old:
                data["gcal_events"] = old["gcal_events"]
                data["gcal_updated"] = old.get("gcal_updated")
        except Exception:
            pass

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    k = data["kpis"]
    print(f"[OK] {OUT.name} — {k['auditorias_ativas']} auditorias, "
          f"{k['ptas_concluidos']}/{k['ptas_total']} PTAs, "
          f"{k['documentos_indexados']} docs, {k['achados_confirmados']} achados")
    print(f"     {len(data['conclusoes'])} conclusoes, {len(data['tarefas'])} tarefas, "
          f"{len(data['emails'])} emails, {len(data['activity'])} atividades")
