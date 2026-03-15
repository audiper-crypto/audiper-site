#!/usr/bin/env python
"""
work_manager.py — Gerenciador central de trabalhos do sistema Audiper.

Cada trabalho realizado pelos agentes (auditoria, perícia, consultoria,
design, dev, marketing) é salvo na pasta correta automaticamente.

Estrutura:
  agents/work/
    auditoria/
      clientes/<CNPJ>_<empresa>/
        <YYYY-MM>/
          PTA-A_aceite.json
          PTA-B_planejamento.json
          ...
          _meta.json              ← índice do trabalho
      templates/                  ← modelos reutilizáveis
      normas/                     ← NBCs (base RAG AUDIZ)
    pericia/
      processos/<numero>/
        laudo.md
        quesitos.json
        _meta.json
      jurisprudencia/             ← base RAG IUDEX
    consultoria/
      projetos/<empresa>_<slug>/
        proposta.html
        diagnostico.json
        relatorio_final.md
        _meta.json
    design/
      clientes/<empresa>/
        briefing.json
        assets/
        _meta.json
    dev/
      projetos/<nome>/
        spec.md
        _meta.json
    marketing/
      campanhas/<nome>/
        _meta.json
    _inbox/                       ← trabalhos recebidos aguardando classificação

Uso:
  # Salvar um output de trabalho
  from scripts.work_manager import WorkManager
  wm = WorkManager()
  path = wm.save("auditoria", cnpj="12345678000199", empresa="ABC LTDA",
                 filename="PTA-A_aceite.json", content={...}, agent="audiz-senior")

  # Buscar trabalhos de um cliente
  works = wm.find(work_type="auditoria", query="ABC LTDA")

  # CLI
  python work_manager.py --list auditoria
  python work_manager.py --inbox      # lista _inbox para classificação
  python work_manager.py --classify   # classifica _inbox automaticamente
"""
import argparse, json, os, re, shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORK_ROOT = Path("D:/Site/audiper/agents/work")

# ─── Tipos de trabalho e seus caminhos ────────────────────────────────────────
WORK_TYPES = {
    "auditoria":   WORK_ROOT / "auditoria",
    "pericia":     WORK_ROOT / "pericia",
    "consultoria": WORK_ROOT / "consultoria",
    "design":      WORK_ROOT / "design",
    "dev":         WORK_ROOT / "dev",
    "marketing":   WORK_ROOT / "marketing",
}

# Palavras-chave para classificação automática dos agentes
CLASSIFIER_KEYWORDS = {
    "auditoria":   ["auditoria", "nbc", "pta", "sped", "balanço", "balancete",
                    "cnpj", "cliente", "empresa", "eqcr", "achado", "evidência"],
    "pericia":     ["perícia", "laudo", "quesito", "processo", "judicial",
                    "trabalhista", "cálculo forense", "assistente técnico"],
    "consultoria": ["consultoria", "diagnóstico", "proposta", "relatório",
                    "planejamento tributário", "reorganização"],
    "design":      ["design", "logo", "identidade visual", "banner", "site",
                    "landing", "ux", "ui", "wireframe"],
    "dev":         ["dev", "código", "backend", "frontend", "api", "endpoint",
                    "deploy", "docker", "python", "javascript"],
    "marketing":   ["marketing", "campanha", "seo", "conteúdo", "post",
                    "anúncio", "email marketing", "crm"],
}


