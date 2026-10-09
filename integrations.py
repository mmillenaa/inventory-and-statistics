"""Consultas externas paginadas, com limite de tempo e falhas explícitas."""
import pandas as pd
import requests


def search_dataverse(url, query, token=""):
    headers = {"X-Dataverse-key": token} if token else {}
    start, items = 0, []
    while True:
        response = requests.get(url, headers=headers, params={"q":query, "type":"dataset", "per_page":100, "start":start}, timeout=15)
        response.raise_for_status()
        data = response.json()["data"]
        page = data.get("items", [])
        if not page:
            break
        items.extend(page)
        start += len(page)
        if start >= data.get("total_count", start):
            break
    return items


def author_publications(tokens, authors):
    unique, errors = {}, []
    tokens = [tokens] if isinstance(tokens, str) else tokens
    def keep(items):
        for item in items:
            identifier = item.get("global_id")
            if identifier:
                author = item.get("authors", [])
                unique[identifier] = {"Título da base":item.get("name", "[sem título]"), "Autores":"; ".join(author) if isinstance(author,list) else str(author), "Identificador":identifier, "Link de acesso":item.get("url", "")}
    for author in authors:
        for token in dict.fromkeys(tokens or [""]):
            try:
                keep(search_dataverse("https://dataverse.fgv.br/api/search", f'"{author}"', token))
            except (requests.RequestException, ValueError, KeyError):
                errors.append(f"FGV: consulta indisponível para {author}.")
        parts = author.split(", ")
        inverted = f"{parts[1]} {parts[0]}" if len(parts)==2 else author
        for query in dict.fromkeys((f'"{author}"', f'"{inverted}"', f'author:"{author}"', f'author:"{inverted}"', author, inverted)):
            try:
                items = search_dataverse("https://data.scielo.org/api/search", query)
                keep(items)
                if items:
                    break
            except (requests.RequestException, ValueError, KeyError):
                errors.append(f"SciELO: consulta indisponível para {author}.")
                break
    frame = pd.DataFrame(list(unique.values()))
    frame.attrs["errors"] = list(dict.fromkeys(errors))
    return frame
