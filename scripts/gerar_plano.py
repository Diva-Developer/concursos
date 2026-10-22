"""Gera saida/Concursos_Nordeste_Plano.html a partir de dados/*.json + perfis.py.

Site de uma página: régua de 24 meses com quando abrem as inscrições, filtros (localidade com foco
na Paraíba, área, quando, escolaridade, salário) e uma linha do tempo de cartões. Cada cartão
fechado mostra banca, cargo e data; aberto, traz abas Vaga, Banca e Plano (plano por cargo, com
datas até a prova). Filtros e abas funcionam em CSS puro (:has); o JS só acrescenta busca,
banca, clique no mês, ordenação, contagem e salvar marcações.

Uso: python gerar_plano.py [arquivo_saida] [--app]   (padrão: ../saida/Concursos_Nordeste_Plano.html)
     --app  versão instalável (PWA): manifesto, ícones, botão Atualizar e modo offline.
Sempre grava também app.json ao lado da página: os mesmos dados para o app SwiftUI.
"""
import hashlib
import html
import unicodedata
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from perfis import AREAS, BANCA_PADRAO, BANCAS, F, PERFIS  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
APP = "--app" in sys.argv
SAIDA = Path(ARGS[0]) if ARGS else BASE / "saida" / "Concursos_Nordeste_Plano.html"
HOJE = date.today()
INICIO = HOJE + timedelta(days=(7 - HOJE.weekday()) % 7 or 7)  # próxima segunda-feira
SEM_PADRAO = {"aberto": 8, "iminente": 16, "previsto": 16}     # semanas de plano quando a prova não tem data
STATUS = {"aberto": "Inscrições abertas", "iminente": "Edital iminente", "previsto": "Previsto"}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
GRUPOS = [("agora", "Inscrições abertas", "Corra: o prazo está correndo"),
          ("3", "Próximos 3 meses", "Edital esperado até {m3}"),
          ("6", "Em 3 a 6 meses", "De {m3} a {m6}"),
          ("12", "Em 6 meses a 1 ano", "De {m6} a {m12}"),
          ("mais", "Daqui a mais de um ano", "Depois de {m12}: dá para estudar com calma"),
          ("sem", "Sem data prevista", "Autorização ou orçamento ainda em aberto")]
e = html.escape


def _d(x):
    return date.fromisoformat(x) if x else None


def fdata(d, ano=False):
    return f"{d.day:02d}/{MESES[d.month - 1]}" + (f"/{d.year}" if ano else "")


def fmes(ym):
    a, m = map(int, ym.split("-"))
    return f"{MESES[m - 1]}/{a}"


def num(x):
    return f"{x:.1f}".replace(".", ",").replace(",0", "")


def meses_ate(ym):
    a, m = map(int, ym.split("-"))
    return (a - HOJE.year) * 12 + m - HOJE.month


def mes_mais(n):
    a, m = divmod(HOJE.month - 1 + n, 12)
    return f"{HOJE.year + a}-{m + 1:02d}"


def salario_max(t):
    vals = []
    for v, mil in re.findall(r"R\$\s*([\d.]+(?:,\d+)?)\s*(mil)?", t or ""):
        x = float(v.replace(".", "").replace(",", "."))
        vals.append(x * 1000 if mil else x)
    return max(vals) if vals else 0


# ---------- dados ----------
cur = json.loads((BASE / "dados" / "concursos.json").read_text(encoding="utf-8"))
var_arq = BASE / "dados" / "varredura.json"
var = json.loads(var_arq.read_text(encoding="utf-8")) if var_arq.exists() else {"itens": [], "erros": [], "gerado_em": None}

ITENS = []
for c in cur["concursos"]:
    if c["st"] == "encerrado":
        continue
    ITENS.append(dict(c, prazo=_d(c.get("prazo")), prova=_d(c.get("prova")), fonte="curadoria",
                      links=[(c["link_nome"], c["link_url"])]))
