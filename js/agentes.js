/**
 * agentes.js — Interatividade da pagina Agentes IA
 * Pipeline toggle, counter animation, card reveals
 */
(function () {
    'use strict';

    gsap.registerPlugin(ScrollTrigger);

    document.addEventListener('DOMContentLoaded', function () {
        initCounters();
        initPhaseToggle();
        initPipelineReveal();
    });

    /* -------------------------------------------------------
     * 1. Counter Animation
     * Anima .ag-stat .number de 0 ate data-target
     * ------------------------------------------------------- */
    function initCounters() {
        var numbers = document.querySelectorAll('.ag-stat .number');
        if (!numbers.length) return;

        numbers.forEach(function (el) {
            var target = parseInt(el.getAttribute('data-target'), 10) || 0;
            var obj = { val: 0 };

            ScrollTrigger.create({
                trigger: '.ag-stats',
                start: 'top 85%',
                once: true,
                onEnter: function () {
                    gsap.to(obj, {
                        val: target,
                        duration: 2,
                        ease: 'power2.out',
                        onUpdate: function () {
                            el.textContent = Math.round(obj.val);
                        }
                    });
                }
            });
        });
    }

    /* -------------------------------------------------------
     * 2. Phase Click -> Toggle Panel
     * ------------------------------------------------------- */
    function initPhaseToggle() {
        var phases = document.querySelectorAll('.ag-phase');
        var panels = document.querySelectorAll('.ag-panel');

        phases.forEach(function (phase) {
            phase.addEventListener('click', function () {
                var key = phase.getAttribute('data-phase');
                var wasActive = phase.classList.contains('active');

                // Remove active de todas as fases e paineis
                phases.forEach(function (p) { p.classList.remove('active'); });
                panels.forEach(function (p) { p.classList.remove('active'); });

                // Se clicou na ja ativa, apenas fecha (toggle off)
                if (wasActive) return;

                // Ativa fase e painel correspondente
                phase.classList.add('active');
                var matchingPanel = document.querySelector('.ag-panel[data-panel="' + key + '"]');
                if (!matchingPanel) return;

                matchingPanel.classList.add('active');

                // Smooth scroll ate o painel
                setTimeout(function () {
                    matchingPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 50);

                // Anima cards do painel
                animateCards(matchingPanel);
            });

            // Acessibilidade: ativar com Enter/Space
            phase.setAttribute('tabindex', '0');
            phase.setAttribute('role', 'button');
            phase.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    phase.click();
                }
            });
        });
    }

    /* -------------------------------------------------------
     * 3. Pipeline Reveal Animation
     * Stagger .ag-phase e .ag-connector ao entrar no viewport
     * Auto-abre primeira fase apos conclusao
     * ------------------------------------------------------- */
    function initPipelineReveal() {
        var pipeline = document.querySelector('.ag-pipeline');
        if (!pipeline) return;

        var phaseEls = pipeline.querySelectorAll('.ag-phase');
        var connectors = pipeline.querySelectorAll('.ag-connector');

        // Estado inicial: invisivel
        gsap.set(phaseEls, { opacity: 0, scale: 0.8 });
        gsap.set(connectors, { opacity: 0 });

        ScrollTrigger.create({
            trigger: '.ag-pipeline',
            start: 'top 80%',
            once: true,
            onEnter: function () {
                // Anima fases
                var tl = gsap.timeline();

                tl.to(phaseEls, {
                    opacity: 1,
                    scale: 1,
                    duration: 0.5,
                    ease: 'back.out(1.4)',
                    stagger: 0.15
                });

                // Connectors aparecem intercalados
                tl.to(connectors, {
                    opacity: 1,
                    duration: 0.3,
                    stagger: 0.1
                }, '-=0.8');

                // Auto-abrir primeira fase apos 1s do fim da animacao
                tl.call(function () {
                    setTimeout(function () {
                        var first = document.querySelector('.ag-phase[data-phase="descoberta"]');
                        if (first && !first.classList.contains('active')) {
                            first.click();
                        }
                    }, 1000);
                });
            }
        });
    }

    /* -------------------------------------------------------
     * 4. Card Reveal Animation
     * Stagger .ag-card dentro do painel ativo
     * ------------------------------------------------------- */
    function animateCards(panel) {
        var cards = panel.querySelectorAll('.ag-card');
        if (!cards.length) return;

        gsap.fromTo(cards,
            { opacity: 0, y: 30 },
            {
                opacity: 1,
                y: 0,
                duration: 0.4,
                ease: 'power2.out',
                stagger: 0.08
            }
        );
    }

})();
