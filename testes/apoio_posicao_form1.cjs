// Geometria e eventos simulados: prova de comportamento, não de aceite visual.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const codigo = fs.readFileSync('app/estaticos/posicao_form1.js', 'utf8');
function preparar({memoria=new Map(), state=null, tipo='navigate', conta='CONTA-FICTICIA', registro='REG-FICTICIO', hash='#titulo-bloco-2', storageBloqueado=false}={}) {
  const eventos={}, eventosRaiz={}; let focado;
  const janela = {location:{search:'?conta_id='+conta,hash,href:'https://poc.invalid/registros/'+registro+'?conta_id='+conta+hash},
    history:{state,scrollRestoration:'auto',replaceState(s){this.state=s;}},
    performance:{getEntriesByType(){return [{type:tipo}];}},scrollY:1000,innerHeight:800,
    addEventListener(nome,fn){eventos[nome]=fn;},scrollTo({top}){this.scrollY=top;}};
  const titulo={id:'titulo-bloco-2',setAttribute(){},focus(){focado=this;},closest(){return bloco;}};
  const bloco={oculto:false,top:400,height:2600,getClientRects(){return this.oculto?[]:[{}];},closest(){return this.oculto?this:null;},
    getBoundingClientRect(){return {top:this.top-janela.scrollY,height:this.height};},
    querySelector(){return titulo;},querySelectorAll(s){return s==='form'?[form]:campos;}};
  const form={getAttribute(){return '/registros/REG-FICTICIO/form1-integral/bloco-2/salvar';},querySelectorAll(){return campos;},closest(){return bloco;}};
  const campos=[800,1300,1900].map((top,i)=>({name:'campo__2.'+(i+8),value:'RESPOSTA-FICTICIA-NUNCA-NA-MEMORIA',top,disabled:false,oculto:false,
    closest(s){return s==='form'?form:this.oculto?this:null;},getClientRects(){return this.oculto?[]:[{}];},
    getBoundingClientRect(){return {top:this.top-janela.scrollY,bottom:this.top-janela.scrollY+40};},focus(){focado=this;}}));
  const raiz={dataset:{registroId:registro},querySelectorAll(){return [bloco];},addEventListener(nome,fn){eventosRaiz[nome]=fn;}};
  let alturaMensagem=0;
  const contexto={window:janela,URLSearchParams,document:{getElementById(id){return id==='retorno-painel-form1'?{getBoundingClientRect(){return {height:50};}}:id==='mensagem-registro'?{getBoundingClientRect(){return {height:alturaMensagem};}}:titulo;}}};
  vm.runInNewContext(codigo,contexto);
  const sessao={getItem(k){return storageBloqueado?null:memoria.get(k);},setItem(k,v){if(!storageBloqueado)memoria.set(k,v);},removeItem(k){if(!storageBloqueado)memoria.delete(k);}};
  const retomada=janela.criarRetomadaForm1(raiz,sessao);
  return {janela,campos,bloco,form,retomada,eventos,eventosRaiz,memoria,foco:()=>focado,mensagem:h=>alturaMensagem=h};
}
// Save/permanecer: última pergunta editada, ainda que o rodapé esteja distante.
let e=preparar(); e.eventosRaiz.input({target:e.campos[1]}); e.janela.scrollY=2300;
e.retomada.antesDeSalvar(e.form,{value:'permanecer'});
assert.ok(!Array.from(e.memoria.values()).join('').includes('RESPOSTA-FICTICIA'));
let retorno=preparar({memoria:e.memoria}); retorno.janela.scrollY=0; retorno.mensagem(60);
assert.equal(retorno.retomada.restaurar(),true); assert.equal(retorno.foco(),retorno.campos[1]);
assert.equal(retorno.campos[1].getBoundingClientRect().top,146); // barra + mensagem + respiro
assert.equal(e.memoria.size,0); // Intenção consumida, não sequestra uma navegação futura.

// Ctrl+R: conserva o controle visível e sua posição, sem guardar respostas.
e=preparar(); e.eventos.pagehide();
retorno=preparar({tipo:'reload',state:e.janela.history.state}); retorno.janela.scrollY=0;
retorno.retomada.restaurar(); assert.equal(retorno.campos[1].getBoundingClientRect().top,300);
assert.equal(retorno.janela.history.scrollRestoration,'manual');
assert.ok(!JSON.stringify(e.janela.history.state).includes('RESPOSTA-FICTICIA'));

// Avançar não restaura a pergunta anterior; hash explícito e conta são respeitados.
e=preparar(); e.retomada.antesDeSalvar(e.form,{value:'permanecer'}); e.retomada.antesDeSalvar(e.form,{value:'proximo'});
assert.equal(preparar({memoria:e.memoria,hash:'#titulo-bloco-3'}).retomada.posicao,null);
e=preparar(); e.eventos.pagehide();
assert.equal(preparar({tipo:'reload',state:e.janela.history.state,hash:'#titulo-bloco-3'}).retomada.posicao,null);
assert.equal(preparar({tipo:'reload',state:e.janela.history.state,conta:'OUTRA-FICTICIA'}).retomada.posicao,null);
assert.equal(preparar({tipo:'reload',state:e.janela.history.state,registro:'OUTRO-FICTICIO'}).retomada.posicao,null);
assert.equal(preparar({tipo:'navigate',state:e.janela.history.state}).retomada.posicao,null);
assert.equal(preparar({tipo:'reload',state:e.janela.history.state,hash:'#titulo-pre-validacao-form1'}).retomada.posicao,null);

// Não reabre uma condicional que deixou de ser aplicável.
retorno=preparar({tipo:'reload',state:e.janela.history.state}); retorno.campos[1].oculto=true;
retorno.janela.scrollY=0; retorno.retomada.restaurar();
assert.notEqual(retorno.foco(),retorno.campos[1]); assert.equal(retorno.campos[1].oculto,true);
assert.ok(retorno.janela.scrollY>0);

// Falta de sessionStorage não impede a retomada de recarga pela entrada do histórico.
retorno=preparar({tipo:'reload',state:e.janela.history.state,storageBloqueado:true});
assert.ok(retorno.retomada.restaurar());
// Em um bloco curto, deslocamento antigo é limitado ao tamanho atual.
retorno=preparar({tipo:'reload',state:e.janela.history.state}); retorno.campos.forEach(c=>c.oculto=true);
retorno.bloco.height=180; retorno.janela.scrollY=0; retorno.retomada.restaurar();
assert.equal(retorno.janela.scrollY,414);
console.log('Salvar/permanecer, recarga, isolamento, condicionais e avanço: aprovados (DOM simulado).');