chaves = [c["chave_pci"].lower() for c in cur["concursos"] if c.get("chave_pci")]
for v in var["itens"]:
    if any(ch in f'{v["orgao"]} {v["titulo"]}'.lower() for ch in chaves):
        continue  # já está na curadoria, com mais detalhe
    m = re.match(r"(.*?vagas?)\s*(até.*)?$", v["vagas"])
    ITENS.append(dict(
        nome=v["orgao"], uf=v["uf"], st=v.get("st", "aberto"), perfis=v["perfis"], banca=v.get("banca") or "Banca a conferir",
        nivel=v["nivel"] or "Conferir no edital", vagas=(m.group(1) if m else v["vagas"]) or "Conferir no edital",
        salario=(m.group(2) if m and m.group(2) else "Conferir no edital"),
        insc=v["prazo_txt"] or ("Sem edital" if v.get("st") == "previsto" else "Conferir"),
        prazo=_d(v["prazo"]), prova=_d(v.get("prova")), previsao=v.get("previsao"), previsao_txt=v.get("previsao_txt"),
        obs=v["titulo"] if v["titulo"] != v["orgao"] else "Notícia lida automaticamente no PCI Concursos.",
        fonte="varredura", novo=v.get("novo"), links=[("Notícia e link do edital (PCI)", v["url"])]))
ITENS = [i for i in ITENS if not (i["st"] == "aberto" and i["prazo"] and i["prazo"] < HOJE)]


def periodo(i):
    """Grupo da linha do tempo + mês da inscrição (AAAA-MM) para a régua."""
    if i["st"] == "aberto":
        return "agora", HOJE.strftime("%Y-%m")
    p = i.get("previsao")
    if not p:
        return "sem", None
    n = meses_ate(p)
    return ("3" if n <= 3 else "6" if n <= 6 else "12" if n <= 12 else "mais"), max(p, HOJE.strftime("%Y-%m"))


ORD = {g: n for n, (g, _, _) in enumerate(GRUPOS)}
def cidade(i):
    """Cidade da vaga: nome da prefeitura/câmara, campo 'cidade' da curadoria, ou abrangência estadual/federal."""
    if i.get("cidade"):
        return i["cidade"]
    m = re.match(r"(?:Prefeitura|Câmara)(?: Municipal)? d[eoa]s? (.+?)(?: - | · |$)", i["nome"])
    if m:
        return m.group(1).strip()
    return {"PB": "Paraíba (estado todo)", "PE": "Pernambuco (estado todo)"}.get(i["uf"], "Federal (vagas em PB/PE)")


def slug(t):
    t = unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


for i in ITENS:
    i["cidade"] = cidade(i)
    i["cid"] = "cid-" + slug(i["cidade"])
    i["grupo"], i["mes"] = periodo(i)
    i["id"] = "c" + hashlib.md5(f'{i["nome"]}{i["uf"]}'.encode()).hexdigest()[:6]
    i["areas"] = sorted({PERFIS[p]["area"] for p in i["perfis"]})
    i["sal"] = salario_max(i["salario"])
ITENS.sort(key=lambda i: (ORD[i["grupo"]], i["uf"] != "PB", i["prazo"] or date.max, i.get("previsao") or "9999", i["nome"]))


# ---------- classes de filtro ----------
# grupos de filtro com várias escolhas: (id do checkbox, classe do cartão)
FILTROS = {
    "loc": [("f-pb", "loc-pb"), ("f-pe", "loc-pe"), ("f-fed", "loc-fed")],
    "area": [(f"a-{a}", f"ar-{a}") for a in AREAS],
    "quando": [(f"q-{g}", f"q-{g}") for g, _, _ in GRUPOS],
    "niv": [("n-fund", "niv-fund"), ("n-med", "niv-med"), ("n-sup", "niv-sup")],
}


def classes(i):
    loc = {"PB": "loc-pb", "PE": "loc-pe"}.get(i["uf"], "loc-fed")
    niv = i["nivel"].lower()
    nv = [c for c, rx in (("niv-fund", "fundamental"), ("niv-med", "médio|medio|técnico|tecnico"), ("niv-sup", "superior")) if re.search(rx, niv)]
    sal = [f"sal-{k}" for k in (3, 5, 10) if i["sal"] >= k * 1000]
    return " ".join(["conc", f"st-{i['st']}", loc, i["cid"], f"q-{i['grupo']}", *(nv or ["niv-x"]), *sal, *[f"ar-{a}" for a in i["areas"]]]
                    + ([f"m-{i['mes']}"] if i["mes"] else []))


SALARIOS = [("s-todos", None), ("s-3", "sal-3"), ("s-5", "sal-5"), ("s-10", "sal-10")]
PADRAO = {"f-pb", "f-fed", "s-todos"}  # marcados ao abrir


