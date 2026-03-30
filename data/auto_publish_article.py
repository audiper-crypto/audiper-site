"""
Pipeline automatizado: Pesquisa -> Artigo -> Publicacao no blog AUDIPER.

Uso:
    python auto_publish_article.py           # gera 1 artigo
    python auto_publish_article.py --count 3 # gera 3 artigos
    python auto_publish_article.py --list    # lista temas pendentes
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import textwrap
import unicodedata

import psycopg2

# ---------------------------------------------------------------------------
# Configuracao
# ---------------------------------------------------------------------------
DB_URL = "postgresql://postgres:audiper2026@localhost:5432/audiper"
BLOG_DIR = "D:/Site/audiper/blog"
TEMPLATE_PATH = "D:/Site/audiper/blog/_template.html"
REPO_DIR = "D:/Site/audiper"

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_URL)


def get_pending_topics(limit=10):
    """Retorna temas de orientacoes_pesquisa que ainda nao possuem artigo."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT op.id, op.publico_alvo, op.tema, op.palavras_chave,
                   op.tipo_conteudo, op.prioridade
            FROM orientacoes_pesquisa op
            WHERE op.ativo = TRUE
              AND NOT EXISTS (
                  SELECT 1 FROM artigos_blog ab
                  WHERE ab.titulo = op.tema
              )
            ORDER BY
                CASE op.prioridade
                    WHEN 'ALTA' THEN 1
                    WHEN 'MEDIA' THEN 2
                    ELSE 3
                END,
                op.id
            LIMIT %s
        """, (limit,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def register_research(titulo, categoria, resumo, fontes_json):
    """Registra a pesquisa no banco e retorna o id."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO pesquisas (titulo, categoria, resumo, fonte, relevancia, virou_artigo, artigo_url)
            VALUES (%s, %s, %s, %s, 'ALTA', TRUE, NULL)
            RETURNING id
        """, (titulo, categoria, resumo, fontes_json))
        pesquisa_id = cur.fetchone()[0]
        conn.commit()
        return pesquisa_id
    finally:
        conn.close()


def register_article(titulo, slug, categoria, resumo, palavras_chave, pesquisa_id):
    """Registra o artigo no banco e atualiza a pesquisa."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO artigos_blog (titulo, slug, categoria, resumo, palavras_chave,
                                      pesquisa_id, publicado, data_publicacao)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE, CURRENT_DATE)
            ON CONFLICT (slug) DO NOTHING
            RETURNING id
        """, (titulo, slug, categoria, resumo, palavras_chave, pesquisa_id))
        row = cur.fetchone()
        if row:
            artigo_id = row[0]
            cur.execute(
                "UPDATE pesquisas SET virou_artigo = TRUE, artigo_url = %s WHERE id = %s",
                (f"blog/{slug}.html", pesquisa_id),
            )
            conn.commit()
            return artigo_id
        conn.commit()
        return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Pesquisa web
# ---------------------------------------------------------------------------

def search_web(query, max_results=8):
    """Pesquisa via DuckDuckGo e retorna lista de resultados."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(
                f"{query} 2026 Brasil auditoria contabilidade",
                max_results=max_results,
            ))
            return results
    except Exception as e:
        print(f"  [AVISO] Erro na pesquisa web: {e}")
        return []


def build_research_context(results):
    """Extrai pontos-chave dos resultados de pesquisa."""
    context_parts = []
    for i, r in enumerate(results[:6], 1):
        title = r.get("title", "")
        body = r.get("body", "")
        if body:
            context_parts.append(f"- {title}: {body[:200]}")
    return "\n".join(context_parts)


# ---------------------------------------------------------------------------
# Geracao de slug
# ---------------------------------------------------------------------------

def generate_slug(titulo):
    """Gera slug URL-safe a partir do titulo."""
    # Remover acentos
    nfkd = unicodedata.normalize("NFKD", titulo)
    slug = "".join(c for c in nfkd if not unicodedata.combining(c))
    slug = slug.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug[:60]


