"""Release version detection from source metadata or URL patterns."""

import re


def detect_version_from_url(url: str) -> str | None:
    """Extract version-like patterns from URL.

    Looks for patterns like: oesm2024, db_29_1, 2018, etc.
    """
    # OEWS year pattern: oesm{YYYY}
    match = re.search(r"oesm(\d{4})", url)
    if match:
        return f"{match.group(1)}.05"  # OEWS is May reference period

    # O*NET database version: db_{major}_{minor}
    match = re.search(r"db_(\d+)_(\d+)", url)
    if match:
        return f"{match.group(1)}.{match.group(2)}"

    # SOC year: /soc/{YYYY}/
    match = re.search(r"/soc/(\d{4})/", url)
    if match:
        return match.group(1)

    # Generic year in filename
    match = re.search(r"(\d{4})", url.split("/")[-1])
    if match:
        return match.group(1)

    return None


def detect_version_from_content_header(content: str) -> str | None:
    """Extract version from file content header lines.

    Looks for version patterns in the first few lines.
    """
    for line in content.split("\n")[:10]:
        # "Version X.Y" or "Release X.Y"
        match = re.search(r"(?:version|release)\s+(\d+[\.\d]*)", line, re.IGNORECASE)
        if match:
            return match.group(1)
        # "SOC 2018" or "OEWS 2024"
        match = re.search(r"(?:SOC|OEWS|O\*NET)\s+(\d{4})", line, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def detect_version(url: str, content: str | None = None, strategy: str = "url_pattern") -> str | None:
    """Detect source release version using the specified strategy."""
    if strategy == "url_pattern":
        return detect_version_from_url(url)
    elif strategy == "content_header":
        if content:
            result = detect_version_from_content_header(content)
            if result:
                return result
        return detect_version_from_url(url)
    else:
        return detect_version_from_url(url)