def html_inputs():
    """Estado dos filtros: inputs irmãos anteriores a <main>, ligados ao form pelo atributo form=."""
    out = [f'<input type="checkbox" class="fx" id="{i}" form="filtros"{" checked" if i in PADRAO else ""}>'
           for ops in FILTROS.values() for i, _ in ops]
    out += [f'<input type="radio" class="fx" name="sal" id="{i}" form="filtros"{" checked" if i in PADRAO else ""}>' for i, _ in SALARIOS]
    out += [f'<input type="checkbox" class="fx" id="{c}" form="filtros">' for c, _, _, _ in CIDADES]
    return "".join(out)


def html_cidades():
    """Chips de cidade agrupados por estado, Paraíba primeiro."""
    blocos = []
    for uf, titulo in (("PB", "Paraíba"), ("PE", "Pernambuco"), ("BR", "Estado todo e federais")):
        chips = "".join(f'<label for="{c}">{e(nome)} <small>{n}</small></label>' for c, nome, u, n in CIDADES if u == uf)
        if chips:
            blocos.append(f'<div class="cid-uf"><b>{titulo}</b><div class="opcoes">{chips}</div></div>')
    return "".join(blocos)


def css_filtros():
    """Várias escolhas por grupo, sem JS e sem :has (barato de recalcular): para cada conjunto exato de
    opções marcadas no grupo, esconde o cartão que não tem nenhuma das classes marcadas.
    Os inputs são irmãos anteriores de <main>, então o seletor é uma cadeia de ~."""
    regras = []
    for g, ops in FILTROS.items():
        extra = ":not(.niv-x)" if g == "niv" else ""
        for mask in range(1, 2 ** len(ops)):            # mask = opções marcadas (pelo menos uma)
            cadeia = " ~ ".join(f"#{i}" + (":checked" if mask >> k & 1 else ":not(:checked)") for k, (i, _) in enumerate(ops))
            nao = "".join(f":not(.{c})" for k, (_, c) in enumerate(ops) if mask >> k & 1)
            regras.append(f"{cadeia} ~ main .conc{nao}{extra}")
    regras += [f"#{i}:checked ~ main .conc:not(.{c})" for i, c in SALARIOS if c]
    # cidade: marcar qualquer cidade esconde todos e mostra de volta só os das cidades marcadas.
    # Os demais filtros usam !important, então o "mostrar" da cidade nunca desfaz outro filtro.
    cid = (",".join(f"#{c}:checked ~ main .conc" for c, _, _, _ in CIDADES) + "{display:none}\n"
           + ",".join(f"#{c}:checked ~ main .conc.{c}" for c, _, _, _ in CIDADES) + "{display:block}\n")
    rotulos = []
    for ops in list(FILTROS.values()) + [SALARIOS] + [[(c, 0) for c, _, _, _ in CIDADES]]:
        for i, _ in ops:
            rotulos.append(f'#{i}:checked ~ .filtros label[for="{i}"]')
    foco = ",".join(f'#{i}:focus-visible ~ .filtros label[for="{i}"]' for ops in list(FILTROS.values()) + [SALARIOS] for i, _ in ops)
    marca = ",".join(f'#{i}:checked ~ .filtros label[for="{i}"]::before' for ops in list(FILTROS.values()) + [[(c, 0) for c, _, _, _ in CIDADES]] for i, _ in ops)
    return (",\n".join(regras) + "{display:none!important}\n" + cid
            + ",".join(rotulos) + "{background:var(--tinta);color:var(--papel);border-color:var(--tinta)}\n"
            + marca + '{content:"✓";width:1.05em}\n'
            + foco + "{outline:2px solid var(--sol);outline-offset:2px}\n"
            + '#f-pb:checked ~ .filtros label[for="f-pb"]{background:var(--pb);border-color:var(--pb);color:#fff}\n'
            + '#f-pe:checked ~ .filtros label[for="f-pe"]{background:var(--pe);border-color:var(--pe);color:#fff}')


# ---------- partes do cartão ----------
def banca_info(nome):
    if re.match(r"a definir|banca a conferir", nome or "", re.I):
        return nome, BANCA_PADRAO  # "A definir (2024: Idecan)" não é Idecan
    for k, b in BANCAS.items():
        if k.lower() == (nome or "").lower() or re.search(b["rx"], nome or "", re.I):
            return k, b
    return nome, BANCA_PADRAO


