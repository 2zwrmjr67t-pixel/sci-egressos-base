"""Critérios de aceite sobre os dados e regras de segurança do repositório.

Rodar: python3 -m unittest discover -s tests -v
"""
import json
import re
import subprocess
import unittest
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
J = json.loads((RAIZ / "docs/data/jogadores.json").read_text(encoding="utf-8"))
META = json.loads((RAIZ / "docs/data/meta.json").read_text(encoding="utf-8"))


def por_nome(nome):
    achados = [j for j in J if j["nome"] == nome]
    assert len(achados) == 1, f"{nome}: {len(achados)} registros"
    return achados[0]


class TestDados(unittest.TestCase):
    def test_total_e_classes(self):
        self.assertEqual(len(J), 227)
        esperado = {"A": 13, "B": 6, "C": 8, "D": 43, "E": 139, "SD": 16, "DESC": 2}
        self.assertEqual(dict(Counter(j["classe"] for j in J)), esperado)
        self.assertEqual(META["classes"], esperado)

    def test_casos(self):
        m = por_nome("Micael")
        self.assertEqual((m["classe"], m["vinculo"], m["dono"]), ("A", "emprestimo", "Palmeiras"))
        c = por_nome("Cipriano")
        self.assertEqual((c["classe"], c["vinculo"], c["dono"]), ("B", "emprestimo", "APOEL"))
        self.assertEqual(por_nome("Kevyson")["disponibilidade"], "vermelho")
        self.assertTrue(por_nome("Felipe Andrade")["alerta_altura"])

    def test_ordenacao_padrao(self):
        topo = max(J, key=lambda j: j["min_3a"] or -1)
        self.assertEqual((topo["nome"], topo["min_3a"]), ("Lucas Piton", 13278))

    def test_disponibilidade_so_cor(self):
        validas = {"verde", "amarelo", "vermelho", "nao_verificado"}
        self.assertTrue(all(j["disponibilidade"] in validas for j in J))

    def test_copias_identicas(self):
        for nome in ("jogadores.json", "meta.json"):
            self.assertEqual((RAIZ / "data" / nome).read_bytes(), (RAIZ / "docs/data" / nome).read_bytes(), nome)


class TestRepositorio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True)
        cls.arquivos = [f for f in out.stdout.splitlines() if f]

    def test_sem_arquivos_proibidos(self):
        proibidos = [f for f in self.arquivos
                     if f.lower().endswith(".xlsx")
                     or "sofascore_consolidado" in f.lower()
                     or Path(f).name.startswith("PROMPT_")
                     or f.endswith(".env") or "notas_privadas" in f]
        self.assertEqual(proibidos, [])

    def test_sem_termo_proibido_nem_caminho_local(self):
        termo = "agen" + "te"  # montado para este teste não acusar a si próprio
        padrao_caminho = re.compile(r"[A-Za-z]:\\\\?Users\\\\?", re.I)
        achados = []
        for f in self.arquivos:
            p = RAIZ / f
            if not p.is_file():
                continue
            try:
                txt = p.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue
            if termo in txt.lower():
                achados.append(f"{f}: '{termo}'")
            if padrao_caminho.search(txt):
                achados.append(f"{f}: caminho local")
        self.assertEqual(achados, [])


if __name__ == "__main__":
    unittest.main()
