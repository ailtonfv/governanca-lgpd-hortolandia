"""Copia a edição privada validada para uma NOVA entrega, sem iniciar servidor."""
from pathlib import Path
from hashlib import sha256
import shutil
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.ajudas_cartilha_form1 import ARQUIVO_CARTILHA, SHA256_CARTILHA


def preparar(origem, destino):
    origem, destino = Path(origem), Path(destino)
    relativo = Path('documentos_locais/cartilha') / ARQUIVO_CARTILHA
    arquivo = origem / relativo
    if not arquivo.is_file() or sha256(arquivo.read_bytes()).hexdigest() != SHA256_CARTILHA:
        raise ValueError('Cartilha da origem ausente ou diferente da edição aprovada.')
    alvo = destino / relativo
    if alvo.exists():
        if sha256(alvo.read_bytes()).hexdigest() != SHA256_CARTILHA:
            raise ValueError('Destino já tem outra Cartilha; não foi sobrescrita.')
    else:
        alvo.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(arquivo,alvo)
    from app import cartilha_local
    anterior = cartilha_local.CAMINHO_CARTILHA
    try:
        cartilha_local.CAMINHO_CARTILHA=alvo
        from app.ajudas_cartilha_form1 import topico_do_bloco
        secoes=cartilha_local.secoes_cartilha_disponiveis()
        if not all(topico_do_bloco(b,secoes) for b in range(1,15)):
            raise ValueError('A Cartilha não oferece os 14 destinos esperados.')
    finally:
        cartilha_local.CAMINHO_CARTILHA=anterior
    return alvo


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('origem');p.add_argument('destino')
    args=p.parse_args()
    preparar(args.origem,args.destino)
    print('Cartilha local conferida: hash aprovado e 14 destinos disponíveis. Nenhum servidor iniciado.')
