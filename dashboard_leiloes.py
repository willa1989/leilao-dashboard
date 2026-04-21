"""
LEILÃO INTEL v3.0 — PDF Intelligence Engine
Wealth Management | Real Estate Due Diligence
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import re
import io
from scipy.optimize import brentq

# ── Imports opcionais (PDF) ──────────────────
try:
    import pdfplumber
    PDF_OK = True
except ImportError:
    PDF_OK = False

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="LEILÃO INTEL v3 · PDF Engine",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Syne:wght@400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #060a0e !important;
    color: #c8d8e8 !important;
    font-family: 'Syne', sans-serif;
}
[data-testid="stSidebar"] {
    background: #080c12 !important;
    border-right: 1px solid #1a2635;
}
[data-testid="stHeader"] { background: transparent !important; }

h1,h2,h3 { font-family:'Syne',sans-serif; font-weight:800; }
h1 { color:#e8f4ff; letter-spacing:-1px; }

/* Upload zone */
[data-testid="stFileUploader"] {
    border: 1px dashed #1e4a6a !important;
    border-radius: 6px !important;
    background: #080f18 !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #2a7aaa !important;
    background: #0a1520 !important;
}

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg,#0d1820 0%,#0a1520 100%);
    border:1px solid #1e3448; border-top:2px solid;
    border-radius:4px; padding:1.2rem 1.4rem; position:relative; overflow:hidden;
}
.kpi-card::before {
    content:''; position:absolute; top:0;left:0;right:0;bottom:0;
    background:radial-gradient(ellipse at top left,rgba(0,180,255,0.04),transparent 60%);
    pointer-events:none;
}
.kpi-label { font-family:'Share Tech Mono',monospace; font-size:0.62rem;
    letter-spacing:3px; text-transform:uppercase; color:#4a6a8a; margin-bottom:0.4rem; }
.kpi-value { font-family:'Share Tech Mono',monospace; font-size:1.7rem;
    font-weight:600; line-height:1; }
.kpi-sub { font-family:'Share Tech Mono',monospace; font-size:0.68rem;
    color:#4a6a8a; margin-top:0.35rem; }

/* Extracted field badge */
.field-extracted {
    display:inline-block; background:#0a2010; border:1px solid #1a5a2a;
    border-radius:3px; padding:0.1rem 0.5rem;
    font-family:'Share Tech Mono',monospace; font-size:0.6rem;
    color:#4acc88; letter-spacing:2px; margin-left:0.5rem; vertical-align:middle;
}
.field-manual {
    display:inline-block; background:#1a1408; border:1px solid #4a3a08;
    border-radius:3px; padding:0.1rem 0.5rem;
    font-family:'Share Tech Mono',monospace; font-size:0.6rem;
    color:#ccaa44; letter-spacing:2px; margin-left:0.5rem; vertical-align:middle;
}

/* Alerts */
.alert-orange {
    background:linear-gradient(135deg,#1a0f08,#1f1408);
    border:1px solid #ff6b35; border-left:4px solid #ff6b35;
    border-radius:4px; padding:0.9rem 1.2rem; margin:0.8rem 0;
    font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:#ff9a6b;
}
.alert-blue {
    background:linear-gradient(135deg,#0a0f1a,#0d1520);
    border:1px solid #4488cc; border-left:4px solid #4488cc;
    border-radius:4px; padding:0.9rem 1.2rem; margin:0.8rem 0;
    font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:#88bbdd;
}
.alert-purple {
    background:linear-gradient(135deg,#0f0a14,#140f1a);
    border:1px solid #aa55ff; border-left:4px solid #aa55ff;
    border-radius:4px; padding:0.9rem 1.2rem; margin:0.8rem 0;
    font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:#cc99ff;
}
.alert-green {
    background:linear-gradient(135deg,#081408,#0a1a0a);
    border:1px solid #22aa55; border-left:4px solid #22aa55;
    border-radius:4px; padding:0.9rem 1.2rem; margin:0.8rem 0;
    font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:#55cc88;
}
.alert-red {
    background:linear-gradient(135deg,#180808,#1a0a0a);
    border:1px solid #cc2244; border-left:4px solid #cc2244;
    border-radius:4px; padding:0.9rem 1.2rem; margin:0.8rem 0;
    font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:#ff6688;
}

/* Recommendation box */
.rec-box {
    border-radius:6px; padding:1.5rem 2rem; margin:1rem 0;
    font-family:'Share Tech Mono',monospace;
}
.rec-esperar {
    background:linear-gradient(135deg,#081408,#0a1a0a);
    border:2px solid #22aa55;
}
.rec-lancar {
    background:linear-gradient(135deg,#0a0f1a,#0d1520);
    border:2px solid #2a7aaa;
}
.rec-cautela {
    background:linear-gradient(135deg,#1a1408,#1f1a08);
    border:2px solid #ffaa33;
}

.section-header {
    font-family:'Share Tech Mono',monospace; font-size:0.62rem;
    letter-spacing:4px; text-transform:uppercase; color:#2a4a6a;
    border-bottom:1px solid #1a2e42; padding-bottom:0.4rem; margin:1.2rem 0 0.8rem;
}

/* PDF status bar */
.pdf-status {
    background:#0a1a0a; border:1px solid #1a4a2a; border-radius:4px;
    padding:0.8rem 1.2rem; margin:0.8rem 0;
    font-family:'Share Tech Mono',monospace; font-size:0.72rem; color:#4acc88;
}

[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background:#0d1820 !important; border:1px solid #1e3448 !important;
    border-radius:3px !important; color:#c8d8e8 !important;
    font-family:'Share Tech Mono',monospace !important;
}
.stButton>button {
    background:linear-gradient(135deg,#0a2840,#0d3050) !important;
    border:1px solid #1e5a88 !important; color:#88ccff !important;
    font-family:'Share Tech Mono',monospace !important;
    letter-spacing:2px !important; font-size:0.72rem !important;
    border-radius:3px !important;
}
.stButton>button:hover {
    background:linear-gradient(135deg,#0d3050,#103860) !important;
    border-color:#2a7aaa !important;
}
[data-testid="stSelectbox"]>div>div {
    background:#0d1820 !important; border:1px solid #1e3448 !important;
    color:#c8d8e8 !important; font-family:'Share Tech Mono',monospace !important;
}
.stTabs [data-baseweb="tab-list"] {
    background:#080c12 !important; border-bottom:1px solid #1a2e42; gap:0;
}
.stTabs [data-baseweb="tab"] {
    font-family:'Share Tech Mono',monospace !important; font-size:0.68rem !important;
    letter-spacing:2px !important; color:#4a6a8a !important;
    border-radius:0 !important; padding:0.6rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
    color:#88ccff !important; border-bottom:2px solid #2a7aaa !important;
    background:transparent !important;
}
[data-testid="stSidebar"] label {
    font-family:'Share Tech Mono',monospace !important;
    font-size:0.68rem !important; letter-spacing:1px !important;
    color:#4a6a8a !important; text-transform:uppercase;
}
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:#060a0e; }
::-webkit-scrollbar-thumb { background:#1e3448; border-radius:2px; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060a0e",
    font=dict(family="Share Tech Mono, monospace", color="#7a9ab8", size=11),
    title_font=dict(family="Syne, sans-serif", color="#a8c8e8", size=13),
    xaxis=dict(gridcolor="#0f1e2e", linecolor="#1a2e42", tickcolor="#1a2e42", zerolinecolor="#1a2e42"),
    yaxis=dict(gridcolor="#0f1e2e", linecolor="#1a2e42", tickcolor="#1a2e42", zerolinecolor="#1a2e42"),
    margin=dict(l=40, r=20, t=45, b=35),
)

# ─────────────────────────────────────────────
#  PDF EXTRACTION ENGINE
# ─────────────────────────────────────────────

def limpar_valor(texto: str) -> float:
    """Converte string monetária brasileira para float."""
    if not texto:
        return 0.0
    t = re.sub(r'[R$\s]', '', str(texto))
    t = t.replace('.', '').replace(',', '.')
    try:
        return float(re.search(r'\d+\.?\d*', t).group())
    except Exception:
        return 0.0

def extrair_valor_monetario(texto: str, padrao: str) -> tuple[float, str]:
    """Extrai valor monetário do texto usando regex."""
    matches = re.findall(
        padrao + r'[\s:]*R?\$?\s*([\d.,]+)',
        texto, re.IGNORECASE
    )
    if matches:
        raw = matches[0]
        return limpar_valor(raw), raw
    return 0.0, ""

def extrair_texto_pdf(arquivo_bytes: bytes) -> str:
    """Extrai texto completo do PDF."""
    if not PDF_OK:
        return ""
    try:
        with pdfplumber.open(io.BytesIO(arquivo_bytes)) as pdf:
            texto = ""
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texto += t + "\n"
        return texto
    except Exception as e:
        return ""

def parse_edital(texto: str) -> dict:
    """
    Parser inteligente v2 — suporta BCO Leilões, Sold, Superbid,
    Lance&Lance, editais judiciais e extrajudiciais.
    """
    dados = {
        "endereco": "", "area_util": 0.0, "area_total": 0.0,
        "avaliacao": 0.0, "lance_1praca": 0.0, "lance_2praca": 0.0,
        "data_leilao": "", "data_1praca": "", "data_2praca": "",
        "comissao_pct": 5.0, "itbi_pct": 3.0,
        "iptu_debito": 0.0, "cond_debito": 0.0,
        "matricula": "", "comarca": "", "vara": "",
        "ad_corpus": False, "venda_condicionada": False,
        "numero_processo": "", "leiloeira": "", "plataforma": "",
        "lance_na_plataforma": False,  # flag BCO/Sold: lance só no site
        "_extraidos": [],
        "_avisos": [],  # avisos para o usuário
    }

    # ── Detectar leiloeira / plataforma ──
    if re.search(r'bcoleil[oõ]es', texto, re.IGNORECASE):
        dados["plataforma"] = "bcoleiloes.com.br"
        dados["_extraidos"].append("plataforma")
    if re.search(r'sold\s*leil', texto, re.IGNORECASE):
        dados["plataforma"] = "sold.com.br"
        dados["_extraidos"].append("plataforma")
    if re.search(r'superbid', texto, re.IGNORECASE):
        dados["plataforma"] = "superbid.net"
        dados["_extraidos"].append("plataforma")

    # Detectar padrão "lance será disponibilizado na plataforma" (BCO Leilões)
    if re.search(r'lance\s+(?:inicial\s+)?(?:do\s+imóvel\s+)?(?:deste\s+leilão\s+)?será\s+(?:aquele\s+)?(?:estipulado|disponibilizado)',
                 texto, re.IGNORECASE):
        dados["lance_na_plataforma"] = True
        dados["_avisos"].append(
            "⚠ LANCE INICIAL não consta no edital — consulte a plataforma "
            + (dados["plataforma"] or "do leiloeiro") + " e insira manualmente."
        )

    # ── Leiloeira ──
    lei_p = r'leiloeira?\s+oficial[:\s]+([^\n,\.]{5,60})'
    m = re.search(lei_p, texto, re.IGNORECASE)
    if m:
        dados["leiloeira"] = m.group(1).strip()
        dados["_extraidos"].append("leiloeira")

    # ── Endereço — múltiplas estratégias ──
    # Estratégia 1: padrão "LOCALIZAÇÃO: ..."
    m = re.search(r'LOCALIZA[ÇC][ÃA]O[:\s]+([^\n]{10,120})', texto, re.IGNORECASE)
    if m:
        dados["endereco"] = m.group(1).strip()
        dados["_extraidos"].append("endereco")
    else:
        # Estratégia 2: linha com rua/avenida + número
        m = re.search(
            r'(?:Rua|Av\.?|Avenida|Alameda|Travessa|Estrada|Al\.)\s+[^\n,]{5,60},?\s*n[°º]?\s*\d+[^\n]{0,60}',
            texto, re.IGNORECASE)
        if m:
            dados["endereco"] = m.group(0).strip()[:150]
            dados["_extraidos"].append("endereco")
        else:
            # Estratégia 3: após LOTE / imóvel descrito
            m = re.search(r'LOTE[:\s]+[^\n]{10,150}', texto, re.IGNORECASE)
            if m:
                dados["endereco"] = m.group(0).strip()[:150]
                dados["_extraidos"].append("endereco")

    # ── Área útil — prioridade para "área útil de X m²" ──
    area_util_patterns = [
        r'área\s+útil\s+de\s+([\d.,]+)\s*m[²2]?',
        r'área\s+(?:útil|privativa)[:\s]*([\d.,]+)\s*m[²2]?',
        r'([\d.,]+)\s*m[²2]\s*,?\s*(?:de\s+)?área\s+(?:útil|privativa)',
    ]
    for p in area_util_patterns:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            v = limpar_valor(m.group(1))
            if v > 0:
                dados["area_util"] = v
                dados["_extraidos"].append("area_util")
                break

    # ── Área total ──
    area_total_patterns = [
        r'área\s+total\s+de\s+([\d.,]+)\s*m[²2]?',
        r'área\s+total[:\s]*([\d.,]+)\s*m[²2]?',
        r'([\d.,]+)\s*m[²2]\s*,?\s*(?:de\s+)?área\s+total',
    ]
    for p in area_total_patterns:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            v = limpar_valor(m.group(1))
            if v > 0:
                dados["area_total"] = v
                dados["_extraidos"].append("area_total")
                break

    # ── Valor de avaliação ──
    aval_patterns = [
        r'valor\s+(?:de\s+)?avalia[çc][ãa]o[:\s]*R?\$?\s*([\d.,]+)',
        r'avalia[çc][ãa]o[:\s]*R?\$?\s*([\d.,]+)',
        r'avaliado\s+(?:em\s+)?R?\$?\s*([\d.,]+)',
        r'valor\s+venal[:\s]*R?\$?\s*([\d.,]+)',
        r'pre[çc]o\s+de\s+avalia[çc][ãa]o[:\s]*R?\$?\s*([\d.,]+)',
    ]
    for p in aval_patterns:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            v = limpar_valor(m.group(1))
            if v > 1000:
                dados["avaliacao"] = v
                dados["_extraidos"].append("avaliacao")
                break

    # ── Lances (só tenta se o valor NÃO está apenas na plataforma) ──
    if not dados["lance_na_plataforma"]:
        p1_patterns = [
            r'1[aª°]\s*pra[çc]a[:\s]*(?:lance\s+m[íi]nimo[:\s]*)?R?\$?\s*([\d.,]+)',
            r'primeira\s+pra[çc]a[:\s]*R?\$?\s*([\d.,]+)',
            r'lance\s+(?:m[íi]nimo\s+)?(?:inicial\s+)?[:\s]*R?\$?\s*([\d.,]+)',
            r'lance\s+inicial\s+de\s+R?\$?\s*([\d.,]+)',
            r'valor\s+m[íi]nimo[:\s]*R?\$?\s*([\d.,]+)',
        ]
        for p in p1_patterns:
            m = re.search(p, texto, re.IGNORECASE)
            if m:
                v = limpar_valor(m.group(1))
                if v > 1000:
                    dados["lance_1praca"] = v
                    dados["_extraidos"].append("lance_1praca")
                    break

        p2_patterns = [
            r'2[aª°]\s*pra[çc]a[:\s]*(?:lance\s+m[íi]nimo[:\s]*)?R?\$?\s*([\d.,]+)',
            r'segunda\s+pra[çc]a[:\s]*R?\$?\s*([\d.,]+)',
        ]
        for p in p2_patterns:
            m = re.search(p, texto, re.IGNORECASE)
            if m:
                v = limpar_valor(m.group(1))
                if v > 1000:
                    dados["lance_2praca"] = v
                    dados["_extraidos"].append("lance_2praca")
                    break

    # ── Data do leilão ──
    data_leilao_p = [
        r'encerrando[- ]se\s+(?:no\s+dia\s+)?([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
        r'dia\s+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})\s+às\s+\d{1,2}\s*horas',
        r'realiza[rç][ãa]o[:\s]+(?:dia\s+)?([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    ]
    for p in data_leilao_p:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            dados["data_leilao"] = m.group(1)
            dados["data_1praca"] = m.group(1)
            dados["_extraidos"].append("data_leilao")
            break

    # ── Matrícula ──
    mat_patterns = [
        r'[Mm]atrícula\s+n[°º.]?\s*([\d.]+)',
        r'[Mm]atrícula\s+nº\s*([\d.]+)',
        r'matr[íi]cula\s*([\d.]+)',
    ]
    for p in mat_patterns:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            dados["matricula"] = m.group(1).strip()
            dados["_extraidos"].append("matricula")
            break

    # ── Cartório / Comarca ──
    cart_p = r'(\d+[°º]?\s*Cart[oó]rio\s+de\s+Registro\s+de\s+Im[oó]veis[^\n,\.]{0,40})'
    m = re.search(cart_p, texto, re.IGNORECASE)
    if m:
        dados["comarca"] = m.group(1).strip()
        dados["_extraidos"].append("comarca")

    # Foro
    foro_p = r'[Ff]oro\s+(?:[Cc]entral\s+)?(?:da\s+[Cc]idade\s+de\s+)?([\w\s\/]+?)(?:\n|,|\.)'
    m = re.search(foro_p, texto)
    if m:
        dados["vara"] = "Foro: " + m.group(1).strip()[:60]
        dados["_extraidos"].append("vara")

    # ── Processo ──
    proc_p = r'[Pp]rocesso\s+(?:n[°º.]?\s*)?([\d.\-\/]+\-[\d.\/]+)'
    m = re.search(proc_p, texto)
    if m:
        dados["numero_processo"] = m.group(1)
        dados["_extraidos"].append("numero_processo")

    # ── IPTU / Condomínio ──
    # Verificar se há débitos com valores concretos
    iptu_p = [
        r'IPTU[^\n]{0,30}R?\$?\s*([\d.,]+)',
        r'd[ée]bito[s]?\s+(?:de\s+)?IPTU[:\s]*R?\$?\s*([\d.,]+)',
    ]
    for p in iptu_p:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            v = limpar_valor(m.group(1))
            if 100 < v < 500_000:  # filtro sanidade
                dados["iptu_debito"] = v
                dados["_extraidos"].append("iptu_debito")
                break

    cond_p = [
        r'condom[íi]nio[^\n]{0,30}R?\$?\s*([\d.,]+)',
        r'd[ée]bito[s]?\s+(?:de\s+)?condom[íi]nio[:\s]*R?\$?\s*([\d.,]+)',
    ]
    for p in cond_p:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            v = limpar_valor(m.group(1))
            if 100 < v < 500_000:
                dados["cond_debito"] = v
                dados["_extraidos"].append("cond_debito")
                break

    # Detectar se a VENDEDORA é responsável pelos débitos propter rem
    if re.search(r'VENDEDORA\s+ser[aá]\s+respons[aá]vel\s+pelo\s+pagamento\s+de\s+todos\s+os\s+d[eé]bitos\s+propter\s+rem',
                 texto, re.IGNORECASE):
        dados["_avisos"].append(
            "✅ IPTU e condomínio: responsabilidade da VENDEDORA até pagamento (cláusula 4.1)"
        )
        dados["_extraidos"].append("debitos_vendedora_confirmado")

    # ── Ad Corpus ──
    if re.search(r'["\']?[Aa][Dd]\s+[Cc][Oo][Rr][Pp][Uu][Ss]["\']?', texto):
        dados["ad_corpus"] = True
        dados["_extraidos"].append("ad_corpus")

    # ── Venda Condicionada ──
    if re.search(r'(?:VENDA\s+DIRETA\s+)?CONDICIONAD[AO]\s+[AÀ]\s+APROVA[ÇC][ÃA]O|'
                 r'MAIOR\s+LANCE\s+OU\s+OFERTA\s+CONDICIONAD[AO]|'
                 r'condicionad[ao]\s+(?:à|a)\s+(?:exclusivo\s+)?crit[eé]rio',
                 texto, re.IGNORECASE):
        dados["venda_condicionada"] = True
        dados["_extraidos"].append("venda_condicionada")

    # ── Comissão ──
    com_pct_patterns = [
        r'(\d+(?:[,\.]\d+)?)\s*%\s*\([^)]*cinco[^)]*por\s*cento[^)]*\)[^\n]{0,30}comiss[ãa]o',
        r'comiss[ãa]o[^\n]{0,50}(\d+(?:[,\.]\d+)?)\s*%',
        r'(\d+)\s*%\s*\([^)]*\)[^\n]{0,20}comiss[ãa]o',
        r'a\s+(?:quantia\s+correspondente\s+a\s+)?(\d+(?:[,\.]\d+)?)\s*%[^\n]{0,30}comiss[ãa]o',
    ]
    for p in com_pct_patterns:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            v = limpar_valor(m.group(1))
            if 0 < v <= 20:
                dados["comissao_pct"] = v
                dados["_extraidos"].append("comissao_pct")
                break

    return dados

# ─────────────────────────────────────────────
#  FINANCIAL ENGINE
# ─────────────────────────────────────────────

def fmt(v: float) -> str:
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calc_escritura(lance: float) -> float:
    if lance <= 50_000:      return 800
    elif lance <= 100_000:   return 1_200
    elif lance <= 250_000:   return 1_800
    elif lance <= 500_000:   return 2_800
    elif lance <= 1_000_000: return 4_500
    else:                    return 7_200

def custo_total(lance, comissao_pct, itbi_pct, outros=0):
    c = lance * comissao_pct / 100
    i = lance * itbi_pct / 100
    e = calc_escritura(lance)
    return dict(lance=lance, comissao=c, itbi=i, escritura=e,
                outros=outros, total=lance + c + i + e + outros)

def vgv(area_adj, m2_medio):
    return area_adj * m2_medio

def lucro_liq(vgv_val, custo):
    gb = vgv_val - custo
    if gb <= 0: return gb, 0, gb
    igc = gb * 0.15
    return gb - igc, igc, gb

def calcular_tir(custo, vgv_val, meses):
    fluxo = [-custo] + [0] * (meses - 1) + [vgv_val]
    def npv(r): return sum(f / (1+r)**t for t, f in enumerate(fluxo))
    try:
        r_m = brentq(npv, -0.99, 10, maxiter=500)
        return (1 + r_m) ** 12 - 1
    except:
        return None

# ─────────────────────────────────────────────
#  ANÁLISE 1ª vs 2ª PRAÇA
# ─────────────────────────────────────────────

def analise_pracas(lance_1, lance_2, avaliacao, vgv_val, comissao_pct, itbi_pct, outros):
    """
    Retorna recomendação fundamentada sobre qual praça atacar.
    """
    if lance_1 == 0 and lance_2 == 0:
        return None

    resultados = {}
    for nome, lance in [("1ª Praça", lance_1), ("2ª Praça", lance_2)]:
        if lance == 0:
            continue
        c = custo_total(lance, comissao_pct, itbi_pct, outros)
        ll, igc, gb = lucro_liq(vgv_val, c["total"])
        roi_val = ll / c["total"] * 100 if c["total"] > 0 else 0
        ms = (1 - c["total"] / vgv_val) * 100 if vgv_val > 0 else 0
        desc_aval = (1 - lance / avaliacao) * 100 if avaliacao > 0 else 0
        tir12 = calcular_tir(c["total"], vgv_val, 12)
        resultados[nome] = dict(
            lance=lance, custo=c["total"], lucro=ll, roi=roi_val,
            margem=ms, desc_aval=desc_aval, tir12=tir12, igc=igc
        )

    if not resultados:
        return None

    # Lógica de recomendação
    rec = {}
    if "1ª Praça" in resultados and "2ª Praça" in resultados:
        r1 = resultados["1ª Praça"]
        r2 = resultados["2ª Praça"]
        ganho_extra = r2["lucro"] - r1["lucro"]
        risco_esperar = 0.35  # probabilidade estimada de concorrência na 2ª praça

        if r1["roi"] >= 25 and r1["margem"] >= 30:
            rec = dict(
                acao="ARREMATAR NA 1ª PRAÇA",
                motivo="ROI e margem de segurança excelentes já na 1ª praça. Não vale o risco de perder para concorrentes na 2ª.",
                cor="blue", ganho_extra=ganho_extra,
            )
        elif r2["roi"] > r1["roi"] + 15 and r1["roi"] < 15:
            rec = dict(
                acao="AGUARDAR A 2ª PRAÇA",
                motivo=f"A 2ª praça melhora o ROI em {r2['roi']-r1['roi']:.1f}pp. O retorno na 1ª praça não justifica o capital.",
                cor="green", ganho_extra=ganho_extra,
            )
        else:
            lance_max = vgv_val / 1.35  # custo máximo para 35% de margem
            rec = dict(
                acao="CAUTELA · AVALIAR LANCE MÁXIMO",
                motivo=f"Lance máximo recomendado para 35% de margem: {fmt(lance_max * 0.88)}",
                cor="yellow", ganho_extra=ganho_extra,
            )
    elif "2ª Praça" in resultados:
        r2 = resultados["2ª Praça"]
        rec = dict(
            acao="SOMENTE 2ª PRAÇA DISPONÍVEL",
            motivo="Analise ROI e margem abaixo.", cor="blue", ganho_extra=0,
        )
    else:
        r1 = resultados["1ª Praça"]
        rec = dict(
            acao="SOMENTE 1ª PRAÇA DISPONÍVEL",
            motivo="Analise ROI e margem abaixo.", cor="blue", ganho_extra=0,
        )

    return dict(resultados=resultados, recomendacao=rec)

# ─────────────────────────────────────────────
#  COMPARÁVEIS SINTÉTICOS
# ─────────────────────────────────────────────

DEMO_COMPS = {
    "Zona Norte – SP":   [8_500, 9_200, 8_800],
    "Zona Sul – SP":     [11_000, 10_500, 12_000],
    "Zona Leste – SP":   [7_200, 7_800, 7_500],
    "Zona Oeste – SP":   [13_500, 14_000, 13_200],
    "ABC Paulista":      [6_800, 7_100, 6_500],
    "Campinas":          [8_200, 8_800, 8_500],
    "Santos / Baixada":  [10_000, 11_500, 10_800],
    "Interior SP":       [5_500, 6_000, 5_800],
}

def get_comps(regiao):
    prices = DEMO_COMPS.get(regiao, [8_000, 8_500, 9_000])
    enderecos = [f"Comparable {i+1} – {regiao}" for i in range(3)]
    comps = []
    for i, p in enumerate(prices):
        area = np.random.randint(55, 130)
        comps.append({"Endereço": enderecos[i], "Área (m²)": area,
                      "Preço Total": p * area, "R$/m²": p})
    return comps

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────

if "dados_edital" not in st.session_state:
    st.session_state.dados_edital = {}
if "pdf_texto" not in st.session_state:
    st.session_state.pdf_texto = ""
if "pdf_nome" not in st.session_state:
    st.session_state.pdf_nome = ""

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style='padding:0.8rem 0 0.3rem'>
        <div style='font-family:Share Tech Mono,monospace;font-size:0.58rem;
                    letter-spacing:4px;color:#2a5a8a;text-transform:uppercase;margin-bottom:0.2rem'>
            Wealth Desk · v3.0</div>
        <div style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:#e8f4ff'>
            LEILÃO INTEL</div>
        <div style='font-family:Share Tech Mono,monospace;font-size:0.62rem;color:#4a7a9a;margin-top:0.1rem'>
            PDF Intelligence Engine</div>
    </div>
    <hr style='border:none;border-top:1px solid #1a2e42;margin:0.8rem 0'>
    """, unsafe_allow_html=True)

    # ── UPLOAD PDF ──
    st.markdown('<div class="section-header">// UPLOAD DO EDITAL (PDF)</div>',
                unsafe_allow_html=True)

    if not PDF_OK:
        st.warning("⚠ pdfplumber não instalado. Adicione ao requirements.txt")

    pdf_file = st.file_uploader(
        "Arraste o edital aqui",
        type=["pdf"],
        help="PDF do edital de leilão — o sistema extrai automaticamente todos os dados"
    )

    if pdf_file and pdf_file.name != st.session_state.pdf_nome:
        with st.spinner("Lendo edital..."):
            pdf_bytes = pdf_file.read()
            texto = extrair_texto_pdf(pdf_bytes)
            if texto:
                dados = parse_edital(texto)
                st.session_state.dados_edital = dados
                st.session_state.pdf_texto = texto
                st.session_state.pdf_nome = pdf_file.name
                n = len(dados["_extraidos"])
                st.success(f"✅ {n} campos extraídos automaticamente!")
                for av in dados.get("_avisos", []):
                    st.warning(av)
                if dados.get("plataforma"):
                    st.info(f"🌐 Plataforma: {dados["plataforma"]}")
            else:
                st.error("Não foi possível ler o PDF. Verifique se não é escaneado.")

    d = st.session_state.dados_edital

    def val(campo, default):
        return d.get(campo, default) if d else default

    def badge(campo):
        if campo in d.get("_extraidos", []):
            return '<span class="field-extracted">AUTO</span>'
        return '<span class="field-manual">MANUAL</span>'

    # ── IDENTIFICAÇÃO ──
    st.markdown('<div class="section-header">// IDENTIFICAÇÃO</div>', unsafe_allow_html=True)
    endereco  = st.text_input("Endereço",   value=val("endereco", ""))
    regiao    = st.selectbox("Região",      list(DEMO_COMPS.keys()))
    matricula = st.text_input("Matrícula",  value=val("matricula", ""))
    comarca   = st.text_input("Comarca",    value=val("comarca", ""))
    processo  = st.text_input("Nº Processo",value=val("numero_processo", ""))

    # ── ÁREAS ──
    st.markdown('<div class="section-header">// ÁREAS</div>', unsafe_allow_html=True)
    area_util    = st.number_input("Área Útil (m²)",  min_value=1.0,
                                   value=float(val("area_util", 80.0)) or 80.0, step=0.5)
    margem_ad    = st.number_input("Margem Ad Corpus (%)", min_value=0.0,
                                   max_value=20.0, value=3.0, step=0.5)

    # ── PRAÇAS ──
    st.markdown('<div class="section-header">// PRAÇAS</div>', unsafe_allow_html=True)
    avaliacao    = st.number_input("Valor de Avaliação (R$)", min_value=0.0,
                                   value=float(val("avaliacao", 0.0)), step=1_000.0)
    lance_1      = st.number_input("Lance Mínimo 1ª Praça (R$)", min_value=0.0,
                                   value=float(val("lance_1praca", 0.0)), step=1_000.0)
    data_1       = st.text_input("Data 1ª Praça", value=val("data_1praca", ""))
    lance_2      = st.number_input("Lance Mínimo 2ª Praça (R$)", min_value=0.0,
                                   value=float(val("lance_2praca", 0.0)), step=1_000.0)
    data_2       = st.text_input("Data 2ª Praça", value=val("data_2praca", ""))

    # ── CUSTOS ──
    st.markdown('<div class="section-header">// CUSTOS & TAXAS</div>', unsafe_allow_html=True)
    comissao_pct = st.number_input("Comissão (%)", min_value=0.0, max_value=10.0,
                                   value=float(val("comissao_pct", 5.0)), step=0.5)
    itbi_pct     = st.number_input("ITBI (%)", min_value=0.0, max_value=10.0,
                                   value=float(val("itbi_pct", 3.0)), step=0.25)
    outros_custos= st.number_input("Outros (reforma, regulariz. R$)",
                                   min_value=0.0, value=0.0, step=500.0)

    # ── DÉBITOS ──
    st.markdown('<div class="section-header">// DÉBITOS PROPTER REM</div>', unsafe_allow_html=True)
    iptu_deb     = st.number_input("IPTU Atrasado (R$) ← vendedora",
                                   min_value=0.0,
                                   value=float(val("iptu_debito", 0.0)), step=100.0)
    cond_deb     = st.number_input("Condomínio Atrasado (R$) ← vendedora",
                                   min_value=0.0,
                                   value=float(val("cond_debito", 0.0)), step=100.0)
    outros_deb   = st.number_input("Outros Débitos (R$) → comprador",
                                   min_value=0.0, value=0.0, step=100.0)

    # ── FLAGS ──
    st.markdown('<div class="section-header">// FLAGS DE RISCO</div>', unsafe_allow_html=True)
    ad_corpus_f  = st.checkbox("⚠ Ad Corpus",          value=bool(val("ad_corpus", False)))
    venda_cond_f = st.checkbox("⚠ Venda Condicionada", value=bool(val("venda_condicionada", False)))

    run = st.button("⬡  ANALISAR EDITAL", use_container_width=True)

