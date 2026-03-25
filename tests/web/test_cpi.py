"""CPI HTML page and navigation tests."""


class TestCPILanding:
    def test_cpi_returns_200(self, client):
        resp = client.get("/cpi")
        assert resp.status_code == 200

    def test_cpi_has_page_title(self, client):
        resp = client.get("/cpi")
        assert "Consumer Price Index" in resp.text

    def test_cpi_has_search(self, client):
        resp = client.get("/cpi")
        assert "cpi-member-search" in resp.text

    def test_cpi_has_hierarchy_tree(self, client):
        resp = client.get("/cpi")
        assert "cpi-hierarchy-tree" in resp.text

    def test_cpi_has_area_section(self, client):
        resp = client.get("/cpi")
        assert "Geographic Areas" in resp.text

    def test_cpi_has_cross_cutting_section(self, client):
        resp = client.get("/cpi")
        assert "Cross-Cutting Aggregates" in resp.text


class TestCPIMemberPage:
    def test_hierarchy_node_returns_200(self, client):
        resp = client.get("/cpi/member/SA0")
        assert resp.status_code == 200

    def test_cross_cutting_aggregate_returns_200(self, client):
        resp = client.get("/cpi/member/SA0L1E")
        assert resp.status_code == 200

    def test_member_page_has_data_attr(self, client):
        resp = client.get("/cpi/member/SA0")
        assert 'data-member-code="SA0"' in resp.text

    def test_member_page_has_series_section(self, client):
        resp = client.get("/cpi/member/SA0")
        assert "Index Series" in resp.text

    def test_member_page_has_importance_section(self, client):
        resp = client.get("/cpi/member/SA0")
        assert "importance-section" in resp.text

    def test_member_page_has_revisions_section(self, client):
        resp = client.get("/cpi/member/SA0")
        assert "revisions-section" in resp.text

    def test_member_page_has_avg_price_section(self, client):
        resp = client.get("/cpi/member/SA0")
        assert "avg-price-section" in resp.text

    def test_member_page_includes_js(self, client):
        resp = client.get("/cpi/member/SA0")
        assert "cpi_member.js" in resp.text

    def test_unknown_member_returns_200(self, client):
        """Page returns 200 — JS handles 404 from API."""
        resp = client.get("/cpi/member/ZZZZZ")
        assert resp.status_code == 200


class TestCPIAreaPage:
    def test_national_area_returns_200(self, client):
        resp = client.get("/cpi/area/0000")
        assert resp.status_code == 200

    def test_area_page_has_data_attr(self, client):
        resp = client.get("/cpi/area/0000")
        assert 'data-area-code="0000"' in resp.text

    def test_area_page_has_caveats_section(self, client):
        resp = client.get("/cpi/area/0000")
        assert "area-caveats" in resp.text

    def test_area_page_has_members_section(self, client):
        resp = client.get("/cpi/area/0000")
        assert "Published Members" in resp.text

    def test_area_page_has_filter(self, client):
        resp = client.get("/cpi/area/0000")
        assert "area-member-filter" in resp.text


class TestCPIExplorer:
    def test_explorer_returns_200(self, client):
        resp = client.get("/cpi/explorer")
        assert resp.status_code == 200

    def test_explorer_has_visualization_container(self, client):
        resp = client.get("/cpi/explorer")
        assert "explorer-viz" in resp.text

    def test_explorer_has_controls(self, client):
        resp = client.get("/cpi/explorer")
        assert "cpi-explorer-controls" in resp.text

    def test_explorer_includes_js(self, client):
        resp = client.get("/cpi/explorer")
        assert "cpi_explorer.js" in resp.text


class TestCPINavLink:
    def test_cpi_nav_link_on_home(self, client):
        resp = client.get("/")
        assert "/cpi" in resp.text

    def test_cpi_nav_link_on_search(self, client):
        resp = client.get("/search")
        assert "/cpi" in resp.text

    def test_cpi_nav_link_on_methodology(self, client):
        resp = client.get("/methodology")
        assert "/cpi" in resp.text


class TestCPIHierarchyNavigation:
    def test_member_page_has_breadcrumb(self, client):
        resp = client.get("/cpi/member/SAF")
        assert "cpi-breadcrumb" in resp.text

    def test_member_page_has_children_section(self, client):
        resp = client.get("/cpi/member/SAF")
        assert "children-section" in resp.text

    def test_member_page_has_siblings_section(self, client):
        resp = client.get("/cpi/member/SAF")
        assert "siblings-section" in resp.text

    def test_member_page_breadcrumb_links_to_cpi(self, client):
        resp = client.get("/cpi/member/SAF")
        assert 'href="/cpi"' in resp.text
