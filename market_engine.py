"""
LEILÃO INTEL — Market Intelligence Engine
Geocodificação + FipeZap + Scraping ZAP/VivaReal/OLX
Para uso no Streamlit Cloud (acesso livre à internet)
"""

import requests
import re
import json
import time
import random
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional

# ─────────────────────────────────────────────
#  DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class GeoResult:
    lat: float
    lon: float
    bairro: str
    cidade: str
    cep: str
    estado: str
    endereco_formatado: str

@dataclass
class ComparableImovel:
    titulo: str
    endereco: str
    bairro: str
    area_m2: float
    preco_total: float
    preco_m2: float
    fonte: str
    url: str

@dataclass
class MarketResult:
    bairro: str
    cidade: str
    preco_m2_fipezap: float       # FipeZap oficial
    preco_m2_medio: float          # Média dos comparáveis
    preco_m2_min: float
    preco_m2_max: float
    comparaveis: list
    fonte_principal: str
    confiabilidade: str            # "Alta", "Média", "Baixa"
    nota: str

# ─────────────────────────────────────────────
#  BASE DE PREÇOS FIPEZAP (SP + Grande SP)
#  Dados referência Março/2025 — fonte FipeZap
# ─────────────────────────────────────────────

FIPEZAP_BASE = {
    # SP Capital — bairros nobres
    "pinheiros":         {"m2": 17_800, "cidade": "São Paulo"},
    "vila madalena":     {"m2": 16_500, "cidade": "São Paulo"},
    "jardins":           {"m2": 22_000, "cidade": "São Paulo"},
    "jardim paulista":   {"m2": 21_500, "cidade": "São Paulo"},
    "itaim bibi":        {"m2": 20_000, "cidade": "São Paulo"},
    "moema":             {"m2": 18_500, "cidade": "São Paulo"},
    "brooklin":          {"m2": 15_000, "cidade": "São Paulo"},
    "vila olímpia":      {"m2": 16_000, "cidade": "São Paulo"},
    "perdizes":          {"m2": 14_500, "cidade": "São Paulo"},
    "pompeia":           {"m2": 12_800, "cidade": "São Paulo"},
    "lapa":              {"m2": 11_500, "cidade": "São Paulo"},
    "consolação":        {"m2": 15_000, "cidade": "São Paulo"},
    "bela vista":        {"m2": 13_500, "cidade": "São Paulo"},
    "liberdade":         {"m2": 11_000, "cidade": "São Paulo"},
    "aclimação":         {"m2": 12_500, "cidade": "São Paulo"},
    "cambuci":           {"m2": 9_500,  "cidade": "São Paulo"},
    "vila mariana":      {"m2": 14_000, "cidade": "São Paulo"},
    "saúde":             {"m2": 12_000, "cidade": "São Paulo"},
    "ipiranga":          {"m2": 9_800,  "cidade": "São Paulo"},
    "santo andré":       {"m2": 8_500,  "cidade": "São Paulo"},
    # SP Capital — zona norte
    "santana":           {"m2": 10_500, "cidade": "São Paulo"},
    "tucuruvi":          {"m2": 8_800,  "cidade": "São Paulo"},
    "vila guilherme":    {"m2": 9_200,  "cidade": "São Paulo"},
    "casa verde":        {"m2": 8_500,  "cidade": "São Paulo"},
    "limão":             {"m2": 7_800,  "cidade": "São Paulo"},
    "freguesia do ó":    {"m2": 7_500,  "cidade": "São Paulo"},
    "pirituba":          {"m2": 7_200,  "cidade": "São Paulo"},
    # SP Capital — zona leste
    "tatuapé":           {"m2": 10_000, "cidade": "São Paulo"},
    "mooca":             {"m2": 10_500, "cidade": "São Paulo"},
    "belém":             {"m2": 9_000,  "cidade": "São Paulo"},
    "penha":             {"m2": 8_000,  "cidade": "São Paulo"},
    "vila prudente":     {"m2": 8_500,  "cidade": "São Paulo"},
    "são mateus":        {"m2": 6_500,  "cidade": "São Paulo"},
    "itaquera":          {"m2": 6_200,  "cidade": "São Paulo"},
    "guaianases":        {"m2": 5_800,  "cidade": "São Paulo"},
    # SP Capital — zona sul
    "santo amaro":       {"m2": 11_000, "cidade": "São Paulo"},
    "campo belo":        {"m2": 13_000, "cidade": "São Paulo"},
    "interlagos":        {"m2": 8_000,  "cidade": "São Paulo"},
    "parelheiros":       {"m2": 5_500,  "cidade": "São Paulo"},
    "grajaú":            {"m2": 5_800,  "cidade": "São Paulo"},
    "socorro":           {"m2": 6_500,  "cidade": "São Paulo"},
    "cursino":           {"m2": 9_000,  "cidade": "São Paulo"},
    "jabaquara":         {"m2": 9_500,  "cidade": "São Paulo"},
    # Grande SP
    "guarulhos":         {"m2": 7_500,  "cidade": "Guarulhos"},
    "centro guarulhos":  {"m2": 6_800,  "cidade": "Guarulhos"},
    "santo andré":       {"m2": 8_200,  "cidade": "Santo André"},
    "centro santo andré":{"m2": 7_500,  "cidade": "Santo André"},
    "são bernardo do campo":{"m2": 8_000,"cidade": "São Bernardo do Campo"},
    "centro sbc":        {"m2": 7_200,  "cidade": "São Bernardo do Campo"},
    "são caetano do sul":{"m2": 10_500, "cidade": "São Caetano do Sul"},
    "diadema":           {"m2": 6_500,  "cidade": "Diadema"},
    "mauá":              {"m2": 6_200,  "cidade": "Mauá"},
    "osasco":            {"m2": 7_800,  "cidade": "Osasco"},
    "centro osasco":     {"m2": 7_000,  "cidade": "Osasco"},
    "carapicuíba":       {"m2": 6_000,  "cidade": "Carapicuíba"},
    "barueri":           {"m2": 8_500,  "cidade": "Barueri"},
    "alphaville":        {"m2": 12_000, "cidade": "Barueri"},
    "santana de parnaíba":{"m2": 9_000, "cidade": "Santana de Parnaíba"},
    "cotia":             {"m2": 6_800,  "cidade": "Cotia"},
    "taboão da serra":   {"m2": 7_000,  "cidade": "Taboão da Serra"},
    "embu das artes":    {"m2": 6_000,  "cidade": "Embu das Artes"},
    "mogi das cruzes":   {"m2": 6_500,  "cidade": "Mogi das Cruzes"},
    "suzano":            {"m2": 5_800,  "cidade": "Suzano"},
    "itaquaquecetuba":   {"m2": 5_200,  "cidade": "Itaquaquecetuba"},
    "ferraz de vasconcelos":{"m2": 5_000,"cidade": "Ferraz de Vasconcelos"},
}

