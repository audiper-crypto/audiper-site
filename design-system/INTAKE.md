# Como entregar isso para Claude Design

O Claude Design (claude.ai/design) pede 3 coisas neste formulario. Use os textos abaixo:

---

## 1. Company name and blurb

**AUDIPER -- Auditores e Peritos Independentes**

Firma de auditoria independente de Teresina/PI, registrada no CRC/PI 000023/O desde 1985 (40 anos). Atende auditoria contabil sob NBC TA 200-810, pericia, ICMS, ISO 27001, LGPD e setores ANS/iGaming/concessionarias/terceiro setor. Nosso diferencial e entrega Visual Law: relatorios HTML -> PDF com glassmorphism, dashboards de KPIs, Mapa de Reflexos Regionais em OpenStreetMap, e cronogramas Visual Law. Tambem produzimos Reels institucionais 1080x1920 (HyperFrames + Gemini 3.1 Flash TTS) e propostas comerciais com card dourado de honorarios. Posicionamento canonico: "Auditoria Preventiva. Risco Mapeado, Risco Controlado." -- auditoria como libertacao do gestor, nunca como acusacao.

---

## 2. Link code from your computer (drag-and-drop)

Arrastar a pasta inteira: **`~/audix/audiper-design-system/`**

Estrutura focada em frontend, contem:
- `tokens.css` -- tokens canonicos (paleta, tipografia, radius, shadows)
- `examples/01-dossie-visual-law.html` -- relatorio A4 (capa + Mapa de Reflexos)
- `examples/02-email-premium.html` -- email Gmail-safe (inline styles, tabelas)
- `examples/03-reel-storyboard.html` -- storyboard 4-beat para Reel 1080x1920
- `examples/04-proposta-comercial.html` -- proposta com card dourado
- `components/` -- KPI card, glass card, Mapa de Reflexos, Timeline
- `assets/` -- logo radar (PNG + GIF loop), fotos seniors, rubricas, mapa OSM, textura de capa

---

## 3. Add fonts, logos and assets

Anexar TODA a familia do logo radar (9 variantes, cada uma com uso especifico — ver `components/logo-radar-inventory.html`):

**Animadas (preferencial sempre que o medium suportar):**
- `assets/radar-avatar.gif` (32KB) — **header de email, letterhead PDF, favicon**
- `assets/radar-500-transparent.gif` (94KB) — **hero claret, capa de relatorio, CTA Reel**
- `assets/radar-500.gif` (108KB) — dashboard interno
- `assets/radar-1080.gif` (364KB) — IG carrossel, YouTube thumb, LinkedIn banner
- `assets/logo-radar-loop.gif` (286KB) — loop oficial canonico (ja em GitHub raw publico)
- `assets/radar-scan-200.gif` (280KB) — APENAS materiais ISO 27001 / ciberseguranca

**Estaticas e video:**
- `assets/logo-radar.png` (476KB) — **PDF impresso** (Chromium nao anima GIF no print)
- `assets/logo-audiper.png` — assinatura horizontal com texto
- `assets/radar-loop.mp4` (202KB) — Reels, OBS, HyperFrames

**Cronometro (Reel Remotion component):**
- `assets/cronometro-1x1.png` (1,1MB) — 1080x1080 IG feed
- `assets/cronometro-9x16.png` (1,4MB) — 1080x1920 Reels/Stories
- `assets/cronometro-1x1-midloop.png` (1,6MB) — frame intermediario do loop
- componente Remotion fonte em `_AUDIX/_components/reel-cronometro/`

Outros assets:
- `assets/foto_vitor.jpg` + `assets/foto_ricardo.png` (seniors)
- `assets/rubrica-vitor.png` + `assets/rubrica-ricardo.png` (assinaturas manuscritas)
- `assets/contabil_1240_600.png` (textura premium para capas)
- `assets/mapa_ne_cropped.png` (base OSM Nordeste do Mapa de Reflexos)

Fontes (todas via Google Fonts CDN):
- **Inter** (300/400/500/600/700) -- corpo, tabelas, captions
- **Outfit** (400/500/600/700/800) -- titulos, KPI big, badges
- **Merriweather** (400/700) -- citacoes regulatorias (NBC TA, CPC)
- **JetBrains Mono** (400/600) -- refs (PROP-XYZ), valores tecnicos

---

## 4. Any other notes? (campo livre -- COLE INTEGRAL)