# ---------------------------------------------------------------------------
# Geracao do artigo HTML
# ---------------------------------------------------------------------------

def infer_category(tema, palavras_chave):
    """Infere a categoria do artigo com base no tema."""
    tema_lower = tema.lower()
    kw = (palavras_chave or "").lower()
    combined = tema_lower + " " + kw

    if any(w in combined for w in ["tribut", "imposto", "reforma", "ibs", "cbs", "split", "defis"]):
        return "Reforma Tributaria"
    if any(w in combined for w in ["pericia", "calculo", "judicial", "revisao", "bancari"]):
        return "Pericia Contabil"
    if any(w in combined for w in ["fraude", "compliance", "controle", "governanca", "anticorrup"]):
        return "Compliance"
    if any(w in combined for w in ["ia ", "inteligencia artificial", "machine", "automat", "rpa", "dados"]):
        return "Tecnologia"
    if any(w in combined for w in ["lgpd", "privacidade", "dados pessoais"]):
        return "LGPD"
    if any(w in combined for w in ["esg", "sustentab"]):
        return "ESG"
    return "Auditoria Contabil"


def estimate_reading_time(text):
    """Estima tempo de leitura em minutos."""
    words = len(text.split())
    return max(3, round(words / 200))


def generate_article_body(tema, context, palavras_chave):
    """Gera o corpo do artigo em HTML com base no contexto pesquisado.

    O conteudo e gerado localmente, sem IA externa, a partir dos dados
    coletados na pesquisa. O resultado sao 4-5 secoes com linguagem
    acessivel para empresarios.
    """
    kw_list = [k.strip() for k in (palavras_chave or "").split(",") if k.strip()]
    primary_kw = kw_list[0] if kw_list else tema.split(":")[0].strip()

    # Extrair insights dos resultados de pesquisa
    insights = []
    for line in context.split("\n"):
        line = line.strip("- ").strip()
        if line and len(line) > 30:
            insights.append(line)

    # Montar secoes do artigo
    sections = _build_article_sections(tema, primary_kw, kw_list, insights)

    # Montar HTML
    html_parts = []
    for title, paragraphs in sections:
        html_parts.append(f"          <h2>{title}</h2>")
        for p in paragraphs:
            html_parts.append(f"          <p>{p}</p>")

    # Highlight box
    html_parts.append("""
          <div class="highlight-box">
            <h4>Ponto de atencao para gestores</h4>
            <p>Empresas que adotam boas praticas de governanca e contabilidade transparente
            possuem maior facilidade de acesso a credito, melhor relacao com investidores
            e menor exposicao a riscos regulatorios.</p>
          </div>""")

    # CTA final
    html_parts.append("""
          <h2>Proximo passo</h2>
          <p>Se a sua empresa precisa de orientacao especializada sobre esse tema,
          a AUDIPER pode ajudar. Com mais de 40 anos de experiencia em auditoria
          independente e pericia contabil, nossa equipe esta preparada para atender
          empresas de todos os portes no Nordeste.</p>
          <p><strong>Fale com um auditor:</strong> entre em contato pelo WhatsApp
          <a href="https://wa.me/5586981251918">(86) 98125-1918</a> ou envie um
          e-mail para <a href="mailto:audiper@audiper.com">audiper@audiper.com</a>.</p>""")

    return "\n".join(html_parts)


