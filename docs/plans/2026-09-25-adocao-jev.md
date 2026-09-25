# Adoção do Jev (TypeSafe AI) nas aplicações AUDIPER

**Data:** 25/09/2026
**Status:** proposta — nenhuma linha de código alterada ainda

---

## 1. O que o Jev é (e o que ele não é)

Jev é um modelo "System One" da TypeSafe AI, lançado em 15/09/2026. Ele **não gera texto**.
Recebe um estado (`state`) e um mapa de perguntas tipadas (`questions`), e devolve uma resposta
por pergunta, em uma única passada paralela, com probabilidade calibrada.

Três primitivas:

| Primitiva | Para quê | Retorno |
|---|---|---|
| `Choice` | escolher entre opções sem ordem | `.choice` + `probabilities` |
| `Score` | classificar num espectro ordenado (2 a 10 níveis) | `.score` (média ponderada) + `confidence` |
| `Noul` | pergunta sim/não | `.noul` (0.0–1.0) |

- Endpoint: `POST https://api.typesafe.ai/v1/systemone`
- SDK Python: `pip install typesafe-sdk` (exige Python ≥ 3.10)
- Autenticação: variável de ambiente `TYPESAFE_API_KEY`
- Modelo padrão: `jev-latest`
- Preço: **US$ 0,042 por 1M de tokens de entrada; saída US$ 0** (não há stream de saída para cobrar)
- Latência divulgada: 70–500ms

Exemplo oficial, verbatim:

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

client = TypeSafeClient()

response = client.system_one(
    state=ticket,
    questions={
        "department": Choice(
            instructions="Which team should handle this",
            criteria={
                "billing": "Payment or subscription issues",
                "technical": "Bugs or integration problems",
                "sales": "Pricing or account questions",
            },
        ),
        "frustration": Score(
            instructions="How frustrated the customer appears",
            criteria=[
                "Calm, just stating facts",
                "Frustrated but civil",
                "Very angry, strong language",
            ],
        ),
        "is_urgent": Noul(
            instructions="The message conveys urgency or time-sensitivity",
        ),
    },
)

