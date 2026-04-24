import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .api_helpers import serialize_catalog_game


CATALOG_BASE_URL = "https://www.cheapshark.com/api/1.0/games"
CATALOG_TIMEOUT_SECONDS = 5
CATALOG_MAX_IDS_PER_REQUEST = 25


class CatalogUnavailableError(Exception):
    pass


class CatalogResponseError(Exception):
    pass


def _normalize_external_game_id(value):
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and value:
        return value
    raise CatalogResponseError()


def _request_catalog_json(params):
    query = urlencode(params)
    request = Request(
        f"{CATALOG_BASE_URL}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "daw-dwes-catalog/1.0",
        },
    )

    try:
        with urlopen(request, timeout=CATALOG_TIMEOUT_SECONDS) as response:
            status_code = getattr(response, "status", response.getcode())
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise CatalogResponseError() from exc
    except TimeoutError as exc:
        raise CatalogUnavailableError() from exc
    except URLError as exc:
        if isinstance(exc.reason, socket.timeout):
            raise CatalogUnavailableError() from exc
        raise CatalogUnavailableError() from exc

    if status_code != 200:
        raise CatalogResponseError()

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise CatalogResponseError() from exc


def search_catalog_games(query):
    data = _request_catalog_json({"title": query})
    if not isinstance(data, list):
        raise CatalogResponseError()

    results = []
    for item in data:
        if not isinstance(item, dict):
            raise CatalogResponseError()
        external_game_id = _normalize_external_game_id(item.get("gameID"))
        title = item.get("external")
        thumb = item.get("thumb")
        if not isinstance(title, str) or not isinstance(thumb, str):
            raise CatalogResponseError()
        results.append(serialize_catalog_game(external_game_id, title, thumb))

    return results


def _extract_game_summary(external_game_id, raw_game):
    if not isinstance(raw_game, dict):
        raise CatalogResponseError()
    info = raw_game.get("info")
    if not isinstance(info, dict):
        raise CatalogResponseError()
    title = info.get("title")
    thumb = info.get("thumb")
    if not isinstance(title, str) or not isinstance(thumb, str):
        raise CatalogResponseError()
    return serialize_catalog_game(external_game_id, title, thumb)


def _chunked(values, size):
    for index in range(0, len(values), size):
        yield values[index : index + size]


def resolve_catalog_games(external_game_ids):
    results = []
    for batch in _chunked(external_game_ids, CATALOG_MAX_IDS_PER_REQUEST):
        data = _request_catalog_json({"ids": ",".join(batch)})
        if not isinstance(data, dict):
            raise CatalogResponseError()
        for external_game_id in batch:
            raw_game = data.get(external_game_id)
            if raw_game is None:
                continue
            results.append(_extract_game_summary(external_game_id, raw_game))
    return results


def catalog_game_exists(external_game_id):
    resolved = resolve_catalog_games([external_game_id])
    return bool(resolved)
