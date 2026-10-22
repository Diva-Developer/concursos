# Atualização completa do radar de concursos

Você está na pasta do atualizador. Objetivo: deixar `dados/concursos.json` com o retrato mais atual dos concursos de interesse e regerar a página. Hoje é a data do sistema.

## Contexto
- Público: pessoa em João Pessoa/PB. Recorte: só Paraíba (foco principal) e Pernambuco, mais federais com vaga ou prova em PB ou PE. Nada de outros estados.
- Horizonte: inscrições abertas agora e previstas para os próximos meses e anos (até uns 2 anos).
- Áreas: segurança pública (polícias, guardas, penal, PRF, PF), tecnologia (TI, segurança da informação), fisioterapia, e administrativos de grande porte (tribunais, bancos, universidades, prefeituras de capital, CNU).
- `dados/varredura.json` já tem os concursos abertos achados automaticamente no PCI Concursos. Não copie esses para a curadoria, a não ser que você tenha detalhe a mais (banca, estrutura da prova); nesse caso use `chave_pci` com um trecho do nome do órgão para evitar duplicata.
- Chaves válidas de `perfis` estão em `scripts/perfis.py` (seg_sup, seg_med, ti_sup, ti_med, fis, banc, adm_med, geral_sup). O valor é o nome do cargo.

## Passos
1. Leia `dados/concursos.json`, `scripts/perfis.py` (só os nomes das chaves) e a lista de órgãos em `dados/varredura.json`.
2. Para cada concurso da curadoria, pesquise a situação atual (edital, banca, datas, vagas, salário). Atualize `st` (aberto, iminente, previsto, encerrado), `prazo` e `prova` (AAAA-MM-DD ou null), `banca`, `vagas`, `salario`, `insc`, `obs`, `link_nome`, `link_url` e, se o edital trouxer, `estrutura` (formato e número de questões). Para quem não está aberto, preencha `previsao` (AAAA-MM do mês em que a inscrição deve abrir, sua melhor estimativa pelas notícias; null se não houver nenhum sinal) e `previsao_txt` (de onde vem a estimativa, em uma frase).
3. Concurso cuja prova já passou: `st` = "encerrado". Remova os encerrados há mais de 60 dias.
4. Procure concursos novos do recorte, começando pela Paraíba (estado, João Pessoa, Campina Grande, tribunais, universidades, conselhos) (abertos, com banca contratada ou autorizados) que ainda não estejam na curadoria nem na varredura e acrescente no mesmo formato, com `uf` (PB, PE ou BR) e `perfis`.
5. Prefira fonte oficial (edital, site da banca, Diário Oficial). Quando só houver blog de cursinho, diga isso em `obs`. Não invente número: se não achar, use "Conferir no edital" ou "—".
6. Atualize `atualizado_em` com a data de hoje. Mantenha o JSON válido, em UTF-8, com acentos.
7. Rode `python scripts/gerar_plano.py` e confira que terminou sem erro.
8. Escreva em `dados/ultima_atualizacao.txt` um resumo curto: o que mudou, o que entrou, o que saiu e o que ficou incerto.

Não altere outros arquivos.