# ─────────────────────────────────────────────
#  HEADER PRINCIPAL
# ─────────────────────────────────────────────

col_t, col_tag = st.columns([4, 1])
with col_t:
    st.markdown("""
    <h1 style='margin-bottom:0'>ANÁLISE DE LEILÃO IMOBILIÁRIO</h1>
    <div style='font-family:Share Tech Mono,monospace;font-size:0.68rem;
                color:#2a5a8a;letter-spacing:3px;margin-top:0.2rem'>
        PDF INTELLIGENCE ENGINE · WEALTH MANAGEMENT DESK · v3.0
    </div>""", unsafe_allow_html=True)
with col_tag:
    if st.session_state.pdf_nome:
        st.markdown(f"""
        <div style='text-align:right;padding-top:0.6rem'>
            <div style='display:inline-block;background:#0a2010;border:1px solid #1a5a2a;
                        border-radius:3px;padding:0.3rem 0.8rem;font-family:Share Tech Mono,monospace;
                        font-size:0.62rem;letter-spacing:2px;color:#4acc88'>PDF CARREGADO</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align:right;padding-top:0.6rem'>
            <div style='display:inline-block;background:#0a2840;border:1px solid #1e5a88;
                        border-radius:3px;padding:0.3rem 0.8rem;font-family:Share Tech Mono,monospace;
                        font-size:0.62rem;letter-spacing:2px;color:#4a9acc'>AGUARDANDO PDF</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:1px;background:linear-gradient(90deg,#1a3a5a,transparent);margin:0.4rem 0 1.2rem'></div>",
            unsafe_allow_html=True)

# ── Status do PDF ──
if st.session_state.pdf_nome:
    d_ext = st.session_state.dados_edital
    n_campos = len(d_ext.get("_extraidos", []))
    campos_nomes = ", ".join(d_ext.get("_extraidos", []))
    st.markdown(f"""
    <div class='pdf-status'>
        ✅ EDITAL CARREGADO: {st.session_state.pdf_nome} &nbsp;·&nbsp;
        {n_campos} CAMPOS EXTRAÍDOS AUTOMATICAMENTE &nbsp;·&nbsp;
        {campos_nomes}
    </div>""", unsafe_allow_html=True)

# ── Alerts de risco ──
if venda_cond_f:
    st.markdown("""
    <div class='alert-orange'>
        ⚠ RISCO · VENDA CONDICIONADA — Esta operação está sujeita à aprovação expressa
        do COMITENTE. A homologação pode ser recusada unilateralmente mesmo após o maior lance.
        Consulte o departamento jurídico antes de imobilizar capital.
    </div>""", unsafe_allow_html=True)

if ad_corpus_f:
    area_adj_display = area_util * (1 - margem_ad / 100)
    st.markdown(f"""
    <div class='alert-blue'>
        ℹ AD CORPUS — Imóvel vendido como um todo, sem garantia de metragem exata.
        Margem configurada: {margem_ad:.1f}% → área ajustada para cálculo: {area_adj_display:.1f} m²
    </div>""", unsafe_allow_html=True)

deb_vendedora = iptu_deb + cond_deb
if deb_vendedora > 0:
    st.markdown(f"""
    <div class='alert-purple'>
        ⚖ DÉBITOS PROPTER REM — IPTU + Condomínio ({fmt(deb_vendedora)}) são responsabilidade
        da VENDEDORA até a homologação judicial. Exija quitação como condição precedente.
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ENGINE DE CÁLCULO
# ─────────────────────────────────────────────

# Usar lance mais relevante para KPIs (1ª praça ou 2ª se 1ª = 0)
lance_ref = lance_1 if lance_1 > 0 else lance_2

comps        = get_comps(regiao)
precos_m2    = [c["R$/m²"] for c in comps]
m2_medio     = np.mean(precos_m2)
area_adj     = area_util * (1 - margem_ad / 100)
vgv_val      = vgv(area_adj, m2_medio)

custos_ref   = custo_total(lance_ref, comissao_pct, itbi_pct, outros_custos + outros_deb)
ll_ref, igc_ref, gb_ref = lucro_liq(vgv_val, custos_ref["total"])
roi_ref      = ll_ref / custos_ref["total"] * 100 if custos_ref["total"] > 0 else 0
ms_ref       = (1 - custos_ref["total"] / vgv_val) * 100 if vgv_val > 0 else 0
tir_12       = calcular_tir(custos_ref["total"], vgv_val, 12)
tir_18       = calcular_tir(custos_ref["total"], vgv_val, 18)

analise_p    = analise_pracas(lance_1, lance_2, avaliacao, vgv_val,
                               comissao_pct, itbi_pct, outros_custos + outros_deb)

# ─────────────────────────────────────────────
#  KPI CARDS
# ─────────────────────────────────────────────

def kpi(label, value, sub="", color="#2a7aaa"):
    return f"""<div class='kpi-card' style='border-top-color:{color}'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value' style='color:{color}'>{value}</div>
        <div class='kpi-sub'>{sub}</div></div>"""

lc = "#00cc88" if ll_ref >= 0 else "#ff4455"
rc = "#00cc88" if roi_ref >= 20 else "#ffaa33" if roi_ref >= 10 else "#ff4455"
mc = "#00cc88" if ms_ref >= 25 else "#ffaa33" if ms_ref >= 15 else "#ff4455"

c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.markdown(kpi("CUSTO TOTAL", fmt(custos_ref["total"]),
                          f"Lance ref: {fmt(lance_ref)}", "#4a8acc"), unsafe_allow_html=True)
with c2: st.markdown(kpi("VALOR DE MERCADO", fmt(vgv_val),
                          f"R$/m²: {m2_medio:,.0f} · área: {area_adj:.0f}m²", "#6a9acc"), unsafe_allow_html=True)
with c3: st.markdown(kpi("LUCRO LÍQUIDO", fmt(ll_ref),
                          f"IGC 15%: {fmt(igc_ref)}", lc), unsafe_allow_html=True)
with c4: st.markdown(kpi("ROI ESTIMADO", f"{roi_ref:.1f}%",
                          "Sobre custo total", rc), unsafe_allow_html=True)
with c5: st.markdown(kpi("MARGEM DE SEGURANÇA", f"{ms_ref:.1f}%",
                          "Desconto vs mercado", mc), unsafe_allow_html=True)

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚖  1ª vs 2ª PRAÇA", "📊  COMPARATIVO",
    "💰  CUSTOS & P&L", "📈  TIR & SENSIBILIDADE", "🏠  COMPARÁVEIS"
])

