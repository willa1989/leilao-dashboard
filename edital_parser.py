"""
LEILÃO INTEL — Edital Parser v2.0
Parser universal para editais de leilão imobiliário
Suporta: BCO Leilões, Sold, Superbid, Lance&Lance, TJSP, Zuk, e genéricos
"""

import re
import unicodedata
from typing import Optional

# ─────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────

def norm(s: str) -> str:
    """Normaliza texto: minúsculas, sem acento, sem espaço duplo."""
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s.lower()).strip()

def limpar_valor(texto: str) -> float:
    """Converte string monetária brasileira → float."""
    if not texto:
        return 0.0
    t = re.sub(r'[R$\s\.]', '', str(texto)).replace(',', '.')
    m = re.search(r'\d+\.?\d*', t)
    return float(m.group()) if m else 0.0

def extrair_primeiro_valor(texto: str, padrao: str,
                           minimo: float = 0, maximo: float = 9e9) -> float:
    """Extrai primeiro valor monetário que casa com o padrão."""
    matches = re.findall(padrao, texto, re.IGNORECASE)
    for raw in matches:
        v = limpar_valor(raw)
        if minimo < v < maximo:
            return v
    return 0.0

def extrair_data(texto: str, padrao_ctx: str) -> str:
    """Extrai data próxima a um contexto."""
    DATA_RE = r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}'
    DATA_EXT = r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}'
    m = re.search(
        padrao_ctx + r'[^\d]{0,30}(' + DATA_RE + r'|' + DATA_EXT + r')',
        texto, re.IGNORECASE
    )
    if m:
        return m.group(1)
    return ""

# ─────────────────────────────────────────────
#  DETECÇÃO DE LEILOEIRA
# ─────────────────────────────────────────────

LEILOEIRAS = {
    "bco":        ["bcoleiloes", "bco leiloes", "bco leil"],
    "sold":       ["sold leil", "sold.com", "sold imoveis"],
    "superbid":   ["superbid"],
    "lance_lance":["lance & lance", "lancelance", "lance e lance"],
    "tjsp":       ["tribunal de justica", "tjsp", "poder judiciario",
                   "juizo", "vara civel", "execucao fiscal",
                   "alienacao judicial", "hasta publica"],
    "zuk":        ["zuk leil", "zukleiloes"],
    "sold_imoveis":["sold imoveis"],
    "jeff":       ["jeff leil", "jeffleiloes"],
    "sodresantoro":["sodre santoro", "sodresantoro"],
}

def detectar_leiloeira(texto: str) -> str:
    """Retorna chave da leiloeira ou 'generico'."""
    t = norm(texto[:2000])  # olha só no início
    for nome, sinais in LEILOEIRAS.items():
        for sinal in sinais:
            if sinal in t:
                return nome
    return "generico"

# ─────────────────────────────────────────────
#  PARSERS ESPECIALIZADOS POR LEILOEIRA
# ─────────────────────────────────────────────

def _parse_bco(texto: str, dados: dict):
    """BCO Leilões — extrajudicial, lance só na plataforma."""
    dados["leiloeira_nome"] = "BCO Leilões"
    dados["tipo_leilao"]    = "Extrajudicial"
    dados["lance_na_plataforma"] = True
    dados["_avisos"].append(
        "⚠ BCO LEILÕES — Lance não consta no edital. "
        "Consulte bcoleiloes.com.br e insira manualmente."
    )
    # Áreas
    m = re.search(r'área\s+total\s+de\s+([\d.,]+)\s*m[²2]', texto, re.I)
    if m: dados["area_total"] = limpar_valor(m.group(1)); dados["_extraidos"].append("area_total")
    m = re.search(r'área\s+útil\s+de\s+([\d.,]+)\s*m[²2]', texto, re.I)
    if m: dados["area_util"] = limpar_valor(m.group(1)); dados["_extraidos"].append("area_util")
    # Data
    m = re.search(r'encerrando.se\s+no\s+dia\s+(\d{2}\/\d{2}\/\d{4})', texto, re.I)
    if m: dados["data_leilao"] = m.group(1); dados["data_1praca"] = m.group(1); dados["_extraidos"].append("data_leilao")
    # Comissão
    m = re.search(r'(\d+)\s*%\s*\([^)]*cinco[^)]*\)', texto, re.I)
    if m: dados["comissao_pct"] = float(m.group(1)); dados["_extraidos"].append("comissao_pct")


