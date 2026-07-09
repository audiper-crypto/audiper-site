#!/usr/bin/env python3
"""
AUDIPER - Baixar & Analisar Reels do Instagram (para comparar com os nossos)

Baixa um Reel do Instagram (video + audio), salva a legenda/metadados e,
opcionalmente, gera a transcricao do audio. Serve para analisar reels de
referencia e comparar com o nosso roteiro (ROTEIRO-REELS.md / reels-animacao.html).

------------------------------------------------------------------------------
POR QUE ESTE SCRIPT RODA NA SUA MAQUINA, E NAO NO AMBIENTE DA WEB
------------------------------------------------------------------------------
O ambiente do Claude Code na web usa uma politica de rede em ALLOWLIST: so
libera GitHub e registries de pacote (pypi/npm). instagram.com e qualquer
servico de download de terceiros (cobalt.tools, apify, etc.) respondem 403 no
proxy. Portanto o download PRECISA rodar aqui, na sua maquina, onde:
  - ha acesso normal a internet;
  - existe um navegador logado na Instagram (para os cookies de sessao).

------------------------------------------------------------------------------
PRE-REQUISITOS
------------------------------------------------------------------------------
  pip install -U yt-dlp
  # ffmpeg no PATH (para juntar video+audio e extrair audio):
  #   Windows:  winget install Gyan.FFmpeg      (ou choco install ffmpeg)
  #   macOS:    brew install ffmpeg
  #   Linux:    sudo apt install ffmpeg
  # (Opcional) transcricao:  pip install -U openai-whisper   (tambem usa ffmpeg)

  Esteja LOGADO na Instagram no Chrome (ou Firefox/Edge). O script usa os
  cookies do navegador; Reels quase sempre exigem sessao autenticada.

------------------------------------------------------------------------------
USO
------------------------------------------------------------------------------
  python tools/baixar_reel.py "https://www.instagram.com/reel/XXXXXXXXX/"

  # escolher navegador dos cookies (padrao: chrome)
  python tools/baixar_reel.py URL --browser firefox

  # usar arquivo cookies.txt exportado (extensao "Get cookies.txt LOCALLY")
  python tools/baixar_reel.py URL --cookies-file cookies.txt

  # ja transcrever o audio (requer openai-whisper)
  python tools/baixar_reel.py URL --transcrever

  # pasta de saida (padrao: reels_baixados/)
  python tools/baixar_reel.py URL --saida reels_baixados

Saidas geradas na pasta de destino:
  <id>.mp4        video
  <id>.m4a        audio extraido
  <id>.info.json  metadados completos (legenda, hashtags, autor, duracao...)
  <id>.txt        resumo legivel (titulo, autor, legenda, hashtags)
  <id>.transcricao.txt  (se --transcrever)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str]) -> int:
    print("  $", " ".join(cmd))
    return subprocess.call(cmd)


def yt_dlp_disponivel() -> bool:
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def montar_auth_args(args) -> list[str]:
    if args.cookies_file:
        return ["--cookies", args.cookies_file]
    # cookies direto do navegador logado (metodo recomendado pela comunidade em 2026)
    return ["--cookies-from-browser", args.browser]


def baixar(url: str, saida: Path, auth: list[str]) -> Path | None:
    saida.mkdir(parents=True, exist_ok=True)
    template = str(saida / "%(id)s.%(ext)s")

    # 1) video (merge do melhor video+audio em mp4) + salva metadados .info.json
    rc = sh([
        "yt-dlp",
        *auth,
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "--write-info-json",
        "--no-playlist",
        "-o", template,
        url,
    ])
    if rc != 0:
        print("\n[!] Falha no download. Causas comuns:")
        print("    - Nao esta logado na Instagram no navegador escolhido (--browser).")
        print("    - Cookies expirados: reabra a Instagram no navegador e tente de novo.")
        print("    - Extractor desatualizado: rode  yt-dlp -U  (ou --update-to nightly).")
        print("    - Rate-limit: espere alguns minutos.")
        return None

    # 2) extrai o audio em .m4a (para transcrever/analisar a trilha)
    sh([
        "yt-dlp",
        *auth,
        "-f", "ba/b",
        "-x", "--audio-format", "m4a",
        "--no-playlist",
        "-o", template,
        url,
    ])

    infos = sorted(saida.glob("*.info.json"), key=lambda p: p.stat().st_mtime)
    return infos[-1] if infos else None


def resumir_metadados(info_json: Path) -> Path:
    data = json.loads(info_json.read_text(encoding="utf-8"))
    descricao = (data.get("description") or "").strip()
    hashtags = re.findall(r"#\w+", descricao)

    linhas = [
        f"URL........: {data.get('webpage_url', '')}",
        f"ID.........: {data.get('id', '')}",
        f"Autor......: {data.get('uploader', '')} (@{data.get('uploader_id', '')})",
        f"Duracao....: {data.get('duration', '')} s",
        f"Curtidas...: {data.get('like_count', 'n/d')}",
        f"Views......: {data.get('view_count', 'n/d')}",
        f"Data.......: {data.get('upload_date', 'n/d')}",
        "",
        "LEGENDA / DESCRICAO:",
        descricao or "(sem legenda)",
        "",
        "HASHTAGS:",
        " ".join(hashtags) if hashtags else "(nenhuma)",
    ]
    out = info_json.with_suffix("").with_suffix(".txt")
    out.write_text("\n".join(linhas), encoding="utf-8")
    print(f"[ok] Resumo salvo em: {out}")
    return out


def transcrever(saida: Path, info_json: Path) -> None:
    try:
        import whisper  # type: ignore
    except ImportError:
        print("[!] --transcrever requer:  pip install -U openai-whisper")
        return
    audio = info_json.with_suffix("").with_suffix(".m4a")
    if not audio.exists():
        cand = list(saida.glob(f"{info_json.stem.split('.')[0]}*.m4a"))
        if not cand:
            print("[!] Audio .m4a nao encontrado para transcrever.")
            return
        audio = cand[0]
    print(f"[..] Transcrevendo {audio.name} (modelo 'small')...")
    model = whisper.load_model("small")
    result = model.transcribe(str(audio), language="pt")
    out = info_json.with_suffix("").with_suffix(".transcricao.txt")
    out.write_text(result["text"].strip(), encoding="utf-8")
    print(f"[ok] Transcricao salva em: {out}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Baixa e analisa um Reel do Instagram.")
    ap.add_argument("url", help="URL do reel, ex: https://www.instagram.com/reel/XXXX/")
    ap.add_argument("--browser", default="chrome",
                    choices=["chrome", "firefox", "edge", "brave", "chromium", "opera", "vivaldi", "safari"],
                    help="Navegador de onde ler os cookies de sessao (padrao: chrome).")
    ap.add_argument("--cookies-file", help="Caminho para cookies.txt (alternativa a --browser).")
    ap.add_argument("--saida", default="reels_baixados", help="Pasta de saida.")
    ap.add_argument("--transcrever", action="store_true", help="Transcrever o audio (requer openai-whisper).")
    args = ap.parse_args()

    if not yt_dlp_disponivel():
        print("[!] yt-dlp nao encontrado. Instale com:  pip install -U yt-dlp")
        return 1

    saida = Path(args.saida)
    auth = montar_auth_args(args)
    print(f"[..] Baixando {args.url}")
    info_json = baixar(args.url, saida, auth)
    if not info_json:
        return 2

    resumir_metadados(info_json)
    if args.transcrever:
        transcrever(saida, info_json)

    print("\n[ok] Pronto. Compare os arquivos gerados com ROTEIRO-REELS.md e reels-animacao.html.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
