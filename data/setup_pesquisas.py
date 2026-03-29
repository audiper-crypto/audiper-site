"""Criar tabelas de pesquisas e artigos no PostgreSQL e indexar conteudo existente."""
import psycopg, os

conn = psycopg.connect('postgresql://postgres:audiper2026@localhost:5432/audiper')
conn.autocommit = True
c = conn.cursor()

# Tabela pesquisas (briefings noturnos)
c.execute("""CREATE TABLE IF NOT EXISTS pesquisas (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    categoria VARCHAR(50),
    titulo TEXT NOT NULL,
    resumo TEXT,
    fonte TEXT,
    relevancia VARCHAR(10) DEFAULT 'MEDIA',
    virou_artigo BOOLEAN DEFAULT FALSE,
    artigo_url TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
)""")
c.execute("CREATE INDEX IF NOT EXISTS idx_pesquisas_cat ON pesquisas(categoria, data DESC)")
print("pesquisas OK")

# Tabela artigos blog
c.execute("""CREATE TABLE IF NOT EXISTS artigos_blog (
    id SERIAL PRIMARY KEY,
    titulo TEXT NOT NULL,
    slug TEXT UNIQUE,
    categoria VARCHAR(50),
    resumo TEXT,
    palavras_chave TEXT,
    pesquisa_id INTEGER REFERENCES pesquisas(id),
    publicado BOOLEAN DEFAULT FALSE,
    data_publicacao DATE,
    criado_em TIMESTAMP DEFAULT NOW()
)""")
print("artigos_blog OK")

# Indexar pesquisas do Obsidian
pesq_count = 0
vault = "D:/Site/obsidian-vault"
for root, dirs, files in os.walk(vault):
    for f in files:
        if f.endswith(".md") and "pesquisa" in root.replace("\\", "/").lower():
            nome = f.replace(".md", "").replace("_", " ").replace("-", " ")
            path = os.path.join(root, f).replace("\\", "/")
            # Categoria do diretorio
            rel = root.replace("\\", "/").replace(vault + "/", "")
            parts = [p for p in rel.split("/") if p and p != "pesquisa"]
            cat = parts[-1] if parts else "geral"
            try:
                c.execute("INSERT INTO pesquisas (titulo, categoria, fonte) VALUES (%s, %s, %s)", (nome, cat, path))
                pesq_count += 1
            except Exception as e:
                pass
print(f"{pesq_count} pesquisas indexadas")

# Indexar artigos do blog
art_count = 0
blog_dir = "D:/Site/audiper/blog"
for f in os.listdir(blog_dir):
    if f.endswith(".html") and f != "_template.html":
        slug = f.replace(".html", "")
        titulo = slug.replace("-", " ").title()
        try:
            c.execute("INSERT INTO artigos_blog (titulo, slug, publicado, data_publicacao) VALUES (%s, %s, TRUE, CURRENT_DATE)", (titulo, slug))
            art_count += 1
        except:
            pass
print(f"{art_count} artigos indexados")

# Verificar
for t in ["pesquisas", "artigos_blog"]:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {c.fetchone()[0]} registros")

conn.close()
print("Concluido!")
