/* DOM simulado: comprova comportamento, não aceitação visual. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const formularios = new Map();
let sujo = true, envios = 0;
for (const seletor of ['[data-adotar-medidas]', '[data-adotar-guarda]', '[data-adotar-rev18]']) {
  const aviso = {textContent: '', focus() { this.focado = true; }};
  formularios.set(seletor, {
    aviso,
    querySelector() { return aviso; },
    addEventListener(tipo, acao) { this.enviar = acao; },
  });
}
vm.runInNewContext(fs.readFileSync('app/estaticos/extensao_medidas_form1.js', 'utf8'), {
  document: {querySelector(seletor) { return formularios.get(seletor); }},
  window: {saidaForm1: {temAlteracoes() { return sujo; }, envioNormal() { envios++; }}},
});
for (const form of formularios.values()) {
  let impedido = false;
  form.enviar({preventDefault() { impedido = true; }});
  assert.ok(impedido && form.aviso.focado);
}
assert.equal(envios, 0);
sujo = false;
for (const form of formularios.values()) form.enviar({preventDefault() { assert.fail('Não havia alterações locais'); }});
assert.equal(envios, formularios.size);

// Condições declarativas executadas pelo mesmo script usado nos 14 blocos.
const definicao = JSON.parse(fs.readFileSync('app/catalogos/form1_rev13_ext_guarda_v1.json', 'utf8'));
const campos = definicao.campos.filter(c => c.condicoes.length).map(c => ({
  id: c.id, dataset: {condicoes: JSON.stringify(c.condicoes)},
}));
const eventos = new Map(), valores = new Map();
const html = fs.readFileSync('app/paginas/registro.html', 'utf8');
const inicio = html.indexOf("  document.querySelectorAll('[data-condicoes]').forEach");
const fim = html.indexOf('  (function aplicarExclusividades', inicio);
vm.runInNewContext(html.slice(inicio, fim), {
  document: {
    querySelectorAll() { return campos; },
    getElementsByName(nome) { return [{addEventListener(tipo, fn) {
      if (!eventos.has(nome)) eventos.set(nome, []);
      eventos.get(nome).push(fn);
    }}]; },
  },
  valorDoCampo(nome) { return valores.get(nome) || []; },
  sincronizarControlesForm1() {},
});
function responder(id, resposta) {
  valores.set('campo__' + id, Array.isArray(resposta) ? resposta : [resposta]);
  (eventos.get('campo__' + id) || []).forEach(fn => fn());
}
function visivel(id) { return !campos.find(c => c.id === id).hidden; }
assert.ok(campos.every(c => c.hidden));
responder('12.4.2', 'Sim');
assert.ok(visivel('12.4.2.1') && !visivel('12.4.1'));
responder('12.4.3', 'Em alguns casos');
assert.ok(visivel('12.4.3.1'));
responder('12.4.2', 'Não se aplica');
assert.ok(!visivel('12.4.2.1') && visivel('12.4.3.1'));
responder('12.4.3', 'A confirmar');
assert.ok(!visivel('12.4.3.1'));
responder('12.5', 'Sim');
assert.ok(visivel('12.5.1') && visivel('12.5.2') && !visivel('12.5.1.1'));
responder('12.5.1', ['Entre sistemas', 'Outra situação']);
assert.ok(visivel('12.5.1.1'));
responder('12.5', 'Não');
assert.ok(!visivel('12.5.1.1') && !visivel('12.5.2'));
console.log('Adoções independentes e condições por operação: verificadas.');
