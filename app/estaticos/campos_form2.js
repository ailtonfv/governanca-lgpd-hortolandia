document.addEventListener('input', event => {
  if (!event.target.matches('[data-cnpj]')) return;
  const n = event.target.value.replace(/\D/g, '').slice(0, 14);
  event.target.value = n.replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2}\.\d{3})(\d)/, '$1.$2')
    .replace(/^(\d{2}\.\d{3}\.\d{3})(\d)/, '$1/$2')
    .replace(/(\/\d{4})(\d)/, '$1-$2');
});
document.addEventListener('change', event => {
  if (!event.target.matches('[data-modo-temporal]')) return;
  const campo = event.target.closest('[data-referencia-temporal]').querySelector('[data-valor-temporal]');
  if (event.target.value === 'date' && campo.value && !/^\d{4}-\d{2}-\d{2}$/.test(campo.value)) {
    event.target.value = 'text';
    campo.setCustomValidity('Apague a referência em texto antes de escolher uma data.');
    campo.reportValidity();
    campo.addEventListener('input', () => campo.setCustomValidity(''), {once: true});
    return;
  }
  campo.setCustomValidity('');
  campo.type = event.target.value;
});
