/**
 * AUDIPER Global Animations
 * - Scroll Reveal (IntersectionObserver)
 * - Network Canvas (finance red dots)
 */

/* ── SCROLL REVEAL ── */
(function(){
  var sel = '.gs-reveal, .gs-reveal-left, .gs-reveal-right, .gs-reveal-scale';
  var els = document.querySelectorAll(sel);
  if (!els.length) return;
  if (!('IntersectionObserver' in window)) {
    els.forEach(function(e){ e.classList.add('gs-visible'); });
    return;
  }
  var obs = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if (entry.isIntersecting) {
        entry.target.classList.add('gs-visible');
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  els.forEach(function(el){ obs.observe(el); });
})();

/* ── NETWORK CANVAS (red finance dots) ── */
(function(){
  var canvases = document.querySelectorAll('.gs-network-wrap canvas');
  if (!canvases.length) return;
  // respect reduced motion
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  canvases.forEach(function(canvas){
    var ctx = canvas.getContext('2d');
    var dots = [];
    var numDots = 70;
    var maxDist = 160;
    var w, h;

    function resize(){
      var rect = canvas.parentElement.getBoundingClientRect();
      var dpr = window.devicePixelRatio || 1;
      w = rect.width; h = rect.height;
      canvas.width = w * dpr; canvas.height = h * dpr;
      canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function init(){
      resize(); dots = [];
      for (var i = 0; i < numDots; i++){
        dots.push({
          x: Math.random() * w, y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          r: Math.random() * 2 + 1.2,
          pulse: Math.random() * Math.PI * 2
        });
      }
    }

    var running = false;
    function draw(){
      if (!running) return;
      ctx.clearRect(0, 0, w, h);
      var t = Date.now() * 0.001;
      // lines
      for (var i = 0; i < dots.length; i++){
        for (var j = i + 1; j < dots.length; j++){
          var dx = dots[i].x - dots[j].x, dy = dots[i].y - dots[j].y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < maxDist){
            var alpha = (1 - dist / maxDist) * 0.35;
            ctx.beginPath();
            ctx.moveTo(dots[i].x, dots[i].y);
            ctx.lineTo(dots[j].x, dots[j].y);
            ctx.strokeStyle = 'rgba(196,26,26,' + alpha + ')';
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
      // dots
      for (var k = 0; k < dots.length; k++){
        var d = dots[k];
        var ps = 1 + Math.sin(t * 1.5 + d.pulse) * 0.3;
        var a = 0.4 + Math.sin(t * 1.5 + d.pulse) * 0.2;
        ctx.beginPath();
        ctx.arc(d.x, d.y, d.r * ps, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(196,26,26,' + a + ')';
        ctx.fill();
        d.x += d.vx; d.y += d.vy;
        if (d.x < 0 || d.x > w) d.vx *= -1;
        if (d.y < 0 || d.y > h) d.vy *= -1;
      }
      requestAnimationFrame(draw);
    }

    // Only animate when visible
    var visObs = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if (entry.isIntersecting && !running) {
          running = true; draw();
        } else if (!entry.isIntersecting) {
          running = false;
        }
      });
    }, { threshold: 0.05 });

    init();
    visObs.observe(canvas.parentElement);
    window.addEventListener('resize', function(){ resize(); });
  });
})();

/* ── DEPARTMENT NETWORK (connected dept nodes) ── */
(function(){
  var wraps = document.querySelectorAll('.gs-dept-network');
  if (!wraps.length) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  wraps.forEach(function(canvas){
    var ctx = canvas.getContext('2d');
    var w, h, dpr, nodes, particles;

    var deptLabels = [
      { label: 'Financeiro', icon: '💰' },
      { label: 'Comercial', icon: '📊' },
      { label: 'TI', icon: '🖥️' },
      { label: 'Gestão', icon: '⚙️' },
      { label: 'RH', icon: '👥' },
      { label: 'Jurídico', icon: '⚖️' }
    ];

    function resize(){
      var rect = canvas.parentElement.getBoundingClientRect();
      dpr = window.devicePixelRatio || 1;
      w = rect.width; h = rect.height;
      canvas.width = w * dpr; canvas.height = h * dpr;
      canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      layoutNodes();
    }

    function layoutNodes(){
      nodes = [];
      var cx = w * 0.5, cy = h * 0.5;
      var rx = Math.min(w * 0.32, 260), ry = Math.min(h * 0.32, 180);
      // center node
      nodes.push({ x: cx, y: cy, r: 28, label: 'AUDÍPER', isCenter: true, pulse: 0, baseX: cx, baseY: cy });
      // dept nodes in a circle
      for (var i = 0; i < deptLabels.length; i++){
        var angle = (Math.PI * 2 * i / deptLabels.length) - Math.PI / 2;
        var nx = cx + Math.cos(angle) * rx;
        var ny = cy + Math.sin(angle) * ry;
        nodes.push({
          x: nx, y: ny, r: 20, label: deptLabels[i].label,
          icon: deptLabels[i].icon, isCenter: false,
          pulse: i * 0.8, baseX: nx, baseY: ny, angle: angle
        });
      }
      // init particles flowing along edges
      particles = [];
      for (var p = 0; p < 12; p++){
        particles.push({
          fromIdx: 0,
          toIdx: 1 + Math.floor(Math.random() * deptLabels.length),
          progress: Math.random(),
          speed: 0.003 + Math.random() * 0.004,
          reverse: Math.random() > 0.5
        });
      }
    }

    var running = false;
    function draw(){
      if (!running) return;
      ctx.clearRect(0, 0, w, h);
      var t = Date.now() * 0.001;

      // subtle node floating
      for (var n = 1; n < nodes.length; n++){
        nodes[n].x = nodes[n].baseX + Math.sin(t * 0.5 + nodes[n].pulse) * 4;
        nodes[n].y = nodes[n].baseY + Math.cos(t * 0.4 + nodes[n].pulse) * 3;
      }

      // draw connection lines (center to each dept)
      for (var i = 1; i < nodes.length; i++){
        var fromN = nodes[0], toN = nodes[i];
        var lineAlpha = 0.15 + Math.sin(t * 1.2 + i) * 0.08;
        ctx.beginPath();
        ctx.moveTo(fromN.x, fromN.y);
        // curved line
        var mx = (fromN.x + toN.x) / 2 + Math.sin(t * 0.3 + i) * 15;
        var my = (fromN.y + toN.y) / 2 + Math.cos(t * 0.3 + i) * 10;
        ctx.quadraticCurveTo(mx, my, toN.x, toN.y);
        ctx.strokeStyle = 'rgba(196,26,26,' + lineAlpha + ')';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // dashed outer ring connections (dept to dept)
        if (i < nodes.length - 1){
          var nextN = nodes[i + 1];
          var dAlpha = 0.06 + Math.sin(t + i * 2) * 0.03;
          ctx.beginPath();
          ctx.setLineDash([4, 8]);
          ctx.moveTo(toN.x, toN.y);
          ctx.lineTo(nextN.x, nextN.y);
          ctx.strokeStyle = 'rgba(196,26,26,' + dAlpha + ')';
          ctx.lineWidth = 0.8;
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
      // close the ring
      var last = nodes[nodes.length - 1], first = nodes[1];
      ctx.beginPath(); ctx.setLineDash([4, 8]);
      ctx.moveTo(last.x, last.y); ctx.lineTo(first.x, first.y);
      ctx.strokeStyle = 'rgba(196,26,26,0.06)'; ctx.lineWidth = 0.8;
      ctx.stroke(); ctx.setLineDash([]);

      // draw flowing particles
      for (var p = 0; p < particles.length; p++){
        var pt = particles[p];
        var f = nodes[pt.fromIdx], to = nodes[pt.toIdx];
        var prog = pt.reverse ? 1 - pt.progress : pt.progress;
        var px = f.x + (to.x - f.x) * prog;
        var py = f.y + (to.y - f.y) * prog;
        var pAlpha = 0.6 * Math.sin(prog * Math.PI);
        ctx.beginPath();
        ctx.arc(px, py, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(196,26,26,' + pAlpha + ')';
        ctx.fill();
        pt.progress += pt.speed;
        if (pt.progress > 1){
          pt.progress = 0;
          pt.toIdx = 1 + Math.floor(Math.random() * deptLabels.length);
          pt.reverse = Math.random() > 0.5;
          pt.speed = 0.003 + Math.random() * 0.004;
        }
      }

      // draw nodes
      for (var j = 0; j < nodes.length; j++){
        var nd = nodes[j];
        var pulseScale = 1 + Math.sin(t * 1.2 + nd.pulse) * 0.08;
        var rr = nd.r * pulseScale;
        // glow
        var grd = ctx.createRadialGradient(nd.x, nd.y, rr * 0.5, nd.x, nd.y, rr * 2.5);
        grd.addColorStop(0, nd.isCenter ? 'rgba(196,26,26,0.12)' : 'rgba(196,26,26,0.06)');
        grd.addColorStop(1, 'rgba(196,26,26,0)');
        ctx.beginPath(); ctx.arc(nd.x, nd.y, rr * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = grd; ctx.fill();
        // circle bg
        ctx.beginPath(); ctx.arc(nd.x, nd.y, rr, 0, Math.PI * 2);
        ctx.fillStyle = nd.isCenter ? 'rgba(196,26,26,0.12)' : 'rgba(255,255,255,0.7)';
        ctx.fill();
        // circle border
        ctx.beginPath(); ctx.arc(nd.x, nd.y, rr, 0, Math.PI * 2);
        ctx.strokeStyle = nd.isCenter ? 'rgba(196,26,26,0.5)' : 'rgba(196,26,26,0.25)';
        ctx.lineWidth = nd.isCenter ? 2 : 1.2;
        ctx.stroke();
        // label
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        if (nd.isCenter){
          ctx.font = '700 11px Figtree, sans-serif';
          ctx.fillStyle = 'rgba(196,26,26,0.7)';
          ctx.fillText(nd.label, nd.x, nd.y);
        } else {
          ctx.font = '600 9px Figtree, sans-serif';
          ctx.fillStyle = 'rgba(80,80,80,0.6)';
          ctx.fillText(nd.label, nd.x, nd.y + rr + 14);
          // icon inside node
          ctx.font = '14px sans-serif';
          ctx.fillText(nd.icon, nd.x, nd.y);
        }
      }

      requestAnimationFrame(draw);
    }

    var visObs = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if (entry.isIntersecting && !running) { running = true; draw(); }
        else if (!entry.isIntersecting) { running = false; }
      });
    }, { threshold: 0.05 });

    resize();
    visObs.observe(canvas.parentElement);
    window.addEventListener('resize', function(){ resize(); });
  });
})();