def link(chave):
    n, u, gratis = F[chave]
    return f'<a href="{u}" target="_blank" rel="noopener">{e(n)}</a><span class="tag">{"grátis" if gratis else "pago"}</span>'


def plano_dados(item, pk):
    """Plano do perfil pk para este concurso: etapas do perfil + treino na banca + reta final, distribuídas até a prova."""
    p = PERFIS[pk]
    bnome, b = banca_info(item["banca"])
    etapas = [dict(t=t, h=h, tarefas=list(ts), fontes=fs) for t, h, ts, fs in p["etapas"]]
    base_h = sum(x["h"] for x in etapas)
    treino = [f"Fazer 2 provas anteriores da {bnome} para cargo parecido, cronometradas" if b is not BANCA_PADRAO
              else "Descobrir a banca no edital e fazer 2 provas anteriores dela",
              "Simulado completo a cada 15 dias, no horário da prova",
              "Refazer os erros e anotar no caderno de erros"]
    if item.get("estrutura"):
        treino.insert(0, "Montar o simulado no formato do edital: " + item["estrutura"])
    etapas.append(dict(t=f"Simulados no estilo {bnome if b is not BANCA_PADRAO else 'da banca'}", h=round(base_h * .15),
                       tarefas=treino, fontes=["pci", "qc"]))
    etapas.append(dict(t="Reta final", h=round(base_h * .07), fontes=[],
                       tarefas=["Revisar só caderno de erros e resumos", "Nada de conteúdo novo na última semana",
                                "Conferir local de prova e documentos"]))
    total = sum(x["h"] for x in etapas)
    if item.get("prova") and item["prova"] > INICIO:
        sem, ref = max(1, (item["prova"] - INICIO).days / 7), f'até a prova em {fdata(item["prova"], True)}'
    else:
        sem = SEM_PADRAO.get(item["st"], 12)
        ref = f"em {sem} semanas (prova sem data: ajuste quando sair o edital)"
    hs = total / sem
    saida, acum = [], 0
    for et in etapas:
        d1 = INICIO + timedelta(days=round(acum / total * sem * 7))
        acum += et["h"]
        d2 = INICIO + timedelta(days=max(round(acum / total * sem * 7) - 1, 0))
        saida.append(dict(titulo=et["t"], inicio=d1.isoformat(), fim=d2.isoformat(), horas=et["h"], tarefas=et["tarefas"],
                          fontes=[dict(nome=F[f][0], url=F[f][1], gratis=bool(F[f][2])) for f in et["fontes"]]))
    return dict(perfil=pk, cargo=item["perfis"][pk], nome=p["nome"], conteudo=p["conteudo"], totalHoras=total,
                horasSemana=round(hs, 1), referencia=f"{ref}, começando em {fdata(INICIO)}",
                alerta=(f"Para cobrir tudo seriam {num(hs)} h por semana. Se não der, faça as etapas 1 e 2, "
                        f"os simulados e a reta final, e passe rápido pelo resto.") if hs > 25 else None,
                etapas=saida)


def plano(item, pk):
    d = plano_dados(item, pk)
    blocos = []
    for n, et in enumerate(d["etapas"]):
        tarefas = "".join(f'<li><label><input type="checkbox" data-k="{item["id"]}-{pk}-{n}-{j}"><span>{e(t)}</span></label></li>'
                          for j, t in enumerate(et["tarefas"]))
        fontes = (f'<p class="fontes">{" · ".join(link_dado(f) for f in et["fontes"])}</p>' if et["fontes"] else "")
        blocos.append(f'<li class="etp"><div class="etp-h"><b>{e(et["titulo"])}</b><time>{fdata(_d(et["inicio"]))} – '
                      f'{fdata(_d(et["fim"]))} · {et["horas"]} h</time></div><ul class="check">{tarefas}</ul>{fontes}</li>')
    chips = "".join(f"<span>{e(x)}</span>" for x in d["conteudo"])
    alerta = f'<p class="aviso">{e(d["alerta"])}</p>' if d["alerta"] else ""
    return (f'<h4>O que costuma cair</h4><div class="chips">{chips}</div>'
            f'<p class="nota">Lista típica de {e(d["nome"].split(" (")[0].lower())} nessa banca. Confira o conteúdo exato no edital.</p>'
            f'<div class="ritmo"><span><b>{d["totalHoras"]} h</b> de estudo</span><span><b>{num(d["horasSemana"])} h</b> por semana</span>'
            f'<span>{e(d["referencia"])}</span></div>{alerta}'
            f'<ol class="etapas">{"".join(blocos)}</ol>')


