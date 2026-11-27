(() => {
 function atualizar(){document.querySelectorAll('[data-r17][data-condicional-r17="1"]').forEach(m=>{
  const f=m.closest('fieldset'); const controles=f ? [...f.querySelectorAll('input:not([type=hidden]),select,textarea')] : [];
  const condicao=f && (f.matches('[data-gatilhos],[data-depende],[data-prioridade-origem]') ? f : f.querySelector('[data-gatilhos]'));
  const ativo=condicao ? !condicao.disabled : f && !f.disabled;
  const texto=ativo?'Obrigatório neste caso':'Obrigatório se a condição indicada estiver ativa';
  if(m.textContent!==texto)m.textContent=texto;
  m.classList.toggle('indicador-obrigatoriedade-obrigatorio',!!ativo);
  m.classList.toggle('indicador-obrigatoriedade-condicional',!ativo);
 });}
 document.addEventListener('change',()=>setTimeout(atualizar,0));
 document.addEventListener('reset',()=>setTimeout(atualizar,0));
 new MutationObserver(atualizar).observe(document.body,{subtree:true,attributes:true,attributeFilter:['disabled']});
 atualizar();
})();
