/* Adoção explícita: não descarta nem converte edições locais. */
(function () {
  'use strict';
  var formulario = document.querySelector('[data-adotar-medidas]');
  if (!formulario) return;
  formulario.addEventListener('submit', function (evento) {
    if (window.saidaForm1 && window.saidaForm1.temAlteracoes()) {
      evento.preventDefault();
      var aviso = formulario.querySelector('[data-aviso-adocao]');
      aviso.textContent = 'Salve suas alterações antes de adotar a extensão. Nenhuma resposta foi alterada.';
      aviso.focus();
      return;
    }
    if (window.saidaForm1) window.saidaForm1.envioNormal();
  });
})();