# ────────────────────────────────────
#  TAB 1 · ANÁLISE DE PRAÇAS
# ────────────────────────────────────
with tab1:
    if analise_p is None or (lance_1 == 0 and lance_2 == 0):
        st.markdown("""
        <div class='alert-blue'>
            ℹ Preencha os valores de lance da 1ª e/ou 2ª praça na sidebar para ativar
            a análise comparativa de praças.
        </div>""", unsafe_allow_html=True)
    else:
        res = analise_p["resultados"]
        rec = analise_p["recomendacao"]

        # ── Recomendação ──
        cor_map = {"blue": "rec-lancar", "green": "rec-esperar", "yellow": "rec-cautela"}
        cor_text = {"blue": "#4a9acc", "green": "#22aa55", "yellow": "#ffaa33"}
        cls = cor_map.get(rec["cor"], "rec-cautela")
        ct  = cor_text.get(rec["cor"], "#ffaa33")

        st.markdown(f"""
        <div class='rec-box {cls}'>
            <div style='font-size:0.65rem;letter-spacing:3px;color:{ct};margin-bottom:0.5rem'>
                RECOMENDAÇÃO DO ENGINE</div>
            <div style='font-size:1.2rem;font-weight:700;color:{ct};margin-bottom:0.6rem'>
                {rec["acao"]}</div>
            <div style='font-size:0.78rem;color:#a8c8e8;line-height:1.6'>{rec["motivo"]}</div>
            {"<div style='font-size:0.72rem;color:#6a9a8a;margin-top:0.6rem'>Ganho extra aguardando 2ª praça: " + fmt(rec["ganho_extra"]) + "</div>" if rec["ganho_extra"] != 0 else ""}
        </div>""", unsafe_allow_html=True)

        # ── Tabela comparativa ──
        col_a, col_b = st.columns(2)
        praça_cols = list(res.keys())
        rows = []
        metricas = [
            ("Lance Mínimo",       "lance",    True,  False),
            ("Custo Total",        "custo",    True,  False),
            ("Lucro Líquido",      "lucro",    True,  True),
            ("ROI",                "roi",      False, True),
            ("Margem Segurança",   "margem",   False, True),
            ("Desc. s/ Avaliação", "desc_aval",False, True),
            ("TIR 12 meses",       "tir12",    False, True),
        ]
        for label, campo, is_money, higher_better in metricas:
            row = {"Métrica": label}
            vals = []
            for p in praça_cols:
                v = res[p][campo]
                if campo == "tir12":
                    row[p] = f"{v*100:.1f}%" if v else "N/C"
                    vals.append(v or 0)
                elif is_money:
                    row[p] = fmt(v)
                    vals.append(v)
                else:
                    row[p] = f"{v:.1f}%"
                    vals.append(v)
            rows.append(row)

        df_comp = pd.DataFrame(rows)
        with col_a:
            st.markdown('<div class="section-header">// COMPARATIVO DE PRAÇAS</div>',
                        unsafe_allow_html=True)
            st.dataframe(df_comp, hide_index=True, use_container_width=True)

        # ── Gráfico radar ──
        with col_b:
            if len(res) >= 2:
                cats = ["ROI", "Margem\nSegurança", "Desc.\nAvaliação", "Lucro\nNorm."]
                p_names = list(res.keys())
                lucro_max = max(r["lucro"] for r in res.values()) or 1

                fig = go.Figure()
                colors = ["#2a7aaa", "#22aa55"]
                for i, (pname, rdata) in enumerate(res.items()):
                    vals_radar = [
                        min(rdata["roi"], 100),
                        min(rdata["margem"], 100),
                        min(rdata["desc_aval"], 100),
                        rdata["lucro"] / lucro_max * 100,
                    ]
                    fig.add_trace(go.Scatterpolar(
                        r=vals_radar + [vals_radar[0]],
                        theta=cats + [cats[0]],
                        fill="toself",
                        fillcolor=f"rgba({','.join(str(int(c,16)) for c in [colors[i][1:3],colors[i][3:5],colors[i][5:]])},0.15)",
                        line=dict(color=colors[i], width=2),
                        name=pname,
                    ))
                fig.update_layout(
                    **PLOTLY_LAYOUT,
                    polar=dict(
                        bgcolor="#060a0e",
                        radialaxis=dict(visible=True, range=[0,100],
                                        gridcolor="#0f1e2e", linecolor="#1a2e42",
                                        tickfont=dict(size=8, color="#4a6a8a")),
                        angularaxis=dict(gridcolor="#0f1e2e", linecolor="#1a2e42",
                                         tickfont=dict(size=9, color="#7a9ab8")),
                    ),
                    title="Radar · 1ª vs 2ª Praça",
                    showlegend=True,
                    legend=dict(font=dict(family="Share Tech Mono", size=9, color="#7a9ab8")),
                    height=340,
                )
                st.plotly_chart(fig, use_container_width=True)

        # ── Gráfico de barras comparativo ──
        if len(res) >= 1:
            fig2 = go.Figure()
            p_names = list(res.keys())
            bar_colors = ["#2a7aaa", "#22aa55"]
            metricas_bar = [("Custo Total", "custo"), ("Lucro Líquido", "lucro"),
                            ("VGV Mercado", None)]
            x_labels = []
            for pname in p_names:
                for ml, _ in metricas_bar:
                    x_labels.append(f"{ml}\n{pname}")

            fig2 = go.Figure()
            for i, (pname, rdata) in enumerate(res.items()):
                fig2.add_trace(go.Bar(
                    name=pname,
                    x=["Lance Mínimo", "Custo Total", "Lucro Líquido"],
                    y=[rdata["lance"], rdata["custo"], rdata["lucro"]],
                    marker=dict(color=bar_colors[i],
                                line=dict(color=bar_colors[i], width=1)),
                    text=[fmt(v) for v in [rdata["lance"], rdata["custo"], rdata["lucro"]]],
                    textposition="outside",
                    textfont=dict(family="Share Tech Mono", size=9, color="#a8c8e8"),
                ))

            fig2.add_hline(y=vgv_val, line_dash="dot", line_color="#ffaa33", line_width=1,
                           annotation_text=" VGV Mercado", annotation_font=dict(color="#ffaa33", size=9))
            fig2.update_layout(
                **PLOTLY_LAYOUT,
                title="Lance · Custo · Lucro por Praça",
                barmode="group",
                yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
                showlegend=True,
                legend=dict(font=dict(family="Share Tech Mono", size=9, color="#7a9ab8")),
                height=340,
            )
            st.plotly_chart(fig2, use_container_width=True)

