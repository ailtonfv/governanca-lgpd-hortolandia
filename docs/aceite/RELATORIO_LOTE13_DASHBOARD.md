# Lote 13 — dashboard demonstrativo — 20/11/2026

Branch `lote-13-dashboard`, base autorizada `f99c9fe` do Lote 12-F. Sem merge no `main`, sem migração e sem carga na base da vistoria. A implementação segue a especificação final de 20/11 e os dois complementos sobre ciências e espera do DPO.

| Implementado | Verificado | Falta conferir em tela |
|---|---|---|
| Abertura: atenção por perfil, Registros ativos, faixa do pior risco, esteira, atrasos, aprendizagens, cobertura e circulação. | Contagens e listas pela mesma consulta; reserva sem ingresso excluída; nota vigente preservada. | Teste dos cinco segundos por Ailton; cenário completo da demonstração. |
| Risco: matriz inerente/residual, efeito dos controles, decisão e referência do RIPD. | Mesma classificação do FORM 3; propostas fora da matriz; referência sem conteúdo; cores verificadas no navegador. | Comparar a matriz com o R01 da cópia de vistoria. |
| Correção: situações exclusivas, prazo original, prorrogações, prazo vigente e linha do tempo. | Primeira aprovação como origem do prazo; verificação recusada não encerra a ação; prazo vencido não inclui ação verificada/cancelada. | Percorrer A01 e conferir prorrogações existentes. |
| Operação: seis filas por papel, Registros distintos, participações, mediana e maior espera. | Ciências não contam; espera do DPO abre na confirmação conjunta ou pedido de cancelamento, fecha na manifestação; rodadas pareadas. | Conferir marcos com o histórico dos casos demonstrados. |
| Cobertura: Secretarias ativas, inclusive zero real; confirmação do FORM 1 e conclusão do FORM 2 em barras comparativas. | Escopo e quantidade consultados; participação externa separada no escopo permitido; sem percentual inventado. | Conferir os totais municipais e o filtro do Secretário. |
| Aprendizados: contexto, diretriz, limites, datas e identificadores. | Só a última versão verificada, conferida e autorizada; proposta nova não remove a versão autorizada. | Aprendizado da demonstração, após os atos autorizados. |
| Circulação simplificada: Secretarias × categorias estruturadas; instrumento formal declarado. | Leitura dos identificadores F1-10.2 e F2-8.1/8.2/8.7; sem interpretar texto livre; fonte indisponível não vira zero. | Categorias dos casos 1 e 3, quando os textos forem entregues. |
| Permissões e projeção: filtro não amplia acesso, nenhum nome de pessoa, manifestação ou evidência. | URL de outra Secretaria recusada; rotas GET sem gravação, transação somente leitura; POST recusado. | Navegação com Gabinete, DPO, Comitê, Secretário e AAL/ARP na nova cópia. |
| Interface comum, filtros preservados, listas, gráfico/tabela e aviso D11. | Sete páginas em 1366×768 e 390×768; sem rolagem horizontal da página; tabelas e matriz têm rolagem local. Alternância conferida no navegador. | Aceite de legibilidade e facilidade de navegação por Ailton. |

## Testes

| Grupo | Total | Aprovados | Falhas |
|---|---:|---:|---:|
| Base fixa e lotes anteriores ao Lote 12 | 252 | 250 | 2 antigas |
| Regressões do Lote 12 | 133 | 133 | 0 |
| Novos do dashboard | 38 | 38 | 0 |
| Total de testes distintos | 423 | 421 | 2 antigas |

Falhas antigas preservadas, sem relaxamento de expectativa:

- `test_unidade_isola_origens_e_reutiliza_anotacao`;
- `test_catalogo_local_indisponivel_preserva_preparacao[True]`.

A terceira falha histórica não se reproduziu. A base foi executada integralmente. Depois dos ajustes finais de apresentação, os testes do dashboard foram reexecutados; as oito verificações HTTP/visual foram repetidas após o acabamento da linha do tempo. Na rodada intermediária, dois testes do dashboard encontraram o template atualizado com o módulo anterior ainda carregado; a execução final com os arquivos alinhados passou. Nenhum teste existente foi alterado.

Execução somente no banco isolado terminado em `_teste`. Evidências locais no pacote `entrega-lgpd-lote13`: `regressao.xml`, `dashboard37.xml`, `cancelamento.xml`, `testes.xml` e `visual/medidas.json`. Capturas são de massa sintética de teste, não da cópia da 8013. A inspeção automatizada e visual não substitui a vistoria de Ailton.

## Arquivos e decisões

- `app/dashboard/fontes.py`: escopo, leitura autorizada e categorias estruturadas.
- `app/dashboard/consultas.py`: indicadores e respectivas listas; sem SQL de escrita.
- `app/dashboard/rotas.py`: rotas GET, transação somente leitura e apresentação.
- `app/paginas/dashboard.html`, `app/estaticos/dashboard.css` e `dashboard.js`: componentes compartilhados das sete telas.
- `app/main.py` e `app/paginas/central.html`: acesso ao dashboard conforme o perfil.
- `testes/test_dashboard.py`: cenários e recusas.
- Especificação final, SAD 10, padrão de interação e README atualizados.

Na mediana de uma fila, cada Registro usa a sua espera mais antiga ainda aberta, evitando dar peso extra a quem tem várias participações. O detalhe conserva as participações e seus marcos. Datas de prazo sem horário não são deslocadas pelo fuso. A linha do tempo compartilha a escala de datas entre ações e encerra somente com verificação aprovada ou cancelamento.

As consultas não criam competências, decisões, percentuais, comunicação de incidentes nem estado de elaboração do RIPD. Catálogos privados, Mestre, credenciais, cópias de banco e capturas permanecem fora dos commits. Não foram alterados Cartilha, palestra ou servidores em uso.

## Preparação da vistoria

A 8013 permanece no Lote 12-F, em pasta exclusiva. Para o dashboard, o pacote local prepara a porta 8014 com pasta exclusiva e commit fixado, catálogos copiados e nova base derivada da cópia da 8013. A criação depende da senha do administrador informada somente no PowerShell; os scripts não aplicam migração, não executam testes e não interrompem portas ocupadas.

1. Preparar a cópia com `preparar_8014.py`; depois iniciar com `abrir_8014.py`.
2. Entrar como Gabinete e verificar a Abertura em cinco segundos.
3. Abrir um número e conferir a lista que o compõe.
4. Em Risco, alternar inerente/residual e gráfico/tabela; comparar o R01.
5. Em Correção, conferir a A01, prazo, prorrogações e situação.
6. Em Operação, conferir que ciência não é pendência nem espera.
7. Em Cobertura, aplicar filtros e testar o Secretário.
8. Conferir Aprendizados e Circulação; não esperar dados ainda não registrados.

Os casos 1 e 3 não foram carregados: seus textos fictícios aprovados ainda não foram recebidos. Os demais casos permanecem somente no protótipo, conforme a especificação. A 8014 não deve ser tratada como ativada antes da criação da cópia e da abertura pelo comando preparado.