def link_dado(f):
    return (f'<a href="{f["url"]}" target="_blank" rel="noopener">{e(f["nome"])}</a>'
            f'<span class="tag">{"grátis" if f["gratis"] else "pago"}</span>')


def app_json():
    """Mesmos concursos e planos em JSON, para o app SwiftUI (e quem mais quiser ler)."""
    rot = {"m3": fmes(mes_mais(3)), "m6": fmes(mes_mais(6)), "m12": fmes(mes_mais(12))}
    itens = []
    for i in ITENS:
        bnome, b = banca_info(i["banca"])
        itens.append(dict(
            id=i["id"], nome=i["nome"], uf=i["uf"], cidade=i["cidade"], st=i["st"], status=STATUS[i["st"]], grupo=i["grupo"],
            mes=i["mes"], areas=i["areas"], cargos=list(dict.fromkeys(i["perfis"].values())), banca=bnome,
            bancaFormato=b["formato"], bancaDicas=b["dicas"], bancaProvas=b.get("provas"), nivel=i["nivel"],
            vagas=i["vagas"], salario=i["salario"], salarioMax=int(i["sal"]), inscricoes=i["insc"],
            prazo=i["prazo"].isoformat() if i.get("prazo") else None, prova=i["prova"].isoformat() if i.get("prova") else None,
            previsao=i.get("previsao"), previsaoTxt=i.get("previsao_txt"), estrutura=i.get("estrutura"), obs=i["obs"],
            novo=bool(i.get("novo")), links=[dict(nome=n, url=u) for n, u in i["links"]],
            planos=[plano_dados(i, pk) for pk in i["perfis"]]))
    return dict(geradoEm=datetime.now().isoformat(timespec="minutes"), curadoria=cur["atualizado_em"],
                varredura=var.get("gerado_em"), inicioPlano=INICIO.isoformat(),
                grupos=[dict(id=g, titulo=t, sub=sub.format(**rot)) for g, t, sub in GRUPOS], itens=itens)


def carimbo(i):
    """Bloco de data à esquerda do cartão: prazo de inscrição, mês previsto ou sem data."""
    if i["st"] == "aberto" and i.get("prazo"):
        dias = (i["prazo"] - HOJE).days
        urg = " urgente" if dias <= 7 else ""
        return (f'<div class="carimbo{urg}"><small>inscreva até</small><b>{i["prazo"].day:02d}</b><span>{MESES[i["prazo"].month - 1]}</span>'
                f'<em class="cont" data-ate="{i["prazo"].isoformat()}">{dias} dias</em></div>')
    if i["st"] == "aberto":
        return '<div class="carimbo"><small>inscrição</small><b>já</b><span>aberta</span></div>'
    if i.get("previsao"):
        a, m = i["previsao"].split("-")
        return f'<div class="carimbo prev"><small>previsão</small><b>{MESES[int(m) - 1]}</b><span>{a}</span></div>'
    return '<div class="carimbo prev"><small>previsão</small><b>—</b><span>sem data</span></div>'


