"""Tests for Markdown-to-HTML conversion."""

import pytest
from poster.markdown import md_to_html


class TestBasicElements:
    def test_paragraph(self):
        result = md_to_html("Hello world.")
        assert "<p>Hello world.</p>" in result

    def test_multiple_paragraphs(self):
        result = md_to_html("Para 1.\n\nPara 2.")
        assert "<p>Para 1.</p>" in result
        assert "<p>Para 2.</p>" in result

    def test_bold(self):
        result = md_to_html("This is **bold** text.")
        assert "<strong>bold</strong>" in result

    def test_italic(self):
        result = md_to_html("This is *italic* text.")
        assert "<em>italic</em>" in result

    def test_inline_code(self):
        result = md_to_html("Use `print()` to debug.")
        assert "<code>print()</code>" in result

    def test_html_escaped(self):
        result = md_to_html("Tag: <div>")
        assert "&lt;div&gt;" in result

    def test_h2_heading(self):
        result = md_to_html("## Section Title")
        assert "<h2>Section Title</h2>" in result

    def test_h1_stripped(self):
        result = md_to_html("# Main Title\n\nSome text.")
        assert "<h1>" not in result
        assert "<p>Some text.</p>" in result

    def test_h1_only(self):
        result = md_to_html("# Just a title")
        assert result == ""


class TestLists:
    def test_unordered_list(self):
        src = "- item 1\n- item 2\n- item 3"
        result = md_to_html(src)
        assert "<ul>" in result
        assert result.count("<li>") == 3
        assert "</ul>" in result

    def test_ordered_list(self):
        src = "1. first\n2. second\n3. third"
        result = md_to_html(src)
        assert "<ol>" in result
        assert result.count("<li>") == 3

    def test_list_then_paragraph(self):
        src = "- item 1\n- item 2\n\nAfter list paragraph."
        result = md_to_html(src)
        assert "<ul>" in result
        assert "</ul>" in result
        assert "<p>After list paragraph.</p>" in result


class TestCodeBlocks:
    def test_fenced_code_block(self):
        src = "```python\nprint('hello')\n```"
        result = md_to_html(src)
        assert "<pre><code" in result
        assert "language-python" in result
        assert "print('hello')" in result

    def test_plain_code_block(self):
        src = "```\njust code\n```"
        result = md_to_html(src)
        assert "<pre><code>" in result
        assert "language-" not in result


class TestTables:
    def test_simple_table(self):
        src = "| A | B |\n| --- | --- |\n| 1 | 2 |"
        result = md_to_html(src)
        assert "<table>" in result
        assert "<thead>" in result
        assert "<th>A</th>" in result
        assert "<th>B</th>" in result
        assert "<td>1</td>" in result
        assert "<td>2</td>" in result


class TestBlockquote:
    def test_blockquote(self):
        src = "> A wise quote."
        result = md_to_html(src)
        assert "<blockquote>" in result
        assert "A wise quote." in result


class TestImages:
    def test_image(self):
        src = "![alt text](image.png)"
        result = md_to_html(src)
        assert '<img src="image.png"' in result
        assert 'alt="alt text"' in result

    def test_image_with_title(self):
        src = '![alt](img.png "title")'
        result = md_to_html(src)
        assert '<img src="img.png"' in result


class TestMixedContent:
    def test_full_article_snippet(self):
        src = """## Introduction

This is a **bold** claim with `code` and *emphasis*.

- Point one
- Point two

| Col1 | Col2 |
|------|------|
| A    | B    |

> Final thought."""
        result = md_to_html(src)
        assert "<h2>Introduction</h2>" in result
        assert "<strong>bold</strong>" in result
        assert "<code>code</code>" in result
        assert "<em>emphasis</em>" in result
        assert "<ul>" in result
        assert "<table>" in result
        assert "<blockquote>" in result
