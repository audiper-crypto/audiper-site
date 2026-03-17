# Fluxograma Agentes IA - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Criar pagina publica `agentes.html` com pipeline visual de 7 fases mostrando 146 agentes IA da Audiper, com conexoes inter-fase animadas e paineis expansiveis.

**Architecture:** Pagina HTML estatica seguindo o padrao das 67 paginas regulares (8-space indent). Pipeline horizontal (desktop) / vertical (mobile) com nos hexagonais SVG. Paineis expansiveis via JS vanilla. Animacoes GSAP ScrollTrigger (ja no site). Conexoes inter-fase via SVG paths animados com CSS.

**Tech Stack:** HTML5, CSS3 (custom properties, grid, flexbox), SVG inline, GSAP 3.x + ScrollTrigger (js/gsap.min.js + js/ScrollTrigger.min.js ja existem), Material Symbols (ja no site), Bootstrap 5 (ja no site).

---

### Task 1: Criar esqueleto HTML com head, nav e footer

**Files:**
- Create: `D:/Site/audiper/agentes.html`
- Reference: `D:/Site/audiper/ia-negocios.html` (copiar estrutura head/nav/footer)

**Step 1: Criar o arquivo com head completo**

Copiar de ia-negocios.html:
- `<head>` inteiro (meta, fonts, css) trocando title/description/canonical/og para "Agentes IA"
- Navbar identico (trocar `active` para o link "IA & Data Intelligence")
- Footer identico
- Scripts identicos (jquery, gsap, ScrollTrigger, bootstrap, main.js, gs-animations.js)
- Adicionar `<link>` para `css/agentes.css` (sera criado na Task 2)
- Body contem: nav + hero section vazio + footer + scripts

**Step 2: Verificar que carrega sem erros**

Run: `npx http-server D:/Site/audiper -p 8080`
Abrir: http://localhost:8080/agentes.html
Expected: Pagina com nav e footer funcionando, conteudo vazio

**Step 3: Commit**

```bash
cd D:/Site/audiper && git add agentes.html && git commit -m "feat: add agentes.html skeleton with nav and footer"
```

---

### Task 2: Criar CSS dedicado (agentes.css)

**Files:**
- Create: `D:/Site/audiper/css/agentes.css`

**Step 1: Escrever o CSS completo**

Sections:
1. **Custom properties** - cores, fontes, espacamento
2. **Hero dark** - fundo #0a0a0a, texto branco, glow vermelho
3. **Stats bar** - flex row, JetBrains Mono counters, separadores
4. **Pipeline** - horizontal scroll container, nos hexagonais, linhas SVG
5. **Phase nodes** - hexagono CSS (clip-path), gradiente, hover glow
6. **Agent panels** - grid de cards, slide-down animation
7. **Agent cards** - fundo escuro, borda vermelha hover, badge NBC dourado
8. **Inter-phase connections** - SVG overlay, dash animation
9. **Orchestrator radials** - linhas do orchestrator para todas as fases
10. **Responsive** - breakpoints 1200, 991, 768, 576
11. **Animations** - keyframes para glow pulse, dash flow, fade-in-up

