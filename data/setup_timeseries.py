"""Criar tabelas de series temporais no PostgreSQL e migrar dados."""
import psycopg

conn = psycopg.connect('postgresql://postgres:audiper2026@localhost:5432/audiper')
conn.autocommit = True
c = conn.cursor()

# 1. Metricas diarias
c.execute("""CREATE TABLE IF NOT EXISTS metricas_diarias (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    auditorias_ativas INTEGER DEFAULT 0,
    achados_abertos INTEGER DEFAULT 0,
    achados_comunicados INTEGER DEFAULT 0,
    achados_resolvidos INTEGER DEFAULT 0,
    documentos_total INTEGER DEFAULT 0,
    relatorios_emitidos INTEGER DEFAULT 0,
    ptas_total INTEGER DEFAULT 0,
    ptas_concluidos INTEGER DEFAULT 0,
    leads_total INTEGER DEFAULT 0,
    leads_qualificados INTEGER DEFAULT 0,
    emails_recebidos INTEGER DEFAULT 0,
    emails_respondidos INTEGER DEFAULT 0,
    criado_em TIMESTAMP DEFAULT NOW(),
    UNIQUE(data)
)""")
print("metricas_diarias OK")

# 2. Atividade dos agentes
c.execute("""CREATE TABLE IF NOT EXISTS atividade_agentes (
    id SERIAL PRIMARY KEY,
    agente VARCHAR(50) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    descricao TEXT NOT NULL,
    resultado TEXT,
    duracao_ms INTEGER,
    criado_em TIMESTAMP DEFAULT NOW()
)""")
c.execute("CREATE INDEX IF NOT EXISTS idx_atividade_agente ON atividade_agentes(agente, criado_em DESC)")
c.execute("CREATE INDEX IF NOT EXISTS idx_atividade_tipo ON atividade_agentes(tipo, criado_em DESC)")
print("atividade_agentes OK")

# 3. Alertas do Igor
c.execute("""CREATE TABLE IF NOT EXISTS alertas_log (
    id SERIAL PRIMARY KEY,
    prioridade VARCHAR(10) NOT NULL DEFAULT 'INFO',
    categoria VARCHAR(30),
    cliente VARCHAR(100),
    descricao TEXT NOT NULL,
    acao_sugerida TEXT,
    status VARCHAR(20) DEFAULT 'pendente',
    resolvido_em TIMESTAMP,
    criado_em TIMESTAMP DEFAULT NOW()
)""")
c.execute("CREATE INDEX IF NOT EXISTS idx_alertas_status ON alertas_log(status, prioridade, criado_em DESC)")
print("alertas_log OK")

# 4. Leads historico
c.execute("""CREATE TABLE IF NOT EXISTS leads_historico (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    leads_novos INTEGER DEFAULT 0,
    leads_qualificados INTEGER DEFAULT 0,
    mensagens_total INTEGER DEFAULT 0,
    interesse_proposta INTEGER DEFAULT 0,
    interesse_pericia INTEGER DEFAULT 0,
    interesse_auditoria INTEGER DEFAULT 0,
    interesse_ia INTEGER DEFAULT 0,
    interesse_lgpd INTEGER DEFAULT 0,
    criado_em TIMESTAMP DEFAULT NOW(),
    UNIQUE(data)
)""")
print("leads_historico OK")

# 5. Emails log
c.execute("""CREATE TABLE IF NOT EXISTS emails_log (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    total_recebidos INTEGER DEFAULT 0,
    total_respondidos INTEGER DEFAULT 0,
    de_clientes INTEGER DEFAULT 0,
    urgentes INTEGER DEFAULT 0,
    com_documentos INTEGER DEFAULT 0,
    criado_em TIMESTAMP DEFAULT NOW(),
    UNIQUE(data)
)""")
print("emails_log OK")

# 6. Sessoes de trabalho
c.execute("""CREATE TABLE IF NOT EXISTS sessoes_trabalho (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    resumo TEXT NOT NULL,
    conquistas TEXT,
    horas REAL DEFAULT 0,
    tarefas_concluidas INTEGER DEFAULT 0,
    tarefas_pendentes INTEGER DEFAULT 0,
    commits INTEGER DEFAULT 0,
    arquivos_alterados INTEGER DEFAULT 0,
    criado_em TIMESTAMP DEFAULT NOW()
)""")
print("sessoes_trabalho OK")

# 7. Evolucao de metricas
c.execute("""CREATE TABLE IF NOT EXISTS evolucao_metricas (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    metrica VARCHAR(50) NOT NULL,
    valor REAL NOT NULL,
    unidade VARCHAR(20),
    criado_em TIMESTAMP DEFAULT NOW()
)""")
c.execute("CREATE INDEX IF NOT EXISTS idx_evolucao_metrica ON evolucao_metricas(metrica, data DESC)")
print("evolucao_metricas OK")

# === DADOS INICIAIS ===

