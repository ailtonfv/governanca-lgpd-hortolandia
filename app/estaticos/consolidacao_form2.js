(() => {
  const form = document.getElementById('conferencia-consolidacao');
  if (!form) return;
  let alterado = false;
  form.addEventListener('input', () => { alterado = true; });
  form.addEventListener('submit', () => { alterado = false; });
  window.addEventListener('beforeunload', event => {
    if (!alterado) return;
    event.preventDefault();
    event.returnValue = '';
  });
})();