# Médias por cidade (fallback quando bairro não encontrado)
FIPEZAP_CIDADE = {
    "são paulo":              9_800,
    "guarulhos":              7_200,
    "santo andré":            8_000,
    "são bernardo do campo":  7_800,
    "são caetano do sul":    10_200,
    "diadema":                6_300,
    "mauá":                   6_000,
    "osasco":                 7_500,
    "barueri":                8_200,
    "carapicuíba":            5_800,
    "cotia":                  6_600,
    "taboão da serra":        6_800,
    "embu das artes":         5_800,
    "mogi das cruzes":        6_300,
    "suzano":                 5_600,
    "santana de parnaíba":    8_800,
    "default":                7_000,
}

# ─────────────────────────────────────────────
#  GEOCODIFICAÇÃO
# ─────────────────────────────────────────────

def geocodificar_endereco(endereco: str, gmaps_key: str = "") -> Optional[GeoResult]:
    """
    Tenta geocodificar em cascata:
    1. Google Maps API (se tiver key)
    2. OpenStreetMap Nominatim (gratuito)
    3. ViaCEP (se tiver CEP no endereço)
    """
    # Limpeza do endereço
    end_limpo = re.sub(r'\s+', ' ', endereco).strip()

    # ── 1. Google Maps ──
    if gmaps_key and gmaps_key not in ("", "DEMO", "SUA_KEY_AQUI"):
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            r = requests.get(url, params={
                "address": end_limpo + ", São Paulo, Brasil",
                "key": gmaps_key,
                "language": "pt-BR",
            }, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if data.get("results"):
                    res = data["results"][0]
                    loc = res["geometry"]["location"]
                    comps = {c["types"][0]: c["long_name"]
                             for c in res.get("address_components", [])
                             if c.get("types")}
                    return GeoResult(
                        lat=loc["lat"], lon=loc["lng"],
                        bairro=comps.get("sublocality_level_1",
                               comps.get("neighborhood", "")),
                        cidade=comps.get("administrative_area_level_2", "São Paulo"),
                        cep=comps.get("postal_code", ""),
                        estado=comps.get("administrative_area_level_1", "SP"),
                        endereco_formatado=res.get("formatted_address", end_limpo),
                    )
        except Exception:
            pass

    # ── 2. OpenStreetMap Nominatim ──
    try:
        url = "https://nominatim.openstreetmap.org/search"
        r = requests.get(url, params={
            "q": end_limpo + ", São Paulo, Brasil",
            "format": "json", "limit": 1,
            "addressdetails": 1,
        }, headers={"User-Agent": "LeilaoIntel/3.0 (wealth@leilao.app)"},
        timeout=10)
        if r.status_code == 200 and r.json():
            res = r.json()[0]
            addr = res.get("address", {})
            return GeoResult(
                lat=float(res["lat"]), lon=float(res["lon"]),
                bairro=addr.get("suburb", addr.get("neighbourhood",
                       addr.get("quarter", ""))),
                cidade=addr.get("city", addr.get("town", "São Paulo")),
                cep=addr.get("postcode", ""),
                estado=addr.get("state", "SP"),
                endereco_formatado=res.get("display_name", end_limpo),
            )
    except Exception:
        pass

    # ── 3. CEP via ViaCEP ──
    cep_match = re.search(r'\d{5}-?\d{3}', end_limpo)
    if cep_match:
        try:
            cep = cep_match.group().replace("-", "")
            r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=6)
            if r.status_code == 200:
                d = r.json()
                if not d.get("erro"):
                    return GeoResult(
                        lat=0.0, lon=0.0,
                        bairro=d.get("bairro", ""),
                        cidade=d.get("localidade", "São Paulo"),
                        cep=cep, estado=d.get("uf", "SP"),
                        endereco_formatado=f"{d.get('logradouro','')} — {d.get('bairro','')} — {d.get('localidade','')}",
                    )
        except Exception:
            pass

    # ── 4. Parse manual do endereço ──
    return _parse_endereco_manual(end_limpo)


