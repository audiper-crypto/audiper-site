"""
Pipeline: Pesquisa → Artigo → Publicacao
Roda como scheduled task ou sob demanda.
1. Le orientacoes de pesquisa do banco
2. Pesquisa via DuckDuckGo
3. Gera artigo em HTML (formato blog AUDIPER)
4. Salva no banco + arquivo
5. Commit + push (manual ou automatico)
"""
import psycopg, json, os, datetime

DB_URL = 'postgresql://postgres:audiper2026@localhost:5432/audiper'
BLOG_DIR = 'D:/Site/audiper/blog'
TEMPLATE = 'D:/Site/audiper/blog/_template.html'

def get_conn():
    return psycopg.connect(DB_URL, autocommit=True)

def get_pending_topics(limit=3):
    """Busca temas de pesquisa que ainda nao viraram artigo."""
    with get_conn() as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT op.id, op.publico_alvo, op.tema, op.palavras_chave, op.prioridade
                FROM orientacoes_pesquisa op
                WHERE op.ativo = TRUE
                AND NOT EXISTS (
                    SELECT 1 FROM artigos_blog ab
                    WHERE ab.palavras_chave LIKE '%%' || split_part(op.palavras_chave, ',', 1) || '%%'
                )
                ORDER BY CASE op.prioridade WHEN 'ALTA' THEN 1 WHEN 'MEDIA' THEN 2 ELSE 3 END
                LIMIT %s
            """, (limit,))
            cols = [d[0] for d in c.description]
            return [dict(zip(cols, row)) for row in c.fetchall()]

def search_topic(query, max_results=5):
    """Pesquisa via DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query + ' 2026 Brasil', max_results=max_results))
            return results
    except Exception as e:
        print(f"Erro pesquisa: {e}")
        return []

def generate_slug(titulo):
    """Gera slug para URL do artigo."""
    import re
    slug = titulo.lower()
    slug = re.sub(r'[áàãâ]', 'a', slug)
    slug = re.sub(r'[éèê]', 'e', slug)
    slug = re.sub(r'[íì]', 'i', slug)
    slug = re.sub(r'[óòõô]', 'o', slug)
    slug = re.sub(r'[úù]', 'u', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug[:80]

def register_article(titulo, slug, categoria, resumo, palavras_chave):
    """Registra artigo no banco."""
    with get_conn() as conn:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO artigos_blog (titulo, slug, categoria, resumo, palavras_chave, publicado, data_publicacao)
                VALUES (%s, %s, %s, %s, %s, TRUE, CURRENT_DATE)
                ON CONFLICT (slug) DO NOTHING
                RETURNING id
            """, (titulo, slug, categoria, resumo, palavras_chave))
            row = c.fetchone()
            return row[0] if row else None

def register_research(titulo, categoria, resumo, relevancia='ALTA'):
    """Registra pesquisa no banco."""
    with get_conn() as conn:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO pesquisas (titulo, categoria, resumo, relevancia, virou_artigo)
                VALUES (%s, %s, %s, %s, TRUE)
                RETURNING id
            """, (titulo, categoria, resumo, relevancia))
            return c.fetchone()[0]

def list_pending():
    """Lista temas pendentes."""
    topics = get_pending_topics(10)
    if not topics:
        print("Nenhum tema pendente!")
        return
    print(f"\n{len(topics)} temas pendentes:\n")
    for t in topics:
        print(f"  [{t['prioridade']:5}] {t['publico_alvo']:25} | {t['tema']}")
        print(f"         Palavras-chave: {t['palavras_chave']}")
        print()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_pending()
    else:
        print("Pipeline de Artigos AUDIPER")
        print("Uso: python pipeline_artigos.py list")
        print("      python pipeline_artigos.py generate  (futuro - gera artigos)")
        list_pending()
