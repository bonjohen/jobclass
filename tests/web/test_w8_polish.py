"""Phase W8 tests: Visual polish, responsive design, accessibility."""

import pytest


class TestAccessibility:
    """WT8-03, WT8-04: Semantic HTML and keyboard navigation."""

    def test_landing_has_landmarks(self, client):
        html = client.get("/").text
        assert 'role="banner"' in html
        assert 'role="main"' in html
        assert 'role="contentinfo"' in html

    def test_landing_has_skip_link(self, client):
        html = client.get("/").text
        assert "Skip to main content" in html
        assert 'href="#main-content"' in html

    def test_nav_has_aria_label(self, client):
        html = client.get("/").text
        assert 'aria-label="Main navigation"' in html

    def test_search_input_has_aria_label(self, client):
        html = client.get("/search").text
        assert 'aria-label=' in html

    def test_hierarchy_tree_has_role(self, client):
        html = client.get("/hierarchy").text
        assert 'role="tree"' in html

    def test_main_content_has_id(self, client):
        html = client.get("/").text
        assert 'id="main-content"' in html

    def test_html_lang_attribute(self, client):
        html = client.get("/").text
        assert 'lang="en"' in html

    def test_pages_have_viewport_meta(self, client):
        html = client.get("/").text
        assert 'name="viewport"' in html
        assert "width=device-width" in html


class TestVisualConsistency:
    """WT8-01: Consistent styling across pages."""

    def test_all_pages_include_css(self, client):
        pages = ["/", "/search", "/hierarchy", "/methodology"]
        for page in pages:
            html = client.get(page).text
            assert 'href="/static/css/main.css"' in html

    def test_all_pages_include_js(self, client):
        pages = ["/", "/search", "/hierarchy", "/methodology"]
        for page in pages:
            html = client.get(page).text
            assert 'src="/static/js/main.js"' in html

    def test_all_pages_have_header_footer(self, client):
        pages = ["/", "/search", "/hierarchy", "/methodology"]
        for page in pages:
            html = client.get(page).text
            assert "<header" in html
            assert "<footer" in html


class TestPerformance:
    """WT8-06: API response time check."""

    def test_health_responds_quickly(self, client):
        import time
        start = time.time()
        resp = client.get("/api/health")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 2.0, f"Health endpoint took {elapsed:.2f}s"

    def test_search_responds_quickly(self, client):
        import time
        start = time.time()
        resp = client.get("/api/occupations/search?q=Software")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 2.0, f"Search took {elapsed:.2f}s"

    def test_profile_responds_quickly(self, client):
        import time
        start = time.time()
        resp = client.get("/api/occupations/15-1252")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 2.0, f"Profile took {elapsed:.2f}s"
