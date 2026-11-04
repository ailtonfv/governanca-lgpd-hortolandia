/* Associação HTML nativa: Bloco 10 e ocorrências continuam formulários irmãos. */
window.elementosFormularioForm1 = function (formulario, seletor) {
  var elementos = Array.from(formulario.querySelectorAll(seletor));
  var continuacao = formulario.id && document.querySelector('[data-continuacao-formulario="' + formulario.id + '"]');
  if (continuacao) elementos = elementos.concat(Array.from(continuacao.querySelectorAll(seletor)));
  Array.from(formulario.elements || []).forEach(function (controle) {
    if (controle.matches(seletor) && !elementos.includes(controle)) elementos.push(controle);
  });
  return elementos;
};
document.querySelectorAll('[data-continuacao-formulario]').forEach(function (area) {
  ['input', 'change'].forEach(function (tipo) {
    area.addEventListener(tipo, function (evento) {
      // Os controles externos não propagam eventos até seu form associado.
      // Notifica os observadores existentes, sem executar salvamento adicional.
      if (evento.target.form) evento.target.form.dispatchEvent(new Event(tipo));
    });
  });
});
document.querySelectorAll('[data-destinatario-editor]').forEach(function (editor) {
  var categoria = editor.querySelector('[name="destinatario__categoria"]');
  var modo = editor.querySelector('[name="destinatario__modalidade"]');
  var complementares = editor.querySelector('[data-destinatario-complementares]');
  var municipais = JSON.parse(editor.dataset.categoriasMunicipais);
  function orientar() {
    // Recolher não desabilita, apaga ou torna obrigatórios os campos.
    complementares.open = !municipais.includes(categoria.value) || modo.value !== 'identificado';
  }
  categoria.addEventListener('change', orientar);
  modo.addEventListener('change', orientar);
  orientar();
});
