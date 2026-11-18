document.addEventListener('change', event => {
  const campo = event.target;
  if (!campo.matches('input[type=checkbox]') || !campo.form || !campo.name || !campo.checked) return;
  const opcoes = Array.from(campo.form.elements).filter(e => e.type === 'checkbox' && e.name === campo.name);
  const exclusiva = e => /^(a confirmar$|não se aplica(?:\b|$)|não aplicável(?:\b|$)|nenhum(?:a)?(?:\b|$)|faixa etária não registrada$)/i.test(e.labels[0]?.textContent.trim() || e.value.replace('A_CONFIRMAR','A confirmar'));
  for (const opcao of opcoes) {
    if (opcao !== campo && (exclusiva(opcao) || exclusiva(campo))) opcao.checked = false;
  }
  campo.dispatchEvent(new Event('input', {bubbles: true}));
}, true);
