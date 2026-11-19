(() => {
 const selected=(form,name)=>[...form.querySelectorAll('input,select')].filter(x=>x.name===name&&!x.disabled&&(x.tagName==='SELECT'||x.checked)).map(x=>x.value);
 const wrappers=()=>document.querySelectorAll('[data-outro-origem]');
 function update(){wrappers().forEach(w=>{const form=w.closest('form');if(!form)return;
  let opts=w.dataset.outroOpcoes?JSON.parse(w.dataset.outroOpcoes):null;
  if(!opts){const controls=[...form.querySelectorAll('input,select')].filter(x=>x.name===w.dataset.outroOrigem);opts=controls.flatMap(x=>x.tagName==='SELECT'?[...x.options].map(o=>o.value):[x.value]).filter(v=>/^outr[oa]s?\b/i.test(v));if(!opts.length)return;}
  const active=selected(form,w.dataset.outroOrigem).some(v=>opts.includes(v)),input=w.querySelector('input,textarea');w.hidden=!active;input.required=active;
  if(active&&w.hasAttribute('data-outro-form1')){w.childNodes[0].textContent='Qual?';input.maxLength=200;}
 });}
 document.addEventListener('change',e=>{const t=e.target;if(t.type==='checkbox'&&t.checked&&t.closest('form')){
  const siblings=[...t.form.querySelectorAll('input[type=checkbox]')].filter(x=>x.name===t.name&&x!==t);
  const label=(t.closest('label')?.textContent||t.value).trim();if(label==='A confirmar'||t.value==='A_CONFIRMAR'){
   siblings.forEach(x=>x.checked=false);let notice=t.closest('fieldset').querySelector('[data-exclusivo-aviso]');if(!notice){notice=document.createElement('p');notice.dataset.exclusivoAviso='';notice.setAttribute('role','status');t.closest('fieldset').append(notice);}notice.textContent="'A confirmar' é exclusivo: as outras opções foram desmarcadas.";
  }
 }update();});document.addEventListener('reset',()=>setTimeout(update,0));update();
})();