def _parse_sold(texto: str, dados: dict):
    """Sold Leilões — estrutura bem definida."""
    dados["leiloeira_nome"] = "Sold Leilões"
    dados["tipo_leilao"] = "Extrajudicial"

    # Áreas
    for p in [r'[ÁA]rea\s+[Pp]rivativa[:\s]*([\d.,]+)\s*m',
              r'[ÁA]rea\s+[úu]til[:\s]*([\d.,]+)\s*m']:
        m = re.search(p, texto, re.I)
        if m: dados["area_util"] = limpar_valor(m.group(1)); dados["_extraidos"].append("area_util"); break

    for p in [r'[ÁA]rea\s+[Tt]otal[:\s]*([\d.,]+)\s*m',
              r'[ÁA]rea\s+[Cc]onstruída[:\s]*([\d.,]+)\s*m']:
        m = re.search(p, texto, re.I)
        if m: dados["area_total"] = limpar_valor(m.group(1)); dados["_extraidos"].append("area_total"); break

    # Avaliação
    for p in [r'[Vv]alor\s+de\s+[Aa]valia[çc][ãa]o[:\s]*R?\$?\s*([\d.,]+)',
              r'[Aa]valia[çc][ãa]o[:\s]*R?\$?\s*([\d.,]+)']:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if v > 1000: dados["avaliacao"] = v; dados["_extraidos"].append("avaliacao"); break

    # Praças — Sold usa formato "1ª Praça: R$ X / 2ª Praça: R$ X"
    p1 = re.search(r'1[aª°]\s*[Pp]ra[çc]a[:\s]+R?\$?\s*([\d.,]+)', texto, re.I)
    if p1:
        v = limpar_valor(p1.group(1))
        if v > 1000: dados["lance_1praca"] = v; dados["_extraidos"].append("lance_1praca")

    p2 = re.search(r'2[aª°]\s*[Pp]ra[çc]a[:\s]+R?\$?\s*([\d.,]+)', texto, re.I)
    if p2:
        v = limpar_valor(p2.group(1))
        if v > 1000: dados["lance_2praca"] = v; dados["_extraidos"].append("lance_2praca")

    # Datas
    d1 = re.search(r'1[aª°]\s*[Pp]ra[çc]a[^\d]{0,20}(\d{2}\/\d{2}\/\d{4})', texto, re.I)
    if d1: dados["data_1praca"] = d1.group(1); dados["_extraidos"].append("data_1praca")
    d2 = re.search(r'2[aª°]\s*[Pp]ra[çc]a[^\d]{0,20}(\d{2}\/\d{2}\/\d{4})', texto, re.I)
    if d2: dados["data_2praca"] = d2.group(1); dados["_extraidos"].append("data_2praca")


def _parse_superbid(texto: str, dados: dict):
    """Superbid — formato conciso."""
    dados["leiloeira_nome"] = "Superbid"
    dados["tipo_leilao"] = "Extrajudicial"

    # Lance inicial
    for p in [r'[Ll]ance\s+[Ii]nicial[:\s]+R?\$?\s*([\d.,]+)',
              r'[Vv]alor\s+[Mm]ínimo[:\s]+R?\$?\s*([\d.,]+)',
              r'LANCE[:\s]+R?\$?\s*([\d.,]+)']:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if v > 1000: dados["lance_1praca"] = v; dados["_extraidos"].append("lance_1praca"); break

    # Área — formato "XX m² (área útil)"
    for p in [r'([\d.,]+)\s*m[²2]\s*\(?[áa]rea\s+[úu]til',
              r'[áa]rea\s+[úu]til[:\s]*([\d.,]+)\s*m']:
        m = re.search(p, texto, re.I)
        if m: dados["area_util"] = limpar_valor(m.group(1)); dados["_extraidos"].append("area_util"); break

    # Avaliação
    m = re.search(r'[Aa]valia[çc][ãa]o[:\s]*R?\$?\s*([\d.,]+)', texto, re.I)
    if m:
        v = limpar_valor(m.group(1))
        if v > 1000: dados["avaliacao"] = v; dados["_extraidos"].append("avaliacao")

    # Data
    m = re.search(r'[Dd]ata\s+do\s+[Ll]eilão[:\s]+(\d{2}\/\d{2}\/\d{4})', texto, re.I)
    if m: dados["data_leilao"] = m.group(1); dados["data_1praca"] = m.group(1); dados["_extraidos"].append("data_leilao")


