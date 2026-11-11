(() => {
  const form = document.getElementById('revisao-bloco');
  let alterado = false;
  document.getElementById('adicionar-ocorrencia')?.addEventListener('click', event => {
    const grupos = [...form.querySelectorAll('[data-ocorrencia]')];
    const ultimo = Math.max(...grupos.map(el => Number(el.dataset.ocorrencia)));
    if (ultimo >= 99) return;
    const numero = ultimo + 1;
    for (const grupo of grupos.filter(el => Number(el.dataset.ocorrencia) === ultimo)) {
      const novo = grupo.cloneNode(true);
      novo.dataset.ocorrencia = numero;
      novo.querySelector('strong span').textContent = numero;
      // Um conjunto novo ainda não possui respostas às perguntas condicionantes.
      const condicional = novo.querySelector('[data-dependencia-local]');
      if (condicional) condicional.disabled = true;
      for (const el of novo.querySelectorAll('[name]')) {
        el.name = el.name.replace(/#\d+$/, '#' + numero);
        if (el.type === 'checkbox') el.checked = false;
        else el.value = '';
      }
      grupo.after(novo);
    }
    alterado = true;
    if (numero === 99) event.target.disabled = true;
  });
  form.addEventListener('input', () => { alterado = true; });
  form.addEventListener('submit', () => { alterado = false; });
  window.addEventListener('beforeunload', event => {
    if (alterado) { event.preventDefault(); event.returnValue = ''; }
  });
})();
