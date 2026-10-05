# sci-egressos-base

Mapeamento dos egressos das categorias de base de sete clubes brasileiros — Internacional, Flamengo, Palmeiras, São Paulo, Corinthians, Santos e Fluminense — para o pilar de recrutamento do Projeto Futebol do Inter.

O repositório contém a **tabela curada** (227 jogadores, dados do Sofascore + curadoria manual) e um **painel estático** que só filtra, ordena e exibe essa tabela. Scores, pilares e classes **já vêm calculados**; o painel não recalcula nada.

> **Triagem estatística, não recomendação.**

## Estrutura

```
├── config/qualidades.json      # regras das tags de qualidade/ponto fraco (versão q1)
├── data/                       # FONTE dos dados
│   ├── jogadores.json          # 1 registro por jogador (lido pelo painel)
│   ├── jogadores.csv           # mesma tabela em CSV
│   ├── curadoria_manual.csv    # vínculo, dono, disponibilidade (só cor), alerta de altura
│   └── meta.json               # versão, data de referência, contagem por classe, limitações
├── docs/                       # publicado pelo GitHub Pages
│   ├── index.html              # painel: HTML único, JS puro, sem build
│   └── data/                   # CÓPIA de data/jogadores.json e data/meta.json
├── scripts/sync_docs.py        # copia data/*.json → docs/data/ e falha se divergir
└── tests/
    ├── test_dados.py           # critérios de aceite dos dados + regras de segurança
    └── painel.test.mjs         # teste do painel em navegador (Playwright)
```

O GitHub Pages serve apenas `/docs`, por isso existe a cópia em `docs/data/`. **Nunca edite `docs/data/` à mão**: edite `data/` e rode o script de sincronização.

## Classes

| Classe | Significado |
|---|---|
| A | Alvo prioritário |
| B | Imposição |
| C | Qualidade técnica |
| D | Monitorar (amostra baixa) |
| E | Base |
| SD | Sem dados suficientes (selo cinza) |
| DESC | Desconsiderado |

Distribuição na versão v2 [Verificado — `data/meta.json`]: A 13 · B 6 · C 8 · D 43 · E 139 · SD 16 · DESC 2 (total 227).

## Painel

Depois de publicado no GitHub Pages, o painel carrega os dados sozinho. Aberto direto do disco (duplo clique, `file://`), o navegador bloqueia a leitura automática do JSON: o painel avisa e oferece um botão para escolher `docs/data/jogadores.json` (e `meta.json`) manualmente. Para testar localmente com carga automática, sirva a pasta por HTTP:

```bash
python3 -m http.server -d docs 8000
# http://localhost:8000
```

- Chips de classe ligáveis, com contagem (início: A, B, C e D ligados).
- Filtros: posição, clube formador (formação compartilhada, como "Flamengo / Internacional", aparece nos dois), Tier, janela contratual, faixa de valor, vínculo e busca por nome (ignora acentos).
- Faixas de valor: "até € 500 mil"; "até € 1,5 mi" (inclui a faixa anterior); "acima de € 1,5 mi". Jogadores sem valor ficam fora quando uma faixa é escolhida.
- Ordenação padrão: minutos 2023–25, do maior para o menor; alternativas: BSC, imposição, rendimento, altura, valor (com inversão de sentido). Jogadores sem o dado vão sempre para o fim.
- Se as contagens de `jogadores.json` divergirem de `meta.json`, o painel mostra um aviso.

## Como atualizar os dados

1. Substitua os arquivos em `data/` (`jogadores.json`, `jogadores.csv`, `meta.json`, `curadoria_manual.csv`).
2. Rode a sincronização, que valida a fonte (contagem por classe = `meta.json`, ids únicos, `disponibilidade` só com cor) e copia para `docs/data/`:
   ```bash
   python3 scripts/sync_docs.py          # valida + copia + confere
   python3 scripts/sync_docs.py --check  # só confere (útil antes do commit)
   ```
3. Rode os testes:
   ```bash
   python3 -m unittest discover -s tests -v
   node tests/painel.test.mjs            # requer o pacote playwright e um Chromium
   ```
   Os números esperados em `tests/test_dados.py` são da versão v2; atualize-os junto com uma nova versão dos dados.
4. Faça o commit de `data/` e `docs/data/` juntos.

### Regras para o repositório público

- Não versionar CSVs brutos do Sofascore, planilhas `.xlsx`, notas privadas, tokens, `.env` nem caminhos locais (o `.gitignore` cobre os padrões conhecidos).
- `disponibilidade` guarda **só a cor** (`verde`, `amarelo`, `vermelho`, `nao_verificado`). Nenhum detalhe clínico em nenhum arquivo.
- Não incluir dados de representação/intermediação dos atletas.

## Limitações

- **Percentis comparam os egressos entre si**, por posição, e não o mercado. Um percentil alto significa "acima dos outros egressos da mesma posição".
- **Estatísticas de métrica vêm da temporada exibida no perfil do Sofascore** (algumas com poucos jogos); **minutos e gols 2023–25 vêm dos totais da Carreira**. As duas janelas não coincidem.
- **Fator de nível por Tier é calibração inicial** [Especulação]; ainda não foi validado contra desempenho posterior.
- **Vínculo e disponibilidade vêm de curadoria manual**, não do Sofascore (`data/curadoria_manual.csv`); podem ficar desatualizados entre coletas.
- **Sem dados de salário.** Valores de mercado são estimativas do Sofascore.
- **Nota média do Sofascore não capturada**; o pilar de avaliação usa atributos e Time da semana.
- A **imposição** mede altura, duelos aéreos, disputas, velocidade e gols de cabeça em relação aos egressos da mesma posição; não mede território nem aspecto mental.
- 140 dos 227 jogadores têm amostra **Baixa** [Verificado — `data/jogadores.json`]; no painel, as qualidades desses jogadores aparecem esmaecidas.
- Fora de escopo nesta etapa: pipeline Python de coleta (próxima etapa, com teste de paridade contra esta tabela) e dados da América do Sul.
