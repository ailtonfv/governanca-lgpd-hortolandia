// Executa os trechos reais de seleção/foco com geometria simulada, sem aceite visual.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const html = fs.readFileSync('app/paginas/registro.html','utf8');
const selecao = html.slice(html.indexOf('var destinoInicial = blocoDaUrl'),html.indexOf('var blocoGuardado ='));
const posicionar = html.slice(html.indexOf('function posicionarDestinoForm1('),html.indexOf('function sincronizarSinalizacaoObrigatoriedade('));
const chamada = html.match(/exibirEtapa\(etapaInicial, destinoInicial \? window.location.hash : null, blocoInicial\);/)[0];
for (const id of ['instrumentos-registro','titulo-form1-integral']) {
  let focado = false, destinoEtapa, topo;
  const alvo = {id, setAttribute(k,v){assert.equal(k,'tabindex');assert.equal(v,'-1');},
    focus(){focado=true;},closest(){return null;},getBoundingClientRect(){return {top:1000};}};
  const contexto = {blocoDaUrl:null,preValidacaoDaUrl:false,destinatariosDaUrl:false,numeroBloco:null,
    etapaInicial:'1',blocoInicial:1,exibirEtapa(etapa,destino){destinoEtapa=destino;},
    window:{location:{hash:'#'+id},scrollY:0,requestAnimationFrame(fn){fn();},scrollTo(p){topo=p.top;}},
    document:{getElementById(chave){return chave===id?alvo:chave==='retorno-painel-form1'?{getBoundingClientRect(){return {height:50};}}:null;}}};
  vm.runInNewContext(selecao+'\n'+chamada+'\n'+posicionar+'\nposicionarDestinoForm1(destinoInicial);',contexto);
  assert.equal(destinoEtapa,'#'+id);
  assert.equal(focado,true);
  assert.equal(topo,926);
}
console.log('Destino e foco dos instrumentos preservados (DOM simulado).');
