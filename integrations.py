"""Consultas públicas automáticas, paginadas, com cópia da última atualização."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re

import pandas as pd
import requests

from data_logic import normalize

LOGGER = logging.getLogger(__name__)
REPOSITORIES = {"FGV": "https://dataverse.fgv.br/api/search",
                "SciELO": "https://data.scielo.org/api/search"}
COLUMNS = ["Título da base", "Autores", "Identificador", "Link de acesso"]
CACHE_PATH = Path(__file__).resolve().parent / ".cache" / "observatorio.json"
SNAPSHOT_PATH = Path(__file__).resolve().parent / "publicacoes_dataverse.json"


def search_dataverse(url, query, token=""):
    headers = {"X-Dataverse-key": token} if token else {}
    start, items = 0, []
    while True:
        response = requests.get(url, headers=headers,
                                params={"q": query, "type": "dataset", "per_page": 100,
                                        "start": start, "fq": "publicationStatus:Published"},
                                timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status", "OK") != "OK" or not isinstance(payload.get("data"), dict):
            raise ValueError("Resposta inválida da API Dataverse")
        data = payload["data"]
        page = data.get("items", [])
        if not isinstance(page, list):
            raise ValueError("Lista inválida na resposta Dataverse")
        if not page:
            break
        items.extend(page)
        start += len(page)
        if start >= data.get("total_count", start):
            break
    return items


def _author_tokens(name):
    return set(re.findall(r"[a-z0-9]+", normalize(name)))


def _belongs_to_team(item, authors):
    names = item.get("authors", [])
    names = names if isinstance(names, list) else [names]
    return any(_author_tokens(wanted) and _author_tokens(wanted) <= _author_tokens(name)
               for wanted in authors for name in names)


def _records(items, authors):
    records = {}
    for item in items:
        identifier = item.get("global_id")
        if not identifier or not _belongs_to_team(item, authors):
            continue
        names = item.get("authors", [])
        records[identifier] = {"Título da base": item.get("name", "[sem título]"),
                               "Autores": "; ".join(names) if isinstance(names, list) else str(names),
                               "Identificador": identifier, "Link de acesso": item.get("url", "")}
    return list(records.values())


def _query(authors):
    names = []
    for author in authors:
        parts = author.split(", ")
        names.extend([author, f"{parts[1]} {parts[0]}" if len(parts) == 2 else author])
    return " OR ".join("authorName:" + json.dumps(name, ensure_ascii=False) for name in dict.fromkeys(names))


def _load_snapshot(path):
    try:
        data = json.loads(Path(path).read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def author_publications(tokens, authors, cache_path=None):
    # Somente publicações públicas: tokens expirados não devem bloquear a listagem.
    # As chaves permanecem nos segredos para outras operações da instituição.
    path = Path(cache_path) if cache_path is not None else CACHE_PATH
    previous = _load_snapshot(SNAPSHOT_PATH)
    previous.update(_load_snapshot(path))
    query = _query(authors)
    if not query:
        return pd.DataFrame(columns=COLUMNS)
    snapshots, issues = {}, {}
    def fetch(repository):
        try:
            records = _records(search_dataverse(REPOSITORIES[repository], query), authors)
            return repository, {"records": records, "updated_at": datetime.now(timezone.utc).isoformat()}, None
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            reason = f"HTTP {status}" if status else type(error).__name__
            LOGGER.warning("Observatório: %s — %s", repository, reason)
            return repository, previous.get(repository, {}), reason
    with ThreadPoolExecutor(max_workers=2) as executor:
        for repository, snapshot, reason in executor.map(fetch, REPOSITORIES):
            snapshots[repository] = snapshot
            if reason:
                issues[repository] = reason
    if any(repository not in issues for repository in REPOSITORIES):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(snapshots, ensure_ascii=False, indent=2))
            temporary.replace(path)
        except OSError:
            LOGGER.warning("Observatório: não foi possível salvar a última atualização.")
    unique = {}
    for snapshot in snapshots.values():
        for record in snapshot.get("records", []):
            # A cópia local também respeita a lista atual de pesquisadoras.
            names = record.get("Autores", "").split("; ")
            if _belongs_to_team({"authors": names}, authors):
                unique[record["Identificador"]] = record
    frame = pd.DataFrame(list(unique.values()), columns=COLUMNS)
    frame.attrs["diagnostics"] = issues
    frame.attrs["updates"] = {repository: snapshot.get("updated_at", "")
                              for repository, snapshot in snapshots.items()}
    if issues:
        stored = [repository for repository in issues if snapshots[repository].get("records")]
        if stored:
            frame.attrs["notice"] = "Atualização automática temporariamente indisponível em " + ", ".join(issues) + ". Mantida a última listagem disponível."
        else:
            frame.attrs["notice"] = "Atualização automática temporariamente indisponível em " + ", ".join(issues) + ". As demais publicações disponíveis continuam abaixo."
    return frame