```css
/* === Custom Properties === */
:root {
  --ag-bg: #0a0a0a;
  --ag-bg-card: #141414;
  --ag-red: #ff3333;
  --ag-red-glow: rgba(255, 51, 51, 0.4);
  --ag-gold: #d4a843;
  --ag-gold-glow: rgba(212, 168, 67, 0.3);
  --ag-white: #f5f5f5;
  --ag-gray: #888;
  --ag-border: rgba(255, 255, 255, 0.08);
  --ag-font-display: 'Figtree', sans-serif;
  --ag-font-body: 'Inter', sans-serif;
  --ag-font-mono: 'JetBrains Mono', monospace;
}

/* === Hero Dark === */
.ag-hero {
  background: var(--ag-bg);
  padding: 160px 0 80px;
  position: relative;
  overflow: hidden;
}
.ag-hero .badge-label {
  font-family: var(--ag-font-mono);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--ag-red);
  letter-spacing: 3px;
  text-transform: uppercase;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.ag-hero .badge-label::before {
  content: '';
  width: 32px;
  height: 2px;
  background: var(--ag-red);
}
.ag-hero h1 {
  font-family: var(--ag-font-display);
  font-size: clamp(2rem, 4vw, 3.2rem);
  font-weight: 900;
  color: #fff;
  line-height: 1.15;
  margin-bottom: 16px;
}
.ag-hero h1 .accent {
  color: var(--ag-red);
  text-shadow: 0 0 30px var(--ag-red-glow);
}
.ag-hero h1 em {
  font-family: 'Fraunces', serif;
  font-style: italic;
  font-weight: 600;
  color: var(--ag-red);
}
.ag-hero p {
  font-family: var(--ag-font-body);
  font-size: 1.05rem;
  color: var(--ag-gray);
  max-width: 600px;
  line-height: 1.7;
}
.ag-hero .breadcrumb {
  margin-top: 24px;
  padding: 0;
  background: none !important;
}
.ag-hero .breadcrumb a { color: #666; text-decoration: none; font-size: 0.9rem; }
.ag-hero .breadcrumb a:hover { color: var(--ag-red); }
.ag-hero .breadcrumb span { color: #444; margin: 0 8px; }
.ag-hero .breadcrumb .current { color: var(--ag-red); font-size: 0.9rem; }

/* === Stats Bar === */
.ag-stats {
  background: var(--ag-bg);
  border-top: 1px solid var(--ag-border);
  border-bottom: 1px solid var(--ag-border);
  padding: 40px 0;
}
.ag-stats-row {
  display: flex;
  justify-content: center;
  gap: 48px;
  flex-wrap: wrap;
}
.ag-stat {
  text-align: center;
}
.ag-stat .number {
  font-family: var(--ag-font-mono);
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--ag-red);
  display: block;
  line-height: 1;
}
.ag-stat .label {
  font-family: var(--ag-font-body);
  font-size: 0.85rem;
  color: var(--ag-gray);
  margin-top: 4px;
}

/* === Pipeline Section === */
.ag-pipeline-section {
  background: var(--ag-bg);
  padding: 80px 0 40px;
  position: relative;
}
.ag-pipeline-title {
  font-family: var(--ag-font-mono);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--ag-red);
  letter-spacing: 3px;
  text-transform: uppercase;
  text-align: center;
  margin-bottom: 48px;
}

/* Pipeline Track */
.ag-pipeline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 40px 20px;
  position: relative;
  overflow-x: auto;
}

/* Connector Lines */
.ag-connector {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, var(--ag-red), rgba(255, 51, 51, 0.3));
  position: relative;
  flex-shrink: 0;
}
.ag-connector::after {
  content: '';
  position: absolute;
  top: -1px;
  left: 0;
  width: 20px;
  height: 4px;
  background: var(--ag-red);
  border-radius: 2px;
  animation: ag-flow 2s linear infinite;
  box-shadow: 0 0 8px var(--ag-red-glow);
}

/* Phase Nodes (Hexagon) */
.ag-phase {
  flex-shrink: 0;
  text-align: center;
  cursor: pointer;
  position: relative;
  z-index: 2;
}
.ag-phase-hex {
  width: 100px;
  height: 100px;
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  background: linear-gradient(135deg, #1a1a1a, #2a0a0a);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  transition: all 0.3s ease;
  position: relative;
}
.ag-phase-hex::before {
  content: '';
  position: absolute;
  inset: -3px;
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  background: linear-gradient(135deg, var(--ag-red), #660000);
  z-index: -1;
  transition: all 0.3s ease;
}
.ag-phase:hover .ag-phase-hex::before,
.ag-phase.active .ag-phase-hex::before {
  background: var(--ag-red);
  box-shadow: 0 0 30px var(--ag-red-glow);
}
.ag-phase-hex .material-symbols-outlined {
  font-size: 36px;
  color: var(--ag-red);
  transition: all 0.3s;
}
.ag-phase:hover .ag-phase-hex .material-symbols-outlined,
.ag-phase.active .ag-phase-hex .material-symbols-outlined {
  color: #fff;
  text-shadow: 0 0 12px var(--ag-red-glow);
}
.ag-phase-label {
  font-family: var(--ag-font-display);
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--ag-white);
  white-space: nowrap;
}
.ag-phase-count {
  font-family: var(--ag-font-mono);
  font-size: 0.7rem;
  color: var(--ag-gray);
  margin-top: 2px;
}

/* === Agent Panels === */
.ag-panels-section {
  background: var(--ag-bg);
  padding: 0 0 80px;
}
.ag-panel {
  display: none;
  padding: 40px 0;
  animation: ag-slideDown 0.4s ease;
}
.ag-panel.active {
  display: block;
}
.ag-panel-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--ag-border);
}
.ag-panel-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(255, 51, 51, 0.15), rgba(255, 51, 51, 0.05));
  display: flex;
  align-items: center;
  justify-content: center;
}
.ag-panel-icon .material-symbols-outlined {
  font-size: 24px;
  color: var(--ag-red);
}
.ag-panel-title {
  font-family: var(--ag-font-display);
  font-weight: 800;
  font-size: 1.4rem;
  color: #fff;
}
.ag-panel-desc {
  font-family: var(--ag-font-body);
  font-size: 0.9rem;
  color: var(--ag-gray);
}

/* Agent Cards Grid */
.ag-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
.ag-card {
  background: var(--ag-bg-card);
  border: 1px solid var(--ag-border);
  border-radius: 12px;
  padding: 24px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.ag-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--ag-red), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}
.ag-card:hover {
  border-color: rgba(255, 51, 51, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(255, 51, 51, 0.1);
}
.ag-card:hover::before {
  opacity: 1;
}
.ag-card-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(255, 51, 51, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.ag-card-icon .material-symbols-outlined {
  font-size: 20px;
  color: var(--ag-red);
}
.ag-card h5 {
  font-family: var(--ag-font-display);
  font-weight: 700;
  font-size: 0.95rem;
  color: #fff;
  margin-bottom: 6px;
}
.ag-card p {
  font-family: var(--ag-font-body);
  font-size: 0.82rem;
  color: var(--ag-gray);
  line-height: 1.6;
  margin: 0;
}

/* NBC Badge (gold) for BR audit agents */
.ag-badge-nbc {
  display: inline-block;
  font-family: var(--ag-font-mono);
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--ag-gold);
  background: rgba(212, 168, 67, 0.1);
  border: 1px solid rgba(212, 168, 67, 0.3);
  padding: 2px 8px;
  border-radius: 4px;
  margin-top: 8px;
}
.ag-card.ag-card-br {
  border-color: rgba(212, 168, 67, 0.2);
}
.ag-card.ag-card-br:hover {
  border-color: var(--ag-gold);
  box-shadow: 0 8px 32px var(--ag-gold-glow);
}
.ag-card.ag-card-br::before {
  background: linear-gradient(90deg, transparent, var(--ag-gold), transparent);
}

/* === Inter-Phase Connections SVG === */
.ag-connections-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}
.ag-connection-line {
  stroke: var(--ag-red);
  stroke-width: 1.5;
  stroke-dasharray: 8 4;
  fill: none;
  opacity: 0.4;
  animation: ag-dash 3s linear infinite;
}
.ag-connection-line.gold {
  stroke: var(--ag-gold);
}
.ag-connection-orch {
  stroke: rgba(255, 51, 51, 0.2);
  stroke-width: 1;
  stroke-dasharray: 4 8;
  fill: none;
  animation: ag-dash 4s linear infinite;
}

/* === CTA Section === */
.ag-cta {
  background: linear-gradient(135deg, #c41a1a, #e32018);
  padding: 80px 0;
  text-align: center;
}
.ag-cta h2 {
  font-family: var(--ag-font-display);
  font-weight: 800;
  color: #fff;
  font-size: clamp(1.5rem, 3vw, 2.2rem);
  margin-bottom: 16px;
}
.ag-cta p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.05rem;
  margin-bottom: 32px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}
.ag-cta .btn-white {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  color: #c41a1a;
  font-family: var(--ag-font-display);
  font-weight: 700;
  font-size: 1rem;
  padding: 14px 32px;
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.3s;
}
.ag-cta .btn-white:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

/* === Animations === */
@keyframes ag-flow {
  0% { left: -20px; }
  100% { left: calc(100% + 20px); }
}
@keyframes ag-slideDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes ag-dash {
  to { stroke-dashoffset: -24; }
}
@keyframes ag-glow-pulse {
  0%, 100% { box-shadow: 0 0 20px var(--ag-red-glow); }
  50% { box-shadow: 0 0 40px var(--ag-red-glow), 0 0 60px rgba(255, 51, 51, 0.2); }
}
@keyframes ag-fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

/* === Responsive === */
@media (max-width: 1200px) {
  .ag-pipeline { gap: 0; padding: 40px 10px; }
  .ag-connector { width: 40px; }
  .ag-phase-hex { width: 80px; height: 80px; }
  .ag-phase-hex .material-symbols-outlined { font-size: 28px; }
}
@media (max-width: 991px) {
  .ag-hero { padding: 120px 0 60px; }
  .ag-pipeline {
    flex-direction: column;
    gap: 0;
    padding: 20px;
  }
  .ag-connector {
    width: 2px;
    height: 40px;
    background: linear-gradient(180deg, var(--ag-red), rgba(255, 51, 51, 0.3));
  }
  .ag-connector::after {
    width: 4px;
    height: 20px;
    top: 0;
    left: -1px;
    animation: ag-flow-v 2s linear infinite;
  }
  .ag-phase-hex { width: 80px; height: 80px; }
  .ag-cards { grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
}
@media (max-width: 576px) {
  .ag-stats-row { gap: 24px; }
  .ag-stat .number { font-size: 2rem; }
  .ag-phase-hex { width: 70px; height: 70px; }
  .ag-phase-hex .material-symbols-outlined { font-size: 24px; }
  .ag-phase-label { font-size: 0.75rem; }
  .ag-cards { grid-template-columns: 1fr; }
}
@keyframes ag-flow-v {
  0% { top: -20px; }
  100% { top: calc(100% + 20px); }
}
```

