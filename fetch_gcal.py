"""
fetch_gcal.py — Busca eventos do Google Calendar via gws CLI e salva em dashboard-data.json.
Executar: python fetch_gcal.py
Requer: gws CLI autenticado (npm -g gws)
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR  = Path(__file__).parent
DATA_FILE = BASE_DIR / 'dashboard-data.json'


def run_gws(params: dict) -> dict:
    cmd = f'gws calendar events list --params {json.dumps(json.dumps(params))}'
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', shell=True)
    output = result.stdout
    # remover linha do keyring
    lines = [l for l in output.split('\n') if not l.startswith('Using keyring')]
    return json.loads('\n'.join(lines))


def classify(summary: str, desc: str = '') -> str:
    text = (summary + ' ' + (desc or '')).lower()
    if any(w in text for w in ['prazo','deadline','defis','sped','ecd','ecf','dctf','pgdas','multa','vencimento']):
        return 'prazo'
    if any(w in text for w in ['reuni','meeting','kick','apresenta','visita']):
        return 'reuniao'
    if any(w in text for w in ['entrega','relat','cvm','nota fiscal','emiss','envio','declarac','declaraç']):
        return 'entrega'
    return 'pta'


def fetch_events(days_ahead: int = 90) -> list:
    now = datetime.now(timezone.utc)
    params = {
        'calendarId': 'primary',
        'timeMin': now.isoformat(),
        'timeMax': (now + timedelta(days=days_ahead)).isoformat(),
        'maxResults': 100,
        'singleEvents': True,
        'orderBy': 'startTime',
    }
    data = run_gws(params)
    events = []
    for item in data.get('items', []):
        summary  = item.get('summary', '(sem título)')
        desc_raw = item.get('description', '') or ''
        desc     = re.sub(r'<[^>]+>', '', desc_raw)[:100].strip()
        start    = item.get('start', {})
        date_str = start.get('date') or start.get('dateTime', '')[:10]
        events.append({
            'date':   date_str,
            'type':   classify(summary, desc),
            'label':  summary[:50],
            'detail': desc or summary,
            'source': 'gcal',
        })
    return events


def update_dashboard(events: list):
    data = {}
    if DATA_FILE.exists():
        data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
    data['gcal_events']   = events
    data['gcal_updated']  = datetime.now().isoformat()
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[gcal] {len(events)} eventos salvos em {DATA_FILE.name}')


if __name__ == '__main__':
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    print(f'[gcal] Buscando eventos (próximos {days} dias)...')
    events = fetch_events(days)
    update_dashboard(events)
    for e in events[:15]:
        print(f"  {e['date']} [{e['type']:8}] {e['label']}")
    if len(events) > 15:
        print(f'  ... (+{len(events)-15} mais)')
