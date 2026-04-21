"""
Dashboard de Análise de Leilões Imobiliários
Wealth Management | Real Estate Investment Intelligence
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy.optimize import brentq
import re

# ─────────────────────────────────────────────
#  PAGE CONFIG & DARK THEME
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="LEILÃO INTEL · Wealth Desk",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Syne:wght@400;600;700;800&display=swap');

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #080c10 !important;
    color: #c8d8e8 !important;
    font-family: 'Syne', sans-serif;
}
[data-testid="stSidebar"] {
    background: #0a0f15 !important;
    border-right: 1px solid #1a2635;
}
[data-testid="stHeader"] { background: transparent !important; }

/* ── Typography ── */
h1, h2, h3 { font-family: 'Syne', sans-serif; font-weight: 800; }
h1 { color: #e8f4ff; letter-spacing: -1px; }
h2 { color: #a8c8e8; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 3px; }
h3 { color: #7ab8d8; }
.mono { font-family: 'Share Tech Mono', monospace; }

/* ── Metric Cards ── */
.kpi-card {
    background: linear-gradient(135deg, #0d1820 0%, #0a1520 100%);
    border: 1px solid #1e3448;
    border-top: 2px solid;
    border-radius: 4px;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at top left, rgba(0,180,255,0.04), transparent 60%);
    pointer-events: none;
}
.kpi-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4a6a8a;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    line-height: 1;
}
.kpi-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    color: #4a6a8a;
    margin-top: 0.4rem;
}

/* ── Alert Box ── */
.alert-condicionada {
    background: linear-gradient(135deg, #1a0f08, #1f1408);
    border: 1px solid #ff6b35;
    border-left: 4px solid #ff6b35;
    border-radius: 4px;
    padding: 1rem 1.4rem;
    margin: 1rem 0;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    color: #ff9a6b;
}
.alert-corpus {
    background: linear-gradient(135deg, #0a0f1a, #0d1520);
    border: 1px solid #4488cc;
    border-left: 4px solid #4488cc;
    border-radius: 4px;
    padding: 1rem 1.4rem;
    margin: 1rem 0;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    color: #88bbdd;
}
.alert-debito {
    background: linear-gradient(135deg, #0f0a14, #140f1a);
    border: 1px solid #aa55ff;
    border-left: 4px solid #aa55ff;
    border-radius: 4px;
    padding: 1rem 1.4rem;
    margin: 1rem 0;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    color: #cc99ff;
}

/* ── Section Divider ── */
.section-header {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #2a4a6a;
    border-bottom: 1px solid #1a2e42;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem;
}

/* ── Inputs ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: #0d1820 !important;
    border: 1px solid #1e3448 !important;
    border-radius: 3px !important;
    color: #c8d8e8 !important;
    font-family: 'Share Tech Mono', monospace !important;
}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus {
    border-color: #2a7aaa !important;
    box-shadow: 0 0 0 2px rgba(42,122,170,0.15) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0a2840, #0d3050) !important;
    border: 1px solid #1e5a88 !important;
    color: #88ccff !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 2px !important;
    font-size: 0.75rem !important;
    border-radius: 3px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0d3050, #103860) !important;
    border-color: #2a7aaa !important;
    color: #aaddff !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1a2e42 !important;
    border-radius: 4px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0a0f15 !important;
    border-bottom: 1px solid #1a2e42;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 2px !important;
    color: #4a6a8a !important;
    border-radius: 0 !important;
    padding: 0.7rem 1.5rem !important;
}
.stTabs [aria-selected="true"] {
    color: #88ccff !important;
    border-bottom: 2px solid #2a7aaa !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: transparent !important;
    padding-top: 1.5rem;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: #0d1820 !important;
    border: 1px solid #1e3448 !important;
    color: #c8d8e8 !important;
    font-family: 'Share Tech Mono', monospace !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #080c10; }
::-webkit-scrollbar-thumb { background: #1e3448; border-radius: 2px; }

/* ── Sidebar labels ── */
[data-testid="stSidebar"] label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 1px !important;
    color: #4a6a8a !important;
    text-transform: uppercase;
}
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#080c10",
    font=dict(family="Share Tech Mono, monospace", color="#7a9ab8", size=11),
    title_font=dict(family="Syne, sans-serif", color="#a8c8e8", size=14),
    xaxis=dict(
        gridcolor="#0f1e2e", linecolor="#1a2e42", tickcolor="#1a2e42",
        zerolinecolor="#1a2e42"
    ),
    yaxis=dict(
        gridcolor="#0f1e2e", linecolor="#1a2e42", tickcolor="#1a2e42",
        zerolinecolor="#1a2e42"
    ),
    margin=dict(l=40, r=20, t=50, b=40),
)

# ─────────────────────────────────────────────
#  FINANCIAL ENGINE
# ─────────────────────────────────────────────
def format_brl(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calc_escritura(lance: float) -> float:
    """Tabela TABELIONATOS-SP simplificada (faixas de valor)."""
    if lance <= 50_000:     return 800
    elif lance <= 100_000:  return 1_200
    elif lance <= 250_000:  return 1_800
    elif lance <= 500_000:  return 2_800
    elif lance <= 1_000_000: return 4_500
    else:                   return 7_200

def custo_aquisicao(lance, comissao_pct, itbi_pct, outros_custos=0):
    comissao = lance * comissao_pct / 100
    itbi     = lance * itbi_pct / 100
    escritura = calc_escritura(lance)
    total    = lance + comissao + itbi + escritura + outros_custos
    return dict(lance=lance, comissao=comissao, itbi=itbi,
                escritura=escritura, outros=outros_custos, total=total)

def valor_mercado_real(area_util, margem_erro_pct, comp_precos_m2):
    """Média ponderada dos comparáveis · ajuste Ad Corpus."""
    m2_medio = np.mean(comp_precos_m2) if comp_precos_m2 else 0
    area_adj = area_util * (1 - margem_erro_pct / 100)  # cláusula Ad Corpus
    return m2_medio * area_adj, m2_medio, area_adj

def lucro_liquido(vgv, custo_total, debito_responsabilidade_vendedora=0):
    """Ganho bruto - Imposto sobre Ganho de Capital (15%)."""
    ganho_bruto = vgv - custo_total + debito_responsabilidade_vendedora
    if ganho_bruto <= 0:
        return ganho_bruto, 0, ganho_bruto
    igc = ganho_bruto * 0.15
    return ganho_bruto - igc, igc, ganho_bruto

def calcular_tir(custo_total, vgv, meses):
    """TIR mensal → anualizada: (1+r_m)^12 - 1."""
    fluxo = [-custo_total] + [0] * (meses - 1) + [vgv]
    def npv(r):
        return sum(f / (1 + r) ** t for t, f in enumerate(fluxo))
    try:
        r_m = brentq(npv, -0.99, 10, maxiter=500)
        return (1 + r_m) ** 12 - 1
    except Exception:
        return None

def roi(lucro, custo_total):
    return lucro / custo_total * 100 if custo_total else 0

def margem_seguranca(custo_total, vgv):
    return (1 - custo_total / vgv) * 100 if vgv else 0

# ─────────────────────────────────────────────
#  WEB SCRAPING SIMULATOR
# ─────────────────────────────────────────────
DEMO_COMPS = {
    "Zona Norte – SP":  [8_500, 9_200, 8_800],
    "Zona Sul – SP":    [11_000, 10_500, 12_000],
    "Zona Leste – SP":  [7_200, 7_800, 7_500],
    "Zona Oeste – SP":  [13_500, 14_000, 13_200],
    "ABC Paulista":     [6_800, 7_100, 6_500],
}

def scrape_simulator(urls: list[str], regiao: str) -> list[dict]:
    """Retorna dados sintéticos baseados na região selecionada."""
    base_prices = DEMO_COMPS.get(regiao, [8_000, 8_500, 9_000])
    results = []
    enderecos = [
        f"Av. Principal, 100 – {regiao}",
        f"Rua Comercial, 45 – {regiao}",
        f"Travessa Residencial, 78 – {regiao}",
    ]
    for i, preco in enumerate(base_prices):
        area = np.random.randint(55, 130)
        results.append({
            "Endereço":     enderecos[i],
            "Área (m²)":   area,
            "Preço Total":  preco * area,
            "R$/m²":        preco,
            "Fonte":        urls[i] if i < len(urls) else f"ZAP Imóveis – Comp {i+1}",
        })
    return results

# ─────────────────────────────────────────────
#  SIDEBAR – INPUT DE DADOS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 1rem 0 0.5rem'>
        <div style='font-family: Share Tech Mono, monospace; font-size: 0.6rem;
                    letter-spacing: 4px; color: #2a5a8a; text-transform: uppercase;
                    margin-bottom: 0.3rem'>Wealth Desk · v2.4</div>
        <div style='font-family: Syne, sans-serif; font-size: 1.4rem; font-weight: 800;
                    color: #e8f4ff; letter-spacing: -0.5px'>LEILÃO INTEL</div>
        <div style='font-family: Share Tech Mono, monospace; font-size: 0.65rem;
                    color: #4a7a9a; margin-top: 0.2rem'>Real Estate · Due Diligence</div>
    </div>
    <hr style='border: none; border-top: 1px solid #1a2e42; margin: 1rem 0'>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">// IDENTIFICAÇÃO DO IMÓVEL</div>',
                unsafe_allow_html=True)
    endereco   = st.text_input("Endereço", placeholder="Rua das Flores, 123 – SP")
    regiao     = st.selectbox("Região de Referência", list(DEMO_COMPS.keys()))
    area_util  = st.number_input("Área Útil (m²)", min_value=1.0, value=80.0, step=0.5)
    margem_ad_corpus = st.number_input("Margem Ad Corpus (%)",
                                       min_value=0.0, max_value=20.0, value=3.0, step=0.5,
                                       help="Risco de metragem real divergir do edital")

    st.markdown('<div class="section-header">// LANCE & CUSTOS</div>',
                unsafe_allow_html=True)
    lance         = st.number_input("Lance Inicial (R$)", min_value=1_000.0,
                                    value=250_000.0, step=1_000.0)
    comissao_pct  = st.number_input("Comissão do Leiloeiro (%)", min_value=0.0,
                                    max_value=10.0, value=5.0, step=0.5)
    itbi_pct      = st.number_input("ITBI (%)", min_value=0.0, max_value=10.0,
                                    value=3.0, step=0.25)
    outros_custos = st.number_input("Outros Custos (R$)", min_value=0.0,
                                    value=0.0, step=500.0,
                                    help="Reformas, regularizações, etc.")

    st.markdown('<div class="section-header">// DÉBITOS DO IMÓVEL</div>',
                unsafe_allow_html=True)
    debito_iptu   = st.number_input("IPTU Atrasado (R$) ← vendedora",
                                    min_value=0.0, value=0.0, step=100.0,
                                    help="Propter rem: responsabilidade da vendedora até homologação")
    debito_cond   = st.number_input("Condomínio Atrasado (R$) ← vendedora",
                                    min_value=0.0, value=0.0, step=100.0,
                                    help="Propter rem: responsabilidade da vendedora até homologação")
    debito_outros = st.number_input("Outros Débitos (R$) → comprador",
                                    min_value=0.0, value=0.0, step=100.0,
                                    help="Débitos que passam ao adquirente")

    st.markdown('<div class="section-header">// FLAGS DE RISCO</div>',
                unsafe_allow_html=True)
    venda_condicionada = st.checkbox("⚠ Venda Condicionada (comitente)",
                                     help="Lote sujeito à aprovação do comitente – risco de frustração")
    ad_corpus_flag     = st.checkbox("⚠ Cláusula Ad Corpus presente", value=True)

    st.markdown('<div class="section-header">// COMPARÁVEIS · URLS</div>',
                unsafe_allow_html=True)
    url1 = st.text_input("URL Comp. 1", placeholder="https://www.zapimoveis.com.br/...")
    url2 = st.text_input("URL Comp. 2", placeholder="https://www.vivareal.com.br/...")
    url3 = st.text_input("URL Comp. 3", placeholder="https://www.zapimoveis.com.br/...")

    run_btn = st.button("⬡  EXECUTAR ANÁLISE", use_container_width=True)

# ─────────────────────────────────────────────
#  MAIN AREA – HEADER
# ─────────────────────────────────────────────
col_title, col_tag = st.columns([4, 1])
with col_title:
    st.markdown("""
    <h1 style='margin-bottom:0'>ANÁLISE DE LEILÃO IMOBILIÁRIO</h1>
    <div style='font-family: Share Tech Mono, monospace; font-size: 0.7rem;
                color: #2a5a8a; letter-spacing: 3px; margin-top: 0.3rem'>
        DUE DILIGENCE ENGINE · WEALTH MANAGEMENT DESK
    </div>
    """, unsafe_allow_html=True)
with col_tag:
    st.markdown("""
    <div style='text-align:right; padding-top:0.5rem'>
        <div style='display:inline-block; background:#0a2840; border:1px solid #1e5a88;
                    border-radius:3px; padding:0.3rem 0.8rem;
                    font-family: Share Tech Mono, monospace; font-size:0.65rem;
                    letter-spacing:2px; color:#4a9acc'>LIVE MODE</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:1px; background: linear-gradient(90deg, #1a3a5a, transparent); margin: 0.5rem 0 1.5rem'></div>",
            unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ALERTS (always visible if flags set)
