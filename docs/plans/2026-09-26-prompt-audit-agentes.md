# Prompt Audit — definições de agentes AUDIPER

**Data:** 26/09/2026
**Status:** relatório + diff proposto. **Nenhuma edição aplicada.**

---

## Premissas (Passo 0)

**Escopo.** A superfície de prompt do repositório: `data/agentes-audiper.md`,
`data/agentes-audix.md`, `templates/prompt-diagnostico.md`, `agents/registry.json`,
`agents/sectors/*.json`, `agents/schema/*.json` e `.claude/launch.json`.
Não há `CLAUDE.md` nem `AGENTS.md` neste repositório.

`.claude/launch.json` foi verificado apenas quanto a chaves de modelo/prompt — não
carrega nenhuma — e não foi lido por inteiro, porque arquivos de configuração do
agente podem guardar segredo.

**Modelo-alvo.** A requisição não nomeou modelo e o repositório não documenta
migração em curso, então os arquivos de instrução foram auditados contra o modelo
que executa esta auditoria.

**Marcadores de outro fornecedor.** O repositório chama Gemini, Groq/Llama e Ollama
(`data/dashboard_api.py` conversa com `localhost:11434`). Isso está registrado como
premissa e **nada aqui propõe trocar fornecedor** — as observações sobre esses
modelos tratam apenas de versão desatualizada citada no próprio texto.

---

## Resumo

Três achados de alta confiança, todos da mesma família: **o texto dos agentes
descreve uma realidade que o repositório não tem mais.** O agente de QC é mandado
validar tom contra dois arquivos que não existem; o atendente de WhatsApp declara
usar um contexto RAG que nenhum código gera; e sete definições fixam versões de
modelo, quatro delas numa geração já superseda.

Nenhum achado em Grupo 1a/1c que valha edição: a linguagem de pressão nos prompts
quase toda carrega restrição real de auditoria — evidência, confidencialidade,
vocabulário técnico — e fica. Isso é resultado bom, não ausência de auditoria.

| Grupo | Achados |
|---|---|
| 1 — texto datado | 2 (1 rewrite, 2 flag) |
| 2 — arquivos de instrução | 5 |
| 3 — descrições de ferramenta | não aplicável (não há array `tools`) |
| 4 — configuração de requisição | 1 |

---

## Achados

### F1 · ALTA · `data/agentes-audiper.md:417`

**Evidência:** `- CLAUDE.md e SOUL.md (regras de tom e estilo)`

**Padrão:** Grupo 2 — especificidade volátil (caminho citado que não resolve).

**Por que:** Nem `CLAUDE.md` nem `SOUL.md` existem no repositório. O agente de QC —
o que tem poder de reprovar documento antes de ir ao cliente — é instruído a validar
tom e estilo contra dois arquivos ausentes. As regras que ele deveria aplicar existem,
mas em outro lugar: `design-system/INTAKE.md` (vocabulário, anti-IA na copy, regras
visuais inegociáveis) e `design-system/notes.md`.

**Ação:** `rewrite`

---

### F2 · ALTA · `data/agentes-audiper.md:435`

**Evidência:** `**Modelo:** Groq (llama-3.3-70b) + RAG (rag_context.txt)`

**Padrão:** Grupo 2 — especificidade volátil.

**Por que:** `rag_context.txt` não existe no repositório e nenhum script o gera:
a busca por `rag_context` em todo `*.py` e `*.json` do projeto não retorna nada.
A Audina Jr é o agente que fala com cliente no WhatsApp, e a base de conhecimento
que ela declara consultar não está no projeto. Ou o arquivo vive fora do repositório
— e então precisa de caminho —, ou a instrução descreve uma capacidade que ela não tem.

**Ação:** `rewrite` — nomear a origem real do contexto, ou remover a menção.

---

### F3 · ALTA · `data/agentes-audiper.md:34,142,216,352` e `data/agentes-audix.md:33`

**Evidência:** `**Modelo:** Claude Sonnet 4 (via OpenClaw) / Claude Code (direto)`,
`**Modelo:** Claude Sonnet 4 (analise complexa)`, `**Modelo:** Claude Sonnet 4
(redacao premium)`, `**Modelo:** Claude Sonnet 4 (revisao rigorosa)`