**Step 2: Commit**

```bash
cd D:/Site/audiper && git add css/agentes.css && git commit -m "feat: add agentes.css with full pipeline styling"
```

---

### Task 3: Construir Hero section + Stats bar

**Files:**
- Modify: `D:/Site/audiper/agentes.html` (inserir conteudo no body)

**Step 1: Adicionar Hero com fundo escuro**

```html
<!-- Hero -->
<section class="ag-hero">
  <div class="container">
    <div class="badge-label">ECOSSISTEMA DE IA</div>
    <h1>Nossos <span class="accent">Agentes</span> de <em>Inteligencia Artificial</em></h1>
    <p>146 agentes especializados orquestrando cada fase da auditoria. Da descoberta a operacao, cada agente domina seu campo e colabora com os demais em um pipeline inteligente.</p>
    <div class="breadcrumb">
      <a href="index.html">Inicio</a> <span>/</span>
      <a href="ia-negocios.html">IA para Negocios</a> <span>/</span>
      <span class="current">Agentes IA</span>
    </div>
  </div>
</section>
```

**Step 2: Adicionar Stats bar com contadores**

```html
<!-- Stats -->
<section class="ag-stats">
  <div class="container">
    <div class="ag-stats-row">
      <div class="ag-stat">
        <span class="number" data-target="146">0</span>
        <span class="label">Agentes</span>
      </div>
      <div class="ag-stat">
        <span class="number" data-target="12">0</span>
        <span class="label">Divisoes</span>
      </div>
      <div class="ag-stat">
        <span class="number" data-target="7">0</span>
        <span class="label">Fases</span>
      </div>
      <div class="ag-stat">
        <span class="number" data-target="7">0</span>
        <span class="label">NBCs Cobertas</span>
      </div>
    </div>
  </div>
</section>
```