def _build_article_sections(tema, primary_kw, kw_list, insights):
    """Constroi as secoes do artigo com variacao de tamanho e tom AUDIPER."""
    sections = []

    # Secao 1 — Introducao / Contexto
    intro_paragraphs = [
        f"O tema \"{tema.lower()}\" tem ganhado relevancia entre gestores e "
        f"contadores nos ultimos meses. A conjuntura economica e as mudancas "
        f"regulatorias de 2025 e 2026 tornaram esse assunto ainda mais presente "
        f"no dia a dia das empresas brasileiras.",

        f"Para empresarios que acompanham o cenario contabil e tributario, "
        f"entender os fundamentos de {primary_kw.lower()} deixou de ser opcional. "
        f"Trata-se de uma questao que afeta desde a apuracao de tributos ate "
        f"a tomada de decisoes estrategicas.",
    ]
    sections.append(("O que muda no cenario atual", intro_paragraphs))

    # Secao 2 — Conceitos / Como funciona
    concept_paragraphs = []
    if insights:
        concept_paragraphs.append(
            f"Segundo levantamentos recentes, {insights[0][:180]}."
            if len(insights[0]) > 40
            else f"Dados recentes indicam mudancas significativas nesse campo."
        )
    concept_paragraphs.append(
        f"Na pratica, {primary_kw.lower()} envolve uma serie de procedimentos "
        f"que variam conforme o porte da empresa, o regime tributario adotado "
        f"e o setor de atuacao. Empresas do Simples Nacional, por exemplo, "
        f"possuem obrigacoes diferentes das que operam no Lucro Real."
    )
    concept_paragraphs.append(
        f"O ponto central e que a legislacao brasileira exige atencao constante. "
        f"Normas emitidas pelo CFC, pela Receita Federal e por orgaos reguladores "
        f"setoriais podem alterar procedimentos de um exercicio para outro."
    )
    sections.append(("Como funciona na pratica", concept_paragraphs))

    # Secao 3 — Impacto para empresas
    impact_paragraphs = [
        f"Para empresas de pequeno e medio porte, a principal preocupacao costuma "
        f"ser o impacto financeiro. Multas por descumprimento de obrigacoes "
        f"acessorias, glosas fiscais e autuacoes representam riscos concretos "
        f"que podem comprometer o fluxo de caixa.",

        f"Ja para empresas maiores, o foco tende a recair sobre a governanca. "
        f"Investidores, bancos e parceiros comerciais exigem demonstracoes "
        f"contabeis auditadas e controles internos robustos. Nesse contexto, "
        f"contar com uma auditoria independente nao e custo — e protecao.",
    ]
    if len(insights) > 1:
        impact_paragraphs.append(
            f"Alem disso, {insights[1][:160]}."
            if len(insights[1]) > 40
            else f"Estudos apontam que empresas com controles adequados apresentam "
                 f"menor incidencia de fraudes e desvios."
        )
    sections.append(("Impacto para a sua empresa", impact_paragraphs))

    # Secao 4 — O que fazer / Recomendacoes
    action_paragraphs = [
        f"O primeiro passo e fazer um diagnostico da situacao atual da empresa. "
        f"Isso inclui revisar obrigacoes fiscais pendentes, verificar a "
        f"conformidade das demonstracoes contabeis e mapear os principais "
        f"riscos do negocio.",

        f"Em seguida, vale considerar o apoio de profissionais especializados. "
        f"Um auditor independente consegue identificar vulnerabilidades que "
        f"passam despercebidas no dia a dia e propor ajustes antes que se "
        f"tornem problemas graves.",

        f"Empresas que investem em prevencao — seja por meio de auditoria "
        f"preventiva, consultoria tributaria ou adequacao a normas — "
        f"costumam obter retornos significativos em economia fiscal e "
        f"reducao de passivos.",
    ]
    sections.append(("O que sua empresa pode fazer agora", action_paragraphs))

    return sections


def build_related_links(categoria, current_slug):
    """Busca artigos relacionados da mesma categoria."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT titulo, slug FROM artigos_blog
            WHERE publicado = TRUE AND slug != %s
            ORDER BY data_publicacao DESC NULLS LAST
            LIMIT 5
        """, (current_slug,))
        links = []
        for titulo, slug in cur.fetchall():
            links.append(
                f'            <li><a href="{slug}.html">'
                f'<span class="material-symbols-outlined">article</span> '
                f'{titulo[:50]}</a></li>'
            )
        return "\n".join(links) if links else '<li><a href="../blog.html">Ver todos os artigos</a></li>'
    finally:
        conn.close()