def _parse_lance_lance(texto: str, dados: dict):
    """Lance & Lance — campos em maiúsculas."""
    dados["leiloeira_nome"] = "Lance & Lance"
    dados["tipo_leilao"] = "Extrajudicial"

    # LANCE MÍNIMO: R$ X.XXX.XXX,XX
    m = re.search(r'LANCE\s+M[ÍI]NIMO[:\s]+R?\$?\s*([\d.,]+)', texto, re.I)
    if m:
        v = limpar_valor(m.group(1))
        if v > 1000: dados["lance_1praca"] = v; dados["_extraidos"].append("lance_1praca")

    # PRAÇAS
    p1 = re.search(r'1[aª°]?\s*PRA[ÇC]A[:\s]+(\d{2}\/\d{2}\/\d{4})', texto, re.I)
    if p1: dados["data_1praca"] = p1.group(1); dados["_extraidos"].append("data_1praca")
    p1v = re.search(r'1[aª°]?\s*PRA[ÇC]A[^\n]{0,30}R?\$?\s*([\d.,]+)', texto, re.I)
    if p1v:
        v = limpar_valor(p1v.group(1))
        if v > 1000: dados["lance_1praca"] = v

    p2 = re.search(r'2[aª°]?\s*PRA[ÇC]A[:\s]+(\d{2}\/\d{2}\/\d{4})', texto, re.I)
    if p2: dados["data_2praca"] = p2.group(1); dados["_extraidos"].append("data_2praca")
    p2v = re.search(r'2[aª°]?\s*PRA[ÇC]A[^\n]{0,30}R?\$?\s*([\d.,]+)', texto, re.I)
    if p2v:
        v = limpar_valor(p2v.group(1))
        if v > 1000: dados["lance_2praca"] = v; dados["_extraidos"].append("lance_2praca")

    # ÁREA: XX,XXm²
    m = re.search(r'[ÁA]REA[:\s]*([\d.,]+)\s*m[²2]?', texto, re.I)
    if m: dados["area_util"] = limpar_valor(m.group(1)); dados["_extraidos"].append("area_util")

    # AVALIAÇÃO: R$ X.XXX.XXX,XX
    m = re.search(r'AVALIA[ÇC][ÃA]O[:\s]*R?\$?\s*([\d.,]+)', texto, re.I)
    if m:
        v = limpar_valor(m.group(1))
        if v > 1000: dados["avaliacao"] = v; dados["_extraidos"].append("avaliacao")

    # DÉBITOS inline: IPTU R$ XXX / COND. R$ XXX
    m_iptu = re.search(r'IPTU[:\s]*R?\$?\s*([\d.,]+)', texto, re.I)
    if m_iptu:
        v = limpar_valor(m_iptu.group(1))
        if 0 < v < 500_000: dados["iptu_debito"] = v; dados["_extraidos"].append("iptu_debito")

    m_cond = re.search(r'COND(?:OM[ÍI]NIO)?[.:\s]*R?\$?\s*([\d.,]+)', texto, re.I)
    if m_cond:
        v = limpar_valor(m_cond.group(1))
        if 0 < v < 500_000: dados["cond_debito"] = v; dados["_extraidos"].append("cond_debito")

    # COMISSÃO: X%
    m = re.search(r'COMISS[ÃA]O[:\s]*([\d,]+)\s*%', texto, re.I)
    if m: dados["comissao_pct"] = limpar_valor(m.group(1)); dados["_extraidos"].append("comissao_pct")


