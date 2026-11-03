// Proteção de interação: os comandos e as autorizações continuam no servidor.
(function () {
  var form = document.getElementById('form-confirmar-conferencia');
  var dialogo = document.getElementById('dialogo-confirmar-conferencia');
  if (!form || !dialogo || !dialogo.showModal) return;
  var cancelar = dialogo.querySelector('[data-cancelar-confirmacao]');
  var efetivar = dialogo.querySelector('[data-efetivar-confirmacao]');
  var autorizado = false, enviando = false;
  form.addEventListener('submit', function (evento) {
    if (enviando) { evento.preventDefault(); return; }
    if (!autorizado) {
      evento.preventDefault();
      dialogo.showModal();
      cancelar.focus();
      return;
    }
    enviando = true;
    efetivar.disabled = true;
  });
  cancelar.addEventListener('click', function () { autorizado = false; dialogo.close(); });
  dialogo.addEventListener('cancel', function () { autorizado = false; });
  efetivar.addEventListener('click', function () {
    if (enviando) return;
    autorizado = true;
    dialogo.close();
    form.requestSubmit();
    autorizado = false;
  });
  window.addEventListener('pageshow', function () {
    autorizado = false; enviando = false; efetivar.disabled = false;
    document.getElementById('ciencia-confirmacao').checked = false;
  });
})();
