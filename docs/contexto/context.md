# Contexto do produto

## Produto

O Sistema Municipal de Governança LGPD apoia a Prefeitura de Hortolândia no mapeamento e na governança de serviços, processos e atividades que tratam dados pessoais. Ele organiza Registros LGPD, instrumentos, versões, análise, pendências, decisões, medidas e evidências.

O sistema mapeia tratamentos. Ele não é cadastro de cidadãos, servidores ou titulares.

## Fontes de verdade

| Fonte | Função |
|---|---|
| Cartilha LGPD e seus quatro FORMs | Referência funcional principal e linguagem para os servidores |
| SAD 00 a SAD 10 | Arquitetura, requisitos, workflow, dados, integrações, segurança, validação e decisões |
| `README.md` | Visão integrada e estado corrente da PoC |
| `docs/arquitetura/MAPA_M1a.md` | Leitura funcional e técnica do fluxo nuclear |
| Contratos em `docs/arquitetura/` | Fronteiras executáveis do corte implementado |
| `docs/aceite/` | Testes formais, evidências e estado do aceite |
| `docs/diario/DIARIO_POC.md` | Histórico datado das mudanças |

Os SADs completos ficam no conjunto documental de arquitetura mantido separadamente. Este repositório contém os guias operacionais necessários para construir e verificar a PoC.

## Estágio atual

- PoC nuclear M1a: tecnicamente concluída e aceita pelo Encarregado de Dados em 22/10/2026, com limitações conhecidas.
- Rodada formal: `M1A-20261022-001`.
- Resultado: 189 de 189 testes automatizados e 9 de 9 cenários `POC-TS` aprovados.
- Ensaio de volume: 1.000 Registros, 50.000 eventos, 1.000 cadeias íntegras e 25 reconstruções coincidentes.
- Pendente: apresentação, registro dos participantes e transferência técnica à T.I.
- PoC ampliada: iniciada por decisão expressa em 24/10/2026, de forma incremental. O contrato 3 candidato permite iniciar, salvar e retomar os 14 Blocos do FORM 1 integral no mesmo rascunho, acessíveis pelas quatro etapas de navegação. Canais múltiplos, continuidade institucional do APA e pré-validação consultiva estão implementados; a submissão integral permanece bloqueada.

## Escopo por camada

| Camada | Pergunta | Escopo resumido |
|---|---|---|
| PoC nuclear M1a | O desenho funciona? | Registro, FORM 1 sintético, versões, submissão, análise, devolução, validação, conclusão, pendência intersecretarial, auditoria, hash e reconstrução |
| PoC ampliada | O desenho resiste às situações difíceis? | FORM 1 integral, suspensão, retomada, cancelamento, reabertura, continuidade institucional, participação por unidade, backup e restauração |
| Piloto | A Prefeitura consegue operar? | Caso real autorizado, integrações, suporte, treinamento e operação pela equipe designada |

## Limites permanentes da PoC

- Somente massa fictícia.
- Nomes públicos das Secretarias podem ser reais; pessoas, vínculos, objetos, contextos e Registros permanecem fictícios.
- Hortoprev não integra o recorte atual das 18 Secretarias da Administração Direta.
- Nenhuma senha real existe na PoC.
- Inventários e relatórios são apoio; não substituem os FORMs nem criam campos automaticamente.
- Temporalidade e descarte dependem da tabela oficial e da governança municipal responsável.
- Piloto e produção exigem autorização, equipe, segurança e controles próprios.

## Frame para cada incremento

Antes de implementar uma funcionalidade, registre:

1. objetivo e problema;
2. dentro e fora do escopo;
3. regra de domínio e fonte SAD;
4. atores e autorizações;
5. estados e eventos afetados;
6. dados e catálogos utilizados;
7. critérios de aceite;
8. testes e evidências;
9. limitações e decisões pendentes.

