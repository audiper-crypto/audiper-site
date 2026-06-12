"""
Inteligencia Competitiva com FireCrawl — AUDIX/AUDIPER
Analisa concorrentes, extrai padroes e gera relatorio.
"""
import json, os, sys
from firecrawl import FirecrawlApp

API_KEY = os.environ.get('FIRECRAWL_API_KEY', '')
app = FirecrawlApp(api_key=API_KEY)

def scrape_site(url):
    """Scrape uma pagina e retorna markdown."""
    print(f"  Scraping {url}...")
    result = app.scrape_url(url)
    if result and result.get('markdown'):
        return result['markdown']
    return None

def analyze_competitor(url):
    """Analisa um concorrente e extrai informacoes chave."""
    md = scrape_site(url)
    if not md:
        return None

    info = {
        'url': url,
        'content_length': len(md),
        'has_whatsapp': 'whatsapp' in md.lower(),
        'has_blog': 'blog' in md.lower(),
        'has_faq': 'faq' in md.lower() or 'pergunt' in md.lower(),
        'has_testimonials': 'depoiment' in md.lower() or 'testemunho' in md.lower(),
        'has_cta': 'contato' in md.lower() or 'orcamento' in md.lower() or 'proposta' in md.lower(),
        'has_lgpd': 'lgpd' in md.lower() or 'privacidade' in md.lower(),
        'content_preview': md[:500],
    }

    # Extrair servicos mencionados
    servicos = []
    keywords = ['auditoria', 'pericia', 'contabil', 'fiscal', 'tributar', 'compliance', 'lgpd', 'consultoria']
    for kw in keywords:
        if kw in md.lower():
            servicos.append(kw)
    info['servicos'] = servicos

    return info

def generate_report(target_url, competitors):
    """Gera relatorio de inteligencia competitiva."""
    print(f"\n{'='*60}")
    print(f"  RELATORIO DE INTELIGENCIA COMPETITIVA")
    print(f"  Site alvo: {target_url}")
    print(f"{'='*60}\n")

    # Analisar site alvo
    print("Analisando site alvo...")
    target = analyze_competitor(target_url)

    # Analisar concorrentes
    results = []
    for url in competitors:
        print(f"\nAnalisando concorrente...")
        info = analyze_competitor(url)
        if info:
            results.append(info)

    # Gerar comparativo
    print(f"\n{'='*60}")
    print(f"  RESULTADO: {len(results)} concorrentes analisados")
    print(f"{'='*60}\n")

    if target:
        print(f"SITE ALVO: {target_url}")
        print(f"  Conteudo: {target['content_length']} caracteres")
        print(f"  Servicos: {', '.join(target['servicos'])}")
        print(f"  WhatsApp: {'Sim' if target['has_whatsapp'] else 'Nao'}")
        print(f"  Blog: {'Sim' if target['has_blog'] else 'Nao'}")
        print(f"  FAQ: {'Sim' if target['has_faq'] else 'Nao'}")
        print(f"  LGPD: {'Sim' if target['has_lgpd'] else 'Nao'}")

    print(f"\nCOMPARATIVO CONCORRENTES:")
    print(f"{'Site':40} {'Conteudo':10} {'WA':4} {'Blog':5} {'FAQ':4} {'CTA':4} {'Servicos'}")
    print("-"*90)
    for r in results:
        print(f"{r['url'][:38]:40} {r['content_length']:>8}  {'Y' if r['has_whatsapp'] else 'N':>3} {'Y' if r['has_blog'] else 'N':>4} {'Y' if r['has_faq'] else 'N':>3} {'Y' if r['has_cta'] else 'N':>3}  {', '.join(r['servicos'][:4])}")

    # Insights
    print(f"\nINSIGHTS:")
    wa_count = sum(1 for r in results if r['has_whatsapp'])
    blog_count = sum(1 for r in results if r['has_blog'])
    faq_count = sum(1 for r in results if r['has_faq'])
    print(f"  WhatsApp: {wa_count}/{len(results)} concorrentes tem")
    print(f"  Blog: {blog_count}/{len(results)} concorrentes tem")
    print(f"  FAQ: {faq_count}/{len(results)} concorrentes tem")

    return {'target': target, 'competitors': results}

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Teste rapido com 1 pagina
        result = scrape_site('https://audiper.com.br')
        if result:
            print(f"OK! {len(result)} caracteres")
            print(result[:200])
    elif len(sys.argv) > 1 and sys.argv[1] == 'audit':
        # Analise do proprio site
        info = analyze_competitor('https://audiper.com.br')
        if info:
            for k, v in info.items():
                if k != 'content_preview':
                    print(f"  {k}: {v}")
    else:
        print("FireCrawl Intelligence AUDIX")
        print("Uso:")
        print("  python firecrawl_intel.py test          — testa scraping")
        print("  python firecrawl_intel.py audit         — audita audiper.com.br")
        print("  python firecrawl_intel.py report <url>  — analisa concorrentes")
