/**
 * AUDIPER Nebula 3D — Nuvem de particulas rotativa com orbe central
 * Efeito tipo starfield 3D com glow, projecao perspectiva real
 * Renderizado em Canvas 2D — sem dependencias
 */
(function() {
  'use strict';

  const isMobile = window.innerWidth < 768 || ('ontouchstart' in window);

  // ========== CONFIG ==========
  const NEBULA_CONFIGS = [
    {
      containerId: 'nebula-hero',
      particleCount: isMobile ? 600 : 1500,
      color: [220, 30, 35],       // vermelho AUDIPER
      glowColor: [255, 60, 60],   // glow vermelho claro
      bgColor: null,               // transparente (sobre hero branco)
      size: { width: 500, height: 500 },
      position: { right: '2%', top: '15%' },
      rotationSpeed: 0.0008,
      spread: 8,
      coreSize: 12,
      coreGlow: true,
      opacity: 0.6
    },
    {
      containerId: 'nebula-stats',
      particleCount: isMobile ? 800 : 2000,
      color: [220, 40, 40],
      glowColor: [255, 80, 70],
      bgColor: null,
      size: { width: 600, height: 400 },
      position: { left: '50%', top: '50%', transform: 'translate(-50%,-50%)' },
      rotationSpeed: 0.0006,
      spread: 10,
      coreSize: 15,
      coreGlow: true,
      opacity: 0.4
    },
    {
      containerId: 'nebula-servicos',
      particleCount: isMobile ? 600 : 1400,
      color: [200, 30, 35],
      glowColor: [255, 70, 60],
      bgColor: null,
      size: { width: 500, height: 600 },
      position: { right: '3%', top: '15%' },
      rotationSpeed: 0.0007,
      spread: 9,
      coreSize: 14,
      coreGlow: true,
      opacity: 0.55
    },
    {
      containerId: 'nebula-data',
      particleCount: isMobile ? 500 : 1200,
      color: [200, 25, 30],
      glowColor: [255, 50, 50],
      bgColor: null,
      size: { width: 450, height: 450 },
      position: { left: '5%', top: '20%' },
      rotationSpeed: 0.001,
      spread: 7,
      coreSize: 10,
      coreGlow: true,
      opacity: 0.5
    }
  ];

  class Nebula {
    constructor(config) {
      this.config = config;
      this.canvas = document.createElement('canvas');
      this.ctx = this.canvas.getContext('2d');
      this.particles = [];
      this.angleY = 0;
      this.angleX = 0.3;
      this.mouse = { x: 0, y: 0 };
      this.mounted = false;
      this.animId = null;

      this.init();
    }

    init() {
      const c = this.config;
      const w = c.size.width;
      const h = c.size.height;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);

      this.canvas.width = w * dpr;
      this.canvas.height = h * dpr;
      this.canvas.style.width = w + 'px';
      this.canvas.style.height = h + 'px';
      this.canvas.style.position = 'absolute';
      this.canvas.style.pointerEvents = 'none';
      this.canvas.style.opacity = c.opacity;
      this.canvas.style.zIndex = '5';
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Apply position
      for (const [k, v] of Object.entries(c.position)) {
        this.canvas.style[k] = v;
      }

      this.w = w;
      this.h = h;
      this.cx = w / 2;
      this.cy = h / 2;
      this.fov = 300;

      // Generate particles in 3D sphere
      for (let i = 0; i < c.particleCount; i++) {
        // Uniform sphere distribution
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        const r = Math.pow(Math.random(), 0.6) * c.spread; // concentration toward center

        const x = r * Math.sin(phi) * Math.cos(theta);
        const y = r * Math.sin(phi) * Math.sin(theta);
        const z = r * Math.cos(phi);

        // Size variation (smaller = further feel)
        const baseSize = 0.5 + Math.random() * 2;
        // Brightness variation
        const brightness = 0.3 + Math.random() * 0.7;

        this.particles.push({ x, y, z, baseSize, brightness, ox: x, oy: y, oz: z });
      }
    }

    mount(parentEl) {
      if (!parentEl) return;
      parentEl.style.position = 'relative';
      // Nao forcar overflow:hidden — respeitar o original da secao
      parentEl.appendChild(this.canvas);
      this.mounted = true;

      // Mouse tracking on parent
      parentEl.addEventListener('mousemove', (e) => {
        const rect = parentEl.getBoundingClientRect();
        this.mouse.x = (e.clientX - rect.left) / rect.width - 0.5;
        this.mouse.y = (e.clientY - rect.top) / rect.height - 0.5;
      }, { passive: true });

      this.animate();
    }

    rotatePoint(x, y, z, ax, ay) {
      // Rotate Y
      let cosY = Math.cos(ay), sinY = Math.sin(ay);
      let x1 = x * cosY + z * sinY;
      let z1 = -x * sinY + z * cosY;
      // Rotate X
      let cosX = Math.cos(ax), sinX = Math.sin(ax);
      let y1 = y * cosX - z1 * sinX;
      let z2 = y * sinX + z1 * cosX;
      return [x1, y1, z2];
    }

    project(x, y, z) {
      const scale = this.fov / (this.fov + z);
      return {
        x: this.cx + x * scale,
        y: this.cy + y * scale,
        scale: scale,
        z: z
      };
    }

    animate() {
      const c = this.config;
      const ctx = this.ctx;
      const loop = () => {
        this.animId = requestAnimationFrame(loop);

        ctx.clearRect(0, 0, this.w, this.h);

        // Slow auto-rotation + mouse influence
        this.angleY += c.rotationSpeed;
        const targetAX = 0.3 + this.mouse.y * 0.5;
        const targetAY = this.angleY + this.mouse.x * 0.5;
        this.angleX += (targetAX - this.angleX) * 0.02;

        // Sort particles by Z for depth (back to front)
        const projected = [];
        for (const p of this.particles) {
          const [rx, ry, rz] = this.rotatePoint(p.ox, p.oy, p.oz, this.angleX, targetAY);
          const proj = this.project(rx * 30, ry * 30, rz * 30);
          projected.push({ ...proj, brightness: p.brightness, baseSize: p.baseSize });
        }
        projected.sort((a, b) => b.z - a.z); // back to front

        // Draw particles
        for (const p of projected) {
          if (p.x < -10 || p.x > this.w + 10 || p.y < -10 || p.y > this.h + 10) continue;

          const size = p.baseSize * p.scale * 1.5;
          if (size < 0.3) continue;

          const alpha = Math.min(1, p.brightness * p.scale * 1.2);
          const [r, g, b] = c.color;

          // Brighter particles near front
          const depthBoost = Math.max(0, p.scale - 0.5) * 0.5;
          const finalR = Math.min(255, r + depthBoost * 55);
          const finalG = Math.min(255, g + depthBoost * 30);
          const finalB = Math.min(255, b + depthBoost * 20);

          ctx.beginPath();
          ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${finalR|0},${finalG|0},${finalB|0},${alpha})`;
          ctx.fill();

          // Glow for bright/large particles
          if (size > 2 && alpha > 0.5) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, size * 2.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${finalR|0},${finalG|0},${finalB|0},${alpha * 0.15})`;
            ctx.fill();
          }
        }

        // Central glowing orb
        if (c.coreGlow) {
          const coreProj = this.project(0, 0, 0);
          const [gr, gg, gb] = c.glowColor;
          const coreR = c.coreSize * coreProj.scale;

          // Outer glow
          const outerGrad = ctx.createRadialGradient(coreProj.x, coreProj.y, 0, coreProj.x, coreProj.y, coreR * 4);
          outerGrad.addColorStop(0, `rgba(${gr},${gg},${gb},0.25)`);
          outerGrad.addColorStop(0.3, `rgba(${gr},${gg},${gb},0.08)`);
          outerGrad.addColorStop(1, `rgba(${gr},${gg},${gb},0)`);
          ctx.fillStyle = outerGrad;
          ctx.fillRect(0, 0, this.w, this.h);

          // Core orb
          const coreGrad = ctx.createRadialGradient(coreProj.x, coreProj.y, 0, coreProj.x, coreProj.y, coreR);
          coreGrad.addColorStop(0, `rgba(255,255,255,0.9)`);
          coreGrad.addColorStop(0.3, `rgba(${gr},${gg},${gb},0.7)`);
          coreGrad.addColorStop(0.7, `rgba(${gr},${gg},${gb},0.3)`);
          coreGrad.addColorStop(1, `rgba(${gr},${gg},${gb},0)`);
          ctx.beginPath();
          ctx.arc(coreProj.x, coreProj.y, coreR, 0, Math.PI * 2);
          ctx.fillStyle = coreGrad;
          ctx.fill();

          // Horizontal light streak through core
          ctx.beginPath();
          ctx.moveTo(coreProj.x - coreR * 5, coreProj.y);
          ctx.lineTo(coreProj.x + coreR * 5, coreProj.y);
          ctx.strokeStyle = `rgba(${gr},${gg},${gb},0.15)`;
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }
      };
      loop();
    }

    destroy() {
      if (this.animId) cancelAnimationFrame(this.animId);
      if (this.canvas.parentElement) this.canvas.parentElement.removeChild(this.canvas);
      this.mounted = false;
    }
  }

  // ========== MOUNT NEBULAS ==========
  // Wait for DOM, then inject into sections
  function mountAll() {
    // Stats section (dark bg) — centered nebula
    const statsSection = document.getElementById('estatisticas');
    if (statsSection) {
      const n = new Nebula(NEBULA_CONFIGS[2]);
      n.mount(statsSection);
    }

    // Data Intelligence — desligada (muito intensa sobre fundo branco)
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountAll);
  } else {
    setTimeout(mountAll, 200);
  }

})();