class WorkManager:
    """Gerenciador central de trabalhos dos agentes Audiper."""

    def __init__(self, work_root: str = ""):
        self.root = Path(work_root) if work_root else WORK_ROOT
        self._ensure_structure()

    def _ensure_structure(self):
        for wt in WORK_TYPES:
            (self.root / wt).mkdir(parents=True, exist_ok=True)
        (self.root / "_inbox").mkdir(parents=True, exist_ok=True)

    # ─── Salvar trabalho ──────────────────────────────────────────────────────
    def save(
        self,
        work_type: str,
        filename: str,
        content,
        agent: str = "unknown",
        # Auditoria
        cnpj: str = "",
        empresa: str = "",
        periodo: str = "",
        # Perícia
        processo: str = "",
        # Consultoria / Design / Dev / Marketing
        projeto: str = "",
        cliente: str = "",
        # Metadados extras
        tags: list = None,
        description: str = "",
    ) -> Path:
        """
        Salva um arquivo de trabalho na pasta correta e atualiza _meta.json.
        Retorna o Path do arquivo salvo.
        """
        if work_type not in WORK_TYPES and work_type != "_inbox":
            raise ValueError(f"work_type inválido: {work_type}. Use: {list(WORK_TYPES.keys())}")

        # Determina subpasta de destino
        dest_dir = self._resolve_dest(work_type, cnpj=cnpj, empresa=empresa,
                                      periodo=periodo, processo=processo,
                                      projeto=projeto, cliente=cliente)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / filename

        # Serializa conteúdo
        if isinstance(content, (dict, list)):
            with open(dest_file, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        elif isinstance(content, str):
            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(content)
        elif isinstance(content, bytes):
            with open(dest_file, "wb") as f:
                f.write(content)
        else:
            raise TypeError(f"content deve ser dict, list, str ou bytes. Recebido: {type(content)}")

        # Atualiza _meta.json
        self._update_meta(dest_dir, {
            "work_type":   work_type,
            "filename":    filename,
            "agent":       agent,
            "saved_at":    datetime.now(timezone.utc).isoformat(),
            "tags":        tags or [],
            "description": description,
            "path":        str(dest_file.relative_to(self.root)),
        })

        print(f"[WORK] Salvo: {dest_file.relative_to(self.root)}")
        return dest_file

    def _resolve_dest(self, work_type: str, **kwargs) -> Path:
        """Resolve a subpasta de destino conforme o tipo de trabalho e parâmetros."""
        base = self.root / work_type if work_type in WORK_TYPES else self.root / "_inbox"

        if work_type == "auditoria":
            cnpj    = _slug(kwargs.get("cnpj", ""))
            empresa = _slug(kwargs.get("empresa", "desconhecido"))
            periodo = kwargs.get("periodo", "") or datetime.now().strftime("%Y-%m")
            folder  = f"{cnpj}_{empresa}" if cnpj else empresa
            return base / "clientes" / folder / periodo

        elif work_type == "pericia":
            numero = _slug(kwargs.get("processo", "sem-numero"))
            return base / "processos" / numero

        elif work_type in ("consultoria", "design", "dev", "marketing"):
            key     = _slug(kwargs.get("projeto", "") or kwargs.get("cliente", ""))
            subdir  = "projetos" if work_type in ("consultoria", "dev") else "clientes"
            if work_type == "marketing":
                subdir = "campanhas"
            return base / subdir / (key or "sem-nome")

        return base / "_inbox"

    def _update_meta(self, dest_dir: Path, entry: dict):
        meta_file = dest_dir / "_meta.json"
        if meta_file.exists():
            with open(meta_file, encoding="utf-8") as f:
                meta = json.load(f)
        else:
            meta = {"created_at": datetime.now(timezone.utc).isoformat(), "files": []}
        meta["files"].append(entry)
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    # ─── Busca ────────────────────────────────────────────────────────────────
    def find(self, work_type: str = "", query: str = "") -> list:
        """
        Busca trabalhos. Retorna lista de dicts com path, work_type, meta.
        - work_type: filtra por tipo ("auditoria", "dev", etc.)
        - query: busca por nome de pasta ou descrição (case-insensitive)
        """
        results = []
        search_roots = []

        if work_type and work_type in WORK_TYPES:
            search_roots = [self.root / work_type]
        else:
            search_roots = [self.root / wt for wt in WORK_TYPES]

        for sr in search_roots:
            for meta_file in sr.rglob("_meta.json"):
                try:
                    with open(meta_file, encoding="utf-8") as f:
                        meta = json.load(f)
                    folder_name = meta_file.parent.name
                    if not query or query.lower() in folder_name.lower() or \
                       any(query.lower() in str(f).lower() for f in meta.get("files", [])):
                        results.append({
                            "path":      str(meta_file.parent.relative_to(self.root)),
                            "work_type": meta_file.parts[len(self.root.parts)],
                            "files":     len(meta.get("files", [])),
                            "updated":   meta.get("updated_at", "")[:10],
                        })
                except (json.JSONDecodeError, KeyError):
                    pass
        return sorted(results, key=lambda x: x.get("updated", ""), reverse=True)

    def list_client(self, cnpj: str = "", empresa: str = "") -> list:
        """Lista todos os trabalhos de um cliente (qualquer tipo)."""
        query = cnpj or empresa
        all_results = []
        for wt in WORK_TYPES:
            all_results.extend(self.find(wt, query))
        return all_results

    # ─── Inbox e classificação automática ────────────────────────────────────
    def inbox_list(self) -> list:
        """Lista arquivos no _inbox aguardando classificação."""
        inbox = self.root / "_inbox"
        return [f.name for f in inbox.iterdir() if f.is_file() and f.name != "_meta.json"]

    def classify_inbox(self, dry_run: bool = False) -> list:
        """
        Classifica automaticamente arquivos do _inbox com base em keywords.
        Retorna lista de movimentações realizadas.
        """
        inbox = self.root / "_inbox"
        moves = []

        for fpath in inbox.iterdir():
            if not fpath.is_file() or fpath.name.startswith("_"):
                continue

            # Tenta ler conteúdo para classificar
            try:
                text = fpath.read_text(encoding="utf-8").lower()
            except Exception:
                text = fpath.name.lower()

            work_type = _classify_text(fpath.name + " " + text)
            if not work_type:
                work_type = "consultoria"  # fallback

            dest_dir = self.root / work_type / "_classificado"
            if not dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(fpath), str(dest_dir / fpath.name))

            moves.append({"file": fpath.name, "work_type": work_type, "dry_run": dry_run})
            print(f"[CLASSIFY] {fpath.name} → {work_type}{'  (dry-run)' if dry_run else ''}")

        return moves

    # ─── Índice global ────────────────────────────────────────────────────────
    def build_global_index(self) -> dict:
        """Constrói índice global de todos os trabalhos."""
        index = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "totals":       {},
            "recent":       [],
            "by_type":      {},
        }
        all_items = []
        for wt in WORK_TYPES:
            items = self.find(wt)
            index["totals"][wt] = len(items)
            index["by_type"][wt] = items[:10]  # top 10 mais recentes por tipo
            all_items.extend(items)

        index["recent"] = sorted(all_items, key=lambda x: x.get("updated", ""), reverse=True)[:20]

        out = self.root / "work_index.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"[INDEX] {out} — {sum(index['totals'].values())} trabalhos indexados")
        return index


