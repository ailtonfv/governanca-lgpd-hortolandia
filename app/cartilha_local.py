"""Leitura local da edição conferida; DOCX fora do Git e de /estaticos.

Não executa macros, busca recursos externos ou persiste dados do formulário.
"""
import base64
import hashlib
from functools import lru_cache
from io import BytesIO
from ipaddress import ip_address
from pathlib import Path, PurePosixPath
import re
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from app.ajudas_cartilha_form1 import ARQUIVO_CARTILHA, SECOES_CARTILHA, SHA256_CARTILHA

CAMINHO_CARTILHA = Path(__file__).resolve().parent.parent / "documentos_locais" / "cartilha" / ARQUIVO_CARTILHA
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}


def acesso_local_cartilha(request):
    """Apenas loopback; não confiar em cabeçalhos fornecidos pelo cliente."""
    try:
        return bool(request.client and ip_address(request.client.host).is_loopback)
    except ValueError:
        return False


def _texto(elemento):
    return "".join(
        (item.text or "") if item.tag == f"{{{NS['w']}}}t" else "\n"
        for item in elemento.iter()
        if item.tag in {f"{{{NS['w']}}}t", f"{{{NS['w']}}}br", f"{{{NS['w']}}}tab"}
    ).strip()


def _nivel(paragrafo):
    estilo = paragrafo.find("w:pPr/w:pStyle", NS)
    nome = "" if estilo is None else estilo.get(f"{{{NS['w']}}}val", "")
    numero = re.fullmatch(r"(?:Ttulo|Heading)([1-6])", nome)
    return int(numero[1]) if numero else None


@lru_cache(maxsize=2)
def _ler_edicao(caminho, mtime_ns, tamanho):
    dados = Path(caminho).read_bytes()
    if hashlib.sha256(dados).hexdigest() != SHA256_CARTILHA:
        return {}  # Outra edição não pode receber os destinos da REV30.13.
    with ZipFile(BytesIO(dados)) as arquivo:
        documento = ET.fromstring(arquivo.read("word/document.xml"))
        relacoes = ET.fromstring(arquivo.read("word/_rels/document.xml.rels"))
        imagens = {}
        for relacao in relacoes:
            alvo = relacao.get("Target", "")
            caminho_imagem = PurePosixPath("word") / alvo
            if (relacao.get("TargetMode") != "External"
                    and alvo.startswith("media/") and ".." not in caminho_imagem.parts
                    and caminho_imagem.suffix.lower() in {".png", ".jpg", ".jpeg"}):
                mime = "image/png" if caminho_imagem.suffix.lower() == ".png" else "image/jpeg"
                imagens[relacao.get("Id")] = "data:" + mime + ";base64," + base64.b64encode(
                    arquivo.read(str(caminho_imagem))
                ).decode("ascii")

        def blocos(elemento):
            if elemento.tag == f"{{{NS['w']}}}tbl":
                linhas = []
                for linha in elemento.findall("w:tr", NS):
                    celulas = []
                    for celula in linha.findall("w:tc", NS):
                        span = celula.find("w:tcPr/w:gridSpan", NS)
                        celulas.append({
                            "blocos": [b for filho in celula for b in blocos(filho)],
                            "colunas": int(span.get(f"{{{NS['w']}}}val", "1")) if span is not None else 1,
                        })
                    linhas.append(celulas)
                return [{"tipo": "tabela", "linhas": linhas}]
            if elemento.tag != f"{{{NS['w']}}}p":
                return []
            resultado = []
            texto = _texto(elemento)
            if texto:
                resultado.append({"tipo": "titulo" if _nivel(elemento) else "texto", "texto": texto})
            for desenho in elemento.findall(".//w:drawing", NS):
                descricao = desenho.find(".//wp:docPr", NS)
                for imagem in desenho.findall(".//a:blip", NS):
                    src = imagens.get(imagem.get(f"{{{NS['r']}}}embed"))
                    if src:
                        resultado.append({"tipo": "imagem", "src": src,
                                          "alt": (descricao.get("descr") if descricao is not None else None)
                                          or "Ilustração da seção da Cartilha"})
            return resultado

        secoes, atual = {}, None
        por_titulo = {titulo: chave for chave, titulo in SECOES_CARTILHA.items()}
        for elemento in documento.find("w:body", NS):
            nivel = _nivel(elemento) if elemento.tag == f"{{{NS['w']}}}p" else None
            if nivel is not None and nivel <= 2:
                atual = por_titulo.get(_texto(elemento))
                if atual:
                    secoes[atual] = []
                continue
            if atual:
                secoes[atual].extend(blocos(elemento))
        return {chave: conteudo for chave, conteudo in secoes.items() if conteudo}


def secoes_cartilha_disponiveis():
    """Ajuda permanece; link só existe para seção efetivamente disponível."""
    try:
        estado = CAMINHO_CARTILHA.stat()
        return _ler_edicao(str(CAMINHO_CARTILHA), estado.st_mtime_ns, estado.st_size)
    except (OSError, BadZipFile, ET.ParseError, KeyError, ValueError):
        return {}
