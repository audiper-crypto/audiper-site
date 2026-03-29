"""
API REST para o Dashboard AUDIPER v2.
Serve dados do PostgreSQL em tempo real.
Porta 3001 — CORS habilitado para localhost:8080.
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import psycopg

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
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()

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
