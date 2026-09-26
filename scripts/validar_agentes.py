#!/usr/bin/env python3
"""
validar_agentes.py — valida as definicoes de agentes contra o schema e contra
a regra de escolha de modelo.

Tres invariantes:
  1. Todo agente valida contra agents/schema/agent-definition.json.
  2. Todo model_tier declarado existe em agents/model-tiers.json.
  3. Nenhum agente fixa modelo direto — a escolha vive so no model-tiers.json.

A terceira e o ponto: enquanto o modelo estiver escrito na definicao do agente,
trocar de geracao significa editar N arquivos e torcer para nao esquecer um.

Uso:
    python scripts/validar_agentes.py            # valida tudo
    python scripts/validar_agentes.py --tiers    # mostra a distribuicao por tier

Sai com codigo 1 se algo falhar, para poder rodar em CI.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SETORES = RAIZ / "agents" / "sectors"
SCHEMA = RAIZ / "agents" / "schema" / "agent-definition.json"
TIERS = RAIZ / "agents" / "model-tiers.json"

# Nomes de modelo que nao devem aparecer dentro de uma definicao de agente.
MODELO_CRAVADO = re.compile(
    r"\b("
    r"claude-(?:opus|sonnet|haiku|fable|mythos|instant)[a-z0-9.-]*"
    r"|(?:opus|sonnet|haiku|fable)[ -][0-9][0-9.-]*"
    r"|gpt-[0-9][0-9.-]*"
    r"|gemini[ -][0-9][0-9.-]*"
    r"|llama-[0-9][0-9.-]*"
    r")\b",
    re.IGNORECASE,
)
# Nao casa nome de biblioteca (claude-agent-sdk, claude-code): so forma de ID de modelo.


def carregar(p: Path):
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    erros, avisos = [], []

    tiers = carregar(TIERS)["tiers"]
    schema = carregar(SCHEMA)

    try:
        from jsonschema import Draft7Validator
        validador = Draft7Validator(schema)
    except ImportError:
        validador = None
        avisos.append("jsonschema nao instalado — validacao estrutural pulada (pip install jsonschema)")

    distribuicao, total = {}, 0

    for arquivo in sorted(SETORES.glob("*.json")):
        setor = carregar(arquivo)
        for agente in setor.get("agents", []):
            total += 1
            onde = f"{arquivo.name}:{agente.get('id', '?')}"

            if validador:
                # O schema descreve um agente completo; nos arquivos de setor o campo
                # 'sector' e fatorado para a raiz. Injeta antes de validar, em vez de
                # repetir o setor em 141 registros.
                completo = dict(agente)
                completo.setdefault("sector", setor.get("sector"))
                for e in validador.iter_errors(completo):
                    erros.append(f"{onde}: {e.message}")

            tier = agente.get("model_tier")
            if tier is None:
                avisos.append(f"{onde}: sem model_tier")
            elif tier not in tiers:
                erros.append(f"{onde}: model_tier '{tier}' nao existe em model-tiers.json")
            else:
                distribuicao[tier] = distribuicao.get(tier, 0) + 1

            # Invariante 3: procura nome de modelo em qualquer campo de texto.
            for campo in ("role", "capabilities", "skills"):
                valor = agente.get(campo)
                textos = valor if isinstance(valor, list) else [valor or ""]
                for t in textos:
                    achado = MODELO_CRAVADO.search(str(t))
                    if achado:
                        erros.append(
                            f"{onde}: modelo cravado em '{campo}' ({achado.group(0)}) "
                            "— use model_tier e deixe o modelo em model-tiers.json"
                        )

    print(f"{total} agentes em {len(list(SETORES.glob('*.json')))} setores")
    if distribuicao:
        com_tier = sum(distribuicao.values())
        print(f"com model_tier: {com_tier} ({com_tier * 100 // total}%)")
        for t, n in sorted(distribuicao.items(), key=lambda x: -x[1]):
            print(f"  {t:<14} {n:>3}  ->  {tiers[t]['modelo']}")

    if avisos:
        print(f"\n{len(avisos)} aviso(s):")
        for a in avisos[:10]:
            print(f"  · {a}")
        if len(avisos) > 10:
            print(f"  · ... e mais {len(avisos) - 10}")

    if erros:
        print(f"\n{len(erros)} ERRO(S):")
        for e in erros:
            print(f"  ✗ {e}")
        return 1

    print("\nok — nenhum erro")
    return 0


if __name__ == "__main__":
    sys.exit(main())
