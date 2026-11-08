// Ensaio visual de leitura, com a aplicação apontada para lgpd_poc_teste.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

async function verificar(browser, origem, largura) {
  const pagina = await browser.newPage({ viewport: { width: largura, height: 900 } });
  const erros = [];
  pagina.on('pageerror', erro => erros.push(erro.message));
  await pagina.route('**/*', rota => {
    const pedido = rota.request();
    return pedido.method() === 'GET' && new URL(pedido.url()).origin === origem
      ? rota.continue() : rota.abort();
  });
  try {
    const objeto = pagina.locator('#objeto_principal_id');
    const canais = pagina.locator('#canais-habituais');
    const selecionados = canais.locator('input:checked');
    const situacao = valor => canais.locator('input[value="' + valor + '"]');
    for (const [conta, secretaria] of [['CONTA-C1', 'Finanças'], ['CONTA-A1', 'Planejamento Urbano e Gestão Estratégica']]) {
      await pagina.goto(origem + '/central?conta_id=' + conta);
      await pagina.getByRole('button', { name: 'Abrir Painel de Registros' }).click();
      await pagina.waitForURL('**/painel?**');
      assert(await pagina.getByRole('link', { name: 'Voltar à Central de Acesso' }).isVisible());
      await pagina.getByRole('link', { name: 'Criar novo Registro LGPD' }).click();
      await pagina.waitForURL('**/registros/novo?**');
      assert((await pagina.locator('.detalhe').innerText()).includes('Secretaria responsável: ' + secretaria));
      assert.equal(await pagina.locator('select[name=unidade_id]').count(), 0);
      assert(await situacao('identificados').isDisabled());
      await pagina.locator('input[name=tipo_objeto][value=servico]').check();
      assert.equal(await selecionados.count(), 0);
      assert(await situacao('identificados').isDisabled());
      if (conta === 'CONTA-C1') {
        await objeto.selectOption('OBJ-SRV-902');
        assert.equal(await selecionados.count(), 0);
        assert(await situacao('identificados').isEnabled());
        await situacao('identificados').check();
        assert.equal(await canais.locator('.sugestao-canal:visible').count(), 0);
        assert.equal(await canais.locator('input[type=checkbox]:checked').count(), 0);
        await situacao('CNL-003').check();
        await situacao('nenhum').check();
        assert.equal(await selecionados.count(), 1);
        await situacao('informacao_insuficiente').check();
        assert((await pagina.locator('#orientacao-contexto').innerText()).includes('Único contexto'));
        assert.equal(await pagina.locator('#contexto_id').inputValue(), '');
        await pagina.locator('#contexto_id').selectOption('CTX-COM-01');
        assert((await pagina.locator('#orientacao-contexto').innerText()).includes('seleção de fornecedores'));
        assert(await situacao('informacao_insuficiente').isChecked());
        assert.equal(await selecionados.count(), 1);
      } else {
        await objeto.selectOption('OBJ-SRV-001');
        await situacao('identificados').check();
        assert.equal(await canais.locator('.sugestao-canal:visible').count(), 2);
        assert.equal(await canais.locator('input[type=checkbox]:checked').count(), 0);
        await situacao('CNL-002').check();
        await objeto.selectOption('OBJ-SRV-002');
        assert.equal(await selecionados.count(), 0);
        await situacao('identificados').check();
        assert.equal(await canais.locator('.sugestao-canal:visible').count(), 1);
        await pagina.locator('input[name=tipo_objeto][value=atividade]').check();
        assert(await situacao('identificados').isDisabled());
        assert.equal(await selecionados.count(), 0);
      }
      assert(await pagina.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await pagina.getByRole('link', { name: /Voltar ao painel/ }).click();
      await pagina.waitForURL('**/painel?**');
      assert.equal(new URL(pagina.url()).pathname, '/painel');
    }
    assert.deepEqual(erros, []);
    console.log('OK: Gama e Alfa, cascata de canais e retorno, ' + largura + ' px');
  } finally {
    await pagina.close();
  }
}

(async () => {
  const origem = new URL(process.env.CENTRAL_TEST_URL);
  assert.equal(origem.hostname, '127.0.0.1');
  const browser = await chromium.launch({ channel: 'msedge', chromiumSandbox: true });
  try {
    for (const largura of [1440, 360]) await verificar(browser, origem.origin, largura);
  } finally {
    await browser.close();
  }
})().catch(erro => { console.error(erro); process.exitCode = 1; });
