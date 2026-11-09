(() => {
  const form = document.getElementById('form2-rascunho');
  const input = document.getElementById('anotacao');
  const saved = document.getElementById('form2-conteudo-salvo');
  const destinosLocais = ['#anotacoes', '#unidade-guarda'];
  const contador = document.getElementById('contador-anotacao');
  if (input && contador) {
    const atualizar = () => { contador.textContent = input.value.length + ' de 2.000 caracteres utilizados'; };
    input.addEventListener('input', atualizar);
    atualizar();
  }
  let submitting = false;
  const dirty = () => Boolean(input && saved && input.value !== JSON.parse(saved.textContent));
  window.addEventListener('beforeunload', event => {
    if (dirty() && !submitting) { event.preventDefault(); event.returnValue = ''; }
  });
  document.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (link && destinosLocais.includes(link.hash) && link.href === location.href.split('#')[0] + link.hash) return;
    if (link && dirty() && !window.confirm('Há anotações não salvas. Sair descarta somente essas alterações. Continuar?')) event.preventDefault();
  });
  document.addEventListener('submit', event => {
    if (event.target === form) { submitting = true; return; }
    if (dirty() && !window.confirm('Há anotações não salvas. Continuar sem salvar?')) event.preventDefault();
  });
  const error = document.getElementById('erro-form2');
  const target = error || (destinosLocais.includes(location.hash) && document.getElementById(location.hash.slice(1)));
  if (target) target.focus();
})();
