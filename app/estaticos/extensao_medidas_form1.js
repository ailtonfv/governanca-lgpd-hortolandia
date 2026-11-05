/* Adoção explícita: não descarta nem converte edições locais. */
(function () {
  'use strict';
  function protegerAdocao(formulario) {
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
  }
  protegerAdocao(document.querySelector('[data-adotar-medidas]'));
  protegerAdocao(document.querySelector('[data-adotar-guarda]'));
})();
