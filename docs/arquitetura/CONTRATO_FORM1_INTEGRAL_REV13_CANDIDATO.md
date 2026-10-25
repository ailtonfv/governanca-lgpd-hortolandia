# Contrato candidato do FORM 1 integral — REV13

**Situação:** candidato a contrato 3; rascunho parcial dos Blocos 1 a 4 implementado, ainda não aprovado para submissão
**Escopo:** preparação da PoC ampliada
**Fonte funcional:** FORM 1 do Documento-Mestre REV13, organizado nos três insumos de 23/10/2026
**Dados permitidos:** exclusivamente fictícios durante toda a PoC

## 1. Objetivo

Definir a fronteira segura para incorporar o FORM 1 integral sem substituir o FORM 1 sintético do M1a nem reinterpretar versões já submetidas.

O contrato nuclear 2 continua válido para todas as versões que já o utilizam. O contrato integral somente poderá ser gravado como uma nova versão de contrato depois da aprovação das decisões pendentes deste documento.

## 2. Compatibilidade obrigatória

- versões de contrato 1 e 2 permanecem imutáveis e recuperáveis;
- o motor vigente de rascunho, autoria, controle otimista, lacre, submissão, auditoria e cadeia de eventos será reutilizado;
- uma versão informa explicitamente qual contrato validou o seu conteúdo;
- o Registro e o FORM 1 continuam sob responsabilidade da Secretaria responsável;
- o Agente Público Autorizado pode abrir e preencher; outro servidor autorizado pode colaborar no preenchimento;
- nenhuma resposta pode identificar uma pessoa titular ou reproduzir caso real durante a PoC;
- texto visível, catálogo e código armazenado são tratados separadamente para evitar mudança retroativa de significado.

## 3. Conteúdo da REV13

O inventário possui **128 identificadores**, distribuídos em identificação inicial e 14 blocos. Condicionais fazem com que nem todas as perguntas sejam exibidas simultaneamente.

| Grupo | Identificadores |
|---|---:|
| Identificação do responsável pelo preenchimento | 3 |
| Bloco 1 — Identificação | 5 |
| Bloco 2 — Entrada, recepção e execução | 27 |
| Bloco 3 — Outras unidades, órgãos ou entidades participantes | 7 |
| Bloco 4 — Pessoas a quem os dados se referem | 9 |
| Bloco 5 — Categorias de dados | 1 |
| Bloco 6 — Origem dos dados | 5 |
| Bloco 7 — O que é feito com os dados | 1 |
| Bloco 8 — Sistemas, canais e suporte | 23 |
| Bloco 9 — Acesso | 5 |
| Bloco 10 — Envio, disponibilização ou saída | 12 |
| Bloco 11 — Armazenamento e dependência de terceiro | 8 |
| Bloco 12 — Guarda e destinação | 10 |
| Bloco 13 — Exposição física ou visual | 4 |
| Bloco 14 — Achados e pendências | 8 |
| **Total** | **128** |

Controles sugeridos na fonte: 55 seleções únicas, 31 seleções múltiplas, 24 respostas curtas ou numéricas, 8 textos longos, 4 reutilizações de catálogo, 3 faixas de volume, 2 seleções de Secretaria e 1 controle ainda a confirmar.

### Organização visual decidida em 24/10/2026

| Etapa | Blocos | Denominação |
|---|---|---|
| 1 de 4 | 1–3 | Identificação e funcionamento do serviço |
| 2 de 4 | 4–8 | Dados pessoais e operações de tratamento |
| 3 de 4 | 9–11 | Acesso, compartilhamento e armazenamento |
| 4 de 4 | 12–14 | Guarda, situações observadas e pendências |

Os itens 0.1 a 0.3 antecedem as quatro etapas. As etapas são divisões de apresentação do mesmo FORM 1, não instrumentos independentes.

## 4. Forma candidata do conteúdo

O snapshot integral deverá possuir um envelope próprio, distinto do objeto plano do contrato 2:

```json
{
  "revisao_fonte": "REV13-2026-09-20",
  "respostas": {
    "2.1": "<codigo-de-catalogo>",
    "2.5": ["<codigo-de-catalogo>"],
    "2.6": "<texto factual limitado>"
  }
}
```

Essa forma permanece candidata para submissão, mas já é executada no rascunho parcial dos Blocos 1 a 4. O envelope registra `revisao_fonte`, `versao_contrato`, `respostas` e, no Bloco 3, uma coleção de `participantes`; o rascunho pode permanecer incompleto. Somente a futura submissão aplicará a validação integral do contrato aprovado.

