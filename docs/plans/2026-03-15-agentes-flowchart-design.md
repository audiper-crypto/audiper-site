# Fluxograma de Agentes IA - Design Doc

**Data**: 2026-03-15
**Pagina**: audiper.com/agentes.html
**Objetivo**: Pagina institucional publica mostrando o ecossistema de 146 agentes IA da Audiper em pipeline de 7 fases

## Stack

- HTML/CSS puro + GSAP (scroll animations) + SVG (conexoes)
- Paleta: preto #0a0a0a, vermelho neon #ff3333, dourado #d4a843, branco #f5f5f5
- Responsivo: pipeline horizontal (desktop) / vertical (mobile)
- Segue padrao 8-space indent das paginas regulares

## Estrutura

### 1. Hero
- Fundo preto, titulo "Ecossistema de Agentes IA" com glow vermelho
- Subtitulo "146 agentes especializados orquestrando cada fase da auditoria"
- Breadcrumb: Home > IA para Negocios > Agentes IA

### 2. Stats Bar (scroll-animated counters)
- 146 agentes | 12 divisoes | 7 fases | 7 NBCs cobertas

### 3. Pipeline (7 fases)
Nos hexagonais conectados por linhas SVG animadas com particulas:

```
Descoberta -> Estrategia -> Fundacao -> Construcao -> Hardening -> Lancamento -> Operacao
```

Cada no: icone Material Symbols + nome + cor gradiente preto->vermelho

### 4. Paineis expansiveis por fase
Clique em fase -> abre painel com cards dos agentes + conexoes internas SVG

| Fase | Agentes | Icone |
|------|---------|-------|
| Descoberta | discovery-coach, trend-researcher, feedback-synthesizer, competitive-intel | search |
| Estrategia | proposal-strategist, deal-strategist, account-strategist, ceo-advisor, cfo-advisor | strategy |
| Fundacao | backend-architect, software-architect, database-optimizer, security-engineer, brand-guardian | foundation |
| Construcao | frontend-developer, ai-engineer, mcp-builder, data-engineer, rapid-prototyper, document-generator + 7 agentes BR (auditor-senior-br, contabil-societario, tributario, testes-substantivos, setorial-regulatorio, controles-internos, dossie-cre) | build |
| Hardening | code-reviewer, reality-checker, evidence-collector, compliance-auditor, api-tester, performance-benchmarker, accessibility-auditor | shield |
| Lancamento | devops-automator, seo-specialist, content-creator, linkedin-content-creator, carousel-growth-engine, growth-hacker | rocket_launch |
| Operacao | agents-orchestrator, project-shepherd, workflow-optimizer, finance-tracker, support-responder, executive-summary-generator | settings |

### 5. Conexoes inter-fase (SVG tracejado)
- compliance-auditor (Hardening) <-> auditor-senior-br (Construcao)
- code-reviewer (Hardening) <-> backend-architect (Fundacao)
- content-creator (Lancamento) <-> brand-guardian (Fundacao)
- agents-orchestrator (Operacao) -> todas as fases (linhas radiais)

### 6. Agentes BR - Destaque especial
Cards com badge dourado NBC TA (ex: "NBC TA 200-810"), borda dourada

### 7. Footer
Footer padrao do site (3 colunas)

## Dependencias externas
- GSAP 3.x (CDN, ~30KB gzip) - scroll trigger + animacoes
- Material Symbols (ja no site)
- Font Awesome (ja no site)
- Fonts: Figtree, Inter, JetBrains Mono (ja no site)

## SEO
- Conteudo no HTML semantico (nao canvas)
- Meta description focada em "agentes IA auditoria"
- JSON-LD SoftwareApplication schema