Paleta canonica AUDIPER:
- claret #7a1220 (PRIMARY) + claret-dark #5c0d18 + claret-light #B91C1C
- dourado #c9a962 (ACCENT) + dourado-deep #a16207
- graphite #334155 (corpo) + dark #1e293b (rodape/metadata)
- info azul #1a5276, verde-ok #047857, ambar-warn #d9a441
- paper warm: bg #F6F4F1 + borda #EDE8DC

Tom de voz "auditor sobrio". O auditor nao julga, nao acusa, nao confronta. Apresenta fatos, comunica observacoes, oferece recomendacoes. Frases padrao: "Identificamos a seguinte situacao" / "Recomendamos o fortalecimento" / "Ponto de atencao" / "Solicitamos a gentileza" / "Tempestivamente". JAMAIS usar: "erro grave", "falha", "deficiencia", "irregularidade", "urgente", "imediato", "critico" (em emails), emoji em documentos formais.

Regras visuais inegociaveis:
1. **Logo radar nunca esticado** -- sempre aspect-ratio 1:1 (square com border-radius 50% ou square puro). Usar `object-fit: cover` se precisar enquadrar, nunca `contain` com letterbox.
2. **Glassmorphism com fallback @media print obrigatorio** -- Chromium nao renderiza backdrop-filter em PDF; substituir por rgba solido.
3. **Marca dagua CONFIDENCIAL** diagonal 45 graus, opacity 4%, presente ate aprovacao final do socio.
4. **Tipografia mista institucional** -- Inter (corpo) + Outfit (display) + Merriweather (citacoes) + JetBrains Mono (refs). Webfonts via Google Fonts CDN; em emails, fallback Arial/Helvetica.
5. **Reels usam mostrador de progresso** ( emojis bandeira/dinheiro/foguete + barras solidas) -- unico contexto onde emoji eh permitido.
6. **Anti-IA na copy**: variar tamanho de frases, sem trios forcados, sem "Additionally/Furthermore" em sequencia, sem em-dash excessivo (max 2 por pagina), negrito apenas em normas/valores/contas.
7. **CNAI Vitor = 4711** (NUNCA 4877 -- erro recorrente). CRC firma = 000023/O.
8. **Em emails Gmail-safe**: 100% inline styles, layout em tabelas (nunca div/flexbox), background-color solido (nunca linear-gradient), fontes Arial/Helvetica, max 680px.

Tagline oficial: "Auditoria Preventiva. Risco Mapeado, Risco Controlado. ISO 27001."
WhatsApp: (86) 9 9401-0525 -- audiper.com (sem .br) -- audiper@audiper.com

Quatro formatos canonicos:
- Relatorio/dossie A4 (HTML -> PDF Playwright, margin 0, printBackground true)
- Email Gmail-safe (tabelas inline-styles, max 680px)
- Reel vertical 1080x1920 (HyperFrames + voz Algenib gravelly + violin -14dB)
- Proposta comercial (derivada do dossie A4, 6 paginas, dashboard pg.2, card dourado de honorarios)

Tres patterns canonicos replicaveis:
- Mapa de Reflexos Regionais (5 aneis concentricos sobre OSM Nordeste)
- Dashboard pg.2 (KPI big + mini-bars/donut + period-chip + top-table)
- Timeline Visual Law (linha vertical claret + bolinhas numeradas A-G por fase NBC TA)

Tres tratamentos visuais (ver `components/shadcn-premium.html`):
1. **shadcn flat** -- default em dashboards, formularios, tabelas, propostas. Border-radius 12px, shadow 0 1px 2px rgba(0,0,0,.04), hover transform translateY(-2px).
2. **Glassmorphism** -- hero, capa, overlay sobre gradiente claret. backdrop-filter blur(18px). Fallback @media print rgba(255,255,255,.85) solido obrigatorio.
3. **Skeumorphism** -- USO RESTRITO a capas fisicas, certificados, selos, materiais comemorativos (40 anos), Reel Cronometro. Paper warm + sombra suave + texturas. Nao usar em dashboards/emails/Reels normais.

Iconografia profissional:
- **Padrao novo: lucide SVG inline** (componentes shadcn-premium). stroke-width 1.5 default. cor herdada via currentColor. Zero CDN, funciona offline e em PDF. 16 icones canonicos pre-incluidos (shield, file, chart, map-pin, clock, gavel, star, users, message, check-circle, alert, swap, verified, search, help, monitor).
- **Font Awesome 6.4** continua valido para relatorios A4 que ja embedam o CDN (compat com BADESPI v7).
