# concursos

Radar de concursos da Paraíba e de Pernambuco, com plano de estudos. É um app web que instala no celular e funciona sem internet.

**App:** https://diva-developer.github.io/concursos/

## Como funciona

- Todo dia às 6h um workflow do GitHub Actions roda `scripts/raspar_pci.py`, que varre o PCI Concursos atrás de editais abertos e previstos para PB e PE.
- Para cada concurso o script abre a notícia e lê banca, data da prova e cargos. Usa só a biblioteca padrão do Python.
- O resultado vai para `dados/` e o `index.html` é gerado de novo e publicado no GitHub Pages.
- No app, os concursos aparecem agrupados por prazo: inscrições abertas, próximos 3 meses, de 3 a 6 meses.
- O botão "Atualizar" baixa a última versão. Com um token do GitHub cadastrado no app, ele dispara a varredura na hora.

Existe ainda uma atualização completa opcional usando a API do Claude, ligada pela secret `ANTHROPIC_API_KEY`.

## Estrutura

```
index.html        o app (gerado, não editar na mão)
sw.js             service worker, pra funcionar offline
dados/            concursos.json e varredura.json
scripts/          raspagem e geração do plano de estudos
```

O passo a passo de publicação e de instalação no iPhone está em `LEIA-ME.txt`.