def _parse_endereco_manual(endereco: str) -> Optional[GeoResult]:
    """Extrai bairro/cidade do texto do endereço sem API."""
    end_lower = endereco.lower()
    # Tenta identificar cidade da Grande SP
    cidades_grande_sp = [
        "guarulhos", "santo andré", "são bernardo", "são caetano",
        "diadema", "mauá", "osasco", "barueri", "carapicuíba",
        "cotia", "taboão", "embu", "mogi das cruzes", "suzano",
        "santana de parnaíba", "ferraz", "itaquaquecetuba"
    ]
    cidade = "São Paulo"
    for c in cidades_grande_sp:
        if c in end_lower:
            cidade = c.title()
            break

    # Detecta bairro
    bairro = ""
    for b in FIPEZAP_BASE.keys():
        if b in end_lower:
            bairro = b.title()
            break

    return GeoResult(
        lat=0.0, lon=0.0,
        bairro=bairro, cidade=cidade, cep="", estado="SP",
        endereco_formatado=endereco,
    )

# ─────────────────────────────────────────────
#  FIPEZAP LOOKUP
# ─────────────────────────────────────────────

def buscar_preco_fipezap(bairro: str, cidade: str) -> tuple[float, str]:
    """
    Retorna (preco_m2, fonte_descricao).
    Cascata: bairro exato → bairro fuzzy → cidade → default
    """
    b = bairro.lower().strip()
    c = cidade.lower().strip()

    # Match exato de bairro
    if b in FIPEZAP_BASE:
        return FIPEZAP_BASE[b]["m2"], f"FipeZap · Bairro: {bairro.title()}"

    # Match parcial de bairro (fuzzy)
    for key, val in FIPEZAP_BASE.items():
        if b and (b in key or key in b):
            return val["m2"], f"FipeZap · Bairro similar: {key.title()}"

    # Fallback por cidade
    for key, preco in FIPEZAP_CIDADE.items():
        if key in c or c in key:
            return preco, f"FipeZap · Média cidade: {cidade.title()}"

    return FIPEZAP_CIDADE["default"], "FipeZap · Média regional SP"


