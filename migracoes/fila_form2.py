"""Fila demonstrativa REV22. Aplicação aditiva sobre a base existente."""
from app.modelos import ParticipacaoForm2, AvisoDpo, ResumoDpo, ComplementoForm2

def aplicar(sessao):
    for modelo in (ParticipacaoForm2, AvisoDpo, ResumoDpo, ComplementoForm2):
        modelo.__table__.create(sessao.connection(), checkfirst=True)


def reverter(sessao):
    """Reverte somente a fila vazia; participação/aviso/histórico impedem perda."""
    from migracoes.reversao_segura import reverter_tabelas_vazias
    reverter_tabelas_vazias(sessao, [m.__tablename__ for m in
        (ComplementoForm2, AvisoDpo, ResumoDpo, ParticipacaoForm2)])
