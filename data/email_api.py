"""
Micro API de emails para o dashboard AUDIPER.
Roda na porta 3001, retorna os 5 emails mais recentes em JSON.
Usa credenciais OAuth do Gmail (mesmo token do n8n).
"""
import json, os, sys, base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Gmail API
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

PORT = 3001
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = Path(__file__).parent / 'gmail_token.json'
CREDS_PATH = Path(__file__).parent / 'gmail_credentials.json'

def get_gmail_service():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_recent_emails(service, max_results=5):
    results = service.users().messages().list(
        userId='me', maxResults=max_results, q='is:inbox'
    ).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        headers = {h['name']: h['value'] for h in detail.get('payload', {}).get('headers', [])}
        from_raw = headers.get('From', '')
        # Extract name from "Name <email>" format
        if '<' in from_raw:
            from_name = from_raw.split('<')[0].strip().strip('"')
            from_email = from_raw.split('<')[1].rstrip('>')
        else:
            from_name = from_raw
            from_email = from_raw
        emails.append({
            'id': msg['id'],
            'from_name': from_name,
            'from_email': from_email,
            'subject': headers.get('Subject', '(sem assunto)'),
            'date': headers.get('Date', ''),
            'snippet': detail.get('snippet', '')[:100],
            'unread': 'UNREAD' in detail.get('labelIds', []),
        })
    return emails

class EmailHandler(BaseHTTPRequestHandler):
    service = None

    def do_GET(self):
        if self.path.startswith('/api/emails'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                if not EmailHandler.service:
                    EmailHandler.service = get_gmail_service()
                if not EmailHandler.service:
                    self.wfile.write(json.dumps({'error': 'Gmail nao configurado', 'emails': []}).encode())
                    return
                emails = get_recent_emails(EmailHandler.service)
                self.wfile.write(json.dumps({'emails': emails, 'count': len(emails)}).encode())
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e), 'emails': []}).encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'ok')
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Silenciar logs

if __name__ == '__main__':
    print(f'Email API rodando em http://localhost:{PORT}')
    print(f'Endpoints: /api/emails, /health')
    server = HTTPServer(('127.0.0.1', PORT), EmailHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nParando...')
