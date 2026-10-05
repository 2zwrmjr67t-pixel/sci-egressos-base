// Teste de navegador do painel (docs/index.html) com Playwright.
// Rodar: node tests/painel.test.mjs
// Requer o pacote "playwright" e um Chromium disponível (não é dependência do painel).
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import assert from "node:assert/strict";

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); }
catch { ({ chromium } = await import("playwright")); }

const DOCS = fileURLToPath(new URL("../docs/", import.meta.url));
const TIPOS = { ".html": "text/html; charset=utf-8", ".json": "application/json" };

// Servidor estático mínimo; com BLOQUEIA_JSON simula falha de carregamento.
function servidor(bloqueiaJson = false) {
  return createServer(async (req, res) => {
    const rel = normalize(decodeURIComponent(req.url.split("?")[0])).replace(/^(\.\.[/\\])+/, "");
    const caminho = join(DOCS, rel.endsWith("/") ? rel + "index.html" : rel);
    if (bloqueiaJson && caminho.endsWith(".json")) { res.writeHead(404); return res.end(); }
    try {
      const corpo = await readFile(caminho);
      res.writeHead(200, { "content-type": TIPOS[extname(caminho)] || "application/octet-stream" });
      res.end(corpo);
    } catch { res.writeHead(404); res.end(); }
  });
}
const sobe = (s) => new Promise((ok) => s.listen(0, "127.0.0.1", () => ok(`http://127.0.0.1:${s.address().port}/`)));

const browser = await chromium.launch();
const falhas = [];
const ok = (nome) => console.log("ok  " + nome);

async function abre(url, largura) {
  const ctx = await browser.newContext({ viewport: { width: largura, height: 800 } });
  const page = await ctx.newPage();
  const erros = [];
  page.on("pageerror", (e) => erros.push(e.message));
  page.on("console", (m) => { if (m.type() === "error" && !/fonts\.(googleapis|gstatic)/.test(m.text())) erros.push(m.text()); });
  // Fontes externas não são necessárias para o teste.
  await page.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.fulfill({ status: 200, contentType: "text/css", body: "" }));
  await page.goto(url);
  return { ctx, page, erros };
}

const s1 = servidor();
const url = await sobe(s1);
try {
  const meta = JSON.parse(await readFile(join(DOCS, "data/meta.json"), "utf8"));

  for (const largura of [375, 1280]) {
    const { ctx, page, erros } = await abre(url, largura);
    await page.waitForSelector(".cartao");

    // 3. Chips com contagens iguais ao meta.json
    const chips = await page.$$eval(".chip-classe", (bs) => bs.map((b) => ({
      k: b.dataset.classe, n: Number(b.querySelector(".n").textContent), on: b.getAttribute("aria-pressed") === "true" })));
    for (const c of chips) assert.equal(c.n, meta.classes[c.k], `chip ${c.k}`);
    assert.deepEqual(chips.filter((c) => c.on).map((c) => c.k), ["A", "B", "C", "D"]);

    // Estado inicial: A+B+C+D = 70 cartões; ordenação padrão por minutos 2023–25
    const n = await page.$$eval(".cartao", (x) => x.length);
    assert.equal(n, 13 + 6 + 8 + 43);
    // 5. Lucas Piton (classe E) só aparece com E ligado; ligar E e conferir topo
    await page.click('.chip-classe[data-classe="E"]');
    const primeiro = await page.$eval(".cartao h2", (h) => h.textContent);
    assert.equal(primeiro, "Lucas Piton");
    assert.match(await page.$eval(".cartao .numeros", (e) => e.textContent), /13\.278/);

    // Todas as classes ligadas = 227
    await page.click('.chip-classe[data-classe="SD"]');
    await page.click('.chip-classe[data-classe="DESC"]');
    assert.equal(await page.$$eval(".cartao", (x) => x.length), 227);

    // 4. Casos
    const card = (nome) => page.locator(".cartao", { has: page.locator("h2", { hasText: new RegExp(`^${nome}$`) }) });
    assert.match(await card("Micael").locator(".selo").first().textContent(), /^A$/);
    assert.equal(await card("Micael").locator(".emprestado").textContent(), "Emprestado pelo Palmeiras");
    assert.match(await card("Cipriano").locator(".selo").first().textContent(), /^B$/);
    assert.equal(await card("Cipriano").locator(".emprestado").textContent(), "Emprestado pelo APOEL");
    assert.match(await card("Kevyson").locator(".disp").textContent(), /disponibilidade: atenção/);
    assert.equal(await card("Felipe Andrade").locator(".ficha .alerta").count(), 1);

    // Filtros
    await page.selectOption("#f-vinculo", "emprestimo");
    assert.equal(await page.$$eval(".cartao", (x) => x.length), 3);
    await page.selectOption("#f-vinculo", "");
    await page.selectOption("#f-pos", "GOL");
    assert.equal(await page.$$eval(".cartao", (x) => x.length), 18);
    await page.selectOption("#f-pos", "");
    await page.selectOption("#f-formador", "Internacional");
    assert.equal(await page.$$eval(".cartao", (x) => x.length), 58); // 56 + 2 com formação compartilhada
    await page.click("#f-limpar");
    await page.fill("#f-busca", "micael");
    assert.equal(await page.$$eval(".cartao", (x) => x.length), 1);
    await page.click("#f-limpar");

    // Rodapé obrigatório
    const rodape = await page.textContent("footer");
    assert.match(rodape, /Triagem estatística, não recomendação\./);
    assert.match(rodape, /Fonte: Sofascore \(coleta de 30\/09\/2026\)/);

    // 6. Sem rolagem horizontal e sem erros de JS
    const transborda = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    assert.equal(transborda, false, `rolagem horizontal em ${largura}px`);
    assert.deepEqual(erros, []);
    await page.screenshot({ path: `${process.env.SCREENSHOT_DIR || "/tmp"}/painel-${largura}.png`, fullPage: false });
    await ctx.close();
    ok(`painel em ${largura}px`);
  }
} catch (e) { falhas.push(e); }
finally { s1.close(); }

// Erro visível se o JSON não carregar
const s2 = servidor(true);
try {
  const { ctx, page } = await abre(await sobe(s2), 375);
  await page.waitForSelector("#erro.ativo");
  assert.match(await page.textContent("#erro"), /Não foi possível carregar/);
  await ctx.close();
  ok("mensagem de erro quando o JSON falha");
} catch (e) { falhas.push(e); }
finally { s2.close(); }

await browser.close();
if (falhas.length) { falhas.forEach((f) => console.error("FALHA", f.message)); process.exit(1); }
console.log("todos os testes do painel passaram");
