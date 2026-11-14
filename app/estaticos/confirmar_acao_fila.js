document.querySelectorAll('[data-abrir-dialogo]').forEach(function (abrir) {
  const dialogo = document.getElementById(abrir.dataset.abrirDialogo);
  const formulario = abrir.form;
  function confirmar() {
    if (!formulario.reportValidity()) return;
    const nome = dialogo.querySelector('[data-nome-agente]');
    if (nome) nome.textContent = formulario.elements.responsavel_id.selectedOptions[0]?.textContent || '';
    dialogo.showModal();
  }
  abrir.addEventListener('click', confirmar);
  formulario.addEventListener('submit', function (evento) {
    if (!dialogo.open) {
      evento.preventDefault();
      confirmar();
    }
  });
  dialogo.querySelector('[data-fechar-dialogo]').addEventListener('click', function () {
    dialogo.close();
  });
});
