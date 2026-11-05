/* Comportamento real dos scripts; não substitui inspeção visual. */
const fs = require('fs');
const vm = require('vm');
const assert = require('node:assert/strict');

let listener, impedido = false, focado = false, enviado = false, sujo = true;
const aviso = {textContent: '', focus() { focado = true; }};
const formulario = {addEventListener(tipo, fn) { listener = fn; }, querySelector() { return aviso; }};
const contexto = {
  document: {querySelector() { return formulario; }},
  window: {saidaForm1: {temAlteracoes() { return sujo; }, envioNormal() { enviado = true; }}},
};
vm.runInNewContext(fs.readFileSync('app/estaticos/extensao_medidas_form1.js', 'utf8'), contexto);
listener({preventDefault() { impedido = true; }});
assert.ok(impedido && focado && !enviado);
assert.match(aviso.textContent, /Salve suas alterações/);
sujo = false; impedido = false;
listener({preventDefault() { impedido = true; }});
assert.ok(enviado && !impedido);

// Executa a função de recuperação que realmente é entregue na página.
const pagina = fs.readFileSync('app/paginas/registro.html', 'utf8');
const inicio = pagina.indexOf('    function restaurarTentativa(formulario) {');
const fim = pagina.indexOf('\n    var ', pagina.indexOf('\n    }', inicio));
const funcao = pagina.slice(inicio, fim);
let campo = {name: 'campo__13.2', value: '', type: 'select-one'};
let estrutura = 'F1-C3-REV13-EXT-MEDIDAS-v1';
let dados = [['campo__13.2', 'Sempre']];
const recuperar = {
  atualizarEstado() {},
  chaveRecuperacao() { return 'tentativa'; },
  sessaoForm1: {getItem() { return JSON.stringify(dados); }},
  window: {},
  formulario: {
    dataset: {},
    querySelector() { return {value: estrutura}; },
    querySelectorAll() { return [campo]; },
  },
};
vm.createContext(recuperar);
vm.runInContext(funcao + '\nrestaurarTentativa(formulario);', recuperar);
assert.equal(campo.value, ''); // Memória anterior ao discriminador.
dados = [['estrutura_lida', 'F1-C3-REV13'], ['campo__13.2', 'Sempre']];
vm.runInContext('restaurarTentativa(formulario);', recuperar);
assert.equal(campo.value, ''); // Aba legada não converte sua resposta.
dados = [['estrutura_lida', estrutura], ['campo__13.2', 'Não']];
vm.runInContext('restaurarTentativa(formulario);', recuperar);
assert.equal(campo.value, 'Não'); // Recuperação da mesma versão permanece válida.
console.log('Adoção e recuperação versionada: verificadas em JavaScript.');
