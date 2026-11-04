// DOM simulado: execução da navegação real; não constitui aceite visual.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const html = fs.readFileSync('app/paginas/registro.html','utf8');
const codigo = html.slice(html.indexOf('    function destinoDaPendencia'), html.indexOf('    botoes.forEach', html.indexOf('    function destinoDaPendencia')));
for (const modo of ['editar','consultar','oculto','indisponivel']) {
 for (const [campo, bloco, etapa] of [['5.1','5','2'],['2.4','2','1']]) {
  let foco, rolagem, chamada;
  const estado = {}, respostas = {valor:'resposta fictícia não salva'};
  function alvo(tag) { return {tagName:tag,style:{},classList:{add(){},remove(){}},setAttribute(){},focus(){foco=this;},scrollIntoView(op){rolagem={alvo:this,op};},closest(){return null;}}; }
  const titulo=alvo('H3'), grupo=alvo('FIELDSET'), controle=alvo('INPUT'), leitura=alvo('SECTION');
  controle.closest=s=>s.includes('data-condicional') ? (modo==='oculto'?{}:null) : grupo;
  leitura.closest=s=>s.includes('campo-integral')?leitura:null;
  const ctx={raiz:{dataset:{modoConsulta:modo==='consultar'?'true':'false'},querySelector(){return estado;},querySelectorAll(){return [];}},
    document:{getElementById(id){return id==='consulta-integral-'+campo && modo==='consultar'?leitura:id==='titulo-bloco-'+bloco?titulo:id==='retorno-painel-form1'?{getBoundingClientRect(){return {height:48};}}:null;}},
    controleDoCampo(){return modo==='indisponivel'?null:controle;},
    exibirEtapa(...args){chamada=args;},atualizarPainelJornada(){},window:{setTimeout(){},matchMedia(){return {matches:true};}}};
  vm.runInNewContext(codigo,ctx);
  ctx.focarPendencia({dataset:{pendenciaCampo:campo,pendenciaBloco:bloco,pendenciaEtapa:etapa,pendenciaDestino:'campo'}});
  assert.deepEqual(chamada,[etapa,'#titulo-bloco-'+bloco,bloco]);
  assert.equal(foco,modo==='editar'?controle:modo==='consultar'?leitura:titulo);
  assert.equal(rolagem.op.block,'start'); assert.equal(rolagem.op.behavior,'auto');
  assert.equal(rolagem.alvo.style.scrollMarginTop,'72px');
  assert.equal(respostas.valor,'resposta fictícia não salva');
  if(modo==='consultar') assert.match(estado.textContent,/Somente leitura/);
  if(modo==='oculto') assert.match(estado.textContent,/condição ativa/);
  if(modo==='indisponivel') assert.match(estado.textContent,/não possui destino disponível/);
 }
}
console.log('Consulta, edição, destino ausente, condicional e início da pergunta: aprovados.');
