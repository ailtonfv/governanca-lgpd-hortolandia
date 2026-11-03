// Ensaio de comportamento JavaScript com DOM simulado; não é inspeção visual.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync('app/paginas/registro.html', 'utf8');
const auxiliares = html.slice(html.indexOf('var sessaoForm1 ='), html.indexOf('function sincronizarSinalizacaoObrigatoriedade'));
const navegacao = html.slice(html.indexOf('(function iniciarNavegacaoForm1()'), html.indexOf('(function iniciarFeedbackDeSalvamento()'));

for (const indisponivel of [false, true]) {
 for (const alturaJanela of [600, 900]) {
  for (const alturaBarra of [0, 48, 96]) {
  for (const inicial of [1, 2, 3, 4, 8, 14]) {
    const eventos = {};
    let focado, rolado;
    let janela;
    const criar = (dataset = {}) => ({
      dataset, style: {}, attrs: {}, hidden: false,
      classList: { toggle() {}, add() {}, remove() {} },
      addEventListener(tipo, acao) { this[tipo] = acao; },
      setAttribute(nome, valor) { this.attrs[nome] = valor; },
      removeAttribute(nome) { delete this.attrs[nome]; },
      focus() { focado = this; },
      scrollIntoView(opcoes) { rolado = this; assert.equal(opcoes.block, 'start'); },
      closest() { return criar(); }
    });
    const titulos = Array.from({length: 14}, (_, i) => Object.assign(criar(), {id: 'titulo-bloco-' + (i + 1)}));
    const blocos = titulos.map(t => Object.assign(criar(), {querySelector() { return t; }}));
    const alturas = titulos.map((_, i) => i === 1 ? 2400 : 300);
    const ordem = [];
    blocos.forEach((b, i) => {
      b.getBoundingClientRect = () => ({top: (ordem.indexOf(etapas.find(p => !p.hidden)) < ordem.indexOf(progresso) ? 420 : 1800) - janela.scrollY, height: alturas[i]});
      titulos[i].closest = () => b;
    });
    const etapas = [1, 2, 3, 4].map(n => Object.assign(criar({etapaPainel: String(n)}), {
      querySelectorAll() { return blocos.filter((_, i) => (i < 3 ? 1 : i < 8 ? 2 : i < 11 ? 3 : 4) === n); }
    }));
    const botoes = [1, 2, 3, 4].map(n => criar({etapaAlvo: String(n)}));
    const mapa = titulos.map((_, i) => criar({painelBloco: String(i + 1)}));
    const anterior = criar({blocoAnterior: '2'});
    const progresso = Object.assign(criar(), {querySelector() {return null;}, querySelectorAll() {return [];}});
    ordem.push(progresso, ...etapas);
    const raiz = Object.assign(criar({registroId: 'FICTICIO'}), {
      insertBefore(painel, referencia) { ordem.splice(ordem.indexOf(painel), 1); ordem.splice(ordem.indexOf(referencia), 0, painel); },
      querySelector(seletor) { return seletor === '[data-painel-progresso]' ? progresso : seletor.includes('data-painel-bloco="2"') ? mapa[1] : null; },
      querySelectorAll(seletor) {
        return ({'[data-etapa-alvo]': botoes, '[data-etapa-painel]': etapas,
          '[data-painel-bloco]': mapa, '[data-bloco-anterior]': [anterior]})[seletor] || [];
      }
    });
    mapa.forEach(b => { b.click = () => b.clickHandler(); b.addEventListener = (_, acao) => { b.clickHandler = acao; }; });
    const memoria = new Map([['form1-integral-etapa-FICTICIO', '4'], ['form1-integral-bloco-FICTICIO', '14']]);
    const storage = {getItem(k) { return memoria.get(k) || null; }, setItem(k,v) { memoria.set(k,v); }, removeItem(k) {memoria.delete(k);}};
    janela = {
      scrollY: 0,
      scrollTo(opcoes) {
        const ativo = blocos.findIndex(b => !b.hidden);
        // Limite de rolagem com acompanhamento abaixo do bloco, sem altura mínima.
        const limite = 420 + alturas[ativo] + 1200 - alturaJanela;
        janela.scrollY = Math.min(opcoes.top, limite);
        rolado = titulos[ativo];
      },
      location: {hash: '#titulo-bloco-' + inicial},
      history: {replaceState(_, __, hash) { janela.location.hash = hash; }},
      requestAnimationFrame(acao) { acao(); },
      addEventListener(tipo, acao) { eventos[tipo] = acao; }, confirm() { return true; }
    };
    Object.defineProperty(janela, 'sessionStorage', {get() { if (indisponivel) throw Error('Storage bloqueado'); return storage; }});
    const contexto = {
      window: janela, document: {
        readyState: 'loading', querySelector() { return raiz; },
        getElementById(id) { return id === 'retorno-painel-form1' ? {getBoundingClientRect() {return {height: alturaBarra};}} : id === 'mensagem-registro' ? {getBoundingClientRect() { return {height: 60}; }} : titulos.find(t => t.id === id); }
      }, sincronizarControlesForm1() {}
    };
    vm.runInNewContext(auxiliares + navegacao, contexto);
    assert.equal(focado, titulos[inicial - 1]);
    assert.equal(rolado, focado);
    assert.equal(blocos[inicial - 1].getBoundingClientRect().top, 96 + alturaBarra);
    assert.ok(ordem.indexOf(etapas.find(p => !p.hidden)) < ordem.indexOf(progresso));
    assert.equal(blocos.filter(b => !b.hidden).length, 1);
    eventos.load();
    for (const n of [3, 2, 4, 5, 14, 1]) {
      mapa[n - 1].click();
      assert.equal(rolado, titulos[n - 1]);
      assert.equal(janela.location.hash, '#titulo-bloco-' + n);
      assert.equal(blocos[n - 1].hidden, false);
      assert.equal(blocos[n - 1].getBoundingClientRect().top, 96 + alturaBarra);
    }
    anterior.click();
    assert.equal(rolado, titulos[1]);
    botoes[1].click();
    assert.equal(rolado, titulos[3]);
  }
  }
 }
}
console.log('Navegação, foco, retorno e armazenamento bloqueado: aprovados (DOM simulado).');
