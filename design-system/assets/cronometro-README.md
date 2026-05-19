# Reel Cronometro — componente Remotion AUDIPER

Componente reusavel pra produzir Reels de **40s** com a estrutura:

```
[bookend image fade-in 4s] → [animacao loop 32s] → [bookend image fade-out 4s]
                          + violin BGM com fade in/out
```

Formato configuravel: **1:1** (1080x1080 feed/multi), **9:16** (1080x1920 Reels nativo), **4:5** (1080x1350 feed IG).

Validado em 16/05/2026 com a serie de pericia trabalhista (AUDIX msgs 685-691).

---

## Instalacao

```bash
cd /home/audiper/AUDITORIAS/_AUDIX/_components/reel-cronometro
bun install   # ou npm install
```

## Uso 1 — Studio (preview ao vivo)

```bash
npm run studio
# abre http://localhost:3000 com 3 compositions:
#  - ReelCronometro                (generica, edita props na UI)
#  - ReelCronometroTrabalhista     (9:16 pericia exemplo)
#  - ReelCronometro1x1Sandwich     (1:1 sandwich exemplo)
```

Edita props no painel direito do Studio sem mexer no codigo.

## Uso 2 — Render CLI parametrizado

```bash
./scripts/render.sh \
  --client=megalink \
  --format=9x16 \
  --image=megalink-infografico.png \
  --animation=megalink-cronograma.mp4 \
  --bookend-secs=4 \
  --video-secs=32 \
  --out=out/megalink_cronograma.mp4
```

Assets devem estar em `public/` (ou caminho absoluto).

## Uso 3 — Render via remotion CLI direto

```bash
npx remotion render src/index.ts ReelCronometro out/foo.mp4 \
  --props='{
    "format": "9x16",
    "bookendImage": "foo.png",
    "animation": "foo.mp4",
    "audio": "violin-bgm.mp3",
    "bookendDurationSeconds": 4,
    "videoDurationSeconds": 32,
    "audioStartFromSeconds": 30,
    "audioVolume": 0.55,
    "audioFadeInFrames": 45,
    "audioFadeOutFrames": 60,
    "bookendFadeFrames": 18,
    "bookendObjectFit": "cover",
    "bookendObjectPosition": "center",
    "bookendBackgroundColor": "#0e1116",
    "videoObjectFit": "cover"
  }'
```

## Uso 4 — Importar em outra composition Remotion

```tsx
import { ReelCronometro } from "/home/audiper/AUDITORIAS/_AUDIX/_components/reel-cronometro/src";

<ReelCronometro
  format="1x1"
  bookendImage={staticFile("client/arte.png")}
  animation={staticFile("client/anim.mp4")}
  audio={staticFile("violin-bgm.mp3")}
  bookendDurationSeconds={4}
  videoDurationSeconds={32}
  audioStartFromSeconds={30}
  audioVolume={0.55}
  audioFadeInFrames={45}
  audioFadeOutFrames={60}
  bookendFadeFrames={18}
  bookendObjectFit="cover"
  bookendObjectPosition="center"
  bookendBackgroundColor="#0e1116"
  videoObjectFit="cover"
/>
```

---

## Schema Zod (props)

| Prop | Tipo | Default | Descricao |
|---|---|---|---|
| `format` | `'1x1' \| '9x16' \| '4x5'` | `'1x1'` | Aspect ratio |
| `bookendImage` | string | `'example-infografico.png'` | Imagem estatica nos bookends |
| `animation` | string | `'example-animation.mp4'` | MP4 da animacao do meio (loop) |
| `audio` | string | `'violin-bgm.mp3'` | Trilha sonora |
| `bookendDurationSeconds` | number | `4` | Duracao de cada bookend |
| `videoDurationSeconds` | number | `32` | Duracao da animacao do meio |
| `audioStartFromSeconds` | number | `30` | Seek inicial no audio (-ss) |
| `audioVolume` | number | `0.55` | Volume da trilha |
| `audioFadeInFrames` | number | `45` | Fade-in da trilha (1.5s @ 30fps) |
| `audioFadeOutFrames` | number | `60` | Fade-out da trilha (2s @ 30fps) |
| `bookendFadeFrames` | number | `18` | Fade in/out do bookend image |
| `bookendObjectFit` | `'cover' \| 'contain'` | `'cover'` | CSS object-fit |
| `bookendObjectPosition` | string | `'center'` | CSS object-position |
| `bookendBackgroundColor` | string | `'#0e1116'` | Fundo (letterbox/pillarbox) |
| `videoObjectFit` | `'cover' \| 'contain'` | `'cover'` | CSS object-fit do video |

---

## Pattern AUDIPER

- **Audio default**: `violin-bgm.mp3` com `-ss 30` (pula intro pra ponto musical mais forte)
- **Cor fundo default**: `#0e1116` (claret-deep escuro, sem competir com a arte)
- **Duracao default**: 4+32+4 = 40s
- **fps**: 30 (Reels-friendly)
- **Encode recomendado**: CRF 22, maxrate 5500k, yuv420p, faststart

## Onde usar (memoria `feedback_reel_40s_widget_relatorios`)

- **Proposta HTML**: `<video autoplay loop muted playsinline>` na secao Cronograma
- **Relatorio PDF**: poster frame + QR code linkando pro MP4
- **Telegram/WhatsApp cliente**: anexar MP4 direto
- **LinkedIn/IG da AUDIPER**: Reel nativo

## Assets default em `public/`

- `violin-bgm.mp3` — trilha sonora padrao AUDIPER
- `example-infografico.png` — bookend exemplo (infografico pericia)
- `example-animation.mp4` — animation exemplo (K-style pericia trabalhista)

---

## Render direto via ffmpeg (alternativa sem Node)

Se nao quiser Remotion, o pattern equivalente em ffmpeg esta documentado em
`/home/audiper/AUDITORIAS/_AUDIX/cards-pericia-2026/` (build_reel.sh) e usa
xfade entre loops + violin BGM. Use Remotion quando precisar de:
- preview ao vivo (Studio)
- parametrizacao tipada (Zod schema)
- componentizacao (importar em outras compositions)

Use ffmpeg quando:
- one-off render simples sem instalar Node
- batch automation puro shell

## Manutencao

- Padrao registrado em `~/.claude/projects/-home-audiper/memory/feedback_reel_40s_widget_relatorios.md`
- Quando criar variante recorrente (ex: cronograma fases A->G), adicionar
  Composition pre-configurada em `src/Root.tsx`
