# AUDIPER — Notas de Design e Marca

## Marca

**AUDIPER — Auditores e Peritos Independentes** | CRC/PI 000023/O | CNPJ 23.626.575/0001-10 | Teresina/PI | Desde 1985 (40 anos).

Dois bracos:
- **AUDIPER Auditoria** — auditoria independente, pericia, consultoria contabil/fiscal (core).
- **AUDIX** — sites, auditoria ISO 27001, LGPD, marketing digital (extensao).

## Paleta canonica

| Token | Hex | Uso |
|---|---|---|
| `--audiper-claret-dark` | `#5c0d18` | gradientes profundos, footer |
| `--audiper-claret` | `#7a1220` | **PRIMARY** — header, sec-title, KPI |
| `--audiper-claret-light` | `#B91C1C` | gradientes capa, accent alerta |
| `--audiper-gold` | `#c9a962` | **ACCENT** — premium, badges, divisores |
| `--audiper-gold-deep` | `#a16207` | texto sobre fundo dourado |
| `--audiper-graphite` | `#334155` | corpo de texto |
| `--audiper-dark` | `#1e293b` | metadata bar, rodape escuro |
| `--audiper-blue-info` | `#1a5276` | cards info, callouts azuis |
| `--audiper-green-ok` | `#047857` | positivo, conformidade |
| `--audiper-amber-warn` | `#d9a441` | observacao (NAO "ressalva" — termo reservado NBC TA 705) |
| `--paper-bg` | `#F6F4F1` | fundo paper warm de dashboards |
| `--paper-stone` | `#EDE8DC` | borda warm em dcards |

Regras de uso:
- Vermelho claret nunca em ambiente saturado, sempre como ancora de hierarquia.
- Dourado e divisor (linha de 1-2px), nunca preenchimento de area grande.
- Verde e ambar sao status, nao decoracao.

## Tipografia

| Familia | Pesos | Uso |
|---|---|---|
| **Inter** | 300, 400, 500, 600, 700 | corpo, captions, tabelas |
| **Outfit** | 400, 500, 600, 700, 800 | H1-H6, KPI big, badges |
| **Merriweather** | 400, 700 | citacoes regulatorias (NBC TA, CPC) |
| **JetBrains Mono** | 400, 600 | refs (PROP-XYZ-2026/01), valores monetarios em tabelas tecnicas |

Escala otimizada para A4 (pt) + tela (rem equivalente em tokens.css):
- KPI big = 18pt (24px), H2 capa = 24pt, H1 capa = 36pt.
- Corpo = 10pt (13.3px), small = 8.5pt, micro = 7pt (labels).

## Tom de voz — "Auditor sobrio"

O auditor **nao julga, nao acusa, nao confronta**. Apresenta fatos, comunica observacoes, oferece recomendacoes.

| Situacao | USAR | NUNCA usar |
|---|---|---|
| Problema | "Identificamos a seguinte situacao" | "Erro grave" / "Falha" |
| Controle fraco | "Recomendamos o fortalecimento" | "Deficiencia" |
| Risco | "Ponto de atencao" | "Critico" (em emails) |
| Solicitar | "Solicitamos a gentileza de" | "Cobramos" / "Exigimos" |
| Achado grave | "Situacao que requer providencias" | "Irregularidade" |
| Prazo | "Tempestivamente" / "ate [data], caso possivel" | "Urgente" / "Imediato" |

Tagline oficial: **"Auditoria Preventiva. Risco Mapeado, Risco Controlado. ISO 27001."**

Posicionamento: auditoria como **libertacao do gestor**, nunca como acusacao. AUDIPER vem para "fale com peritos" + "40 anos" + antecipacao regulatoria.

### Anti-IA (obrigatorio em qualquer copy gerada)
- Variar tamanho de frases e paragrafos.
- Sem trios forcados (X, Y e Z artificiais).
- Sem "Additionally / Furthermore / Moreover" em sequencia.
- Negrito apenas em normas, valores e contas contabeis.
- Em-dash maximo 2 por pagina.
- Conclusoes concretas (nunca "the future looks bright").
- **Zero emoji** em documentos corporativos. Reels podem ter mostrador de progresso ( 🏁💰🚀 + 🟩⬜ ) — apenas la.

## Logo radar — regra inegociavel

**O logo radar nunca pode ser esticado.** Sempre aspect-ratio 1:1.

### Inventario oficial (9 variantes — ver `components/logo-radar-inventory.html`)

| Arquivo | Peso | Tipo | Uso preferencial |
|---|---|---|---|
| `assets/radar-avatar.gif` | 32 KB | GIF redondo small | **Headers/footers email (40px)** &middot; letterhead PDF (18-28px) &middot; favicon &middot; avatar TG/IG |
| `assets/radar-500-transparent.gif` | 94 KB | GIF 500x500 transparente | **Hero claret** &middot; capa de relatorio sobre gradiente &middot; CTA Reel beat 4 |
| `assets/radar-500.gif` | 108 KB | GIF 500x500 opaco | Dashboard interno &middot; thumbnail &middot; container sem cor de marca |
| `assets/radar-1080.gif` | 364 KB | GIF 1080x1080 hi-res | Carrossel IG &middot; thumbnail YT &middot; banner LinkedIn &middot; hero shot Reel |
| `assets/logo-radar-loop.gif` | 286 KB | GIF loop oficial | GitHub raw publico para emails HTML hospedados |
| `assets/radar-scan-200.gif` | 280 KB | GIF com efeito scan | **APENAS ciberseguranca / ISO 27001 / Audix** |
| `assets/radar-scan.gif` | 611 KB | GIF scan hi-res | Mesmo de scan-200 em hi-res |
| `assets/logo-radar.png` | 476 KB | PNG estatico | **PDF impresso** (Chromium nao anima GIF no print) &middot; Word &middot; Excel &middot; PowerPoint |
| `assets/radar-loop.mp4` | 202 KB | MP4 H.264 | Reels (Higgsfield/Veo bumper) &middot; OBS &middot; HyperFrames &middot; transicoes |

