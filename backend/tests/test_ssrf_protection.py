import pytest
from fastapi import HTTPException

from backend.utils.media_processor import validate_external_image_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/secret.jpg",
        "http://localhost/secret.jpg",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata endpoint
        "http://10.0.0.5/internal.jpg",       # RFC1918 private
        "http://192.168.1.10/internal.jpg",   # RFC1918 private
        "http://172.16.0.1/internal.jpg",     # RFC1918 private
    ],
)
def test_rejects_internal_and_private_targets(url):
    with pytest.raises(HTTPException) as exc_info:
        validate_external_image_url(url)
    assert exc_info.value.status_code == 400


def test_rejects_unresolvable_host(monkeypatch):
    import socket
    from backend.utils import media_processor

    def raise_gaierror(host, port):
        raise socket.gaierror("Name or service not known")

    monkeypatch.setattr(media_processor.socket, "getaddrinfo", raise_gaierror)

    with pytest.raises(HTTPException) as exc_info:
        validate_external_image_url("http://this-host-should-not-exist.invalid/image.jpg")
    assert exc_info.value.status_code == 400


def test_rejects_non_http_scheme():
    with pytest.raises(HTTPException) as exc_info:
        validate_external_image_url("javascript:alert(1)")
    assert exc_info.value.status_code == 400


def test_allows_valid_public_url_through_host_check(monkeypatch):
    """A legitimate public hostname must pass the SSRF host check itself
    (the DNS resolution + IP-range check), even though we don't want this
    unit test to depend on actually reaching the network for the rest of
    the pipeline (MIME/content validation)."""
    from backend.utils import media_processor

    # A public IP (documentation/example range is fine here — TEST-NET-1,
    # 192.0.2.0/24, is globally routable-shaped but reserved for docs, so it
    # is NOT loopback/private/link-local and must pass the host check).
    monkeypatch.setattr(
        media_processor.socket,
        "getaddrinfo",
        lambda host, port: [(2, 1, 6, "", ("93.184.216.34", 0))],
    )
    # Should not raise from the host-safety check itself.
    media_processor._assert_safe_external_host("example.com")