# ─────────────────────────────────────────────
#  SCRAPING ZAP IMÓVEIS
# ─────────────────────────────────────────────

HEADERS_SCRAPING = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def _extrair_valor(texto: str) -> float:
    """Extrai valor numérico de string monetária BR."""
    t = re.sub(r'[R$\s]', '', texto)
    t = t.replace('.', '').replace(',', '.')
    m = re.search(r'\d+\.?\d*', t)
    return float(m.group()) if m else 0.0

def _extrair_area(texto: str) -> float:
    """Extrai área em m² do texto."""
    m = re.search(r'([\d.,]+)\s*m[²2]?', texto, re.IGNORECASE)
    if m:
        return _extrair_valor(m.group(1))
    return 0.0

def scrape_zap(bairro: str, cidade: str, tipo: str = "apartamento") -> list[ComparableImovel]:
    """Busca comparáveis no ZAP Imóveis."""
    resultados = []
    cidade_slug = cidade.lower().replace(" ", "-").replace("ã", "a").replace("ç", "c")
    bairro_slug = bairro.lower().replace(" ", "-").replace("ã", "a").replace("ç", "c")

    url = (f"https://www.zapimoveis.com.br/venda/{tipo}s/"
           f"sp+{cidade_slug}+{bairro_slug}/")

    try:
        r = requests.get(url, headers=HEADERS_SCRAPING, timeout=12)
        if r.status_code != 200:
            return resultados

        soup = BeautifulSoup(r.text, 'html.parser')

        # ZAP usa JSON-LD e data attributes
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data[:5]:
                        if item.get('@type') == 'Product':
                            preco = item.get('offers', {}).get('price', 0)
                            if preco:
                                resultados.append(ComparableImovel(
                                    titulo=item.get('name', '')[:60],
                                    endereco=item.get('description', '')[:80],
                                    bairro=bairro,
                                    area_m2=0,
                                    preco_total=float(preco),
                                    preco_m2=0,
                                    fonte="ZAP Imóveis",
                                    url=url,
                                ))
            except Exception:
                continue

        # Fallback: cards HTML
        if not resultados:
            cards = soup.select('[data-type="property"]')[:5]
            for card in cards:
                try:
                    preco_el = card.select_one('[class*="price"]')
                    area_el  = card.select_one('[class*="area"]')
                    title_el = card.select_one('[class*="title"]')
                    if preco_el and area_el:
                        preco = _extrair_valor(preco_el.text)
                        area  = _extrair_area(area_el.text)
                        if preco > 50_000 and area > 20:
                            resultados.append(ComparableImovel(
                                titulo=title_el.text.strip()[:60] if title_el else "Imóvel ZAP",
                                endereco=bairro + ", " + cidade,
                                bairro=bairro,
                                area_m2=area,
                                preco_total=preco,
                                preco_m2=preco / area if area else 0,
                                fonte="ZAP Imóveis",
                                url=url,
                            ))
                except Exception:
                    continue

    except Exception:
        pass

    return resultados


