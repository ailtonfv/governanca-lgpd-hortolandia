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
      grupo.querySelector('[data-ajuda-condicao]').hidden = ativa;
      const aviso = grupo.querySelector('[data-aviso-complemento]');
      if (aviso) aviso.hidden = !ativa;
    }
  }
  form.addEventListener('input', atualizarCondicoes);
  form.addEventListener('change', atualizarCondicoes);
  atualizarCondicoes();
  let alterado = false;
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
    alterado = true;
    if (numero === 99) event.target.disabled = true;
  });
  form.addEventListener('input', () => { alterado = true; });
  form.addEventListener('submit', () => { alterado = false; });
  window.addEventListener('beforeunload', event => {
    if (alterado) { event.preventDefault(); event.returnValue = ''; }
  });
})();
