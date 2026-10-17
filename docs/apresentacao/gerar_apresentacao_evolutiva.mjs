import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
const { Presentation, PresentationFile } = await import(
  "file:///C:/Users/ailto/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs"
);

const workspaceDir = "D:\\Ailton\\PMH\\Cidades_Inteligentes\\LGPD\\poc";
const skillDir = "C:\\Users\\ailto\\.codex\\plugins\\cache\\openai-primary-runtime\\presentations\\26.1015.12040\\skills\\presentations";
const runtimePython = "C:\\Users\\ailto\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe";
const buildDir = path.join(workspaceDir, ".codex-build", "apresentacao");
const outputDir = path.join(workspaceDir, "docs", "apresentacao");
const finalPath = path.join(outputDir, "Jornada_LGPD_PoC_apresentacao_evolutiva_v2.pptx");
const imagePath = path.join(outputDir, "assets", "capa_guia_mato_grosso_do_sul.png");
const crestPath = path.join(outputDir, "assets", "brasao_hortolandia_cartilha.png");

const utils = await import(pathToFileURL(path.join(skillDir, "container_tools", "artifact_tool_utils.mjs")).href);
const { resolvePresentationFont, applyPresentationChartFont, finalizePresentation } = utils;
const fontFamily = resolvePresentationFont();

const W = 1280;
const H = 720;
const C = {
  navy: "#005596",
  blue: "#0B3A82",
  green: "#006B35",
  green2: "#149454",
  ink: "#18313F",
  muted: "#5D6B75",
  pale: "#EFF5F8",
  paleGreen: "#E8F4ED",
  paleBlue: "#E7F0F8",
  line: "#C8D5DE",
  white: "#FFFFFF",
  amber: "#B26A00",
};

