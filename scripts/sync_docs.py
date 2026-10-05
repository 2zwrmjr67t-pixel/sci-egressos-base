#!/usr/bin/env python3
"""Sincroniza a cópia publicada dos dados (docs/data/) com a fonte (data/).

O GitHub Pages serve apenas a pasta docs/, por isso jogadores.json e meta.json
existem em duas cópias. Este script:

1. valida a fonte (227 registros, ids únicos, contagens por classe iguais às
   de meta.json, disponibilidade só com cores, sem coluna proibida);
2. copia data/*.json para docs/data/;
3. confere byte a byte que as duas cópias ficaram idênticas.

Uso:
    python3 scripts/sync_docs.py           # valida, copia e confere
    python3 scripts/sync_docs.py --check   # só confere; não escreve nada

Sai com código 1 se houver divergência ou dado inválido.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "data"
DESTINO = RAIZ / "docs" / "data"
ARQUIVOS = ("jogadores.json", "meta.json")

CLASSES_VALIDAS = {"A", "B", "C", "D", "E", "SD", "DESC"}
DISPONIBILIDADE_VALIDA = {"verde", "amarelo", "vermelho", "nao_verificado"}
CAMPOS_PROIBIDOS = {"agente", "agent"}


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def valida_fonte() -> list[str]:
    erros: list[str] = []
    jogadores = json.loads((ORIGEM / "jogadores.json").read_text(encoding="utf-8"))
    meta = json.loads((ORIGEM / "meta.json").read_text(encoding="utf-8"))

    if not isinstance(jogadores, list):
        return ["jogadores.json não é uma lista"]

    if meta.get("n_jogadores") != len(jogadores):
        erros.append(f"n_jogadores em meta.json ({meta.get('n_jogadores')}) != registros ({len(jogadores)})")

    ids = Counter(j.get("id") for j in jogadores)
    repetidos = [i for i, n in ids.items() if n > 1]
    if repetidos:
        erros.append(f"ids repetidos: {repetidos}")

    contagem = Counter(j.get("classe") for j in jogadores)
    invalidas = set(contagem) - CLASSES_VALIDAS
    if invalidas:
        erros.append(f"classes inválidas: {sorted(invalidas)}")
    if dict(contagem) != meta.get("classes", {}):
        erros.append(f"contagem por classe {dict(contagem)} != meta.json {meta.get('classes')}")

    for j in jogadores:
        if j.get("disponibilidade") not in DISPONIBILIDADE_VALIDA:
            erros.append(f"{j.get('nome')}: disponibilidade fora do padrão de cores: {j.get('disponibilidade')!r}")
        proibidos = {k for k in j if k.lower() in CAMPOS_PROIBIDOS}
        if proibidos:
            erros.append(f"{j.get('nome')}: campo proibido {sorted(proibidos)}")
    return erros


def divergencias() -> list[str]:
    out = []
    for nome in ARQUIVOS:
        a, b = ORIGEM / nome, DESTINO / nome
        if not b.exists():
            out.append(f"{b.relative_to(RAIZ)} não existe")
        elif sha256(a) != sha256(b):
            out.append(f"{b.relative_to(RAIZ)} difere de {a.relative_to(RAIZ)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="só confere, sem copiar")
    args = ap.parse_args()

    erros = valida_fonte()
    if erros:
        print("ERRO na fonte data/:", *erros, sep="\n  - ")
        return 1

    if not args.check:
        DESTINO.mkdir(parents=True, exist_ok=True)
        for nome in ARQUIVOS:
            shutil.copyfile(ORIGEM / nome, DESTINO / nome)

    dif = divergencias()
    if dif:
        print("DIVERGÊNCIA entre data/ e docs/data/:", *dif, sep="\n  - ")
        if args.check:
            print("Rode: python3 scripts/sync_docs.py")
        return 1

    for nome in ARQUIVOS:
        print(f"ok  {nome}  sha256={sha256(ORIGEM / nome)[:12]}")
    print("docs/data/ idêntico a data/." + (" (somente conferência)" if args.check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