# Metricas de hoje
c.execute("""INSERT INTO metricas_diarias (data, auditorias_ativas, achados_abertos, documentos_total, relatorios_emitidos, ptas_total, ptas_concluidos, leads_total, leads_qualificados)
    VALUES (CURRENT_DATE, 9, 47, 4390, 4, 378, 168, 6, 1)
    ON CONFLICT (data) DO UPDATE SET auditorias_ativas=EXCLUDED.auditorias_ativas, achados_abertos=EXCLUDED.achados_abertos, documentos_total=EXCLUDED.documentos_total""")
print("metricas hoje OK")

# Sessoes
sessoes = [
    ("2026-03-28", "OpenClaw + Design System + Hero 3D", "OpenClaw configurado, 13 skills, 10 logos, assinatura email, hero 3D", 8.0, 15, 0, 20, 0),
    ("2026-03-29", "Bot WhatsApp + Dashboard Leads + Numero novo", "Bot WhatsApp 18 fluxos, leads.db, multimodal, dashboard leads, numero 98125-1918", 10.0, 12, 0, 17, 114),
    ("2026-03-29", "Dashboard abas + emails + calendario + push", "Aba Tarefas, Aba Auditorias, Widget emails, Calendario semanal, RAG bot, Webhook leads, Mission Control", 3.0, 12, 0, 2, 10),
]
for s in sessoes:
    c.execute("INSERT INTO sessoes_trabalho (data, resumo, conquistas, horas, tarefas_concluidas, tarefas_pendentes, commits, arquivos_alterados) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", s)
print(f"{len(sessoes)} sessoes OK")

# Atividade agentes
atividades = [
    ("Helena", "pesquisa", "Pesquisou NBC TA 500 - Evidencia de Auditoria", "Resumo salvo", 45000),
    ("Helena", "pesquisa", "Briefing regulatorio - Licitacoes PI", "Nenhuma licitacao encontrada", 30000),
    ("Igor", "alerta", "Email OIG Gaming sem resposta ha 48h", "Reenvio sugerido", None),
    ("Igor", "alerta", "FAPEC parada ha 8 dias - 0/42 PTAs", "Sem progresso", None),
    ("Igor", "monitoramento", "Verificacao de prazos - 3 proximos 7 dias", "2 criticos", 5000),
    ("Audina Jr", "atendimento", "Lead qualificado: Vitor Eduardo (IA)", "Telegram notificado", 2000),
    ("Audina Jr", "atendimento", "Atendimento Carlos Kitanda - 2 msgs", "Lead registrado", 3000),
    ("QC", "revisao", "Revisao COM-08 OIG Gaming - APROVADO", "6/6 checklists OK", 60000),
    ("Audina", "coordenacao", "Delegou pesquisa NBC TA 330 para Helena", "Tarefa atribuida", 1000),
    ("Marcos", "analise", "Aguardando balancete OIG Gaming 2025", "Doc pendente 25/03", None),
]
for a in atividades:
    c.execute("INSERT INTO atividade_agentes (agente, tipo, descricao, resultado, duracao_ms) VALUES (%s,%s,%s,%s,%s)", a)
print(f"{len(atividades)} atividades OK")

# Alertas
alertas = [
    ("URGENTE", "prazo", "Japan Veiculos", "Prazo G-01 vence em 3 dias (15/04)", "Concluir revisao"),
    ("ATENCAO", "email", "OIG Gaming", "Email sem resposta ha 48h", "Reenviar solicitacao"),
    ("INFO", "auditoria", "FAPEC", "Parada ha 8 dias - 0/42 PTAs", "Verificar impedimentos"),
    ("ATENCAO", "prazo", "Unimed Floriano", "Encerramento fase em 2 dias", "Finalizar testes"),
    ("INFO", "compliance", None, "CRC/CNAI em dia", None),
]
for a in alertas:
    c.execute("INSERT INTO alertas_log (prioridade, categoria, cliente, descricao, acao_sugerida) VALUES (%s,%s,%s,%s,%s)", a)
print(f"{len(alertas)} alertas OK")

# Leads historico
c.execute("""INSERT INTO leads_historico (data, leads_novos, leads_qualificados, mensagens_total, interesse_ia)
    VALUES (CURRENT_DATE, 6, 1, 38, 1) ON CONFLICT (data) DO NOTHING""")
print("leads historico OK")

# Evolucao
metricas = [
    ("2026-03-28", "skills_openclaw", 13), ("2026-03-28", "logos_criados", 10),
    ("2026-03-29", "fluxos_whatsapp", 18), ("2026-03-29", "leads_captados", 6),
    ("2026-03-29", "mensagens_bot", 38), ("2026-03-29", "paginas_site", 86),
    ("2026-03-29", "arquivos_atualizados", 93), ("2026-03-29", "workflows_n8n", 15),
    ("2026-03-29", "pendencias_concluidas", 12),
]
for m in metricas:
    c.execute("INSERT INTO evolucao_metricas (data, metrica, valor) VALUES (%s,%s,%s)", m)
print(f"{len(metricas)} metricas evolucao OK")

# Verificar
print("\n=== RESUMO ===")
for t in ["metricas_diarias","atividade_agentes","alertas_log","leads_historico","emails_log","sessoes_trabalho","evolucao_metricas"]:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {c.fetchone()[0]} registros")

conn.close()
print("\nTodas as tabelas criadas e populadas!")
