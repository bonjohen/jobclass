"""Phase W2 tests: Occupation search, hierarchy, and profile endpoints and pages."""



class TestSearchAPI:
    """WT2-01 through WT2-05: Search endpoint tests."""

    def test_search_by_keyword(self, client):
        resp = client.get("/api/occupations/search?q=Software")
        assert resp.status_code == 200
        data = resp.json()
        codes = [r["soc_code"] for r in data["results"]]
        assert "15-1252" in codes

    def test_search_by_soc_code(self, client):
        resp = client.get("/api/occupations/search?q=15-1252")
        data = resp.json()
        assert len(data["results"]) >= 1
        assert data["results"][0]["soc_code"] == "15-1252"

    def test_search_empty_query(self, client):
        resp = client.get("/api/occupations/search?q=")
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"] == []

    def test_search_response_schema(self, client):
        resp = client.get("/api/occupations/search?q=Software")
        data = resp.json()
        for r in data["results"]:
            assert "soc_code" in r
            assert "occupation_title" in r
            assert "occupation_level" in r
            assert isinstance(r["soc_code"], str)
            assert isinstance(r["occupation_level"], int)

    def test_search_page_renders(self, client):
        resp = client.get("/search")
        assert resp.status_code == 200
        assert "<input" in resp.text
        assert "search-input" in resp.text


class TestHierarchyAPI:
    """WT2-06 through WT2-08: Hierarchy endpoint tests."""

    def test_hierarchy_returns_tree(self, client):
        resp = client.get("/api/occupations/hierarchy")
        assert resp.status_code == 200
        data = resp.json()
        assert "hierarchy" in data
        assert len(data["hierarchy"]) > 0

    def test_hierarchy_has_children(self, client):
        data = client.get("/api/occupations/hierarchy").json()
        # At least one root should have children
        has_children = any(len(n.get("children", [])) > 0 for n in data["hierarchy"])
        assert has_children

    def test_hierarchy_contains_computer_group(self, client):
        data = client.get("/api/occupations/hierarchy").json()
        all_codes = _collect_codes(data["hierarchy"])
        # Should have at least a major or minor group in the 15 family
        has_15 = any(c.startswith("15-") for c in all_codes)
        assert has_15

    def test_hierarchy_page_renders(self, client):
        resp = client.get("/hierarchy")
        assert resp.status_code == 200
        assert "hierarchy-tree" in resp.text


class TestProfileAPI:
    """WT2-09 through WT2-12: Profile endpoint tests."""

    def test_profile_returns_data(self, client):
        resp = client.get("/api/occupations/15-1252")
        assert resp.status_code == 200
        data = resp.json()
        assert data["soc_code"] == "15-1252"
        assert "Software" in data["occupation_title"]

    def test_profile_has_hierarchy_fields(self, client):
        data = client.get("/api/occupations/15-1252").json()
        assert data["soc_version"] == "2018"
        assert data["source_release_id"] is not None

    def test_profile_has_breadcrumb(self, client):
        data = client.get("/api/occupations/15-1252").json()
        assert "breadcrumb" in data
        assert len(data["breadcrumb"]) > 0

    def test_profile_has_definition(self, client):
        data = client.get("/api/occupations/15-1252").json()
        assert data["occupation_definition"] is not None

    def test_profile_nonexistent_returns_404(self, client):
        resp = client.get("/api/occupations/99-9999")
        assert resp.status_code == 404

    def test_profile_page_renders(self, client):
        resp = client.get("/occupation/15-1252")
        assert resp.status_code == 200
        assert 'data-soc-code="15-1252"' in resp.text

    def test_profile_lineage_badge_in_page(self, client):
        resp = client.get("/occupation/15-1252")
        assert "lineage-badge" in resp.text


def _collect_codes(nodes):
    """Recursively collect all SOC codes from hierarchy tree."""
    codes = []
    for n in nodes:
        codes.append(n["soc_code"])
        if n.get("children"):
            codes.extend(_collect_codes(n["children"]))
    return codes
