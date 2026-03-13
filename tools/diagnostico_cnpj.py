"""
AUDIPER - Diagnostico de CNPJ (v2)
Consulta dados de CNPJ via APIs publicas e gera diagnostico enriquecido.

Uso:
  python diagnostico_cnpj.py 12345678000190
  python diagnostico_cnpj.py 12.345.678/0001-90

APIs utilizadas:
  Dados cadastrais (com fallback):
    1. BrasilAPI (brasilapi.com.br)
    2. ReceitaWS (receitaws.com.br)
    3. MinhaReceita (minhareceita.org)
  Sancoes e certidoes:
    4. TCU Certidoes Consolidada (TCU + CNJ + CEIS + CNEP)
  Detalhamento societario:
    5. CNPJ.ws (natureza juridica, socios estrangeiros)
"""

import sys
import json
import re
import ssl
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, date


# ============================================================
# CONFIGURACAO DAS APIs
# ============================================================
APIS = [
    {
        "nome": "BrasilAPI",
        "url": "https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
        "timeout": 10,
    },
    {
        "nome": "ReceitaWS",
        "url": "https://receitaws.com.br/v1/cnpj/{cnpj}",
        "timeout": 15,
    },
    {
        "nome": "MinhaReceita",
        "url": "https://minhareceita.org/{cnpj}",
        "timeout": 10,
    },
]

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="


def limpar_cnpj(cnpj_raw: str) -> str:
    """Remove formatacao do CNPJ, retornando apenas digitos."""
    return re.sub(r"\D", "", cnpj_raw)


def formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ: 12.345.678/0001-90"""
    c = limpar_cnpj(cnpj)
    if len(c) != 14:
        return cnpj
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"


def consultar_cnpj(cnpj: str) -> dict:
    """Consulta CNPJ em multiplas APIs com fallback."""
    cnpj_limpo = limpar_cnpj(cnpj)
    if len(cnpj_limpo) != 14:
        return {"erro": f"CNPJ invalido: {cnpj} ({len(cnpj_limpo)} digitos)"}

    for api in APIS:
        url = api["url"].format(cnpj=cnpj_limpo)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AUDIPER-Diagnostico/1.0"})
            with urllib.request.urlopen(req, timeout=api["timeout"]) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "erro" not in str(data).lower() or "error" not in str(data).lower():
                    data["_api_fonte"] = api["nome"]
                    return normalizar_dados(data, api["nome"])
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
            print(f"  [WARN] {api['nome']} falhou: {e}", file=sys.stderr)
            continue

    return {"erro": "Todas as APIs falharam. Tente novamente em alguns minutos."}


def consultar_certidoes_tcu(cnpj: str) -> list:
    """Consulta TCU Certidoes Consolidada - checa 4 bases de sancoes em 1 chamada."""
    cnpj_limpo = limpar_cnpj(cnpj)
    url = f"https://certidoes-apf.apps.tcu.gov.br/api/rest/publico/certidoes/{cnpj_limpo}?seEmitirPDF=false"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            certidoes = data.get("certidoes", []) if isinstance(data, dict) else []
            return certidoes
    except Exception as e:
        print(f"  [WARN] TCU Certidoes falhou: {e}", file=sys.stderr)
        return []


def consultar_cnpjws(cnpj: str) -> dict:
    """Consulta CNPJ.ws para dados societarios detalhados."""
    cnpj_limpo = limpar_cnpj(cnpj)
    url = f"https://publica.cnpj.ws/cnpj/{cnpj_limpo}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AUDIPER-Diagnostico/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [WARN] CNPJ.ws falhou: {e}", file=sys.stderr)
        return {}


def consultar_cnpja_open(cnpj: str) -> dict:
    """Consulta CNPJa Open para confirmar Simples/MEI/IE/SUFRAMA."""
    cnpj_limpo = limpar_cnpj(cnpj)
    url = f"https://open.cnpja.com/office/{cnpj_limpo}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AUDIPER-Diagnostico/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            simples = data.get("simples", {}) or {}
            simei = data.get("simei", {}) or {}
            registrations = data.get("registrations", []) or []
            return {
                "simples_optante": simples.get("optant", False),
                "simples_desde": simples.get("since", ""),
                "mei_optante": simei.get("optant", False),
                "mei_desde": simei.get("since", ""),
                "inscricoes_estaduais": [
                    {"uf": r.get("state", ""), "numero": r.get("number", ""), "status": r.get("enabled", False)}
                    for r in registrations
                ],
                "suframa": data.get("suframa", {}),
                "_api_fonte": "CNPJa Open",
            }
    except Exception as e:
        print(f"  [WARN] CNPJa Open falhou: {e}", file=sys.stderr)
        return {}


def consultar_datajud_processos(cnpj: str) -> dict:
    """Consulta processos judiciais no DataJud (CNJ) por CNPJ."""
    cnpj_limpo = limpar_cnpj(cnpj)
    indices = [
        ("api_publica_tst", "Justica do Trabalho"),
        ("api_publica_tjsp", "Justica Estadual (SP)"),
        ("api_publica_trf1", "Justica Federal (TRF1)"),
    ]
    todos_processos = []
    total_encontrados = 0

    for indice, nome_justica in indices:
        url = f"https://api-publica.datajud.cnj.jus.br/{indice}/_search"
        body = json.dumps({
            "query": {"match": {"_all": cnpj_limpo}},
            "size": 5,
            "sort": [{"dataAjuizamento": {"order": "desc"}}],
        }).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=body, headers={
                "Authorization": f"ApiKey {DATAJUD_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "AUDIPER-Diagnostico/2.0",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("hits", {}).get("hits", [])
                total = data.get("hits", {}).get("total", {}).get("value", 0)
                total_encontrados += total
                for h in hits:
                    src = h.get("_source", {})
                    todos_processos.append({
                        "numero": src.get("numeroProcesso", ""),
                        "classe": src.get("classeProcessual", ""),
                        "orgao": (src.get("orgaoJulgador") or {}).get("nomeOrgao", ""),
                        "data_ajuizamento": src.get("dataAjuizamento", ""),
                        "justica": nome_justica,
                    })
        except Exception as e:
            print(f"  [WARN] DataJud {indice} falhou: {e}", file=sys.stderr)
            continue

    return {
        "total_encontrados": total_encontrados,
        "processos": todos_processos[:10],
        "_api_fonte": "DataJud (CNJ)",
    }


def consultar_pgfn_divida(cnpj: str) -> dict:
    """Consulta debitos em Divida Ativa da Uniao (PGFN) via DataJud."""
    cnpj_limpo = limpar_cnpj(cnpj)
    url = "https://api-publica.datajud.cnj.jus.br/api_publica_pgfn/_search"
    try:
        params = urllib.parse.urlencode({"q": cnpj_limpo})
        full_url = f"{url}?{params}"
        req = urllib.request.Request(full_url, headers={
            "Authorization": f"ApiKey {DATAJUD_API_KEY}",
            "User-Agent": "AUDIPER-Diagnostico/2.0",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            hits = data.get("hits", {}).get("hits", [])
            total = data.get("hits", {}).get("total", {}).get("value", 0)
            registros = []
            for h in hits[:10]:
                src = h.get("_source", {})
                registros.append({
                    "tipo_devedor": src.get("tipoDevedor", ""),
                    "situacao_inscricao": src.get("situacaoInscricao", ""),
                    "tipo_situacao": src.get("tipoSituacaoInscricao", ""),
                    "receita_principal": src.get("receitaPrincipalDescricao", ""),
                })
            return {
                "total_registros": total,
                "tem_divida": total > 0,
                "registros": registros,
                "_api_fonte": "PGFN / Divida Ativa",
            }
    except Exception as e:
        print(f"  [WARN] PGFN Divida Ativa falhou: {e}", file=sys.stderr)
        return {"total_registros": 0, "tem_divida": False, "registros": [], "_api_fonte": "PGFN (indisponivel)"}


def normalizar_dados(data: dict, fonte: str) -> dict:
    """Normaliza dados de diferentes APIs para formato padrao."""
    if fonte == "BrasilAPI":
        return {
            "cnpj": data.get("cnpj", ""),
            "cnpj_formatado": formatar_cnpj(str(data.get("cnpj", ""))),
            "razao_social": data.get("razao_social", ""),
            "nome_fantasia": data.get("nome_fantasia", ""),
            "situacao_cadastral": _situacao_texto(data.get("descricao_situacao_cadastral", "")),
            "data_situacao": data.get("data_situacao_cadastral", ""),
            "data_inicio": data.get("data_inicio_atividade", ""),
            "cnae_principal": str(data.get("cnae_fiscal", "")),
            "cnae_descricao": data.get("cnae_fiscal_descricao", ""),
            "natureza_juridica": data.get("descricao_natureza_juridica", ""),
            "porte": _porte_texto(data.get("porte", data.get("descricao_porte", ""))),
            "capital_social": float(data.get("capital_social", 0)),
            "opcao_simples": data.get("opcao_pelo_simples", False),
            "opcao_mei": data.get("opcao_pelo_mei", False),
            "uf": data.get("uf", ""),
            "municipio": data.get("municipio", ""),
            "logradouro": data.get("logradouro", ""),
            "numero": data.get("numero", ""),
            "bairro": data.get("bairro", ""),
            "cep": data.get("cep", ""),
            "telefone": data.get("ddd_telefone_1", ""),
            "email": data.get("email", ""),
            "qsa": _normalizar_qsa(data.get("qsa", [])),
            "_api_fonte": fonte,
        }
    elif fonte == "ReceitaWS":
        return {
            "cnpj": limpar_cnpj(data.get("cnpj", "")),
            "cnpj_formatado": data.get("cnpj", ""),
            "razao_social": data.get("nome", ""),
            "nome_fantasia": data.get("fantasia", ""),
            "situacao_cadastral": data.get("situacao", ""),
            "data_situacao": data.get("data_situacao", ""),
            "data_inicio": data.get("abertura", ""),
            "cnae_principal": data.get("atividade_principal", [{}])[0].get("code", ""),
            "cnae_descricao": data.get("atividade_principal", [{}])[0].get("text", ""),
            "natureza_juridica": data.get("natureza_juridica", ""),
            "porte": _porte_texto(data.get("porte", "")),
            "capital_social": _parse_capital(data.get("capital_social", "0")),
            "opcao_simples": data.get("simples", {}).get("optante", False) if isinstance(data.get("simples"), dict) else False,
            "opcao_mei": data.get("simei", {}).get("optante", False) if isinstance(data.get("simei"), dict) else False,
            "uf": data.get("uf", ""),
            "municipio": data.get("municipio", ""),
            "logradouro": data.get("logradouro", ""),
            "numero": data.get("numero", ""),
            "bairro": data.get("bairro", ""),
            "cep": data.get("cep", ""),
            "telefone": data.get("telefone", ""),
            "email": data.get("email", ""),
            "qsa": _normalizar_qsa(data.get("qsa", [])),
            "_api_fonte": fonte,
        }
    else:  # MinhaReceita ou generica
        return {
            "cnpj": limpar_cnpj(str(data.get("cnpj", ""))),
            "cnpj_formatado": formatar_cnpj(str(data.get("cnpj", ""))),
            "razao_social": data.get("razao_social", data.get("nome", "")),
            "nome_fantasia": data.get("nome_fantasia", data.get("fantasia", "")),
            "situacao_cadastral": data.get("descricao_situacao_cadastral", data.get("situacao", "")),
            "data_inicio": data.get("data_inicio_atividade", data.get("abertura", "")),
            "cnae_principal": str(data.get("cnae_fiscal", "")),
            "cnae_descricao": data.get("cnae_fiscal_descricao", ""),
            "natureza_juridica": data.get("descricao_natureza_juridica", data.get("natureza_juridica", "")),
            "porte": _porte_texto(data.get("porte", data.get("descricao_porte", ""))),
            "capital_social": float(data.get("capital_social", 0)),
            "opcao_simples": data.get("opcao_pelo_simples", False),
            "opcao_mei": data.get("opcao_pelo_mei", False),
            "uf": data.get("uf", ""),
            "municipio": data.get("municipio", ""),
            "telefone": data.get("ddd_telefone_1", data.get("telefone", "")),
            "email": data.get("email", ""),
            "qsa": _normalizar_qsa(data.get("qsa", [])),
            "_api_fonte": fonte,
        }


def _situacao_texto(s):
    return s if s else "ATIVA"

def _porte_texto(p):
    p = str(p).upper()
    if "MICRO" in p or "ME" in p:
        return "ME"
    elif "PEQUENO" in p or "EPP" in p:
        return "EPP"
    elif "MEDIO" in p:
        return "MEDIO"
    elif "GRANDE" in p:
        return "GRANDE"
    elif "DEMAIS" in p:
        return "MEDIO"
    return "MEDIO"  # default

def _parse_capital(v):
    if isinstance(v, (int, float)):
        return float(v)
    return float(re.sub(r"[^\d.]", "", str(v).replace(",", ".")) or "0")

def _normalizar_qsa(qsa_list):
    result = []
    for s in qsa_list[:5]:  # max 5 socios
        result.append({
            "nome": s.get("nome_socio", s.get("nome", "")),
            "qualificacao": s.get("qualificacao_socio", s.get("qual", "")),
        })
    return result


# ============================================================
# DIAGNOSTICO
# ============================================================
def gerar_diagnostico(dados: dict, certidoes_tcu: list = None, dados_cnpjws: dict = None,
                      dados_cnpja: dict = None, dados_processos: dict = None,
                      dados_pgfn: dict = None) -> dict:
    """Gera diagnostico preliminar baseado nos dados do CNPJ."""
    alertas = []
    servicos_recomendados = []
    certidoes_tcu = certidoes_tcu or []
    dados_cnpjws = dados_cnpjws or {}

    # Carregar config
    config_path = "D:/Site/audiper/templates/config-diagnostico.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"tabela_precos": {}, "regras_diagnostico": {}}

    porte = dados.get("porte", "MEDIO")
    capital = dados.get("capital_social", 0)
    simples = dados.get("opcao_simples", False)
    situacao = dados.get("situacao_cadastral", "ATIVA")
    cnae = dados.get("cnae_principal", "")[:2]
    data_inicio = dados.get("data_inicio", "")

    # Calcular anos de atividade
    anos_atividade = 0
    if data_inicio:
        try:
            for fmt in ["%Y-%m-%d", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(data_inicio, fmt)
                    anos_atividade = (date.today() - dt.date()).days // 365
                    break
                except ValueError:
                    continue
        except Exception:
            pass

    # Regra: Situacao cadastral irregular
    if situacao and "ATIVA" not in situacao.upper():
        alertas.append({
            "emoji": "🔴",
            "urgencia": "URGENTE",
            "texto": f"Situacao cadastral: {situacao}. Risco de multas e impedimentos junto a Receita Federal.",
        })
        servicos_recomendados.append("consultoria_permanente")

    # Regra: Simples com capital alto
    if simples and capital > 500000:
        alertas.append({
            "emoji": "🔴",
            "urgencia": "ALTA",
            "texto": f"Optante pelo Simples Nacional com capital de R$ {capital:,.2f}. Possivel desenquadramento por excesso.",
        })
        servicos_recomendados.append("planejamento_tributario")

    # Regra: CNAE industrial
    if cnae.isdigit() and 10 <= int(cnae) <= 33:
        alertas.append({
            "emoji": "🟡",
            "urgencia": "MEDIA",
            "texto": f"CNAE industrial ({dados.get('cnae_descricao', '')}). ICMS/IPI complexo, risco de creditos indevidos.",
        })
        servicos_recomendados.append("revisao_sped_fiscal")

    # Regra: CNAE comercio
    if cnae.isdigit() and cnae == "47":
        alertas.append({
            "emoji": "🟡",
            "urgencia": "MEDIA",
            "texto": "Comercio varejista com ICMS-ST. Risco de creditos tributarios e obrigacoes acessorias.",
        })
        servicos_recomendados.append("revisao_sped_fiscal")

    # Regra: Capital alto LTDA
    if capital > 1000000 and "LTDA" in dados.get("natureza_juridica", "").upper():
        alertas.append({
            "emoji": "🟡",
            "urgencia": "MEDIA",
            "texto": f"Capital social de R$ {capital:,.2f} para LTDA. Avaliar transformacao em S/A ou obrigatoriedade de auditoria.",
        })
        servicos_recomendados.append("auditoria_independente")

    # Regra: Grande porte
    if porte == "GRANDE" or capital > 50000000:
        alertas.append({
            "emoji": "🔴",
            "urgencia": "ALTA",
            "texto": "Empresa de grande porte. Possivel obrigatoriedade de auditoria independente (Lei 11.638/07).",
        })
        servicos_recomendados.append("auditoria_independente")

    # Regra: Empresa antiga sem revisao
    if anos_atividade > 5:
        alertas.append({
            "emoji": "🟡",
            "urgencia": "MEDIA",
            "texto": f"{anos_atividade} anos de operacao. Revisao periodica reduz risco de distorcoes acumuladas.",
        })
        if "revisao_sped_ecd" not in servicos_recomendados:
            servicos_recomendados.append("revisao_sped_ecd")

    # Regra: MEI tentando crescer
    if dados.get("opcao_mei", False):
        alertas.append({
            "emoji": "🟢",
            "urgencia": "NORMAL",
            "texto": "Empresa e MEI. Consultoria para transicao quando ultrapassar limite.",
        })
        servicos_recomendados.append("planejamento_tributario")

    # === TCU Certidoes - Sancoes e impedimentos ===
    sancoes_encontradas = []
    for cert in certidoes_tcu:
        situacao_cert = cert.get("situacao", "").upper()
        emissor = cert.get("emissor", "")
        tipo = cert.get("tipo", cert.get("descricao", ""))
        if situacao_cert == "CONSTA":
            sancoes_encontradas.append(f"{emissor}: {tipo}")

    if sancoes_encontradas:
        alertas.append({
            "emoji": "🔴",
            "urgencia": "URGENTE",
            "texto": f"SANCOES encontradas em {len(sancoes_encontradas)} base(s): {'; '.join(sancoes_encontradas)}. Risco de impedimento em licitacoes e contratos publicos.",
        })
        servicos_recomendados.append("consultoria_permanente")
    elif certidoes_tcu:
        alertas.append({
            "emoji": "🟢",
            "urgencia": "NORMAL",
            "texto": "Certidoes TCU/CNJ/CEIS/CNEP: NADA CONSTA em todas as bases consultadas.",
        })

    # === CNPJ.ws - Dados societarios enriquecidos ===
    if dados_cnpjws:
        # Socios estrangeiros
        socios_ws = dados_cnpjws.get("socios", [])
        estrangeiros = [s for s in socios_ws if s.get("pais", {}).get("comex_id", "105") != "105"]
        if estrangeiros:
            nomes = [s.get("nome", "?") for s in estrangeiros[:3]]
            alertas.append({
                "emoji": "🟡",
                "urgencia": "MEDIA",
                "texto": f"Socio(s) estrangeiro(s) detectado(s): {', '.join(nomes)}. Pode exigir escrituracao especial (transfer pricing, DERCAT).",
            })
            servicos_recomendados.append("consultoria_permanente")

        # Natureza juridica detalhada
        nj = dados_cnpjws.get("natureza_juridica", {})
        if isinstance(nj, dict) and nj.get("id", ""):
            nj_id = str(nj.get("id", ""))
            # S/A de capital aberto ou fechado
            if nj_id.startswith("204"):
                alertas.append({
                    "emoji": "🔴",
                    "urgencia": "ALTA",
                    "texto": "Sociedade Anonima - auditoria independente obrigatoria (CVM/Lei 6.404).",
                })
                servicos_recomendados.append("auditoria_independente")

        # Total de socios (pode ser > 5 que normalizamos)
        total_socios_ws = len(socios_ws)
        if total_socios_ws > 10:
            alertas.append({
                "emoji": "🟡",
                "urgencia": "MEDIA",
                "texto": f"Estrutura societaria complexa: {total_socios_ws} socios. Requer atencao especial na escrituracao.",
            })

    # === Processos Judiciais (DataJud CNJ) ===
    dados_processos = dados_processos or {}
    total_processos = dados_processos.get("total_encontrados", 0)
    if total_processos > 10:
        alertas.append({
            "emoji": "\U0001f534",
            "urgencia": "ALTA",
            "texto": f"{total_processos} processos judiciais encontrados. Risco de contingencias relevantes - avaliar provisoes (CPC 25).",
        })
        servicos_recomendados.append("consultoria_juridico_contabil")
    elif total_processos > 0:
        alertas.append({
            "emoji": "\U0001f7e1",
            "urgencia": "MEDIA",
            "texto": f"{total_processos} processo(s) judicial(is) encontrado(s). Recomendamos avaliacao de contingencias.",
        })
        servicos_recomendados.append("consultoria_juridico_contabil")

    # === Divida Ativa PGFN ===
    dados_pgfn = dados_pgfn or {}
    if dados_pgfn.get("tem_divida"):
        total_div = dados_pgfn.get("total_registros", 0)
        alertas.append({
            "emoji": "\U0001f534",
            "urgencia": "ALTA",
            "texto": f"{total_div} inscricao(oes) em Divida Ativa da Uniao. Risco de bloqueio de CND e impedimento em licitacoes.",
        })
        servicos_recomendados.append("regularizacao_fiscal")

    # === CNPJa Open - Confirmacao tributaria ===
    dados_cnpja = dados_cnpja or {}
    if dados_cnpja.get("simples_optante") and not dados.get("opcao_simples"):
        dados["opcao_simples"] = True
    if dados_cnpja.get("mei_optante") and not dados.get("opcao_mei"):
        dados["opcao_mei"] = True

    # Regra: Inscricoes estaduais inativas
    ies = dados_cnpja.get("inscricoes_estaduais", [])
    ies_inativas = [ie for ie in ies if not ie.get("status")]
    if ies_inativas:
        ufs = ", ".join(ie.get("uf", "?") for ie in ies_inativas)
        alertas.append({
            "emoji": "\U0001f7e1",
            "urgencia": "MEDIA",
            "texto": f"Inscricao(oes) estadual(is) inativa(s) em: {ufs}. Verificar pendencias SEFAZ.",
        })

    # Se nao encontrou nada especifico, recomendar basico
    if not alertas:
        alertas.append({
            "emoji": "🟢",
            "urgencia": "NORMAL",
            "texto": "Nenhuma irregularidade identificada na analise preliminar. Recomendamos revisao preventiva.",
        })
        servicos_recomendados.append("revisao_sped_ecd")

    # Determinar perfil tributario detalhado
    perfil_tributario = "Lucro Presumido"
    if dados.get("opcao_mei"):
        perfil_tributario = "MEI"
    elif dados.get("opcao_simples"):
        perfil_tributario = "Simples Nacional"
    elif capital > 50000000 or porte == "GRANDE":
        perfil_tributario = "Lucro Real (obrigatorio)"
    elif "S/A" in dados.get("natureza_juridica", "").upper() or "ANONIMA" in dados.get("natureza_juridica", "").upper():
        perfil_tributario = "Lucro Real (S/A)"
    else:
        perfil_tributario = "Lucro Presumido/Real"

    # Remover duplicatas mantendo ordem
    servicos_unicos = list(dict.fromkeys(servicos_recomendados))

    # Calcular valores
    tabela = config.get("tabela_precos", {})
    servicos_com_valor = []
    total = 0
    for srv in servicos_unicos:
        if srv in tabela:
            info = tabela[srv]
            faixa = info.get("faixas", {}).get(porte, info.get("faixas", {}).get("MEDIO", {}))
            valor_medio = (faixa.get("min", 0) + faixa.get("max", 0)) / 2
            total += valor_medio
            servicos_com_valor.append({
                "id": srv,
                "descricao": info["descricao"],
                "fundamentacao": info.get("fundamentacao", ""),
                "periodicidade": faixa.get("periodicidade", "pontual"),
                "valor": valor_medio,
                "valor_formatado": f"R$ {valor_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            })

    # Encontrar socio administrador
    socio_admin = "Prezado(a) Responsavel"
    for s in dados.get("qsa", []):
        qual = s.get("qualificacao", "").lower()
        if "admin" in qual or "diretor" in qual or "presidente" in qual:
            socio_admin = s.get("nome", socio_admin)
            break
    if socio_admin == "Prezado(a) Responsavel" and dados.get("qsa"):
        socio_admin = dados["qsa"][0].get("nome", socio_admin)

    # Resumo certidoes para exibicao
    certidoes_resumo = ""
    if certidoes_tcu:
        resumo_parts = []
        for cert in certidoes_tcu:
            sit = cert.get("situacao", "?").upper()
            emissor = cert.get("emissor", "?")
            icon = "\u2705" if "NADA" in sit else "\u274c"
            resumo_parts.append(f"{icon} {emissor}: {sit.replace('_', ' ')}")
        certidoes_resumo = "\n".join(resumo_parts)
    else:
        certidoes_resumo = "\u26a0\ufe0f API TCU indisponivel no momento"

    return {
        "dados_empresa": dados,
        "alertas": alertas,
        "servicos_recomendados": servicos_com_valor,
        "valor_total": total,
        "valor_total_formatado": f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "contato_nome": socio_admin.title(),
        "anos_atividade": anos_atividade,
        "porte": porte,
        "certidoes_resumo": certidoes_resumo,
        "processos_judiciais": dados_processos,
        "divida_ativa": dados_pgfn,
        "dados_cnpja": dados_cnpja,
        "perfil_tributario": perfil_tributario,
    }


def gerar_mensagem_telegram(diag: dict) -> str:
    """Gera mensagem HTML formatada para Telegram (parse_mode=HTML)."""
    d = diag["dados_empresa"]
    lines = []

    # Header
    lines.append("\u2705 <b>DIAGNOSTICO RAPIDO - AUDIPER</b>")
    lines.append("\u2501" * 24)
    lines.append(f"\U0001f3e2 <b>{_html_escape(d.get('razao_social', 'N/A'))}</b>")
    if d.get("nome_fantasia"):
        lines.append(f"    <i>({_html_escape(d['nome_fantasia'])})</i>")
    lines.append(f"\U0001f4cd {_html_escape(d.get('cnpj_formatado', d.get('cnpj', '?')))}")
    lines.append(f"\U0001f4cd {_html_escape(d.get('municipio', '?'))}/{_html_escape(d.get('uf', '?'))} | Porte: {diag['porte']}")
    lines.append(f"\U0001f4bc CNAE: {_html_escape(d.get('cnae_descricao', 'N/A'))}")

    regime = "Simples Nacional" if d.get("opcao_simples") else "Lucro Presumido/Real"
    if d.get("opcao_mei"):
        regime = "MEI"
    lines.append(f"\U0001f4cb Regime: {regime}")

    if d.get("capital_social", 0) > 0:
        cap_fmt = f"R$ {d['capital_social']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        lines.append(f"\U0001f4b0 Capital: {cap_fmt}")

    socios = len(d.get("qsa", []))
    if socios > 0:
        nomes_socios = [_html_escape(s.get("nome", "?")) for s in d.get("qsa", [])[:3]]
        lines.append(f"\U0001f465 Socios: {socios} ({', '.join(nomes_socios)}{'...' if socios > 3 else ''})")

    if diag.get("anos_atividade", 0) > 0:
        lines.append(f"\U0001f4c5 Atividade: {diag['anos_atividade']} anos")

    # TCU Certidoes section
    certidoes_info = diag.get("certidoes_resumo", "")
    if certidoes_info:
        lines.append("")
        lines.append(f"\U0001f6e1 <b>CERTIDOES (TCU/CNJ/CEIS/CNEP):</b>")
        lines.append(certidoes_info)

    # Processos Judiciais
    processos = diag.get("processos_judiciais", {})
    total_proc = processos.get("total_encontrados", 0)
    lines.append("")
    lines.append("\u2696\ufe0f <b>PROCESSOS JUDICIAIS (CNJ):</b>")
    if total_proc > 0:
        lines.append(f"\u274c {total_proc} processo(s) encontrado(s)")
        for p in processos.get("processos", [])[:3]:
            lines.append(f"  \u2022 {_html_escape(p.get('classe', ''))} - {_html_escape(p.get('justica', ''))}")
    else:
        lines.append("\u2705 Nenhum processo encontrado")

    # Divida Ativa
    divida = diag.get("divida_ativa", {})
    lines.append("")
    lines.append("\U0001f4b8 <b>DIVIDA ATIVA (PGFN):</b>")
    if divida.get("tem_divida"):
        lines.append(f"\u274c {divida.get('total_registros', 0)} inscricao(oes) em Divida Ativa")
    else:
        lines.append("\u2705 Sem inscricoes em Divida Ativa")

    # Perfil tributario
    lines.append("")
    lines.append(f"\U0001f4ca <b>PERFIL:</b> {diag.get('perfil_tributario', regime)}")

    lines.append("")
    lines.append("\u26a0\ufe0f <b>PONTOS DE ATENCAO:</b>")
    for i, a in enumerate(diag["alertas"], 1):
        lines.append(f"{a['emoji']} {i}. {_html_escape(a['texto'])}")

    lines.append("")
    lines.append("\U0001f4ca <b>PROPOSTA SUGERIDA:</b>")
    for s in diag["servicos_recomendados"]:
        per = "/mes" if s["periodicidade"] == "mensal" else " (pontual)"
        lines.append(f"  \u2022 {_html_escape(s['descricao'])}: <b>{s['valor_formatado']}</b>{per}")

    lines.append(f"\n  \U0001f4b0 <b>Total: {diag['valor_total_formatado']}</b>")

    lines.append("")
    lines.append(f"\U0001f4e7 Contato: <b>{_html_escape(diag.get('contato_nome', ''))}</b>")
    email = d.get("email", "") or ""
    telefone = d.get("telefone", "") or ""
    if email and email.lower() not in ("none", ""):
        lines.append(f"\U0001f4e7 {_html_escape(email)}")
    if telefone and telefone.lower() not in ("none", ""):
        lines.append(f"\U0001f4f1 {_html_escape(telefone)}")
    lines.append("")
    lines.append(f"<i>Fontes: {_html_escape(d.get('_api_fonte', '?'))} + TCU + CNPJ.ws + CNPJa + DataJud + PGFN | {datetime.now().strftime('%d/%m/%Y %H:%M')}</i>")

    return "\n".join(lines)


def _html_escape(text: str) -> str:
    """Escape HTML special chars for Telegram."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt_capital(valor: float) -> str:
    """Format capital social as R$ with Brazilian formatting."""
    if valor <= 0:
        return "N/I"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ============================================================
