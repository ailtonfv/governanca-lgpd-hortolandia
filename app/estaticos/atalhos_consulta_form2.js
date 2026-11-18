function atualizarAtalhosConsulta() {
 document.querySelectorAll('[data-atalho-consulta]').forEach(aviso => {
  const permitidos = JSON.parse(aviso.dataset.codigos);
  const campos = [...document.querySelectorAll('input[type=checkbox],select')].filter(e => e.name === 'resposta_' + aviso.dataset.item || e.name === 'opcao:' + aviso.dataset.item || e.name.startsWith('opcao:' + aviso.dataset.item + '#'));
  aviso.hidden = !campos.some(e => !e.matches(':disabled') && (e.tagName === 'SELECT' || e.checked) && permitidos.includes(e.value));
 });
}
document.addEventListener('change', atualizarAtalhosConsulta);
atualizarAtalhosConsulta();
