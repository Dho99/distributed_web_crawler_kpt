"""URL normalization, scope checks and SSRF-adjacent safety checks.

Kept dependency-free so both master and worker can import it.
"""

from __future__ import annotations

import hashlib
import ipaddress
import re
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlsplit, urlunsplit

TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "gclsrc",
    "dclid",
    "msclkid",
    "yclid",
    "mc_cid",
    "mc_eid",
    "_hsenc",
    "_hsmi",
    "igshid",
    "ref",
    "ref_src",
}

TRACKING_PREFIXES = ("utm_",)

DEFAULT_PORTS = {"http": 80, "https": 443}

BAD_HOSTS = {"localhost", "localhost.localdomain", "ip6-localhost", "metadata.google.internal"}

UNSAFE_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_SLASHES = re.compile(r"/{2,}")
_WHITESPACE = re.compile(r"[\r\n\t]+")


def _clean_query(query: str) -> str:
    if not query:
        return ""
    pairs = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in TRACKING_PARAMS or lowered.startswith(TRACKING_PREFIXES):
            continue
        pairs.append((key, value))
    pairs.sort(key=lambda kv: (kv[0], kv[1]))
    return urlencode(pairs, doseq=True)


def normalize_url(url: str, base: str | None = None) -> str | None:
    """Return a canonical absolute http(s) URL, or None if unusable."""
    if not url:
        return None
    url = _WHITESPACE.sub("", url.strip())
    if base:
        url = urljoin(base, url)
    if url.startswith(("mailto:", "tel:", "javascript:", "data:", "ftp:", "file:")):
        return None

    try:
        parts = urlsplit(url)
    except ValueError:
        return None

    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        return None
    if not parts.hostname:
        return None

    host = parts.hostname.lower()
    try:
        host_ascii = host.encode("idna").decode("ascii")
    except UnicodeError:
        return None

    port = parts.port
    netloc = host_ascii
    if port and port != DEFAULT_PORTS[scheme]:
        netloc = f"{host_ascii}:{port}"

    path = parts.path or "/"
    path = _SLASHES.sub("/", path)
    path = quote(unquote(path), safe="/:@!$&'()*+,;=-._~%")

    query = _clean_query(parts.query)
    return urlunsplit((scheme, netloc, path, query, ""))


def url_hash(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def domain_of(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def _matches_domain(host: str, allowed: str, include_subdomains: bool) -> bool:
    allowed = allowed.lower().lstrip(".")
    if host == allowed:
        return True
    if include_subdomains and host.endswith("." + allowed):
        return True
    return False


def in_scope(url: str, allowed_domains: list[str], include_subdomains: bool = False) -> bool:
    if not allowed_domains:
        return True
    host = domain_of(url)
    if not host:
        return False
    return any(_matches_domain(host, d, include_subdomains) for d in allowed_domains)


def is_safe_public_url(url: str) -> bool:
    """Reject literal private/loopback/link-local targets (SSRF guard)."""
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return False
    if not host:
        return False
    if host in BAD_HOSTS or host.endswith(".local") or host.endswith(".internal"):
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Hostname: literal-IP check is not enough, fetch layer must re-check
        # resolved addresses. Hostnames are allowed here.
        return True
    return not any(ip in network for network in UNSAFE_NETWORKS)
