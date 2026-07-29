/* AUDÍPER — carregador do chat com contingência para WhatsApp.
 *
 * Regra de ouro: a contingência NÃO pode depender do que caiu.
 *
 * Sinais reais que o SDK do Chatwoot emite (conferidos no sdk.js servido):
 *   chatwoot:ready · chatwoot:error · chatwoot:opened · chatwoot:closed · chatwoot:postback
 * NÃO existe evento de mensagem — por isso o silêncio do agente é tratado no
 * servidor (AlertChannel avisa a equipe), não aqui.
 *
 * Modos de falha cobertos:
 *   1. sdk.js não carrega (servidor fora, rede ruim)  -> timeout no <script>
 *   2. sdk.js veio DO CACHE mas o servidor está fora   -> `chatwoot:ready` nunca chega
 *   3. o SDK avisa erro explicitamente                 -> `chatwoot:error`
 *
 * O caso 2 é o que engana: um visitante recorrente tem o sdk.js em cache, o
 * onload dispara normalmente e o widget sobe sem servidor atrás. Só o
 * `chatwoot:ready` prova que a sessão foi realmente estabelecida.
 *
 * Embutir no site com:  <script src="/js/audiper-chat.js" defer></script>
 */
(function () {
  "use strict";

  var CFG = {
    baseUrl: "https://chat.audiper.com.br",
    websiteToken: "EqxhuGzuH6p6rAFG46KKEYRQ",
    whatsapp: "5586994010525",
    sdkTimeout: 8000,   // download do sdk.js
    readyTimeout: 12000, // do run() até o chatwoot:ready
    locale: "pt_BR",

    // Redirect próprio do site (/wa/), que dispara o evento GA4 whatsapp_click
    // e faz o prefill por origem. Separa, na medição, o lead que veio de CTA
    // do lead que veio da contingência do chat.
    //
    // FICA false ATÉ /wa/ ESTAR PUBLICADO. Com /wa/ ausente o visitante cai
    // num 404 justamente no momento em que o chat já falhou — o pior lugar
    // possível pra ter um segundo defeito. Conferir antes de virar:
    //     curl -o /dev/null -w '%{http_code}' https://audiper.com/wa/?o=chat
    usarRedirectProprio: false,
    origemContingencia: "chat",
  };

  function waLink(motivo) {
    if (CFG.usarRedirectProprio) {
      // O /wa/ injeta o prefill a partir da origem; ?t= só quando há motivo.
      return "/wa/?o=" + encodeURIComponent(CFG.origemContingencia) +
             (motivo ? "&t=" + encodeURIComponent(
               "Olá! Vim pelo site da AUDÍPER. (" + motivo + ")") : "");
    }
    var t = motivo
      ? "Olá! Vim pelo site da AUDÍPER. (" + motivo + ")"
      : "Olá! Vim pelo site da AUDÍPER e gostaria de falar com a equipe.";
    return "https://wa.me/" + CFG.whatsapp + "?text=" + encodeURIComponent(t);
  }

  // ---------------------------------------------------------------- fallback UI
  var jaMostrou = false;
  function mostrarFallback(motivo) {
    if (jaMostrou) return;
    jaMostrou = true;

    // Esconde o balão do Chatwoot, se ele chegou a aparecer sem servidor atrás.
    var iframe = document.querySelector(".woot-widget-holder, .woot--bubble-holder");
    if (iframe) iframe.style.display = "none";

    var a = document.createElement("a");
    a.href = waLink(motivo);
    a.target = "_blank";
    a.rel = "noopener";
    a.setAttribute("aria-label", "Falar com a AUDÍPER no WhatsApp");
    a.style.cssText = [
      "position:fixed", "right:20px", "bottom:20px", "z-index:2147483000",
      "display:flex", "align-items:center", "gap:10px",
      "background:#25D366", "color:#fff", "text-decoration:none",
      "font:600 15px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif",
      "padding:14px 20px", "border-radius:999px",
      "box-shadow:0 6px 24px rgba(0,0,0,.22)",
    ].join(";");
    a.innerHTML =
      '<svg width="22" height="22" viewBox="0 0 16 16" fill="#fff" aria-hidden="true">' +
      '<path d="M13.601 2.326A7.854 7.854 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.933 7.933 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.898 7.898 0 0 0 13.6 2.326zM7.994 14.521a6.573 6.573 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.557 6.557 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592z"/></svg>' +
      "<span>Falar no WhatsApp</span>";
    document.body.appendChild(a);

    var nota = document.createElement("div");
    nota.textContent =
      "Nosso chat está indisponível no momento. Fale direto com a equipe pelo WhatsApp.";
    nota.style.cssText = [
      "position:fixed", "right:20px", "bottom:82px", "z-index:2147483000",
      "max-width:280px", "background:#fff", "color:#1e293b",
      "border:1px solid #e2e8f0", "border-left:4px solid #7a1220",
      "border-radius:8px", "padding:12px 14px",
      "font:400 13px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif",
      "box-shadow:0 6px 24px rgba(0,0,0,.12)",
    ].join(";");
    document.body.appendChild(nota);
    setTimeout(function () { nota.remove(); }, 20000);
  }

  // ------------------------------------------------------------- carregar o SDK
  // Tag <script> não sofre CORS. Um fetch em /api falharia sempre: o endpoint
  // não envia Access-Control-Allow-Origin.
  function carregarSdk() {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = CFG.baseUrl + "/packs/js/sdk.js";
      s.async = true;
      s.defer = true;
      var t = setTimeout(function () { reject(new Error("timeout")); }, CFG.sdkTimeout);
      s.onload = function () { clearTimeout(t); resolve(); };
      s.onerror = function () { clearTimeout(t); reject(new Error("erro")); };
      document.head.appendChild(s);
    });
  }

  // ------------------------------------------------------------------ orquestra
  function iniciar() {
    window.chatwootSettings = {
      position: "right",
      type: "expanded_bubble",
      launcherTitle: "Fale com a AUDÍPER",
      locale: CFG.locale,
    };

    // O SDK avisa erro por conta própria.
    window.addEventListener("chatwoot:error", function () {
      mostrarFallback("nosso chat está fora do ar");
    });

    carregarSdk()
      .then(function () {
        // A prova de vida é o `ready`. Se o sdk.js veio do cache mas o servidor
        // está fora, ele nunca chega — e é aí que a contingência entra.
        var prazo = setTimeout(function () {
          mostrarFallback("nosso chat está fora do ar");
        }, CFG.readyTimeout);

        window.addEventListener("chatwoot:ready", function () {
          clearTimeout(prazo);
        });

        window.chatwootSDK.run({
          websiteToken: CFG.websiteToken,
          baseUrl: CFG.baseUrl,
        });
      })
      .catch(function () {
        mostrarFallback("nosso chat está fora do ar");
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
