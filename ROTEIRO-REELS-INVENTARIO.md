# ROTEIRO — Instagram Reels AUDIPER
## "Inventário ao vivo" | Painel de telemetria | 20 segundos

**Arquivo:** `reels-inventario-painel.html`
**Destino do CTA:** audiper.com (página de inventário: `auditoria-inventario-drone-agentes.html`)
**Sem prazo de validade.**

> **Formato:** painel que se explica sozinho. **Não tem locução e não precisa de
> uma** — é o único dos quatro reels que pode ir ao ar sem esperar o TTS ou a
> trilha. A sensação de sistema vivo vem dos contadores correndo e da malha se
> reorganizando, não de alguém narrando.

> **Nenhum motor de decisão em nuvem é citado.** A página de inventário vende
> "100% on-host · zero dado à nuvem" como diferencial. Creditar API de terceiro
> aqui contradiria a promessa, então o painel mostra apenas o que é da casa.

---

## LINHA DO TEMPO (20s, quatro fases de 5s)

| Fase | Janela | Destaque na tira | Rótulo abaixo |
|---|---|---|---|
| 01 | 0–5s | CAPTURA | BIND · CAPTURA AÉREA |
| 02 | 5–10s | RECONCILIAÇÃO | CRUZA FÍSICO × CONTÁBIL |
| 03 | 10–15s | ACHADO | ISOLA A DIVERGÊNCIA |
| 04 | 15–20s | ASSEGURAÇÃO | AUDITOR ASSINA |

---

## O QUE ESTÁ NA TELA

### Cabeçalho (fixo)
Logo radar 1:1 · **Inventário ao vivo** · `DRONE CONTA · AGENTE RECONCILIA · AUDITOR ASSEGURA`

Três contadores à direita, correndo:

| Contador | Comportamento | Valor final |
|---|---|---|
| POSIÇÕES | sobe de 0 até o total nos primeiros 4s | 1.680 |
| CONFERIDAS | sobe de 1,5s a 14,5s | 1.674 |
| DIVERGÊNCIAS | mostra "—" até 9s, depois sobe até 12s | 6 |

**Os números fecham entre si: 1.674 + 6 = 1.680.** Foi deliberado. Quem pausar o
vídeo e conferir encontra consistência — em material de auditoria isso pesa.

### Malha de agentes (centro)
46 nós e 34 arestas, em quatro grupos rotulados: DRONE · VISÃO COMPUTACIONAL ·
RAZÃO / SPED · AUDITOR.

A cada fase a malha se reorganiza:
- **01** — nós dispersos, sem estrutura (a captura ainda acontece)
- **02** — quatro grupos separados, um por papel
- **03** — grupos se aproximam; os nós de divergência acendem em vermelho
- **04** — tudo converge para o canto do auditor

### Painéis laterais (fixos)
**O QUE MUDA** — contagem sem parar a operação · nenhuma planilha no caminho ·
cada divergência com evidência · achado vira papel de trabalho

**ONDE RODA** — processamento `on-host` · dado à nuvem `zero` · evidência
`NBC TA 501` · registro `CRC/PI 000023/O`

### Grade de posições (rodapé)
168 células (24 × 7), preenchendo de 1,5s a 14,5s. Seis ficam vermelhas — as
mesmas seis do contador de divergências.

### Rodapé
`37 anos · fé de auditor · desde 1989` · audiper.com

E, em corpo menor: **simulação de operação · números ilustrativos**. Painel ao
vivo com números correndo sugere dados reais de cliente; sem essa linha, o reel
afirmaria resultado que não aconteceu.

---

## LEGENDA SUGERIDA

```
A contagem de estoque ainda é o elo fraco do controle patrimonial.

Feita à mão, ela para a operação, depende de planilha e é onde o erro se esconde
melhor. O balanço acaba confiando num número que quase ninguém consegue reauditar.

Trocamos isso por três camadas. O drone sobrevoa e a visão computacional conta,
sem interromper o estoque. A malha de agentes reconcilia o físico capturado contra
o contábil, o razão e o SPED, apontando cada divergência com evidência. E o auditor
valida a amostra, testa os achados e assina — dando fé pública conforme a NBC TA 501.

Tudo roda on-host. O dado do cliente não sai do ambiente.

A tecnologia acelera a contagem. Só o auditor transforma contagem em prova.

audiper.com

#audiper #auditoria #inventario #estoque #controlepatrimonial #NBCTA
#auditoriainterna #compliance #teresina #piaui #maranhao
```

---

## CONFERIR ANTES DE PUBLICAR

- [ ] A operação descrita (drone + malha de agentes) já é prestada como serviço
- [ ] O aviso de simulação está legível no rodapé
- [ ] Nenhum número foi apresentado como resultado de cliente real
- [ ] Logo radar em 1:1
- [ ] Os seis quadrados vermelhos da grade batem com o contador de divergências

---

## REGRAVAR

```bash
# abrir reels-inventario-painel.html e capturar 1080x1920 por 20s
```

A página segura as animações até estar pintada e só então as solta — por isso a
captura precisa descartar o primeiro segundo e meio. Sem esse descarte, os
primeiros quadros saem brancos.
