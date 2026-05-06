"""Tests for HTML builder."""

from pathlib import Path
from poster.config import PosterConfig
from poster.builder import build_html


class TestBuildHTML:
    def test_single_page_structure(self):
        config = PosterConfig(
            title="Test Title",
            author="Test Author",
            date="2026-05-06",
            footer_label="Test Label",
            total_pages=1,
            theme="light",
        )
        html = build_html(["Some **bold** content."], config)

        assert "<!DOCTYPE html>" in html
        assert "<h1>Test Title</h1>" in html
        assert "Test Author" in html
        assert "Test Label" in html
        assert "<strong>bold</strong>" in html
        assert 'data-page="1"' in html

    def test_multi_page_structure(self):
        config = PosterConfig(
            title="Multi Page",
            author="Author",
            date="2026-01-01",
            footer_label="Footer",
            total_pages=2,
            theme="light",
        )
        html = build_html(["Page 1 content.", "## Page 2 heading\nPage 2 body."], config)

        assert 'data-page="1"' in html
        assert 'data-page="2"' in html
        assert "<h1>Multi Page</h1>" in html
        assert "<h2>Page 2 heading</h2>" in html
        assert "1 / 2" in html

    def test_dark_theme(self):
        config = PosterConfig(
            title="Dark",
            author="A",
            date="2026-01-01",
            total_pages=1,
            theme="dark",
        )
        html = build_html(["Content."], config)
        assert "#1A1A1E" in html  # dark bg
        assert "#D4D4D4" in html  # dark text
        assert "#FFFFFF" in html  # dark heading