# ────────────────────────────────────
#  TAB 2 · COMPARATIVO
# ────────────────────────────────────
with tab2:
    ca, cb = st.columns([3, 2])
    with ca:
        fig = go.Figure()
        cats   = ["Lance Ref.", "Custo Total\n(c/ taxas)", "Valor Mercado"]
        values = [lance_ref, custos_ref["total"], vgv_val]
        colors = ["#1e5a88", "#2a7aaa", "#00cc88" if vgv_val > custos_ref["total"] else "#ff4455"]
        fig.add_trace(go.Bar(
            x=cats, y=values, marker=dict(color=colors),
            text=[fmt(v) for v in values], textposition="outside",
            textfont=dict(family="Share Tech Mono", size=10, color="#a8c8e8"),
        ))
        fig.add_hline(y=custos_ref["total"], line_dash="dot", line_color="#ffaa33",
                      line_width=1, annotation_text=" breakeven",
                      annotation_font=dict(color="#ffaa33", size=9))
        if avaliacao > 0:
            fig.add_hline(y=avaliacao, line_dash="dash", line_color="#aa55ff",
                          line_width=1, annotation_text=" avaliação oficial",
                          annotation_font=dict(color="#aa55ff", size=9))
        fig.update_layout(**PLOTLY_LAYOUT, title="Lance vs. Custo vs. Mercado",
                          yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
                          showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with cb:
        fig2 = go.Figure(go.Waterfall(
            orientation="v", measure=["absolute","relative","relative","relative","relative","total"],
            x=["Lance", "Comissão", "ITBI", "Escritura", "Outros", "TOTAL"],
            y=[lance_ref, custos_ref["comissao"], custos_ref["itbi"],
               custos_ref["escritura"], custos_ref["outros"], 0],
            connector=dict(line=dict(color="#1a2e42", width=1)),
            decreasing=dict(marker=dict(color="#ff4455")),
            increasing=dict(marker=dict(color="#2a7aaa")),
            totals=dict(marker=dict(color="#00cc88" if vgv_val > custos_ref["total"] else "#ff4455")),
            texttemplate="%{y:,.0f}", textfont=dict(family="Share Tech Mono", size=9),
        ))
        fig2.update_layout(**PLOTLY_LAYOUT, title="Waterfall · Composição de Custos",
                           yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f", height=380)
        st.plotly_chart(fig2, use_container_width=True)

# ────────────────────────────────────
#  TAB 3 · CUSTOS & P&L
# ────────────────────────────────────
with tab3:
    cx, cy = st.columns(2)
    with cx:
        st.markdown('<div class="section-header">// BREAKDOWN DE AQUISIÇÃO</div>',
                    unsafe_allow_html=True)
        bd = [
            {"Item": "Lance Inicial",        "Valor": fmt(custos_ref["lance"]),   "% Lance": f"{custos_ref['lance']/lance_ref*100:.1f}%"  if lance_ref else "—"},
            {"Item": "Comissão Leiloeiro",    "Valor": fmt(custos_ref["comissao"]),"% Lance": f"{custos_ref['comissao']/lance_ref*100:.1f}%" if lance_ref else "—"},
            {"Item": "ITBI",                 "Valor": fmt(custos_ref["itbi"]),    "% Lance": f"{custos_ref['itbi']/lance_ref*100:.1f}%"    if lance_ref else "—"},
            {"Item": "Escritura / Cartório", "Valor": fmt(custos_ref["escritura"]),"% Lance": f"{custos_ref['escritura']/lance_ref*100:.1f}%" if lance_ref else "—"},
            {"Item": "Outros",               "Valor": fmt(custos_ref["outros"]),  "% Lance": f"{custos_ref['outros']/lance_ref*100:.1f}%"  if lance_ref else "—"},
            {"Item": "──────────────",       "Valor": "──────────",              "% Lance": "──────"},
            {"Item": "CUSTO TOTAL",          "Valor": fmt(custos_ref["total"]),   "% Lance": f"{custos_ref['total']/lance_ref*100:.1f}%"   if lance_ref else "—"},
        ]
        st.dataframe(pd.DataFrame(bd), hide_index=True, use_container_width=True)

        st.markdown('<div class="section-header">// DÉBITOS & RESPONSABILIDADES</div>',
                    unsafe_allow_html=True)
        deb_rows = [
            {"Débito": "IPTU Atrasado",       "Valor": fmt(iptu_deb),  "Responsável": "VENDEDORA ← propter rem"},
            {"Débito": "Condomínio Atrasado", "Valor": fmt(cond_deb),  "Responsável": "VENDEDORA ← propter rem"},
            {"Débito": "Outros → comprador",  "Valor": fmt(outros_deb),"Responsável": "COMPRADOR → entra no custo"},
            {"Débito": "Total vendedora",     "Valor": fmt(deb_vendedora),"Responsável": "Exigir quitação"},
        ]
        st.dataframe(pd.DataFrame(deb_rows), hide_index=True, use_container_width=True)

    with cy:
        st.markdown('<div class="section-header">// P&L PROJETADO</div>', unsafe_allow_html=True)
        pl = [
            {"Item": "VGV (Valor de Mercado)",   "Valor": fmt(vgv_val)},
            {"Item": "(-) Custo Total",          "Valor": fmt(-custos_ref["total"])},
            {"Item": "= Ganho Bruto",            "Valor": fmt(gb_ref)},
            {"Item": "(-) IGC 15%",              "Valor": fmt(-igc_ref)},
            {"Item": "= LUCRO LÍQUIDO",          "Valor": fmt(ll_ref)},
        ]
        st.dataframe(pd.DataFrame(pl), hide_index=True, use_container_width=True)

        if avaliacao > 0:
            st.markdown('<div class="section-header">// POSICIONAMENTO vs AVALIAÇÃO</div>',
                        unsafe_allow_html=True)
            desc_1 = (1 - lance_1/avaliacao)*100 if lance_1 and avaliacao else 0
            desc_2 = (1 - lance_2/avaliacao)*100 if lance_2 and avaliacao else 0
            pos_rows = [
                {"Item": "Valor de Avaliação Oficial",  "Valor": fmt(avaliacao)},
                {"Item": "Desconto 1ª Praça vs. Aval.", "Valor": f"{desc_1:.1f}%"},
                {"Item": "Desconto 2ª Praça vs. Aval.", "Valor": f"{desc_2:.1f}%"},
                {"Item": "Desconto Mercado vs. Aval.",  "Valor": f"{(1-vgv_val/avaliacao)*100:.1f}%" if avaliacao else "—"},
            ]
            st.dataframe(pd.DataFrame(pos_rows), hide_index=True, use_container_width=True)

# ────────────────────────────────────
#  TAB 4 · TIR & SENSIBILIDADE
# ────────────────────────────────────
with tab4:
    cp, cq = st.columns([2, 3])
    with cp:
        st.markdown('<div class="section-header">// TIR ANUALIZADA</div>', unsafe_allow_html=True)
        tir_rows = []
        for meses, tir in [(12, tir_12), (18, tir_18)]:
            tir_rows.append({
                "Horizonte": f"{meses} meses",
                "TIR Anual": f"{tir*100:.1f}%" if tir else "N/C",
                "Rating": "✅ Excelente" if tir and tir > 0.20
                           else "⚡ Bom" if tir and tir > 0.12
                           else "⚠ Atenção" if tir and tir > 0
                           else "❌ Negativo",
            })
        st.dataframe(pd.DataFrame(tir_rows), hide_index=True, use_container_width=True)

        st.markdown('<div class="section-header">// INDICADORES</div>', unsafe_allow_html=True)
        inds = [
            {"Indicador": "Múltiplo VGV/Custo",     "Valor": f"{vgv_val/custos_ref['total']:.2f}x" if custos_ref["total"] else "—"},
            {"Indicador": "R$/m² Adquirido",         "Valor": f"R$ {custos_ref['total']/area_adj:,.0f}" if area_adj else "—"},
            {"Indicador": "R$/m² Mercado",           "Valor": f"R$ {m2_medio:,.0f}"},
            {"Indicador": "Spread m²",               "Valor": f"R$ {m2_medio - custos_ref['total']/area_adj:,.0f}" if area_adj else "—"},
            {"Indicador": "Lance / Avaliação",       "Valor": f"{lance_ref/avaliacao*100:.1f}%" if avaliacao and lance_ref else "—"},
        ]
        st.dataframe(pd.DataFrame(inds), hide_index=True, use_container_width=True)

    with cq:
        descontos  = np.linspace(-0.20, 0.35, 70)
        lucros_var = []
        for d_pct in descontos:
            l_v = lance_ref * (1 - d_pct)
            c_v = custo_total(l_v, comissao_pct, itbi_pct, outros_custos + outros_deb)
            ll_v, _, _ = lucro_liq(vgv_val, c_v["total"])
            lucros_var.append(ll_v)

        fig3 = go.Figure()
        pos_mask = [v >= 0 for v in lucros_var]
        neg_mask = [not m for m in pos_mask]
        fig3.add_trace(go.Scatter(
            x=[descontos[i]*100 for i in range(len(descontos)) if pos_mask[i]],
            y=[lucros_var[i]    for i in range(len(lucros_var)) if pos_mask[i]],
            fill="tozeroy", fillcolor="rgba(0,204,136,0.08)",
            line=dict(color="#00cc88", width=2), name="Lucro",
        ))
        fig3.add_trace(go.Scatter(
            x=[descontos[i]*100 for i in range(len(descontos)) if neg_mask[i]],
            y=[lucros_var[i]    for i in range(len(lucros_var)) if neg_mask[i]],
            fill="tozeroy", fillcolor="rgba(255,68,85,0.08)",
            line=dict(color="#ff4455", width=2), name="Prejuízo",
        ))
        fig3.add_vline(x=0, line_dash="dot", line_color="#ffaa33", line_width=1,
                       annotation_text=" lance atual", annotation_font=dict(color="#ffaa33", size=9))
        fig3.update_layout(
            **PLOTLY_LAYOUT,
            title="Sensibilidade · Lucro Líquido vs. Variação do Lance",
            xaxis_title="Variação no Lance (%)",
            yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
            showlegend=False, height=340,
        )
        st.plotly_chart(fig3, use_container_width=True)

# ────────────────────────────────────
#  TAB 5 · COMPARÁVEIS
# ────────────────────────────────────
with tab5:
    st.markdown('<div class="section-header">// PESQUISA DE MERCADO · COMPARÁVEIS</div>',
                unsafe_allow_html=True)
    comp_df = pd.DataFrame(comps)
    disp = comp_df.copy()
    disp["Preço Total"] = disp["Preço Total"].apply(fmt)
    disp["R$/m²"]       = disp["R$/m²"].apply(lambda x: f"R$ {x:,.0f}")
    st.dataframe(disp, hide_index=True, use_container_width=True)

    cr, cs = st.columns(2)
    with cr:
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=[c["Área (m²)"] for c in comps],
            y=[c["Preço Total"] for c in comps],
            mode="markers+text",
            text=[f"Comp {i+1}" for i in range(len(comps))],
            textposition="top center",
            marker=dict(size=14, color=["#2a7aaa","#4a9acc","#6ab8cc"],
                        line=dict(color="#88ccff", width=1)),
        ))
        if area_util > 0 and lance_ref > 0:
            fig4.add_trace(go.Scatter(
                x=[area_util], y=[lance_ref], mode="markers+text", text=["LEILÃO"],
                textposition="top center",
                marker=dict(size=18, color="#ffaa33", symbol="diamond",
                            line=dict(color="#ffcc55", width=2)),
            ))
        fig4.update_layout(**PLOTLY_LAYOUT, title="Dispersão · Área vs. Preço",
                           xaxis_title="Área (m²)",
                           yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
                           showlegend=False, height=300)
        st.plotly_chart(fig4, use_container_width=True)

    with cs:
        pct_mercado = (lance_ref / vgv_val * 100) if vgv_val > 0 and lance_ref > 0 else 50
        fig5 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pct_mercado,
            number=dict(suffix="%", font=dict(family="Share Tech Mono", color="#a8c8e8", size=26)),
            delta=dict(reference=100, valueformat=".1f",
                       increasing=dict(color="#ff4455"), decreasing=dict(color="#00cc88")),
            gauge=dict(
                axis=dict(range=[0, 130],
                          tickfont=dict(family="Share Tech Mono", size=8, color="#4a6a8a")),
                bar=dict(color="#2a7aaa", thickness=0.25),
                bgcolor="#060a0e", borderwidth=1, bordercolor="#1a2e42",
                steps=[
                    dict(range=[0,70],    color="#0a1a10"),
                    dict(range=[70,90],   color="#0a1a18"),
                    dict(range=[90,110],  color="#1a1008"),
                    dict(range=[110,130], color="#1a0808"),
                ],
                threshold=dict(line=dict(color="#00cc88", width=2), value=80),
            ),
            title=dict(text="Lance / Valor de Mercado",
                       font=dict(family="Share Tech Mono", color="#4a6a8a", size=10)),
        ))
        fig5.update_layout(**PLOTLY_LAYOUT, height=300)
        st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────
