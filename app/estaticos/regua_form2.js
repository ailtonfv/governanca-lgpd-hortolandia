(() => {
  const regua = document.querySelector('nav[data-preparacao]');
  if (!regua || !regua.dataset.preparacao) return;
  const prefixo = JSON.stringify([regua.dataset.conta, regua.dataset.preparacao]);
  function atualizar() {
    const destino = {'#identificacao': '1', '#unidade-guarda': '2'}[location.hash];
    for (const link of regua.querySelectorAll('[data-numero]')) {
      const chave = 'visita-form2:' + prefixo + ':' + link.dataset.numero;
      let visitado = link.getAttribute('aria-current') === 'page' ||
        (destino === link.dataset.numero && document.getElementById(location.hash.slice(1)));
      try {
        if (visitado) sessionStorage.setItem(chave, '1');
        visitado = sessionStorage.getItem(chave) === '1';
      } catch { /* A página atual continua identificada sem armazenamento local. */ }
      link.classList.toggle('bloco-visitado', Boolean(visitado));
      link.querySelector('[data-visitado]').hidden = !visitado;
    }
  }
  atualizar();
  window.addEventListener('pageshow', atualizar);
  window.addEventListener('hashchange', atualizar);
})();