function addShape(slide, { geometry = "rect", left, top, width, height, fill = "none", line = "none", radius, name }) {
  return slide.shapes.add({
    geometry,
    name,
    position: { left, top, width, height },
    fill,
    line: line === "none" ? { style: "solid", fill: "none", width: 0 } : line,
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function addText(slide, text, { left, top, width, height, size = 24, color = C.ink, bold = false, align = "left", valign = "middle", name }) {
  const box = addShape(slide, { geometry: "textbox", left, top, width, height, fill: "none", line: "none", name });
  box.text = text;
  box.text.style = { fontFamily, fontSize: size, color, bold, alignment: align, verticalAlignment: valign };
  return box;
}

function addTitle(slide, title, subtitle) {
  addText(slide, title, { left: 68, top: 42, width: 1010, height: 56, size: 34, bold: true, color: C.navy });
  if (subtitle) addText(slide, subtitle, { left: 70, top: 98, width: 1030, height: 34, size: 17, color: C.muted });
  slide.images.add({ blob: crestBytes.slice(0), contentType: "image/png", alt: "Brasão da Prefeitura Municipal de Hortolândia", fit: "contain", position: { left: 1128, top: 24, width: 76, height: 76 } });
  addShape(slide, { left: 68, top: 134, width: 1144, height: 3, fill: C.green, line: "none" });
}

function addFooter(slide, n) {
  addText(slide, "Apresentação evolutiva da PoC", { left: 70, top: 682, width: 360, height: 20, size: 11, color: C.muted });
  addText(slide, String(n), { left: 1170, top: 682, width: 40, height: 20, size: 11, color: C.muted, align: "right" });
}

function setNotes(slide, lines) {
  slide.speakerNotes.text = lines;
}

function addNode(slide, text, x, y, w, h, fill, textColor = C.ink, size = 20) {
  const node = addShape(slide, { geometry: "roundRect", left: x, top: y, width: w, height: h, fill, line: { style: "solid", fill: C.line, width: 1 }, radius: "rounded-xl" });
  node.text = text;
  node.text.style = { fontFamily, fontSize: size, color: textColor, bold: true, alignment: "center", verticalAlignment: "middle" };
  return node;
}

async function readImageBlob(p) {
  const bytes = await fs.readFile(p);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

const crestBytes = await readImageBlob(crestPath);
const presentation = Presentation.create({ slideSize: { width: W, height: H } });

// 1. Capa
{
  const s = presentation.slides.add();
  s.background.fill = C.white;
  addShape(s, { left: 0, top: 540, width: 1280, height: 180, fill: C.green, line: "none" });
  addShape(s, { geometry: "arc", left: 0, top: 500, width: 860, height: 220, fill: C.navy, line: "none" });
  addShape(s, { geometry: "arc", left: 580, top: 500, width: 700, height: 220, fill: C.green2, line: "none" });
  s.images.add({ blob: crestBytes.slice(0), contentType: "image/png", alt: "Brasão da Prefeitura Municipal de Hortolândia", fit: "contain", position: { left: 1000, top: 66, width: 190, height: 190 } });
  addText(s, "Jornada de Conformidade LGPD", { left: 90, top: 140, width: 850, height: 92, size: 48, bold: true, color: C.navy });
  addText(s, "PoC nuclear e evolução planejada", { left: 94, top: 240, width: 760, height: 44, size: 26, color: C.green });
  addText(s, "Prefeitura Municipal de Hortolândia", { left: 96, top: 310, width: 760, height: 34, size: 20, color: C.ink });
  addText(s, "Secretaria de Planejamento Urbano e Gestão Estratégica", { left: 96, top: 348, width: 780, height: 34, size: 18, color: C.ink });
  addText(s, "Versão de trabalho · 17 de outubro de 2026", { left: 96, top: 390, width: 650, height: 30, size: 16, color: C.muted });
  addText(s, "Um arquivo vivo, atualizado junto com a implementação", { left: 700, top: 626, width: 490, height: 36, size: 17, color: C.white, bold: true, align: "right" });
  setNotes(s, [
    "Apresentação iniciada em 17/10/2026 para acompanhar a evolução da PoC.",
    "Identidade institucional: Prefeitura Municipal de Hortolândia, Secretaria de Planejamento Urbano e Gestão Estratégica.",
    "Brasão municipal extraído da CARTILHA_LGPD_REV30_11_2026-10-16.docx, conforme padrão indicado pelo usuário.",
    "Referências institucionais de reporte: Andreia Missio, Secretária Adjunta, e Eduardo Marchetti Francisco, Secretário Municipal.",
  ]);
}

// 2. Origem e evolução
{
  const s = presentation.slides.add();
  s.background.fill = C.white;
  addTitle(s, "Como o trabalho evoluiu", "A PoC ficou menor, mas a arquitetura continua olhando para a Jornada completa");
  const img = await readImageBlob(imagePath);
  s.images.add({ blob: img, contentType: "image/png", alt: "Capa do guia de boas práticas LGPD do Governo do Estado de Mato Grosso do Sul", fit: "contain", position: { left: 76, top: 166, width: 290, height: 440 } });

  const nodes = [
    ["Referência estadual\nMato Grosso do Sul", 430, 164, C.paleBlue],
    ["Inventário municipal\nadaptado", 430, 254, C.paleGreen],
    ["Jornada municipal\nem quatro FORMs", 430, 344, C.paleBlue],
    ["PoC nuclear +\nPoC ampliada", 430, 434, C.paleGreen],
    ["PoC ampliada\nessencial até dezembro", 430, 524, C.paleBlue],
  ].map(([t, x, y, fill]) => addNode(s, t, x, y, 410, 66, fill, C.ink, 19));
  for (let i = 0; i < nodes.length - 1; i++) {
    s.shapes.connect(nodes[i], nodes[i + 1], { fromSide: "bottom", toSide: "top", kind: "straight", line: { style: "solid", fill: C.green, width: 2 }, tail: { type: "arrow", width: "sm", length: "sm" } });
  }
  addText(s, "A redução de escopo protege o prazo. Ela não apaga o desenho dos quatro instrumentos.", { left: 875, top: 260, width: 315, height: 150, size: 23, bold: true, color: C.navy, align: "center" });
  addText(s, "Cada incremento deve dizer qual parte da Jornada prova hoje e qual parte permanece planejada.", { left: 875, top: 430, width: 315, height: 120, size: 18, color: C.muted, align: "center" });
  addFooter(s, 2);
  setNotes(s, [
    "Fontes: Inventário de dados2.pdf. O próprio formulário declara adaptação do modelo do Poder Executivo Estadual do Mato Grosso do Sul.",
    "Fonte: docs/planejamento/LGPD_PoC.docx. Registra PoC nuclear, PoC ampliada essencial e itens fora do escopo de 2026.",
    "Fonte visual: docs/apresentacao/assets/capa_guia_mato_grosso_do_sul.png.",
  ]);
}

// 3. Os quatro FORMs
{
  const s = presentation.slides.add();
  s.background.fill = C.white;
  addTitle(s, "Os quatro instrumentos continuam sendo o norte", "O Registro LGPD liga as quatro etapas sem misturar seus estados, versões e responsabilidades");
  const labels = [
    ["FORM 1", "Realidade", "Como o tratamento funciona de fato", C.navy],
    ["FORM 2", "Legitimidade", "Por que o tratamento pode ocorrer", C.green],
    ["FORM 3", "Risco", "O que pode afetar os titulares", C.navy],
    ["FORM 4", "Ação e\nacompanhamento", "O que será feito e acompanhado", C.green],
  ];
  const nodes = [];
  labels.forEach(([code, name, desc, color], i) => {
    const x = 65 + i * 300;
    const n = addShape(s, { geometry: "roundRect", left: x, top: 220, width: 255, height: 230, fill: C.white, line: { style: "solid", fill: color, width: 3 }, radius: "rounded-xl" });
    addText(s, code, { left: x + 18, top: 244, width: 219, height: 30, size: 17, bold: true, color });
    addText(s, name, { left: x + 18, top: 286, width: 219, height: 62, size: name.includes("\n") ? 22 : 27, bold: true, color: C.ink, align: "center" });
    addText(s, desc, { left: x + 24, top: 358, width: 207, height: 70, size: 16, color: C.muted, align: "center" });
    nodes.push(n);
  });
  for (let i = 0; i < nodes.length - 1; i++) {
    s.shapes.connect(nodes[i], nodes[i + 1], { fromSide: "right", toSide: "left", kind: "straight", line: { style: "solid", fill: C.line, width: 2 }, tail: { type: "arrow", width: "sm", length: "sm" } });
  }
  addShape(s, { geometry: "roundRect", left: 315, top: 510, width: 650, height: 88, fill: C.pale, line: { style: "solid", fill: C.line, width: 1 }, radius: "rounded-xl" });
  addText(s, "Mesmo Identificador LGPD", { left: 350, top: 526, width: 580, height: 28, size: 22, bold: true, color: C.navy, align: "center" });
  addText(s, "Um Registro, quatro instrumentos com histórico próprio", { left: 350, top: 558, width: 580, height: 24, size: 16, color: C.muted, align: "center" });
  addFooter(s, 3);
  setNotes(s, [
    "Rótulos históricos recuperados em SAD_03_ATORES_PAPEIS_E_PERMISSOES_REV07.docx, SAD_04_WORKFLOW_E_ESTADOS_REV07.docx e SAD_05_MODELO_DE_DADOS_E_IDENTIFICADORES_REV07.docx.",
    "Fonte vigente de arquitetura: SAD_02_REQUISITOS_FUNCIONAIS_REV17.docx. Os campos internos dos FORMs ficam fora do SAD 02, mas os quatro instrumentos permanecem vinculados ao mesmo Identificador LGPD.",
  ]);
}

// 4. Recorte correto do inventário
{
  const s = presentation.slides.add();
  s.background.fill = C.white;
  addTitle(s, "O recorte do inventário LGPD", "Não é necessário mapear toda atividade municipal sem relação com titulares");
  const a = addNode(s, "Serviço, processo\nou atividade municipal", 90, 250, 280, 120, C.paleBlue, C.ink, 21);
  const b = addNode(s, "Há tratamento de\ndados pessoais?", 500, 235, 280, 150, C.white, C.navy, 23);
  const c = addNode(s, "Entra na Jornada\ne no inventário", 910, 170, 280, 120, C.paleGreen, C.green, 22);
  const d = addNode(s, "Fica fora do inventário\nLGPD", 910, 390, 280, 120, C.pale, C.muted, 22);
  s.shapes.connect(a, b, { fromSide: "right", toSide: "left", kind: "straight", line: { style: "solid", fill: C.navy, width: 3 }, tail: { type: "arrow" } });
  s.shapes.connect(b, c, { fromSide: "right", toSide: "left", kind: "elbow", line: { style: "solid", fill: C.green, width: 3 }, tail: { type: "arrow" } });
  s.shapes.connect(b, d, { fromSide: "right", toSide: "left", kind: "elbow", line: { style: "solid", fill: C.muted, width: 2 }, tail: { type: "arrow" } });
  addText(s, "sim", { left: 805, top: 213, width: 70, height: 28, size: 15, bold: true, color: C.green, align: "center" });
  addText(s, "não", { left: 805, top: 430, width: 70, height: 28, size: 15, bold: true, color: C.muted, align: "center" });
  addText(s, "Quando houver dados sensíveis, os cuidados especiais precisam ficar documentados no próprio percurso.", { left: 250, top: 530, width: 780, height: 70, size: 22, bold: true, color: C.navy, align: "center" });
  addFooter(s, 4);
  setNotes(s, [
    "Fonte: README.md. O catálogo operacional lista serviços, processos e atividades que tratam ou podem tratar dados pessoais.",
    "Fonte: CARTILHA_LGPD_REV30_11_2026-10-16.docx. O inventário sustenta finalidades, bases legais, compartilhamentos, retenção, segurança e avaliação de riscos.",
    "Decisão de trabalho discutida em 16/10 e 17/10: explicitar a triagem LGPD e os controles para dados sensíveis nos próximos incrementos.",
  ]);
}

// 5. Matriz de alinhamento
{
  const s = presentation.slides.add();
  s.background.fill = C.white;
  addTitle(s, "Matriz de alinhamento com os quatro FORMs", "A PoC reduz profundidade e volume, mas preserva a direção arquitetural");
  const values = [
    ["Instrumento", "PoC nuclear M1a", "PoC ampliada essencial", "Depois da PoC"],
    ["FORM 1\nRealidade", "Contrato sintético\ne motor completo", "FORM 1 real\ne ingestão", "Operação institucional"],
    ["FORM 2\nLegitimidade", "Motor compatível", "Segundo instrumento\nmínimo executável", "Instrumento integral"],
    ["FORM 3\nRisco", "Motor compatível", "Estrutura preservada", "Instrumento integral\ne RIPD"],
    ["FORM 4\nAção e acompanhamento", "Ação obrigatória\nsintética", "Fluxos de controle\ne continuidade", "Instrumento integral"],
  ];
  const table = s.tables.add({ rows: 5, columns: 4, left: 66, top: 180, width: 1148, height: 405, values, columnWidths: [230, 285, 315, 318] });
  table.borders.assign({ style: "solid", fill: C.line, width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: 4 }).assign({ fill: C.navy, textStyle: { fontFamily, fontSize: 17, bold: true, color: C.white }, margins: { left: 12, right: 12, top: 8, bottom: 8 }, anchor: "middle" });
  table.cells.block({ row: 1, column: 0, rowCount: 4, columnCount: 1 }).assign({ fill: C.paleBlue, textStyle: { fontFamily, fontSize: 17, bold: true, color: C.navy }, margins: { left: 12, right: 12, top: 8, bottom: 8 }, anchor: "middle" });
  table.cells.block({ row: 1, column: 1, rowCount: 4, columnCount: 3 }).assign({ fill: C.white, textStyle: { fontFamily, fontSize: 16, color: C.ink }, margins: { left: 12, right: 12, top: 8, bottom: 8 }, anchor: "middle" });
  addText(s, "Regra de acompanhamento: nenhum incremento deve contradizer os quatro instrumentos, mesmo quando só implementa uma parte deles.", { left: 125, top: 610, width: 1030, height: 46, size: 19, bold: true, color: C.green, align: "center" });
  addFooter(s, 5);
  setNotes(s, [
    "Fonte: README.md, seção PoC nuclear x PoC ampliada.",
    "Fonte: docs/planejamento/LGPD_PoC.docx, seções 3 e 4.",
    "Fonte: SAD_09_POC_E_VALIDACAO_TECNICA_REV12.docx e SAD_10_DECISOES_DE_ARQUITETURA_REV16.docx.",
    "A expressão 'segundo instrumento mínimo executável' não define qual dos FORMs 2 a 4 será escolhido. Essa escolha permanece pendente.",
  ]);
}

// 6. Fluxo M1a
{
  const s = presentation.slides.add();
  s.background.fill = C.white;
  addTitle(s, "Fluxo implementado no M1a", "Rascunho, versão, análise e devolução preservam autoria, histórico e concorrência");
  const steps = [
    ["1", "Criar Registro", "G1"],
    ["2", "Preencher e salvar", "I1 · I2"],
    ["3", "Submeter versão", "I3"],
    ["4", "Analisar", "I13 · I14"],
    ["5", "Validar ou devolver", "I5 · I6"],
    ["6", "Corrigir com pendência", "P1 · P2 · I7"],
  ];
  const nodes = [];
  steps.forEach(([num, name, code], i) => {
    const x = 60 + i * 202;
    const fill = i % 2 === 0 ? C.paleBlue : C.paleGreen;
    const n = addShape(s, { geometry: "roundRect", left: x, top: 245, width: 168, height: 168, fill, line: { style: "solid", fill: i % 2 === 0 ? C.navy : C.green, width: 2 }, radius: "rounded-xl" });
    const badge = addShape(s, { geometry: "ellipse", left: x + 55, top: 214, width: 58, height: 58, fill: i % 2 === 0 ? C.navy : C.green, line: "none" });
    badge.text = num;
    badge.text.style = { fontFamily, fontSize: 23, bold: true, color: C.white, alignment: "center", verticalAlignment: "middle" };
    addText(s, name, { left: x + 14, top: 286, width: 140, height: 64, size: 19, bold: true, color: C.ink, align: "center" });
    addText(s, code, { left: x + 14, top: 358, width: 140, height: 28, size: 15, bold: true, color: i % 2 === 0 ? C.navy : C.green, align: "center" });
    nodes.push(n);
  });
  for (let i = 0; i < nodes.length - 1; i++) {
    s.shapes.connect(nodes[i], nodes[i + 1], { fromSide: "right", toSide: "left", kind: "straight", line: { style: "solid", fill: C.line, width: 2 }, tail: { type: "arrow", width: "sm", length: "sm" } });
  }
  addText(s, "A versão submetida não é apagada. Uma tela antiga não pode sobrescrever um salvamento novo.", { left: 180, top: 505, width: 920, height: 62, size: 22, bold: true, color: C.navy, align: "center" });
  addText(s, "As ações de conclusão e os passos restantes da pendência entram nos próximos incrementos.", { left: 250, top: 575, width: 780, height: 38, size: 17, color: C.muted, align: "center" });
  addFooter(s, 6);
  // Mantém o brasão acima dos conectores do fluxo neste slide.
  s.images.add({ blob: crestBytes.slice(0), contentType: "image/png", alt: "Brasão da Prefeitura Municipal de Hortolândia", fit: "contain", position: { left: 1128, top: 24, width: 76, height: 76 } });
  setNotes(s, [
    "Fontes: README.md e docs/arquitetura/MAPA_M1a.md.",
    "Implementação local ainda não commitada em 17/10/2026. Preservar esse status até decisão explícita de commit.",
  ]);
}

// 7. Testes
{
  const s = presentation.slides.add();
  s.background.fill = C.white;
  addTitle(s, "113 testes confirmam o núcleo construído", "A suíte completa passou novamente em 17 de outubro de 2026");
  const chart = s.charts.add("bar", {
    position: { left: 80, top: 175, width: 760, height: 420 },
    categories: ["Submissão", "Duplicidade", "Rascunho", "Idempotência", "Transversalidade", "Integridade", "Numeração", "Segregação"],
    series: [{ name: "Testes", values: [59, 18, 14, 6, 6, 5, 3, 2], fill: C.navy }],
    hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 14, color: C.ink } },
    xAxis: { majorGridlines: { style: "solid", fill: C.line, width: 1 }, textStyle: { fontSize: 12, color: C.muted } },
    yAxis: { textStyle: { fontSize: 14, color: C.ink } },
  });
  applyPresentationChartFont(chart, { fontFamily });
  addText(s, "113", { left: 905, top: 235, width: 250, height: 110, size: 72, bold: true, color: C.green, align: "center" });
  addText(s, "testes aprovados", { left: 905, top: 342, width: 250, height: 40, size: 22, bold: true, color: C.ink, align: "center" });
  addText(s, "7 migrações aplicadas\n0 migrações pendentes", { left: 905, top: 430, width: 250, height: 90, size: 20, color: C.navy, align: "center" });
  addFooter(s, 7);
  setNotes(s, [
    "Fonte: execução local de pytest -q em 17/10/2026. Toda a suíte passou.",
    "Coleta: duplicidade 18, idempotência 6, integridade 5, numeração 3, rascunho 14, segregação 2, submissão 59, transversalidade 6.",
    "Fonte: migracoes.aplicar em 17/10/2026. Sete versões aplicadas e nenhuma pendente.",
  ]);
}

// 8. Próximos passos
{
  const s = presentation.slides.add();
  s.background.fill = C.white;
  addTitle(s, "Próximos passos sem perder a visão completa", "Fechar o M1a e reforçar o recorte LGPD antes de ampliar o escopo");
  const left = addShape(s, { geometry: "roundRect", left: 75, top: 190, width: 520, height: 405, fill: C.paleGreen, line: { style: "solid", fill: C.green, width: 2 }, radius: "rounded-xl" });
  const right = addShape(s, { geometry: "roundRect", left: 685, top: 190, width: 520, height: 405, fill: C.paleBlue, line: { style: "solid", fill: C.navy, width: 2 }, radius: "rounded-xl" });
  addText(s, "Fechar o M1a", { left: 110, top: 220, width: 450, height: 44, size: 28, bold: true, color: C.green, align: "center" });
  addText(s, "• completar resposta e aceite da pendência\n• concluir ação obrigatória e G6\n• produzir telas mínimas e evidências\n• registrar o aceite da PoC nuclear", { left: 125, top: 285, width: 420, height: 230, size: 20, color: C.ink });
  addText(s, "Reforçar o recorte LGPD", { left: 720, top: 220, width: 450, height: 44, size: 28, bold: true, color: C.navy, align: "center" });
  addText(s, "• triagem explícita: há dados pessoais?\n• marcar categorias sensíveis\n• documentar cuidados especiais\n• manter categorias fechadas, sem nomes de titulares", { left: 735, top: 285, width: 420, height: 230, size: 20, color: C.ink });
  addText(s, "A apresentação será atualizada a cada incremento relevante e continuará mostrando o vínculo com os quatro FORMs.", { left: 180, top: 620, width: 920, height: 44, size: 19, bold: true, color: C.navy, align: "center" });
  addFooter(s, 8);
  setNotes(s, [
    "Fontes: README.md, docs/arquitetura/MAPA_M1a.md e docs/planejamento/LGPD_PoC.docx.",
    "Os dois reforços de recorte são decisões de desenho a incorporar em incremento posterior, não funcionalidades já concluídas.",
  ]);
}

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

for (const [index, slide] of presentation.slides.items.entries()) {
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(buildDir, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
}
const montage = await presentation.export({ format: "webp", montage: true });
await fs.writeFile(path.join(buildDir, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));

const candidatePath = path.join(buildDir, "candidate-v2.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const result = await finalizePresentation({
  explicitTotalSlideCount: 8,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit", "--require-native-table-slide", "5"],
  requiredNativeTableOwnerSlides: [5],
  requiredNativeChartOwnerSlides: [],
  materializeLiteralChartWorkbooks: true,
  fontPolicy: { basis: "design", families: [...new Set([fontFamily, "Aptos"])] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, "Jornada_LGPD_PoC_apresentacao_evolutiva_v2.validation.json"),
});

console.log(JSON.stringify({ finalPath, fontFamily, result }, null, 2));
