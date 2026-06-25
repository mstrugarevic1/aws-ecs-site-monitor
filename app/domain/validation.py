import ipaddress
import os
from urllib.parse import urlparse

LOCALHOST_NAMES = {"localhost", "localhost.localdomain"}


def validate_target_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("url scheme must be http or https")
    if not parsed.hostname:
        raise ValueError("url must include a hostname")

    host = parsed.hostname.lower().rstrip(".")
    if host in LOCALHOST_NAMES:
        raise ValueError("localhost targets are not allowed")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return url

    if address.is_loopback:
        raise ValueError("loopback targets are not allowed")
    if address.is_link_local:
        raise ValueError("link-local targets are not allowed")
    if address.is_private and os.getenv("ALLOW_PRIVATE_TARGETS", "").lower() != "true":
        raise ValueError("private IP targets require ALLOW_PRIVATE_TARGETS=true")

    return url