# ─── Utils ────────────────────────────────────────────────────────────────────
def _slug(text: str) -> str:
    """Converte texto em slug de pasta seguro."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text[:40]


def _classify_text(text: str) -> Optional[str]:
    """Classifica texto por keywords — retorna work_type ou None."""
    text = text.lower()
    scores = {wt: 0 for wt in CLASSIFIER_KEYWORDS}
    for wt, keywords in CLASSIFIER_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[wt] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Gerenciador de trabalhos Audiper")
    parser.add_argument("--list",     metavar="WORK_TYPE", help="Lista trabalhos de um tipo")
    parser.add_argument("--find",     metavar="QUERY",     help="Busca por nome/cliente")
    parser.add_argument("--inbox",    action="store_true", help="Lista _inbox")
    parser.add_argument("--classify", action="store_true", help="Classifica _inbox")
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--index",    action="store_true", help="Reconstrói índice global")
    args = parser.parse_args()

    wm = WorkManager()

    if args.list:
        items = wm.find(args.list)
        if items:
            for item in items:
                print(f"  [{item['work_type']}] {item['path']} — {item['files']} arquivo(s) — {item['updated']}")
        else:
            print(f"Nenhum trabalho encontrado para '{args.list}'")

    elif args.find:
        items = wm.find(query=args.find)
        for item in items:
            print(f"  [{item['work_type']}] {item['path']} — {item['updated']}")

    elif args.inbox:
        files = wm.inbox_list()
        if files:
            print(f"_inbox ({len(files)} arquivo(s)):")
            for f in files:
                print(f"  {f}")
        else:
            print("_inbox vazio")

    elif args.classify:
        moves = wm.classify_inbox(args.dry_run)
        print(f"\n{len(moves)} arquivo(s) classificado(s)")

    elif args.index:
        wm.build_global_index()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