def scrape_vivareal(bairro: str, cidade: str, tipo: str = "apartamento") -> list[ComparableImovel]:
    """Busca comparáveis no VivaReal."""
    resultados = []
    cidade_slug = cidade.lower().replace(" ", "-")
    bairro_slug = bairro.lower().replace(" ", "-")

    url = (f"https://www.vivareal.com.br/venda/{tipo}/"
           f"sp/{cidade_slug}/{bairro_slug}/")

    try:
        r = requests.get(url, headers=HEADERS_SCRAPING, timeout=12)
        if r.status_code != 200:
            return resultados

        soup = BeautifulSoup(r.text, 'html.parser')

        # VivaReal usa JSON no __NEXT_DATA__ ou data-json
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data:
            try:
                data = json.loads(next_data.string)
                listings = (data.get('props', {})
                               .get('pageProps', {})
                               .get('searchResult', {})
                               .get('listings', []))
                for item in listings[:5]:
                    listing = item.get('listing', {})
                    preco = listing.get('pricingInfos', [{}])[0].get('price', 0)
                    area  = listing.get('usableAreas', [0])[0]
                    if preco and area:
                        resultados.append(ComparableImovel(
                            titulo=listing.get('title', 'Imóvel VivaReal')[:60],
                            endereco=listing.get('address', {}).get('street', bairro),
                            bairro=bairro,
                            area_m2=float(area),
                            preco_total=float(preco),
                            preco_m2=float(preco) / float(area) if area else 0,
                            fonte="VivaReal",
                            url=url,
                        ))
            except Exception:
                pass

        # Fallback: cards
        if not resultados:
            cards = soup.select('.property-card__container')[:5]
            for card in cards:
                try:
                    preco_el = card.select_one('.property-card__price')
                    area_el  = card.select_one('[class*="area"]')
                    title_el = card.select_one('.property-card__title')
                    if preco_el:
                        preco = _extrair_valor(preco_el.text)
                        area  = _extrair_area(area_el.text) if area_el else 0
                        if preco > 50_000:
                            resultados.append(ComparableImovel(
                                titulo=title_el.text.strip()[:60] if title_el else "Imóvel VivaReal",
                                endereco=bairro + ", " + cidade,
                                bairro=bairro,
                                area_m2=area,
                                preco_total=preco,
                                preco_m2=preco / area if area else 0,
                                fonte="VivaReal",
                                url=url,
                            ))
                except Exception:
                    continue

    except Exception:
        pass

    return resultados


