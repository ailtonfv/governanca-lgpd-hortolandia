// Execução de JavaScript com DOM simulado; não constitui aceitação visual.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const html = fs.readFileSync('app/paginas/registro.html', 'utf8');
const contexto = {window: {}};
vm.runInNewContext(fs.readFileSync('app/estaticos/localizador_form1.js', 'utf8'), contexto);
const entrada = {value: '', addEventListener(_, fn) {this.input = fn;}};
const estado = {}, itens = [
 {dataset: {localizarId: '2.4', localizarTitulo: 'Identificação do fluxo'}},
 {dataset: {localizarId: '2.4.1', localizarTitulo: 'Identificação complementar'}},
 {dataset: {localizarId: '14.2.3', localizarTitulo: 'Documento institucional'}}
];
const lista = {querySelectorAll() {return itens;}};
const area = {querySelector(s) {return s === 'ul' ? lista : s === '[role="status"]' ? estado : entrada;}};
contexto.window.iniciarLocalizadorForm1({querySelector() {return area;}});
for (const [busca, esperados] of [['2.4', ['2.4']], ['identificacao', ['2.4', '2.4.1']], ['DOCUMENTO', ['14.2.3']], ['inexistente', []], ['', []]]) {
 entrada.value = busca; entrada.input();
 assert.deepEqual(itens.filter(i => !i.hidden).map(i => i.dataset.localizarId), esperados);
 assert.equal(lista.hidden, esperados.length === 0);
 assert.ok(estado.textContent.length > 0);
}
// Reutiliza a função real de navegação para campo ativo e condicional oculto.
const funcoesDestino = html.slice(html.indexOf('    function destinoDaPendencia'), html.indexOf('    botoes.forEach', html.indexOf('    function destinoDaPendencia')));
for (const oculto of [false, true]) {
 let focado, etapa;
 const titulo = {tagName:'H3', closest(){return this;}, classList:{add(){},remove(){}}, setAttribute(){}, focus(){focado=this;}, scrollIntoView(){}};
 const controle = {tagName:'INPUT', closest(s){return s.includes('data-condicional') ? (oculto ? {} : null) : titulo;}, focus(){focado=this;}};
 const mensagem = {};
 const ctx = {raiz:{querySelector(){return mensagem;},querySelectorAll(){return [];}},document:{getElementById(id){return id.startsWith("titulo-bloco-") ? titulo : null;}},
 controleDoCampo(){return controle;},exibirEtapa(n){etapa=n;},atualizarPainelJornada(){},window:{setTimeout(){},matchMedia(){return {matches:true};}}};
 vm.runInNewContext(funcoesDestino, ctx);
 ctx.focarPendencia({dataset:{pendenciaCampo:'2.4',pendenciaBloco:'2',pendenciaEtapa:'1',pendenciaDestino:'campo'}});
 assert.equal(etapa,'1'); assert.equal(focado,oculto ? titulo : controle);
 if(oculto) assert.match(mensagem.textContent,/condição ativa/);
}
// Feedback: sucesso exige retorno positivo, tentativa correspondente e versão confirmada.
const inicio = html.indexOf('(function iniciarFeedbackDeSalvamento()');
const feedback = html.slice(inicio, html.indexOf('</script>', inicio));
for (const caso of ['inicial', 'sucesso', 'outra-versao', 'erro']) {
 const memoria = new Map(), prefixo='form1-integral-tentativa-FICTICIO-';
 if(caso !== 'inicial') {
  memoria.set(prefixo+'confirmacao', JSON.stringify({acao:'/salvar',versao:1}));
  memoria.set(prefixo+'2',JSON.stringify([['campo__2.4','texto digitado fictício']]));
 }
 const valor = {name:'campo__2.4',type:'text',tagName:'INPUT',value:'resposta persistida'};
 const versao = {name:'versao_lida',type:'hidden',value:caso === 'outra-versao' ? '3':'2'};
 const status = {textContent:'Sem alterações para salvar.',classList:{add(){},remove(){}}};
 const f = {dataset:{},classList:{contains(){return true;}},getAttribute(){return '/salvar';},
 closest(){return {querySelector(){return {id:'titulo-bloco-2'};}};},
 querySelector(s){return s === '[data-estado-salvamento]' ? status : s === '[name="versao_lida"]' ? versao : null;},
 querySelectorAll(s){return s === '[name]' ? [valor,versao] : [];},addEventListener(tipo,fn){this[tipo]=fn;}};
 const win={location:{search:caso==='erro'?'?erro=1':caso==='inicial'?'':'?erro=0'},addEventListener(){}};
 const ctx={window:win,URLSearchParams,document:{querySelectorAll(){return [f];},querySelector(){return {dataset:{registroId:'FICTICIO'}};},getElementById(){return {textContent:'Rascunho salvo com sucesso às 10:00.'};}},
 sessaoForm1:{getItem(k){return memoria.get(k)||null;},setItem(k,v){memoria.set(k,v);},removeItem(k){memoria.delete(k);},chaves(){return [...memoria.keys()];}}};
 vm.runInNewContext(feedback,ctx);
 assert.equal(status.textContent.includes('Rascunho salvo com sucesso.'),caso==='sucesso');
 if(caso==='erro') { assert.equal(valor.value,'texto digitado fictício'); assert.equal(f.dataset.alterado,'true'); assert.match(status.textContent,/salvamento falhou/); }
 f.input(); assert.match(status.textContent,/Alterações não salvas/);
 win.saidaForm1={alterado(){return false;}}; f.change(); assert.match(status.textContent,/Sem alterações para salvar/);
}
console.log('Busca explícita, destinos condicionais e feedback de salvamento: aprovados.');