def cartao(i, n):
    bnome, b = banca_info(i["banca"])
    cargos = " · ".join(dict.fromkeys(i["perfis"].values()))
    loc = {"PB": ("pb", "Paraíba"), "PE": ("pe", "Pernambuco")}.get(i["uf"], ("fed", "Federal"))
    chips = "".join(f'<span class="area a-{a}">{AREAS[a]}</span>' for a in i["areas"])
    novo = '<span class="novo">Novo</span>' if i.get("novo") else ""
    meta = []
    if i.get("prova"):
        meta.append(f"Prova {fdata(i['prova'], True)}")
    if i["st"] != "aberto" and i.get("previsao_txt"):
        meta.append(i["previsao_txt"])
    if i["sal"]:
        meta.append(i["salario"])
    linhas = [("Cargos do seu interesse", cargos), ("Escolaridade", i["nivel"]), ("Vagas", i["vagas"]),
              ("Remuneração", i["salario"]), ("Inscrições", i["insc"])]
    if i.get("prova"):
        linhas.append(("Prova", fdata(i["prova"], True)))
    if i["st"] != "aberto" and i.get("previsao"):
        linhas.append(("Previsão do edital", f'{fmes(i["previsao"])} · {i.get("previsao_txt") or ""}'))
    if i.get("estrutura"):
        linhas.append(("Como é a prova", i["estrutura"]))
    vaga = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in linhas)
    links = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{e(t)} ↗</a>' for t, u in i["links"])
    provas_b = f'<a href="{b["provas"]}" target="_blank" rel="noopener">Provas anteriores da banca ↗</a>' if b.get("provas") else ""
    banca = (f'<p class="formato"><b>{e(bnome)}</b> · {e(b["formato"])}</p>'
             f'<ul class="dicas">{"".join(f"<li>{e(x)}</li>" for x in b["dicas"])}</ul>{provas_b}')
    pks = list(i["perfis"])
    if len(pks) == 1:
        planos = plano(i, pks[0])
    else:
        nome_g = f'{i["id"]}-pl'
        escolha = "".join(f'<input type="radio" class="c{k}" name="{nome_g}" id="{nome_g}{k}"{" checked" if k == 0 else ""}>'
                          f'<label for="{nome_g}{k}">{e(i["perfis"][pk])}</label>' for k, pk in enumerate(pks))
        planos = (f'<p class="nota">Este edital tem {len(pks)} cargos do seu interesse. Escolha o plano:</p>'
                  f'<div class="planos">{escolha}' + "".join(f'<div class="pl pl{k}">{plano(i, pk)}</div>' for k, pk in enumerate(pks)) + "</div>")
    t = f"{i['id']}-t"
    return f"""
<details class="{classes(i)}" id="{i['id']}" data-sal="{int(i['sal'])}" data-banca="{e(bnome)}" style="--i:{min(n, 12)}">
  <summary>
    {carimbo(i)}
    <div class="topo-c">
      <div class="selos"><span class="loc l-{loc[0]}">{loc[1]}</span><span class="cid">{e(i["cidade"])}</span><span class="st">{STATUS[i['st']]}</span>{chips}{novo}<span class="iniciado">Plano iniciado</span></div>
      <h3>{e(i['nome'])}</h3>
      <p class="resumo"><b>{e(bnome)}</b> · {e(cargos)}</p>
      <p class="meta">{" · ".join(e(x) for x in meta)}</p>
    </div>
    <span class="seta" aria-hidden="true"></span>
  </summary>
  <div class="painel">
    <input type="radio" class="t1" name="{t}" id="{t}1" checked><label for="{t}1">Vaga</label>
    <input type="radio" class="t2" name="{t}" id="{t}2"><label for="{t}2">Banca</label>
    <input type="radio" class="t3" name="{t}" id="{t}3"><label for="{t}3">Plano de estudos</label>
    <section class="p1"><dl class="ficha">{vaga}</dl><p class="obs">{e(i['obs'])}</p><p class="links">{links}</p></section>
    <section class="p2">{banca}</section>
    <section class="p3">{planos}</section>
  </div>
</details>"""


# ---------- régua de 24 meses ----------
def regua():
    meses = [mes_mais(k) for k in range(24)]
    cont = {m: {"ab": 0, "pr": 0} for m in meses}
    for i in ITENS:
        if i["mes"] in cont:
            cont[i["mes"]]["ab" if i["st"] == "aberto" else "pr"] += 1
    topo = max(1, max(c["ab"] + c["pr"] for c in cont.values()))
    barras = []
    for k, m in enumerate(meses):
        a, mm = m.split("-")
        c = cont[m]
        tot = c["ab"] + c["pr"]
        ano = f'<i class="ano">{a}</i>' if mm == "01" or k == 0 else ""
        barras.append(
            f'<button type="button" class="mes" data-mes="{m}" style="--d:{k}" {"disabled" if not tot else ""} '
            f'aria-label="{fmes(m)}: {tot} concursos">'
            f'<span class="col"><span class="pr" style="height:{c["pr"] / topo * 100:.0f}%"></span>'
            f'<span class="ab" style="height:{c["ab"] / topo * 100:.0f}%"></span></span>'
            f'<span class="n">{tot or ""}</span><span class="lbl">{MESES[int(mm) - 1]}</span>{ano}</button>')
    sem = sum(1 for i in ITENS if not i["mes"])
    return "".join(barras), sem


def contagem(f):
    return sum(1 for i in ITENS if f(i))