**Padrão:** Grupo 2 — narrativa histórica, versão de modelo fixada no texto.

**Por que:** São sete pins de modelo no arquivo, quatro deles numa geração Sonnet já
superseda. Versão fixada em texto de instrução degrada em silêncio a cada
lançamento: ninguém é dono da atualização, e o documento passa a descrever uma
configuração que não roda mais. O papel de cada agente ("análise complexa",
"redação premium") é a informação estável; a versão não é.

**Ação:** `rewrite` — descrever o papel e concentrar as versões numa tabela única,
em vez de espalhá-las por sete seções.

---

### F4 · MÉDIA · `data/agentes-audiper.md:269`

**Evidência:** `- Templates em D:/AUDITORIAS/_templates/`

**Padrão:** Grupo 2 — especificidade volátil (caminho absoluto fixado).

**Por que:** Caminho absoluto de Windows dentro do prompt. Não é verificável a partir
do repositório (está fora dele) e quebra em qualquer máquina que não seja aquela —
inclusive na máquina Linux do stack. É o mesmo problema que `tools/diagnostico_cnpj.py`
tinha com `D:/Site/audiper/`.

**Ação:** `rewrite` — variável de ambiente.

---

### F5 · MÉDIA · `data/agentes-audiper.md:340`

**Evidência:** `- NUNCA envie alerta duplicado (verificar ultimos alertas antes)`

**Padrão:** Grupo 2 — instrução não fiscalizada.

**Por que:** Nenhum código verifica duplicidade de alerta. A busca por
`duplicad|duplicate|ja_enviado|last_alert` em `data/` e `scripts/` não retorna nada.
A regra existe só como prosa, e prosa não impede o segundo alerta de sair. Regra que
pode virar checagem em código é mais confiável em código.

**Ação:** `rewrite` + fiscalizar no código — a checagem cabe onde o alerta é montado.

---

### F6 · MÉDIA · `data/agentes-audiper.md:451`

**Evidência:** `6. NUNCA responda fora do escopo (piadas, politica, esportes)`

**Padrão:** Grupo 1e — proibição sem procedência, descrevendo estilo de saída.

**Por que:** Diferente das regras vizinhas (449 e 450 protegem responsabilidade
profissional e sigilo de cliente, e ficam), esta enumera assuntos indesejados sem
dizer o que fazer. Enumerar o que não fazer ancora o modelo naquilo e não cobre o
caso seguinte; dizer o comportamento desejado cobre.

**Ação:** `rewrite` — afirmação positiva.

---

### F7 · MÉDIA · `data/agentes-audiper.md:287` vs `design-system/INTAKE.md:11`

**Evidência:** `**Modelo:** Gemini 2.5 Flash (rapido, baixo custo) / Groq (fallback)`
contra `Reels institucionais 1080x1920 (HyperFrames + Gemini 3.1 Flash TTS)`

**Padrão:** Grupo 2 — arquivos de instrução em desacordo sobre o mesmo ponto.

**Por que:** Dois arquivos do projeto citam gerações diferentes do mesmo fornecedor.
Os usos não são idênticos (um é o agente Igor, outro é TTS de reels), então pode não
ser contradição — mas nada no repositório diz qual é a versão corrente, e o
`git blame` não ordena os dois de forma conclusiva.

**Ação:** `flag` — a equipe decide qual versão está em uso. Sem proposta de troca de
fornecedor.

---

### F8 · BAIXA · `data/agentes-audiper.md:112`

**Evidência:** `- NUNCA invente ou extrapole — se nao encontrar, diga "nao localizado"`

**Padrão:** Grupo 1c — datação por idioma (`do not hallucinate`).

**Por que:** É a forma clássica de uma instrução escrita contra modelos que
fabricavam com mais frequência. Remover aqui é hipótese, não conclusão — e num agente
de pesquisa para auditoria o custo de um erro é alto.

**Ação:** `flag` — não editar sem medir. Se um dia for testada, a forma mínima
("registre 'não localizado' quando a busca não retornar") substitui a original.

---

### F9 · BAIXA · `data/agentes-audiper.md:446`

**Evidência:** `1. Responda SEMPRE em portugues BR`

**Padrão:** Grupo 1a — ênfase sem necessidade demonstrada.

