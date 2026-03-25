"""CPI API endpoint tests."""


class TestCpiSearch:
    def test_search_returns_200(self, client):
        resp = client.get("/api/cpi/search?q=food")
        assert resp.status_code == 200

    def test_search_finds_members(self, client):
        resp = client.get("/api/cpi/search?q=food")
        data = resp.json()
        assert data["total"] > 0
        assert any("Food" in r["title"] for r in data["results"])

    def test_search_by_code(self, client):
        resp = client.get("/api/cpi/search?q=SA0")
        data = resp.json()
        assert data["total"] > 0
        assert any(r["member_code"] == "SA0" for r in data["results"])

    def test_search_empty_query(self, client):
        resp = client.get("/api/cpi/search?q=")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_search_result_fields(self, client):
        resp = client.get("/api/cpi/search?q=All items")
        data = resp.json()
        assert len(data["results"]) > 0
        r = data["results"][0]
        assert "member_code" in r
        assert "title" in r
        assert "semantic_role" in r


class TestCpiMemberDetail:
    def test_known_member_returns_200(self, client):
        resp = client.get("/api/cpi/members/SA0")
        assert resp.status_code == 200

    def test_member_fields(self, client):
        resp = client.get("/api/cpi/members/SA0")
        data = resp.json()
        assert data["member_code"] == "SA0"
        assert data["title"] == "All items"
        assert data["semantic_role"] == "hierarchy_node"
        assert "variant_count" in data
        assert "children_count" in data
        assert "ancestors" in data

    def test_cross_cutting_member(self, client):
        resp = client.get("/api/cpi/members/SA0L1E")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_cross_cutting"] is True
        assert data["semantic_role"] == "special_aggregate"

    def test_unknown_member_returns_404(self, client):
        resp = client.get("/api/cpi/members/ZZZZZ")
        assert resp.status_code == 404

    def test_case_insensitive(self, client):
        resp = client.get("/api/cpi/members/sa0")
        assert resp.status_code == 200


class TestCpiMemberChildren:
    def test_children_returns_200(self, client):
        resp = client.get("/api/cpi/members/SAF/children")
        assert resp.status_code == 200

    def test_children_list(self, client):
        resp = client.get("/api/cpi/members/SAF/children")
        data = resp.json()
        assert data["member_code"] == "SAF"
        assert len(data["children"]) > 0
        # SAF1 (Food) should be a child of SAF (Food and beverages)
        codes = {c["member_code"] for c in data["children"]}
        assert "SAF1" in codes

    def test_leaf_has_no_children(self, client):
        resp = client.get("/api/cpi/members/SAF1111/children")
        data = resp.json()
        assert len(data["children"]) == 0


class TestCpiMemberRelations:
    def test_relations_returns_200(self, client):
        resp = client.get("/api/cpi/members/SA0L1E/relations")
        assert resp.status_code == 200

    def test_relations_have_type(self, client):
        resp = client.get("/api/cpi/members/SA0L1E/relations")
        data = resp.json()
        if data["relations"]:
            r = data["relations"][0]
            assert "relation_type" in r
            assert "member_code" in r


class TestCpiMemberSeries:
    def test_series_returns_200(self, client):
        resp = client.get("/api/cpi/members/SA0/series")
        assert resp.status_code == 200

    def test_series_fields(self, client):
        resp = client.get("/api/cpi/members/SA0/series")
        data = resp.json()
        assert data["member_code"] == "SA0"
        assert data["index_family"] == "CPI-U"
        assert "series" in data


class TestCpiAreaDetail:
    def test_national_area(self, client):
        resp = client.get("/api/cpi/areas/0000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["area_code"] == "0000"
        assert data["area_title"] == "U.S. city average"
        assert data["area_type"] == "national"
        assert "member_count" in data

    def test_unknown_area_returns_404(self, client):
        resp = client.get("/api/cpi/areas/9999")
        assert resp.status_code == 404


class TestCpiAreaMembers:
    def test_area_members_returns_200(self, client):
        resp = client.get("/api/cpi/areas/0000/members")
        assert resp.status_code == 200
        data = resp.json()
        assert data["area_code"] == "0000"
        assert "members" in data
