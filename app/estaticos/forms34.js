(() => {
 const form=document.querySelector('[data-respostas34]');if(!form)return;
 let dirty=false,next=null;const dialog=document.querySelector('#sair34');
 function conditions(){document.querySelectorAll('[data-depende]').forEach(f=>{
   const origin=form.elements.namedItem(f.dataset.depende);if(!origin)return;
   f.disabled=origin.value!=='Sim';f.classList.toggle('bloqueada34',f.disabled);
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
 window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
 // Alternativa exclusiva, sem substituir a validação do servidor.
 form.addEventListener('change',e=>{const t=e.target;if(t.type!=='checkbox'||!t.checked)return;
  form.querySelectorAll('input[type=checkbox]').forEach(x=>{if(x!==t&&x.name===t.name&&(t.value==='A confirmar'||x.value==='A confirmar'))x.checked=false;});});
})();
