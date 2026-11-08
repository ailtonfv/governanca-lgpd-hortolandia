"""Rótulos de consulta; não modifica nem reinterpreta a origem histórica."""
from sqlalchemy import select

from app.modelos import Pessoa


ROTULOS = {
    "id": "Identificador preservado", "respostas": "Respostas",
    "resposta": "Resposta histórica", "respostas_inativas": "Respostas anteriores inativas",
    "complementos": "Complementos", "complementos_inativos": "Complementos anteriores inativos",
    "categoria": "Categoria do destinatário", "modalidade": "Modo de identificação",
    "unidade_id": "Código da unidade preservado na origem",
    "identificacao": "Identificação institucional", "cnpj": "CNPJ da entidade",
    "instrumento": "Instrumento pertinente", "classe_orgao_requisitante": "Classe do órgão requisitante",
    "hipotese_requisicao": "Hipótese da requisição", "meio_publicacao": "Meio de publicação",
    "natureza_destinatario": "Natureza do destinatário", "justificativa": "Justificativa",
    "motivo_desativacao": "Motivo da desativação", "motivo_inativacao": "Motivo da inativação",
    "desativada_na_versao": "Desativada na versão",
    "desativado_na_versao": "Desativado na versão", "valor": "Valor preservado", "motivo": "Motivo",
    "versao": "Versão", "versao_estrutura": "Estrutura histórica", "matriz": "Matriz da extensão",
    "adotada_por": "Adoção por", "papel": "Papel exercido", "adotada_em": "Data da adoção",
    "legado": "Respostas anteriores à adoção — não convertidas para os novos campos",
    "campos": "Perguntas anteriores", "campo_id": "Identificador da pergunta",
    "pergunta": "Enunciado histórico", "snapshot_id": "Identificador do snapshot anterior",
    "numero_snapshot": "Número do snapshot anterior", "lacre_snapshot": "Lacre anterior",
    "versao_rascunho": "Versão do rascunho", "rascunho_salvo_por": "Rascunho salvo por",
    "rascunho_salvo_em": "Data de salvamento do rascunho",
}
PAPEIS = {
    "APA_designante": "APA — Agente Público Autorizado (designação)",
    "preparador_demonstrativo": "Preparador autorizado do FORM 2",
    "ARP": "ARP — Agente Responsável pelo Preenchimento",
}
GRUPOS = (
    ("participantes", "Participantes institucionais — ocorrências do Bloco 3"),
    ("participantes_inativos", "Participantes anteriores inativos"),
    ("destinatarios_10_2_1", "10.2.1 — Destinatários registrados"),
    ("destinatarios_10_2_1_inativos", "10.2.1 — Destinatários anteriores inativos"),
    ("complementos", "Complementos das respostas"),
    ("complementos_inativos", "Complementos anteriores inativos"),
    ("respostas_inativas", "Respostas anteriores inativas"),
    ("extensao_medidas", "Extensão MEDIDAS — adoção e legado preservado"),
    ("extensao_guarda", "Extensão GUARDA — adoção e legado preservado"),
)


def apresentar_origem(origem):
    """Usa os enunciados do catálogo efetivo já validado por ler_origem."""
    rotulos = dict(ROTULOS)
    if not origem:
        return {"rotulos": rotulos, "grupos": []}
    rotulos.update({p["id"]: f'{p["id"]} — {p["pergunta"]}' for p in origem["perguntas"]})
    fonte = origem["conteudo"]
    return {"rotulos": rotulos, "grupos": [
        {"titulo": titulo, "valor": fonte[chave]} for chave, titulo in GRUPOS if chave in fonte
    ]}


def identificar_agentes(sessao, dados):
    """Resolve somente autores já presentes na consulta autorizada, sem ampliar acesso."""
    ids = {dados["pessoa"].id}
    preparacao, origem = dados.get("preparacao"), dados.get("origem")
    if preparacao:
        ids.update((preparacao.preparador_id, preparacao.salvo_por))
    if origem:
        ids.add(origem["snapshot"].preparado_por)
        ids.add(origem["canais"].get("confirmado_por_id"))
        for chave in ("extensao_medidas", "extensao_guarda"):
            extensao = origem["conteudo"].get(chave, {})
            ids.add(extensao.get("adotada_por"))
            ids.add(extensao.get("legado", {}).get("rascunho_salvo_por"))
    ids.update(ato.ator_id for ato in dados.get("historico", []))
    pessoas = sessao.scalars(select(Pessoa).where(Pessoa.id.in_(ids - {None})))
    return {p.id: f"{p.matricula} — {p.nome}" for p in pessoas}