#  PDF REPORT GENERATOR
# ─────────────────────────────────────────────

def gerar_pdf_relatorio(
    endereco, regiao, area_util, area_adj, margem_ad,
    lance_ref, lance_1, lance_2, data_1, data_2, avaliacao,
    comissao_pct, itbi_pct, outros_custos, outros_deb,
    iptu_deb, cond_deb,
    custos_ref, vgv_val, ll_ref, igc_ref, gb_ref,
    roi_ref, ms_ref, m2_medio,
    tir_12, tir_18,
    analise_p, comps,
    ad_corpus_f, venda_cond_f,
) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, KeepTogether
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import Image as RLImage
    import plotly.io as pio
    import io as _io
    from datetime import datetime

    # ── Cores ──
    C_BG        = colors.HexColor('#060a0e')
    C_PANEL     = colors.HexColor('#0d1820')
    C_BLUE      = colors.HexColor('#2a7aaa')
    C_BLUE_LT   = colors.HexColor('#88ccff')
    C_GREEN     = colors.HexColor('#00cc88')
    C_RED       = colors.HexColor('#ff4455')
    C_YELLOW    = colors.HexColor('#ffaa33')
    C_PURPLE    = colors.HexColor('#aa55ff')
    C_ORANGE    = colors.HexColor('#ff6b35')
    C_TEXT      = colors.HexColor('#c8d8e8')
    C_MUTED     = colors.HexColor('#4a6a8a')
    C_BORDER    = colors.HexColor('#1e3448')
    C_WHITE     = colors.white

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    W = A4[0] - 3.6*cm  # usable width

    # ── Estilos ──
    def sty(name, **kw):
        base = dict(fontName='Helvetica', fontSize=9, textColor=C_TEXT,
                    leading=13, spaceAfter=2)
        base.update(kw)
        return ParagraphStyle(name, **base)

    S_TITLE  = sty('title',  fontName='Helvetica-Bold', fontSize=20,
                   textColor=C_WHITE, leading=24, spaceAfter=4)
    S_SUB    = sty('sub',    fontName='Helvetica', fontSize=8,
                   textColor=C_MUTED, leading=10, spaceAfter=12)
    S_H1     = sty('h1',     fontName='Helvetica-Bold', fontSize=11,
                   textColor=C_BLUE_LT, leading=14, spaceBefore=14, spaceAfter=6)
    S_H2     = sty('h2',     fontName='Helvetica-Bold', fontSize=9,
                   textColor=C_MUTED, leading=11, spaceBefore=8, spaceAfter=4)
    S_BODY   = sty('body')
    S_MONO   = sty('mono',   fontName='Courier', fontSize=8, textColor=C_TEXT)
    S_ALERT  = sty('alert',  fontName='Helvetica', fontSize=8,
                   textColor=C_ORANGE, leading=11)
    S_GREEN  = sty('green',  fontName='Helvetica-Bold', fontSize=9,
                   textColor=C_GREEN)
    S_RED    = sty('red',    fontName='Helvetica-Bold', fontSize=9,
                   textColor=C_RED)
    S_CENTER = sty('center', alignment=TA_CENTER)
    S_RIGHT  = sty('right',  alignment=TA_RIGHT)

    # ── Helpers ──
    def hr(color=C_BORDER, thickness=0.5):
        return HRFlowable(width='100%', thickness=thickness,
                          color=color, spaceAfter=6, spaceBefore=2)

    def kpi_table(items):
        """items: list of (label, value, color)"""
        n = len(items)
        col_w = W / n
        header_row = [Paragraph(f'<font size="6" color="#{C_MUTED.hexval()[2:]}">{lb}</font>',
                                 S_MONO) for lb, _, _ in items]
        value_row  = [Paragraph(f'<font size="14" color="#{c.hexval()[2:]}">'
                                 f'<b>{vl}</b></font>', S_MONO)
                      for _, vl, c in items]
        t = Table([header_row, value_row], colWidths=[col_w]*n)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C_PANEL),
            ('BOX',        (0,0), (-1,-1), 0.5, C_BORDER),
            ('INNERGRID',  (0,0), (-1,-1), 0.3, C_BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING',(0,0),(-1,-1), 8),
            ('LEFTPADDING', (0,0),(-1,-1), 8),
            ('RIGHTPADDING',(0,0),(-1,-1), 8),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ]))
        return t

    def data_table(headers, rows, col_widths=None, highlight_last=False):
        data = [[Paragraph(f'<b><font color="#{C_MUTED.hexval()[2:]}" size="7">{h}</font></b>',
                            S_MONO) for h in headers]]
        for i, row in enumerate(rows):
            data.append([Paragraph(f'<font size="8" color="#{C_TEXT.hexval()[2:]}">{str(c)}</font>',
                                    S_MONO) for c in row])
        cw = col_widths or [W/len(headers)]*len(headers)
        t = Table(data, colWidths=cw, repeatRows=1)
        style = [
            ('BACKGROUND', (0,0), (-1,0),  C_BORDER),
            ('BACKGROUND', (0,1), (-1,-1), C_PANEL),
            ('BOX',        (0,0), (-1,-1), 0.5, C_BORDER),
            ('INNERGRID',  (0,0), (-1,-1), 0.3, C_BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ('LEFTPADDING', (0,0),(-1,-1), 6),
            ('RIGHTPADDING',(0,0),(-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [C_PANEL, colors.HexColor('#0a1218')]),
        ]
        if highlight_last:
            style += [
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#0a1a28')),
                ('TEXTCOLOR',  (0,-1), (-1,-1), C_BLUE_LT),
                ('FONTNAME',   (0,-1), (-1,-1), 'Helvetica-Bold'),
            ]
        t.setStyle(TableStyle(style))
        return t

    def alert_box(text, color):
        t = Table([[Paragraph(text, ParagraphStyle('al', fontName='Helvetica',
                   fontSize=8, textColor=color, leading=11))]],
                  colWidths=[W])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0a0f18')),
            ('BOX',        (0,0), (-1,-1), 1.5, color),
            ('LEFTPADDING',(0,0), (-1,-1), 10),
            ('RIGHTPADDING',(0,0),(-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ]))
        return t

    def plotly_to_image(fig, width=700, height=300):
        try:
            img_bytes = pio.to_image(fig, format='png', width=width, height=height, scale=2)
            return RLImage(_io.BytesIO(img_bytes), width=W, height=W*height/width)
        except Exception:
            return Paragraph('[Gráfico não disponível]', S_MONO)

    # ── Gerar gráficos ──
    def make_bar_chart():
        fig = go.Figure()
        cats   = ["Lance Ref.", "Custo Total", "Valor Mercado"]
        values = [lance_ref, custos_ref["total"], vgv_val]
        bar_c  = ["#1e5a88", "#2a7aaa", "#00cc88" if vgv_val > custos_ref["total"] else "#ff4455"]
        fig.add_trace(go.Bar(x=cats, y=values, marker_color=bar_c,
                             text=[fmt(v) for v in values], textposition="outside",
                             textfont=dict(color="#a8c8e8", size=10)))
        fig.add_hline(y=custos_ref["total"], line_dash="dot", line_color="#ffaa33", line_width=1)
        if avaliacao > 0:
            fig.add_hline(y=avaliacao, line_dash="dash", line_color="#aa55ff", line_width=1)
        fig.update_layout(**PLOTLY_LAYOUT, height=280,
                          yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f", showlegend=False)
        return fig

    def make_waterfall():
        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute","relative","relative","relative","relative","total"],
            x=["Lance","Comissão","ITBI","Escritura","Outros","TOTAL"],
            y=[lance_ref, custos_ref["comissao"], custos_ref["itbi"],
               custos_ref["escritura"], custos_ref["outros"], 0],
            connector=dict(line=dict(color="#1a2e42")),
            decreasing=dict(marker_color="#ff4455"),
            increasing=dict(marker_color="#2a7aaa"),
            totals=dict(marker_color="#00cc88" if vgv_val > custos_ref["total"] else "#ff4455"),
            texttemplate="%{y:,.0f}", textfont=dict(size=8),
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=260,
                          yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f")
        return fig

    def make_sensitivity():
        descontos  = np.linspace(-0.20, 0.35, 60)
        lucros_var = []
        for d_pct in descontos:
            l_v = lance_ref * (1 - d_pct)
            c_v = custo_total(l_v, comissao_pct, itbi_pct, outros_custos + outros_deb)
            ll_v, _, _ = lucro_liq(vgv_val, c_v["total"])
            lucros_var.append(ll_v)
        fig = go.Figure()
        pos = [v >= 0 for v in lucros_var]
        fig.add_trace(go.Scatter(
            x=[descontos[i]*100 for i in range(len(descontos)) if pos[i]],
            y=[lucros_var[i]    for i in range(len(lucros_var)) if pos[i]],
            fill="tozeroy", fillcolor="rgba(0,204,136,0.10)",
            line=dict(color="#00cc88", width=2)))
        fig.add_trace(go.Scatter(
            x=[descontos[i]*100 for i in range(len(descontos)) if not pos[i]],
            y=[lucros_var[i]    for i in range(len(lucros_var)) if not pos[i]],
            fill="tozeroy", fillcolor="rgba(255,68,85,0.10)",
            line=dict(color="#ff4455", width=2)))
        fig.add_vline(x=0, line_dash="dot", line_color="#ffaa33", line_width=1)
        fig.update_layout(**PLOTLY_LAYOUT, height=260, showlegend=False,
                          xaxis_title="Variação no Lance (%)",
                          yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f")
        return fig

    def make_pracas_bar():
        if not analise_p: return None
        res = analise_p["resultados"]
        fig = go.Figure()
        colors_p = ["#2a7aaa", "#22aa55"]
        for i, (pname, rdata) in enumerate(res.items()):
            fig.add_trace(go.Bar(
                name=pname,
                x=["Lance Mínimo", "Custo Total", "Lucro Líquido"],
                y=[rdata["lance"], rdata["custo"], rdata["lucro"]],
                marker_color=colors_p[i],
                text=[fmt(v) for v in [rdata["lance"], rdata["custo"], rdata["lucro"]]],
                textposition="outside", textfont=dict(size=9, color="#a8c8e8"),
            ))
        fig.add_hline(y=vgv_val, line_dash="dot", line_color="#ffaa33", line_width=1)
        fig.update_layout(**PLOTLY_LAYOUT, barmode="group", height=260,
                          yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
                          showlegend=True,
                          legend=dict(font=dict(size=9, color="#7a9ab8")))
        return fig

    # ── Montar story ──
    story = []
    now = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # ════════════════════════════════════════
    # CAPA
    # ════════════════════════════════════════
    capa_bg = Table([
        [Paragraph('LEILÃO INTEL', ParagraphStyle('cp1', fontName='Helvetica-Bold',
                   fontSize=28, textColor=C_WHITE, leading=32))],
        [Paragraph('RELATÓRIO DE DUE DILIGENCE · WEALTH MANAGEMENT DESK',
                   ParagraphStyle('cp2', fontName='Helvetica', fontSize=8,
                   textColor=C_MUTED, leading=10))],
        [Spacer(1, 0.3*cm)],
        [hr(C_BLUE, 1)],
        [Paragraph(endereco or 'Imóvel não identificado',
                   ParagraphStyle('cp3', fontName='Helvetica-Bold', fontSize=13,
                   textColor=C_BLUE_LT, leading=16))],
        [Paragraph(f'Região: {regiao}  ·  Área útil: {area_util:.1f} m²  ·  '
                   f'Área adj. (Ad Corpus): {area_adj:.1f} m²',
                   ParagraphStyle('cp4', fontName='Helvetica', fontSize=8,
                   textColor=C_TEXT, leading=11))],
        [Spacer(1, 0.3*cm)],
        [hr(C_BORDER)],
        [Paragraph(f'Gerado em {now}  ·  v3.0 · PDF Intelligence Engine',
                   ParagraphStyle('cp5', fontName='Helvetica', fontSize=7,
                   textColor=C_MUTED, leading=9))],
    ], colWidths=[W])
    capa_bg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_BG),
        ('BOX',        (0,0), (-1,-1), 1, C_BORDER),
        ('LEFTPADDING',(0,0), (-1,-1), 16),
        ('RIGHTPADDING',(0,0),(-1,-1), 16),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
    ]))
    story.append(capa_bg)
    story.append(Spacer(1, 0.4*cm))

    # ── Alertas de risco ──
    if venda_cond_f:
        story.append(alert_box(
            '⚠  VENDA CONDICIONADA — Homologação sujeita à aprovação exclusiva do COMITENTE. '
            'A VENDEDORA pode recusar o lance sem justificativa.', C_ORANGE))
        story.append(Spacer(1, 0.2*cm))
    if ad_corpus_f:
        story.append(alert_box(
            f'ℹ  AD CORPUS — Imóvel vendido como um todo. Margem de metragem: {margem_ad:.1f}% '
            f'→ Área ajustada para cálculo: {area_adj:.1f} m²', C_BLUE))
        story.append(Spacer(1, 0.2*cm))
    if iptu_deb + cond_deb > 0:
        story.append(alert_box(
            f'⚖  DÉBITOS PROPTER REM — IPTU + Condomínio ({fmt(iptu_deb+cond_deb)}) são '
            'responsabilidade da VENDEDORA até a homologação judicial.', C_PURPLE))
        story.append(Spacer(1, 0.2*cm))

    # ── KPIs ──
    story.append(Spacer(1, 0.2*cm))
    lc = C_GREEN if ll_ref >= 0 else C_RED
    rc = C_GREEN if roi_ref >= 20 else C_YELLOW if roi_ref >= 10 else C_RED
    mc = C_GREEN if ms_ref >= 25 else C_YELLOW if ms_ref >= 15 else C_RED
    story.append(kpi_table([
        ('CUSTO TOTAL',        fmt(custos_ref['total']), C_BLUE),
        ('VALOR DE MERCADO',   fmt(vgv_val),             C_BLUE_LT),
        ('LUCRO LÍQUIDO',      fmt(ll_ref),              lc),
        ('ROI ESTIMADO',       f'{roi_ref:.1f}%',        rc),
        ('MARGEM SEGURANÇA',   f'{ms_ref:.1f}%',         mc),
    ]))
    story.append(Spacer(1, 0.4*cm))

    # ════════════════════════════════════════
    # SEÇÃO 1 — 1ª vs 2ª PRAÇA
    # ════════════════════════════════════════
    story.append(Paragraph('1.  ANÁLISE DE PRAÇAS', S_H1))
    story.append(hr(C_BLUE))

    if analise_p and (lance_1 > 0 or lance_2 > 0):
        res  = analise_p["resultados"]
        rec  = analise_p["recomendacao"]
        cor_map = {"blue": C_BLUE, "green": C_GREEN, "yellow": C_YELLOW}
        rec_cor = cor_map.get(rec["cor"], C_YELLOW)

        # Recomendação
        story.append(alert_box(
            f'RECOMENDAÇÃO: {rec["acao"]}  —  {rec["motivo"]}', rec_cor))
        story.append(Spacer(1, 0.3*cm))

        # Tabela comparativa
        headers = ["Métrica"] + list(res.keys())
        metricas_pdf = [
            ("Lance Mínimo",     "lance",     True),
            ("Custo Total",      "custo",     True),
            ("Lucro Líquido",    "lucro",     True),
            ("ROI",              "roi",       False),
            ("Margem Segurança", "margem",    False),
            ("Desc. Avaliação",  "desc_aval", False),
            ("TIR 12 meses",     "tir12",     None),
        ]
        rows = []
        for label, campo, is_money in metricas_pdf:
            row = [label]
            for p in res.keys():
                v = res[p][campo]
                if campo == "tir12":
                    row.append(f"{v*100:.1f}%" if v else "N/C")
                elif is_money:
                    row.append(fmt(v))
                else:
                    row.append(f"{v:.1f}%")
            rows.append(row)

        cw = [W*0.35] + [W*0.325]*len(res)
        story.append(data_table(headers, rows, cw))
        story.append(Spacer(1, 0.3*cm))

        # Gráfico praças
        fig_p = make_pracas_bar()
        if fig_p:
            story.append(plotly_to_image(fig_p, 700, 260))
    else:
        story.append(alert_box(
            'ℹ Lance(s) de praça não informado(s). Preencha na sidebar para ativar esta seção.', C_BLUE))

    story.append(Spacer(1, 0.5*cm))

    # ════════════════════════════════════════
    # SEÇÃO 2 — COMPARATIVO
    # ════════════════════════════════════════
    story.append(Paragraph('2.  COMPARATIVO: LANCE vs. MERCADO', S_H1))
    story.append(hr(C_BLUE))

    # Gráfico barras
    story.append(plotly_to_image(make_bar_chart(), 700, 280))
    story.append(Spacer(1, 0.2*cm))

    # Gráfico waterfall
    story.append(Paragraph('Composição de Custos (Waterfall)', S_H2))
    story.append(plotly_to_image(make_waterfall(), 700, 260))
    story.append(Spacer(1, 0.5*cm))

    # ════════════════════════════════════════
    # SEÇÃO 3 — CUSTOS & P&L
    # ════════════════════════════════════════
    story.append(Paragraph('3.  CUSTOS DETALHADOS & P&L', S_H1))
    story.append(hr(C_BLUE))

    # Breakdown de custos
    story.append(Paragraph('Breakdown de Aquisição', S_H2))
    bd_headers = ["Item", "Valor (R$)", "% do Lance"]
    bd_rows = [
        ["Lance Inicial",        fmt(custos_ref['lance']),    f"{custos_ref['lance']/lance_ref*100:.1f}%" if lance_ref else "—"],
        ["Comissão Leiloeiro",   fmt(custos_ref['comissao']), f"{custos_ref['comissao']/lance_ref*100:.1f}%" if lance_ref else "—"],
        ["ITBI",                 fmt(custos_ref['itbi']),     f"{custos_ref['itbi']/lance_ref*100:.1f}%" if lance_ref else "—"],
        ["Escritura / Cartório", fmt(custos_ref['escritura']),f"{custos_ref['escritura']/lance_ref*100:.1f}%" if lance_ref else "—"],
        ["Outros (reforma/déb.)",fmt(custos_ref['outros']),   f"{custos_ref['outros']/lance_ref*100:.1f}%" if lance_ref else "—"],
        ["CUSTO TOTAL",          fmt(custos_ref['total']),    f"{custos_ref['total']/lance_ref*100:.1f}%" if lance_ref else "—"],
    ]
    story.append(data_table(bd_headers, bd_rows,
                            [W*0.45, W*0.30, W*0.25], highlight_last=True))
    story.append(Spacer(1, 0.3*cm))

    # Débitos
    story.append(Paragraph('Débitos & Responsabilidades', S_H2))
    deb_headers = ["Débito", "Valor (R$)", "Responsável"]
    deb_rows = [
        ["IPTU Atrasado",        fmt(iptu_deb),           "VENDEDORA ← propter rem"],
        ["Condomínio Atrasado",  fmt(cond_deb),           "VENDEDORA ← propter rem"],
        ["Outros → comprador",   fmt(outros_deb),         "COMPRADOR → entra no custo"],
        ["Total s/ vendedora",   fmt(iptu_deb+cond_deb),  "Exigir quitação prévia"],
    ]
    story.append(data_table(deb_headers, deb_rows, [W*0.30, W*0.22, W*0.48]))
    story.append(Spacer(1, 0.3*cm))

    # P&L
    story.append(Paragraph('Demonstrativo P&L Projetado', S_H2))
    pl_headers = ["Item", "Valor (R$)"]
    pl_rows = [
        ["VGV (Valor de Mercado)",  fmt(vgv_val)],
        ["(-) Custo Total",         fmt(-custos_ref['total'])],
        ["= Ganho Bruto",           fmt(gb_ref)],
        ["(-) IGC 15% (Imp. Ganho Capital)", fmt(-igc_ref)],
        ["= LUCRO LÍQUIDO",         fmt(ll_ref)],
    ]
    story.append(data_table(pl_headers, pl_rows, [W*0.65, W*0.35], highlight_last=True))
    story.append(Spacer(1, 0.5*cm))

    # ════════════════════════════════════════
    # SEÇÃO 4 — TIR & SENSIBILIDADE
    # ════════════════════════════════════════
    story.append(Paragraph('4.  TIR & ANÁLISE DE SENSIBILIDADE', S_H1))
    story.append(hr(C_BLUE))

    # TIR
    story.append(Paragraph('Taxa Interna de Retorno (TIR Anualizada)', S_H2))
    tir_headers = ["Horizonte", "TIR Anual", "Classificação"]
    tir_rows = []
    for meses, tir in [(12, tir_12), (18, tir_18)]:
        tir_rows.append([
            f"{meses} meses",
            f"{tir*100:.1f}%" if tir else "N/C",
            "Excelente (>20%)" if tir and tir > 0.20
            else "Bom (12–20%)" if tir and tir > 0.12
            else "Atenção (0–12%)" if tir and tir > 0
            else "Negativo",
        ])
    story.append(data_table(tir_headers, tir_rows, [W*0.28, W*0.28, W*0.44]))
    story.append(Spacer(1, 0.2*cm))

    # Indicadores
    story.append(Paragraph('Indicadores Financeiros', S_H2))
    ind_headers = ["Indicador", "Valor"]
    ind_rows = [
        ["Múltiplo VGV/Custo",    f"{vgv_val/custos_ref['total']:.2f}x" if custos_ref['total'] else "—"],
        ["R$/m² Adquirido",       f"R$ {custos_ref['total']/area_adj:,.0f}" if area_adj else "—"],
        ["R$/m² Mercado (média)", f"R$ {m2_medio:,.0f}"],
        ["Spread m² (mercado-adq.)", f"R$ {m2_medio - custos_ref['total']/area_adj:,.0f}" if area_adj else "—"],
        ["Lance / Avaliação",     f"{lance_ref/avaliacao*100:.1f}%" if avaliacao and lance_ref else "—"],
        ["Margem de Segurança",   f"{ms_ref:.1f}%"],
        ["ROI Estimado",          f"{roi_ref:.1f}%"],
    ]
    story.append(data_table(ind_headers, ind_rows, [W*0.60, W*0.40]))
    story.append(Spacer(1, 0.3*cm))

    # Gráfico sensibilidade
    story.append(Paragraph('Sensibilidade: Lucro Líquido vs. Variação do Lance', S_H2))
    story.append(plotly_to_image(make_sensitivity(), 700, 260))
    story.append(Spacer(1, 0.5*cm))

    # ════════════════════════════════════════
    # SEÇÃO 5 — COMPARÁVEIS
    # ════════════════════════════════════════
    story.append(Paragraph('5.  PESQUISA DE MERCADO · COMPARÁVEIS', S_H1))
    story.append(hr(C_BLUE))

    comp_headers = ["Endereço", "Área (m²)", "Preço Total", "R$/m²"]
    comp_rows = []
    for c in comps:
        comp_rows.append([
            c["Endereço"][:40],
            f"{c['Área (m²)']}",
            fmt(c["Preço Total"]),
            f"R$ {c['R$/m²']:,.0f}",
        ])
    story.append(data_table(comp_headers, comp_rows,
                            [W*0.46, W*0.14, W*0.22, W*0.18]))
    story.append(Spacer(1, 0.3*cm))

    # Resumo comparáveis
    story.append(Paragraph('Resumo Estatístico dos Comparáveis', S_H2))
    pm2_list = [c["R$/m²"] for c in comps]
    stat_headers = ["Estatística", "R$/m²", "Impacto no VGV"]
    stat_rows = [
        ["Mínimo",  f"R$ {min(pm2_list):,.0f}", fmt(min(pm2_list) * area_adj)],
        ["Média",   f"R$ {np.mean(pm2_list):,.0f}", fmt(np.mean(pm2_list) * area_adj)],
        ["Máximo",  f"R$ {max(pm2_list):,.0f}", fmt(max(pm2_list) * area_adj)],
        ["Imóvel (custo/m²)", f"R$ {custos_ref['total']/area_adj:,.0f}" if area_adj else "—",
         f"Lance: {fmt(lance_ref)}"],
    ]
    story.append(data_table(stat_headers, stat_rows,
                            [W*0.35, W*0.30, W*0.35], highlight_last=True))
    story.append(Spacer(1, 0.5*cm))

    # ════════════════════════════════════════
    # RODAPÉ LEGAL
    # ════════════════════════════════════════
    story.append(hr(C_BORDER, 0.5))
    disc = Table([[Paragraph(
        'AVISO LEGAL: Este relatório foi gerado automaticamente pelo sistema LEILÃO INTEL v3.0 '
        'com base nos dados inseridos pelo usuário. As projeções financeiras são estimativas e '
        'não constituem oferta, recomendação ou aconselhamento de investimento. '
        'Os valores de mercado são baseados em comparáveis sintéticos regionais. '
        'O investidor deve realizar due diligence independente antes de tomar qualquer decisão. '
        f'Gerado em {now}.',
        ParagraphStyle('disc', fontName='Helvetica', fontSize=6.5,
                       textColor=C_MUTED, leading=9)
    )]], colWidths=[W])
    disc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_BG),
        ('LEFTPADDING',(0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
    ]))
    story.append(disc)

    # ── Build ──
    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── BOTÃO DE EXPORTAÇÃO ──
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='font-family:Share Tech Mono,monospace;font-size:0.65rem;
            letter-spacing:3px;color:#2a5a8a;margin-bottom:0.5rem'>
    // EXPORTAR ANÁLISE COMPLETA
