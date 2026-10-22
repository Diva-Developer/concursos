"""Varredura rápida e gratuita no PCI Concursos -> dados/varredura.json.

Abertos: listas Nordeste, Nacional e vagas de fisioterapeuta, só PB e PE (federais entram
quando a notícia cita vaga ou prova em PB/PE). Previstos: notícias de "previstos" dos últimos
6 meses que citam PB ou PE, com o mês esperado do edital quando o texto informa.
Para cada concurso abre a notícia e lê banca, data da prova e cargos (perfis de perfis.py).
Só biblioteca padrão do Python.

Uso: python raspar_pci.py
"""
import html
import json
import re
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from perfis import BANCAS, PERFIS  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
ARQ = BASE / "dados" / "varredura.json"
UFS = {"PB", "PE"}
PAUSA = 1.0  # segundos entre páginas, para não sobrecarregar o site
ABERTOS = [
    ("nordeste", "https://www.pciconcursos.com.br/concursos/nordeste/"),
    ("nacional", "https://www.pciconcursos.com.br/concursos/nacional/"),
    ("fisio", "https://www.pciconcursos.com.br/vagas/fisioterapeuta"),
]
PREVISTOS = "https://www.pciconcursos.com.br/previstos/"
RX_PB = r"Para[ií]ba|\bPB\b|Jo[aã]o Pessoa|Campina Grande|Cabedelo|Santa Rita|Bayeux|Patos|Guarabira|Sousa|Cajazeiras"
RX_PE = r"Pernambuco|\bPE\b|Recife|Olinda|Jaboat[aã]o|Caruaru|Petrolina|Paulista|Garanhuns|Alepe"
RX_FED_LOCAL = RX_PB + "|" + RX_PE + r"|todo o (pa[ií]s|Brasil)|todos os estados|todas as capitais|todas as unidades da federa"
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
MES = {m: i + 1 for i, m in enumerate(MESES)}


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (atualizador pessoal de concursos)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def texto(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def corpo_noticia(pagina):
    """Só o texto da notícia: o menu do site cita Informática e D. Penal em toda página."""
    m = re.search(r'<article id="noticia".*?</article>', pagina, re.S)
    return texto(m.group(0) if m else "").split("Compartilhe")[0]


def achar_banca(t):
    for nome, b in BANCAS.items():
        if re.search(b["rx"], t, re.I):
            return nome
    m = re.search(r"(?:organiza(?:do|da|ção)|banca)[^.]{0,40}?(?:pel[oa]|é [oa]|:)\s+([A-ZÁÉÍÓÚ][\w&/\-. ]{2,40}?)(?:[,.;(]| e | com )", t)
    return m.group(1).strip() if m else None


def achar_prova(t, depois_de):
    """Primeira data perto da palavra 'prova' que caia depois do fim das inscrições."""
    limite = depois_de or date.today().isoformat()
    for m in re.finditer(r"prova", t, re.I):
        trecho = t[m.end():m.end() + 160]
        datas = [date(int(a), MES[mes.lower()], int(d)) for d, mes, a in
                 re.findall(r"(\d{1,2})º? de (" + "|".join(MESES) + r") de (\d{4})", trecho, re.I)]
        datas += [date(int(a), int(mm), int(d)) for d, mm, a in re.findall(r"(\d{2})/(\d{2})/(\d{4})", trecho)]
        for d in datas:
            if d.isoformat() > limite:
                return d.isoformat()
    return None


def achar_previsao(t):
    """Mês esperado do edital (AAAA-MM) e o trecho que o informa, se o texto disser."""
    hoje = date.today().strftime("%Y-%m")
    regras = [
        (r"(primeiro|1º) semestre de (20\d\d)", lambda m: f"{m.group(2)}-03"),
        (r"(segundo|2º) semestre de (20\d\d)", lambda m: f"{m.group(2)}-09"),
        (r"(?:fim|final) de (20\d\d)", lambda m: f"{m.group(1)}-11"),
        (r"(" + "|".join(MESES) + r") de (20\d\d)", lambda m: f"{m.group(2)}-{MES[m.group(1).lower()]:02d}"),
        (r"(?:em|até|para|no ano de) (20\d\d)", lambda m: f"{m.group(1)}-06"),
    ]
    for m in re.finditer(r"edital|inscriç|publicaç|previst|concurso", t, re.I):
        trecho = t[m.start():m.start() + 120]
        for rx, conv in regras:
            p = re.search(rx, trecho, re.I)
            if p and conv(p) >= hoje:
                return conv(p), re.sub(r"\s+", " ", trecho[:p.end()]).strip()
    return None, None


def achar_perfis(t):
    """Perfis encontrados e o cargo que bateu, completando a palavra (ex.: 'fisioterap' -> 'Fisioterapeuta')."""
    achados = {}
    for k, p in PERFIS.items():
        m = re.search(r"(?:" + p["rx"] + r")[\wÀ-ú]*(?: (?:de|em|da|do) [\wÀ-ú]+)?", t, re.I)
        if m:
            ini = m.start()
            while ini > 0 and t[ini - 1].isalpha():
                ini -= 1
            cargo = t[ini:m.end()].strip()
            achados[k] = cargo[:1].upper() + cargo[1:]
    return achados


def ler_lista(pagina):
    itens = []
    for b in re.findall(r'<div class="na".*?<div class="clear">', pagina, re.S):
        a = re.search(r'<div class="ca"><a href="([^"]+)" title="([^"]*)"[^>]*>([^<]*)</a>', b)
        if not a:
            continue
        uf = re.search(r'class="cc">(.*?)</div>', b, re.S)
        cd = re.search(r'class="cd">(.*?)</div>', b, re.S)
        ce = re.search(r'class="ce">(.*?)</div>', b, re.S)
        partes = [texto(p) for p in re.split(r"<br\s*/?>", cd.group(1))] if cd else []
        datas = re.findall(r"(\d{2})/(\d{2})/(\d{4})", ce.group(1) if ce else "")
        prazo = date(int(datas[-1][2]), int(datas[-1][1]), int(datas[-1][0])) if datas else None
        itens.append(dict(uf=(texto(uf.group(1)) if uf else "") or "BR", url=a.group(1), titulo=html.unescape(a.group(2)),
                          orgao=html.unescape(a.group(3)), vagas=partes[0] if partes else "",
                          cargos=partes[1] if len(partes) > 1 else "", nivel=partes[2] if len(partes) > 2 else "",
                          prazo_txt=texto(ce.group(1)) if ce else "", prazo=prazo.isoformat() if prazo else None,
                          st="aberto"))
    return itens


def ler_previstos(pagina):
    """Notícias de previstos dos últimos 180 dias que citam PB ou PE."""
    corte, atual, itens = date.today() - timedelta(days=180), None, []
    for m in re.finditer(r'<h2 class="principal">(\d{2})/(\d{2})/(\d{4})</h2>|<a href="(https://www\.pciconcursos\.com\.br/previstos/[^"#]+)" title="([^"]*)"', pagina):
        if m.group(1):
            atual = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            continue
        if not atual or atual < corte:
            continue
        titulo = html.unescape(m.group(5))
        alvo = f"{titulo} {m.group(4).replace('-', ' ')}"
        uf = "PB" if re.search(RX_PB, alvo, re.I) else "PE" if re.search(RX_PE, alvo, re.I) else None
        if uf:
            itens.append(dict(uf=uf, url=m.group(4), titulo=titulo, orgao=titulo, vagas="", cargos="", nivel="",
                              prazo_txt="", prazo=None, st="previsto", noticia_em=atual.isoformat()))
    return itens


def main():
    anterior = {}
    if ARQ.exists():
        try:
            anterior = {i["url"]: i for i in json.loads(ARQ.read_text(encoding="utf-8")).get("itens", [])}
        except (ValueError, KeyError):
            anterior = {}
    hoje, erros, achados = date.today().isoformat(), [], {}
    fontes = [(n, u, ler_lista) for n, u in ABERTOS] + [("previstos", PREVISTOS, ler_previstos)]
    for nome, url, leitor in fontes:
        try:
            lista = leitor(baixar(url))
            print(f"{nome}: {len(lista)} concursos na lista")
        except Exception as ex:  # site fora do ar ou mudou: segue com o resto
            erros.append(f"{nome}: {ex}")
            print(f"{nome}: ERRO {ex}")
            continue
        for it in lista:
            if (it["prazo"] and it["prazo"] < hoje) or (it["uf"] not in UFS and it["uf"] != "BR"):
                continue
            achados.setdefault(it["url"], it)
        time.sleep(PAUSA)

    # abre a notícia de cada um (reaproveita a rodada anterior para não baixar de novo)
    final = {}
    for n, it in enumerate(achados.values(), 1):
        velho = anterior.get(it["url"], {})
        if velho.get("lida"):
            it.update({k: velho[k] for k in ("banca", "prova", "perfis", "lida", "local", "previsao", "previsao_txt") if k in velho})
        else:
            try:
                corpo = corpo_noticia(baixar(it["url"]))
                it["lida"] = True
                print(f"  [{n}/{len(achados)}] {it['orgao'][:60]}")
            except Exception as ex:
                erros.append(f'{it["orgao"][:60]}: {ex}')
                corpo = ""
            alvo = f'{it["titulo"]} {it["cargos"]} {corpo}'
            it["banca"], it["perfis"] = achar_banca(corpo), achar_perfis(alvo)
            it["prova"] = achar_prova(corpo, it["prazo"]) if it["st"] == "aberto" else None
            it["local"] = bool(re.search(RX_FED_LOCAL, f'{it["titulo"]} {corpo}', re.I)) if it["uf"] == "BR" else True
            if it["st"] == "previsto":
                it["previsao"], it["previsao_txt"] = achar_previsao(corpo)
            time.sleep(PAUSA)
        if not it.get("local", True) and it.get("lida"):
            continue  # federal sem vaga ou prova em PB/PE
        if not it["perfis"]:  # cargo genérico: plano administrativo ou superior em geral
            it["perfis"] = {"geral_sup" if it["nivel"].strip() == "Superior" else "adm_med": "Cargos gerais do edital"}
        it["areas"] = sorted({PERFIS[p]["area"] for p in it["perfis"]})
        it["novo"] = bool(anterior) and it["url"] not in anterior
        final[it["url"]] = it

    itens = sorted(final.values(), key=lambda i: (i["st"], i["prazo"] or i.get("previsao") or "9999", i["orgao"]))
    ARQ.write_text(json.dumps({"gerado_em": datetime.now().isoformat(timespec="minutes"), "fonte": "pciconcursos.com.br",
                               "erros": erros, "itens": itens}, ensure_ascii=False, indent=1), encoding="utf-8")
    abertos = sum(i["st"] == "aberto" for i in itens)
    print(f"{len(itens)} concursos guardados ({abertos} abertos, {len(itens) - abertos} previstos, "
          f"{sum(i['novo'] for i in itens)} novos). Erros: {len(erros)}")
    return 1 if len(erros) >= len(fontes) else 0


if __name__ == "__main__":
    sys.exit(main())
