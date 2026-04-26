"""
LEILÃO INTEL — Gemini PDF Parser
Leitura inteligente de editais via Google Gemini API
Suporta qualquer formato de leiloeira
"""

import json
import re
import base64
import streamlit as st
from typing import Optional

# ─────────────────────────────────────────────
#  PROMPT DE EXTRAÇÃO
# ─────────────────────────────────────────────

PROMPT_EXTRACAO = """
Você é um especialista em análise de editais de leilão imobiliário no Brasil.
Analise o edital PDF fornecido e extraia TODAS as informações abaixo.

RETORNE APENAS um JSON válido, sem texto antes ou depois, sem markdown, sem ```json.
Se um campo não existir no edital, use null para texto e 0 para números.

{
  "leiloeira_nome": "nome da empresa leiloeira",
  "tipo_leilao": "Extrajudicial ou Judicial",
  "plataforma": "url do site de lances (ex: bcoleiloes.com.br)",
  "numero_processo": "número do processo judicial se houver",
  "matricula": "número da matrícula do imóvel no cartório",
  "comarca": "comarca ou cartório de registro",
  "vara": "vara judicial se houver",
  
  "endereco": "endereço completo do imóvel incluindo bairro cidade e CEP",
  "bairro": "bairro do imóvel",
  "cidade": "cidade do imóvel",
  "cep": "CEP se mencionado",
  
  "area_util": número em m² da área útil ou privativa (apenas o número, sem texto),
  "area_total": número em m² da área total ou construída (apenas o número, sem texto),
  
  "avaliacao": valor numérico de avaliação em reais (apenas o número, sem R$ ou pontos),
  
  "lance_na_plataforma": true se o lance inicial não constar no PDF e estiver apenas na plataforma online,
  "lance_1praca": valor numérico do lance mínimo da 1ª praça em reais (0 se não constar),
  "lance_2praca": valor numérico do lance mínimo da 2ª praça em reais (0 se não constar),
  "data_1praca": "data da 1ª praça no formato DD/MM/AAAA",
  "data_2praca": "data da 2ª praça no formato DD/MM/AAAA",
  "data_leilao": "data do leilão no formato DD/MM/AAAA",
  
  "comissao_pct": porcentagem numérica da comissão do leiloeiro (padrão 5 se não mencionado),
  "itbi_pct": porcentagem do ITBI se mencionado (0 se não),
  
  "iptu_debito": valor numérico de débitos de IPTU em reais (0 se não houver ou não informado),
  "cond_debito": valor numérico de débitos de condomínio em reais (0 se não houver ou não informado),
  
  "ad_corpus": true se o edital mencionar cláusula "ad corpus",
  "venda_condicionada": true se a venda depender de aprovação do comitente ou vendedor,
  "debitos_vendedora": true se o edital confirmar que IPTU e condomínio são responsabilidade da vendedora,
  
  "tipo_imovel": "apartamento, casa, cobertura, sala, galpão, terreno, etc",
  "observacoes": "outras informações relevantes não capturadas acima, máximo 200 caracteres"
}

REGRAS IMPORTANTES:
- Para valores monetários: converta "R$ 1.234.567,89" para 1234567.89
- Para áreas: "116,700 m²" vira 116.7
- Se o lance só está disponível na plataforma online (não consta no PDF), coloque lance_na_plataforma: true e lance_1praca: 0
- Para datas por extenso como "15 de março de 2026", converta para "15/03/2026"
- Se houver apenas uma praça ou apenas data do leilão, preencha somente data_leilao e data_1praca
- Retorne APENAS o JSON, nada mais
"""

# ─────────────────────────────────────────────
#  FUNÇÃO PRINCIPAL
# ─────────────────────────────────────────────

