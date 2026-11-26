document.querySelectorAll('[data-fechar-cartilha]').forEach(botao => {
  // Abas abertas pelo usuário podem não aceitar window.close; a instrução permanece.
  botao.hidden = !window.opener;
  botao.addEventListener('click', () => window.close());
});
