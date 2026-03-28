"""
seed_clientes.py — Popula PostgreSQL com todos os clientes e auditorias AUDIPER.
Executar: python D:/Site/audiper/seed_clientes.py
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
from datetime import date

DB_URL = "postgresql://postgres:audiper2026@localhost:5432/audiper"

CLIENTES = [
    {
        "cnpj": "55.459.453/0001-72",
        "razao_social": "OIG Gaming Brazil Ltda",
        "nome_fantasia": "OIG Gaming",
        "cnae": "92.00-3-99",
        "cnae_descricao": "Exploração de jogos de azar e apostas",
        "porte": "MEDIO",
        "natureza_juridica": "Sociedade Empresária Limitada",
        "situacao_cadastral": "ATIVA",
        "municipio": "Teresina",
        "uf": "PI",
        "setor": "iGaming / Apostas Esportivas",
        "status_auditoria": "exec",
        "fase_atual": "execucao",
        "exercicio": "2025",
        "periodo_inicio": date(2025, 1, 1),
        "periodo_fim": date(2025, 12, 31),
        "achados": 13,
        "materialidade_global": 150000.00,
        "qsa": {
            "socios": [
                {"nome": "OIG Holdings Ltd", "qualificacao": "Sócio Investidor", "capital_pct": 100}
            ],
            "contador": {"nome": "A identificar", "crc": ""},
            "observacoes": "Operadora de apostas esportivas habilitada pela SPA/MF. Base legal: Lei 14.790/2023."
        }
    },
    {
        "cnpj": "41.511.429/0001-20",
        "razao_social": "Unimed Floriano Cooperativa de Trabalho Médico",
        "nome_fantasia": "Unimed Floriano",
        "cnae": "86.22-3-00",
        "cnae_descricao": "Serviços especializados em saúde",
        "porte": "MEDIO",
        "natureza_juridica": "Cooperativa",
        "situacao_cadastral": "ATIVA",
        "municipio": "Floriano",
        "uf": "PI",
        "setor": "Operadora de Saúde / ANS",
        "status_auditoria": "exec",
        "fase_atual": "execucao",
        "exercicio": "2025",
        "periodo_inicio": date(2025, 1, 1),
        "periodo_fim": date(2025, 12, 31),
        "achados": 11,
        "materialidade_global": 120000.00,
        "qsa": {
            "socios": [
                {"nome": "Cooperados médicos", "qualificacao": "Cooperados", "capital_pct": 100}
            ],
            "contador": {"nome": "A identificar", "crc": ""},
            "observacoes": "Operadora de planos de saúde. Regulada pela ANS. RN 528/2022, RN 569/2022."
        }
    },
    {
        "cnpj": "03.998.690/0001-08",
        "razao_social": "Japan Veiculos Ltda",
        "nome_fantasia": "Japan Veículos",
        "cnae": "45.11-1-01",
        "cnae_descricao": "Comércio a varejo de automóveis, camionetas e utilitários novos",
        "porte": "MEDIO",
        "natureza_juridica": "Sociedade Empresária Limitada",
        "situacao_cadastral": "ATIVA",
        "municipio": "Teresina",
        "uf": "PI",
        "setor": "Concessionária de Veículos",
        "status_auditoria": "exec",
        "fase_atual": "execucao",
        "exercicio": "2025",
        "periodo_inicio": date(2025, 1, 1),
        "periodo_fim": date(2025, 12, 31),
        "achados": 9,
        "materialidade_global": 80000.00,
        "qsa": {
            "socios": [
                {"nome": "A identificar", "qualificacao": "Sócio Administrador", "capital_pct": 100}
            ],
            "contador": {"nome": "A identificar", "crc": ""},
            "observacoes": "Concessionária. CPC 16 (Estoques), CPC 27 (Imobilizado), CPC 12 (AVP)."
        }
    },
    {
        "cnpj": "07.634.740/0001-63",
        "razao_social": "Via Paris Comercio de Roupas Ltda",
        "nome_fantasia": "Via Paris",
        "cnae": "47.81-4-00",
        "cnae_descricao": "Comércio varejista de artigos do vestuário e acessórios",
        "porte": "PEQUENO",
        "natureza_juridica": "Sociedade Empresária Limitada",
        "situacao_cadastral": "ATIVA",
        "municipio": "Teresina",
        "uf": "PI",
        "setor": "Comércio Varejista / Vestuário",
        "status_auditoria": "concluida",
        "fase_atual": "relatorios",
        "exercicio": "2024",
        "periodo_inicio": date(2024, 1, 1),
        "periodo_fim": date(2024, 12, 31),
        "achados": 13,
        "materialidade_global": 45000.00,
        "qsa": {
            "socios": [
                {"nome": "A identificar", "qualificacao": "Sócio Administrador", "capital_pct": 100}
            ],
            "contador": {"nome": "A identificar", "crc": ""},
            "observacoes": "Relatório G-01 emitido. 13 achados confirmados. COM-09 entregue."
        }
    },
    {
        "cnpj": "62.697.793/0001-05",
        "razao_social": "Via Shanghai Automoveis Ltda",
        "nome_fantasia": "Via Shanghai",
        "cnae": "45.11-1-01",
        "cnae_descricao": "Comércio a varejo de automóveis, camionetas e utilitários novos",
        "porte": "MEDIO",
        "natureza_juridica": "Sociedade Empresária Limitada",
        "situacao_cadastral": "ATIVA",
        "municipio": "Teresina",
        "uf": "PI",
        "setor": "Concessionária de Veículos",
        "status_auditoria": "concluida",
        "fase_atual": "relatorios",
        "exercicio": "2024",
        "periodo_inicio": date(2024, 1, 1),
        "periodo_fim": date(2024, 12, 31),
        "achados": 8,
        "materialidade_global": 70000.00,
        "qsa": {
            "socios": [
                {"nome": "A identificar", "qualificacao": "Sócio Administrador", "capital_pct": 100}
            ],
            "contador": {"nome": "A identificar", "crc": ""},
            "observacoes": "Relatório G-01 entregue. 8 achados. WPs concluídos."
        }
    },
    {
        "cnpj": "13.746.922/0001-94",
        "razao_social": "Resolve Administradora de Beneficios Ltda",
        "nome_fantasia": "Resolve",
        "cnae": "65.50-2-00",
        "cnae_descricao": "Planos de saúde",
        "porte": "PEQUENO",
        "natureza_juridica": "Sociedade Empresária Limitada",
        "situacao_cadastral": "ATIVA",
        "municipio": "Teresina",
        "uf": "PI",
        "setor": "Administradora de Benefícios",
        "status_auditoria": "concluida",
        "fase_atual": "relatorios",
        "exercicio": "2024",
        "periodo_inicio": date(2024, 1, 1),
        "periodo_fim": date(2024, 12, 31),
        "achados": 6,
        "materialidade_global": 30000.00,
        "qsa": {
            "socios": [
                {"nome": "A identificar", "qualificacao": "Sócio Administrador", "capital_pct": 100}
            ],
            "contador": {"nome": "A identificar", "crc": ""},
            "observacoes": "Relatório G-01 emitido. 6 achados. WP Fase F concluído."
        }
    },
    {
        "cnpj": "15.513.690/0001-50",
        "razao_social": "Fundacao de Apoio a Pesquisa e ao Ensino de Campo Grande",
        "nome_fantasia": "FAPEC",
        "cnae": "85.92-9-99",
        "cnae_descricao": "Atividades de ensino não especificadas anteriormente",
        "porte": "MEDIO",
        "natureza_juridica": "Fundação Privada",
        "situacao_cadastral": "ATIVA",
        "municipio": "Campo Grande",
        "uf": "MS",
        "setor": "Terceiro Setor / Fundação",
        "status_auditoria": "em_andamento",
        "fase_atual": "planejamento",
        "exercicio": "2025",
        "periodo_inicio": date(2025, 1, 1),
        "periodo_fim": date(2025, 12, 31),
        "achados": 0,
        "materialidade_global": 60000.00,
        "qsa": {
            "socios": [
                {"nome": "Conselho Curador", "qualificacao": "Órgão Governança", "capital_pct": 0}
            ],
            "contador": {"nome": "A identificar", "crc": ""},
            "observacoes": "Fundação de apoio. Terceiro setor. ITG 2002 + Lei 9.790/1999."
        }
    },
    {
        "cnpj": "11.408.142/0001-09",
        "razao_social": "Mega Teleinformatica Ltda",
        "nome_fantasia": "Megalink Telecom",
        "cnae": "61.10-8-03",
        "cnae_descricao": "Serviços de comunicação multimídia - SCM",
        "porte": "MEDIO",
        "natureza_juridica": "Sociedade Empresária Limitada",
        "situacao_cadastral": "ATIVA",
        "municipio": "Teresina",
        "uf": "PI",
        "setor": "Telecomunicações / ISP",
        "status_auditoria": "em_andamento",
        "fase_atual": "aceitacao",
        "exercicio": "2025",
        "periodo_inicio": date(2025, 1, 1),
        "periodo_fim": date(2025, 12, 31),
        "achados": 0,
        "materialidade_global": 35000.00,
        "qsa": {
            "socios": [
                {"nome": "A identificar", "qualificacao": "Sócio Administrador", "capital_pct": 100}
            ],
            "contador": {"nome": "A identificar", "crc": ""},
            "observacoes": "Provedor de internet. ANATEL. FUST/FUNTTEL. SUDENE. Reunião início realizada. Contrato R$35k."
        }
    },
    {
        "cnpj": "06.865.166/0001-57",
        "razao_social": "Caritas Diocesana de Teresina",
        "nome_fantasia": "Cáritas Teresina",
        "cnae": "94.99-5-00",
        "cnae_descricao": "Atividades associativas não especificadas anteriormente",
        "porte": "PEQUENO",
        "natureza_juridica": "Associação Privada",
        "situacao_cadastral": "ATIVA",
        "municipio": "Teresina",
        "uf": "PI",
        "setor": "Terceiro Setor / Entidade Social",
        "status_auditoria": "em_andamento",
        "fase_atual": "aceitacao",
        "exercicio": "2025",
        "periodo_inicio": date(2025, 1, 1),
        "periodo_fim": date(2025, 12, 31),
        "achados": 0,
        "materialidade_global": 20000.00,
        "qsa": {
            "socios": [
                {"nome": "Diocese de Teresina", "qualificacao": "Mantenedora", "capital_pct": 0}
            ],
            "contador": {"nome": "A identificar", "crc": ""},
            "observacoes": "Entidade social ligada à Igreja Católica. ITG 2002 + NBC TA gerais."
        }
    },
]


def get_firma_id(cur):
    cur.execute("SELECT id FROM firmas WHERE cnpj = '23.626.575/0001-10'")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("Firma AUDIPER não encontrada. Execute o backend primeiro para criar o seed.")
    return row[0]


def get_auditor_id(cur, email):
    cur.execute("SELECT id FROM auditores WHERE email = %s", (email,))
    row = cur.fetchone()
    return row[0] if row else None


def upsert_cliente(cur, firma_id, c):
    cur.execute("SELECT id FROM clientes WHERE cnpj = %s", (c["cnpj"],))
    existing = cur.fetchone()

    if existing:
        cur.execute("""
            UPDATE clientes SET
                razao_social = %s,
                nome_fantasia = %s,
                cnae = %s,
                cnae_descricao = %s,
                porte = %s,
                natureza_juridica = %s,
                situacao_cadastral = %s,
                municipio = %s,
                uf = %s,
                qsa = %s
            WHERE cnpj = %s
            RETURNING id
        """, (
            c["razao_social"], c["nome_fantasia"], c["cnae"], c["cnae_descricao"],
            c["porte"], c["natureza_juridica"], c["situacao_cadastral"],
            c["municipio"], c["uf"], json.dumps(c["qsa"]), c["cnpj"]
        ))
        return cur.fetchone()[0], "updated"
    else:
        new_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO clientes (id, firma_id, cnpj, razao_social, nome_fantasia, cnae, cnae_descricao,
                porte, natureza_juridica, situacao_cadastral, municipio, uf, qsa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            new_id, firma_id, c["cnpj"], c["razao_social"], c["nome_fantasia"],
            c["cnae"], c["cnae_descricao"], c["porte"], c["natureza_juridica"],
            c["situacao_cadastral"], c["municipio"], c["uf"], json.dumps(c["qsa"])
        ))
        return cur.fetchone()[0], "inserted"


def get_next_codigo(cur, prefix="AUD"):
    cur.execute("SELECT COUNT(*) FROM auditorias")
    n = cur.fetchone()[0]
    return f"{prefix}-{2025 + n // 20:04d}-{(n % 20) + 1:03d}"


def upsert_auditoria(cur, firma_id, cliente_id, c, responsavel_id, coordenador_id):
    # Usar código baseado no nome fantasia + exercício
    slug = c["nome_fantasia"].upper().replace(" ", "")[:6]
    codigo = f"{slug}-{c['exercicio']}"

    cur.execute("SELECT id FROM auditorias WHERE codigo = %s", (codigo,))
    existing = cur.fetchone()

    # Mapear status do cliente para status/fase da auditoria
    status_map = {
        "exec": "em_andamento",
        "concluida": "concluida",
        "em_andamento": "em_andamento",
    }
    status = status_map.get(c["status_auditoria"], "em_andamento")

    if existing:
        cur.execute("""
            UPDATE auditorias SET
                status = %s,
                fase_atual = %s,
                materialidade_global = %s
            WHERE codigo = %s
            RETURNING id
        """, (status, c["fase_atual"], c["materialidade_global"], codigo))
        return cur.fetchone()[0], "updated"
    else:
        new_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO auditorias (id, firma_id, cliente_id, codigo, exercicio,
                periodo_inicio, periodo_fim, status, fase_atual,
                materialidade_global, responsavel_tecnico_id, coordenador_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            new_id, firma_id, cliente_id, codigo, c["exercicio"],
            c["periodo_inicio"], c["periodo_fim"],
            status, c["fase_atual"],
            c["materialidade_global"],
            responsavel_id, coordenador_id
        ))
        return cur.fetchone()[0], "inserted"


def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    print("=== SEED CLIENTES AUDIPER ===\n")

    firma_id = get_firma_id(cur)
    print(f"Firma: {firma_id}\n")

    nazare_id = get_auditor_id(cur, "nazare@audiper.com.br")
    ricardo_id = get_auditor_id(cur, "ricardo@audiper.com.br")
    vitor_id = get_auditor_id(cur, "vitor@audiper.com.br")

    print(f"Auditores: Nazaré={nazare_id}, Ricardo={ricardo_id}, Vitor={vitor_id}\n")

    # Corrigir cargos e registros conforme equipe real AUDIPER
    # Nazaré: sócia responsável técnica
    cur.execute("UPDATE auditores SET cargo = 'socio', cnai = 'CNAI 1468', crc = 'CRC/PI 2629', cvm = 'CVM 5290', nivel_acesso = 4 WHERE email = 'nazare@audiper.com.br'")
    # Ricardo: usuário principal / coordenador sênior
    cur.execute("UPDATE auditores SET cargo = 'gerente', crc = 'CRC/PI 5374/O', nivel_acesso = 3 WHERE email = 'ricardo@audiper.com.br'")
    # Vitor: Gerente de Auditoria (não assistente)
    cur.execute("UPDATE auditores SET cargo = 'gerente', cnai = 'CNAI 4711', crc = 'CRC/PI 7929', nivel_acesso = 2 WHERE email = 'vitor@audiper.com.br'")
    print("Auditores atualizados com registros corretos.\n")

    totais = {"clientes_inseridos": 0, "clientes_atualizados": 0,
              "auditorias_inseridas": 0, "auditorias_atualizadas": 0}

    for c in CLIENTES:
        cliente_id, op_c = upsert_cliente(cur, firma_id, c)
        if op_c == "inserted":
            totais["clientes_inseridos"] += 1
        else:
            totais["clientes_atualizados"] += 1

        auditoria_id, op_a = upsert_auditoria(
            cur, firma_id, cliente_id, c,
            responsavel_id=nazare_id,
            coordenador_id=ricardo_id
        )
        if op_a == "inserted":
            totais["auditorias_inseridas"] += 1
        else:
            totais["auditorias_atualizadas"] += 1

        print(f"  [{op_c.upper()[:3]}/{op_a.upper()[:3]}] {c['nome_fantasia']:25} CNPJ: {c['cnpj']}  Fase: {c['fase_atual']:12}  Exercício: {c['exercicio']}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n=== CONCLUIDO ===")
    print(f"  Clientes: {totais['clientes_inseridos']} inseridos, {totais['clientes_atualizados']} atualizados")
    print(f"  Auditorias: {totais['auditorias_inseridas']} inseridas, {totais['auditorias_atualizadas']} atualizadas")


if __name__ == "__main__":
    main()