response.answers["department"].choice   # "technical"
response.answers["frustration"].score   # 1.0
response.answers["is_urgent"].noul      # 1.0
```

A resposta traz `usage` com `input_tokens` / `output_tokens`.

**Regra de ouro para nós:** Jev decide, classifica e pontua. Ele não escreve proposta, não
redige artigo, não fundamenta laudo. Onde hoje usamos LLM para *redigir*, continua LLM.

---

## 2. Onde isso encaixa no nosso código hoje

Mapeei os pontos onde já existe decisão — hoje feita por `if` de substring ou por regra fixa.
Ordenados por relação ganho/risco.

### 2.1 `should_trigger()` — `data/workflow_processor.py:45`

Hoje são 11 comparações de substring encadeadas. O roteamento erra de forma previsível: uma
mensagem "precisamos ver isso hoje ainda, o cliente tá cobrando" não dispara o workflow de
alerta, porque não contém as palavras `alerta` nem `urgente`.

Troca natural: um `Noul` por condição, ou um `Choice` único entre os workflows cadastrados.
Estado = a mensagem + autor + canal.

**Melhor primeiro alvo.** É função isolada, tem fallback trivial (a regra atual) e o erro é
barato e reversível.

### 2.2 Qualificação de lead — `data/agentes-audiper.md:462` e `wa/`

Hoje as regras de qualificação vivem dentro do prompt do LLM ("Pediu proposta/orçamento →
interesse 'proposta' → QUALIFICADO"). Isso significa que a decisão comercial depende de o
modelo de texto lembrar de seguir a instrução, e não é auditável depois.

Com Jev, a decisão sai do prompt e vira contrato tipado:

```python
questions={
    "interesse": Choice(
        instructions="Qual serviço AUDIPER o cliente está buscando",
        criteria={
            "proposta": "Pediu proposta, orçamento ou valores",
            "pericia": "Perícia contábil, judicial ou extrajudicial",
            "auditoria": "Auditoria contábil, fiscal ou de licitação",
            "consultoria_ia": "IA, automação, agentes",
            "lgpd": "LGPD, proteção de dados, privacidade",
            "indefinido": "Ainda não dá para dizer",
        },
    ),
    "maturidade": Score(
        instructions="Quão perto de fechar o cliente parece estar",
        criteria=[
            "Só curiosidade, pergunta genérica",
            "Interesse real, ainda comparando",
            "Quer falar com alguém agora, cita prazo ou valor",
        ],
    ),
    "quer_humano": Noul(instructions="O cliente está pedindo falar com uma pessoa"),
}
```

O LLM continua redigindo a resposta; o Jev decide se grava no `leads.db` e se notifica o
Telegram. Ganho real: parar de notificar lead frio e parar de perder lead quente que não usou a
palavra-chave.

### 2.3 Diagnóstico de CNPJ — `tools/diagnostico_cnpj.py:350`

São 9 regras determinísticas (situação cadastral, Simples com capital alto, CNAE industrial,
CNAE comércio, capital alto LTDA, grande porte, empresa antiga, MEI crescendo, IE inativa).

**Aqui não substituímos regra por Jev.** Essas regras são auditáveis, citam fundamentação
normativa e é exatamente isso que o cliente compra de nós. Uma probabilidade de 0,87 não
sustenta "IN RFB 1774/2017".

O Jev entra como camada *adicional*, depois das regras:

- `Score` de prioridade comercial do lead (porte + anos + alertas acumulados)
- `Choice` do serviço âncora da proposta, quando as regras recomendam três ou mais
- `Score` de risco global, para ordenar a fila de follow-up

O `valor_total` e a fundamentação continuam vindo da tabela de preços e das regras.

### 2.4 `firecrawl_intel.py:32`

`'has_cta': 'contato' in md.lower() or 'orcamento' in md.lower() or 'proposta' in md.lower()`
— e mais seis flags iguais. É literalmente o caso de uso do `Noul`. Risco quase zero, é
inteligência interna de concorrência.

### 2.5 Pipeline de artigos — `data/pipeline_artigos.py:75`

`register_research(..., relevancia='ALTA')` chega com o valor fixo no parâmetro. Um `Score` de
relevância editorial sobre o tema pesquisado resolve, e passa a ordenar a fila de produção.

---

## 3. Arquitetura proposta

Um único wrapper, `data/jev.py`, que todo chamador usa. Nada de `TypeSafeClient()` espalhado.

Responsabilidades do wrapper:

1. **Ler a chave de `TYPESAFE_API_KEY`** — nunca hardcoded. (Ver §5.)
2. **Timeout curto** (2s). Jev responde em 70–500ms; se passou de 2s, algo está errado.
3. **Fallback obrigatório.** Toda chamada recebe o resultado da regra atual como parâmetro. Se
   a API falhar, se a confiança vier abaixo do limiar, ou se estourar o timeout, retorna a
   regra. A plataforma está em beta e não tem SLA — o fallback não é refinamento, é requisito.
4. **Porta de confiança.** `confidence` abaixo do limiar (sugiro 0,7) não vira decisão
   automática: cai para o caminho humano ou para a regra antiga.
5. **Log de toda decisão** no Postgres: estado resumido, resposta, probabilidades, confiança,
   tokens, latência, e o que a regra antiga teria decidido. É esse log que permite medir.

```python
decisao = jev.decidir(
    state=mensagem,
    questions={...},
    fallback={"interesse": interesse_por_regra},
    min_confidence=0.7,
    contexto="qualificacao_lead",   # vai pro log
)
```

---

## 4. Rollout em fases

**Fase 0 — infraestrutura (meio dia).** Conta em `console.typesafe.ai` (não há mais lista de
espera desde 20/09), chave em variável de ambiente, `data/jev.py` com fallback e log, tabela
`jev_decisoes` no Postgres.

**Fase 1 — modo sombra (1 semana).** Jev roda em paralelo em `should_trigger()` e na
qualificação de lead, **sem afetar o comportamento**. Só grava o que teria decidido. Ao fim da
semana, comparamos: onde concordam, onde divergem, e em quais divergências o Jev estava certo.

**Fase 2 — ativar o que provou.** Só promove a decisão do Jev onde a taxa de concordância e as
divergências revisadas justificarem. Mantém o log ligado.

**Fase 3 — expandir.** `firecrawl_intel`, relevância de artigos, priorização de diagnósticos.

A fase 1 é o ponto inegociável do plano. Adotar decisão probabilística sem medir contra a regra
que já existe é trocar um erro conhecido por um desconhecido.

---

## 5. Riscos e restrições

**LGPD.** Mensagem de WhatsApp, nome, CNPJ e dado de cliente passando para uma API de terceiro
é tratamento de dados com novo subprocessador. Antes da Fase 2, isso precisa constar no aviso
em `privacidade.html`. Para a Fase 1 (modo sombra) vale começar só com `workflow_processor`, que
é mensagem interna da equipe, e deixar o dado de cliente para depois do ajuste contratual.

**Nada de parecer técnico saindo de probabilidade.** Laudo pericial, fundamentação normativa e
valor de proposta continuam determinísticos. O Jev prioriza e classifica; não conclui.

**Beta sem SLA.** Preço zero na saída hoje não é compromisso de preço amanhã. O wrapper com
fallback cobre a queda; a planilha de custo deve assumir que um dia passa a cobrar.

**Custo real, estimado.** A US$ 0,042/1M de entrada, um estado de ~1.000 tokens sai a
US$ 0,000042 por decisão. Mil decisões por dia = US$ 0,042/dia. Não é fator na decisão.

**Chave de API — não repetir o erro atual.** Hoje temos `postgresql://postgres:audiper2026@...`
em texto claro em sete arquivos de `data/`, versionados. O `.gitignore` cobre apenas
`data/.env`, não um `.env` na raiz. Antes de adicionar qualquer chave nova: corrigir o
`.gitignore` e padronizar tudo em variável de ambiente.

---

## 6. Primeiro passo concreto

Implementar `data/jev.py` + modo sombra em `should_trigger()`. É a fatia que não toca dado de
cliente, não muda comportamento nenhum em produção, e em uma semana devolve número em vez de
opinião sobre o Jev servir ou não para nós.

---

## Fontes

- Quickstart e SDK: https://docs.typesafe.ai/introduction/quickstart
- Primitiva Score: https://docs.typesafe.ai/primitives/score
- Anúncio e características: https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/