### Quando usar GIF vs PNG vs MP4

- **Web / email / app** → GIF (animacao funciona em 99% dos clientes Gmail/Outlook/Apple Mail).
- **PDF impresso ou exportado** → PNG (Chromium congela GIF no print — frame 0 fica esquisito).
- **Video / overlay OBS / Reels** → MP4 (melhor compressao + suporte a alpha).
- **GitHub raw publico** → `logo-radar-loop.gif` (ja indexado em `raw.githubusercontent.com/audiper-crypto/audiper-site`).

### CSS canonico

```css
.logo-radar {
  aspect-ratio: 1 / 1;     /* OBRIGATORIO */
  object-fit: cover;        /* nunca contain com letterbox */
  border-radius: 50%;       /* circular padrao; quadrado puro tambem aceito */
  border: 3px solid rgba(201,169,98,.55); /* aro dourado opcional em fundo claret */
}
```

### Tamanhos pre-aprovados

| Contexto | Tamanho | Variante |
|---|---|---|
| Footer A4 / Reel bumper | 18px | radar-avatar.gif |
| Header letterhead A4 | 28px | radar-avatar.gif |
| Email header Gmail-safe | 40px | radar-avatar.gif |
| Capa secundaria | 64px | radar-500-transparent.gif |
| Capa principal A4 | 80-96px | radar-500-transparent.gif |
| Hero web / Reel beat 4 | 140-160px | radar-500-transparent.gif ou radar-1080.gif |

### Versao horizontal (textual)

`assets/logo-audiper.png` — assinatura horizontal AUDIPER com texto. Usar quando o layout exige logo extenso (rodape de email institucional, cabecalho de PTA). **Nunca tentar transformar o radar em horizontal esticando.**

## Glassmorphism canonico

- `backdrop-filter: blur(16px)` em fundo `rgba(255,255,255,.6)` ou `rgba(30,41,59,.4)`.
- Borda translucida 1px branca a 30% opacity.
- Shadow `0 8px 32px rgba(0,0,0,.08)`.
- **Fallback @media print obrigatorio** — Chromium nao renderiza backdrop-filter em PDF; substituir por `rgba(255,255,255,.85)` solido.

## Tres patterns canonicos

### 1. Mapa de Reflexos Regionais
Mapa OSM cropped do Nordeste + 5 aneis concentricos (Nucleo AUDIPER → Capital → Entorno → Estado → Regiao) + pinos lat/lon dos clientes ativos.

Cores dos aneis: claret (1), claret-light (2), dourado (3), azul-info (4), verde-ok (5). Animacao `pulse` 3s com delays escalonados (.4s, .8s, 1.2s, 1.6s).

### 2. Dashboard pg.2 (KPI + cruzamentos)
Linha superior: 3 dcards com KPI big + mini-bars ou donut + period-chip. Segunda linha: tabela top-5 + grafico (donut ou bars). Padrao "Rocha Filho pg.2".

### 3. Timeline Visual Law
Linha vertical claret + bolinhas numeradas + cards `.tl-item`. Cada milestone com data, titulo, status pill, descricao curta.

## Reels (1080x1920 vertical)

Pattern oficial "audix-reel-informativo" — 4 beats:
1. **Gancho** (0-8s) — pergunta-gancho cyberpunk com tint claret.
2. **Obrigacoes / dados** (8-25s) — KPIs piscando, citacao normativa.
3. **Multa / consequencia** (25-50s) — escalar com counter animado.
4. **CTA** (50-82s) — "fale com peritos" + logo radar loop + WA.

Voz oficial: **Algenib** (Gemini 3.1 Flash TTS, gravelly grave rouca, ~2 palavras/segundo). Fallback: Gacrux.
BGM oficial: violin instrumental, -14dB sob voz a 0dB.
Atmo: cyberpunk com tint claret claro, sem saturar.

## Stack tecnico

- **Tailwind CSS via CDN** (relatorios A4).
- **Google Fonts** Inter + Outfit + Merriweather + JetBrains Mono.
- **Font Awesome 6.4** para iconografia.
- **Playwright** para HTML -> PDF (`page.pdf({ format: 'A4', margin: 0, printBackground: true, preferCSSPageSize: true })`).
- **HyperFrames CLI 0.4.45** para Reels.
- **Gmail-safe HTML** (tabelas, inline styles) para emails — NUNCA copiar CSS de dashboards para emails.

## Erros recorrentes a evitar

- Esticar logo radar (achatado ou alongado) — proibido.
- Usar "ressalva" para observacao — "ressalva" e termo NBC TA 705 (opiniao modificada).
- CNAI Vitor 4877 — esta errado. Oficial: **4711**.
- backdrop-filter em PDF sem fallback — cards somem no print.
- Emoji em documentos formais — apenas em Reels.
- linear-gradient em emails — Gmail rasga, usa background-color solido.