</div>""", unsafe_allow_html=True)

col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 3])
with col_btn1:
    if st.button("⬇  GERAR RELATÓRIO PDF", use_container_width=True):
        if lance_ref == 0:
            st.error("⚠ Informe o lance mínimo antes de gerar o relatório.")
        else:
            with st.spinner("Gerando relatório PDF..."):
                try:
                    pdf_bytes = gerar_pdf_relatorio(
                        endereco=endereco, regiao=regiao,
                        area_util=area_util, area_adj=area_adj, margem_ad=margem_ad,
                        lance_ref=lance_ref, lance_1=lance_1, lance_2=lance_2,
                        data_1=data_1, data_2=data_2, avaliacao=avaliacao,
                        comissao_pct=comissao_pct, itbi_pct=itbi_pct,
                        outros_custos=outros_custos, outros_deb=outros_deb,
                        iptu_deb=iptu_deb, cond_deb=cond_deb,
                        custos_ref=custos_ref, vgv_val=vgv_val,
                        ll_ref=ll_ref, igc_ref=igc_ref, gb_ref=gb_ref,
                        roi_ref=roi_ref, ms_ref=ms_ref, m2_medio=m2_medio,
                        tir_12=tir_12, tir_18=tir_18,
                        analise_p=analise_p, comps=comps,
                        ad_corpus_f=ad_corpus_f, venda_cond_f=venda_cond_f,
                    )
                    from datetime import datetime
                    nome_arquivo = f"leilao_intel_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    st.download_button(
                        label="📄 BAIXAR PDF",
                        data=pdf_bytes,
                        file_name=nome_arquivo,
                        mime="application/pdf",
                        use_container_width=True,
                    )
                    st.success("✅ Relatório gerado! Clique em 'BAIXAR PDF' acima.")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

# ── FOOTER ──
st.markdown("""
<hr style='border:none;border-top:1px solid #1a2e42;margin:2rem 0 0.8rem'>
<div style='font-family:Share Tech Mono,monospace;font-size:0.58rem;
            color:#2a4a6a;text-align:center;letter-spacing:2px'>
    LEILÃO INTEL v3.0 · PDF INTELLIGENCE ENGINE · WEALTH MANAGEMENT DESK ·
    DADOS PARA FINS ANALÍTICOS · NÃO CONSTITUI OFERTA OU RECOMENDAÇÃO DE INVESTIMENTO
</div>""", unsafe_allow_html=True)
