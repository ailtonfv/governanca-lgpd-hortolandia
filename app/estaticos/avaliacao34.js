/* Preview uses the same approved thresholds; the domain validates saved values. */
(() => {
 function score(p,i){p=Number(p);i=Number(i);if(!p||!i)return {nota:null,faixa:'Ainda não avaliado'};const nota=p*i;return {nota,faixa:nota<=3?'Pequeno':nota<=6?'Moderado':nota<=12?'Alto':'Crítico'};}
 if(typeof module!=='undefined')module.exports={score};
 if(typeof document==='undefined')return;
 document.querySelectorAll('[data-quadro-avaliacao]').forEach(box=>{
  const initial=JSON.parse(box.dataset.inicial||'{}'),form=box.closest('form');
  function update(){const scores={};box.querySelectorAll('[data-marca]').forEach(x=>x.textContent='');
   for(const [tipo,pn,iname,mark] of [['inerente','p','i','I'],['residual','pr','ir','R']]){
    const p=box.querySelector(`[name="${pn}"]`)?.value??initial[tipo]?.probabilidade;
    const i=box.querySelector(`[name="${iname}"]`)?.value??initial[tipo]?.impacto;
    const s=score(p,i);scores[tipo]=s;box.querySelector(`[data-nota=${tipo}]`).dataset.faixa=s.faixa;box.querySelector(`[data-nota="${tipo}"]`).textContent=tipo[0].toUpperCase()+tipo.slice(1)+': '+(s.nota===null?'Ainda não avaliado':`${p} × ${i} = ${s.nota} — ${s.faixa}`);
    if(s.nota!==null){const cell=box.querySelector(`[data-p="${p}"][data-i="${i}"] [data-marca]`);if(cell)cell.textContent+=(cell.textContent?' / ':'')+mark;}
   }
   const a=scores.inerente,b=scores.residual;
   const evidencia=form?.querySelector('[data-obrigatorio-evidencia]');if(evidencia){const active=a.nota!==null&&b.nota!==null&&b.nota<a.nota;evidencia.querySelector('textarea').required=active;const badge=evidencia.querySelector('[data-marcador]');badge.textContent=active?'* Obrigatório':'** Obrigatório em alguns casos';badge.className='indicador-obrigatoriedade indicador-obrigatoriedade-'+(active?'obrigatorio':'condicional');}
   box.querySelector('[data-efeito]').textContent=a.nota===null||b.nota===null?'Efeito dos controles: ainda não avaliado':b.nota<a.nota?`De ${a.nota} (${a.faixa}) para ${b.nota} (${b.faixa}). Exige controle implementado e evidência.`:b.nota===a.nota?'Sem redução da nota após os controles.':'A nota residual é superior à inerente; confira e justifique.';
   const notes={Pequeno:'Aceitação pela autoridade da Secretaria.',Moderado:'Aceitação pela autoridade da Secretaria.',Alto:'Manifestação do DPO, ciência do Comitê e aceitação pela autoridade da Secretaria.',Crítico:'Crítico: controles imediatos, triagem de RIPD, manifestação do DPO e do Comitê, aceitação pelo Prefeito.'};
   box.querySelector('[data-exigencia]').textContent=notes[b.faixa]||'';
   box.querySelectorAll('select').forEach(input=>{let help=input.parentElement.querySelector('[data-significado]');if(!help){help=document.createElement('small');help.dataset.significado='';input.after(help);}help.textContent=input.value?input.selectedOptions[0].textContent:'';});
   const btn=form?.querySelector('[data-confirmar-ato]');if(btn)btn.dataset.confirmarAto=`Risco ${form.dataset.risco}: inerente ${a.nota??'não avaliado'} (${a.faixa}), residual ${b.nota??'não avaliado'} (${b.faixa}). Registrar esta proposta?`;
  }box.addEventListener('change',update);update();
 });
 document.querySelectorAll('[data-ingresso34]').forEach(form=>{
  function update(){const selected=form.elements.form.value,active=selected==='4'&&form.dataset.riscoDireto==='sim';form.querySelector('[data-justificativa-direta]').hidden=!active;form.elements.justificativa.required=active;
   form.querySelector('[data-confirmar-ato]').dataset.confirmarAto=`Registro ${form.dataset.registro}: encaminhar a versão ${form.dataset.versao} do FORM 2 para ${selected==='3'?'Riscos (FORM 3)':'Providência (FORM 4)'}. A origem será preservada e a autoria registrada.`;
  }form.addEventListener('change',update);update();
 });
 document.querySelectorAll('[data-ato34]').forEach(form=>{
  function observacao(){const wrap=form.querySelector('[data-obrigatorio-observacao]');if(!wrap)return;
   const active=form.elements.sem_dados_pessoais?.value==='nao'||form.elements.sem_falha_exposta?.value==='nao';wrap.querySelector('textarea').required=active;
   const badge=wrap.querySelector('[data-marcador]');badge.textContent=active?'* Obrigatório neste caso':'** Obrigatório ao responder Não';
   badge.className='indicador-obrigatoriedade indicador-obrigatoriedade-'+(active?'obrigatorio':'condicional');
  }form.addEventListener('change',observacao);observacao();
  function conditions(){const wrap=form.querySelector('[data-obrigatorio-triagem]');if(!wrap)return;
   const active=['elaborar','revisar','determinado_anpd'].includes(form.elements.resultado?.value);
   const input=wrap.querySelector('select');input.required=active;wrap.querySelector('[data-marcador]').textContent=active?'* Obrigatório':'** Obrigatório em alguns casos';wrap.querySelector('[data-marcador]').className='indicador-obrigatoriedade indicador-obrigatoriedade-'+(active?'obrigatorio':'condicional');
  }form.addEventListener('change',conditions);conditions();
 });
 document.addEventListener('submit',e=>{
  const form=e.target;if(!form.matches('[data-ato34]'))return;let first=null;
  form.querySelectorAll('[required]').forEach(input=>{if(input.disabled)return;const bad=!input.value.trim();input.toggleAttribute('aria-invalid',bad);if(bad)input.setAttribute('aria-invalid','true');const msg=document.getElementById(input.getAttribute('aria-describedby'));if(msg){msg.hidden=!bad;msg.textContent=bad?(input.dataset.erroObrigatorio||'Preencha este campo obrigatório.'):'';}if(bad&&!first)first=input;});
  if(first){e.preventDefault();e.stopImmediatePropagation();first.focus();}
 },true);
})();
/* Leitura antes do ato: a caixa resume os campos visíveis, sem decidir pelo servidor. */
(() => {
 if(typeof document==='undefined')return;
 document.querySelectorAll('[data-ato34]').forEach(form=>{
  const button=form.querySelector('[data-confirmar-ato]');if(!button)return;
  const acao=form.elements.acao?.value;
  if(['confirmar_avaliacao','confirmar_triagem'].includes(acao)||form.querySelector('[data-quadro-avaliacao]'))return;
  const base=button.dataset.confirmarAto;
  function resumo(){
   const partes=[];
   form.querySelectorAll('select,textarea,input:not([type=hidden])').forEach(c=>{
    if(c.disabled||!c.value)return;
    const label=form.querySelector(`label[for="${c.id}"]`);
    const nome=(label?.textContent||c.name).replace(/\*.*$/,'').trim();
    partes.push(nome+': '+(c.tagName==='SELECT'?c.selectedOptions[0]?.textContent:c.type==='date'?c.value.split('-').reverse().join('/'):c.value));
   });
   button.dataset.confirmarAto=base+(partes.length?'\n'+partes.join('\n'):'');
   const aviso=form.querySelector('[data-aviso-triagem]');
   if(aviso)aviso.hidden=!(form.elements.resultado?.value==='nao_indicado'&&['Alto','Crítico'].includes(form.dataset.faixa));
  }form.addEventListener('input',resumo);form.addEventListener('change',resumo);resumo();
 });
 function ajustar(el){if(!el.getClientRects().length)return;el.style.height='auto';el.style.height=el.scrollHeight+'px';}
 document.querySelectorAll('.forms34 textarea').forEach(el=>{ajustar(el);el.addEventListener('input',()=>ajustar(el));});
 document.addEventListener('toggle',()=>document.querySelectorAll('.forms34 textarea').forEach(ajustar),true);
 window.addEventListener('resize',()=>document.querySelectorAll('.forms34 textarea').forEach(ajustar));
})();
