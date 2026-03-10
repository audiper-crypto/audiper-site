"""
AUDIPER - Diagnostico de CNPJ
Consulta dados de CNPJ via APIs publicas e gera diagnostico preliminar.

Uso:
  python diagnostico_cnpj.py 12345678000190
  python diagnostico_cnpj.py 12.345.678/0001-90

APIs utilizadas (com fallback):
  1. BrasilAPI (brasilapi.com.br)
  2. ReceitaWS (receitaws.com.br)
  3. MinhaReceita (minhareceita.org)
"""

import sys
import json
import re
import urllib.request
import urllib.error
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
def gerar_diagnostico(dados: dict) -> dict:
    """Gera diagnostico preliminar baseado nos dados do CNPJ."""
    alertas = []
    servicos_recomendados = []

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

    # Se nao encontrou nada especifico, recomendar basico
    if not alertas:
        alertas.append({
            "emoji": "🟢",
            "urgencia": "NORMAL",
            "texto": "Nenhuma irregularidade identificada na analise preliminar. Recomendamos revisao preventiva.",
        })
        servicos_recomendados.append("revisao_sped_ecd")

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

    return {
        "dados_empresa": dados,
        "alertas": alertas,
        "servicos_recomendados": servicos_com_valor,
        "valor_total": total,
        "valor_total_formatado": f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "contato_nome": socio_admin.title(),
        "anos_atividade": anos_atividade,
        "porte": porte,
    }


def gerar_mensagem_telegram(diag: dict) -> str:
    """Gera mensagem formatada para Telegram."""
    d = diag["dados_empresa"]
    lines = []

    # Header
    lines.append(f"✅ DIAGNOSTICO RAPIDO")
    lines.append("━" * 24)
    lines.append(f"🏢 {d.get('razao_social', 'N/A')}")
    if d.get("nome_fantasia"):
        lines.append(f"    ({d['nome_fantasia']})")
    lines.append(f"📍 {d.get('municipio', '?')}/{d.get('uf', '?')} | Porte: {diag['porte']}")
    lines.append(f"💼 CNAE: {d.get('cnae_descricao', 'N/A')}")

    regime = "Simples Nacional" if d.get("opcao_simples") else "Lucro Presumido/Real"
    if d.get("opcao_mei"):
        regime = "MEI"
    lines.append(f"📋 Regime: {regime}")

    if d.get("capital_social", 0) > 0:
        cap_fmt = f"R$ {d['capital_social']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        lines.append(f"💰 Capital: {cap_fmt}")

    socios = len(d.get("qsa", []))
    if socios > 0:
        lines.append(f"👥 Socios: {socios}")

    lines.append("")
    lines.append("⚠️ PONTOS DE ATENCAO:")
    for i, a in enumerate(diag["alertas"], 1):
        lines.append(f"{a['emoji']} {i}. {a['texto']}")

    lines.append("")
    lines.append("📊 PROPOSTA SUGERIDA:")
    for s in diag["servicos_recomendados"]:
        per = "/mes" if s["periodicidade"] == "mensal" else " (pontual)"
        lines.append(f"  • {s['descricao']}: {s['valor_formatado']}{per}")

    lines.append(f"  💰 Total: {diag['valor_total_formatado']}")

    lines.append("")
    lines.append("📧 Enviar proposta para o prospect?")
    lines.append("[Sim ✅] [Editar ✏️] [Cancelar ❌]")

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python diagnostico_cnpj.py <CNPJ>")
        print("Ex:  python diagnostico_cnpj.py 12345678000190")
        sys.exit(1)

    cnpj_input = sys.argv[1]
    print(f"🔍 Consultando CNPJ: {formatar_cnpj(cnpj_input)}...")

    dados = consultar_cnpj(cnpj_input)
    if "erro" in dados:
        print(f"❌ Erro: {dados['erro']}")
        sys.exit(1)

    print(f"✅ Dados obtidos via {dados.get('_api_fonte', '?')}")
    print()

    diagnostico = gerar_diagnostico(dados)

    # Mensagem Telegram
    msg_telegram = gerar_mensagem_telegram(diagnostico)
    print(msg_telegram)

    # Salvar JSON completo
    output_file = f"D:/Site/audiper/diagnosticos/{limpar_cnpj(cnpj_input)}.json"
    try:
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(diagnostico, f, ensure_ascii=False, indent=2)
        print(f"\n📁 Diagnostico salvo em: {output_file}")
    except Exception as e:
        print(f"\n⚠️ Nao salvou arquivo: {e}", file=sys.stderr)
