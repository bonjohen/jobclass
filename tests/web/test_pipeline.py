"""Tests for the Pipeline Explorer page."""


class TestPipelinePage:
    """Pipeline Explorer at /pipeline."""

    def test_returns_200(self, client):
        resp = client.get("/pipeline")
        assert resp.status_code == 200

    def test_has_correct_title(self, client):
        resp = client.get("/pipeline")
        assert "Pipeline Explorer" in resp.text

    def test_has_canvas_element(self, client):
        resp = client.get("/pipeline")
        assert '<canvas id="pipeline-canvas"' in resp.text

    def test_has_control_bar(self, client):
        resp = client.get("/pipeline")
        assert 'pipeline-controls' in resp.text
        assert 'pipeline-search-input' in resp.text

    def test_has_filter_buttons(self, client):
        resp = client.get("/pipeline")
        assert 'data-filter="source"' in resp.text
        assert 'data-filter="process"' in resp.text
        assert 'data-filter="storage"' in resp.text
        assert 'data-filter="gate"' in resp.text
        assert 'data-filter="interface"' in resp.text

    def test_has_guided_mode_buttons(self, client):
        resp = client.get("/pipeline")
        assert "Follow the Data" in resp.text
        assert "What Can Break" in resp.text
        assert "Time-Series Path" in resp.text
        assert "From Query to Proof" in resp.text

    def test_has_detail_panel_hidden(self, client):
        resp = client.get("/pipeline")
        assert 'id="pipeline-detail-panel"' in resp.text
        assert "hidden" in resp.text

    def test_has_minimap(self, client):
        resp = client.get("/pipeline")
        assert 'id="pipeline-minimap"' in resp.text
        assert 'id="pipeline-minimap-canvas"' in resp.text

    def test_includes_pipeline_js(self, client):
        resp = client.get("/pipeline")
        assert "pipeline.js" in resp.text
        assert "pipeline_graph_data.js" in resp.text

    def test_has_aria_labels(self, client):
        resp = client.get("/pipeline")
        assert 'role="toolbar"' in resp.text
        assert 'role="complementary"' in resp.text
        assert 'aria-label="Pipeline Explorer interactive graph"' in resp.text

    def test_has_screen_reader_announcements(self, client):
        resp = client.get("/pipeline")
        assert 'id="pipeline-announcements"' in resp.text
        assert 'aria-live="polite"' in resp.text

    def test_has_guided_step_overlay(self, client):
        resp = client.get("/pipeline")
        assert 'id="pipeline-guided-overlay"' in resp.text


class TestPipelineNavLink:
    """Pipeline nav link appears on all pages."""

    def test_nav_link_on_landing(self, client):
        resp = client.get("/")
        assert 'href="/pipeline"' in resp.text

    def test_nav_link_on_search(self, client):
        resp = client.get("/search")
        assert 'href="/pipeline"' in resp.text

    def test_nav_link_on_methodology(self, client):
        resp = client.get("/methodology")
        assert 'href="/pipeline"' in resp.text

    def test_nav_link_on_lessons(self, client):
        resp = client.get("/lessons")
        assert 'href="/pipeline"' in resp.text

    def test_nav_link_on_trends(self, client):
        resp = client.get("/trends")
        assert 'href="/pipeline"' in resp.text

    def test_nav_link_between_cpi_and_methodology(self, client):
        """Pipeline link should appear between CPI and Methodology in nav."""
        resp = client.get("/")
        cpi_pos = resp.text.find('href="/cpi"')
        pipeline_pos = resp.text.find('href="/pipeline"')
        methodology_pos = resp.text.find('href="/methodology"')
        assert cpi_pos < pipeline_pos < methodology_pos
