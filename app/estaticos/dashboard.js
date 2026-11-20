document.querySelectorAll('[data-dash-modo]').forEach(botao=>{
  botao.addEventListener('click',()=>{
    const tabela=botao.dataset.dashModo==='tabela';
    document.querySelectorAll('[data-dash-grafico]').forEach(el=>el.hidden=tabela);
    document.querySelectorAll('[data-dash-tabela]').forEach(el=>el.hidden=!tabela);
    document.querySelectorAll('[data-dash-modo]').forEach(el=>el.setAttribute('aria-pressed',String(el===botao)));
  });
});
// Sem JavaScript, gráfico e tabela permanecem disponíveis e nenhum dado desaparece.
document.querySelector('[data-dash-modo="grafico"]')?.click();
