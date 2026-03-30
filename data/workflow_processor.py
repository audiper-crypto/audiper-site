"""
Processador de workflows automaticos do Chat AUDIPER.
Quando uma mensagem e enviada, verifica se algum workflow deve ser disparado.
Roda como cron a cada 5 minutos ou chamado pela API.
"""
import psycopg, json, datetime

DB_URL = 'postgresql://postgres:audiper2026@localhost:5432/audiper'

def get_conn():
    return psycopg.connect(DB_URL, autocommit=True)

def process_pending():
    """Processa mensagens recentes e dispara workflows."""
    conn = get_conn()
    c = conn.cursor()

    # Buscar mensagens dos ultimos 5 minutos que nao foram processadas
    c.execute("""
        SELECT cm.id, cm.canal, cm.autor, cm.tipo, cm.mensagem, cm.criado_em
        FROM chat_mensagens cm
        WHERE cm.criado_em > NOW() - INTERVAL '5 minutes'
        ORDER BY cm.criado_em DESC
        LIMIT 20
    """)
    mensagens = [dict(zip([d[0] for d in c.description], r)) for r in c.fetchall()]

    if not mensagens:
        return 0

    # Buscar workflows ativos
    c.execute("SELECT * FROM chat_workflows WHERE ativo = TRUE")
    workflows = [dict(zip([d[0] for d in c.description], r)) for r in c.fetchall()]

    disparados = 0
    for msg in mensagens:
        for wf in workflows:
            if should_trigger(msg, wf):
                execute_workflow(c, msg, wf)
                disparados += 1

    conn.close()
    return disparados

def should_trigger(msg, wf):
    """Verifica se a mensagem dispara o workflow."""
    text = (msg.get('mensagem', '') or '').lower()
    autor = (msg.get('autor', '') or '').lower()
    canal = msg.get('canal', '')
    condicao = (wf.get('condicao', '') or '').lower()

    # Verificar canal de origem
    if wf['canal_origem'] != 'todos' and canal != wf['canal_origem']:
        return False

    # Verificar condicoes
    if 'helena' in condicao and 'helena' not in autor:
        return False
    if 'igor' in condicao and 'igor' not in autor:
        return False
    if 'marcos' in condicao and 'marcos' not in autor:
        return False
    if 'audina jr' in condicao and 'audina jr' not in autor:
        return False
    if 'qc' in condicao and 'qc' not in autor:
        return False

    if 'pesquisa' in condicao and 'pesquis' not in text:
        return False
    if 'alerta' in condicao and 'alerta' not in text and 'urgente' not in text:
        return False
    if 'achado' in condicao and 'achado' not in text and 'divergen' not in text:
        return False
    if 'qualifica' in condicao and 'qualificad' not in text:
        return False
    if 'aprova' in condicao and 'aprovad' not in text:
        return False

    return True

def execute_workflow(cursor, msg, wf):
    """Executa o workflow — posta mensagem no canal destino."""
    canal_destino = wf['canal_destino']
    agente = wf.get('agente_executor', 'Audina')

    # Se destino e 'auto', determinar canal pelo cliente mencionado
    if canal_destino == 'auto':
        text = msg.get('mensagem', '').lower()
        if 'oig' in text: canal_destino = 'oig-gaming'
        elif 'unimed' in text: canal_destino = 'unimed-floriano'
        elif 'fapec' in text: canal_destino = 'fapec'
        elif 'megalink' in text: canal_destino = 'megalink'
        elif 'resolve' in text: canal_destino = 'resolve'
        else: canal_destino = 'geral'

    # Construir mensagem do workflow
    wf_msg = f"[Workflow: {wf['nome']}] {wf['acao']} — Ref: {msg['autor']}: {msg['mensagem'][:100]}"

    cursor.execute(
        "INSERT INTO chat_mensagens (canal, autor, tipo, mensagem) VALUES (%s, %s, 'agente', %s)",
        (canal_destino, agente, wf_msg)
    )

    now = datetime.datetime.now().strftime('%H:%M')
    print(f"  [{now}] Workflow '{wf['nome']}': #{msg['canal']} -> #{canal_destino} ({agente})")

def generate_daily_summary():
    """Gera resumo diario de todos os canais."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT canal, COUNT(*) as msgs, COUNT(DISTINCT autor) as autores
        FROM chat_mensagens
        WHERE criado_em > CURRENT_DATE
        GROUP BY canal
        ORDER BY msgs DESC
    """)
    canais = c.fetchall()

    if not canais:
        conn.close()
        return

    resumo = "Resumo do dia:\n"
    total_msgs = 0
    for canal, msgs, autores in canais:
        resumo += f"• #{canal}: {msgs} mensagens, {autores} participantes\n"
        total_msgs += msgs

    # Buscar alertas pendentes
    c.execute("SELECT COUNT(*) FROM alertas_log WHERE status='pendente'")
    alertas = c.fetchone()[0]

    # Buscar leads do dia
    c.execute("SELECT leads_total, leads_qualificados FROM metricas_diarias WHERE data=CURRENT_DATE")
    m = c.fetchone()
    leads_info = f"Leads: {m[0]} total, {m[1]} qualificados" if m else "Leads: sem dados"

    resumo += f"\nTotal: {total_msgs} mensagens hoje\nAlertas pendentes: {alertas}\n{leads_info}"

    # Postar no canal resumo-diario
    c.execute(
        "INSERT INTO chat_mensagens (canal, autor, tipo, mensagem) VALUES ('resumo-diario', 'Audina', 'agente', %s)",
        (resumo,)
    )
    print(f"Resumo diario postado no #resumo-diario")
    conn.close()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'summary':
        generate_daily_summary()
    else:
        n = process_pending()
        print(f"{n} workflow(s) disparado(s)")
