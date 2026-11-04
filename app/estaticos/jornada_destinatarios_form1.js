/* Coordena comandos existentes; não altera o envelope REV13 nem cria uma transação nova. */
(function () {
  var principal = document.getElementById('formulario-bloco-10');
  if (!principal) return; // Consulta não ganha controles ou permissões.
  var bloco = principal.closest('.bloco-form1-integral');
  var aviso = bloco.querySelector('[data-estado-jornada-destinatarios]');
  var seletores = Array.from(bloco.querySelectorAll('[name="destinatario__categoria"]'));
  function atualizarCategorias() {
    var categorias = Array.from(principal.elements).filter(function (c) {
      return c.name === 'campo__10.2' && c.checked && c.value !== 'A confirmar';
    }).map(function (c) { return c.value; });
    seletores.forEach(function (seletor) {
      var valor = seletor.value;
      seletor.replaceChildren(new Option('Selecione', ''));
      categorias.forEach(function (categoria) { seletor.add(new Option(categoria, categoria)); });
      // Não apagar uma edição quando a categoria deixa de ser selecionada.
      if (valor && !categorias.includes(valor)) seletor.add(new Option(valor + ' — reveja a seleção em 10.2', valor));
      seletor.value = valor;
    });
  }
  principal.addEventListener('change', atualizarCategorias);
  atualizarCategorias();
  bloco.addEventListener('submit', function (evento) {
    var formulario = evento.target;
    if (formulario.tagName !== 'FORM') return;
    evento.preventDefault();
    // Evita o redirecionamento individual que descartaria os outros formulários.
    evento.stopImmediatePropagation();
    if (!window.saidaForm1 || !window.saidaForm1.salvarPendentes) {
      aviso.textContent = 'Não foi possível iniciar o salvamento conjunto. Suas respostas continuam na página. Não recarregue antes de preservar seu trabalho.';
      return;
    }
    var acionador = evento.submitter;
    var destino = new URL(window.location.href);
    destino.searchParams.set('erro', '0');
    destino.searchParams.set('mensagem', 'Rascunho salvo com sucesso. Respostas e destinatários preenchidos nesta página foram guardados. O FORM 1 não foi concluído nem submetido.');
    destino.hash = formulario === principal
      ? (acionador && acionador.value === 'proximo' ? '#titulo-bloco-11' : '#titulo-bloco-10')
      : '#titulo-destinatarios-10-2-1';
    if (formulario === principal && window.retomadaForm1) window.retomadaForm1.antesDeSalvar(principal, acionador);
    var remocao = formulario.getAttribute('action').endsWith('/remover');
    window.saidaForm1.salvarPendentes({destino: destino.href, aviso: aviso, adicional: remocao ? formulario : null});
  }, true);
})();