**Step 3: Preview e commit**

Run: `npx http-server D:/Site/audiper -p 8080`
Expected: Hero escuro com glow vermelho + stats bar visivel

```bash
cd D:/Site/audiper && git add agentes.html && git commit -m "feat: add hero and stats bar to agentes page"
```

---

### Task 4: Construir Pipeline visual com 7 fases

**Files:**
- Modify: `D:/Site/audiper/agentes.html`

**Step 1: Adicionar pipeline HTML**

Cada fase: hexagono clicavel com icone Material Symbols + label + contagem de agentes.
Fases separadas por conectores animados.

```html
<!-- Pipeline -->
<section class="ag-pipeline-section">
  <div class="container">
    <div class="ag-pipeline-title">Pipeline de Auditoria Inteligente</div>
    <div class="ag-pipeline">
      <!-- Fase 1 -->
      <div class="ag-phase" data-phase="descoberta">
        <div class="ag-phase-hex"><span class="material-symbols-outlined">search</span></div>
        <div class="ag-phase-label">Descoberta</div>
        <div class="ag-phase-count">4 agentes</div>
      </div>
      <div class="ag-connector"></div>
      <!-- Fase 2 -->
      <div class="ag-phase" data-phase="estrategia">
        <div class="ag-phase-hex"><span class="material-symbols-outlined">strategy</span></div>
        <div class="ag-phase-label">Estrategia</div>
        <div class="ag-phase-count">5 agentes</div>
      </div>
      <div class="ag-connector"></div>
      <!-- Fase 3 -->
      <div class="ag-phase" data-phase="fundacao">
        <div class="ag-phase-hex"><span class="material-symbols-outlined">foundation</span></div>
        <div class="ag-phase-label">Fundacao</div>
        <div class="ag-phase-count">5 agentes</div>
      </div>
      <div class="ag-connector"></div>
      <!-- Fase 4 -->
      <div class="ag-phase" data-phase="construcao">
        <div class="ag-phase-hex"><span class="material-symbols-outlined">build</span></div>
        <div class="ag-phase-label">Construcao</div>
        <div class="ag-phase-count">13 agentes</div>
      </div>
      <div class="ag-connector"></div>
      <!-- Fase 5 -->
      <div class="ag-phase" data-phase="hardening">
        <div class="ag-phase-hex"><span class="material-symbols-outlined">shield</span></div>
        <div class="ag-phase-label">Hardening</div>
        <div class="ag-phase-count">7 agentes</div>
      </div>
      <div class="ag-connector"></div>
      <!-- Fase 6 -->
      <div class="ag-phase" data-phase="lancamento">
        <div class="ag-phase-hex"><span class="material-symbols-outlined">rocket_launch</span></div>
        <div class="ag-phase-label">Lancamento</div>
        <div class="ag-phase-count">6 agentes</div>
      </div>
      <div class="ag-connector"></div>
      <!-- Fase 7 -->
      <div class="ag-phase" data-phase="operacao">
        <div class="ag-phase-hex"><span class="material-symbols-outlined">settings</span></div>
        <div class="ag-phase-label">Operacao</div>
        <div class="ag-phase-count">6 agentes</div>
      </div>
    </div>
  </div>
</section>
```

