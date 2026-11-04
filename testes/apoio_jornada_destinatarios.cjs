const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const escolha={name:'campo__10.2',value:'Outra Secretaria',checked:true};
const eventos={}, principal={elements:[escolha],addEventListener(t,f){this[t]=f;},tagName:'FORM'};
const seletor={value:'',options:[],replaceChildren(o){this.options=[o];},add(o){this.options.push(o);}};
const aviso={},bloco={querySelector(){return aviso;},querySelectorAll(){return [seletor];},addEventListener(t,f,captura){eventos[t]=f;assert.equal(captura,true);}};
principal.closest=()=>bloco;principal.getAttribute=()=>'/registros/FICTICIO/form1-integral/bloco-10/salvar';
const chamadas=[],window={location:{href:'https://poc.invalid/registros/FICTICIO?conta_id=CONTA-FICTICIA'},saidaForm1:{salvarPendentes(o){chamadas.push(o);}}};
vm.runInNewContext(fs.readFileSync('app/estaticos/jornada_destinatarios_form1.js','utf8'),{
 window,URL,Option:class{constructor(text,value){this.text=text;this.value=value;}},document:{getElementById(){return principal;}}
});
assert.equal(seletor.options[1].value,'Outra Secretaria'); // Categoria disponível antes de gravar.
seletor.value='Outra Secretaria';escolha.checked=false;principal.change();
assert.equal(seletor.value,'Outra Secretaria');assert.match(seletor.options[1].text,/reveja/);
function enviar(f,value){let prevenido=false,interrompido=false;eventos.submit({target:f,submitter:{value},preventDefault(){prevenido=true;},stopImmediatePropagation(){interrompido=true;}});assert.ok(prevenido&&interrompido);}
enviar(principal,'proximo');assert.match(chamadas[0].destino,/#titulo-bloco-11$/);
enviar(principal,'permanecer');assert.match(chamadas[1].destino,/#titulo-bloco-10$/);
const adicionar={tagName:'FORM',getAttribute(){return '/destinatarios/adicionar';}};
enviar(adicionar);assert.match(chamadas[2].destino,/#titulo-destinatarios-10-2-1$/);assert.equal(chamadas[2].adicional,null);
const remover={tagName:'FORM',getAttribute(){return '/destinatarios/ID-FICTICIO/remover';}};
enviar(remover);assert.equal(chamadas[3].adicional,remover);
window.saidaForm1=null;enviar(principal);assert.match(aviso.textContent,/respostas continuam/);
console.log('Categorias locais, interceptação e destinos da jornada: aprovados (DOM simulado).');
