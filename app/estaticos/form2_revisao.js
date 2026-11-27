(() => {
  const form = document.getElementById('revisao-bloco');
  if (!form) return;
  function atualizarCondicoes() {
    const campos = Array.from(form.elements);
    for (const grupo of form.querySelectorAll('[data-gatilhos]')) {
      const conjunto = grupo.closest('[data-ocorrencia]')?.dataset.ocorrencia;
      const resultados = JSON.parse(grupo.dataset.gatilhos).map(regra => {
        if (!regra.local) return regra.fixa;
        const origem = regra.origem + (regra.repetivel && conjunto ? '#' + conjunto : '');
        const prefixo = regra.operador === 'POR_OCORRENCIA' ? 'texto:' : 'opcao:';
        return campos.some(campo => {
          if (![prefixo + origem, 'resposta_' + origem].includes(campo.name)
              || campo.matches(':disabled') || (campo.type === 'checkbox' && !campo.checked)) return false;
          return regra.operador === 'POR_OCORRENCIA' ? Boolean(campo.value.trim()) : campo.value === regra.codigo;
        });
      });
      const ativa = grupo.dataset.modo === 'ou' ? resultados.some(Boolean) : resultados.every(Boolean);
      grupo.disabled = !ativa;
      grupo.hidden = !ativa;
      grupo.querySelector('[data-ajuda-condicao]').hidden = ativa;
      const aviso = grupo.querySelector('[data-aviso-complemento]');
      if (aviso) aviso.hidden = !ativa;
    }
    for (const pergunta of form.querySelectorAll('.resposta-form2')) {
      const controles = Array.from(pergunta.querySelectorAll('.controle-condicional'));
      if (controles.length && controles.every(controle => controle.hasAttribute('data-gatilhos'))) {
        pergunta.hidden = controles.every(controle => controle.hidden);
      }
    }
    const alerta = document.getElementById('alerta-fundamento');
    if (alerta) alerta.hidden = !form.querySelector('[name="opcao:F2-3.1"][value="ANALISE_JURIDICA"]:checked') || form.elements.namedItem('opcao:F2-3.4')?.value === 'SIM';
    const teste = document.getElementById('teste-balanceamento');
    if (teste) {
      const aplicavel = !document.getElementById('F2-3.5').querySelector('[data-gatilhos]').disabled;
      teste.hidden = !aplicavel;
      const resposta = form.elements.namedItem('opcao:F2-3.5').value;
      document.getElementById('aviso-dados-sensiveis').hidden = !aplicavel || !['NAO','PARCIAL'].includes(resposta);
      document.getElementById('balanceamento-inativo').hidden = aplicavel;
    }
  }
  form.addEventListener('input', atualizarCondicoes);
  form.addEventListener('change', atualizarCondicoes);
  atualizarCondicoes();
  // Compare user values, including temporarily disabled fields, not command tokens.
  const estado = () => JSON.stringify(Array.from(form.elements)
    .filter(el => el.name && !['hidden','submit','button'].includes(el.type))
    .filter(el => !['checkbox','radio'].includes(el.type) || el.checked)
    .flatMap(el => el.multiple ? Array.from(el.selectedOptions, o => [el.name, o.value]) : [[el.name, el.value]])
    .filter(([, valor]) => valor !== '').sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b))));
  const salvo = estado();
  let enviando = false;
  document.getElementById('adicionar-ocorrencia')?.addEventListener('click', event => {
    const grupos = [...form.querySelectorAll('[data-ocorrencia]')];
    const ultimo = Math.max(...grupos.map(el => Number(el.dataset.ocorrencia)));
    if (ultimo >= 99) return;
    const numero = ultimo + 1;
    for (const grupo of grupos.filter(el => Number(el.dataset.ocorrencia) === ultimo)) {
      const novo = grupo.cloneNode(true);
      novo.dataset.ocorrencia = numero;
      novo.querySelector('strong span').textContent = numero;
      // Um conjunto novo ainda não possui respostas às perguntas condicionantes.
      const condicional = novo.querySelector('[data-dependencia-local]');
      if (condicional) condicional.disabled = true;
      for (const el of novo.querySelectorAll('[name]')) {
        el.name = el.name.replace(/#\d+$/, '#' + numero);
        if (el.type === 'checkbox') el.checked = false;
        else el.value = '';
      }
      grupo.after(novo);
    }
    atualizarCondicoes();

    if (numero === 99) event.target.disabled = true;
  });


  const caixa = document.getElementById('saida-bloco-form2');
  const erro = document.getElementById('erro-salvar-bloco');
  let destino = null, descartar = false, ocupada = false;
  const alterado = () => estado() !== salvo;
  function abrir(url, descarte = false) {
    destino = url; descartar = descarte;
    caixa.querySelector('h2').textContent = descarte ? 'Descartar as alterações deste bloco?' : 'Você tem alterações não salvas neste bloco.';
    caixa.querySelector('[data-mensagem]').textContent = descarte ? 'O bloco voltará às respostas salvas. As alterações não salvas serão perdidas.' : 'Se sair sem salvar, perderá as alterações feitas desde o último salvamento.';
    caixa.querySelector('[data-salvar]').hidden = descarte;
    caixa.querySelector('[data-sair]').textContent = descarte ? 'Descartar alterações' : 'Sair sem salvar';
    caixa.showModal();
  }
  caixa.addEventListener('cancel', event => { if (ocupada) event.preventDefault(); });
  caixa.querySelector('[data-voltar]').onclick = () => caixa.close();
  caixa.querySelector('[data-sair]').onclick = () => {
    enviando = true;
    if (descartar) window.location.reload();
    else window.location.assign(destino);
  };
  async function salvar(continuar) {
    if (ocupada) return;
    if (!form.reportValidity()) { caixa.close(); return; }
    ocupada = true;
    form.inert = true;
    form.setAttribute('aria-busy', 'true');
    erro.hidden = true;
    const botoes = [...form.querySelectorAll('button'), ...caixa.querySelectorAll('button')];
    const anteriores = botoes.map(b => b.disabled);
    botoes.forEach(b => b.disabled = true);
    try {
      const resposta = await fetch(form.action || window.location.href, {
        method: 'POST', body: new FormData(form), credentials: 'same-origin',
        headers: {'X-Salvar-Bloco': '1', 'Accept': 'application/json'}
      });
      const dados = await resposta.json().catch(() => ({}));
      if (!resposta.ok || dados.salvo !== true) throw new Error(
        typeof dados.detail === 'string' ? dados.detail : 'Não foi possível confirmar o salvamento. Confira as respostas e tente novamente.');
      enviando = true;
      window.location.assign(continuar || dados.destino);
    } catch (falha) {
      caixa.close();
      erro.textContent = falha.message || 'Não foi possível salvar. Suas alterações continuam neste bloco.';
      erro.hidden = false; erro.focus();
    } finally {
      ocupada = false;
      form.inert = false;
      form.removeAttribute('aria-busy');
      botoes.forEach((b, i) => b.disabled = anteriores[i]);
    }
  }
  caixa.querySelector('[data-salvar]').onclick = () => salvar(destino);
  document.getElementById('descartar-alteracoes')?.addEventListener('click', () => {
    if (alterado()) abrir(null, true);
  });
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey ||
        event.shiftKey || event.altKey || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    const url = new URL(link.href, window.location.href);
    if (url.origin !== window.location.origin || !['http:', 'https:'].includes(url.protocol)) return;
    // Local anchors do not leave the block.
    if (url.pathname === location.pathname && url.search === location.search && url.hash) return;
    if (ocupada) { event.preventDefault(); return; }
    if (!alterado()) return;
    event.preventDefault(); abrir(url.href);
  });
  form.addEventListener('submit', event => {
    event.preventDefault(); salvar(null);
  });

  window.addEventListener('beforeunload', event => {
    if (!enviando && estado() !== salvo) { event.preventDefault(); event.returnValue = ''; }
  });
})();