**Step 2: Commit**

```bash
cd D:/Site/audiper && git add agentes.html && git commit -m "feat: add 7-phase pipeline to agentes page"
```

---

### Task 5: Construir paineis de agentes (7 paineis com cards)

**Files:**
- Modify: `D:/Site/audiper/agentes.html`

**Step 1: Adicionar os 7 paineis com todos os agentes**

Cada painel contem header + grid de cards. Agentes BR de auditoria usam classe `.ag-card-br` com badge NBC dourado.

Conteudo completo dos 7 paineis:

**Descoberta (4):** Discovery Coach, Trend Researcher, Feedback Synthesizer, Competitive Intel
**Estrategia (5):** Proposal Strategist, Deal Strategist, Account Strategist, CEO Advisor, CFO Advisor
**Fundacao (5):** Backend Architect, Software Architect, Database Optimizer, Security Engineer, Brand Guardian
**Construcao (13):** Frontend Developer, AI Engineer, MCP Builder, Data Engineer, Rapid Prototyper, Document Generator + 7 BR (Auditor Senior BR, Contabil-Societario, Tributario, Testes Substantivos, Setorial-Regulatorio, Controles Internos, Dossie CRE)
**Hardening (7):** Code Reviewer, Reality Checker, Evidence Collector, Compliance Auditor, API Tester, Performance Benchmarker, Accessibility Auditor
**Lancamento (6):** DevOps Automator, SEO Specialist, Content Creator, LinkedIn Content Creator, Carousel Growth Engine, Growth Hacker
**Operacao (6):** Agents Orchestrator, Project Shepherd, Workflow Optimizer, Finance Tracker, Support Responder, Executive Summary Generator

Cada card: icone Material Symbols relevante, nome, descricao curta (1 linha), badge NBC para BR agents.

**Step 2: Commit**

```bash
cd D:/Site/audiper && git add agentes.html && git commit -m "feat: add 7 agent panels with 46 cards"
```

---

### Task 6: Adicionar JavaScript (interatividade + animacoes)

**Files:**
- Create: `D:/Site/audiper/js/agentes.js`
- Modify: `D:/Site/audiper/agentes.html` (adicionar script tag)

**Step 1: Criar agentes.js com toda a logica**

