"""T2-07: Release version detection tests."""

from jobclass.extract.version_detect import detect_version, detect_version_from_content_header, detect_version_from_url


class TestUrlVersionDetection:
    def test_oews_url_pattern(self):
        assert detect_version_from_url("https://bls.gov/oes/special-requests/oesm2024_nat.zip") == "2024.05"

    def test_onet_db_version(self):
        assert detect_version_from_url("https://onetcenter.org/dl_files/database/db_29_1_text/Skills.txt") == "29.1"

    def test_soc_year(self):
        assert detect_version_from_url("https://bls.gov/soc/2018/soc_2018_direct_match_title_file.csv") == "2018"

    def test_generic_year_in_filename(self):
        result = detect_version_from_url("https://example.com/data_2023.csv")
        assert result == "2023"

    def test_no_version_found(self):
        assert detect_version_from_url("https://example.com/noversion") is None


class TestContentHeaderDetection:
    def test_version_keyword(self):
        content = "Header line\nVersion 3.5\nData starts here"
        assert detect_version_from_content_header(content) == "3.5"

    def test_soc_keyword(self):
        content = "SOC 2018 Classification\ncode,title"
        assert detect_version_from_content_header(content) == "2018"

    def test_no_version_in_content(self):
        content = "just,some,csv,data\n1,2,3,4"
        assert detect_version_from_content_header(content) is None


class TestDetectVersionStrategy:
    def test_url_pattern_strategy(self):
        assert (
            detect_version(
                "https://bls.gov/oes/special-requests/oesm2024_nat.zip",
                strategy="url_pattern",
            )
            == "2024.05"
        )

    def test_content_header_strategy_with_content(self):
        result = detect_version(
            "https://example.com/data.csv",
            content="SOC 2018 Classification\ncode,title",
            strategy="content_header",
        )
        assert result == "2018"

    def test_content_header_falls_back_to_url(self):
        result = detect_version(
            "https://bls.gov/soc/2018/file.csv",
            content="no version here",
            strategy="content_header",
        )
        assert result == "2018"
