import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit


class UnsafeURLError(ValueError):
    """Raised when a submitted URL is not safe to access."""


@dataclass
class URLSecurityPolicy:
    allow_local_urls: bool = False
    allow_file_urls: bool = False

    def validate(self, url: str) -> str:
        cleaned_url = url.strip()

        if not cleaned_url:
            raise UnsafeURLError(
                "The page URL cannot be empty."
            )

        parsed_url = urlsplit(cleaned_url)
        scheme = parsed_url.scheme.lower()

        if scheme == "file":
            return self._validate_file_url(
                cleaned_url
            )

        if scheme not in {"http", "https"}:
            raise UnsafeURLError(
                "Only http and https URLs are allowed."
            )

        if (
            parsed_url.username is not None
            or parsed_url.password is not None
        ):
            raise UnsafeURLError(
                "URLs containing embedded credentials "
                "are not allowed."
            )

        hostname = parsed_url.hostname

        if not hostname:
            raise UnsafeURLError(
                "The URL must contain a hostname."
            )

        self._validate_hostname(
            hostname=hostname,
            port=parsed_url.port,
        )

        return cleaned_url

    def _validate_file_url(
        self,
        url: str,
    ) -> str:
        if not self.allow_file_urls:
            raise UnsafeURLError(
                "File URLs are disabled."
            )

        return url

    def _validate_hostname(
        self,
        hostname: str,
        port: int | None,
    ) -> None:
        normalized_hostname = hostname.lower()

        if (
            normalized_hostname == "localhost"
            or normalized_hostname.endswith(
                ".localhost"
            )
        ):
            if not self.allow_local_urls:
                raise UnsafeURLError(
                    "Localhost URLs are disabled."
                )

            return

        try:
            direct_ip = ipaddress.ip_address(
                normalized_hostname
            )

        except ValueError:
            resolved_ips = self._resolve_hostname(
                hostname=hostname,
                port=port,
            )

        else:
            resolved_ips = [direct_ip]

        for resolved_ip in resolved_ips:
            if self._is_blocked_ip(resolved_ip):
                raise UnsafeURLError(
                    "The URL resolves to a private or "
                    "restricted network address."
                )

    def _resolve_hostname(
        self,
        hostname: str,
        port: int | None,
    ) -> list[
        ipaddress.IPv4Address
        | ipaddress.IPv6Address
    ]:
        try:
            address_info = socket.getaddrinfo(
                hostname,
                port or 443,
                type=socket.SOCK_STREAM,
            )

        except socket.gaierror as error:
            raise UnsafeURLError(
                "The URL hostname could not be resolved."
            ) from error

        resolved_ips = {
            ipaddress.ip_address(
                result[4][0]
            )
            for result in address_info
        }

        if not resolved_ips:
            raise UnsafeURLError(
                "The hostname did not resolve to "
                "an IP address."
            )

        return list(resolved_ips)

    def _is_blocked_ip(
        self,
        ip_address: (
            ipaddress.IPv4Address
            | ipaddress.IPv6Address
        ),
    ) -> bool:
        # These addresses should never be used as
        # browser testing destinations.
        if (
            ip_address.is_unspecified
            or ip_address.is_multicast
        ):
            return True

        if self.allow_local_urls:
            return False

        # is_global is False for private, loopback,
        # link-local and other special-use addresses.
        return not ip_address.is_global
        