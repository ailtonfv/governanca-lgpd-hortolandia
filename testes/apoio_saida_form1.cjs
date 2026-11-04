// Executa o adaptador real. DOM simulado: não constitui aceite visual.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const codigo = fs.readFileSync('app/estaticos/saida_form1.js', 'utf8');
function elemento() {
  return {dataset: {}, eventos: {}, attrs: {}, disabled: false,
    addEventListener(tipo, fn) {this.eventos[tipo] = fn;},
    dispatchEvent() {},
    setAttribute(k,v) {this.attrs[k] = v;}, removeAttribute(k) {delete this.attrs[k];},
    focus() {this.focado = true;}, textContent: ''};
}
function formulario(numero, sufixo = 'salvar') {
  const f = elemento();
  f.action = `https://poc.invalid/registros/FICTICIO/form1-integral/bloco-${numero}/${sufixo}`;
  f.elements = [];
  f.campo = (name, value, type = 'text') => {
    const c = Object.assign(elemento(), {name,value,type,checked:false});
    c.closest = s => s.includes('etapa') ? f.etapaOculta : f.condicaoOculta;
    f.elements.push(c); return c;
  };
  f.campo('conta_id','CONTA-FICTICIA','hidden');
  f.campo('comando_id',`CMD-FICTICIO-${numero}-${sufixo}`,'hidden');
  f.campo('versao_lida','1','hidden');
  f.texto = f.campo('campo__'+numero+'.1','');
  f.check = f.campo('opcao','A confirmar','checkbox');
  f.estado = elemento();
  f.querySelector = s => s === '[data-estado-salvamento]' ? f.estado : f.elements.find(c => s === `[name="${c.name}"]`);
  f.getAttribute = () => f.action;
  f.closest = s => s.includes('condicional') ? f.condicaoOculta : {querySelector() {return {id:'titulo-bloco-'+numero};}};
  return f;
}
class Dados {
  constructor(f) {this.dados = new Map(f.elements.filter(c => !c.disabled && (!['checkbox','radio'].includes(c.type) || c.checked)).map(c => [c.name,c.value]));}
  set(k,v) {this.dados.set(k,v);} get(k) {return this.dados.get(k);}
}
function preparar(numeros = [2,3]) {
  const forms = numeros.map(n => formulario(n));
  const link = elemento(); link.href='https://poc.invalid/?conta_id=CONTA-FICTICIA';
  const barra = elemento(); barra.querySelector = () => link; barra.getBoundingClientRect = () => ({height:48});
  const salvar=elemento(), sair=elemento(), continuar=elemento(), erro=elemento();
  const dialogo=elemento(); dialogo.showModal = () => {dialogo.aberto=true;}; dialogo.close = () => {dialogo.aberto=false;};
  dialogo.querySelector = s => ({'[data-salvar-voltar]':salvar,'[data-sair-sem-salvar]':sair,'[data-continuar-preenchendo]':continuar,'[data-erro-saida]':erro})[s];
  const raiz={dataset:{registroId:'FICTICIO'},querySelectorAll() {return forms;}};
  const window={location:{href:'https://poc.invalid/registros/FICTICIO?conta_id=CONTA-FICTICIA',assign(u) {window.destino=u;}}, addEventListener() {}};
  const env={window, requests:[], forms, link, dialogo,salvar,sair,continuar,erro};
  function pagina(versao) {
    const novos=forms.map((f,i) => {
      const n=formulario(numeros[i]); n.action=f.action;
      n.querySelector('[name="versao_lida"]').value=String(versao);
      n.querySelector('[name="comando_id"]').value=`CMD-RETORNADO-${versao}-${i}`;
      return n;
    });
    return {querySelectorAll() {return novos;},querySelector() {return {dataset:{registroId:'FICTICIO'},querySelector() {return {value:String(versao)};}};}};
  }
  env.resposta=(versao,erro='0') => ({ok:true,url:window.location.href+'&erro='+erro+'&mensagem=Recusa%20ficticia',text:async()=>String(versao)});
  const contexto={window, document:{querySelector() {return raiz;},getElementById(id) {return id==='retorno-painel-form1'?barra:dialogo;},documentElement:{style:{setProperty(){}}}},
    FormData:Dados,URL,TypeError,Event:class {},DOMParser:class {parseFromString(t) {return pagina(Number(t));}},
    fetch:async(url,opts)=>{env.requests.push({url,opts}); return env.fetch ? env.fetch(url,opts) : env.resposta(Number(opts.body.get('versao_lida'))+1);}};
  vm.runInNewContext(codigo,contexto);
  env.abrir=()=>link.eventos.click({preventDefault(){}});
  return env;
}
(async()=>{
  let e=preparar(); e.abrir(); assert.equal(e.window.destino,e.link.href); assert.equal(e.requests.length,0);
  e=preparar(); e.forms[0].texto.value='Descrição fictícia'; assert.equal(e.window.saidaForm1.temAlteracoes(),true);
  e.forms[0].texto.value=''; assert.equal(e.window.saidaForm1.temAlteracoes(),false);
  e.forms[0].check.checked=true; assert.equal(e.window.saidaForm1.temAlteracoes(),true);
  e.forms[0].check.checked=false;
  const multiplo=e.forms[0].texto; multiplo.multiple=true; multiplo.options=[{value:'FICTICIO',selected:true}];
  assert.equal(e.window.saidaForm1.temAlteracoes(),true);

  e=preparar(); e.forms[0].texto.value='Texto local'; e.abrir();
  assert.ok(e.dialogo.aberto && e.continuar.focado); e.continuar.eventos.click();
  assert.equal(e.dialogo.aberto,false); assert.equal(e.forms[0].texto.value,'Texto local'); assert.equal(e.window.destino,undefined);
  e.abrir(); e.dialogo.eventos.cancel({preventDefault(){throw Error('Escape deve permanecer disponível');}});
  e.sair.eventos.click(); assert.equal(e.window.destino,e.link.href); assert.equal(e.requests.length,0);
  assert.equal(e.forms[0].texto.value,''); assert.equal(e.window.saidaForm1.temAlteracoes(),false);

  // Bloco longo e curto, etapa oculta e seleção condicional: envio sem perdas.
  e=preparar([2,3]); e.forms.forEach(f=>{f.texto.value='Resposta fictícia';});
  e.forms[0].etapaOculta=true; e.forms[0].elements.forEach(c=>c.disabled=true);
  e.abrir(); await e.salvar.eventos.click();
  assert.equal(e.requests.length,2); assert.equal(e.requests[0].opts.body.get('campo__2.1'),'Resposta fictícia');
  assert.equal(e.requests[1].opts.body.get('versao_lida'),'2'); assert.equal(e.window.destino,e.link.href);
  assert.equal(e.forms[0].texto.disabled,true);

  // Recusa não deixa a página nem substitui as respostas locais ou versão lida.
  e=preparar(); e.forms[0].texto.value='Resposta local'; e.fetch=async()=>e.resposta(5,'1'); e.abrir(); await e.salvar.eventos.click();
  assert.equal(e.window.destino,undefined); assert.equal(e.forms[0].texto.value,'Resposta local');
  assert.equal(e.forms[0].querySelector('[name="versao_lida"]').value,'1'); assert.match(e.erro.textContent,/Recusa ficticia/);
  assert.ok(e.window.saidaForm1.deveAvisar()); assert.equal(e.continuar.disabled,false);

  // Queda de rede e repetição usam a mesma chave/payload (idempotência existente).
  e=preparar(); e.forms[0].texto.value='Texto'; e.fetch=async()=>{throw new TypeError('rede');};
  e.abrir(); await e.salvar.eventos.click(); assert.equal(e.window.destino,undefined);
  assert.match(e.erro.textContent,/Falha de conexão/); const dados=e.requests[0].opts.body;
  e.fetch=null; await e.salvar.eventos.click(); assert.equal(e.requests[1].opts.body,dados); assert.equal(e.window.destino,e.link.href);

  // Não atualizar cegamente a versão quando outro agente salvou entre POST/GET.
  e=preparar(); e.forms[0].texto.value='Texto'; e.fetch=async()=>e.resposta(9); e.abrir(); await e.salvar.eventos.click();
  assert.equal(e.window.destino,undefined); assert.match(e.erro.textContent,/versão mais recente/);
  assert.equal(e.forms[0].querySelector('[name="versao_lida"]').value,'1');

  // Uma tentativa sem resposta não pode reutilizar a chave com dados diferentes.
  e=preparar(); e.forms[0].texto.value='Primeira'; e.fetch=async()=>{throw new TypeError('rede');};
  e.abrir(); await e.salvar.eventos.click(); e.forms[0].texto.value='Segunda'; await e.salvar.eventos.click();
  assert.equal(e.requests.length,1); assert.equal(e.window.destino,undefined);

  // Duplo clique e Escape durante a gravação não causam abandono/duplicação.
  e=preparar(); e.forms[0].texto.value='Texto'; let resolver;
  e.fetch=()=>new Promise(resolve=>resolver=resolve); e.abrir(); const gravando=e.salvar.eventos.click();
  await e.salvar.eventos.click(); let impediu=false; e.dialogo.eventos.cancel({preventDefault(){impediu=true;}});
  e.sair.eventos.click(); assert.ok(impediu); assert.equal(e.requests.length,1); assert.equal(e.window.destino,undefined);
  resolver(e.resposta(2)); await gravando; assert.equal(e.window.destino,e.link.href);

  // Falha no segundo bloco mantém o primeiro salvo e o restante editado.
  e=preparar(); e.forms.forEach(f=>f.texto.value='Texto');
  e.fetch=async()=>e.requests.length===1?e.resposta(2):e.resposta(2,'1'); e.abrir(); await e.salvar.eventos.click();
  assert.equal(e.window.destino,undefined); assert.equal(e.window.saidaForm1.alterado(e.forms[0]),false);
  assert.equal(e.window.saidaForm1.alterado(e.forms[1]),true);
  e.sair.eventos.click(); assert.equal(e.forms[0].texto.value,'Texto'); assert.equal(e.forms[1].texto.value,'');
  // Jornada do Bloco 10: mesma fila preserva outros blocos antes do destinatário.
  e=preparar([2,10,10]); e.forms[2].action+='/destinatarios/adicionar';
  e.forms.forEach(f=>f.texto.value='Resposta fictícia');
  const destino='https://poc.invalid/registros/FICTICIO?conta_id=CONTA-FICTICIA#titulo-bloco-11';
  await e.window.saidaForm1.salvarPendentes({destino});
  assert.equal(e.requests.length,3); assert.equal(e.window.destino,destino);
  assert.equal(e.requests[2].opts.body.get('versao_lida'),'3');
  assert.match(e.requests[2].url,/destinatarios/);
  assert.equal(e.forms[2].inert,true);
  // Inclusão confirmada seguida de falha: impede editar/reincluir a mesma ocorrência.
  e=preparar([10,14]); e.forms[0].action+='/destinatarios/adicionar';
  e.forms.forEach(f=>f.texto.value='Texto');
  e.fetch=async()=>e.requests.length===1?e.resposta(2):e.resposta(2,'1');
  await e.window.saidaForm1.salvarPendentes({destino});
  assert.equal(e.forms[0].inert,true); assert.equal(e.window.destino,undefined);
  assert.equal(e.window.saidaForm1.alterado(e.forms[0]),false);

  // Remover é ato explícito, depois das respostas e edições já digitadas.
  e=preparar([10]); e.forms[0].texto.value='Correção fictícia';
  const remover=formulario(10,'destinatarios/ID-FICTICIO/remover');
  await e.window.saidaForm1.salvarPendentes({destino,adicional:remover});
  assert.equal(e.requests.length,2); assert.match(e.requests[1].url,/remover$/);

  // Nenhum envio quando uma ocorrência apresenta controles inválidos.
  e=preparar([10,10]); e.forms.forEach(f=>f.texto.value='Texto'); e.forms[1].checkValidity=()=>false;
  const aviso=elemento(); await e.window.saidaForm1.salvarPendentes({destino,aviso});
  assert.equal(e.requests.length,0); assert.equal(e.window.destino,undefined); assert.ok(aviso.focado);

  // Respostas confirmadas + destinatário recusado: retentativa não repete o primeiro ato.
  e=preparar([10,10]); e.forms.forEach(f=>f.texto.value='Texto');
  e.fetch=async()=>e.requests.length===1?e.resposta(2):e.resposta(2,'1');
  await e.window.saidaForm1.salvarPendentes({destino});
  assert.equal(e.window.destino,undefined); assert.equal(e.window.saidaForm1.alterado(e.forms[0]),false);
  e.fetch=null; await e.window.saidaForm1.salvarPendentes({destino});
  assert.equal(e.requests.length,3); assert.equal(e.window.destino,destino);
  console.log('Retorno e jornada coordenada: preservação, falhas, concorrência e idempotência aprovadas (DOM simulado).');
})().catch(e=>{console.error(e);process.exitCode=1;});
