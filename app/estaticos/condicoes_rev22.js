/* Prévia das condições; o domínio volta a validar cada salvamento. */
(() => {
  const origem = document.getElementById('condicoes-rev22');
  if (!origem) return;
  const modelo = JSON.parse(origem.textContent);
  const lista = v => Array.isArray(v) ? v : v ? [v] : [];
  function atualizar() {
    const respostas = {...modelo.respostas};
    const campos = [...document.querySelectorAll('[data-condicao-pergunta]')];
    for (const campo of campos) {
      const id = campo.dataset.condicaoPergunta;
      const inputs = [...campo.querySelectorAll('[name="r:' + id + '"]')];
      const checks = inputs.filter(i => i.type === 'checkbox');
      respostas[id] = checks.length ? checks.filter(i => i.checked).map(i => i.value) : inputs.find(i => i.type !== 'hidden')?.value || '';
    }
    const canais = ['2.1', '2.1.1', '8.3'].flatMap(k => lista(respostas[k]));
    function ativa(id, vistos = new Set()) {
      if (vistos.has(id)) return false;
      const q = modelo.campos[id];
      if (!q) return false;
      const tem = (k, opcoes) => lista(respostas[k]).some(x => opcoes.includes(x));
      if (id.startsWith('WPP.') && !canais.some(x => x.includes('WhatsApp'))) return false;
      if (id.startsWith('OUV.') && !canais.includes('Ouvidoria')) return false;
      if (id.startsWith('ESIC.') && !canais.includes('e-SIC')) return false;
      if (id.startsWith('3.') && id !== '3.1' && !tem('3.1', ['Sim'])) return false;
      if (id.startsWith('10.') && id !== '10.1' && !tem('10.1', ['Sim','Em alguns casos'])) return false;
      if (['13.3','13.4'].includes(id) && !lista(respostas['13.1']).some(x => !['A confirmar','Não se aplica','Nenhuma das situações acima'].includes(x))) return false;
      let cs = q.conditions || [];
      if (id.startsWith('OUV.') || id.startsWith('ESIC.')) cs = typeof cs[0] === 'string' ? [] : cs.filter(c => c[0] !== '2.1');
      if (typeof cs[0] === 'string') cs = [cs];
      return cs.every(([k, opcoes]) => tem(k, opcoes) && (k === id || ativa(k, new Set([...vistos, id]))));
    }
    for (const campo of campos) {
      const id = campo.dataset.condicaoPergunta, aberta = ativa(id);
      campo.hidden = campo.disabled = !aberta;
      const titulo = campo.querySelector('[data-titulo-condicional]');
      if (titulo) {
        const regra = JSON.parse(titulo.dataset.tituloCondicional);
        titulo.textContent = respostas[regra.source] === regra.value ? 'F1-' + id + ' — ' + regra.text : titulo.dataset.tituloPadrao;
      }
      const aviso = document.querySelector('[data-condicao-aviso="' + id + '"]');
      if (aviso) aviso.hidden = aberta;
    }
  }
  document.querySelectorAll('.form1-rev22 form').forEach(f => {
    f.addEventListener('change', atualizar);
    f.addEventListener('reset', () => setTimeout(atualizar, 0));
  });
  atualizar();
})();
