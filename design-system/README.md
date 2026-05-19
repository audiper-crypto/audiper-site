# AUDIPER — Design System

Pacote canonico de identidade visual da AUDIPER (Auditores e Peritos Independentes, CRC/PI 000023/O, Teresina/PI, desde 1985).

Este repositorio existe para alimentar ferramentas de IA generativa (Claude Design, Stitch, etc.) com a DNA visual correta antes de qualquer geracao automatica.

## Estrutura

```
audiper-design-system/
|-- README.md            <- este arquivo
|-- INTAKE.md            <- texto pronto para colar no formulario Claude Design
|-- notes.md             <- paleta + tom de voz + principios
|-- tokens.css           <- tokens canonicos (cores, tipografia, radius)
|-- examples/
|   |-- 01-dossie-visual-law.html    <- relatorio A4 com Mapa de Reflexos
|   |-- 02-email-premium.html        <- email Gmail-safe (inline styles)
|   |-- 03-reel-storyboard.html      <- Reel vertical 1080x1920 (4 beats)
|   |-- 04-proposta-comercial.html   <- proposta auditoria 6 paginas
|-- components/
|   |-- kpi-card.html
|   |-- glass-card.html
|   |-- mapa-reflexos.html
|   |-- timeline-visual-law.html
|-- assets/
    |-- logo-radar.png + logo-radar-loop.gif (loop 4s — NUNCA esticar)
    |-- logo-audiper.png (horizontal)
    |-- foto_vitor.jpg + foto_ricardo.png (seniors)
    |-- rubrica-vitor.png + rubrica-ricardo.png (assinaturas manuscritas)
    |-- contabil_1240_600.png (textura de capa)
    |-- mapa_ne_cropped.png (mapa base OSM para Mapa de Reflexos)
```

## DNA em uma frase

Visual Law glassmorphism, paleta claret + dourado, tom de auditor sobrio. Cada peca comunica antecipacao e controle, nunca acusacao.

## Quatro formatos canonicos

1. **Relatorio / Dossie A4** (HTML -> PDF via Playwright, margin 0, printBackground true) — paginacao pill claret, marca dagua CONFIDENCIAL diagonal opacity 4%, glassmorphism com fallback @media print.
2. **Email Gmail-safe** — 100% inline styles, tabelas, max 680px, fontes Arial/Helvetica, sem gradient (Gmail rasga).
3. **Reel vertical 1080x1920** — HyperFrames HTML, estrutura 4-beat (gancho → dados → multa → CTA), voz Algenib (Gemini 3.1 Flash TTS), BGM violin -14dB.
4. **Proposta comercial** — derivada do dossie A4, 6 paginas, dashboard pg.2, timeline Visual Law, card dourado de honorarios.

## Regras inegociaveis

- Logo radar nunca esticar — sempre aspect-ratio 1:1 (square ou circle com `object-fit: cover`).
- Marca dagua CONFIDENCIAL ate aprovacao final do socio.
- Tom de voz: "Identificamos a seguinte situacao" — nunca "erro grave" / "falha" / "irregularidade".
- Cor primaria: `#7a1220` (claret). Accent: `#c9a962` (dourado). Sem desvios.
- Tipografia: Inter (corpo) + Outfit (display) + Merriweather (citacoes regulatorias) + JetBrains Mono (refs).
- Sem emoji em documentos formais. Sem exclamacao em comunicacoes tecnicas.
- CNAI Vitor = 4711 (NUNCA 4877). CRC firma 000023/O.

## Como usar este pacote em IA generativa

1. Abrir `INTAKE.md` e copiar o bloco "Notes" no campo livre da ferramenta.
2. Anexar a pasta inteira (drag-and-drop) ou apontar para o repositorio.
3. Reforcar regra critica: "logo radar nunca esticar — sempre 1:1".

## Versionamento

- v1.0 — 2026-05-19 — extracao do canonico Pleito BADESPI Inovacao v7.
