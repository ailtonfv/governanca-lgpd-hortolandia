// Ensaio de comportamento DOM simulado, sem alegar inspeção visual.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const callbacks = {};
const input = {value: 'Salvo fictício'};
const saved = {textContent: JSON.stringify(input.value)};
const form = {};
let focused = false;
let consent = false;
const target = {focus() { focused = true; }};
const elements = {'anotacao': input, 'form2-conteudo-salvo': saved, 'form2-rascunho': form, 'anotacoes': target};
const ctx = {
  document: {getElementById: id => elements[id], addEventListener: (name, cb) => callbacks[name] = cb},
  window: {addEventListener: (name, cb) => callbacks[name] = cb, confirm: () => consent},
  location: {href: 'http://testserver/preparacao#anotacoes', hash: '#anotacoes'}
};
vm.runInNewContext(fs.readFileSync('app/estaticos/form2_preparacao.js', 'utf8'), ctx);
assert.equal(focused, true);
const event = target => ({target, prevented: false, preventDefault() { this.prevented = true; }});
let e = event({}); callbacks.beforeunload(e); assert.equal(e.prevented, false);
input.value = 'Mudança fictícia';
e = event({}); callbacks.beforeunload(e); assert.equal(e.prevented, true);
e = event({closest: () => ({})}); callbacks.click(e); assert.equal(e.prevented, true);
assert.equal(input.value, 'Mudança fictícia');
e = event({closest: () => ({hash: '#anotacoes', href: ctx.location.href})});
callbacks.click(e); assert.equal(e.prevented, false);
e = event({closest: () => ({hash: '#anotacoes', href: 'http://testserver/outra-preparacao#anotacoes'})});
callbacks.click(e); assert.equal(e.prevented, true);
e = event({}); callbacks.submit(e); assert.equal(e.prevented, true);
consent = true;
e = event({closest: () => ({})}); callbacks.click(e); assert.equal(e.prevented, false);
e = event(form); callbacks.submit(e); assert.equal(e.prevented, false);
e = event({}); callbacks.beforeunload(e); assert.equal(e.prevented, false);
