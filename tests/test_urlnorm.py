from shared.urlnorm import (
    domain_of,
    in_scope,
    is_safe_public_url,
    normalize_url,
    url_hash,
)


def test_normalize_strips_fragment_and_tracking():
    url = normalize_url("HTTPS://Example.COM:443/a//b/?utm_source=x&b=2&a=1#frag")
    assert url == "https://example.com/a/b/?a=1&b=2"


def test_normalize_preserves_trailing_slash():
    assert normalize_url("https://example.com/bench/") == "https://example.com/bench/"
    assert normalize_url("https://example.com/docs/") == "https://example.com/docs/"


def test_normalize_keeps_path_case():
    assert normalize_url("https://example.com/Docs/Page") == "https://example.com/Docs/Page"


def test_normalize_rejects_non_http():
    assert normalize_url("mailto:a@b.c") is None
    assert normalize_url("javascript:alert(1)") is None
    assert normalize_url("") is None


def test_normalize_relative_with_base():
    assert normalize_url("../x?y=1", "https://example.com/a/b/") == "https://example.com/a/x?y=1"


def test_url_hash_is_stable_and_distinct():
    a = url_hash("https://example.com/")
    assert a == url_hash("https://example.com/")
    assert a != url_hash("https://example.com/other")


def test_scope_exact_domain():
    assert in_scope("https://example.com/a", ["example.com"])
    assert not in_scope("https://sub.example.com/a", ["example.com"])
    assert in_scope("https://sub.example.com/a", ["example.com"], include_subdomains=True)


def test_domain_of():
    assert domain_of("https://Sub.Example.com/x") == "sub.example.com"


def test_private_targets_blocked():
    assert not is_safe_public_url("http://127.0.0.1/")
    assert not is_safe_public_url("http://192.168.1.10/")
    assert not is_safe_public_url("http://169.254.169.254/latest/meta-data")
    assert not is_safe_public_url("http://localhost:8000/")
    assert is_safe_public_url("https://example.com/")