def grupos():
    rot = {"m3": fmes(mes_mais(3)), "m6": fmes(mes_mais(6)), "m12": fmes(mes_mais(12))}
    out, n = [], 0
    for g, titulo, sub in GRUPOS:
        cards = [i for i in ITENS if i["grupo"] == g]
        if not cards:
            continue
        html_c = []
        for i in cards:
            html_c.append(cartao(i, n))
            n += 1
        out.append(f'<section class="grupo g-{g}" id="g-{g}"><header><h2>{titulo}</h2><p>{e(sub.format(**rot))}</p>'
                   f'<span class="qt">{len(cards)}</span></header><div class="cards">{"".join(html_c)}</div></section>')
    return "".join(out)


_cont = {}
for i in ITENS:
    uf = i["uf"] if i["uf"] in ("PB", "PE") and "estado todo" not in i["cidade"] else "BR"
    _cont.setdefault(i["cid"], [i["cidade"], uf, 0])[2] += 1
CIDADES = sorted(((k, n, u, q) for k, (n, u, q) in _cont.items()), key=lambda x: ({"PB": 0, "PE": 1}.get(x[2], 2), 0 if x[0] == "cid-paraiba-estado-todo" else 1, slug(x[1])))
barras, sem_data = regua()
CURTO = {"agora": "Abertas", "3": "3 meses", "6": "6 meses", "12": "1 ano", "mais": "+1 ano", "sem": "Sem data"}
NAV = "".join(f'<a href="#g-{g}" data-g="{g}">{CURTO[g]} <small>{sum(i["grupo"] == g for i in ITENS)}</small></a>'
              for g, _, _ in GRUPOS if any(i["grupo"] == g for i in ITENS))
pb = [i for i in ITENS if i["uf"] == "PB"]
bancas = sorted({banca_info(i["banca"])[0] for i in ITENS})
var_quando = (datetime.fromisoformat(var["gerado_em"]).strftime("%d/%m/%Y às %H:%M") if var.get("gerado_em") else "nunca")
prox = next((i for i in ITENS if i.get("prazo")), None)

subs = {
    "GRUPOS": grupos(), "BARRAS": barras, "CSS_FILTROS": css_filtros(), "INPUTS": html_inputs(), "CIDADES": html_cidades(), "NAV_GRUPOS": NAV, "SEM_DATA": str(sem_data),
    "PB_AB": str(sum(i["st"] == "aberto" for i in pb)), "PB_PREV": str(sum(i["st"] != "aberto" for i in pb)),
    "PE_TOTAL": str(contagem(lambda i: i["uf"] == "PE")), "FED_TOTAL": str(contagem(lambda i: i["uf"] not in ("PB", "PE"))),
    "N_TOTAL": str(len(ITENS)), "N_AB": str(contagem(lambda i: i["st"] == "aberto")),
    "PROX": (f'{fdata(prox["prazo"])} · {e(prox["nome"])}' if prox else "—"),
    "C_PB": str(len(pb)), "C_PE": str(contagem(lambda i: i["uf"] == "PE")),
    "C_SEG": str(contagem(lambda i: "seg" in i["areas"])), "C_TI": str(contagem(lambda i: "ti" in i["areas"])),
    "C_FIS": str(contagem(lambda i: "fis" in i["areas"])), "C_ADM": str(contagem(lambda i: "adm" in i["areas"])),
    "BANCAS": "".join(f'<option value="{e(b)}">{e(b)}</option>' for b in bancas),
    "CURADORIA": fdata(_d(cur["atualizado_em"]), True), "VARREDURA": var_quando,
    "ERROS": e(f' · {len(var["erros"])} página(s) não abriram' if var.get("erros") else ""),
    "GERADO": datetime.now().isoformat(timespec="minutes"),
    "PWA_HEAD": "", "PWA_BODY": "",
}
if APP:  # versão instalável: trechos do app web
    extra = Path(__file__).with_name("app_extra.html").read_text(encoding="utf-8")
    subs["PWA_HEAD"], subs["PWA_BODY"] = extra.split("<!-- CORPO -->")
pagina = Path(__file__).with_name("gerar_plano_template.html").read_text(encoding="utf-8")
for k, v in subs.items():
    pagina = pagina.replace("{{" + k + "}}", v)
assert "{{" not in pagina, "placeholder sobrando"
SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text(pagina, encoding="utf-8")
(SAIDA.parent / "app.json").write_text(json.dumps(app_json(), ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{SAIDA.name}: {len(ITENS)} concursos (PB {len(pb)}, abertos {subs['N_AB']}), {len(pagina) // 1024} KB")
