// Ensaio do script real com DOM simulado; não comprova aceitação visual.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const elemento = () => ({eventos: {}, addEventListener(t, f) {this.eventos[t] = f;}, focus() {this.focado = true;}});
const form = elemento(), dialogo = elemento(), cancelar = elemento(), efetivar = elemento();
const ciencia = {checked: true};
let envios = 0;
form.requestSubmit = () => {
  if (!ciencia.checked) return; // validação nativa do required antes do evento submit
  const evento = {impedido: false, preventDefault() {this.impedido = true;}};
  form.eventos.submit(evento);
  if (!evento.impedido) envios++;
};
dialogo.showModal = () => {dialogo.open = true;};
dialogo.close = () => {dialogo.open = false;};
dialogo.querySelector = s => s.includes('cancelar') ? cancelar : efetivar;
const window = elemento();
vm.runInNewContext(fs.readFileSync('app/estaticos/decisao_conferencia.js', 'utf8'), {
  window, document: {getElementById(id) {return ({'form-confirmar-conferencia': form, 'dialogo-confirmar-conferencia': dialogo, 'ciencia-confirmacao': ciencia})[id];}}
});
window.eventos.pageshow();
assert.equal(ciencia.checked, false);
form.requestSubmit();
assert.equal(envios, 0);
ciencia.checked = true;
form.requestSubmit();
assert.equal(envios, 0);
assert.equal(dialogo.open, true);
assert.equal(cancelar.focado, true);
cancelar.eventos.click();
assert.equal(dialogo.open, false);
assert.equal(envios, 0);
form.requestSubmit();
dialogo.eventos.cancel(); // Escape não decide
dialogo.close();
assert.equal(envios, 0);
form.requestSubmit();
efetivar.eventos.click();
assert.equal(envios, 1);
efetivar.eventos.click();
form.requestSubmit();
assert.equal(envios, 1); // repetição local não envia novamente
window.eventos.pageshow();
assert.equal(ciencia.checked, false);
assert.equal(efetivar.disabled, false);
console.log('Decisão explícita, cancelamento, Escape, repetição e retorno verificados.');
