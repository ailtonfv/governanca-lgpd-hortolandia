/* Coordena comandos existentes; não altera o envelope REV13 nem cria uma transação nova. */
(function () {
  var principal = document.getElementById('formulario-bloco-10');
  if (!principal) return; // Consulta não ganha controles ou permissões.
  var bloco = principal.closest('.bloco-form1-integral');
  var aviso = bloco.querySelector('[data-estado-jornada-destinatarios]');
  var seletores = Array.from(bloco.querySelectorAll('[name="destinatario__categoria"]'));
  seletores.forEach(function (seletor) {
    seletor.addEventListener('change', function (evento) {
      if (!evento.categoriaAutomatica) delete seletor.dataset.categoriaAutomatica;
    });
  });
  function atualizarCategorias() {
    var categorias = Array.from(principal.elements).filter(function (c) {
      return c.name === 'campo__10.2' && c.checked && c.value !== 'A confirmar';
    }).map(function (c) { return c.value; });
    seletores.forEach(function (seletor) {
      if (seletor.form.inert) return; // Inclusão já confirmada em uma fila parcialmente salva.
      var valor = seletor.value;
      var novo = seletor.dataset.destinatarioNovo === 'true';
      var automatico = false;
      // Só recalcular a sugestão de uma ficha nova ainda não preenchida.
      if (novo && seletor.dataset.categoriaAutomatica && window.saidaForm1 && !window.saidaForm1.alterado(seletor.form)) {
        valor = ''; automatico = true;
      }
      if (novo && !valor && categorias.length === 1) { valor = categorias[0]; automatico = true; }
      seletor.replaceChildren(new Option('Selecione', ''));
      categorias.forEach(function (categoria) { seletor.add(new Option(categoria, categoria)); });
      // Não apagar uma edição quando a categoria deixa de ser selecionada.
      if (valor && !categorias.includes(valor)) {
        var anterior = new Option(valor + ' — reveja a seleção em 10.2', valor);
        anterior.disabled = true; // Consulta do valor preservado, não uma opção válida nova.
        seletor.add(anterior);
      }
      seletor.value = valor;
      var inconsistente = valor && !categorias.includes(valor);
      var orientacao = seletor.closest('[data-destinatario-editor]').querySelector('[data-orientacao-categoria]');
      orientacao.textContent = inconsistente
        ? 'Esta categoria deixou de estar selecionada em 10.2. Reveja a seleção antes de editar o destinatário. O salvamento preserva a ocorrência no histórico, conforme as regras atuais.'
        : !categorias.length ? 'Responda à pergunta F1-10.2 antes de adicionar um destinatário.'
        : categorias.length === 1 ? 'Única categoria marcada em 10.2: ' + categorias[0] + '. Identifique abaixo a unidade ou entidade.'
        : 'Escolha, entre as categorias marcadas em 10.2, a correspondente a este destinatário.';
      seletor.setCustomValidity(inconsistente ? 'Reveja a categoria deste destinatário e a resposta 10.2.' : '');
      if (automatico && window.saidaForm1) {
        seletor.dataset.categoriaAutomatica = 'true';
        window.saidaForm1.registrarCategoriaAutomatica(seletor);
      }
      // Reutiliza a orientação municipal/externa e os indicadores existentes.
      var evento = new Event('change', {bubbles: true});
      evento.categoriaAutomatica = true;
      seletor.dispatchEvent(evento);
    });
  }
  principal.addEventListener('change', function (evento) {
    if (evento.target.name === 'campo__10.2') atualizarCategorias();
  });
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
    var atoExplicito = /\/(remover|adicionar)$/.test(formulario.getAttribute('action'));
    window.saidaForm1.salvarPendentes({destino: destino.href, aviso: aviso, adicional: atoExplicito ? formulario : null});
  }, true);
})();