def build_related_cards(current_slug):
    """Monta cards de artigos relacionados."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT titulo, slug, categoria, resumo FROM artigos_blog
            WHERE publicado = TRUE AND slug != %s
            ORDER BY data_publicacao DESC NULLS LAST
            LIMIT 3
        """, (current_slug,))
        cards = []
        for titulo, slug, cat, resumo in cur.fetchall():
            short_resumo = (resumo or titulo)[:100]
            cards.append(f"""      <div class="col-md-4">
        <div class="related-card">
          <span class="tag">{cat or 'Artigo'}</span>
          <h5>{titulo[:60]}</h5>
          <p>{short_resumo}</p>
          <a href="{slug}.html">Ler artigo <i class="fa-solid fa-arrow-right"></i></a>
        </div>
      </div>""")
        return "\n".join(cards)
    finally:
        conn.close()


def build_html(titulo, slug, meta_desc, keywords, category, tag, date_iso,
               date_display, reading_time, article_body, related_links,
               related_cards, hero_title, breadcrumb_short):
    """Preenche o template HTML com os dados do artigo."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    filename = f"{slug}.html"
    title_encoded = titulo.replace(" ", "%20")

    replacements = {
        "{{TITLE}}": titulo,
        "{{META_DESCRIPTION}}": meta_desc,
        "{{FILENAME}}": filename,
        "{{KEYWORDS}}": keywords,
        "{{CATEGORY}}": category,
        "{{HERO_TITLE}}": hero_title,
        "{{BREADCRUMB_SHORT}}": breadcrumb_short,
        "{{TAG}}": tag,
        "{{DATE_ISO}}": date_iso,
        "{{DATE_DISPLAY}}": date_display,
        "{{READING_TIME}}": str(reading_time),
        "{{ARTICLE_BODY}}": article_body,
        "{{RELATED_LINKS}}": related_links,
        "{{RELATED_CARDS}}": related_cards,
        "{{TITLE_ENCODED}}": title_encoded,
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

def git_add_commit(slug):
    """Faz git add e commit do artigo gerado."""
    filepath = f"blog/{slug}.html"
    try:
        subprocess.run(
            ["git", "add", filepath],
            cwd=REPO_DIR, capture_output=True, text=True, check=True,
        )
        msg = f"feat(blog): publicar artigo {slug}"
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=REPO_DIR, capture_output=True, text=True, check=True,
        )
        print(f"  [GIT] Commit realizado: {msg}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [GIT] Erro: {e.stderr.strip()}")
        return False


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def process_topic(topic):
    """Executa o pipeline completo para um tema."""
    tema = topic["tema"]
    palavras_chave = topic.get("palavras_chave", "")
    publico = topic.get("publico_alvo", "empresarios")

    print(f"\n{'='*60}")
    print(f"  Tema: {tema}")
    print(f"  Publico: {publico}")
    print(f"{'='*60}")

    # 1. Gerar slug e verificar se ja existe
    slug = generate_slug(tema)
    filepath = os.path.join(BLOG_DIR, f"{slug}.html")
    if os.path.exists(filepath):
        print(f"  [SKIP] Arquivo ja existe: {filepath}")
        return False

    # 2. Pesquisar na web
    print("  [1/5] Pesquisando na web...")
    results = search_web(tema)
    context = build_research_context(results)
    fontes_json = json.dumps(
        [{"title": r.get("title", ""), "href": r.get("href", "")} for r in results[:5]],
        ensure_ascii=False,
    )

    # 3. Registrar pesquisa no banco
    print("  [2/5] Registrando pesquisa...")
    categoria = infer_category(tema, palavras_chave)
    resumo_pesq = context[:300] if context else f"Pesquisa sobre {tema}"
    pesquisa_id = register_research(tema, categoria, resumo_pesq, fontes_json)

    # 4. Gerar artigo
    print("  [3/5] Gerando artigo HTML...")
    today = datetime.date.today()
    date_iso = today.isoformat()
    meses = [
        "", "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    ]
    date_display = f"{today.day} de {meses[today.month]} de {today.year}"

    article_body = generate_article_body(tema, context, palavras_chave)
    reading_time = estimate_reading_time(article_body)

    meta_desc = (
        f"{tema}. Entenda o impacto para sua empresa e saiba como se preparar. "
        f"Artigo da AUDIPER - Auditores e Peritos Associados."
    )[:160]

    # Hero com italico na parte principal
    parts = tema.split(":")
    if len(parts) > 1:
        hero_title = f"{parts[0]}: <em>{parts[1].strip()}</em>"
    else:
        words = tema.split()
        mid = len(words) // 2
        hero_title = " ".join(words[:mid]) + " <em>" + " ".join(words[mid:]) + "</em>"

    breadcrumb_short = tema[:40] + ("..." if len(tema) > 40 else "")

    related_links = build_related_links(categoria, slug)
    related_cards = build_related_cards(slug)

    html = build_html(
        titulo=tema,
        slug=slug,
        meta_desc=meta_desc,
        keywords=palavras_chave or tema.lower(),
        category=categoria,
        tag=categoria.upper().replace(" ", " "),
        date_iso=date_iso,
        date_display=date_display,
        reading_time=reading_time,
        article_body=article_body,
        related_links=related_links,
        related_cards=related_cards,
        hero_title=hero_title,
        breadcrumb_short=breadcrumb_short,
    )

    # 5. Salvar arquivo
    print(f"  [4/5] Salvando {filepath}...")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    # 6. Registrar artigo no banco
    register_article(
        titulo=tema,
        slug=slug,
        categoria=categoria,
        resumo=meta_desc,
        palavras_chave=palavras_chave or tema.lower(),
        pesquisa_id=pesquisa_id,
    )
    print(f"  [5/5] Artigo registrado no banco.")

    # 7. Git add + commit
    git_add_commit(slug)

    print(f"\n  Publicado: blog/{slug}.html")
    print(f"  URL: https://audiper.com/blog/{slug}.html")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def list_pending():
    """Mostra temas pendentes de publicacao."""
    topics = get_pending_topics(20)
    if not topics:
        print("\nNenhum tema pendente. Todos os temas ja possuem artigo.")
        return

    print(f"\n{len(topics)} tema(s) pendente(s):\n")
    print(f"  {'#':>3}  {'Prioridade':10}  {'Publico':25}  Tema")
    print(f"  {'---':>3}  {'----------':10}  {'-'*25}  {'-'*40}")
    for i, t in enumerate(topics, 1):
        prio = t.get("prioridade", "MEDIA")
        pub = t.get("publico_alvo", "-")[:25]
        print(f"  {i:3}  {prio:10}  {pub:25}  {t['tema']}")
        if t.get("palavras_chave"):
            print(f"       {'':10}  {'':25}  KW: {t['palavras_chave']}")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline pesquisa -> artigo -> blog AUDIPER"
    )
    parser.add_argument("--list", action="store_true", help="Lista temas pendentes")
    parser.add_argument("--count", type=int, default=1, help="Quantidade de artigos a gerar (padrao: 1)")
    args = parser.parse_args()

    if args.list:
        list_pending()
        return

    topics = get_pending_topics(args.count)
    if not topics:
        print("Nenhum tema pendente para gerar artigo.")
        return

    print(f"Gerando {len(topics)} artigo(s)...\n")
    ok = 0
    for topic in topics:
        try:
            if process_topic(topic):
                ok += 1
        except Exception as e:
            print(f"  [ERRO] {topic['tema']}: {e}")

    print(f"\n{'='*60}")
    print(f"  Resultado: {ok}/{len(topics)} artigo(s) publicado(s)")
    print(f"  Para enviar ao servidor: cd {REPO_DIR} && git push origin master")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
