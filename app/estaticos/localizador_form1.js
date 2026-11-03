/* Busca explícita no catálogo; jamais lê ou interpreta a justificativa do APA. */
window.iniciarLocalizadorForm1 = function (raiz) {
  var area = raiz.querySelector('.localizador-pergunta');
  if (!area) return;
  var entrada = area.querySelector('input[type="search"]');
  var lista = area.querySelector('ul');
  var estado = area.querySelector('[role="status"]');
  var itens = Array.from(lista.querySelectorAll('[data-localizar-id]'));
  function normalizar(texto) {
    return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();
  }
  entrada.addEventListener('input', function () {
    var busca = normalizar(entrada.value);
    var exato = itens.some(function (item) { return item.dataset.localizarId === busca; });
    var encontrados = 0;
    itens.forEach(function (item) {
      var corresponde = !!busca && (exato ? item.dataset.localizarId === busca
        : normalizar(item.dataset.localizarId + ' ' + item.dataset.localizarTitulo).includes(busca));
      item.hidden = !corresponde;
      if (corresponde) encontrados++;
    });
    lista.hidden = !encontrados;
    estado.textContent = !busca ? 'Digite para localizar uma pergunta.'
      : encontrados ? encontrados + ' pergunta(s) encontrada(s). Selecione o destino abaixo.'
      : 'Nenhuma pergunta encontrada. Revise o número ou parte do título.';
  });
};
