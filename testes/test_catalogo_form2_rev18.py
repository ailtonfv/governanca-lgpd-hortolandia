"""Conferência documental. Executável via unittest, sem fixtures ou conexão SQL."""

import csv
import hashlib
import json
import os
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from app import catalogo_form2_rev18 as leitor


MATRIZ = (
    Path(__file__).resolve().parents[1] / "docs" / "planejamento"
    / "GOV_FORMS_REV18_02" / "correspondencia_v1.csv"
)


class TestCatalogoForm2(unittest.TestCase):
    def setUp(self):
        self.catalogo = leitor.carregar_catalogo()
        self.blocos = self.catalogo["blocos"]
        self.itens = {item["id"]: item for bloco in self.blocos for item in bloco["itens"]}

    def test_etapas_blocos_e_ordem_editorial(self):
        etapas = self.catalogo["etapas"]
        self.assertEqual([e["numero"] for e in etapas], [1, 2, 3, 4])
        self.assertEqual([e["blocos"] for e in etapas],
                         [[1, 2, 3, 4], [5, 6, 7, 13], [8, 9, 10, 11, 12], [14]])
        self.assertEqual([len(b["itens"]) for b in self.blocos],
                         [8, 16, 15, 8, 11, 11, 26, 13, 24, 35, 25, 27, 13, 18])
        for bloco in self.blocos:
            for item in bloco["itens"]:
                self.assertRegex(item["id"], rf"^F2-{bloco['numero']}[A-Z]?\.\d+(?:\.\d+)*$")

    def test_correspondencia_dos_250_itens_com_a_matriz(self):
        with MATRIZ.open(encoding="utf-8-sig", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo, delimiter=";"))
        f1 = {r["rev18"] for r in linhas if r["form"] == "F1"}
        f1_historico = {r["rev17"] for r in linhas if r["form"] == "F1" and r["rev17"]}
        f2 = sorted((r for r in linhas if r["form"] == "F2"), key=lambda r: int(r["paragrafo_rev18"]))
        self.assertEqual(list(self.itens), [r["rev18"] for r in f2])
        for r in f2:
            item = self.itens[r["rev18"]]
            with self.subTest(id=item["id"]):
                self.assertEqual(item["paragrafo"], int(r["paragrafo_rev18"]))
                self.assertEqual(item["enunciado"], r["enunciado_rev18"])
                self.assertEqual(item["rev17"], r["rev17"] or None)
                self.assertEqual(item["correspondencia"], r["correspondencia"])
                self.assertEqual(item.get("referencias_rev18", []), r["referencias_rev18"].split())
                self.assertTrue(set(item.get("referencias_rev18", ())) <= f1)
                self.assertTrue(set(item.get("subsidios_form1_rev13", ())) <= f1_historico)

    def test_heranca_acrescimos_e_ramos(self):
        antigos = [i["rev17"] for i in self.itens.values() if i["rev17"]]
        self.assertEqual(len(antigos), 245)
        self.assertEqual(len(set(antigos)), 245)
        self.assertEqual({k for k, v in self.itens.items() if not v["rev17"]},
                         {"F2-2.9", "F2-2.9.1", "F2-2.9.2", "F2-2.9.3", "F2-14.3.1"})
        self.assertEqual({k for k, v in self.itens.items() if v["correspondencia"] == "alterado"},
                         {"F2-9.7.1", "F2-14.2", "F2-14.3"})
        ramos = Counter(k.split(".")[0] for k in self.itens if re.search(r"[A-Z]\.", k))
        self.assertEqual(ramos, {"F2-9W": 11, "F2-11S": 8, "F2-12A": 11})

    def test_origem_do_dado_e_papel_do_subsidio(self):
        self.assertEqual(self.itens["F2-1.1"]["natureza"], "dado_registro")
        self.assertEqual(self.itens["F2-1.1"]["contexto_registro"], "identificador_lgpd")
        self.assertEqual(self.itens["F2-1.2"]["natureza"], "pergunta_form2")
        self.assertEqual(self.itens["F2-1.2"]["contexto_registro"], "secretaria_responsavel")
        self.assertEqual(self.itens["F2-8.1"]["natureza"], "fato_form1")
        self.assertEqual(self.itens["F2-8.1"]["subsidios_form1_rev13"], ["F1-10.1"])
        self.assertEqual(self.itens["F2-2.9"]["natureza"], "pergunta_form2")
        self.assertEqual(self.itens["F2-2.9"]["referencias_rev18"], ["F1-12.1"])
        self.assertEqual(self.itens["F2-9.7.1"]["referencias_rev18"], ["F1-11.2.5"])

    def test_guarda_preserva_os_dois_gatilhos_distintos(self):
        for id_, origem in (("2.9.1", "2.9"), ("2.9.3", "2.9.2")):
            self.assertEqual(self.itens["F2-" + id_]["condicao_documental"],
                             {"origem": "F2-" + origem, "resposta": "Sim"})
        self.assertNotIn("condicao_documental", self.itens["F2-2.9.2"])
        self.assertEqual(self.itens["F2-2.9.1"]["escolha_documental"]["modo"], "multipla")
        self.assertIn("referência documental", self.itens["F2-2.9.1"]["orientacao"])
        self.assertNotIn("escolha_documental", self.itens["F2-1.3"])

    def test_leitor_recusa_edicao_inconsistente(self):
        for falha in ("duplicado", "ordem", "enunciado", "etapa"):
            with self.subTest(falha=falha), tempfile.TemporaryDirectory() as pasta:
                copia = leitor.carregar_catalogo()
                itens = copia["blocos"][0]["itens"]
                if falha == "duplicado":
                    itens[1]["id"] = itens[0]["id"]
                elif falha == "ordem":
                    itens[0], itens[1] = itens[1], itens[0]
                elif falha == "enunciado":
                    itens[0]["enunciado"] += "!"
                else:
                    copia["etapas"][0]["blocos"].remove(1)
                caminho = Path(pasta) / "catalogo.json"
                caminho.write_text(json.dumps(copia), encoding="utf-8")
                with patch.object(leitor, "ARQUIVO", caminho), self.assertRaises(ValueError):
                    leitor.carregar_catalogo()

    @unittest.skipUnless(os.environ.get("MESTRE_REV18_DOCX"), "Indique a cópia local do Mestre para o cotejo.")
    def test_cotejo_integral_com_o_docx_da_edicao(self):
        path = Path(os.environ["MESTRE_REV18_DOCX"])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         self.catalogo["fontes"]["mestre"]["sha256"])
        w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        with ZipFile(path) as docx:
            corpo = ET.fromstring(docx.read("word/document.xml")).find(w + "body")
        paragrafos = [""] + ["".join(p.itertext()).strip() for p in corpo.findall(w + "p")]
        inicio = paragrafos.index("FORM 2 — VALIDAÇÃO JURÍDICA E INSTITUCIONAL")
        fim = paragrafos.index("FORM 3 — RISCOS, LACUNAS E CONTROLES", inicio)
        perguntas = {}
        escolhas = {}
        for n in range(inicio + 1, fim):
            texto = paragrafos[n]
            pergunta = re.fullmatch(r"(\d+[A-Z]?(?:\.\d+)+) — (.+)", texto)
            if pergunta:
                id_ = "F2-" + pergunta[1]
                self.assertNotIn(id_, perguntas)
                perguntas[id_] = (n, pergunta[2])
            elif texto.startswith(("○", "☐")):
                self.assertEqual(perguntas[id_][0], n - 1)
                escolhas[id_] = {
                    "modo": "unica" if texto[0] == "○" else "multipla",
                    "alternativas": [s.strip() for s in texto.split(texto[0])[1:]],
                }
        self.assertEqual(perguntas, {k: (i["paragrafo"], i["enunciado"]) for k, i in self.itens.items()})
        self.assertEqual(escolhas, {k: i["escolha_documental"] for k, i in self.itens.items()
                                    if "escolha_documental" in i})
