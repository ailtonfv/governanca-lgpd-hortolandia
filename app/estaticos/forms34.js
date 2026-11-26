(() => {
 const form=document.querySelector('[data-respostas34]');if(!form || form.hasAttribute('data-somente-leitura'))return;
 let dirty=false,next=null;const dialog=document.querySelector('#sair34');
 function conditions(){document.querySelectorAll('[data-depende]').forEach(f=>{
   const origin=form.elements.namedItem(f.dataset.depende);if(!origin)return;
   f.disabled=origin.value!=='Sim';f.classList.toggle('bloqueada34',f.disabled);if(f.hasAttribute('data-ocultar-condicional'))f.hidden=f.disabled;
 });
 document.querySelectorAll('[data-prioridade-origem]').forEach(f=>{
   const origem=f.dataset.prioridadeOrigem, campo=form.elements.namedItem('F4-4.9');
   f.disabled=!origem || !campo || !campo.value || campo.value===origem;
   f.classList.toggle('bloqueada34',f.disabled);
 });}
 form.addEventListener('change',()=>{dirty=true;conditions();});form.addEventListener('input',()=>dirty=true);
 form.addEventListener('reset',()=>{dirty=false;setTimeout(conditions,0);});form.addEventListener('submit',()=>dirty=false);
 document.addEventListener('click',e=>{const a=e.target.closest('a');if(!dirty||!a||a.target==='_blank')return;
   e.preventDefault();next=a.href;dialog.showModal();});
 dialog.querySelector('[data-voltar34]').onclick=()=>dialog.close();
 dialog.querySelector('[data-sair34]').onclick=()=>{dirty=false;location.href=next;};
 dialog.querySelector('[data-salvar34]').onclick=async()=>{
   if(!form.reportValidity())return;const button=dialog.querySelector('[data-salvar34]');button.disabled=true;
   try{const response=await fetch(location.href,{method:'POST',body:new FormData(form)});
     if(response.ok){dirty=false;location.href=next;}else{dialog.close();const notice=document.createElement('p');
       notice.setAttribute('role','alert');notice.textContent='O salvamento foi recusado. Confira o bloco antes de sair.';form.prepend(notice);}
   }finally{button.disabled=false;}
 };
 document.addEventListener('ato-confirmado',()=>dirty=false);
 // Alternativa exclusiva, sem substituir a validação do servidor.
 form.addEventListener('change',e=>{const t=e.target;if(t.type!=='checkbox'||!t.checked)return;
  form.querySelectorAll('input[type=checkbox]').forEach(x=>{if(x!==t&&x.name===t.name&&(t.value==='A confirmar'||x.value==='A confirmar'))x.checked=false;});});
})();

(() => {const check=document.querySelector('[data-filtro-historico]');if(!check)return;
function filtrar(){document.querySelectorAll('[data-historico-ato]').forEach(el=>el.hidden=check.checked&&el.dataset.historicoAto==='nao');}
check.addEventListener('change',filtrar);filtrar();})();

(() => {const form=document.querySelector('#ato-manifestar_comite form');if(!form)return;
const finalidade=form.elements.finalidade,label=form.querySelector('label[for="ato-manifestar_comite-favoravel"]');
const textos={residual:'O Comitê é favorável ao tratamento proposto para o risco residual (RIPD e controles)?',
avaliacao:form.dataset.perguntaAvaliacao,triagem:form.dataset.perguntaTriagem,
prorrogacao:'O Comitê é favorável à prorrogação?',cancelamento:'O Comitê é favorável ao cancelamento?'};
function ajustar(){if(label)label.firstChild.textContent=(textos[finalidade.value]||'O Comitê é favorável à finalidade selecionada?')+' ';}
finalidade.addEventListener('change',ajustar);ajustar();})();

// A2: cada linha é uma condição própria, validada novamente no domínio.
document.querySelectorAll("[data-adicionar-condicao]").forEach(b=>b.addEventListener("click",()=>{const r=b.parentElement.querySelector("[data-condicao]").cloneNode(true);r.querySelectorAll("input,select").forEach(c=>c.value="");b.before(r);}));

// A5: opção exclusiva e detalhes dos controles selecionados.
document.addEventListener('change', event => {
  const field = event.target;
  if (field.name !== 'F3-3.47') return;
  const fields = [...document.querySelectorAll('input[name="F3-3.47"]')];
  const exclusive = ['Nenhum controle identificado', 'A confirmar'];
  if (field.checked) fields.forEach(other => {
    if (other !== field && (exclusive.includes(field.value) || exclusive.includes(other.value))) other.checked = false;
  });
  const selected = fields.filter(i => i.checked).map(i => i.value);
  document.querySelectorAll('[data-detalhe-controle]').forEach(el => {
    el.hidden = !selected.includes(el.dataset.detalheControle);
  });
});
