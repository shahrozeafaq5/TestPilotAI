import pytest

from app.services.url_security import (
    UnsafeURLError,
    URLSecurityPolicy,
)


def test_allows_public_http_url():
    policy = URLSecurityPolicy()

    result = policy.validate(
        "https://8.8.8.8/example"
    )

    assert result == "https://8.8.8.8/example"


def test_rejects_loopback_address():
    policy = URLSecurityPolicy(
        allow_local_urls=False
    )

    with pytest.raises(
        UnsafeURLError
    ):
        policy.validate(
            "http://127.0.0.1:8000"
        )


def test_rejects_private_address():
    policy = URLSecurityPolicy(
        allow_local_urls=False
    )

    with pytest.raises(
        UnsafeURLError
    ):
        policy.validate(
            "http://192.168.1.10"
        )


def test_allows_local_address_when_enabled():
    policy = URLSecurityPolicy(
        allow_local_urls=True
    )

    result = policy.validate(
        "http://127.0.0.1:3000"
    )

    assert result == (
        "http://127.0.0.1:3000"
    )


def test_rejects_file_url_by_default():
    policy = URLSecurityPolicy(
        allow_file_urls=False
    )

    with pytest.raises(
        UnsafeURLError
    ):
        policy.validate(
            "file:///C:/example.html"
        )


def test_allows_file_url_when_enabled():
    policy = URLSecurityPolicy(
        allow_file_urls=True
    )

    result = policy.validate(
        "file:///C:/example.html"
    )

    assert result == (
        "file:///C:/example.html"
    )


def test_rejects_embedded_credentials():
    policy = URLSecurityPolicy()

    with pytest.raises(
        UnsafeURLError
    ):
        policy.validate(
            "https://admin:password@8.8.8.8"
        )


def test_rejects_unsupported_scheme():
    policy = URLSecurityPolicy()

    with pytest.raises(
        UnsafeURLError
    ):
        policy.validate(
            "ftp://8.8.8.8/file"
        )