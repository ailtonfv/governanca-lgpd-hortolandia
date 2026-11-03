/* Memória de navegação: somente referências de controles e geometria, sem respostas. */
window.criarRetomadaForm1 = function (raiz, sessao) {
  var conta = new URLSearchParams(window.location.search).get('conta_id') || '';
  var escopo = raiz.dataset.registroId + ':' + conta;
  var chave = 'form1-integral-posicao-' + escopo;
  var ultimaEdicao = null;
  function visivel(c) { return c && !c.closest('[hidden], [data-condicional-oculta="true"]') && c.getClientRects().length > 0; }
  function blocoAtivo() { return Array.from(raiz.querySelectorAll('.bloco-form1-integral')).find(visivel); }
  function controles(f) { return Array.from(f.querySelectorAll('input:not([type="hidden"]), select, textarea')); }
  function capturar(preferirEdicao) {
    var bloco = blocoAtivo();
    if (!bloco) return null;
    var margem = margemAtual();
    var candidatos = Array.from(bloco.querySelectorAll('input:not([type="hidden"]), select, textarea')).filter(visivel);
    var campo = candidatos.includes(ultimaEdicao) && (preferirEdicao || ultimaEdicao.getBoundingClientRect().top >= margem
      && ultimaEdicao.getBoundingClientRect().top < window.innerHeight) ? ultimaEdicao
      : candidatos.find(function (c) { var r = c.getBoundingClientRect(); return r.bottom > margem && r.top < window.innerHeight; });
    var f = campo && campo.closest('form');
    return {escopo: escopo, bloco: Number(bloco.querySelector('h3').id.replace('titulo-bloco-', '')),
      deslocamento: Math.max(0, margem - bloco.getBoundingClientRect().top),
      acao: f ? f.getAttribute('action') : null, indice: f ? controles(f).indexOf(campo) : -1,
      nome: campo ? campo.name : null, topo: campo ? Math.max(margem, campo.getBoundingClientRect().top) : margem,
      instante: Date.now()};
  }
  function margemAtual() {
    var barra = document.getElementById('retorno-painel-form1');
    var mensagem = document.getElementById('mensagem-registro');
    return 24 + (barra ? barra.getBoundingClientRect().height : 0) + (mensagem ? mensagem.getBoundingClientRect().height + 12 : 0);
  }
  function validar(p) {
    var hash = window.location.hash.match(/^#titulo-bloco-(\d+)$/);
    var etapa = window.location.hash.match(/^#form1-etapa-([1-4])$/);
    return p && p.escopo === escopo && Number.isInteger(p.bloco) && p.bloco >= 1 && p.bloco <= 14
      && Number.isFinite(p.deslocamento) && Number.isFinite(p.topo)
      && (!etapa || Number(etapa[1]) === (p.bloco <= 3 ? 1 : p.bloco <= 8 ? 2 : p.bloco <= 11 ? 3 : 4))
      && (!hash || Number(hash[1]) === p.bloco) && window.location.hash !== '#titulo-pre-validacao-form1';
  }
  var posicao = null;
  try {
    var pendente = JSON.parse(sessao.getItem(chave) || 'null');
    sessao.removeItem(chave); // Intenção de salvar/permanecer é consumida uma só vez.
    if (validar(pendente) && Date.now() - pendente.instante < 120000) posicao = pendente;
  } catch (e) { /* Memória auxiliar inválida não impede a navegação. */ }
  var navegacao = window.performance && window.performance.getEntriesByType('navigation')[0];
  if (!posicao && navegacao && navegacao.type === 'reload') {
    var anterior = window.history.state && window.history.state.posicaoForm1;
    if (validar(anterior)) posicao = anterior;
  }
  // Uma única autoridade de rolagem evita a disputa com a restauração nativa.
  if ('scrollRestoration' in window.history) window.history.scrollRestoration = 'manual';
  raiz.addEventListener('input', function (e) { ultimaEdicao = e.target; });
  raiz.addEventListener('change', function (e) { ultimaEdicao = e.target; });
  function guardarLeitura() {
    var p = capturar(false);
    if (p) window.history.replaceState(Object.assign({}, window.history.state, {posicaoForm1: p}), '', window.location.href);
  }
  var esperaRolagem;
  window.addEventListener('scroll', function () {
    window.clearTimeout(esperaRolagem);
    esperaRolagem = window.setTimeout(guardarLeitura, 150);
  }, {passive: true});
  window.addEventListener('pagehide', guardarLeitura);
  return {
    posicao: posicao,
    antesDeSalvar: function (formulario, acionador) {
      sessao.removeItem(chave);
      if (acionador && acionador.value === 'proximo') return;
      var p = capturar(true);
      if (p && formulario.closest('.bloco-form1-integral') === blocoAtivo()) sessao.setItem(chave, JSON.stringify(p));
    },
    restaurar: function () {
      if (!posicao) return false;
      var p = posicao;
      var titulo = document.getElementById('titulo-bloco-' + p.bloco);
      var bloco = titulo && titulo.closest('.bloco-form1-integral');
      if (!visivel(bloco)) return false;
      var f = Array.from(bloco.querySelectorAll('form')).find(function (item) { return item.getAttribute('action') === p.acao; });
      var campo = f && controles(f)[p.indice];
      if (!campo || campo.name !== p.nome || !visivel(campo) || campo.disabled) campo = null;
      var alvo = campo || titulo;
      if (!campo) alvo.setAttribute('tabindex', '-1');
      alvo.focus({preventScroll: true});
      var margem = margemAtual();
      var topo = campo ? window.scrollY + campo.getBoundingClientRect().top - Math.max(margem, Math.min(p.topo, window.innerHeight - 80))
        : window.scrollY + bloco.getBoundingClientRect().top + Math.min(p.deslocamento, Math.max(0, bloco.getBoundingClientRect().height - 80)) - margem;
      window.scrollTo({top: Math.max(0, topo), behavior: 'instant'});
      return true;
    }
  };
};
