/**
 * AUDIPER Particle System v5 — Cursor Glow + Parallax 3 camadas + Burst + Morphing
 */
(function() {
  'use strict';

  const DPR = Math.min(window.devicePixelRatio || 1, 2);
  const isMobile = window.innerWidth < 768 || ('ontouchstart' in window);

  function throttle(fn, ms) {
    let last = 0;
    return function(...args) { const now = Date.now(); if (now - last >= ms) { last = now; fn.apply(this, args); } };
  }
  function debounce(fn, ms) {
    let timer;
    return function(...args) { clearTimeout(timer); timer = setTimeout(() => fn.apply(this, args), ms); };
  }

  // ========== AURORA ==========
  const aurora = document.getElementById('auroraCanvas');
  if (!aurora) return;
  const actx = aurora.getContext('2d', { alpha: true });
  let aW, aH;
  function resizeAurora() {
    aW = window.innerWidth; aH = window.innerHeight;
    aurora.width = aW * DPR; aurora.height = aH * DPR;
    aurora.style.width = aW + 'px'; aurora.style.height = aH + 'px';
    actx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  resizeAurora();

  class AuroraBlob {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * aW; this.y = Math.random() * aH;
      this.radius = isMobile ? (160 + Math.random() * 280) : (250 + Math.random() * 450);
      this.vx = (Math.random() - 0.5) * 0.3; this.vy = (Math.random() - 0.5) * 0.2;
      this.phase = Math.random() * Math.PI * 2;
      this.speed = 0.001 + Math.random() * 0.002;
      const types = ['red', 'red', 'red', 'dark', 'gold'];
      this.type = types[Math.floor(Math.random() * types.length)];
    }
    update(time) {
      this.x += this.vx + Math.sin(time * this.speed + this.phase) * 0.3;
      this.y += this.vy + Math.cos(time * this.speed * 0.7 + this.phase) * 0.2;
      if (this.x < -this.radius) this.x = aW + this.radius;
      if (this.x > aW + this.radius) this.x = -this.radius;
      if (this.y < -this.radius) this.y = aH + this.radius;
      if (this.y > aH + this.radius) this.y = -this.radius;
    }
    draw() {
      const grad = actx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.radius);
      let r, g, b, a;
      if (this.type === 'red') { r = 160; g = 20; b = 30; a = isMobile ? 0.08 : 0.12; }
      else if (this.type === 'dark') { r = 20; g = 20; b = 22; a = 0.05; }
      else { r = 140; g = 110; b = 60; a = 0.04; }
      grad.addColorStop(0, `rgba(${r},${g},${b},${a})`);
      grad.addColorStop(0.4, `rgba(${r},${g},${b},${a * 0.6})`);
      grad.addColorStop(1, `rgba(${r},${g},${b},0)`);
      actx.fillStyle = grad; actx.fillRect(0, 0, aW, aH);
    }
  }
  const blobs = [];
  for (let i = 0; i < (isMobile ? 6 : 10); i++) blobs.push(new AuroraBlob());
  let auroraLastFrame = 0;
  function animateAurora(time) {
    requestAnimationFrame(animateAurora);
    if (time - auroraLastFrame < (isMobile ? 50 : 33)) return;
    auroraLastFrame = time;
    actx.clearRect(0, 0, aW, aH);
    for (const b of blobs) { b.update(time); b.draw(); }
  }
  requestAnimationFrame(animateAurora);

  // ========== PARTICLE CANVAS ==========
  const canvas = document.getElementById('particleCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d', { alpha: true });
  let W, H, scrollY = 0;
  let mouse = { x: -9999, y: -9999 };
  // Smooth mouse for cursor glow trail
  let smoothMouse = { x: -9999, y: -9999 };

  const PARTICLE_COUNT = isMobile ? 200 : 400;
  const REPEL_RADIUS = isMobile ? 100 : 180;
  const REPEL_FORCE = 12;
  const LINE_DIST = isMobile ? 80 : 130;
  const MOUSE_CONNECT_RADIUS = isMobile ? 160 : 280;
  const MORPH_SPEED = 0.02;

  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * DPR; canvas.height = H * DPR;
    canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  resize();
  const debouncedResize = debounce(() => { resize(); resizeAurora(); }, 150);
  window.addEventListener('resize', debouncedResize);
  window.addEventListener('scroll', () => { scrollY = window.scrollY || window.pageYOffset; }, { passive: true });

  // Mouse
  const handleMouseMove = isMobile
    ? throttle(e => { mouse.x = e.clientX; mouse.y = e.clientY; }, 32)
    : e => { mouse.x = e.clientX; mouse.y = e.clientY; };
  document.addEventListener('mousemove', handleMouseMove, { passive: true });
  document.addEventListener('touchstart', e => { mouse.x = e.touches[0].clientX; mouse.y = e.touches[0].clientY; }, { passive: true });
  document.addEventListener('touchmove', throttle(e => { mouse.x = e.touches[0].clientX; mouse.y = e.touches[0].clientY; }, 32), { passive: true });
  document.addEventListener('touchend', () => { setTimeout(() => { mouse.x = -9999; mouse.y = -9999; }, 600); }, { passive: true });
  document.addEventListener('mouseleave', () => { mouse.x = -9999; mouse.y = -9999; }, { passive: true });

  // ========== CURSOR GLOW ==========
  // Trail of fading circles that follow the mouse
  const TRAIL_LENGTH = isMobile ? 8 : 15;
  const trail = [];

  function updateTrail() {
    if (mouse.x < -100) return;
    // Smooth follow
    smoothMouse.x += (mouse.x - smoothMouse.x) * 0.15;
    smoothMouse.y += (mouse.y - smoothMouse.y) * 0.15;
    trail.unshift({ x: smoothMouse.x, y: smoothMouse.y, life: 1 });
    if (trail.length > TRAIL_LENGTH) trail.pop();
    for (let i = 0; i < trail.length; i++) {
      trail[i].life *= 0.88;
    }
  }

  function drawCursorGlow() {
    if (mouse.x < -100) { trail.length = 0; smoothMouse.x = -9999; smoothMouse.y = -9999; return; }

    // Main glow at cursor
    const grad = ctx.createRadialGradient(smoothMouse.x, smoothMouse.y, 0, smoothMouse.x, smoothMouse.y, isMobile ? 60 : 100);
    grad.addColorStop(0, 'rgba(220,30,35,0.12)');
    grad.addColorStop(0.4, 'rgba(160,20,30,0.06)');
    grad.addColorStop(1, 'rgba(120,10,20,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(smoothMouse.x - 100, smoothMouse.y - 100, 200, 200);

    // Trail circles
    for (let i = 0; i < trail.length; i++) {
      const t = trail[i];
      if (t.life < 0.02) continue;
      const r = (isMobile ? 4 : 6) * t.life;
      ctx.beginPath();
      ctx.arc(t.x, t.y, r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(180,20,30,${t.life * 0.3})`;
      ctx.fill();
    }

    // Outer ring at cursor
    ctx.beginPath();
    ctx.arc(smoothMouse.x, smoothMouse.y, isMobile ? 15 : 22, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(200,25,35,0.2)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Inner dot
    ctx.beginPath();
    ctx.arc(smoothMouse.x, smoothMouse.y, 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(220,30,35,0.5)';
    ctx.fill();
  }

  // ========== SHAPE GENERATORS ==========
  function shapeScatter(i, N, cx, cy, r) {
    const angle = i * 2.399963 + i * 0.01;
    const dist = Math.sqrt(i / N) * r;
    return { x: cx + Math.cos(angle) * dist, y: cy + Math.sin(angle) * dist };
  }
  function shapeSphere(i, N, cx, cy, r, t) {
    const phi = Math.acos(-1 + (2 * i) / N);
    const theta = Math.sqrt(N * Math.PI) * phi + t * 0.0004;
    return { x: cx + r * Math.cos(theta) * Math.sin(phi), y: cy + r * Math.cos(phi) * 0.65 };
  }
  function shapeWave(i, N, cx, cy, r, t) {
    const pct = i / N;
    return { x: cx - r + pct * r * 2, y: cy + Math.sin(pct * Math.PI * 5 + t * 0.0015) * r * 0.35 };
  }
  function shapeDNA(i, N, cx, cy, r, t) {
    const pct = i / N;
    const strand = i % 2 === 0 ? 1 : -1;
    return { x: cx + Math.sin(pct * Math.PI * 8 + t * 0.0008) * r * 0.45 * strand, y: cy - r * 0.5 + pct * r };
  }
  function shapeGrid(i, N, cx, cy, r) {
    const cols = Math.ceil(Math.sqrt(N));
    const row = Math.floor(i / cols), col = i % cols;
    const sp = (r * 2) / cols;
    return { x: cx - r + col * sp + sp / 2, y: cy - r + row * sp + sp / 2 };
  }
  function shapeRing(i, N, cx, cy, r, t) {
    const rings = 4, ring = i % rings;
    const perRing = Math.floor(N / rings), idx = Math.floor(i / rings);
    const angle = (idx / perRing) * Math.PI * 2 + t * 0.0003 * (ring + 1);
    const rad = r * (0.2 + ring * 0.22);
    return { x: cx + Math.cos(angle) * rad, y: cy + Math.sin(angle) * rad * 0.6 };
  }
  function shapeCross(i, N, cx, cy, r) {
    const arm = i % 4, pct = Math.floor(i / 4) / (N / 4), d = pct * r;
    if (arm === 0) return { x: cx + d, y: cy };
    if (arm === 1) return { x: cx - d, y: cy };
    if (arm === 2) return { x: cx, y: cy + d };
    return { x: cx, y: cy - d };
  }
  function shapeHelix(i, N, cx, cy, r, t) {
    const pct = i / N;
    const angle = pct * Math.PI * 10 + t * 0.0006;
    return { x: cx + Math.cos(angle) * r * 0.4, y: cy - r * 0.5 + pct * r };
  }

  // Section -> shape
  const sectionShapeMap = {
    'inicio': 'scatter', 'ia-negocios': 'wave', 'servicos': 'grid',
    'conquistas': 'sphere', 'estatisticas': 'ring', 'data-intelligence': 'DNA',
    'por-que': 'cross', 'setores': 'helix', 'lideranca': 'ring',
    'ferramentas': 'grid', 'pericias': 'sphere', 'depoimentos': 'wave',
    'blog-preview': 'scatter', 'contato': 'DNA'
  };

  let currentShape = 'scatter';
  let prevDetectedShape = 'scatter';
  let burstTimer = 0; // burst countdown
  let sectionElements = [];

  function cacheSections() {
    sectionElements = Object.keys(sectionShapeMap).map(id => {
      const el = document.getElementById(id);
      return el ? { id, el } : null;
    }).filter(Boolean);
  }
  setTimeout(cacheSections, 300);

  function detectCurrentShape() {
    const mid = scrollY + H * 0.4;
    let newShape = 'scatter';
    for (let i = sectionElements.length - 1; i >= 0; i--) {
      if (sectionElements[i].el.offsetTop <= mid) {
        newShape = sectionShapeMap[sectionElements[i].id] || 'scatter';
        break;
      }
    }
    if (newShape !== prevDetectedShape) {
      prevDetectedShape = newShape;
      currentShape = newShape;
      // BURST: kick all particles outward when shape changes
      burstTimer = 1;
      for (const p of particles) {
        const angle = Math.random() * Math.PI * 2;
        const force = 5 + Math.random() * 10;
        p.vx += Math.cos(angle) * force;
        p.vy += Math.sin(angle) * force;
      }
    }
  }

  function getShapeTarget(i, N, time) {
    const cx = W / 2, cy = H / 2;
    const r = Math.max(W, H) * (isMobile ? 0.6 : 0.75);
    switch (currentShape) {
      case 'sphere': return shapeSphere(i, N, cx, cy, r, time);
      case 'wave': return shapeWave(i, N, cx, cy, r, time);
      case 'DNA': return shapeDNA(i, N, cx, cy, r, time);
      case 'grid': return shapeGrid(i, N, cx, cy, r);
      case 'ring': return shapeRing(i, N, cx, cy, r, time);
      case 'cross': return shapeCross(i, N, cx, cy, r);
      case 'helix': return shapeHelix(i, N, cx, cy, r, time);
      default: return shapeScatter(i, N, cx, cy, r);
    }
  }

  // ========== PARALLAX LAYERS ==========
  // 3 depth layers: back (small, slow), mid (normal), front (big, fast)
  const LAYERS = [
    { sizeMulti: 0.5, alphaMulti: 0.5, morphMulti: 0.6, repelMulti: 0.5, breathMulti: 1.5 },  // back
    { sizeMulti: 1.0, alphaMulti: 1.0, morphMulti: 1.0, repelMulti: 1.0, breathMulti: 1.0 },  // mid
    { sizeMulti: 1.6, alphaMulti: 1.2, morphMulti: 1.3, repelMulti: 1.4, breathMulti: 0.6 },  // front
  ];

  // ========== PARTICLE ==========
  class Particle {
    constructor(i, N) {
      this.i = i; this.N = N;
      this.x = Math.random() * (W || 1400);
      this.y = Math.random() * (H || 900);
      this.vx = 0; this.vy = 0;
      this.baseSize = 0.3 + Math.random() * 0.6;
      this.phase = Math.random() * Math.PI * 2;
      this.breathAmp = 0.4 + Math.random() * 1;
      this.friction = 0.88 + Math.random() * 0.07;

      // Assign to depth layer (back 30%, mid 40%, front 30%)
      const lr = Math.random();
      if (lr < 0.3) this.layer = 0;
      else if (lr < 0.7) this.layer = 1;
      else this.layer = 2;
      this.layerProps = LAYERS[this.layer];

      // Paleta VINHO + PRETO
      const r = Math.random();
      if (r < 0.30) { this.r = 100; this.g = 5; this.b = 15; this.alpha = 0.15 + Math.random() * 0.12; }
      else if (r < 0.55) { this.r = 140; this.g = 15; this.b = 25; this.alpha = 0.12 + Math.random() * 0.12; }
      else if (r < 0.75) { this.r = 220; this.g = 30; this.b = 35; this.alpha = 0.12 + Math.random() * 0.15; }
      else if (r < 0.90) { this.r = 20; this.g = 20; this.b = 20; this.alpha = 0.12 + Math.random() * 0.12; }
      else { this.r = 60; this.g = 60; this.b = 60; this.alpha = 0.1 + Math.random() * 0.1; }
    }

    update(time) {
      const t = time * 0.001;
      const L = this.layerProps;
      const target = getShapeTarget(this.i, this.N, time);

      // Breathing (back layer breathes more = floaty feel)
      const bx = Math.sin(t + this.phase) * this.breathAmp * 0.5 * L.breathMulti;
      const by = Math.cos(t * 0.7 + this.phase * 1.3) * this.breathAmp * 0.4 * L.breathMulti;

      // Morph toward target (front layer reaches faster)
      const tx = target.x + bx;
      const ty = target.y + by;
      this.vx += (tx - this.x) * MORPH_SPEED * L.morphMulti;
      this.vy += (ty - this.y) * MORPH_SPEED * L.morphMulti;

      // Mouse repulsion (front layer reacts more)
      if (mouse.x > -100) {
        const dx = this.x - mouse.x, dy = this.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const repR = REPEL_RADIUS * L.repelMulti;
        if (dist < repR && dist > 1) {
          const str = (1 - dist / repR);
          const push = str * str * REPEL_FORCE * L.repelMulti;
          this.vx += (dx / dist) * push;
          this.vy += (dy / dist) * push;
        }
      }

      this.vx *= this.friction;
      this.vy *= this.friction;
      this.x += this.vx;
      this.y += this.vy;

      if (this.x < -80) this.x = W + 80;
      if (this.x > W + 80) this.x = -80;
      if (this.y < -80) this.y = H + 80;
      if (this.y > H + 80) this.y = -80;
    }

    draw() {
      const L = this.layerProps;
      let glow = 0;
      if (mouse.x > -100) {
        const dx = this.x - mouse.x, dy = this.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        glow = dist < 220 ? (1 - dist / 220) : 0;
      }

      const size = this.baseSize * L.sizeMulti + glow * 1.5;
      const a = Math.min(0.4, this.alpha * L.alphaMulti + glow * 0.15);

      ctx.beginPath();
      ctx.arc(this.x, this.y, size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${this.r},${this.g},${this.b},${a})`;
      ctx.fill();

      if (glow > 0.1) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, size + 6, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(160,20,30,${glow * 0.35})`;
        ctx.fill();
      }
    }
  }

  const particles = [];
  for (let i = 0; i < PARTICLE_COUNT; i++) particles.push(new Particle(i, PARTICLE_COUNT));

  // ========== CONNECTIONS ==========
  const GRID_CELL = LINE_DIST;
  function drawConnections() {
    // Spatial grid
    const grid = {};
    for (const p of particles) {
      const gx = Math.floor(p.x / GRID_CELL), gy = Math.floor(p.y / GRID_CELL);
      const key = gx + ',' + gy;
      if (!grid[key]) grid[key] = [];
      grid[key].push(p);
    }

    // Ambient wireframe (always visible, same-layer only)
    for (const key in grid) {
      const cell = grid[key];
      const [gx, gy] = key.split(',').map(Number);
      for (let nx = gx; nx <= gx + 1; nx++) {
        for (let ny = gy; ny <= gy + 1; ny++) {
          const ncell = grid[nx + ',' + ny];
          if (!ncell) continue;
          for (const a of cell) {
            for (const b of ncell) {
              if (a === b || a.layer !== b.layer) continue;
              const dx = a.x - b.x, dy = a.y - b.y;
              const dSq = dx * dx + dy * dy;
              if (dSq < LINE_DIST * LINE_DIST) {
                const d = Math.sqrt(dSq);
                const alpha = (1 - d / LINE_DIST) * 0.08 * LAYERS[a.layer].alphaMulti;
                ctx.beginPath();
                ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
                ctx.strokeStyle = `rgba(120,10,20,${alpha})`;
                ctx.lineWidth = 0.4 * LAYERS[a.layer].sizeMulti;
                ctx.stroke();
              }
            }
          }
        }
      }
    }

    // Enhanced lines near mouse
    if (mouse.x < -100) return;
    const near = [];
    for (const p of particles) {
      const dx = p.x - mouse.x, dy = p.y - mouse.y;
      if (dx * dx + dy * dy < MOUSE_CONNECT_RADIUS * MOUSE_CONNECT_RADIUS) near.push(p);
    }
    for (let i = 0; i < near.length; i++) {
      const a = near[i];
      for (let j = i + 1; j < near.length; j++) {
        const b = near[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dSq = dx * dx + dy * dy;
        if (dSq < LINE_DIST * LINE_DIST) {
          const d = Math.sqrt(dSq);
          const alpha = (1 - d / LINE_DIST) * 0.7;
          const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
          const mD = Math.sqrt((mx - mouse.x) ** 2 + (my - mouse.y) ** 2);
          const prox = Math.max(0, 1 - mD / MOUSE_CONNECT_RADIUS);
          ctx.beginPath();
          ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(${80 + prox * 140},${5 + prox * 32},${15 + prox * 24},${alpha + prox * 0.3})`;
          ctx.lineWidth = 0.8 + prox * 2.5;
          ctx.stroke();
        }
      }
    }
    // Spider lines
    for (const p of near) {
      const dx = p.x - mouse.x, dy = p.y - mouse.y;
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < REPEL_RADIUS) {
        ctx.beginPath();
        ctx.moveTo(mouse.x, mouse.y); ctx.lineTo(p.x, p.y);
        ctx.strokeStyle = `rgba(120,10,20,${(1 - d / REPEL_RADIUS) * 0.3})`;
        ctx.lineWidth = 0.7; ctx.stroke();
      }
    }
  }

  // ========== BURST FLASH ==========
  function drawBurstFlash() {
    if (burstTimer <= 0) return;
    // Quick white/red flash that fades
    ctx.save();
    ctx.globalAlpha = burstTimer * 0.08;
    const grad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) * 0.5);
    grad.addColorStop(0, 'rgba(220,30,35,0.3)');
    grad.addColorStop(1, 'rgba(220,30,35,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);
    ctx.restore();
    burstTimer *= 0.92;
    if (burstTimer < 0.01) burstTimer = 0;
  }

  // ========== SHAPE LABEL ==========
  let labelOpacity = 0, labelText = '', prevLabelShape = '';
  const shapeLabelMap = {
    'scatter': '', 'wave': 'wave', 'sphere': 'sphere', 'DNA': 'helix',
    'grid': 'grid', 'ring': 'orbits', 'cross': 'cross', 'helix': 'spiral'
  };
  function drawShapeLabel() {
    if (currentShape !== prevLabelShape) {
      prevLabelShape = currentShape;
      labelText = shapeLabelMap[currentShape] || '';
      labelOpacity = labelText ? 1 : 0;
    }
    if (labelOpacity > 0.01 && labelText) {
      ctx.save();
      ctx.globalAlpha = labelOpacity * 0.12;
      ctx.font = `${isMobile ? 60 : 100}px 'Figtree', sans-serif`;
      ctx.fillStyle = '#7a1220';
      ctx.textAlign = 'center';
      ctx.fillText(labelText, W / 2, H / 2 + 35);
      ctx.restore();
      labelOpacity *= 0.993;
    }
  }

  // ========== ANIMATION LOOP ==========
  let lastFrame = 0, frameCount = 0;

  function animate(time) {
    requestAnimationFrame(animate);
    if (time - lastFrame < (isMobile ? 33 : 16)) return;
    lastFrame = time;
    frameCount++;

    if (frameCount % 10 === 0) detectCurrentShape();

    ctx.clearRect(0, 0, W, H);

    drawBurstFlash();
    drawShapeLabel();
    updateTrail();

    // Draw back layer first, then mid, then front (parallax depth)
    for (let layer = 0; layer < 3; layer++) {
      for (const p of particles) {
        if (p.layer === layer) { p.update(time); p.draw(); }
      }
    }

    drawConnections();
    drawCursorGlow();
  }
  requestAnimationFrame(animate);

})();
