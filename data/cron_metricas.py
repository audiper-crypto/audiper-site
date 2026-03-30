"""
Cron job: atualiza metricas diarias no PostgreSQL.
Roda 1x por dia (scheduled task ou cron).
Coleta dados de todas as fontes e salva snapshot.
"""
import psycopg, json, os, datetime

DB_URL = 'postgresql://postgres:audiper2026@localhost:5432/audiper'
DASHBOARD_JSON = 'D:/Site/audiper/dashboard-data.json'
LEADS_DB = 'D:/Site/AgenteIAChatbot_PrimeiraVez/AgenteIAChatbot_PrimeiraVez/leads.db'

def get_conn():
    return psycopg.connect(DB_URL, autocommit=True)

def collect_and_save():
    conn = get_conn()
    c = conn.cursor()

    # 1. Dados do dashboard-data.json
    auditorias_ativas = 0
    ptas_total = 0
    ptas_ok = 0
    docs_total = 0
    relatorios = 0
    try:
        with open(DASHBOARD_JSON, encoding='utf-8') as f:
            dd = json.load(f)
        kpis = dd.get('kpis', {})
        auditorias_ativas = kpis.get('auditorias_ativas', 0)
        ptas_total = kpis.get('ptas_total', 0)
        ptas_ok = kpis.get('ptas_concluidos', 0)
        docs_total = kpis.get('documentos_indexados', 0)
        relatorios = kpis.get('relatorios_emitidos', 0)
    except Exception as e:
        print(f"Erro lendo dashboard-data.json: {e}")

    # 2. Dados do bot WhatsApp (leads.db)
    leads_total = 0
    leads_qualificados = 0
    mensagens = 0
    try:
        import sqlite3
        lconn = sqlite3.connect(LEADS_DB)
        lc = lconn.cursor()
        leads_total = lc.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        leads_qualificados = lc.execute("SELECT COUNT(*) FROM leads WHERE status='qualificado'").fetchone()[0]
        mensagens = lc.execute("SELECT COUNT(*) FROM mensagens").fetchone()[0]
        lconn.close()
    except Exception as e:
        print(f"Erro lendo leads.db: {e}")

    # 3. Contar emails (do snapshot JSON)
    emails = 0
    try:
        with open('D:/Site/audiper/data/emails-recentes.json', encoding='utf-8') as f:
            ed = json.load(f)
        emails = len(ed.get('emails', []))
    except:
        pass

    # 4. Salvar metricas
    c.execute("""
        INSERT INTO metricas_diarias (data, auditorias_ativas, achados_abertos, documentos_total,
            relatorios_emitidos, ptas_total, ptas_concluidos, leads_total, leads_qualificados, emails_recebidos)
        VALUES (CURRENT_DATE, %s, 47, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (data) DO UPDATE SET
            auditorias_ativas=EXCLUDED.auditorias_ativas,
            documentos_total=EXCLUDED.documentos_total,
            relatorios_emitidos=EXCLUDED.relatorios_emitidos,
            ptas_total=EXCLUDED.ptas_total,
            ptas_concluidos=EXCLUDED.ptas_concluidos,
            leads_total=EXCLUDED.leads_total,
            leads_qualificados=EXCLUDED.leads_qualificados,
            emails_recebidos=EXCLUDED.emails_recebidos
    """, (auditorias_ativas, docs_total, relatorios, ptas_total, ptas_ok, leads_total, leads_qualificados, emails))

    # 5. Salvar leads historico
    try:
        import sqlite3
        lconn = sqlite3.connect(LEADS_DB)
        lc = lconn.cursor()
        por_interesse = {}
        for r in lc.execute("SELECT interesse, COUNT(*) FROM leads WHERE interesse IS NOT NULL GROUP BY interesse"):
            por_interesse[r[0]] = r[1]
        lconn.close()

        c.execute("""
            INSERT INTO leads_historico (data, leads_novos, leads_qualificados, mensagens_total,
                interesse_proposta, interesse_pericia, interesse_auditoria, interesse_ia, interesse_lgpd)
            VALUES (CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (data) DO UPDATE SET
                leads_novos=EXCLUDED.leads_novos, leads_qualificados=EXCLUDED.leads_qualificados,
                mensagens_total=EXCLUDED.mensagens_total
        """, (leads_total, leads_qualificados, mensagens,
              por_interesse.get('proposta', 0), por_interesse.get('pericia', 0),
              por_interesse.get('auditoria', 0), por_interesse.get('consultoria_ia', 0),
              por_interesse.get('lgpd', 0)))
    except Exception as e:
        print(f"Erro salvando leads historico: {e}")

    # 6. Regenerar ops-data.json
    try:
        import subprocess
        subprocess.run(['python', 'D:/Site/audiper/data/gerar_ops.py'], capture_output=True, timeout=10)
    except:
        pass

    conn.close()

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"[{now}] Metricas atualizadas: {auditorias_ativas} auditorias, {leads_total} leads, {docs_total} docs, {ptas_ok}/{ptas_total} PTAs")

if __name__ == '__main__':
    collect_and_save()
