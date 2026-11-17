document.addEventListener('input', event => {
  if (!event.target.matches('[data-cnpj]')) return;
  const n = event.target.value.replace(/\D/g, '').slice(0, 14);
  event.target.value = n.replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2}\.\d{3})(\d)/, '$1.$2')
    .replace(/^(\d{2}\.\d{3}\.\d{3})(\d)/, '$1/$2')
    .replace(/(\/\d{4})(\d)/, '$1-$2');
});
