# NARRAÇÃO — Reels AUDIPER

Texto pronto para o TTS, cortado no orçamento de tempo de cada cena.

**Voz:** Algenib (Gemini 3.1 Flash TTS), fallback Gacrux
**Cadência de referência:** ~2 palavras/segundo
**BGM:** -14 dB sob a locução

> **Por que o texto mudou.** A locução nos roteiros foi escrita como apoio de
> sentido, sem contar o relógio. Medida na cadência da Algenib, ela dava 44s de
> fala no reel de conciliação (que tem 20s) e 49s no do Simples. Cada linha abaixo
> foi reescrita para caber no seu slide, com margem para respiração.
>
> Os roteiros seguem com o texto longo, que continua servindo para legenda e para
> quem for narrar ao vivo, sem a restrição do TTS.

---

## CENA — CONTEXTO (20s) · `reels-jev-contexto.html`

| Trecho | Janela | Texto | Palavras | Fala |
|---|---|---|---|---|
| C1 | 0,0–6,0s | Agente, prompt, ferramenta, saída. Cada passo espera o anterior. | 9 | 4,5s |
| C2 | 6,0–14,0s | Um estado. Várias perguntas. Uma passada só. | 7 | 3,5s |
| C3 | 14,0–20,0s | O sistema admite quando não sabe. | 6 | 3,0s |

Entrada de cada trecho: 0,5s depois do início da janela.

---

## CENA — CONCILIAÇÃO (20s) · `reels-conciliacao.html`

| Slide | Janela | Texto | Palavras | Fala |
|---|---|---|---|---|
| 1 | 0,0–3,5s | Quatro mil lançamentos. Um não fecha. | 6 | 3,0s |
| 2 | 3,5–8,0s | O tempo some na conferência, não na análise. | 8 | 4,0s |
| 3 | 8,0–13,0s | Casa. Não casa. Ou precisa de auditor. | 7 | 3,5s |
| 4 | 13,0–17,0s | Triagem automatizada. Parecer assinado por auditor. | 6 | 3,0s |
| 5 | 17,0–20,0s | Do dado até a prova. | 5 | 2,5s |

---

## CENA — SIMPLES NACIONAL (20s) · `reels-simples-setembro.html`

| Slide | Janela | Texto | Palavras | Fala |
|---|---|---|---|---|
| 1 | 0,0–3,0s | Cinco dias para decidir. | 4 | 2,0s |
| 2 | 3,0–8,0s | Até 30 de setembro: dentro ou fora do DAS. | 9 | 4,5s |
| 3 | 8,0–14,0s | No DAS, o crédito vai parcial ao seu cliente empresa. | 10 | 5,0s |
| 4 | 14,0–17,5s | Vende para empresa? Faça a conta. | 6 | 3,0s |
| 5 | 17,5–20,0s | Simule antes de decidir. | 4 | 2,0s |

> O número do slide 1 muda a cada dia. Se gravar em 26/09, a locução é
> "Quatro dias para decidir"; em 30/09, "Hoje é o último dia". A imagem se
> ajusta sozinha, o áudio não.

---

## CENA — FECHO (7s) · `reels-fecho.html`

| Trecho | Janela | Texto | Palavras | Fala |
|---|---|---|---|---|
| F1 | 0,5–7,0s | A máquina separa. O auditor assina. | 6 | 3,0s |

---

## O QUE O TTS DEVE RECEBER

Um arquivo por trecho, nomeado pela cena e pelo número:

```
narr-contexto-c1.wav   narr-conciliacao-s1.wav   narr-simples-s1.wav   narr-fecho-f1.wav
narr-contexto-c2.wav   narr-conciliacao-s2.wav   narr-simples-s2.wav
narr-contexto-c3.wav   narr-conciliacao-s3.wav   narr-simples-s3.wav
                       narr-conciliacao-s4.wav   narr-simples-s4.wav
                       narr-conciliacao-s5.wav   narr-simples-s5.wav
```

Arquivos separados, não um áudio corrido: assim cada fala entra no segundo
certo da sua cena, e um ajuste de texto não obriga a regerar tudo.

---

## MONTAGEM

Com os .wav da narração e a trilha, a mixagem é local. Para cada cena:

```bash
# 1. Narração posicionada no tempo de cada slide
ffmpeg -i cena.mp4 \
  -i narr-s1.wav -i narr-s2.wav -i narr-s3.wav -i narr-s4.wav -i narr-s5.wav \
  -i trilha.wav \
  -filter_complex "\
    [1]adelay=500|500[a1]; \
    [2]adelay=4000|4000[a2]; \
    [3]adelay=8500|8500[a3]; \
    [4]adelay=13500|13500[a4]; \
    [5]adelay=17500|17500[a5]; \
    [6]volume=-14dB,afade=t=out:st=18:d=2[bgm]; \
    [a1][a2][a3][a4][a5][bgm]amix=inputs=6:duration=first:normalize=0[mix]" \
  -map 0:v -map "[mix]" -c:v copy -c:a aac -b:a 192k cena-com-audio.mp4
```

Os valores de `adelay` são o início de cada janela em milissegundos, mais 500ms
de respiro. A trilha entra em -14 dB e sai com fade de 2s no fim.

---

## O QUE FALTA, E DE QUEM

**Da equipe:** gerar os .wav pela Algenib e mandar o arquivo da trilha. Não tenho
acesso ao Gemini TTS por aqui, nem existe áudio no repositório.

**Deste lado:** com os arquivos em mãos, a mixagem e a remontagem dos cortes de
47s e 67s saem no mesmo dia.

**A confirmar:** o `design-system/README.md` e o `INTAKE.md` especificam BGM de
**violino** em -14 dB. O pedido foi violoncelo. Se a trilha mudou, os dois
arquivos do design-system precisam ser atualizados — senão o próximo material
sai com a instrução antiga.
