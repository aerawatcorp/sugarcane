import humanize

from datetime import datetime
from sugarlib.redis_helpers import r_master_etag
from urllib import parse


def humanize_delta(date_value):
    return humanize.precisedelta(
        datetime.now() - datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S.%f"),
        minimum_unit="seconds",
    )


def etag_master(updated_on):
    _etag = updated_on.replace(" ", "").replace(":", "").replace("-", "")
    return f"MASTER.{_etag}"


def etag_node(node_name, version):
    return f"NODE.{node_name.upper()}.{version}"


def master_etag_verification(request, conn):
    etag = request.headers.get("If-None-Match")
    if etag:
        stored_etag = r_master_etag(conn)
        return stored_etag == etag
    return None


def get_expires_on_ttl(expires_datetime):
    ttl = (
        datetime.strptime(expires_datetime, "%Y-%m-%d %H:%M:%S.%f") - datetime.now()
    ).total_seconds()
    if ttl < 0:
        return False
    return int(ttl)


def build_url(url: str, relative_url: str = "", query_params: dict = {}) -> str:
    """Build absolute url
    Args:
            url: URL path
            relative_url: Relative URL path
            query_params (dict): Query params for the url. Defaults to {}
    """
    parsed_url = parse.urlparse(url)
    parsed_query = parse.parse_qs(parsed_url.query)
    query_params.update(parsed_query)
    url = parsed_url.scheme + "://" + parsed_url.netloc

    absoulte_url = parse.urljoin(url, relative_url)
    if query_params:
        absoulte_url = absoulte_url + "?" + parse.urlencode(query_params, doseq=True)
    return absoulte_url
