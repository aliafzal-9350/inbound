"""Validation for URLs that businesses give us to call (alert webhooks).

The server POSTs to these URLs, so a business must not be able to point them at our own
infrastructure (Redis, the API, the cloud metadata service at 169.254.169.254, private networks).
Checked when saved and again right before each call (DNS can change in between).
"""
import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse


def public_https_url_error(url: str) -> Optional[str]:
    """Returns why the URL is unacceptable, or None if it's a public https URL."""
    try:
        parsed = urlparse((url or "").strip())
    except ValueError:
        return "That doesn't look like a valid URL."
    if parsed.scheme != "https" or not parsed.hostname:
        return "The webhook URL must start with https://"
    if parsed.username or parsed.password:
        return "The webhook URL must not contain a username or password."
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return "That webhook address could not be found."
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global or ip.is_multicast:
            return "The webhook URL must point to a public internet address."
    return None
