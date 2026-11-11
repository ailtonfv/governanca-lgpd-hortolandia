(() => {
  const form = document.getElementById('form2-rascunho');
  const input = document.getElementById('anotacao');
  const saved = document.getElementById('form2-conteudo-salvo');
  const blocoForm = document.getElementById('form2-bloco-2');
  const identificacao = document.getElementById('form2-bloco-1');
  const destinosLocais = ['#anotacoes', '#unidade-guarda', '#identificacao'];
  if (identificacao) {
    const campo = id => identificacao.elements.namedItem('resposta_' + id);
    const dependente = identificacao.querySelector('[data-identificacao="F2-1.3.1"]');
    const atualizar = () => {
      const ativa = campo('F2-1.2').value === 'DIVERGENTE' || ['NAO', 'PARCIAL'].includes(campo('F2-1.3').value);
      dependente.disabled = !ativa;
      dependente.hidden = !ativa;
    };
    identificacao.addEventListener('change', atualizar);
    atualizar();
  }
  const contador = document.getElementById('contador-anotacao');
  if (input && contador) {
    const atualizar = () => { contador.textContent = input.value.length + ' de 2.000 caracteres utilizados'; };
    input.addEventListener('input', atualizar);
    atualizar();
  }
  let submitting = false;
  const serializar = formAlvo => {
    if (!formAlvo) return '';
    const dados = [...new FormData(formAlvo).entries()]
      .filter(([chave]) => !['comando_id', 'versao_lida'].includes(chave))
      .sort(([a, av], [b, bv]) => a.localeCompare(b) || String(av).localeCompare(String(bv)));
    return JSON.stringify(dados);
  };
  const blocoInicial = serializar(blocoForm);
  const anotacaoAlterada = () => Boolean(input && saved && input.value !== JSON.parse(saved.textContent));
  const blocoAlterado = () => Boolean(blocoForm && serializar(blocoForm) !== blocoInicial);
  const inicialIdentificacao = serializar(identificacao);
  const identificacaoAlterada = () => serializar(identificacao) !== inicialIdentificacao;
  const dirty = () => anotacaoAlterada() || blocoAlterado() || identificacaoAlterada();
  window.addEventListener('beforeunload', event => {
    if (dirty() && !submitting) { event.preventDefault(); event.returnValue = ''; }
  });
  document.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (link && destinosLocais.includes(link.hash) && link.href === location.href.split('#')[0] + link.hash) return;
    if (link && dirty() && !window.confirm('Há anotações não salvas. Sair descarta somente essas alterações. Continuar?')) event.preventDefault();
  });
  document.addEventListener('submit', event => {
    if (event.target !== identificacao && identificacaoAlterada() &&
        !window.confirm('Continuar sem salvar as alterações do Bloco 1?')) {
      event.preventDefault();
      return;
    }
    if (event.target === identificacao) {
      if ((blocoAlterado() || anotacaoAlterada()) && !window.confirm('Continuar sem salvar as alterações nas outras seções?')) event.preventDefault();
      else submitting = true;
      return;
    }
    if (event.target === form) {
      if (blocoAlterado() && !window.confirm('Há respostas do Bloco 2 não salvas. Continuar sem salvá-las?')) event.preventDefault();
      else submitting = true;
      return;
    }
    if (event.target === blocoForm) {
      if (anotacaoAlterada() && !window.confirm('Há uma anotação geral não salva. Continuar sem salvá-la?')) event.preventDefault();
      else submitting = true;
      return;
    }
    if (dirty() && !window.confirm('Há anotações não salvas. Continuar sem salvar?')) event.preventDefault();
  });
  const condicoes = [
    ['resposta-F2-2.9', 'F2-2.9.1'],
    ['resposta-F2-2.9.2', 'F2-2.9.3'],
  ];
  condicoes.forEach(([origemId, alvoId]) => {
    const origem = document.getElementById(origemId);
    const alvo = typeof document.querySelector === 'function'
      ? document.querySelector(`[data-resposta-form2="${alvoId}"]`)
      : null;
    if (!origem || !alvo) return;
    const atualizar = () => { alvo.disabled = origem.value !== 'SIM'; };
    origem.addEventListener('change', atualizar);
    atualizar();
  });
  const error = document.getElementById('erro-form2');
  const target = error || (destinosLocais.includes(location.hash) && document.getElementById(location.hash.slice(1)));
  if (target) target.focus();
})();