def _parse_tjsp(texto: str, dados: dict):
    """TJSP — leilão judicial, linguagem jurídica."""
    dados["leiloeira_nome"] = "Leilão Judicial"
    dados["tipo_leilao"] = "Judicial"

    # Processo
    m = re.search(r'[Pp]rocesso\s+(?:n[°º.]?\s*)?([\d.\-\/]+-[\d.\/]+)', texto)
    if m: dados["numero_processo"] = m.group(1); dados["_extraidos"].append("numero_processo")

    # Vara / Comarca
    m = re.search(r'(\d+[aª°]?\s*[Vv]ara[^\n,\.]{0,60})', texto)
    if m: dados["vara"] = m.group(1).strip()[:80]; dados["_extraidos"].append("vara")
    m = re.search(r'[Cc]omarca\s+(?:de\s+)?([\w\s]+?)(?:\n|,|\.|\s{2})', texto)
    if m: dados["comarca"] = m.group(1).strip()[:40]; dados["_extraidos"].append("comarca")

    # Avaliação
    for p in [r'avaliado\s+em\s+R?\$?\s*([\d.,]+)',
              r'valor\s+de\s+avalia[çc][ãa]o[:\s]*R?\$?\s*([\d.,]+)',
              r'laudo\s+de\s+avalia[çc][ãa]o[^\n]{0,30}R?\$?\s*([\d.,]+)']:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if v > 1000: dados["avaliacao"] = v; dados["_extraidos"].append("avaliacao"); break

    # 1ª Praça — valor da avaliação
    for p in [r'[Pp]rimeira\s+[Pp]ra[çc]a[:\s]*R?\$?\s*([\d.,]+)',
              r'1[aª°]\s*[Pp]ra[çc]a[:\s]*R?\$?\s*([\d.,]+)',
              r'[Ll]ance\s+m[íi]nimo[:\s]*R?\$?\s*([\d.,]+)']:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if v > 1000: dados["lance_1praca"] = v; dados["_extraidos"].append("lance_1praca"); break

    # 2ª Praça — geralmente 60% da avaliação ou valor explícito
    for p in [r'[Ss]egunda\s+[Pp]ra[çc]a[:\s]*R?\$?\s*([\d.,]+)',
              r'2[aª°]\s*[Pp]ra[çc]a[:\s]*R?\$?\s*([\d.,]+)']:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if v > 1000: dados["lance_2praca"] = v; dados["_extraidos"].append("lance_2praca"); break

    # Se 2ª praça não encontrada mas avaliação sim, calcula 60%
    if dados.get("avaliacao") and not dados.get("lance_2praca"):
        if re.search(r'60%|sessenta\s+por\s+cento', texto, re.I):
            dados["lance_2praca"] = dados["avaliacao"] * 0.60
            dados["_extraidos"].append("lance_2praca")
            dados["_avisos"].append("ℹ 2ª Praça calculada como 60% da avaliação (padrão judicial)")

    # Datas — formato extenso "DD de mês de AAAA"
    MESES = {'janeiro':'01','fevereiro':'02','março':'03','abril':'04',
              'maio':'05','junho':'06','julho':'07','agosto':'08',
              'setembro':'09','outubro':'10','novembro':'11','dezembro':'12'}

    def converter_data_extenso(texto_data: str) -> str:
        m = re.match(r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', texto_data, re.I)
        if m:
            dia, mes_nome, ano = m.groups()
            mes = MESES.get(mes_nome.lower(), '??')
            return f"{int(dia):02d}/{mes}/{ano}"
        return texto_data

    for p_ctx, campo in [
        (r'[Pp]rimeira\s+[Pp]ra[çc]a', 'data_1praca'),
        (r'[Ss]egunda\s+[Pp]ra[çc]a', 'data_2praca'),
        (r'1[aª°]\s*[Pp]ra[çc]a', 'data_1praca'),
        (r'2[aª°]\s*[Pp]ra[çc]a', 'data_2praca'),
    ]:
        m = re.search(
            p_ctx + r'[^\d]{0,40}(\d{1,2}\s+de\s+\w+\s+de\s+\d{4}|\d{2}\/\d{2}\/\d{4})',
            texto, re.I
        )
        if m and not dados.get(campo):
            data_raw = m.group(1)
            dados[campo] = converter_data_extenso(data_raw) if 'de' in data_raw else data_raw
            dados["_extraidos"].append(campo)

    # Área
    for p in [r'[áa]rea\s+[úu]til\s+de\s+([\d.,]+)\s*m',
              r'com\s+[áa]rea\s+de\s+([\d.,]+)\s*m',
              r'([\d.,]+)\s*m[²2]\s*de\s+[áa]rea']:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if 10 < v < 5000: dados["area_util"] = v; dados["_extraidos"].append("area_util"); break

    # Débitos
    m = re.search(r'IPTU[^\n]{0,60}R?\$?\s*([\d.,]+)', texto, re.I)
    if m:
        v = limpar_valor(m.group(1))
        if 0 < v < 500_000: dados["iptu_debito"] = v; dados["_extraidos"].append("iptu_debito")

    m = re.search(r'condom[íi]nio[^\n]{0,60}R?\$?\s*([\d.,]+)', texto, re.I)
    if m:
        v = limpar_valor(m.group(1))
        if 0 < v < 500_000: dados["cond_debito"] = v; dados["_extraidos"].append("cond_debito")

    # Sub-rogação — avisa que débitos passam ao comprador
    if re.search(r'sub-?roga[çc][ãa]o|débitos\s+(?:propter\s+rem\s+)?(?:pass|transfer)', texto, re.I):
        dados["_avisos"].append("⚖ JUDICIAL: Verificar se há sub-rogação de débitos (IPTU/condomínio) ao arrematante")


def _parse_zuk(texto: str, dados: dict):
    """Zuk Leilões."""
    dados["leiloeira_nome"] = "Zuk Leilões"
    dados["tipo_leilao"] = "Extrajudicial"

    m = re.search(r'[Vv]alor\s+[Mm][íi]nimo[:\s]*R?\$?\s*([\d.,]+)', texto, re.I)
    if m:
        v = limpar_valor(m.group(1))
        if v > 1000: dados["lance_1praca"] = v; dados["_extraidos"].append("lance_1praca")

    m = re.search(r'[Áá]rea\s+[úu]til[:\s]*([\d.,]+)\s*m', texto, re.I)
    if m: dados["area_util"] = limpar_valor(m.group(1)); dados["_extraidos"].append("area_util")

    m = re.search(r'[Vv]alor\s+de\s+[Aa]valia[çc][ãa]o[:\s]*R?\$?\s*([\d.,]+)', texto, re.I)
    if m:
        v = limpar_valor(m.group(1))
        if v > 1000: dados["avaliacao"] = v; dados["_extraidos"].append("avaliacao")

    m = re.search(r'[Dd]ata[:\s]*(\d{2}\/\d{2}\/\d{4})', texto, re.I)
    if m: dados["data_leilao"] = m.group(1); dados["data_1praca"] = m.group(1); dados["_extraidos"].append("data_leilao")


# ─────────────────────────────────────────────
#  PARSER GENÉRICO (fallback universal)
# ─────────────────────────────────────────────

def _parse_generico(texto: str, dados: dict):
    """Fallback para leiloeiras não reconhecidas."""
    dados["leiloeira_nome"] = "Leiloeira não identificada"
    dados["tipo_leilao"] = "Não identificado"

    # Área útil — múltiplos padrões
    AREA_UTIL_PATTERNS = [
        r'[áa]rea\s+[úu]til\s+de\s+([\d.,]+)\s*m[²2]?',
        r'[áa]rea\s+(?:[úu]til|privativa)[:\s]*([\d.,]+)\s*m[²2]?',
        r'([\d.,]+)\s*m[²2]\s*(?:de\s+)?(?:[áa]rea\s+)?(?:[úu]til|privativa)',
        r'[áa]rea\s+[úu]til[:\s=]+([\d.,]+)',
        r'ÁREA[:\s]+([\d.,]+)\s*m[²2]?',
    ]
    for p in AREA_UTIL_PATTERNS:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if 10 < v < 5000: dados["area_util"] = v; dados["_extraidos"].append("area_util"); break

    # Área total
    AREA_TOT_PATTERNS = [
        r'[áa]rea\s+total\s+de\s+([\d.,]+)\s*m[²2]?',
        r'[áa]rea\s+total[:\s]*([\d.,]+)\s*m[²2]?',
        r'[áa]rea\s+construída[:\s]*([\d.,]+)\s*m[²2]?',
        r'([\d.,]+)\s*m[²2]\s*(?:de\s+)?[áa]rea\s+total',
    ]
    for p in AREA_TOT_PATTERNS:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if 10 < v < 5000: dados["area_total"] = v; dados["_extraidos"].append("area_total"); break

    # Avaliação
    AVAL_PATTERNS = [
        r'[Vv]alor\s+de\s+[Aa]valia[çc][ãa]o[:\s]*R?\$?\s*([\d.]+,\d{2})',
        r'[Aa]valia[çc][ãa]o[:\s]*R?\$?\s*([\d.]+,\d{2})',
        r'avaliado\s+(?:em|por)[:\s]*R?\$?\s*([\d.]+,\d{2})',
        r'[Vv]alor\s+[Vv]enal[:\s]*R?\$?\s*([\d.]+,\d{2})',
        r'[Vv]alor\s+de\s+[Mm]ercado[:\s]*R?\$?\s*([\d.]+,\d{2})',
    ]
    for p in AVAL_PATTERNS:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if v > 1000: dados["avaliacao"] = v; dados["_extraidos"].append("avaliacao"); break

    # Lance — sem lance na plataforma, tenta tudo
    if not dados.get("lance_na_plataforma"):
        LANCE_PATTERNS = [
            r'[Ll]ance\s+(?:[Mm][íi]nimo|[Ii]nicial)[:\s]*R?\$?\s*([\d.]+,\d{2})',
            r'LANCE\s+M[ÍI]NIMO[:\s]*R?\$?\s*([\d.]+,\d{2})',
            r'[Vv]alor\s+[Mm][íi]nimo[:\s]*R?\$?\s*([\d.]+,\d{2})',
            r'[Pp]re[çc]o\s+[Mm][íi]nimo[:\s]*R?\$?\s*([\d.]+,\d{2})',
            r'1[aª°]\s*[Pp]ra[çc]a[:\s]*R?\$?\s*([\d.]+,\d{2})',
            r'[Pp]rimeira\s+[Pp]ra[çc]a[:\s]*R?\$?\s*([\d.]+,\d{2})',
        ]
        for p in LANCE_PATTERNS:
            m = re.search(p, texto, re.I)
            if m:
                v = limpar_valor(m.group(1))
                if v > 1000: dados["lance_1praca"] = v; dados["_extraidos"].append("lance_1praca"); break

        LANCE2_PATTERNS = [
            r'2[aª°]\s*[Pp]ra[çc]a[:\s]*R?\$?\s*([\d.]+,\d{2})',
            r'[Ss]egunda\s+[Pp]ra[çc]a[:\s]*R?\$?\s*([\d.]+,\d{2})',
        ]
        for p in LANCE2_PATTERNS:
            m = re.search(p, texto, re.I)
            if m:
                v = limpar_valor(m.group(1))
                if v > 1000: dados["lance_2praca"] = v; dados["_extraidos"].append("lance_2praca"); break

    # Datas
    DATA_CTX = [
        (r'1[aª°]\s*[Pp]ra[çc]a|[Pp]rimeira\s+[Pp]ra[çc]a', 'data_1praca'),
        (r'2[aª°]\s*[Pp]ra[çc]a|[Ss]egunda\s+[Pp]ra[çc]a',  'data_2praca'),
        (r'[Dd]ata\s+do\s+[Ll]eilão|[Ll]eilão\s+[Rr]ealiz',  'data_leilao'),
        (r'encerrando.se|[Ee]ncerramento',                     'data_leilao'),
    ]
    DATA_RE = r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'
    for ctx, campo in DATA_CTX:
        if not dados.get(campo):
            m = re.search(ctx + r'[^\d]{0,40}' + DATA_RE, texto, re.I)
            if m: dados[campo] = m.group(1); dados["_extraidos"].append(campo)

    # Comissão
    COM_PATTERNS = [
        r'comiss[ãa]o[^\n]{0,30}(\d+(?:[,\.]\d+)?)\s*%',
        r'(\d+(?:[,\.]\d+)?)\s*%[^\n]{0,30}comiss[ãa]o',
        r'(\d+)\s*%\s*\([^)]*(?:cinco|dez|três)[^)]*\)',
    ]
    for p in COM_PATTERNS:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if 0 < v <= 20: dados["comissao_pct"] = v; dados["_extraidos"].append("comissao_pct"); break

    # IPTU
    IPTU_PATTERNS = [
        r'IPTU[^\n]{0,50}R?\$?\s*([\d.]+,\d{2})',
        r'[Dd]ébito[s]?\s+(?:de\s+)?IPTU[:\s]*R?\$?\s*([\d.]+,\d{2})',
        r'imposto\s+(?:predial|territorial)[^\n]{0,30}R?\$?\s*([\d.]+,\d{2})',
    ]
    for p in IPTU_PATTERNS:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if 0 < v < 500_000: dados["iptu_debito"] = v; dados["_extraidos"].append("iptu_debito"); break

    # Condomínio
    COND_PATTERNS = [
        r'[Cc]ondom[íi]nio[^\n]{0,50}R?\$?\s*([\d.]+,\d{2})',
        r'[Dd]ébito[s]?\s+(?:de\s+)?[Cc]ondom[íi]nio[:\s]*R?\$?\s*([\d.]+,\d{2})',
        r'[Ee]ncargo[s]?\s+condominiais?[^\n]{0,30}R?\$?\s*([\d.]+,\d{2})',
    ]
    for p in COND_PATTERNS:
        m = re.search(p, texto, re.I)
        if m:
            v = limpar_valor(m.group(1))
            if 0 < v < 500_000: dados["cond_debito"] = v; dados["_extraidos"].append("cond_debito"); break


# ─────────────────────────────────────────────
#  PARSER UNIVERSAL — CAMPOS COMUNS
# ─────────────────────────────────────────────

def _parse_campos_comuns(texto: str, dados: dict):
    """Campos que são comuns a todos os formatos."""

    # ── Endereço ──
    END_PATTERNS = [
        r'LOCALIZA[ÇC][ÃA]O[:\s]+([^\n]{10,150})',
        r'(?:Rua|Av\.?|Avenida|Alameda|Travessa|Estrada|Al\.|R\.)\s+[^\n,]{5,80},?\s*n[°º]?\s*\d+[^\n]{0,60}',
        r'LOTE[:\s]+[^\n]{10,150}',
        r'[Ii]móvel[:\s]+(?:localizado\s+(?:à|na|no|em)\s+)?([^\n]{10,120})',
        r'[Ss]ituado\s+(?:à|na|no|em)\s+([^\n]{10,120})',
    ]
    if not dados.get("endereco"):
        for p in END_PATTERNS:
            m = re.search(p, texto, re.I)
            if m:
                end = m.group(0) if not m.lastindex else m.group(1)
                dados["endereco"] = end.strip()[:200]
                dados["_extraidos"].append("endereco")
                break

    # ── Matrícula ──
    if not dados.get("matricula"):
        for p in [r'[Mm]atrícula\s+n[°º.]?\s*([\d.]+)',
                  r'[Mm]atrícula\s+nº\s*([\d.,]+)',
                  r'[Mm]at\.\s+n[°º.]?\s*([\d.]+)']:
            m = re.search(p, texto, re.I)
            if m: dados["matricula"] = m.group(1).strip(); dados["_extraidos"].append("matricula"); break

    # ── Flags ──
    if re.search(r'["\']?\s*[Aa][Dd]\s+[Cc][Oo][Rr][Pp][Uu][Ss]\s*["\']?', texto):
        dados["ad_corpus"] = True
        if "ad_corpus" not in dados["_extraidos"]: dados["_extraidos"].append("ad_corpus")

    COND_PATTERNS = [
        r'VENDA\s+DIRETA\s+CONDICIONADA',
        r'MAIOR\s+LANCE\s+(?:OU\s+OFERTA\s+)?CONDICIONAD[AO]',
        r'condicionad[ao]\s+(?:à|a)\s+(?:exclusivo\s+)?crit[eé]rio',
        r'[Vv]enda\s+[Ss]ujeita\s+(?:à|a)\s+[Aa]provação',
        r'[Hh]omologa[çc][ãa]o\s+condicionada',
    ]
    for p in COND_PATTERNS:
        if re.search(p, texto, re.I):
            dados["venda_condicionada"] = True
            if "venda_condicionada" not in dados["_extraidos"]: dados["_extraidos"].append("venda_condicionada")
            break

    # ── Comissão (se ainda não encontrada) ──
    if not dados.get("comissao_pct") or dados["comissao_pct"] == 5.0:
        for p in [r'(\d+)\s*%\s*\([^)]*cinco[^)]*\)',
                  r'comiss[ãa]o\s+de\s+(\d+)\s*%',
                  r'(\d+)\s*%\s*[^\n]{0,20}comiss[ãa]o']:
            m = re.search(p, texto, re.I)
            if m:
                v = limpar_valor(m.group(1))
                if 0 < v <= 20: dados["comissao_pct"] = v; break

    # ── Plataforma ──
    PLATAFORMAS = {
        "bcoleiloes.com.br": "bcoleiloes",
        "sold.com.br":       "sold",
        "superbid.net":      "superbid",
        "lancelance.com.br": "lance & lance",
        "zuk.com.br":        "zuk",
        "jeff.com.br":       "jeff",
    }
    for url, nome in PLATAFORMAS.items():
        if url.split('.')[0] in texto.lower():
            dados["plataforma"] = url
            dados["_extraidos"].append("plataforma")
            break

    # ── Débitos propter rem genérico ──
    if re.search(r'[Vv][Ee][Nn][Dd][Ee][Dd][Oo][Rr][Aa]\s+ser[áa]\s+respons[áa]vel'
                 r'[^\n]{0,80}(?:propter\s+rem|IPTU|condominiais)', texto, re.I):
        dados["_avisos"].append("✅ IPTU e condomínio: responsabilidade da VENDEDORA confirmada no edital")
        if "debitos_vendedora_confirmado" not in dados["_extraidos"]:
            dados["_extraidos"].append("debitos_vendedora_confirmado")


# ─────────────────────────────────────────────
#  FUNÇÃO PRINCIPAL
# ─────────────────────────────────────────────

def parse_edital(texto: str) -> dict:
    """
    Parser universal de editais de leilão.
    Detecta a leiloeira e aplica parser especializado + campos comuns.
    """
    dados = {
        # Identificação
        "leiloeira_nome": "", "tipo_leilao": "", "plataforma": "",
        "numero_processo": "", "matricula": "", "comarca": "", "vara": "",
        # Imóvel
        "endereco": "", "area_util": 0.0, "area_total": 0.0,
        # Financeiro
        "avaliacao": 0.0, "lance_1praca": 0.0, "lance_2praca": 0.0,
        "comissao_pct": 5.0, "itbi_pct": 3.0,
        # Datas
        "data_leilao": "", "data_1praca": "", "data_2praca": "",
        # Débitos
        "iptu_debito": 0.0, "cond_debito": 0.0,
        # Flags
        "ad_corpus": False, "venda_condicionada": False,
        "lance_na_plataforma": False,
        # Metadata
        "_extraidos": [], "_avisos": [],
    }

    # 1. Detectar leiloeira
    leiloeira = detectar_leiloeira(texto)
    dados["_leiloeira_key"] = leiloeira

    # 2. Parser especializado
    parsers = {
        "bco":         _parse_bco,
        "sold":        _parse_sold,
        "sold_imoveis":_parse_sold,
        "superbid":    _parse_superbid,
        "lance_lance": _parse_lance_lance,
        "tjsp":        _parse_tjsp,
        "zuk":         _parse_zuk,
        "jeff":        _parse_zuk,       # Zuk e Jeff têm formato similar
        "sodresantoro":_parse_lance_lance, # similar ao Lance & Lance
        "generico":    _parse_generico,
    }
    parsers.get(leiloeira, _parse_generico)(texto, dados)

    # 3. Campos comuns (complementa o que o especializado não pegou)
    _parse_campos_comuns(texto, dados)

    # 4. Fallback genérico para campos ainda vazios
    if not dados.get("area_util") or not dados.get("endereco"):
        _parse_generico(texto, dados)

    # 5. Consistência: se área total < útil, corrige
    if dados.get("area_total") and dados.get("area_util"):
        if dados["area_total"] < dados["area_util"]:
            dados["area_util"], dados["area_total"] = dados["area_total"], dados["area_util"]

    # 6. Aviso de campos não extraídos
    campos_criticos = ["area_util", "lance_1praca", "endereco"]
    faltando = [c for c in campos_criticos if not dados.get(c)]
    if faltando:
        dados["_avisos"].append(
            f"⚠ Campos não extraídos automaticamente: {', '.join(faltando)}. "
            f"Preencha manualmente na sidebar."
        )

    return dados
