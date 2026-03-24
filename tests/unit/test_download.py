"""T2-01 through T2-04: Download module and checksum tests."""

import hashlib

from jobclass.extract.download import DownloadError, compute_checksum


class TestChecksum:
    """T2-04: SHA-256 checksum computation."""

    def test_known_digest(self):
        data = b"hello world"
        expected = hashlib.sha256(data).hexdigest()
        assert compute_checksum(data) == expected

    def test_empty_bytes(self):
        data = b""
        expected = hashlib.sha256(data).hexdigest()
        assert compute_checksum(data) == expected

    def test_binary_content(self):
        data = bytes(range(256))
        expected = hashlib.sha256(data).hexdigest()
        assert compute_checksum(data) == expected


class TestDownloadError:
    """T2-02: DownloadError carries URL and status code."""

    def test_error_has_url_and_status(self):
        err = DownloadError("https://example.com/file.csv", 404, "Not found")
        assert err.url == "https://example.com/file.csv"
        assert err.status_code == 404
        assert "Not found" in str(err)

    def test_error_with_none_status(self):
        err = DownloadError("https://example.com", None, "Timeout")
        assert err.status_code is None