**Por que:** A instrução é legítima e fica; só o caixa-alta é herança de prompt
escrito para modelo menos aderente. Custo de manter: nenhum. Por isso é `flag`.

**Ação:** `flag`

---

## O que NÃO é cruft — e fica

Registrado porque uma auditoria que só diz "apague" faz mal a quem a segue à risca:

| Local | Texto | Por que fica |
|---|---|---|
| `:204` | `NUNCA apresente excecao como achado confirmado sem evidencia` | Restrição técnica de auditoria (achado exige evidência). Procedência clara. |
| `:257` | Vocabulário proibido: "erro grave", "falha", "irregularidade"… | Política de posicionamento da firma, documentada em `INTAKE.md` ("auditoria como libertação do gestor, nunca como acusação"). Tem razão declarada. |
| `:362` | `CHECKLIST OBRIGATORIO (executar em TODA revisao)` | Operação frágil: onde exatamente uma sequência é segura, script exato é o correto. |
| `:423-424` | `NUNCA aprove documento com dados do cliente errados (BLOQUEANTE)` | Restrição de responsabilidade. Bloqueante de verdade. |
| `:449-450` | Não dar consultoria específica; não revelar dados de outros clientes | Responsabilidade profissional e sigilo. Ficam. |
| Assinaturas fixas, CRC, CNAI 4.711 | — | Fato do ambiente que só o autor sabe. Contexto nunca é cruft. |

---

## Diff proposto

Um achado por bloco, para você aceitar separadamente.

### F1 — QC aponta para os arquivos que existem

```diff
 FERRAMENTAS:
-- CLAUDE.md e SOUL.md (regras de tom e estilo)
+- design-system/INTAKE.md e design-system/notes.md (vocabulario, anti-IA na copy,
+  regras visuais inegociaveis)
 - NBC TAs (validar referencias)
```

### F2 — Audina Jr declara a origem real do contexto

```diff
-**Modelo:** Groq (llama-3.3-70b) + RAG (rag_context.txt)
+**Modelo:** Groq (llama-3.3-70b)
+**Base de conhecimento:** <apontar a origem real; nenhum arquivo rag_context.txt
+existe no repositorio e nenhum script o gera>
```

### F3 — versões saem das sete seções e viram uma tabela

```diff
-**Modelo:** Claude Sonnet 4 (analise complexa) / Python scripts (calculos)
+**Modelo:** analise complexa (ver tabela de modelos no topo) / Python scripts (calculos)
```

E, no topo do arquivo, um bloco único:

```markdown
## Modelos em uso
| Papel | Modelo | Atualizado em |
|---|---|---|
| analise complexa, redacao, revisao | <geracao corrente> | <data> |
| pesquisa rapida, vigilancia | <provedor/versao> | <data> |
| atendimento WhatsApp | <provedor/versao> | <data> |
```

### F4 — caminho de templates por variável de ambiente

```diff
 FERRAMENTAS:
-- Templates em D:/AUDITORIAS/_templates/
+- Templates no diretorio apontado por AUDIPER_TEMPLATES_DIR
```

### F5 — a regra de duplicidade sai da prosa e vira checagem

```diff
-- NUNCA envie alerta duplicado (verificar ultimos alertas antes)
+- Alerta duplicado e bloqueado no codigo que monta o envio, nao aqui:
+  consulte o registro dos ultimos alertas antes de compor um novo.
```

E a checagem correspondente onde o alerta é montado — hoje não existe nenhuma.

### F6 — escopo em afirmação positiva

```diff
-6. NUNCA responda fora do escopo (piadas, politica, esportes)
+6. Mantenha a conversa nos servicos AUDIPER. Para qualquer outro assunto,
+   ofereca o contato com a equipe.
```

---

## Verificação (Passo 7)

Os achados F1, F2, F4 e F5 são verificáveis contra o repositório, não contra
comportamento: basta reconferir se o caminho existe e se a checagem foi escrita.

F3 e F6 mudam texto que o modelo lê, então valem a regra: uma alteração por vez, e
se a remoção piorar, reescrever na forma mínima em vez de restaurar o original.

**Re-auditar a cada troca de modelo.** Prompt é artefato por geração: linha que
sustenta uma pode ser peso morto na seguinte.