def extrair_com_gemini(pdf_bytes: bytes, api_key: str) -> Optional[dict]:
    """
    Envia o PDF para o Gemini e extrai campos estruturados.
    Retorna dict com os dados ou None se falhar.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Encode PDF em base64
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        # Chamar Gemini com o PDF
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="application/pdf",
                                data=pdf_b64,
                            )
                        ),
                        types.Part(text=PROMPT_EXTRACAO),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,   # baixo para extração precisa
                max_output_tokens=2048,
            ),
        )

        raw = response.text.strip()

        # Limpar possível markdown que o modelo retorne
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
        raw = raw.strip()

        dados_gemini = json.loads(raw)
        return _normalizar_dados(dados_gemini)

    except json.JSONDecodeError as e:
        st.error(f"❌ Gemini retornou resposta inválida: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao chamar Gemini API: {e}")
        return None


def _normalizar_dados(d: dict) -> dict:
    """
    Normaliza e valida os dados retornados pelo Gemini,
    convertendo para o formato esperado pelo dashboard.
    """
    def safe_float(v, default=0.0) -> float:
        try:
            if v is None: return default
            if isinstance(v, (int, float)): return float(v)
            # Remove R$, pontos de milhar, substitui vírgula decimal
            s = re.sub(r'[R$\s]', '', str(v))
            s = s.replace('.', '').replace(',', '.')
            return float(re.search(r'\d+\.?\d*', s).group())
        except:
            return default

    def safe_str(v, default="") -> str:
        if v is None: return default
        return str(v).strip()

    def safe_bool(v, default=False) -> bool:
        if v is None: return default
        if isinstance(v, bool): return v
        return str(v).lower() in ('true', '1', 'sim', 'yes')

    def safe_date(v) -> str:
        if not v: return ""
        s = str(v).strip()
        # Já no formato DD/MM/AAAA
        if re.match(r'\d{2}/\d{2}/\d{4}', s): return s
        # Tenta converter formato AAAA-MM-DD
        m = re.match(r'(\d{4})-(\d{2})-(\d{2})', s)
        if m: return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
        return s

    normalizado = {
        # Identificação
        "leiloeira_nome":   safe_str(d.get("leiloeira_nome")),
        "tipo_leilao":      safe_str(d.get("tipo_leilao")),
        "plataforma":       safe_str(d.get("plataforma")),
        "numero_processo":  safe_str(d.get("numero_processo")),
        "matricula":        safe_str(d.get("matricula")),
        "comarca":          safe_str(d.get("comarca")),
        "vara":             safe_str(d.get("vara")),
        # Localização
        "endereco":         safe_str(d.get("endereco")),
        "bairro":           safe_str(d.get("bairro")),
        "cidade":           safe_str(d.get("cidade")),
        "cep":              safe_str(d.get("cep")),
        # Áreas
        "area_util":        safe_float(d.get("area_util")),
        "area_total":       safe_float(d.get("area_total")),
        # Financeiro
        "avaliacao":        safe_float(d.get("avaliacao")),
        "lance_na_plataforma": safe_bool(d.get("lance_na_plataforma")),
        "lance_1praca":     safe_float(d.get("lance_1praca")),
        "lance_2praca":     safe_float(d.get("lance_2praca")),
        "data_1praca":      safe_date(d.get("data_1praca")),
        "data_2praca":      safe_date(d.get("data_2praca")),
        "data_leilao":      safe_date(d.get("data_leilao")),
        "comissao_pct":     safe_float(d.get("comissao_pct"), 5.0) or 5.0,
        "itbi_pct":         safe_float(d.get("itbi_pct"), 3.0) or 3.0,
        # Débitos
        "iptu_debito":      safe_float(d.get("iptu_debito")),
        "cond_debito":      safe_float(d.get("cond_debito")),
        # Flags
        "ad_corpus":        safe_bool(d.get("ad_corpus")),
        "venda_condicionada": safe_bool(d.get("venda_condicionada")),
        "debitos_vendedora":  safe_bool(d.get("debitos_vendedora")),
        # Extra
        "tipo_imovel":      safe_str(d.get("tipo_imovel"), "apartamento"),
        "observacoes":      safe_str(d.get("observacoes")),
        # Metadata
        "_extraidos": [],
        "_avisos": [],
        "_fonte": "gemini",
    }

    # Marca campos extraídos
    campos = [
        ("endereco", "endereco"), ("area_util", "area_util"),
        ("area_total", "area_total"), ("avaliacao", "avaliacao"),
        ("lance_1praca", "lance_1praca"), ("lance_2praca", "lance_2praca"),
        ("data_1praca", "data_1praca"), ("data_2praca", "data_2praca"),
        ("matricula", "matricula"), ("comarca", "comarca"),
        ("numero_processo", "numero_processo"), ("plataforma", "plataforma"),
        ("comissao_pct", "comissao_pct"),
    ]
    for campo, label in campos:
        v = normalizado.get(campo)
        if v and v != 0 and v != "":
            normalizado["_extraidos"].append(label)

    if normalizado["ad_corpus"]:        normalizado["_extraidos"].append("ad_corpus")
    if normalizado["venda_condicionada"]: normalizado["_extraidos"].append("venda_condicionada")
    if normalizado["lance_na_plataforma"]:
        normalizado["_avisos"].append(
            f"⚠ Lance não consta no PDF — consulte {normalizado['plataforma'] or 'a plataforma do leiloeiro'} e insira manualmente."
        )
    if normalizado["debitos_vendedora"]:
        normalizado["_avisos"].append(
            "✅ IPTU e condomínio: responsabilidade da VENDEDORA confirmada pelo Gemini."
        )
    if normalizado.get("observacoes"):
        normalizado["_avisos"].append(f"ℹ {normalizado['observacoes']}")

    return normalizado


def get_api_key() -> str:
    """Busca a API Key do Gemini no Streamlit Secrets ou variável de ambiente."""
    # 1. Streamlit Secrets (produção)
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    # 2. Variável de ambiente (local)
    import os
    key = os.environ.get("GEMINI_API_KEY", "")
    return key