```javascript
// agentes.js - Pipeline interativo
(function() {
  'use strict';

  // 1. Counter animation (ScrollTrigger)
  // Animar .ag-stat .number de 0 ate data-target
  // Usar GSAP ScrollTrigger onEnter

  // 2. Phase click -> toggle panel
  // Clicar .ag-phase -> adiciona .active, mostra .ag-panel correspondente
  // Fecha panel anterior

  // 3. GSAP ScrollTrigger reveals
  // Pipeline nos: stagger fade-in da esquerda
  // Cards: stagger fade-in-up quando painel abre

  // 4. Auto-open primeira fase apos scroll
})();
```

Funcionalidades:
- **counterAnimation()**: GSAP ScrollTrigger que anima contadores de 0 a N
- **phaseToggle()**: click handler nos hexagonos, toggle .active, mostra/esconde painel
- **revealAnimations()**: GSAP stagger para nos do pipeline
- **autoOpenFirst()**: apos 1s de scroll ate pipeline, abre fase 1

**Step 2: Adicionar `<script src="js/agentes.js"></script>` antes do `</body>`**

**Step 3: Testar interatividade**

Run: `npx http-server D:/Site/audiper -p 8080`
Expected:
- Contadores animam ao scroll
- Clicar hexagono abre painel abaixo
- Clicar outro hexagono fecha anterior e abre novo
- Particulas fluem nos conectores

**Step 4: Commit**

```bash
cd D:/Site/audiper && git add js/agentes.js agentes.html && git commit -m "feat: add interactive JS for pipeline and counters"
```

---

### Task 7: Adicionar conexoes inter-fase SVG + CTA + JSON-LD

**Files:**
- Modify: `D:/Site/audiper/agentes.html`

**Step 1: Adicionar SVG de conexoes inter-fase**

SVG overlay no pipeline mostrando:
- compliance-auditor (Hardening) <-> auditor-senior-br (Construcao) [gold]
- code-reviewer (Hardening) <-> backend-architect (Fundacao) [red]
- content-creator (Lancamento) <-> brand-guardian (Fundacao) [red]
- agents-orchestrator (Operacao) -> todas as fases (linhas radiais) [red dim]

**Step 2: Adicionar CTA section**

```html
<section class="ag-cta">
  <div class="container">
    <h2>Quer ver nossos agentes em acao?</h2>
    <p>Agende uma demonstracao e descubra como a IA pode transformar sua auditoria.</p>
    <a href="contato.html" class="btn-white">
      <span>Agendar Demonstracao</span>
      <span class="material-symbols-outlined">arrow_forward</span>
    </a>
  </div>
</section>
```

**Step 3: Adicionar JSON-LD schema no head**

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "AUDIPER Ecossistema de Agentes IA",
  "applicationCategory": "BusinessApplication",
  "description": "146 agentes de IA especializados...",
  "provider": { "@type": "Organization", "name": "AUDIPER" }
}
```

**Step 4: Preview final e commit**

```bash
cd D:/Site/audiper && git add agentes.html && git commit -m "feat: add SVG connections, CTA section, and JSON-LD schema"
```

---

### Task 8: Review visual no browser + ajustes finais

**Files:**
- Possibly modify: `D:/Site/audiper/css/agentes.css`, `D:/Site/audiper/agentes.html`, `D:/Site/audiper/js/agentes.js`

**Step 1: Abrir preview**

Run: `npx http-server D:/Site/audiper -p 8080`

**Step 2: Checklist visual**

- [ ] Hero: glow vermelho visivel, texto legivel
- [ ] Stats: contadores animam ao scroll
- [ ] Pipeline: 7 hexagonos visiveis desktop horizontal
- [ ] Pipeline: mobile vertical funciona
- [ ] Click hexagono: painel abre com slide-down
- [ ] Cards: hover com borda vermelha
- [ ] Cards BR: borda e badge dourados
- [ ] Conectores: particulas fluindo
- [ ] CTA: botao funcional link correto
- [ ] Nav: link ativo em "IA & Data Intelligence"
- [ ] Footer: 3 colunas corretas
- [ ] Mobile 576px: layout vertical, cards 1 coluna

**Step 3: Ajustar qualquer issue encontrado**

**Step 4: Commit final**

```bash
cd D:/Site/audiper && git add -A && git commit -m "feat: agentes.html - final visual adjustments"
```
