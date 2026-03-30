/**
 * AUDIPER Wireframe 3D Shapes — Canvas 2D com projecao perspectiva
 * Formas geometricas wireframe rotativas posicionadas em secoes especificas
 * Cores: vermelho AUDIPER #c41a1a / vinho #7a1220
 */
(function() {
  'use strict';

  const isMobile = window.innerWidth < 768 || ('ontouchstart' in window);
  if (isMobile) return; // skip on mobile for performance

  // ========== 3D MATH ==========
  function rotateX(p, a) {
    const c = Math.cos(a), s = Math.sin(a);
    return [p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c];
  }
  function rotateY(p, a) {
    const c = Math.cos(a), s = Math.sin(a);
    return [p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c];
  }
  function rotateZ(p, a) {
    const c = Math.cos(a), s = Math.sin(a);
    return [p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2]];
  }
  function project(p, cx, cy, fov) {
    const z = p[2] + fov;
    const scale = fov / Math.max(z, 0.1);
    return [cx + p[0] * scale, cy + p[1] * scale, z];
  }

  // ========== SHAPE GENERATORS ==========

  function generateTorus(R, r, segsR, segsr) {
    const verts = [], edges = [];
    for (let i = 0; i < segsR; i++) {
      const theta = (i / segsR) * Math.PI * 2;
      for (let j = 0; j < segsr; j++) {
        const phi = (j / segsr) * Math.PI * 2;
        const x = (R + r * Math.cos(phi)) * Math.cos(theta);
        const y = (R + r * Math.cos(phi)) * Math.sin(theta);
        const z = r * Math.sin(phi);
        verts.push([x, y, z]);
        const idx = i * segsr + j;
        const nextJ = i * segsr + (j + 1) % segsr;
        const nextI = ((i + 1) % segsR) * segsr + j;
        edges.push([idx, nextJ]);
        edges.push([idx, nextI]);
      }
    }
    return { verts, edges };
  }

  function generateIcosahedron(radius) {
    const t = (1 + Math.sqrt(5)) / 2;
    const s = radius / Math.sqrt(1 + t * t);
    const rawVerts = [
      [-1,t,0],[1,t,0],[-1,-t,0],[1,-t,0],
      [0,-1,t],[0,1,t],[0,-1,-t],[0,1,-t],
      [t,0,-1],[t,0,1],[-t,0,-1],[-t,0,1]
    ].map(v => [v[0]*s, v[1]*s, v[2]*s]);
    const faces = [
      [0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],
      [1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],
      [3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],
      [4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]
    ];
    const edgeSet = new Set();
    const edges = [];
    for (const f of faces) {
      for (let i = 0; i < 3; i++) {
        const a = f[i], b = f[(i+1)%3];
        const key = Math.min(a,b)+'-'+Math.max(a,b);
        if (!edgeSet.has(key)) { edgeSet.add(key); edges.push([a,b]); }
      }
    }
    return { verts: rawVerts, edges };
  }

  function generateOctahedron(radius) {
    const verts = [[0,radius,0],[0,-radius,0],[radius,0,0],[-radius,0,0],[0,0,radius],[0,0,-radius]];
    const edges = [[0,2],[0,3],[0,4],[0,5],[1,2],[1,3],[1,4],[1,5],[2,4],[4,3],[3,5],[5,2]];
    return { verts, edges };
  }

  function generateDNA(height, radius, turns, points) {
    const verts = [], edges = [];
    for (let i = 0; i < points; i++) {
      const t = i / points;
      const angle = t * Math.PI * 2 * turns;
      const y = t * height - height / 2;
      // Strand 1
      verts.push([Math.cos(angle) * radius, y, Math.sin(angle) * radius]);
      // Strand 2
      verts.push([Math.cos(angle + Math.PI) * radius, y, Math.sin(angle + Math.PI) * radius]);
      const idx = i * 2;
      if (i > 0) {
        edges.push([idx - 2, idx]);     // strand 1 connection
        edges.push([idx - 1, idx + 1]); // strand 2 connection
      }
      // Rungs every 4 points
      if (i % 4 === 0) edges.push([idx, idx + 1]);
    }
    return { verts, edges };
  }

  function generateGrid(size, divs, depth) {
    const verts = [], edges = [];
    const half = size / 2;
    // Horizontal lines
    for (let i = 0; i <= divs; i++) {
      const z = -depth * (i / divs);
      const idx = verts.length;
      verts.push([-half, 0, z]);
      verts.push([half, 0, z]);
      edges.push([idx, idx + 1]);
    }
    // Vertical lines
    for (let i = 0; i <= divs; i++) {
      const x = -half + (i / divs) * size;
      const idx = verts.length;
      verts.push([x, 0, 0]);
      verts.push([x, 0, -depth]);
      edges.push([idx, idx + 1]);
    }
    return { verts, edges };
  }

  function generateWormhole(rings, segments, maxRadius) {
    const verts = [], edges = [];
    for (let r = 0; r < rings; r++) {
      const depth = -r * 0.8;
      const radius = maxRadius * (0.3 + 0.7 * (1 - r / rings));
      for (let s = 0; s < segments; s++) {
        const angle = (s / segments) * Math.PI * 2;
        const idx = verts.length;
        verts.push([Math.cos(angle) * radius, Math.sin(angle) * radius, depth]);
        // Connect around ring
        if (s > 0) edges.push([idx - 1, idx]);
        if (s === segments - 1) edges.push([idx, r * segments]);
        // Connect to next ring
        if (r > 0) edges.push([idx, idx - segments]);
      }
    }
    return { verts, edges };
  }

  function generateGlobe(radius, latDivs, lonDivs) {
    const verts = [], edges = [];
    for (let i = 0; i <= latDivs; i++) {
      const lat = (i / latDivs) * Math.PI;
      for (let j = 0; j < lonDivs; j++) {
        const lon = (j / lonDivs) * Math.PI * 2;
        const x = radius * Math.sin(lat) * Math.cos(lon);
        const y = radius * Math.cos(lat);
        const z = radius * Math.sin(lat) * Math.sin(lon);
        const idx = verts.length;
        verts.push([x, y, z]);
        // Horizontal edge
        if (j > 0) edges.push([idx - 1, idx]);
        if (j === lonDivs - 1) edges.push([idx, i * lonDivs]);
        // Vertical edge
        if (i > 0) edges.push([idx, idx - lonDivs]);
      }
    }
    return { verts, edges };
  }

  // ========== WIREFRAME INSTANCES ==========
  // Each instance is tied to a section and positioned relative to it

  const instances = [
    { sectionId: 'inicio',            shape: 'torus',       x: 0.82, y: 0.35, size: 120, rotSpeed: [0.003, 0.005, 0.001], opacity: 0.25 },
    { sectionId: 'ia-negocios',       shape: 'wormhole',    x: 0.85, y: 0.5,  size: 100, rotSpeed: [0.002, 0.004, 0],     opacity: 0.2 },
    { sectionId: 'servicos',          shape: 'icosahedron',  x: 0.08, y: 0.3, size: 80,  rotSpeed: [0.005, 0.008, 0.003], opacity: 0.22 },
    { sectionId: 'servicos',          shape: 'octahedron',   x: 0.92, y: 0.7, size: 60,  rotSpeed: [0.007, 0.004, 0.005], opacity: 0.18 },
    { sectionId: 'estatisticas',      shape: 'grid',        x: 0.5,  y: 0.6,  size: 200, rotSpeed: [0.001, 0, 0],         opacity: 0.15 },
    { sectionId: 'data-intelligence', shape: 'dna',         x: 0.88, y: 0.5,  size: 130, rotSpeed: [0.003, 0.006, 0],     opacity: 0.22 },
    { sectionId: 'por-que',           shape: 'torus',       x: 0.1,  y: 0.4,  size: 90,  rotSpeed: [0.004, 0.006, 0.002], opacity: 0.2 },
    { sectionId: 'lideranca',         shape: 'globe',       x: 0.85, y: 0.5,  size: 100, rotSpeed: [0.002, 0.003, 0],     opacity: 0.18 },
    { sectionId: 'pericias',          shape: 'icosahedron',  x: 0.12, y: 0.5, size: 90,  rotSpeed: [0.006, 0.004, 0.002], opacity: 0.2 },
    { sectionId: 'contato',           shape: 'globe',       x: 0.5,  y: 0.4,  size: 120, rotSpeed: [0.001, 0.003, 0],     opacity: 0.15 },
  ];

  // Pre-generate shapes
  const shapeCache = {};
  function getShape(type) {
    if (shapeCache[type]) return shapeCache[type];
    let shape;
    switch (type) {
      case 'torus': shape = generateTorus(1, 0.35, 20, 10); break;
      case 'icosahedron': shape = generateIcosahedron(1); break;
      case 'octahedron': shape = generateOctahedron(1); break;
      case 'dna': shape = generateDNA(3, 0.8, 3, 60); break;
      case 'grid': shape = generateGrid(4, 10, 4); break;
      case 'wormhole': shape = generateWormhole(8, 24, 1.2); break;
      case 'globe': shape = generateGlobe(1, 10, 16); break;
      default: shape = generateIcosahedron(1);
    }
    shapeCache[type] = shape;
    return shape;
  }

  // ========== CANVAS ==========
  const canvas = document.createElement('canvas');
  canvas.id = 'wireframeCanvas';
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:8;pointer-events:none;';
  document.body.insertBefore(canvas, document.body.firstChild);
  const ctx = canvas.getContext('2d');
  const DPR = Math.min(window.devicePixelRatio || 1, 2);
  let W, H;

  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * DPR; canvas.height = H * DPR;
    canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  resize();
  window.addEventListener('resize', () => { resize(); }, { passive: true });

  let scrollY = 0;
  window.addEventListener('scroll', () => { scrollY = window.scrollY || window.pageYOffset; }, { passive: true });

  // Mouse for interactive glow
  let mouse = { x: -9999, y: -9999 };
  document.addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; }, { passive: true });
  document.addEventListener('mouseleave', () => { mouse.x = -9999; mouse.y = -9999; }, { passive: true });

  // Cache section positions
  let sectionRects = {};
  function cacheSections() {
    for (const inst of instances) {
      const el = document.getElementById(inst.sectionId);
      if (el) sectionRects[inst.sectionId] = el;
    }
  }
  setTimeout(cacheSections, 500);

  // ========== RENDER ==========
  let time = 0;

  function drawWireframe(shape, cx, cy, size, rotX, rotY, rotZ, opacity, mouseProx) {
    const fov = 3;
    const { verts, edges } = shape;

    // Project all vertices
    const projected = verts.map(v => {
      let p = [v[0], v[1], v[2]];
      p = rotateX(p, rotX);
      p = rotateY(p, rotY);
      p = rotateZ(p, rotZ);
      return project(p, cx, cy, fov);
    });

    // Boost opacity near mouse
    const glowBoost = mouseProx * 0.15;
    const baseAlpha = opacity + glowBoost;

    // Draw edges
    for (const [a, b] of edges) {
      const pa = projected[a];
      const pb = projected[b];
      if (!pa || !pb) continue;

      // Depth-based alpha
      const avgZ = (pa[2] + pb[2]) / 2;
      const depthAlpha = Math.max(0.1, Math.min(1, 1 - (avgZ - fov * 0.5) / (fov * 2)));
      const alpha = baseAlpha * depthAlpha;

      if (alpha < 0.02) continue;

      // Scale positions
      const x1 = cx + (pa[0] - cx) * size;
      const y1 = cy + (pa[1] - cy) * size;
      const x2 = cx + (pb[0] - cx) * size;
      const y2 = cy + (pb[1] - cy) * size;

      // Color gradient: deeper = darker
      const r = Math.round(196 - depthAlpha * 74);
      const g = Math.round(26 - depthAlpha * 16);
      const b2 = Math.round(26 + depthAlpha * 10);

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = `rgba(${r},${g},${b2},${alpha})`;
      ctx.lineWidth = 0.6 + depthAlpha * 0.8 + mouseProx * 0.5;
      ctx.stroke();
    }

    // Draw vertices as dots
    for (const p of projected) {
      const x = cx + (p[0] - cx) * size;
      const y = cy + (p[1] - cy) * size;
      const avgZ = p[2];
      const depthAlpha = Math.max(0.1, Math.min(1, 1 - (avgZ - fov * 0.5) / (fov * 2)));
      const alpha = (baseAlpha * 0.7) * depthAlpha;
      if (alpha < 0.03) continue;

      const dotSize = 1 + depthAlpha * 1.5 + mouseProx * 1;
      ctx.beginPath();
      ctx.arc(x, y, dotSize, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(196,26,26,${alpha})`;
      ctx.fill();
    }
  }

  function animate() {
    requestAnimationFrame(animate);
    time += 0.016;

    ctx.clearRect(0, 0, W, H);

    for (const inst of instances) {
      const el = sectionRects[inst.sectionId];
      if (!el) continue;

      // Check if section is in viewport
      const rect = el.getBoundingClientRect();
      if (rect.bottom < -100 || rect.top > H + 100) continue;

      // Position within section (relative)
      const cx = inst.x * W;
      const cy = rect.top + inst.y * rect.height;

      // Skip if too far off screen
      if (cy < -200 || cy > H + 200) continue;

      // Mouse proximity
      let mouseProx = 0;
      if (mouse.x > -100) {
        const dx = cx - mouse.x, dy = cy - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        mouseProx = dist < 250 ? (1 - dist / 250) : 0;
      }

      // Rotation
      const rx = time * inst.rotSpeed[0];
      const ry = time * inst.rotSpeed[1];
      const rz = time * inst.rotSpeed[2];

      const shape = getShape(inst.shape);
      drawWireframe(shape, cx, cy, inst.size, rx, ry, rz, inst.opacity, mouseProx);
    }
  }
  requestAnimationFrame(animate);

})();
