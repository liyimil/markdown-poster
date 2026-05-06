"""Tests for auto-pagination."""

from poster.pagination import auto_paginate, resolve_pages


class TestAutoPaginate:
    def test_empty(self):
        assert auto_paginate("") == []

    def test_single_short_page(self):
        text = "Short article.\n\nOnly a few words."
        pages = auto_paginate(text, chars_per_page=500)
        assert len(pages) == 1
        start, end = pages[0]
        assert start == 1

    def test_split_on_headings(self):
        text = """# Title
Intro paragraph with some content here that fills space.

## Section One
This is the first section with enough content to be meaningful and have substantial text for testing pagination logic properly here.

## Section Two
This is the second section also with sufficient content to make the pagination logic work correctly when splitting on heading boundaries.

## Section Three
Final section with more text content to fill out the article and test the splitting behavior thoroughly.
"""
        pages = auto_paginate(text, chars_per_page=50, split_on_headings=True)
        assert len(pages) >= 2, f"Expected >= 2 pages, got {len(pages)}"

    def test_max_pages_limit(self):
        text = "\n\n".join([f"## Section {i}\n" + "x " * 200 for i in range(15)])
        pages = auto_paginate(text, chars_per_page=100, max_pages=8)
        assert len(pages) <= 8

    def test_fallback_no_headings(self):
        text = "Line one.\n\nLine two.\n\nLine three.\n\nLine four.\n\nLine five."
        pages = auto_paginate(text, chars_per_page=15, split_on_headings=True)
        assert len(pages) >= 1


class TestResolvePages:
    def test_manual_pages_take_priority(self):
        lines = ["line1", "line2", "line3", "line4", "line5"]
        manual = [(1, 2), (3, 5)]
        result = resolve_pages(lines, manual_pages=manual, auto=False)
        assert result == manual

    def test_auto_when_no_manual(self):
        lines = ["# Title", "", "## S1", "content here", "", "## S2", "more content"]
        result = resolve_pages(lines, manual_pages=[], auto=True, chars_per_page=20)
        assert len(result) >= 1

    def test_line_ranges_are_1_indexed(self):
        lines = ["a", "b", "c", "d", "e"]
        result = resolve_pages(lines, manual_pages=[(1, 3), (4, 5)])
        for start, end in result:
            assert start >= 1
            assert end <= len(lines)
            assert start <= end
