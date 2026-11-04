/* Retorno ao painel: usa exclusivamente os comandos HTTP já existentes. */
(function () {
  'use strict';
  var raiz = document.querySelector('.form1-integral');
  var barra = document.getElementById('retorno-painel-form1');
  var dialogo = document.getElementById('dialogo-saida-form1');
  if (!raiz || !barra || !dialogo) return;
  var link = barra.querySelector('a');
  var erro = dialogo.querySelector('[data-erro-saida]');
  var salvar = dialogo.querySelector('[data-salvar-voltar]');
  var descartar = dialogo.querySelector('[data-sair-sem-salvar]');
  var continuar = dialogo.querySelector('[data-continuar-preenchendo]');
  var formularios = Array.from(raiz.querySelectorAll('.formulario-integral'));
  var originais = new Map();
  var valoresConfirmados = new Map();
  var tentativas = new Map();
  var ocupado = false, saindo = false, envioNormal = false;

  // Inclui controles condicionais/etapas ocultas; não inclui chaves técnicas.
  // Reverter uma edição ao valor original deixa o formulário limpo novamente.
  function assinatura(formulario) {
    return JSON.stringify(Array.from(formulario.elements).filter(function (c) {
      return c.name && !['hidden', 'submit', 'button', 'reset'].includes(c.type);
    }).map(function (c) {
      return [c.name, c.type, c.type === 'checkbox' || c.type === 'radio' ? c.checked
        : c.multiple ? Array.from(c.options).filter(function (o) { return o.selected; }).map(function (o) { return o.value; }) : c.value];
    }));
  }
  function confirmarValores(f) {
    originais.set(f, assinatura(f));
    valoresConfirmados.set(f, Array.from(f.elements).map(function (c) {
      return {controle: c, valor: c.value, marcado: c.checked,
        opcoes: c.multiple ? Array.from(c.options).map(function (o) { return o.selected; }) : null};
    }));
  }
  formularios.forEach(confirmarValores);
  function alterado(f) { return originais.has(f) && originais.get(f) !== assinatura(f); }
  function temAlteracoes() { return formularios.some(alterado); }
  window.saidaForm1 = {
    alterado: alterado,
    temAlteracoes: temAlteracoes,
    deveAvisar: function () { return !saindo && !envioNormal && (ocupado || temAlteracoes()); },
    envioNormal: function () { envioNormal = true; }
  };
  window.addEventListener('pageshow', function () { envioNormal = false; saindo = false; });

  function medirBarra() {
    document.documentElement.style.setProperty('--altura-retorno-form1', barra.getBoundingClientRect().height + 'px');
  }
  medirBarra();
  if (window.ResizeObserver) new ResizeObserver(medirBarra).observe(barra);
  else window.addEventListener('resize', medirBarra);

  function sair() {
    saindo = true;
    window.location.assign(link.href);
  }
  function fechar() { if (!ocupado) dialogo.close(); }
  link.addEventListener('click', function (e) {
    // Abrir outro separador mantém os dados desta página intactos.
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || e.button > 0) return;
    e.preventDefault();
    if (ocupado) return;
    if (!temAlteracoes()) { sair(); return; }
    erro.textContent = '';
    dialogo.showModal();
    continuar.focus();
  });
  continuar.addEventListener('click', fechar);
  dialogo.addEventListener('cancel', function (e) { if (ocupado) e.preventDefault(); });
  descartar.addEventListener('click', function () {
    if (ocupado) return;
    // O botão Voltar do navegador também não deve ressuscitar a edição descartada.
    valoresConfirmados.forEach(function (valores, f) {
      valores.forEach(function (item) {
        var c = item.controle;
        if (['hidden', 'submit', 'button', 'reset'].includes(c.type)) return;
        if (item.opcoes) Array.from(c.options).forEach(function (o, i) { o.selected = item.opcoes[i]; });
        else c.value = item.valor;
        if (c.type === 'checkbox' || c.type === 'radio') c.checked = item.marcado;
      });
      f.dataset.alterado = 'false';
    });
    formularios.forEach(function (f) {
      Array.from(f.elements).filter(function (c) { return c.name && !['hidden', 'submit', 'button', 'reset'].includes(c.type); })
        .forEach(function (c) { c.dispatchEvent(new Event('change', {bubbles: true})); });
    });
    sair();
  });

  function dadosDoFormulario(f) {
    // Navegar para outra etapa desabilita controles: isso não deve apagar suas
    // edições. Apenas esses controles são habilitados durante a serialização.
    var desabilitados = Array.from(f.elements).filter(function (c) {
      return c.disabled && c.closest('[data-etapa-oculta="true"]') && !c.closest('[data-condicional-oculta="true"]');
    });
    desabilitados.forEach(function (c) { c.disabled = false; });
    try {
      var dados = new FormData(f);
      dados.set('acao_pos_salvar', 'permanecer');
      return dados;
    } finally { desabilitados.forEach(function (c) { c.disabled = true; }); }
  }

  function atualizarChaves(pagina) {
    // Atualiza somente o controle otimista e as chaves de comando retornadas
    // pelo servidor. Nunca substitui respostas digitadas por HTML de resposta.
    var recebidos = Array.from(pagina.querySelectorAll('.form1-integral form'));
    raiz.querySelectorAll('form').forEach(function (f) {
      var novo = recebidos.find(function (n) { return n.getAttribute('action') === f.getAttribute('action'); });
      if (!novo) return;
      ['versao_lida', 'comando_id'].forEach(function (nome) {
        var atual = f.querySelector('[name="' + nome + '"]');
        var recebido = novo.querySelector('[name="' + nome + '"]');
        if (atual && recebido) atual.value = recebido.value;
      });
    });
  }

  async function salvarPendentes(opcoes) {
    opcoes = opcoes || {};
    if (ocupado) return;
    ocupado = true;
    var aviso = opcoes.aviso || erro;
    var focoAnterior = document.activeElement;
    var inerteAnterior = raiz.inert;
    raiz.inert = true;
    dialogo.setAttribute('aria-busy', 'true');
    [salvar, descartar, continuar].forEach(function (b) { b.disabled = true; });
    aviso.textContent = 'Salvando as alterações desta página. Aguarde a confirmação.';
    try {
      // Ordem canônica: resposta controladora antes das ocorrências repetíveis.
      var pendentes = formularios.filter(alterado).sort(function (a, b) {
        function numero(f) { return Number(f.closest('.bloco-form1-integral').querySelector('h3').id.replace('titulo-bloco-', '')); }
        return numero(a) - numero(b);
      });
      if (opcoes.adicional && !pendentes.includes(opcoes.adicional)) pendentes.push(opcoes.adicional);
      // Verificar controles antes da primeira gravação; ramos inativos não exigem envio.
      for (var candidato of pendentes) {
        if (!candidato.closest('[data-condicional-oculta="true"]') && candidato.checkValidity && !candidato.checkValidity()) {
          throw new Error('Revise a categoria e o modo de identificação dos destinatários antes de salvar. Nenhuma alteração foi enviada.');
        }
      }
      for (var f of pendentes) {
        // Uma ocorrência desativada pela resposta controladora não é enviada.
        if (f.closest('[data-condicional-oculta="true"]')) continue;
        var tentativa = tentativas.get(f);
        if (tentativa && tentativa.assinatura !== assinatura(f)) {
          throw new Error('Uma tentativa anterior ficou sem confirmação. Restaure os valores daquela tentativa antes de tentar novamente, ou recarregue após preservar suas anotações.');
        }
        if (!tentativa) {
          tentativa = { dados: dadosDoFormulario(f), assinatura: assinatura(f) };
          tentativas.set(f, tentativa);
        }
        var resposta = await fetch(f.action, {
          method: 'POST', body: tentativa.dados, credentials: 'same-origin', redirect: 'follow'
        });
        var destino = new URL(resposta.url);
        var esperado = new URL(window.location.href);
        if (!resposta.ok || destino.origin !== esperado.origin || destino.pathname !== esperado.pathname
            || destino.searchParams.get('conta_id') !== new URL(link.href).searchParams.get('conta_id')
            || !['0', '1'].includes(destino.searchParams.get('erro'))) {
          throw new Error('Não foi possível confirmar o salvamento. Suas alterações continuam nesta página. Tente novamente.');
        }
        if (destino.searchParams.get('erro') !== '0') {
          tentativas.delete(f); // Recusa confirmada: nenhuma gravação deste comando.
          // Nova tentativa editada terá outra chave, sem reutilização indevida.
          var paginaRecusada = new DOMParser().parseFromString(await resposta.text(), 'text/html');
          // Não atualiza a versão lida após uma recusa de concorrência.
          var novo = Array.from(paginaRecusada.querySelectorAll('.form1-integral form')).find(function (n) { return n.getAttribute('action') === f.getAttribute('action'); });
          if (novo) f.querySelector('[name="comando_id"]').value = novo.querySelector('[name="comando_id"]').value;
          throw new Error(destino.searchParams.get('mensagem') || 'Salvamento recusado. Revise as informações e tente novamente.');
        }
        var pagina = new DOMParser().parseFromString(await resposta.text(), 'text/html');
        var raizRecebida = pagina.querySelector('.form1-integral');
        if (!raizRecebida || raizRecebida.dataset.registroId !== raiz.dataset.registroId) {
          throw new Error('A confirmação recebida não corresponde a este Registro. Suas alterações permanecem na página.');
        }
        var versaoRecebida = raizRecebida.querySelector('.formulario-integral [name="versao_lida"]');
        if (!versaoRecebida || Number(versaoRecebida.value) !== Number(tentativa.dados.get('versao_lida')) + 1) {
          throw new Error('O Registro mudou durante a confirmação. Não salvaremos sobre uma versão mais recente. Preserve suas anotações e recarregue para conferir o estado atual.');
        }
        atualizarChaves(pagina);
        confirmarValores(f);
        // Se uma etapa posterior falhar, não transformar a ocorrência já criada
        // em outra inclusão ao editar o mesmo formulário ainda presente no DOM.
        if (f.getAttribute('action').endsWith('/adicionar')) f.inert = true;
        tentativas.delete(f);
        f.dataset.alterado = 'false';
        var estado = window.elementosFormularioForm1 ? window.elementosFormularioForm1(f, '[data-estado-salvamento]')[0] : f.querySelector('[data-estado-salvamento]');
        if (estado) estado.textContent = 'Rascunho salvo com sucesso. Suas respostas foram guardadas; o FORM 1 não foi concluído nem submetido.';
      }
      if (opcoes.destino) {
        if (!pendentes.length) {
          var semGravacao = new URL(opcoes.destino);
          semGravacao.searchParams.delete('erro');
          semGravacao.searchParams.delete('mensagem');
          opcoes.destino = semGravacao.href;
        }
        saindo = true;
        window.location.assign(opcoes.destino);
      } else sair();
    } catch (falha) {
      aviso.textContent = (falha instanceof TypeError ? 'Falha de conexão. As alterações continuam nesta página; tente novamente.' : falha.message)
        + ' Os blocos já confirmados permanecem salvos. Você pode continuar preenchendo.';
    } finally {
      ocupado = false;
      raiz.inert = inerteAnterior;
      dialogo.removeAttribute('aria-busy');
      [salvar, descartar, continuar].forEach(function (b) { b.disabled = false; });
      if (!saindo && opcoes.aviso && opcoes.aviso.focus) opcoes.aviso.focus();
      else if (!saindo && focoAnterior && focoAnterior.focus) focoAnterior.focus();
    }
  }
  window.saidaForm1.salvarPendentes = salvarPendentes;
  salvar.addEventListener('click', function () { return salvarPendentes(); });
})();
