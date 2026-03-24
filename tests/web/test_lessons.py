"""Tests for the Lessons section: landing page and all lesson pages."""

from pathlib import Path

from jobclass.web.lessons import LESSON_SLUGS, LESSONS


class TestLessonsLanding:
    """Landing page at /lessons."""

    def test_landing_returns_200(self, client):
        resp = client.get("/lessons")
        assert resp.status_code == 200

    def test_landing_has_lesson_cards(self, client):
        resp = client.get("/lessons")
        assert "lesson-card" in resp.text

    def test_landing_links_to_all_lessons(self, client):
        resp = client.get("/lessons")
        for slug in LESSON_SLUGS:
            assert f"/lessons/{slug}" in resp.text, f"Missing link to /lessons/{slug}"

    def test_landing_has_11_cards(self, client):
        resp = client.get("/lessons")
        assert resp.text.count("lesson-card-number") == 12


class TestLessonPages:
    """Each individual lesson page renders correctly."""

    def test_all_lessons_return_200(self, client):
        for slug in LESSON_SLUGS:
            resp = client.get(f"/lessons/{slug}")
            assert resp.status_code == 200, f"/lessons/{slug} returned {resp.status_code}"

    def test_lessons_have_content_sections(self, client):
        for slug in LESSON_SLUGS:
            resp = client.get(f"/lessons/{slug}")
            assert "lesson-section" in resp.text, f"/lessons/{slug} missing lesson-section"

    def test_lessons_have_code_blocks(self, client):
        for slug in LESSON_SLUGS:
            resp = client.get(f"/lessons/{slug}")
            assert "lesson-code" in resp.text, f"/lessons/{slug} missing code blocks"

    def test_lessons_have_prev_next_nav(self, client):
        for slug in LESSON_SLUGS:
            resp = client.get(f"/lessons/{slug}")
            assert "lesson-nav" in resp.text, f"/lessons/{slug} missing prev/next nav"

    def test_invalid_slug_returns_404(self, client):
        resp = client.get("/lessons/nonexistent-lesson")
        assert resp.status_code == 404


class TestLessonNavigation:
    """Prev/next links form a complete chain."""

    def test_first_lesson_links_to_second(self, client):
        resp = client.get("/lessons/federal-data")
        assert "/lessons/dimensional-modeling" in resp.text

    def test_last_lesson_links_to_index(self, client):
        resp = client.get("/lessons/ui-data-alignment")
        assert "/lessons" in resp.text

    def test_nav_chain_is_complete(self, client):
        """Each lesson's next link matches the following lesson's URL."""
        for i in range(len(LESSON_SLUGS) - 1):
            resp = client.get(f"/lessons/{LESSON_SLUGS[i]}")
            assert f"/lessons/{LESSON_SLUGS[i + 1]}" in resp.text, (
                f"Lesson {LESSON_SLUGS[i]} doesn't link to {LESSON_SLUGS[i + 1]}"
            )


class TestLessonsNavBar:
    """Lessons link appears in the site nav."""

    def test_nav_has_lessons_link(self, client):
        resp = client.get("/")
        assert "/lessons" in resp.text
        assert "Lessons" in resp.text

    def test_lessons_link_on_methodology_page(self, client):
        resp = client.get("/methodology")
        assert "/lessons" in resp.text


class TestLessonRegistry:
    """Verify lesson registry integrity."""

    def test_every_lesson_has_template_file(self):
        templates_dir = Path(__file__).resolve().parent.parent.parent / "src" / "jobclass" / "web" / "templates"
        for _slug, _title, template_name in LESSONS:
            assert (templates_dir / template_name).exists(), f"Missing template: {template_name}"

    def test_card_count_matches_registry(self, client):
        resp = client.get("/lessons")
        assert resp.text.count("lesson-card-number") == len(LESSONS)
