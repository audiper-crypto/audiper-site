/**
 * enviar_whatsapp_cdp.js — envia arquivo para um grupo do WhatsApp via CDP.
 *
 * Conecta a uma instancia JA ABERTA e JA LOGADA (WhatsApp Desktop/Electron ou
 * WhatsApp Web no Chrome) pelo Chrome DevTools Protocol. Nao faz login, nao le
 * QR code, nao guarda credencial: usa a sessao que voce ja tem aberta.
 *
 * PRE-REQUISITO — subir o app com a porta de depuracao:
 *
 *   WhatsApp Desktop (Windows):
 *     "%LOCALAPPDATA%\\WhatsApp\\WhatsApp.exe" --remote-debugging-port=9222
 *
 *   WhatsApp Web no Chrome:
 *     chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\wa-profile"
 *     (e abrir web.whatsapp.com nesse perfil)
 *
 * USO:
 *   node scripts/enviar_whatsapp_cdp.js "Vitor Pessoal" caminho/do/arquivo.mp4
 *   node scripts/enviar_whatsapp_cdp.js "Vitor Pessoal" arquivo.mp4 --texto "segue o reel"
 *   node scripts/enviar_whatsapp_cdp.js "Vitor Pessoal" arquivo.mp4 --ensaio
 *
 * --ensaio  faz tudo menos apertar enviar, e tira print em wa-ensaio.png.
 *           Use na primeira vez: confirma que achou o grupo certo.
 *
 * DEPENDENCIA:  npm i playwright
 *
 * AVISO: automatizar o WhatsApp contraria os Termos de Servico da plataforma,
 * que preveem suspensao de conta. Isso vale mesmo para uso proprio, mandando
 * para o seu proprio grupo. Volume alto ou uso continuo aumenta muito o risco.
 * Decisao de quem roda.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ENDPOINT = process.env.WA_CDP || 'http://127.0.0.1:9222';
const ESPERA = 1200;

function args() {
  const a = process.argv.slice(2);
  const grupo = a[0];
  const arquivo = a[1];
  const ensaio = a.includes('--ensaio');
  const i = a.indexOf('--texto');
  const texto = i >= 0 ? a[i + 1] : null;
  if (!grupo || !arquivo) {
    console.error('Uso: node enviar_whatsapp_cdp.js "<nome do grupo>" <arquivo> [--texto "..."] [--ensaio]');
    process.exit(1);
  }
  const abs = path.resolve(arquivo);
  if (!fs.existsSync(abs)) {
    console.error(`Arquivo nao encontrado: ${abs}`);
    process.exit(1);
  }
  return { grupo, arquivo: abs, texto, ensaio };
}

const pausa = (ms) => new Promise((r) => setTimeout(r, ms));

async function acharPaginaWhatsApp(browser) {
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      const url = p.url() || '';
      const titulo = await p.title().catch(() => '');
      if (/whatsapp/i.test(url) || /whatsapp/i.test(titulo)) return p;
    }
  }
  return null;
}

(async () => {
  const { grupo, arquivo, texto, ensaio } = args();

  let browser;
  try {
    browser = await chromium.connectOverCDP(ENDPOINT);
  } catch (e) {
    console.error(`Nao consegui conectar em ${ENDPOINT}.`);
    console.error('O app esta aberto com --remote-debugging-port=9222?');
    process.exit(2);
  }

  const page = await acharPaginaWhatsApp(browser);
  if (!page) {
    console.error('Conectei, mas nenhuma aba/janela do WhatsApp foi encontrada.');
    console.error('Abra o WhatsApp nessa instancia e rode de novo.');
    process.exit(3);
  }
  console.log('Conectado:', page.url() || (await page.title()));

  // 1. Buscar o grupo. O seletor da caixa de busca muda entre versoes —
  //    por isso tentamos varios, do mais estavel para o mais generico.
  const seletoresBusca = [
    'div[contenteditable="true"][data-tab="3"]',
    'div[contenteditable="true"][title*="esquis"]',
    '[aria-label*="esquis"] div[contenteditable="true"]',
    'div[contenteditable="true"]',
  ];
  let busca = null;
  for (const s of seletoresBusca) {
    const el = page.locator(s).first();
    if (await el.count().catch(() => 0)) { busca = el; break; }
  }
  if (!busca) {
    console.error('Nao achei a caixa de busca. O layout do WhatsApp mudou;');
    console.error('ajuste seletoresBusca neste script.');
    process.exit(4);
  }

  await busca.click();
  await page.keyboard.press('Control+A').catch(() => {});
  await busca.fill('').catch(() => {});
  await page.keyboard.type(grupo, { delay: 40 });
  await pausa(ESPERA);
  await page.keyboard.press('Enter');
  await pausa(ESPERA);

  // 2. Conferir que a conversa aberta e mesmo a pedida.
  const cabecalho = await page.locator('header').first().innerText().catch(() => '');
  const bate = cabecalho.toLowerCase().includes(grupo.toLowerCase());
  console.log(`Conversa aberta: "${cabecalho.split('\n')[0] || '(nao lido)'}"`);
  if (!bate) {
    console.error(`ATENCAO: o cabecalho nao contem "${grupo}".`);
    console.error('Parando por seguranca — mandar arquivo na conversa errada nao tem desfazer.');
    console.error('Rode com --ensaio para inspecionar, ou refine o nome do grupo.');
    process.exit(5);
  }

  // 3. Anexar o arquivo. O input[type=file] existe no DOM mesmo sem abrir o menu.
  const inputs = page.locator('input[type="file"]');
  const n = await inputs.count();
  if (!n) {
    console.error('Nenhum input[type=file] no DOM. Abra o menu de anexo manualmente uma vez.');
    process.exit(6);
  }
  let anexado = false;
  for (let i = 0; i < n; i++) {
    const accept = (await inputs.nth(i).getAttribute('accept')) || '';
    if (/video|image|\*/.test(accept) || accept === '') {
      await inputs.nth(i).setInputFiles(arquivo);
      anexado = true;
      break;
    }
  }
  if (!anexado) {
    await inputs.first().setInputFiles(arquivo);
  }
  await pausa(ESPERA * 2);
  console.log('Arquivo anexado:', path.basename(arquivo));

  // 4. Legenda opcional.
  if (texto) {
    const legenda = page.locator('div[contenteditable="true"]').last();
    await legenda.click().catch(() => {});
    await page.keyboard.type(texto, { delay: 25 });
    await pausa(400);
  }

  // 5. Enviar — ou parar, no ensaio.
  if (ensaio) {
    await page.screenshot({ path: 'wa-ensaio.png' });
    console.log('ENSAIO: nada foi enviado. Confira wa-ensaio.png.');
    await browser.close();
    return;
  }

  await page.keyboard.press('Enter');
  await pausa(ESPERA * 2);
  console.log(`Enviado para "${grupo}".`);
  await browser.close();
})().catch((e) => {
  console.error('Falhou:', e.message);
  process.exit(10);
});
