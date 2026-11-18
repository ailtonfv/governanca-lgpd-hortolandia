// Somente orientação; contagem e bloqueio de consolidação ficam no domínio.
function atualizarComplementos() {
 document.querySelectorAll('[data-complemento-necessario]').forEach(aviso => {
  const campos = [...document.getElementsByName(aviso.dataset.opcao)];
  const selecionadas = campos.filter(e => !e.matches(':disabled') && (e.tagName === 'SELECT' || e.checked)).map(e => e.value);
  const texto = document.getElementsByName(aviso.dataset.texto)[0];
  aviso.hidden = !selecionadas.some(v => JSON.parse(aviso.dataset.codigos).includes(v)) || !!texto?.value.trim();
 });
}
document.addEventListener('input', atualizarComplementos);
document.addEventListener('change', atualizarComplementos);
atualizarComplementos();