# PROPOSTA COMERCIAL HTML (3 paginas A4)
# ============================================================
def gerar_proposta_html(diag: dict) -> str:
    """Gera proposta comercial de 3 paginas A4 em HTML, preenchida com dados do diagnostico."""
    d = diag["dados_empresa"]
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    from datetime import timedelta
    data_validade = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")

    regime = "Simples Nacional" if d.get("opcao_simples") else "Lucro Presumido/Real"
    if d.get("opcao_mei"):
        regime = "MEI"

    # Urgencia colors
    urgencia_colors = {
        "URGENTE": ("#DC2626", "#FEF2F2", "#991B1B"),
        "ALTA": ("#EA580C", "#FFF7ED", "#9A3412"),
        "MEDIA": ("#D97706", "#FFFBEB", "#92400E"),
        "NORMAL": ("#059669", "#ECFDF5", "#065F46"),
    }

    # --- Build HTML ---
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Proposta Comercial - {d.get("razao_social", "Cliente")} | AUDIPER</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=Merriweather:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        audiper: {{ red: '#B91C1C', darkred: '#7F1D1D', gold: '#c9a962', wine: '#722F37' }},
                    }},
                    fontFamily: {{
                        sans: ['Inter', 'sans-serif'],
                        display: ['Outfit', 'sans-serif'],
                        serif: ['Merriweather', 'Georgia', 'serif'],
                    }}
                }}
            }}
        }}
    </script>
    <style>
        * {{
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
            color-adjust: exact !important;
            margin: 0; padding: 0; box-sizing: border-box;
        }}
        body {{ background-color: #E5E7EB; font-family: 'Inter', sans-serif; color: #334155; }}
        h1, h2, h3, h4 {{ font-family: 'Outfit', sans-serif; }}
        .a4-page {{
            width: 210mm; height: 297mm; min-height: 297mm; max-height: 297mm;
            margin: 10px auto; background: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            position: relative; overflow: hidden;
            page-break-after: always;
        }}
        .page-wrapper {{
            width: 100%; height: 297mm;
            display: flex; flex-direction: column;
            overflow: hidden;
        }}
        @media print {{
            @page {{ size: A4 portrait; margin: 0; }}
            html, body {{ width: 210mm; height: 297mm; margin: 0; padding: 0; background: white; }}
            .a4-page {{ margin: 0; box-shadow: none; }}
        }}
        .gradient-bar {{
            height: 6px;
            background: linear-gradient(90deg, #7F1D1D 0%, #B91C1C 35%, #DC2626 65%, #7F1D1D 100%);
        }}
        .divider-red {{
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, #B91C1C 30%, #B91C1C 70%, transparent 100%);
        }}
        .divider-gold {{
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, #c9a962 30%, #c9a962 70%, transparent 100%);
        }}
        .page-header {{
            flex-shrink: 0;
            padding: 8px 22px;
            border-bottom: 2px solid #B91C1C;
            display: flex; align-items: center; justify-content: space-between;
        }}
        .page-footer {{
            flex-shrink: 0;
            margin-top: auto;
            padding: 6px 22px;
            border-top: 1px solid #E5E7EB;
            font-size: 7pt; color: #9CA3AF;
            display: flex; justify-content: space-between;
        }}
    </style>
</head>
<body>

<!-- ==================== PAGINA 1: CAPA ==================== -->
<div class="a4-page">
    <div class="page-wrapper">
        <div class="gradient-bar"></div>
        <div class="flex-1 flex flex-col items-center justify-between px-16 py-12">

            <!-- Logo + Nome -->
            <div class="text-center pt-8">
                <div class="w-24 h-24 mx-auto rounded-full flex items-center justify-center overflow-hidden bg-white border-2 border-gray-200 shadow-lg mb-6">
                    <img src="https://www.audiper.com.br/novo-logo-audiper.png" alt="AUDIPER" style="width: 72px; height: 72px; object-fit: contain;">
                </div>
                <h1 class="text-3xl font-bold font-display text-gray-800 tracking-wide">AUDIPER<span class="text-audiper-red">&reg;</span></h1>
                <p class="text-sm text-gray-500 uppercase tracking-[0.2em] mt-1">Auditores Independentes</p>
                <p class="text-xs text-gray-400 mt-1">CRC/PI 000023/O</p>
            </div>

            <div class="w-full my-4"><div class="divider-red"></div></div>

            <!-- Badge Proposta -->
            <div class="text-center">
                <div class="inline-flex items-center gap-2 px-6 py-2 rounded-full mb-4" style="background: linear-gradient(135deg, #7F1D1D 0%, #B91C1C 100%);">
                    <i class="fas fa-file-contract text-white text-sm"></i>
                    <span class="text-white text-xs font-semibold uppercase tracking-wider">Proposta Comercial</span>
                </div>
                <h2 class="text-2xl font-bold font-display text-gray-800 leading-tight">
                    SERVICOS DE<br>
                    <span class="text-audiper-red">AUDITORIA E CONSULTORIA</span>
                </h2>
            </div>

            <div class="w-3/4 my-4"><div class="divider-gold"></div></div>

            <!-- Dados do Cliente -->
            <div class="w-full max-w-sm">
                <div class="space-y-3">
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <span class="text-[9px] text-gray-400 uppercase font-semibold tracking-wide">Cliente</span>
                        <span class="text-sm font-bold text-gray-800">{d.get("razao_social", "N/A")}</span>
                    </div>
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <span class="text-[9px] text-gray-400 uppercase font-semibold tracking-wide">CNPJ</span>
                        <span class="text-sm font-semibold text-gray-600 font-mono">{d.get("cnpj_formatado", d.get("cnpj", ""))}</span>
                    </div>
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <span class="text-[9px] text-gray-400 uppercase font-semibold tracking-wide">Localidade</span>
                        <span class="text-sm font-semibold text-gray-600">{d.get("municipio", "?")}/{d.get("uf", "?")}</span>
                    </div>
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <span class="text-[9px] text-gray-400 uppercase font-semibold tracking-wide">Porte</span>
                        <span class="text-sm font-semibold text-gray-600">{diag["porte"]}</span>
                    </div>
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <span class="text-[9px] text-gray-400 uppercase font-semibold tracking-wide">Data</span>
                        <span class="text-sm font-semibold text-gray-600">{data_hoje}</span>
                    </div>
                    <div class="flex justify-between items-center py-2">
                        <span class="text-[9px] text-gray-400 uppercase font-semibold tracking-wide">Validade</span>
                        <span class="text-sm font-bold text-audiper-red">{data_validade}</span>
                    </div>
                </div>
            </div>

            <!-- Local e Data -->
            <div class="text-center pb-4">
                <div class="divider-gold w-32 mx-auto mb-4"></div>
                <p class="text-sm text-gray-600 font-serif">Teresina &mdash; Piaui</p>
                <p class="text-sm text-gray-500 font-serif">{datetime.now().strftime("%B de %Y").title()}</p>
            </div>
        </div>
        <div class="gradient-bar"></div>
    </div>
</div>

<!-- ==================== PAGINA 2: DIAGNOSTICO ==================== -->
<div class="a4-page">
    <div class="page-wrapper">
        <!-- Header -->
        <div class="page-header">
            <div class="flex items-center gap-3">
                <img src="https://www.audiper.com.br/novo-logo-audiper.png" alt="" style="width:28px;height:28px;">
                <span class="font-display font-bold text-gray-700 text-sm">AUDIPER</span>
                <span class="text-gray-400 text-xs">|</span>
                <span class="text-gray-500 text-xs">Proposta Comercial</span>
            </div>
            <span class="text-xs text-gray-400">2/3</span>
        </div>

        <!-- Content -->
        <div class="flex-1 px-6 py-4 overflow-hidden" style="font-size: 9pt;">

            <!-- Dados da Empresa -->
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-building text-xs"></i> DADOS DA EMPRESA
            </h3>
            <div class="grid grid-cols-2 gap-x-6 gap-y-1 mb-3 text-[9pt]">
                <div><span class="text-gray-400 text-[8pt]">Razao Social:</span> <strong>{d.get("razao_social", "N/A")}</strong></div>
                <div><span class="text-gray-400 text-[8pt]">Nome Fantasia:</span> {d.get("nome_fantasia", "N/A") or "N/A"}</div>
                <div><span class="text-gray-400 text-[8pt]">CNPJ:</span> <strong class="font-mono">{d.get("cnpj_formatado", "")}</strong></div>
                <div><span class="text-gray-400 text-[8pt]">CNAE:</span> {d.get("cnae_descricao", "N/A")}</div>
                <div><span class="text-gray-400 text-[8pt]">Perfil Tributario:</span> <strong>{diag.get("perfil_tributario", regime)}</strong></div>
                <div><span class="text-gray-400 text-[8pt]">Capital:</span> {_fmt_capital(d.get("capital_social", 0))}</div>
                <div><span class="text-gray-400 text-[8pt]">Atividade:</span> {diag.get("anos_atividade", 0)} anos</div>
                <div><span class="text-gray-400 text-[8pt]">Socios:</span> {len(d.get("qsa", []))}</div>
            </div>

            <div class="divider-gold mb-3"></div>

            <!-- Certidoes TCU -->
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-shield-halved text-xs"></i> CERTIDOES (TCU / CNJ / CEIS / CNEP)
            </h3>
            <div class="grid grid-cols-2 gap-2 mb-3">'''

    # TCU certidoes grid
    certidoes_resumo = diag.get("certidoes_resumo", "")
    if certidoes_resumo and "indisponivel" not in certidoes_resumo.lower():
        for line in certidoes_resumo.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            is_clean = "\u2705" in line
            bg = "#ECFDF5" if is_clean else "#FEF2F2"
            border = "#059669" if is_clean else "#DC2626"
            icon_cls = "fa-check-circle text-green-600" if is_clean else "fa-times-circle text-red-600"
            # Extract text after emoji
            text = line.replace("\u2705", "").replace("\u274c", "").strip()
            html += f'''
                <div class="rounded px-3 py-2 flex items-center gap-2" style="background:{bg}; border-left: 3px solid {border};">
                    <i class="fas {icon_cls} text-xs"></i>
                    <span class="text-[8pt]">{text}</span>
                </div>'''
    else:
        html += '''
                <div class="col-span-2 rounded px-3 py-2 bg-yellow-50 border-l-3 border-yellow-500 text-[8pt]">
                    <i class="fas fa-exclamation-triangle text-yellow-600 text-xs"></i> API TCU indisponivel no momento da consulta
                </div>'''

    html += '''
            </div>

            <div class="divider-gold mb-3"></div>'''

    # === Processos Judiciais section ===
    processos = diag.get("processos_judiciais", {})
    total_proc = processos.get("total_encontrados", 0)
    html += '''
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-gavel text-xs"></i> PROCESSOS JUDICIAIS (DataJud/CNJ)
            </h3>'''
    if total_proc > 0:
        html += f'''
            <div class="rounded px-3 py-2 mb-1" style="background:#FEF2F2; border-left: 3px solid #DC2626;">
                <span class="text-[8pt]"><strong>{total_proc}</strong> processo(s) encontrado(s)</span>
            </div>
            <div class="text-[8pt] text-gray-500 mb-3">'''
        for p in processos.get("processos", [])[:5]:
            html += f'''
                <div class="flex gap-2 py-0.5 border-b border-gray-50">
                    <span class="font-mono text-gray-400">{p.get("numero", "")[:20]}</span>
                    <span>{p.get("classe", "")}</span>
                    <span class="text-gray-400">({p.get("justica", "")})</span>
                </div>'''
        html += '</div>'
    else:
        html += '''
            <div class="rounded px-3 py-2 mb-3" style="background:#ECFDF5; border-left: 3px solid #059669;">
                <i class="fas fa-check-circle text-green-600 text-xs"></i>
                <span class="text-[8pt]">Nenhum processo encontrado nas bases consultadas</span>
            </div>'''

    # === Divida Ativa section ===
    divida = diag.get("divida_ativa", {})
    tem_divida = divida.get("tem_divida", False)
    html += '''
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-file-invoice-dollar text-xs"></i> DIVIDA ATIVA DA UNIAO (PGFN)
            </h3>'''
    if tem_divida:
        total_div = divida.get("total_registros", 0)
        html += f'''
            <div class="rounded px-3 py-2 mb-3" style="background:#FEF2F2; border-left: 3px solid #DC2626;">
                <span class="text-[8pt]"><strong>{total_div}</strong> inscricao(oes) em Divida Ativa</span>
            </div>'''
    else:
        html += '''
            <div class="rounded px-3 py-2 mb-3" style="background:#ECFDF5; border-left: 3px solid #059669;">
                <i class="fas fa-check-circle text-green-600 text-xs"></i>
                <span class="text-[8pt]">Sem inscricoes em Divida Ativa da Uniao</span>
            </div>'''

    html += '''
            <div class="divider-gold mb-3"></div>

            <!-- Pontos de Atencao -->
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-exclamation-triangle text-xs"></i> PONTOS DE ATENCAO
            </h3>
            <div class="space-y-1 mb-3">'''

    for i, alerta in enumerate(diag["alertas"], 1):
        urg = alerta.get("urgencia", "NORMAL")
        color, bg, text_color = urgencia_colors.get(urg, ("#059669", "#ECFDF5", "#065F46"))
        html += f'''
                <div class="rounded px-3 py-1.5 flex items-start gap-2" style="background:{bg}; border-left: 3px solid {color};">
                    <span class="text-[7pt] font-bold px-1.5 py-0.5 rounded text-white mt-0.5" style="background:{color};">{urg}</span>
                    <span class="text-[8pt]" style="color:{text_color};">{alerta["texto"]}</span>
                </div>'''

    html += '''
            </div>

            <div class="divider-gold mb-3"></div>

            <!-- Servicos Recomendados -->
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-clipboard-list text-xs"></i> SERVICOS RECOMENDADOS
            </h3>
            <table class="w-full text-[8pt] border-collapse mb-2">
                <thead>
                    <tr class="text-left" style="background: #7F1D1D; color: white;">
                        <th class="px-2 py-1.5 rounded-tl">Servico</th>
                        <th class="px-2 py-1.5">Fundamentacao</th>
                        <th class="px-2 py-1.5 text-center">Periodicidade</th>
                        <th class="px-2 py-1.5 text-right rounded-tr">Valor</th>
                    </tr>
                </thead>
                <tbody>'''

    for idx, srv in enumerate(diag["servicos_recomendados"]):
        bg_row = "#FFF" if idx % 2 == 0 else "#F9FAFB"
        per = "Mensal" if srv["periodicidade"] == "mensal" else "Pontual"
        html += f'''
                    <tr style="background:{bg_row};">
                        <td class="px-2 py-1.5 font-semibold">{srv["descricao"]}</td>
                        <td class="px-2 py-1.5 text-gray-500">{srv.get("fundamentacao", "")}</td>
                        <td class="px-2 py-1.5 text-center">{per}</td>
                        <td class="px-2 py-1.5 text-right font-bold">{srv["valor_formatado"]}</td>
                    </tr>'''

    html += f'''
                    <tr style="background: linear-gradient(135deg, #7F1D1D 0%, #B91C1C 100%); color: white;">
                        <td class="px-2 py-2 font-bold rounded-bl" colspan="3">TOTAL ESTIMADO</td>
                        <td class="px-2 py-2 text-right font-bold text-lg rounded-br">{diag["valor_total_formatado"]}</td>
                    </tr>
                </tbody>
            </table>
            <p class="text-[7pt] text-gray-400 italic">* Valores estimados. Proposta final sujeita a analise detalhada do escopo.</p>

        </div>

        <!-- Footer -->
        <div class="page-footer">
            <span>AUDIPER - Auditores Independentes S/S | CRC/PI 000023/O</span>
            <span>Proposta Comercial | {data_hoje}</span>
        </div>
    </div>
</div>

<!-- ==================== PAGINA 3: SOBRE A AUDIPER ==================== -->
<div class="a4-page">
    <div class="page-wrapper">
        <!-- Header -->
        <div class="page-header">
            <div class="flex items-center gap-3">
                <img src="https://www.audiper.com.br/novo-logo-audiper.png" alt="" style="width:28px;height:28px;">
                <span class="font-display font-bold text-gray-700 text-sm">AUDIPER</span>
                <span class="text-gray-400 text-xs">|</span>
                <span class="text-gray-500 text-xs">Proposta Comercial</span>
            </div>
            <span class="text-xs text-gray-400">3/3</span>
        </div>

        <!-- Content -->
        <div class="flex-1 px-6 py-4 overflow-hidden" style="font-size: 9pt;">

            <!-- Quem Somos -->
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-landmark text-xs"></i> QUEM SOMOS
            </h3>
            <p class="text-[9pt] text-gray-600 mb-3 leading-relaxed">
                Fundada em <strong>1986</strong> em Teresina/PI, a <strong>AUDIPER - Auditores Independentes</strong> atua ha mais de
                <strong>40 anos</strong> oferecendo servicos de auditoria, pericia contabil e consultoria com excelencia tecnica,
                etica e inovacao. Somos referencia no Nordeste brasileiro, com atuacao nos estados do Piaui e Maranhao.
            </p>

            <!-- Numeros -->
            <div class="grid grid-cols-5 gap-2 mb-4">
                <div class="text-center rounded-lg py-2 px-1" style="background: #FEF2F2;">
                    <div class="text-lg font-bold text-audiper-red font-display">40+</div>
                    <div class="text-[7pt] text-gray-500">Anos</div>
                </div>
                <div class="text-center rounded-lg py-2 px-1" style="background: #FEF2F2;">
                    <div class="text-lg font-bold text-audiper-red font-display">500+</div>
                    <div class="text-[7pt] text-gray-500">Clientes</div>
                </div>
                <div class="text-center rounded-lg py-2 px-1" style="background: #FEF2F2;">
                    <div class="text-lg font-bold text-audiper-red font-display">2</div>
                    <div class="text-[7pt] text-gray-500">Estados</div>
                </div>
                <div class="text-center rounded-lg py-2 px-1" style="background: #FEF2F2;">
                    <div class="text-lg font-bold text-audiper-red font-display">15+</div>
                    <div class="text-[7pt] text-gray-500">Profissionais</div>
                </div>
                <div class="text-center rounded-lg py-2 px-1" style="background: #FEF2F2;">
                    <div class="text-lg font-bold text-audiper-red font-display">1000+</div>
                    <div class="text-[7pt] text-gray-500">Laudos</div>
                </div>
            </div>

            <div class="divider-gold mb-3"></div>

            <!-- Certificacoes -->
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-certificate text-xs"></i> CERTIFICACOES
            </h3>
            <div class="flex gap-3 mb-4">
                <div class="flex items-center gap-2 rounded-full px-4 py-1.5" style="background: #7F1D1D;">
                    <i class="fas fa-check-circle text-white text-xs"></i>
                    <span class="text-white text-[8pt] font-semibold">CRC</span>
                </div>
                <div class="flex items-center gap-2 rounded-full px-4 py-1.5" style="background: #7F1D1D;">
                    <i class="fas fa-check-circle text-white text-xs"></i>
                    <span class="text-white text-[8pt] font-semibold">CVM</span>
                </div>
                <div class="flex items-center gap-2 rounded-full px-4 py-1.5" style="background: #7F1D1D;">
                    <i class="fas fa-check-circle text-white text-xs"></i>
                    <span class="text-white text-[8pt] font-semibold">IBRACON</span>
                </div>
                <div class="flex items-center gap-2 rounded-full px-4 py-1.5" style="background: #7F1D1D;">
                    <i class="fas fa-check-circle text-white text-xs"></i>
                    <span class="text-white text-[8pt] font-semibold">CNAI</span>
                </div>
            </div>

            <div class="divider-gold mb-3"></div>

            <!-- Servicos -->
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-briefcase text-xs"></i> NOSSOS SERVICOS
            </h3>
            <div class="grid grid-cols-2 gap-3 mb-4">
                <div class="rounded-lg p-3 border border-gray-100" style="background: #FAFAFA;">
                    <h4 class="font-display font-bold text-[9pt] text-gray-800 mb-1"><i class="fas fa-search-dollar text-audiper-red text-xs mr-1"></i> Auditorias</h4>
                    <p class="text-[8pt] text-gray-500">Anti-Fraude, Contabil e Financeira, Fiscal e Tributaria, Interna, Due Diligence</p>
                </div>
                <div class="rounded-lg p-3 border border-gray-100" style="background: #FAFAFA;">
                    <h4 class="font-display font-bold text-[9pt] text-gray-800 mb-1"><i class="fas fa-balance-scale text-audiper-red text-xs mr-1"></i> Pericias</h4>
                    <p class="text-[8pt] text-gray-500">Tributaria, Revisao Bancaria, Trabalhista, Valuation, Contabil Judicial</p>
                </div>
                <div class="rounded-lg p-3 border border-gray-100" style="background: #FAFAFA;">
                    <h4 class="font-display font-bold text-[9pt] text-gray-800 mb-1"><i class="fas fa-robot text-audiper-red text-xs mr-1"></i> IA & Data</h4>
                    <p class="text-[8pt] text-gray-500">Diagnostico Digital, IA Financeira, IA para Compliance, Treinamentos</p>
                </div>
                <div class="rounded-lg p-3 border border-gray-100" style="background: #FAFAFA;">
                    <h4 class="font-display font-bold text-[9pt] text-gray-800 mb-1"><i class="fas fa-handshake text-audiper-red text-xs mr-1"></i> Consultoria</h4>
                    <p class="text-[8pt] text-gray-500">Planejamento Tributario, Permanente, Compliance/LGPD, Operacional</p>
                </div>
            </div>

            <div class="divider-gold mb-3"></div>

            <!-- Diferenciais -->
            <h3 class="text-sm font-bold font-display text-audiper-red mb-2 flex items-center gap-2">
                <i class="fas fa-star text-xs"></i> DIFERENCIAIS
            </h3>
            <div class="grid grid-cols-2 gap-2 mb-4">
                <div class="flex items-start gap-2">
                    <i class="fas fa-microchip text-audiper-gold text-xs mt-1"></i>
                    <div>
                        <strong class="text-[8pt]">Tecnologia e IA</strong>
                        <p class="text-[7pt] text-gray-400">Inteligencia artificial integrada aos processos de auditoria</p>
                    </div>
                </div>
                <div class="flex items-start gap-2">
                    <i class="fas fa-award text-audiper-gold text-xs mt-1"></i>
                    <div>
                        <strong class="text-[8pt]">40+ Anos</strong>
                        <p class="text-[7pt] text-gray-400">Experiencia consolidada em auditoria e pericia</p>
                    </div>
                </div>
                <div class="flex items-start gap-2">
                    <i class="fas fa-users text-audiper-gold text-xs mt-1"></i>
                    <div>
                        <strong class="text-[8pt]">Equipe Multidisciplinar</strong>
                        <p class="text-[7pt] text-gray-400">Contadores, auditores, peritos, economistas, advogados</p>
                    </div>
                </div>
                <div class="flex items-start gap-2">
                    <i class="fas fa-book text-audiper-gold text-xs mt-1"></i>
                    <div>
                        <strong class="text-[8pt]">Metodologia NBC TA</strong>
                        <p class="text-[7pt] text-gray-400">Normas internacionais de auditoria emitidas pelo CFC</p>
                    </div>
                </div>
            </div>

            <div class="divider-gold mb-3"></div>

            <!-- Contato -->
            <div class="rounded-lg p-4" style="background: linear-gradient(135deg, #7F1D1D 0%, #B91C1C 100%);">
                <h3 class="text-sm font-bold font-display text-white mb-2 flex items-center gap-2">
                    <i class="fas fa-envelope text-xs"></i> ENTRE EM CONTATO
                </h3>
                <div class="grid grid-cols-2 gap-2 text-[8pt] text-red-100">
                    <div><i class="fas fa-map-marker-alt mr-1"></i> Rua Arlindo Nogueira, 614/Sul - Teresina/PI</div>
                    <div><i class="fas fa-phone mr-1"></i> (86) 3303-0987</div>
                    <div><i class="fab fa-whatsapp mr-1"></i> (86) 99401-0525</div>
                    <div><i class="fas fa-envelope mr-1"></i> audiper@audiper.com</div>
                    <div class="col-span-2"><i class="fas fa-globe mr-1"></i> www.audiper.com.br</div>
                </div>
            </div>

        </div>

        <!-- Footer -->
        <div class="page-footer">
            <span>AUDIPER - Auditores Independentes S/S | CRC/PI 000023/O | Desde 1986</span>
            <span>Proposta Comercial | {data_hoje}</span>
        </div>
    </div>
</div>

</body>
</html>'''

    return html


# ============================================================
# ENVIO TELEGRAM
# ============================================================
def enviar_telegram(mensagem: str, chat_id: str, bot_token: str) -> bool:
    """Envia mensagem HTML para Telegram via Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "User-Agent": "AUDIPER-Diagnostico/2.0",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("ok", False)
    except Exception as e:
        print(f"  [ERRO] Telegram falhou: {e}", file=sys.stderr)
        return False


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python diagnostico_cnpj.py <CNPJ> [--telegram] [--proposta]")
        print("Ex:  python diagnostico_cnpj.py 12345678000190")
        print("     python diagnostico_cnpj.py 12345678000190 --telegram")
        print("     python diagnostico_cnpj.py 12345678000190 --proposta")
        sys.exit(1)

    cnpj_input = sys.argv[1]
    enviar_tg = "--telegram" in sys.argv
    gerar_prop = "--proposta" in sys.argv

    print(f"\U0001f50d Consultando CNPJ: {formatar_cnpj(cnpj_input)}...")

    # 1. Dados cadastrais (BrasilAPI / ReceitaWS / MinhaReceita)
    dados = consultar_cnpj(cnpj_input)
    if "erro" in dados:
        print(f"\u274c Erro: {dados['erro']}")
        sys.exit(1)
    print(f"\u2705 Dados cadastrais via {dados.get('_api_fonte', '?')}")

    # 2. TCU Certidoes Consolidada (sancoes)
    print("\U0001f6e1 Consultando certidoes TCU/CNJ/CEIS/CNEP...")
    certidoes = consultar_certidoes_tcu(cnpj_input)
    if certidoes:
        print(f"\u2705 TCU: {len(certidoes)} certidao(oes) retornada(s)")
    else:
        print("\u26a0\ufe0f TCU: sem retorno (API pode estar indisponivel)")

    # 3. CNPJ.ws (detalhamento societario)
    print("\U0001f465 Consultando CNPJ.ws (detalhamento societario)...")
    dados_ws = consultar_cnpjws(cnpj_input)
    if dados_ws:
        n_socios = len(dados_ws.get("socios", []))
        print(f"\u2705 CNPJ.ws: {n_socios} socio(s) encontrado(s)")
    else:
        print("\u26a0\ufe0f CNPJ.ws: sem retorno")

    # 4. CNPJa Open (regime tributario)
    print("\U0001f4cb Consultando CNPJa Open (regime tributario)...")
    dados_cnpja = consultar_cnpja_open(cnpj_input)
    if dados_cnpja:
        simples_str = "Sim" if dados_cnpja.get("simples_optante") else "Nao"
        mei_str = "Sim" if dados_cnpja.get("mei_optante") else "Nao"
        print(f"\u2705 CNPJa Open: Simples={simples_str}, MEI={mei_str}")
    else:
        print("\u26a0\ufe0f CNPJa Open: sem retorno")

    # 5. DataJud CNJ (processos judiciais)
    print("\u2696\ufe0f Consultando DataJud/CNJ (processos judiciais)...")
    dados_processos = consultar_datajud_processos(cnpj_input)
    total_proc = dados_processos.get("total_encontrados", 0)
    if total_proc > 0:
        print(f"\u26a0\ufe0f DataJud: {total_proc} processo(s) encontrado(s)")
    else:
        print(f"\u2705 DataJud: nenhum processo encontrado")

    # 6. PGFN Divida Ativa
    print("\U0001f4b8 Consultando PGFN (divida ativa)...")
    dados_pgfn = consultar_pgfn_divida(cnpj_input)
    if dados_pgfn.get("tem_divida"):
        print(f"\u26a0\ufe0f PGFN: {dados_pgfn.get('total_registros', 0)} inscricao(oes) em Divida Ativa")
    else:
        print(f"\u2705 PGFN: sem divida ativa")

    print()

    # 7. Gerar diagnostico enriquecido
    diagnostico = gerar_diagnostico(dados, certidoes_tcu=certidoes, dados_cnpjws=dados_ws,
                                    dados_cnpja=dados_cnpja, dados_processos=dados_processos,
                                    dados_pgfn=dados_pgfn)

    # 5. Mensagem Telegram (HTML)
    msg_telegram = gerar_mensagem_telegram(diagnostico)
    print(msg_telegram)

    # 6. Enviar para Telegram se solicitado
    if enviar_tg:
        import os
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "62036868")
        if bot_token:
            print(f"\n\U0001f4e4 Enviando para Telegram (chat_id: {chat_id})...")
            ok = enviar_telegram(msg_telegram, chat_id, bot_token)
            if ok:
                print("\u2705 Enviado com sucesso!")
            else:
                print("\u274c Falha no envio.")
        else:
            print("\n\u26a0\ufe0f TELEGRAM_BOT_TOKEN nao definido. Use: set TELEGRAM_BOT_TOKEN=...")

    # 7. Gerar proposta HTML se solicitado
    if gerar_prop:
        proposta_html = gerar_proposta_html(diagnostico)
        proposta_file = f"D:/Site/audiper/diagnosticos/{limpar_cnpj(cnpj_input)}_proposta.html"
        import os
        os.makedirs(os.path.dirname(proposta_file), exist_ok=True)
        with open(proposta_file, "w", encoding="utf-8") as f:
            f.write(proposta_html)
        print(f"\n\U0001f4c4 Proposta salva em: {proposta_file}")

    # 8. Salvar JSON completo
    output_file = f"D:/Site/audiper/diagnosticos/{limpar_cnpj(cnpj_input)}.json"
    try:
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(diagnostico, f, ensure_ascii=False, indent=2)
        print(f"\n\U0001f4c1 Diagnostico salvo em: {output_file}")
    except Exception as e:
        print(f"\n\u26a0\ufe0f Nao salvou arquivo: {e}", file=sys.stderr)
