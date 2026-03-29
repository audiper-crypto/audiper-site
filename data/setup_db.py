import sqlite3

conn = sqlite3.connect("D:/Site/audiper/data/audiper.db")
c = conn.cursor()

c.executescript("""
CREATE TABLE IF NOT EXISTS sessoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL, resumo TEXT NOT NULL,
    conquistas TEXT, horas_estimadas REAL, criado_em TEXT
);
CREATE TABLE IF NOT EXISTS atualizacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, sessao_id INTEGER, area TEXT NOT NULL,
    tipo TEXT NOT NULL, descricao TEXT NOT NULL, arquivo TEXT, criado_em TEXT
);
CREATE TABLE IF NOT EXISTS aprendizados (
    id INTEGER PRIMARY KEY AUTOINCREMENT, sessao_id INTEGER, categoria TEXT NOT NULL,
    descricao TEXT NOT NULL, aplicado INTEGER DEFAULT 0, criado_em TEXT
);
CREATE TABLE IF NOT EXISTS pendencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT NOT NULL,
    prioridade TEXT DEFAULT 'MEDIA', area TEXT, status TEXT DEFAULT 'pendente',
    sessao_origem INTEGER, concluido_em TEXT, criado_em TEXT
);
CREATE TABLE IF NOT EXISTS evolucao (
    id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL, metrica TEXT NOT NULL,
    valor REAL NOT NULL, unidade TEXT, criado_em TEXT
);
""")

from datetime import datetime
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Sessoes
c.execute("INSERT INTO sessoes (data, resumo, conquistas, horas_estimadas, criado_em) VALUES (?,?,?,?,?)",
    ("2026-03-28", "OpenClaw + Design System + Hero 3D", "OpenClaw configurado, 13 skills, 10 logos, assinatura email, hero 3D", 8, now))
s1 = c.lastrowid

c.execute("INSERT INTO sessoes (data, resumo, conquistas, horas_estimadas, criado_em) VALUES (?,?,?,?,?)",
    ("2026-03-29", "Bot WhatsApp + Dashboard Leads + Numero novo", "Bot WhatsApp 18 fluxos, leads.db, multimodal, dashboard leads, numero 98125-1918, heartbeat jobs, Claude Sonnet 4", 10, now))
s2 = c.lastrowid

# Pendencias
for desc, prio, area in [
    ("Corrigir NSSM n8n (N8N_USER_FOLDER)", "ALTA", "n8n"),
    ("Criar workflow n8n Dashboard Emails", "ALTA", "n8n"),
    ("Conectar widget emails no dashboard", "ALTA", "dashboard"),
    ("Redesign painel bot WhatsApp AUDIPER", "MEDIA", "whatsapp"),
    ("Memoria de conversa bot (multi-turn)", "MEDIA", "whatsapp"),
    ("RAG com dados AUDIPER no bot", "MEDIA", "whatsapp"),
    ("Webhook n8n para leads qualificados", "MEDIA", "whatsapp"),
    ("Dashboard mission control Audiz", "ALTA", "dashboard"),
    ("Hero 3D logo transparente + integrar", "MEDIA", "design"),
    ("Git push commits do site", "ALTA", "site"),
    ("NSSM para OpenClaw como servico", "BAIXA", "infra"),
    ("Calendario visual de sessoes no dashboard", "ALTA", "dashboard"),
]:
    c.execute("INSERT INTO pendencias (descricao, prioridade, area, sessao_origem, criado_em) VALUES (?,?,?,?,?)",
        (desc, prio, area, s2, now))

# Aprendizados
for cat, desc in [
    ("infra", "OpenClaw cai com contexto 200K - limpar sessoes periodicamente"),
    ("infra", "NSSM precisa AppEnvironmentExtra com N8N_USER_FOLDER"),
    ("infra", "bootstrapMaxChars=15000 reduz contexto do OpenClaw"),
    ("whatsapp", "Fluxos com match parcial geram respostas erradas - usar match exato"),
    ("whatsapp", "CORS precisa reiniciar bot para aplicar"),
    ("whatsapp", "WhatsApp Business so configura catalogo pelo celular"),
    ("compliance", "Meta 2026 proibe chatbots genericos - suporte/vendas OK"),
    ("design", "mix-blend-mode:lighten nao funciona em PNGs com fundo preto"),
    ("n8n", "Servico NSSM le banco vazio se N8N_USER_FOLDER nao configurado"),
    ("leads", "Qualificacao automatica por palavras-chave funciona bem"),
]:
    c.execute("INSERT INTO aprendizados (sessao_id, categoria, descricao, criado_em) VALUES (?,?,?,?)",
        (s2, cat, desc, now))

# Evolucao
for data, metrica, valor, un in [
    ("2026-03-29", "leads_captados", 6, "un"),
    ("2026-03-29", "mensagens_bot", 34, "un"),
    ("2026-03-29", "fluxos_whatsapp", 18, "un"),
    ("2026-03-29", "skills_openclaw", 13, "un"),
    ("2026-03-29", "workflows_n8n", 15, "un"),
    ("2026-03-29", "paginas_site", 86, "un"),
    ("2026-03-29", "arquivos_atualizados", 93, "un"),
]:
    c.execute("INSERT INTO evolucao (data, metrica, valor, unidade, criado_em) VALUES (?,?,?,?,?)",
        (data, metrica, valor, un, now))

conn.commit()
print(f"audiper.db criado com sucesso!")
print(f"  Sessoes: {c.execute('SELECT COUNT(*) FROM sessoes').fetchone()[0]}")
print(f"  Pendencias: {c.execute('SELECT COUNT(*) FROM pendencias').fetchone()[0]}")
print(f"  Aprendizados: {c.execute('SELECT COUNT(*) FROM aprendizados').fetchone()[0]}")
print(f"  Evolucao: {c.execute('SELECT COUNT(*) FROM evolucao').fetchone()[0]}")
conn.close()
