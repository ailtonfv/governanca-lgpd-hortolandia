(() => {
  const caixa = document.getElementById('confirmar-ato');
  let botao;
  let autorizado = false;
  document.addEventListener('submit', evento => {
    if (!evento.submitter?.hasAttribute('data-confirmar-ato') || autorizado) return;
    evento.preventDefault();
    botao = evento.submitter;
    caixa.querySelector('h2').textContent = botao.textContent.trim() + '?';
    caixa.querySelector('[data-descricao]').textContent = botao.dataset.confirmarAto;
    caixa.querySelector('[data-confirmar]').textContent = botao.textContent.trim();
    caixa.showModal();
  });
  caixa.querySelector('[data-cancelar]').onclick = () => caixa.close();
  caixa.querySelector('[data-confirmar]').onclick = () => {
    caixa.close();
    autorizado = true;
    document.dispatchEvent(new Event('ato-confirmado'));
    try { botao.form.requestSubmit(botao); } finally { autorizado = false; }
  };
})();