No primeiro recorte executável, `1.2` e `1.3` são reaproveitados do tipo e do nome do objeto registrados na abertura. O ARP edita `1.1`, `1.1.1` e `1.4`; valores de seleção precisam pertencer ao catálogo REV13. A condição de `1.1.1` é apresentada na interface quando `1.1 = Sim`, sem converter ou inventar respostas.

O incremento F1-2 acrescenta o Bloco 2, inclusive os ramos condicionais de Ouvidoria e e-SIC, e o Bloco 3. Cada participante do Bloco 3 possui identificador e respostas próprias; adicionar ou remover uma ocorrência gera nova versão do mesmo rascunho e evento próprio. O primeiro recorte de F1-3 acrescenta o Bloco 4 por categorias, reutilizando no item 4.2.5.1 o catálogo do item 5.1 sem antecipar o próprio Bloco 5.

Os itens 0.1 a 0.3 não autorizam digitação livre de identidade. Nome, função e contato institucional serão apresentados como metadados somente leitura quando existirem na identidade simulada ou na futura integração institucional. Dados indisponíveis não serão inventados.

## 5. Relação com o núcleo do contrato 2

| Contrato 2 | Campo candidato da REV13 | Situação |
|---|---|---|
| `finalidade` | 2.11 | Significado compatível; limite e regra de unicidade precisam de confirmação. |
| `categorias_titulares` | 4.1 | Granularidade diferente; exige tabela de correspondência e lacunas. |
| `categorias_dados` | 5.1 | Catálogo integral é mais específico; não existe correspondência automática 1:1. |
| `compartilhamentos` | 10.1 e 10.2 | Deve separar existência de saída e destinatários; códigos atuais não podem ser ampliados por analogia. |

O contrato 3 não reutilizará silenciosamente os códigos do contrato 2 com significado diferente. Qualquer ponte entre versões será explícita e testada.

## 6. Validações que já podem ser especificadas

No rascunho implementado dos Blocos 1 a 4 já são verificadas autoria do ARP, designação vigente de `preenchedor`, catálogo fechado, identificadores permitidos, seleções múltiplas sem repetição, Secretaria ativa, idempotência, versão lida, atomicidade e cadeia de eventos. O contrato nuclear 2 continua em tabela, rotas e fluxo próprios.

- rejeitar identificador de pergunta desconhecido;
- rejeitar alternativa que não pertença ao catálogo versionado da pergunta;
- impedir repetição em seleção múltipla;
- aceitar rascunho parcial;
- preservar condicionais sem apagar respostas históricas silenciosamente;
- impedir que alternativas excludentes do item 13.1 coexistam com situações concretas;
- tratar cada participante dos itens 3.2 a 3.5 como ocorrência própria;
- limitar e orientar textos livres, recusando conteúdo incompatível com massa fictícia;
- preservar autoria individual e controle otimista em cada salvamento;
- gerar nova versão imutável na submissão, sem alterar as versões anteriores.

## 7. Decisões pendentes antes da submissão integral

1. aprovar códigos e correspondências dos catálogos dos itens 4.1, 5.1 e 10.2;
2. resolver a condição de WhatsApp, que menciona uso pessoal sem essa alternativa constar no item 8.3;
3. definir o tratamento controlado da alternativa “Outro” e seus complementos;
4. validar as combinações excludentes nas demais seleções múltiplas;
5. definir como função e e-mail institucional serão obtidos sem autenticação real na PoC;
6. confirmar o marco e o critério de aceite que autorizam a submissão pelo contrato 3.

A obrigatoriedade candidata está detalhada em `docs/planejamento/MATRIZ_CAMPOS_FORM1_REV13.md`: campos essenciais, condicionais e facultativos. Rascunhos incompletos e navegação permanecem permitidos; somente a submissão integral futura aplicará bloqueios aos campos obrigatórios ativos.

Enquanto essas decisões estiverem abertas, a preparação estrutural pode avançar, mas a submissão integral não será apresentada como funcionalidade concluída.

## 8. Rastreabilidade dos insumos

| Insumo | SHA-256 |
|---|---|
| `FORM1_INTEGRAL_REV13_PARA_CODEX.md` | `26f502eb0c27ebe737050193854444111ce2814ba82e70b30b3ad2fad4f0719d` |
| `INSTRUCAO_AO_CODEX_FORM1.md` | `819804e8233de903a404f2d78cf15ae5b4dc88cedc9499978be27c49c4cc546d` |
| `INVENTARIO_CAMPOS_FORM1_REV13.csv` | `37b0c10b0352d1529b73bcfb1a2f57cd95dbcee2c195f4f32b8b028f5d8cc002` |
