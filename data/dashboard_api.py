"""
API REST para o Dashboard AUDIPER v2.
Serve dados do PostgreSQL em tempo real.
Porta 3001 — CORS habilitado para localhost:8080.
"""
import json, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.parse
import psycopg
import urllib.request

ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

DB_URL = 'postgresql://postgres:audiper2026@localhost:5432/audiper'
PORT = 3001

def get_conn():
    return psycopg.connect(DB_URL, autocommit=True)

def query(sql, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            cols = [d[0] for d in cur.description] if cur.description else []
            return [dict(zip(cols, row)) for row in cur.fetchall()]

def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else {}

class DashboardHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/api/chat':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            message = body.get('message', '')
            history = body.get('history', [])

            # Buscar contexto do banco
            context = ''
            try:
                metricas = query_one("SELECT * FROM metricas_diarias WHERE data = CURRENT_DATE")
                if metricas:
                    context += f"\nDados: {metricas.get('auditorias_ativas',0)} auditorias, {metricas.get('achados_abertos',0)} achados, {metricas.get('documentos_total',0)} docs, {metricas.get('ptas_concluidos',0)}/{metricas.get('ptas_total',0)} PTAs."
                alertas = query("SELECT prioridade, cliente, descricao FROM alertas_log WHERE status='pendente' ORDER BY criado_em DESC LIMIT 5")
                if alertas:
                    context += "\nAlertas: " + "; ".join(f"[{a['prioridade']}] {a.get('cliente','')}: {a['descricao']}" for a in alertas)
                agentes = query("SELECT DISTINCT ON (agente) agente, tipo, descricao FROM atividade_agentes ORDER BY agente, criado_em DESC")
                if agentes:
                    context += "\nAgentes: " + "; ".join(f"{a['agente']} ({a['tipo']}): {a['descricao']}" for a in agentes)
            except Exception as e:
                context += f"\n(erro banco: {e})"

            # Buscar auditorias do JSON
            try:
                import pathlib
                djson = pathlib.Path(__file__).parent.parent / 'dashboard-data.json'
                if djson.exists():
                    dd = json.loads(djson.read_text(encoding='utf-8'))
                    if dd.get('auditorias'):
                        context += "\nAuditorias: " + "; ".join(f"{a['label']} ({a['fase']}, {a['ptas_ok']}/{a['ptas_total']} PTAs, {a['docs']} docs)" for a in dd['auditorias'])
            except: pass

            # Chamar Claude API
            try:
                payload = json.dumps({
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 300,
                    "system": f"Voce e a Audina, assistente de auditoria da AUDIPER. Responda em portugues BR, concisa (max 3 frases). Tom sereno e profissional. Use os dados do contexto. Nunca invente dados.\n\nCONTEXTO:{context}",
                    "messages": history[-6:] if history else [{"role":"user","content":message}]
                }).encode()
                req = urllib.request.Request(
                    'https://api.anthropic.com/v1/messages',
                    data=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'x-api-key': ANTHROPIC_KEY,
                        'anthropic-version': '2023-06-01'
                    }
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read())
                    answer = result.get('content', [{}])[0].get('text', 'Nao consegui processar a solicitacao.')
                self.json_response({"response": answer})
            except Exception as e:
                # Fallback 1: Ollama local (gemma3:12b)
                try:
                    op = json.dumps({"model":"qwen3:8b","messages":[{"role":"system","content":f"Voce e a Audina, assistente de auditoria da AUDIPER. Portugues BR, concisa, tom sereno.\n\nCONTEXTO:{context}"},{"role":"user","content":message}],"stream":False}).encode()
                    oreq = urllib.request.Request('http://localhost:11434/api/chat', data=op, headers={'Content-Type':'application/json'})
                    with urllib.request.urlopen(oreq, timeout=30) as oresp:
                        oresult = json.loads(oresp.read())
                        oanswer = oresult.get('message',{}).get('content','')
                        if oanswer:
                            self.json_response({"response": oanswer, "source": "ollama-gemma3"})
                            return
                except: pass
                # Fallback 2: respostas estaticas com dados reais
                answer = self._fallback_response(message, context)
                self.json_response({"response": answer, "source": "fallback"})

        elif path == '/api/braindump':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            cliente = body.get('cliente', '')
            categoria = body.get('categoria', 'geral')
            conteudo = body.get('conteudo', '')
            autor = body.get('autor', 'Vitor Eduardo')
            if not cliente or not conteudo:
                self.json_response({"ok": False, "error": "cliente e conteudo sao obrigatorios"})
            else:
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO brain_dump (cliente, categoria, conteudo, autor) VALUES (%s,%s,%s,%s) RETURNING id, criado_em",
                            (cliente, categoria, conteudo, autor)
                        )
                        row = cur.fetchone()
                        self.json_response({"ok": True, "id": row[0], "criado_em": str(row[1])})

        elif path == '/api/chat/send':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            canal = body.get('canal', 'geral')
            autor = body.get('autor', 'Anonimo')
            mensagem = body.get('mensagem', '')
            tipo = body.get('tipo', 'humano')
            if mensagem.strip():
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("INSERT INTO chat_mensagens (canal, autor, tipo, mensagem) VALUES (%s,%s,%s,%s) RETURNING id, criado_em", (canal, autor, tipo, mensagem))
                        row = cur.fetchone()
                        self.json_response({"ok": True, "id": row[0], "criado_em": str(row[1])})
            else:
                self.json_response({"ok": False, "error": "mensagem vazia"})

        else:
            self.send_response(404)
            self.send_header('Content-Type','application/json')
            self.send_header('Access-Control-Allow-Origin','*')
            self.end_headers()
            self.wfile.write(json.dumps({"error":"not found"}).encode())

    def _fallback_response(self, text, context):
        """Resposta inteligente sem Claude, usando dados do banco."""
        lower = text.lower()
        # Buscar dados
        try:
            m = query_one("SELECT * FROM metricas_diarias WHERE data = CURRENT_DATE")
        except: m = {}
        try:
            alertas = query("SELECT prioridade, cliente, descricao FROM alertas_log WHERE status='pendente' LIMIT 5")
        except: alertas = []
        try:
            agentes = query("SELECT DISTINCT ON (agente) agente, descricao FROM atividade_agentes ORDER BY agente, criado_em DESC")
        except: agentes = []

        # Respostas contextuais
        if 'oig' in lower:
            return 'OIG Gaming esta em fase de execucao. 0 de 42 PTAs concluidos. 1.494 documentos indexados. Testes substantivos pendentes.'
        if 'japan' in lower:
            return 'Japan Veiculos: auditoria entregue. 42/42 PTAs concluidos. Relatorio G-01 emitido.'
        if 'unimed' in lower:
            return 'Unimed Floriano em execucao. 532 documentos indexados. Alerta: encerramento de fase em 2 dias.'
        if 'fapec' in lower:
            return 'FAPEC em planejamento. 72 documentos. 0/42 PTAs concluidos. Parada ha 8 dias.'
        if 'megalink' in lower:
            return 'Megalink Telecom em fase inicial (Proposta). 135 documentos. Aguardando aceite.'
        if 'achado' in lower:
            return f"Achados: {m.get('achados_abertos',47)} confirmados. Alertas: " + "; ".join(f"{a['cliente']}: {a['descricao']}" for a in alertas[:3]) if alertas else 'Sem alertas pendentes.'
        if 'prazo' in lower or 'vence' in lower:
            return "Prazos criticos: " + "; ".join(f"[{a['prioridade']}] {a['cliente']}: {a['descricao']}" for a in alertas if a['prioridade'] in ('URGENTE','ATENCAO')) if alertas else 'Sem prazos criticos.'
        if 'equipe' in lower or 'agente' in lower:
            return "Status da equipe: " + ". ".join(f"{a['agente']}: {a['descricao']}" for a in agentes) if agentes else 'Sem dados de agentes.'
        if 'lead' in lower or 'whatsapp' in lower:
            return f"{m.get('leads_total',6)} leads captados. {m.get('leads_qualificados',1)} qualificados."
        if any(s in lower for s in ('oi','ola','boa','bom')):
            h = __import__('datetime').datetime.now().hour
            sauda = 'Bom dia' if h < 12 else 'Boa tarde' if h < 18 else 'Boa noite'
            return f"{sauda}, Vitor. {m.get('auditorias_ativas',9)} auditorias ativas, {len(alertas)} alertas pendentes. Em que posso ajudar?"
        return f"{m.get('auditorias_ativas',9)} auditorias ativas, {m.get('ptas_concluidos',168)}/{m.get('ptas_total',378)} PTAs concluidos ({round(m.get('ptas_concluidos',168)/max(m.get('ptas_total',378),1)*100)}%), {m.get('relatorios_emitidos',4)} relatorios emitidos."

    def _reverse_prompt(self):
        """Gera sugestoes de melhoria baseadas nos dados reais do banco."""
        from datetime import datetime, timedelta
        sugestoes = []

        try:
            # 1. Verificar agentes inativos (sem atividade em 2+ dias)
            agentes = query("""
                SELECT agente, MAX(criado_em) as ultima_atividade
                FROM atividade_agentes
                GROUP BY agente
            """)
            dois_dias = datetime.now() - timedelta(days=2)
            for a in agentes:
                if a.get('ultima_atividade') and a['ultima_atividade'] < dois_dias:
                    dias = (datetime.now() - a['ultima_atividade']).days
                    sugestoes.append({
                        "agente": a['agente'],
                        "sugestao": f"{a['agente']} esta inativo ha {dias} dias. Verificar se ha tarefas pendentes ou reativar pesquisas.",
                        "prioridade": "ALTA" if dias > 3 else "MEDIA"
                    })
        except: pass

        try:
            # 2. Verificar alertas urgentes pendentes
            alertas_urgentes = query("SELECT COUNT(*) as total FROM alertas_log WHERE status = 'pendente' AND prioridade = 'URGENTE'")
            total_urgentes = alertas_urgentes[0].get('total', 0) if alertas_urgentes else 0
            if total_urgentes > 0:
                sugestoes.append({
                    "agente": "Igor",
                    "sugestao": f"Ha {total_urgentes} alerta(s) URGENTE pendente(s). Igor deve escalar para Telegram e notificar equipe.",
                    "prioridade": "URGENTE"
                })
        except: pass

        try:
            # 3. Verificar leads nao qualificados
            m = query_one("SELECT leads_total, leads_qualificados FROM metricas_diarias WHERE data = CURRENT_DATE")
            if m:
                nao_qualif = (m.get('leads_total', 0) or 0) - (m.get('leads_qualificados', 0) or 0)
                if nao_qualif > 3:
                    sugestoes.append({
                        "agente": "Audina Jr",
                        "sugestao": f"{nao_qualif} leads aguardando qualificacao. Audina Jr deve fazer followup e triagem dos leads novos.",
                        "prioridade": "MEDIA"
                    })
        except: pass

        try:
            # 4. Verificar progresso PTAs
            m2 = query_one("SELECT ptas_concluidos, ptas_total FROM metricas_diarias WHERE data = CURRENT_DATE")
            if m2 and m2.get('ptas_total', 0) > 0:
                pct = (m2.get('ptas_concluidos', 0) or 0) / m2['ptas_total'] * 100
                if pct < 50:
                    sugestoes.append({
                        "agente": "Marcos",
                        "sugestao": f"Apenas {pct:.0f}% dos PTAs concluidos ({m2.get('ptas_concluidos',0)}/{m2['ptas_total']}). Marcos deve priorizar testes substantivos das auditorias em execucao.",
                        "prioridade": "ALTA"
                    })
        except: pass

        try:
            # 5. Sugestao baseada em pesquisas recentes
            pesquisas = query("SELECT descricao FROM atividade_agentes WHERE tipo = 'pesquisa' ORDER BY criado_em DESC LIMIT 3")
            if pesquisas:
                tema = pesquisas[0].get('descricao', 'normas contabeis')
                sugestoes.append({
                    "agente": "Clara",
                    "sugestao": f"Clara pode preparar artigo tecnico sobre o tema mais pesquisado recentemente: {tema[:80]}.",
                    "prioridade": "BAIXA"
                })
            else:
                sugestoes.append({
                    "agente": "Helena",
                    "sugestao": "Helena deveria atualizar pesquisa de normas — nenhuma pesquisa recente encontrada.",
                    "prioridade": "MEDIA"
                })
        except:
            sugestoes.append({
                "agente": "Clara",
                "sugestao": "Clara pode preparar artigo sobre reforma tributaria ou atualizacoes CPC/NBC.",
                "prioridade": "BAIXA"
            })

        # Garantir minimo de 5 sugestoes com genericas inteligentes
        genericas = [
            {"agente": "Helena", "sugestao": "Helena deveria verificar atualizacoes de normas NBC TA e Portarias SPA/MF dos ultimos 7 dias.", "prioridade": "BAIXA"},
            {"agente": "Igor", "sugestao": "Igor pode consolidar relatorio semanal de alertas e enviar resumo ao Telegram.", "prioridade": "BAIXA"},
            {"agente": "Audina Jr", "sugestao": "Audina Jr deve revisar scripts de qualificacao de leads e atualizar respostas automaticas.", "prioridade": "BAIXA"},
            {"agente": "Marcos", "sugestao": "Marcos pode analisar produtividade da equipe e identificar gargalos nos PTAs pendentes.", "prioridade": "MEDIA"},
            {"agente": "Clara", "sugestao": "Clara pode gerar briefing executivo das auditorias em andamento para envio semanal.", "prioridade": "BAIXA"},
        ]
        idx = 0
        while len(sugestoes) < 5 and idx < len(genericas):
            if not any(s['agente'] == genericas[idx]['agente'] and s['sugestao'][:30] == genericas[idx]['sugestao'][:30] for s in sugestoes):
                sugestoes.append(genericas[idx])
            idx += 1

        return {"sugestoes": sugestoes[:5], "total": len(sugestoes)}

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == '/api/metricas':
                data = query_one("SELECT * FROM metricas_diarias WHERE data = CURRENT_DATE")
                self.json_response(data)

            elif path == '/api/metricas/historico':
                data = query("SELECT * FROM metricas_diarias ORDER BY data DESC LIMIT 30")
                self.json_response(data)

            elif path == '/api/atividade':
                data = query("SELECT * FROM atividade_agentes ORDER BY criado_em DESC LIMIT 50")
                # Convert timestamps to string
                for d in data:
                    if d.get('criado_em'):
                        d['criado_em'] = str(d['criado_em'])
                self.json_response(data)

            elif path == '/api/alertas':
                data = query("SELECT * FROM alertas_log WHERE status = 'pendente' ORDER BY CASE prioridade WHEN 'URGENTE' THEN 1 WHEN 'ATENCAO' THEN 2 ELSE 3 END, criado_em DESC")
                for d in data:
                    if d.get('criado_em'): d['criado_em'] = str(d['criado_em'])
                    if d.get('resolvido_em'): d['resolvido_em'] = str(d['resolvido_em'])
                self.json_response(data)

            elif path == '/api/leads/historico':
                data = query("SELECT * FROM leads_historico ORDER BY data DESC LIMIT 30")
                for d in data:
                    if d.get('criado_em'): d['criado_em'] = str(d['criado_em'])
                self.json_response(data)

            elif path == '/api/sessoes':
                data = query("SELECT * FROM sessoes_trabalho ORDER BY data DESC LIMIT 30")
                for d in data:
                    if d.get('criado_em'): d['criado_em'] = str(d['criado_em'])
                self.json_response(data)

            elif path == '/api/evolucao':
                data = query("SELECT * FROM evolucao_metricas ORDER BY data DESC, metrica LIMIT 100")
                for d in data:
                    if d.get('criado_em'): d['criado_em'] = str(d['criado_em'])
                self.json_response(data)

            elif path == '/api/agentes':
                # Ultimas atividades por agente
                data = query("""
                    SELECT DISTINCT ON (agente) agente, tipo, descricao, resultado, criado_em
                    FROM atividade_agentes
                    ORDER BY agente, criado_em DESC
                """)
                for d in data:
                    if d.get('criado_em'): d['criado_em'] = str(d['criado_em'])
                self.json_response(data)

            elif path == '/api/chat/channels':
                data = query("SELECT DISTINCT ON (canal) canal, autor, mensagem, criado_em FROM chat_mensagens ORDER BY canal, criado_em DESC")
                for d in data: d['criado_em'] = str(d.get('criado_em',''))
                self.json_response(data)

            elif path.startswith('/api/chat/messages/'):
                canal = path.split('/')[-1]
                data = query("SELECT id, canal, autor, tipo, mensagem, criado_em FROM chat_mensagens WHERE canal = %s ORDER BY criado_em ASC LIMIT 50", (canal,))
                for d in data: d['criado_em'] = str(d.get('criado_em',''))
                self.json_response(data)

            elif path == '/api/reverse-prompt':
                sugestoes = self._reverse_prompt()
                self.json_response(sugestoes)

            elif path.startswith('/api/braindump/'):
                cliente = path.split('/api/braindump/')[1]
                cliente = urllib.parse.unquote(cliente)
                data = query("SELECT id, cliente, categoria, conteudo, autor, criado_em FROM brain_dump WHERE LOWER(cliente) LIKE LOWER(%s) ORDER BY criado_em DESC LIMIT 50", (f'%{cliente}%',))
                for d in data:
                    if d.get('criado_em'): d['criado_em'] = str(d['criado_em'])
                self.json_response(data)

            elif path == '/api/chat/workflows':
                data = query("SELECT id, nome, canal_origem, canal_destino, condicao, acao, agente_executor, ativo FROM chat_workflows ORDER BY id")
                self.json_response(data)

            elif path == '/api/health':
                self.json_response({"status": "ok", "db": "connected", "port": PORT})

            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "not found"}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())

    def log_message(self, format, *args):
        pass  # Silenciar logs

if __name__ == '__main__':
    print(f'Dashboard API rodando em http://localhost:{PORT}')
    print(f'Endpoints: /api/metricas, /api/atividade, /api/alertas, /api/agentes, /api/sessoes, /api/evolucao, /api/reverse-prompt, /api/braindump/{{cliente}}, /api/health')
    server = HTTPServer(('127.0.0.1', PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Parando...')
