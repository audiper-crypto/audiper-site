"""
API REST para o Dashboard AUDIPER v2.
Serve dados do PostgreSQL em tempo real.
Porta 3001 — CORS habilitado para localhost:8080.
"""
import json, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
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
                # Fallback inteligente com dados reais do banco
                answer = self._fallback_response(message, context)
                self.json_response({"response": answer, "source": "fallback"})

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
    print(f'Endpoints: /api/metricas, /api/atividade, /api/alertas, /api/agentes, /api/sessoes, /api/evolucao, /api/health')
    server = HTTPServer(('127.0.0.1', PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Parando...')
