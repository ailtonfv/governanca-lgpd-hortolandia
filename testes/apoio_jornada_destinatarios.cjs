const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const escolha={name:'campo__10.2',value:'Outra Secretaria',checked:true};
const segunda={name:'campo__10.2',value:'Outro órgão público',checked:false};
const eventos={}, principal={elements:[escolha,segunda],addEventListener(t,f){this[t]=f;},tagName:'FORM'};
function categoria(novo,valor='') {
 const orientacao={};
 return {value:valor,options:[],dataset:{destinatarioNovo:String(novo)},form:{editado:false},orientacao,
 replaceChildren(o){this.options=[o];},add(o){this.options.push(o);},
 addEventListener(t,f){this[t]=f;},dispatchEvent(e){this.change(e);},setCustomValidity(v){this.validacao=v;},
 closest(){return {querySelector(){return orientacao;}};}};
}
const seletor=categoria(true),existente=categoria(false,'Outra Secretaria');
const aviso={},bloco={querySelector(){return aviso;},querySelectorAll(){return [seletor,existente];},addEventListener(t,f,captura){eventos[t]=f;assert.equal(captura,true);}};
principal.closest=()=>bloco;principal.getAttribute=()=>'/registros/FICTICIO/form1-integral/bloco-10/salvar';
const chamadas=[],automaticas=[],window={location:{href:'https://poc.invalid/registros/FICTICIO?conta_id=CONTA-FICTICIA'},saidaForm1:{salvarPendentes(o){chamadas.push(o);},alterado(f){return f.editado;},registrarCategoriaAutomatica(c){automaticas.push(c.value);}}};
vm.runInNewContext(fs.readFileSync('app/estaticos/jornada_destinatarios_form1.js','utf8'),{
 window,URL,Event:class{constructor(type){this.type=type;}},Option:class{constructor(text,value){this.text=text;this.value=value;}},document:{getElementById(){return principal;}}
});
assert.equal(seletor.options[1].value,'Outra Secretaria'); // Categoria disponível antes de gravar.
assert.equal(seletor.value,'Outra Secretaria');assert.match(seletor.orientacao.textContent,/Única categoria/);
assert.deepEqual(automaticas,['Outra Secretaria']);
function atualizar(){principal.change({target:escolha});}
// Duas categorias: uma ficha nova não presume a primeira; a persistida não muda.
segunda.checked=true;atualizar();assert.equal(seletor.value,'');assert.equal(existente.value,'Outra Secretaria');
assert.deepEqual(seletor.options.map(o=>o.value),['','Outra Secretaria','Outro órgão público']);
seletor.value='Outro órgão público';seletor.change({});seletor.form.editado=true;
atualizar();assert.equal(seletor.value,'Outro órgão público');
// Valor escolhido preservado, com alerta e validação, quando deixa de ser aplicável.
segunda.checked=false;atualizar();assert.equal(seletor.value,'Outro órgão público');
assert.match(seletor.validacao,/Reveja/);assert.equal(seletor.options.at(-1).disabled,true);
assert.match(seletor.orientacao.textContent,/histórico/);
// Nenhuma categoria e "A confirmar" não oferecem um destinatário válido.
seletor.value='';seletor.form.editado=false;escolha.checked=false;atualizar();
assert.equal(seletor.value,'');assert.match(seletor.orientacao.textContent,/Responda.*10.2/);
assert.equal(existente.value,'Outra Secretaria');assert.match(existente.validacao,/Reveja/);
principal.elements.push({name:'campo__10.2',value:'A confirmar',checked:true});atualizar();
assert.deepEqual(seletor.options.map(o=>o.value),['']);
escolha.checked=true;atualizar();assert.equal(seletor.value,'Outra Secretaria');
assert.equal(existente.validacao,'');
// Não recalcular uma sugestão quando já há identificação digitada.
seletor.form.editado=true;segunda.checked=true;atualizar();assert.equal(seletor.value,'Outra Secretaria');
// Uma inclusão já confirmada não é recalculada após falha em outro comando.
seletor.form.inert=true;escolha.checked=false;atualizar();assert.equal(seletor.value,'Outra Secretaria');
function enviar(f,value){let prevenido=false,interrompido=false;eventos.submit({target:f,submitter:{value},preventDefault(){prevenido=true;},stopImmediatePropagation(){interrompido=true;}});assert.ok(prevenido&&interrompido);}
enviar(principal,'proximo');assert.match(chamadas[0].destino,/#titulo-bloco-11$/);
enviar(principal,'permanecer');assert.match(chamadas[1].destino,/#titulo-bloco-10$/);
const adicionar={tagName:'FORM',getAttribute(){return '/destinatarios/adicionar';}};
enviar(adicionar);assert.match(chamadas[2].destino,/#titulo-destinatarios-10-2-1$/);assert.equal(chamadas[2].adicional,adicionar);
const remover={tagName:'FORM',getAttribute(){return '/destinatarios/ID-FICTICIO/remover';}};
enviar(remover);assert.equal(chamadas[3].adicional,remover);
window.saidaForm1=null;enviar(principal);assert.match(aviso.textContent,/respostas continuam/);
console.log('Categorias locais, interceptação e destinos da jornada: aprovados (DOM simulado).');
