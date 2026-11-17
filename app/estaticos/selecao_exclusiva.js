document.addEventListener('change', event => {
  const campo = event.target;
  if (!campo.matches('input[type=checkbox]') || !campo.form || !campo.name) return;
  const opcoes = Array.from(campo.form.elements).filter(e => e.type === 'checkbox' && e.name === campo.name);
  const exclusiva = opcoes.find(e => ['A confirmar', 'A_CONFIRMAR'].includes(e.value) || e.labels[0]?.textContent.trim() === 'A confirmar');
  if (!exclusiva || !campo.checked) return;
  for (const opcao of opcoes) {
    if (opcao !== campo && (opcao === exclusiva || campo === exclusiva)) opcao.checked = false;
  }
  campo.dispatchEvent(new Event('input', {bubbles: true}));
}, true);
