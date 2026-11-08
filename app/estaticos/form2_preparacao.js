(() => {
  const form = document.getElementById('form2-rascunho');
  const input = document.getElementById('anotacao');
  const saved = document.getElementById('form2-conteudo-salvo');
  let submitting = false;
  const dirty = () => Boolean(input && saved && input.value !== JSON.parse(saved.textContent));
  window.addEventListener('beforeunload', event => {
    if (dirty() && !submitting) { event.preventDefault(); event.returnValue = ''; }
  });
  document.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (link && link.hash === '#anotacoes' && link.href === location.href.split('#')[0] + '#anotacoes') return;
    if (link && dirty() && !window.confirm('Há anotações não salvas. Sair descarta somente essas alterações. Continuar?')) event.preventDefault();
  });
  document.addEventListener('submit', event => {
    if (event.target === form) { submitting = true; return; }
    if (dirty() && !window.confirm('Há anotações não salvas. Continuar sem salvar?')) event.preventDefault();
  });
  const error = document.getElementById('erro-form2');
  const target = error || (location.hash === '#anotacoes' && document.getElementById('anotacoes'));
  if (target) target.focus();
})();