# ─────────────────────────────────────────────
if venda_condicionada:
    st.markdown("""
    <div class='alert-condicionada'>
        ⚠ RISCO · VENDA CONDICIONADA &nbsp;|&nbsp;
        Esta operação está sujeita à aprovação expressa do <strong>COMITENTE</strong>.
        A homologação pode ser recusada unilateralmente, frustrando o negócio mesmo após
        o maior lance. Avalie jurídico antes de imobilizar capital.
    </div>
    """, unsafe_allow_html=True)

if ad_corpus_flag:
    st.markdown(f"""
    <div class='alert-corpus'>
        ℹ CLÁUSULA AD CORPUS DETECTADA &nbsp;|&nbsp;
        O imóvel é vendido como um todo, sem garantia de metragem exata.
        Margem de erro configurada: <strong>{margem_ad_corpus:.1f}%</strong> →
        área ajustada: <strong>{area_util * (1 - margem_ad_corpus / 100):.1f} m²</strong>.
        O preço de mercado será calculado sobre a área ajustada.
    </div>
    """, unsafe_allow_html=True)

debito_vendedora = debito_iptu + debito_cond
if debito_vendedora > 0:
    st.markdown(f"""
    <div class='alert-debito'>
        ⚖ DÉBITOS PROPTER REM &nbsp;|&nbsp;
        IPTU + Condomínio atrasados ({format_brl(debito_vendedora)}) são responsabilidade
        da <strong>VENDEDORA</strong> até a data de homologação judicial.
        Exija quitação como condição precedente ou desconto equivalente no lance.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  EXECUTE ENGINE
# ─────────────────────────────────────────────
if run_btn or True:  # show placeholder until first run
    urls = [u for u in [url1, url2, url3] if u.strip()]
    comps = scrape_simulator(urls, regiao)
    comp_df = pd.DataFrame(comps)
    precos_m2 = [c["R$/m²"] for c in comps]

    custos = custo_aquisicao(lance, comissao_pct, itbi_pct,
                             outros_custos + debito_outros)
    vgv, m2_medio, area_adj = valor_mercado_real(area_util, margem_ad_corpus, precos_m2)
    lucro_liq, igc, ganho_bruto = lucro_liquido(
        vgv, custos["total"], debito_responsabilidade_vendedora=0
    )
    roi_val    = roi(lucro_liq, custos["total"])
    margem_seg = margem_seguranca(custos["total"], vgv)
    tir_12     = calcular_tir(custos["total"], vgv, 12)
    tir_18     = calcular_tir(custos["total"], vgv, 18)

    # ── KPI CARDS ──
    c1, c2, c3, c4, c5 = st.columns(5)

    def kpi(label, value, sub="", color="#2a7aaa"):
        return f"""
        <div class='kpi-card' style='border-top-color: {color}'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value' style='color:{color}'>{value}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>"""

    is_positive = lucro_liq >= 0
    lucro_color = "#00cc88" if is_positive else "#ff4455"
    roi_color   = "#00cc88" if roi_val >= 15 else "#ffaa33" if roi_val >= 5 else "#ff4455"
    ms_color    = "#00cc88" if margem_seg >= 20 else "#ffaa33" if margem_seg >= 10 else "#ff4455"

    with c1:
        st.markdown(kpi("CUSTO TOTAL", format_brl(custos["total"]),
                        f"Lance: {format_brl(lance)}", "#4a8acc"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi("VALOR DE MERCADO", format_brl(vgv),
                        f"R$/m²: {m2_medio:,.0f} · área adj: {area_adj:.0f}m²", "#6a9acc"),
                    unsafe_allow_html=True)
    with c3:
        st.markdown(kpi("LUCRO LÍQUIDO", format_brl(lucro_liq),
                        f"IGC (15%): {format_brl(igc)}", lucro_color),
                    unsafe_allow_html=True)
    with c4:
        st.markdown(kpi("ROI ESTIMADO", f"{roi_val:.1f}%",
                        "Sobre custo total", roi_color), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi("MARGEM DE SEGURANÇA", f"{margem_seg:.1f}%",
                        "Desconto vs mercado", ms_color), unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── TABS ──
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊  COMPARATIVO", "💰  CUSTOS DETALHADOS",
        "📈  TIR & PROJEÇÕES", "🏠  COMPARÁVEIS"
    ])

    # ────────────────────────────
    #  TAB 1 · COMPARATIVO
    # ────────────────────────────
    with tab1:
        col_a, col_b = st.columns([3, 2])

        with col_a:
            fig = go.Figure()
            categories  = ["Lance Inicial", "Custo Total\n(c/ taxas)", "Valor de Mercado"]
            values      = [lance, custos["total"], vgv]
            bar_colors  = ["#1e5a88", "#2a7aaa", "#00cc88" if vgv > custos["total"] else "#ff4455"]

            fig.add_trace(go.Bar(
                x=categories, y=values,
                marker=dict(
                    color=bar_colors,
                    line=dict(color=["#2a8acc", "#4aaabb", "#00ffaa" if vgv > custos["total"] else "#ff6677"],
                              width=1),
                ),
                text=[format_brl(v) for v in values],
                textposition="outside",
                textfont=dict(family="Share Tech Mono", size=10, color="#a8c8e8"),
                hovertemplate="%{x}<br><b>%{text}</b><extra></extra>",
            ))

            # linha de breakeven
            fig.add_hline(y=custos["total"], line_dash="dot",
                          line_color="#ffaa33", line_width=1,
                          annotation_text=" breakeven",
                          annotation_font=dict(color="#ffaa33", size=9))

            fig.update_layout(
                **PLOTLY_LAYOUT,
                title="Preço Leilão vs. Custo Total vs. Mercado",
                yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
                showlegend=False,
                height=380,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            # Waterfall de composição de custos
            fig2 = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                x=["Lance", "Comissão", "ITBI", "Escritura", "Outros", "TOTAL"],
                y=[lance, custos["comissao"], custos["itbi"],
                   custos["escritura"], custos["outros"] + debito_outros, 0],
                connector=dict(line=dict(color="#1a2e42", width=1)),
                decreasing=dict(marker=dict(color="#ff4455")),
                increasing=dict(marker=dict(color="#2a7aaa")),
                totals=dict(marker=dict(color="#00cc88" if vgv > custos["total"] else "#ff4455")),
                texttemplate="%{y:,.0f}",
                textfont=dict(family="Share Tech Mono", size=9),
                hovertemplate="%{x}<br><b>R$ %{y:,.0f}</b><extra></extra>",
            ))
            fig2.update_layout(
                **PLOTLY_LAYOUT,
                title="Waterfall · Composição de Custos",
                yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
                height=380,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ────────────────────────────
    #  TAB 2 · CUSTOS DETALHADOS
    # ────────────────────────────
    with tab2:
        col_x, col_y = st.columns(2)

        with col_x:
            st.markdown('<div class="section-header">// BREAKDOWN DE AQUISIÇÃO</div>',
                        unsafe_allow_html=True)
            breakdown = {
                "Lance Inicial":        custos["lance"],
                "Comissão Leiloeiro":   custos["comissao"],
                "ITBI":                 custos["itbi"],
                "Escritura / Cartório": custos["escritura"],
                "Outros (reforma+deb)": custos["outros"],
            }
            rows = [{"Item": k, "Valor": format_brl(v), "% do Lance": f"{v/lance*100:.2f}%"}
                    for k, v in breakdown.items()]
            rows.append({"Item": "─────────────", "Valor": "──────────", "% do Lance": "──────"})
            rows.append({"Item": "CUSTO TOTAL", "Valor": format_brl(custos["total"]),
                         "% do Lance": f"{custos['total']/lance*100:.2f}%"})
            df_bd = pd.DataFrame(rows)
            st.dataframe(df_bd, hide_index=True, use_container_width=True,
                         column_config={
                             "Item":        st.column_config.TextColumn(width="medium"),
                             "Valor":       st.column_config.TextColumn(width="small"),
                             "% do Lance":  st.column_config.TextColumn(width="small"),
                         })

        with col_y:
            st.markdown('<div class="section-header">// DÉBITOS & RESPONSABILIDADES</div>',
                        unsafe_allow_html=True)
            deb_rows = [
                {"Débito": "IPTU Atrasado",       "Valor": format_brl(debito_iptu),
                 "Resp.": "VENDEDORA ← propter rem"},
                {"Débito": "Condomínio Atrasado",  "Valor": format_brl(debito_cond),
                 "Resp.": "VENDEDORA ← propter rem"},
                {"Débito": "Outros (→ comprador)", "Valor": format_brl(debito_outros),
                 "Resp.": "COMPRADOR"},
                {"Débito": "Total s/ vendedora",   "Valor": format_brl(debito_vendedora),
                 "Resp.": "Exigir quitação"},
            ]
            st.dataframe(pd.DataFrame(deb_rows), hide_index=True, use_container_width=True)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">// RESUMO P&L</div>',
                        unsafe_allow_html=True)
            pl_rows = [
                {"Item": "VGV (Valor de Mercado)",   "Valor": format_brl(vgv)},
                {"Item": "(-) Custo Total",          "Valor": format_brl(-custos["total"])},
                {"Item": "= Ganho Bruto",            "Valor": format_brl(ganho_bruto)},
                {"Item": "(-) IGC 15%",              "Valor": format_brl(-igc)},
                {"Item": "= LUCRO LÍQUIDO",          "Valor": format_brl(lucro_liq)},
            ]
            st.dataframe(pd.DataFrame(pl_rows), hide_index=True, use_container_width=True)

    # ────────────────────────────
    #  TAB 3 · TIR & PROJEÇÕES
    # ────────────────────────────
    with tab3:
        col_p, col_q = st.columns([2, 3])

        with col_p:
            st.markdown('<div class="section-header">// TAXA INTERNA DE RETORNO</div>',
                        unsafe_allow_html=True)
            tir_rows = []
            for meses, tir in [(12, tir_12), (18, tir_18)]:
                if tir is not None:
                    tir_rows.append({
                        "Horizonte":    f"{meses} meses",
                        "TIR Anual":    f"{tir*100:.1f}%",
                        "Classificação": "✅ Excelente" if tir > 0.20
                                         else "⚡ Bom" if tir > 0.12
                                         else "⚠ Atenção" if tir > 0
                                         else "❌ Negativo",
                    })
                else:
                    tir_rows.append({"Horizonte": f"{meses} meses",
                                     "TIR Anual": "N/C", "Classificação": "—"})
            st.dataframe(pd.DataFrame(tir_rows), hide_index=True, use_container_width=True)

            st.markdown('<div class="section-header">// INDICADORES-CHAVE</div>',
                        unsafe_allow_html=True)
            ind_rows = [
                {"Indicador": "Desconto s/ Mercado",
                 "Valor": f"{(1 - lance/vgv)*100:.1f}%" if vgv > 0 else "—"},
                {"Indicador": "Multiplicador (VGV/Custo)",
                 "Valor": f"{vgv/custos['total']:.2f}x" if custos["total"] > 0 else "—"},
                {"Indicador": "R$/m² Adquirido",
                 "Valor": f"R$ {custos['total']/area_adj:,.0f}" if area_adj > 0 else "—"},
                {"Indicador": "R$/m² Mercado",
                 "Valor": f"R$ {m2_medio:,.0f}"},
                {"Indicador": "Spread (m² mercado - adq.)",
                 "Valor": f"R$ {m2_medio - custos['total']/area_adj:,.0f}" if area_adj > 0 else "—"},
            ]
            st.dataframe(pd.DataFrame(ind_rows), hide_index=True, use_container_width=True)

        with col_q:
            # Gráfico de sensibilidade: lucro vs. % desconto no lance
            descontos   = np.linspace(-0.20, 0.30, 60)
            lances_var  = [lance * (1 - d) for d in descontos]
            lucros_var  = []
            for l_v in lances_var:
                c_v = custo_aquisicao(l_v, comissao_pct, itbi_pct, outros_custos + debito_outros)
                ll, _, _ = lucro_liquido(vgv, c_v["total"])
                lucros_var.append(ll)

            fig3 = go.Figure()
            pos_mask = [v >= 0 for v in lucros_var]
            fig3.add_trace(go.Scatter(
                x=[descontos[i]*100 for i in range(len(descontos)) if pos_mask[i]],
                y=[lucros_var[i]    for i in range(len(lucros_var))  if pos_mask[i]],
                fill="tozeroy", fillcolor="rgba(0,204,136,0.08)",
                line=dict(color="#00cc88", width=2), name="Lucro +",
                hovertemplate="Desconto: %{x:.1f}%<br>Lucro: R$ %{y:,.0f}<extra></extra>",
            ))
            neg_mask = [v < 0 for v in lucros_var]
            fig3.add_trace(go.Scatter(
                x=[descontos[i]*100 for i in range(len(descontos)) if neg_mask[i]],
                y=[lucros_var[i]    for i in range(len(lucros_var))  if neg_mask[i]],
                fill="tozeroy", fillcolor="rgba(255,68,85,0.08)",
                line=dict(color="#ff4455", width=2), name="Prejuízo",
                hovertemplate="Desconto: %{x:.1f}%<br>Resultado: R$ %{y:,.0f}<extra></extra>",
            ))
            # marca lance atual
            current_discount = 0.0
            fig3.add_vline(x=current_discount, line_dash="dot",
                           line_color="#ffaa33", line_width=1,
                           annotation_text=" lance atual",
                           annotation_font=dict(color="#ffaa33", size=9))
            fig3.update_layout(
                **PLOTLY_LAYOUT,
                title="Sensibilidade · Lucro Líquido vs. Variação do Lance",
                xaxis_title="Variação no Lance (%)",
                yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
                showlegend=False, height=360,
            )
            st.plotly_chart(fig3, use_container_width=True)

    # ────────────────────────────
    #  TAB 4 · COMPARÁVEIS
    # ────────────────────────────
    with tab4:
        st.markdown('<div class="section-header">// PESQUISA DE MERCADO · IMÓVEIS COMPARÁVEIS</div>',
                    unsafe_allow_html=True)

        if not any([url1, url2, url3]):
            st.markdown("""
            <div style='font-family: Share Tech Mono, monospace; font-size: 0.75rem;
                        color: #4a6a8a; padding: 0.5rem 0'>
                ℹ URLs não informadas · utilizando base sintética regional para {}.
            </div>
            """.format(regiao), unsafe_allow_html=True)

        # Tabela de comparáveis
        comp_display = comp_df.copy()
        comp_display["Preço Total"] = comp_display["Preço Total"].apply(format_brl)
        comp_display["R$/m²"]      = comp_display["R$/m²"].apply(lambda x: f"R$ {x:,.0f}")
        st.dataframe(comp_display, hide_index=True, use_container_width=True,
                     column_config={
                         "Endereço":    st.column_config.TextColumn(width="large"),
                         "Área (m²)":  st.column_config.NumberColumn(width="small"),
                         "Preço Total": st.column_config.TextColumn(width="medium"),
                         "R$/m²":      st.column_config.TextColumn(width="medium"),
                         "Fonte":      st.column_config.TextColumn(width="large"),
                     })

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        col_r, col_s = st.columns(2)

        with col_r:
            # Scatter: área vs preço total
            fig4 = go.Figure()
            areas   = [c["Área (m²)"] for c in comps]
            totais  = [c["Preço Total"] for c in comps]
            labels  = [f"Comp {i+1}" for i in range(len(comps))]
            fig4.add_trace(go.Scatter(
                x=areas, y=totais, mode="markers+text",
                text=labels, textposition="top center",
                marker=dict(size=14, color=["#2a7aaa", "#4a9acc", "#6ab8cc"],
                            line=dict(color="#88ccff", width=1)),
                hovertemplate="%{text}<br>Área: %{x}m²<br>Preço: R$ %{y:,.0f}<extra></extra>",
            ))
            # marca o imóvel do leilão
            fig4.add_trace(go.Scatter(
                x=[area_util], y=[lance],
                mode="markers+text", text=["LEILÃO"],
                textposition="top center",
                marker=dict(size=18, color="#ffaa33", symbol="diamond",
                            line=dict(color="#ffcc55", width=2)),
                hovertemplate="LEILÃO<br>Área: %{x}m²<br>Lance: R$ %{y:,.0f}<extra></extra>",
            ))
            fig4.update_layout(
                **PLOTLY_LAYOUT,
                title="Dispersão · Área vs. Preço",
                xaxis_title="Área (m²)", yaxis_title="Preço Total",
                yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
                showlegend=False, height=320,
            )
            st.plotly_chart(fig4, use_container_width=True)

        with col_s:
            # Gauge de posicionamento de preço
            pct_mercado = (lance / vgv * 100) if vgv > 0 else 100
            fig5 = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=pct_mercado,
                number=dict(suffix="%", font=dict(family="Share Tech Mono", color="#a8c8e8", size=28)),
                delta=dict(reference=100, valueformat=".1f",
                           increasing=dict(color="#ff4455"),
                           decreasing=dict(color="#00cc88")),
                gauge=dict(
                    axis=dict(range=[0, 130], tickcolor="#1a2e42",
                              tickfont=dict(family="Share Tech Mono", size=9, color="#4a6a8a")),
                    bar=dict(color="#2a7aaa", thickness=0.25),
                    bgcolor="#080c10",
                    borderwidth=1, bordercolor="#1a2e42",
                    steps=[
                        dict(range=[0, 70],   color="#0a1a10"),
                        dict(range=[70, 90],  color="#0a1a18"),
                        dict(range=[90, 110], color="#1a1008"),
                        dict(range=[110, 130], color="#1a0808"),
                    ],
                    threshold=dict(line=dict(color="#00cc88", width=2), value=80),
                ),
                title=dict(text="Lance / Valor de Mercado",
                           font=dict(family="Share Tech Mono", color="#4a6a8a", size=11)),
            ))
            fig5.update_layout(
                **PLOTLY_LAYOUT,
                height=320,
            )
            st.plotly_chart(fig5, use_container_width=True)

    # ── FOOTER ──
    st.markdown("""
    <hr style='border:none; border-top:1px solid #1a2e42; margin: 2rem 0 1rem'>
    <div style='font-family: Share Tech Mono, monospace; font-size:0.6rem;
                color:#2a4a6a; text-align:center; letter-spacing:2px'>
        LEILÃO INTEL · WEALTH MANAGEMENT DESK · DADOS PARA FINS ANALÍTICOS ·
        NÃO CONSTITUI OFERTA OU RECOMENDAÇÃO DE INVESTIMENTO
    </div>
    """, unsafe_allow_html=True)
