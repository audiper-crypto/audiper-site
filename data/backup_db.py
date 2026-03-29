"""
Backup automatico do PostgreSQL AUDIPER.
Salva dump em D:/AUDITORIAS/_backups/ com data no nome.
Manter ultimos 7 backups.
"""
import subprocess, os, datetime, glob

BACKUP_DIR = 'D:/AUDITORIAS/_backups'
PG_BIN = 'C:/Program Files/PostgreSQL/16/bin'
DB_NAME = 'audiper'
DB_USER = 'postgres'
DB_PASS = 'audiper2026'
KEEP_DAYS = 7

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    today = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
    filename = f'{BACKUP_DIR}/audiper_backup_{today}.sql'

    env = os.environ.copy()
    env['PGPASSWORD'] = DB_PASS

    pg_dump = os.path.join(PG_BIN, 'pg_dump.exe')
    if not os.path.exists(pg_dump):
        # Tentar sem path completo
        pg_dump = 'pg_dump'

    cmd = [pg_dump, '-h', 'localhost', '-U', DB_USER, '-d', DB_NAME, '-f', filename]

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            size = os.path.getsize(filename)
            print(f'Backup OK: {filename} ({size//1024}KB)')
            cleanup_old()
            return filename
        else:
            print(f'Erro: {result.stderr[:200]}')
            return None
    except Exception as e:
        print(f'Erro: {e}')
        return None

def cleanup_old():
    """Remove backups com mais de KEEP_DAYS dias."""
    files = sorted(glob.glob(f'{BACKUP_DIR}/audiper_backup_*.sql'))
    while len(files) > KEEP_DAYS:
        old = files.pop(0)
        os.remove(old)
        print(f'  Removido backup antigo: {os.path.basename(old)}')

if __name__ == '__main__':
    backup()