def scrape_olx(bairro: str, cidade: str) -> list[ComparableImovel]:
    """Busca comparáveis no OLX Imóveis."""
    resultados = []
    try:
        cidade_slug = cidade.lower().replace(" ", "-")
        bairro_slug = bairro.lower().replace(" ", "+")
        url = f"https://www.olx.com.br/imoveis/venda/estado-sp?q={bairro_slug}"
        r = requests.get(url, headers=HEADERS_SCRAPING, timeout=12)
        if r.status_code != 200:
            return resultados

        soup = BeautifulSoup(r.text, 'html.parser')
        # OLX usa JSON no __PRELOADED_STATE__
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and '__PRELOADED_STATE__' in (script.string or ''):
                try:
                    raw = re.search(r'__PRELOADED_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                    if raw:
                        data = json.loads(raw.group(1))
                        ads = data.get('listing', {}).get('ads', [])
                        for ad in ads[:5]:
                            preco = ad.get('price', '0')
                            preco_num = _extrair_valor(str(preco))
                            area = 0
                            for prop in ad.get('properties', []):
                                if prop.get('name') == 'size':
                                    area = float(prop.get('value', 0))
                            if preco_num > 50_000:
                                resultados.append(ComparableImovel(
                                    titulo=ad.get('title', 'Imóvel OLX')[:60],
                                    endereco=ad.get('location', {}).get('neighbourhood', bairro),
                                    bairro=bairro,
                                    area_m2=area,
                                    preco_total=preco_num,
                                    preco_m2=preco_num / area if area else 0,
                                    fonte="OLX Imóveis",
                                    url=ad.get('url', url),
                                ))
                except Exception:
                    pass
                break
    except Exception:
        pass
    return resultados


# ─────────────────────────────────────────────
#  ENGINE PRINCIPAL
# ─────────────────────────────────────────────

def buscar_mercado(
    endereco: str,
    area_util: float,
    gmaps_key: str = "",
    usar_scraping: bool = True,
    tipo_imovel: str = "apartamento",
) -> MarketResult:
    """
    Motor principal de inteligência de mercado.
    1. Geocodifica o endereço
    2. Busca preço FipeZap para o bairro
    3. Busca comparáveis via scraping (ZAP + VivaReal + OLX)
    4. Calcula média ponderada e retorna MarketResult
    """

    # ── Geocodificação ──
    geo = geocodificar_endereco(endereco, gmaps_key)
    bairro = geo.bairro if geo else ""
    cidade = geo.cidade if geo else "São Paulo"

    # ── FipeZap ──
    preco_fipezap, fonte_fipezap = buscar_preco_fipezap(bairro, cidade)

    # ── Scraping ──
    comparaveis_raw = []
    if usar_scraping:
        # ZAP
        zap = scrape_zap(bairro, cidade, tipo_imovel)
        comparaveis_raw.extend(zap)
        time.sleep(random.uniform(0.5, 1.5))

        # VivaReal
        viva = scrape_vivareal(bairro, cidade, tipo_imovel)
        comparaveis_raw.extend(viva)
        time.sleep(random.uniform(0.5, 1.5))

        # OLX
        olx = scrape_olx(bairro, cidade)
        comparaveis_raw.extend(olx)

    # ── Calcular m² dos comparáveis ──
    comps_validos = []
    for c in comparaveis_raw:
        # Se não tiver área, estima pela área do imóvel em análise ±20%
        if c.area_m2 <= 0:
            c.area_m2 = area_util
        if c.preco_m2 <= 0 and c.preco_total > 0 and c.area_m2 > 0:
            c.preco_m2 = c.preco_total / c.area_m2
        # Filtro de sanidade: R$/m² entre 3k e 50k
        if 3_000 < c.preco_m2 < 50_000:
            comps_validos.append(c)

    # ── Se sem comparáveis reais, gera sintéticos baseados no FipeZap ──
    if not comps_validos:
        variações = [-0.08, 0.0, +0.08]
        nomes = ["Comparável A", "Comparável B", "Comparável C"]
        import random as _rnd
        for i, var in enumerate(variações):
            preco_m2 = preco_fipezap * (1 + var)
            area_sim = area_util * _rnd.uniform(0.85, 1.15)
            comps_validos.append(ComparableImovel(
                titulo=nomes[i],
                endereco=f"Bairro {bairro or cidade}",
                bairro=bairro,
                area_m2=round(area_sim, 1),
                preco_total=preco_m2 * area_sim,
                preco_m2=preco_m2,
                fonte=f"FipeZap estimado ({fonte_fipezap})",
                url="",
            ))

    # ── Estatísticas ──
    precos = [c.preco_m2 for c in comps_validos]
    preco_medio  = sum(precos) / len(precos)
    preco_min    = min(precos)
    preco_max    = max(precos)

    # ── Confiabilidade ──
    n_reais = sum(1 for c in comps_validos if "FipeZap" not in c.fonte)
    if n_reais >= 3:
        confiabilidade = "Alta"
        nota = f"{n_reais} comparáveis reais dos portais + FipeZap"
    elif n_reais >= 1:
        confiabilidade = "Média"
        nota = f"{n_reais} comparável(is) real(is) + estimativas FipeZap"
    else:
        confiabilidade = "Baixa"
        nota = "Estimativa FipeZap (scraping indisponível ou bloqueado)"

    return MarketResult(
        bairro=bairro or cidade,
        cidade=cidade,
        preco_m2_fipezap=preco_fipezap,
        preco_m2_medio=preco_medio,
        preco_m2_min=preco_min,
        preco_m2_max=preco_max,
        comparaveis=comps_validos[:6],  # máx 6 comparáveis
        fonte_principal=fonte_fipezap,
        confiabilidade=confiabilidade,
        nota=nota,
    )
