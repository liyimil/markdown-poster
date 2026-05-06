"""Markdown-to-HTML conversion via mistune with custom rendering."""

from typing import Any, Optional
import mistune
from mistune.renderers.html import HTMLRenderer
from mistune.util import striptags


class XHSRenderer(HTMLRenderer):
    """Custom mistune renderer for XHS card HTML output."""

    NAME = "xhs"

    def __init__(self, escape: bool = True):
        super().__init__(escape=escape)

    def heading(self, text: str, level: int, **attrs) -> str:
        tag = f"h{level}"
        return f"<{tag}>{text}</{tag}>\n"

    def paragraph(self, text: str) -> str:
        return f"<p>{text}</p>\n"

    def strong(self, text: str) -> str:
        return f"<strong>{text}</strong>"

    def emphasis(self, text: str) -> str:
        return f"<em>{text}</em>"

    def codespan(self, text: str) -> str:
        return f"<code>{text}</code>"

    def linebreak(self) -> str:
        return "<br>\n"

    def link(self, text: str, url: str, title: Optional[str] = None) -> str:
        s = f'<a href="{self.safe_url(url)}" target="_blank" rel="noopener"'
        if title:
            s += f' title="{mistune.safe_entity(title)}"'
        return s + f">{text}</a>"

    def image(self, text: str, url: str, title: Optional[str] = None) -> str:
        src = self.safe_url(url)
        alt = striptags(text)
        s = f'<img src="{src}" alt="{alt}"'
        if title:
            s += f' title="{mistune.safe_entity(title)}"'
        return s + " />"

    def list(self, text: str, ordered: bool, **attrs) -> str:
        tag = "ol" if ordered else "ul"
        return f"<{tag}>\n{text}</{tag}>\n"

    def list_item(self, text: str) -> str:
        return f"<li>{text}</li>\n"

    def block_code(self, code: str, info: Optional[str] = None) -> str:
        html = "<pre><code"
        if info:
            lang = info.strip().split(None, 1)[0]
            if lang:
                html += f' class="language-{lang}"'
        return html + f">{code}</code></pre>\n"

    def block_quote(self, text: str) -> str:
        return f"<blockquote>\n{text}</blockquote>\n"

    def block_text(self, text: str) -> str:
        return text

    def table(self, text: str) -> str:
        return f"<table>\n{text}</table>\n"

    def table_head(self, text: str) -> str:
        return f"<thead>\n{text}</thead>\n"

    def table_body(self, text: str) -> str:
        return f"<tbody>\n{text}</tbody>\n"

    def table_row(self, text: str) -> str:
        return f"<tr>\n{text}</tr>\n"

    def table_cell(self, text: str, align: Optional[str] = None, head: bool = False) -> str:
        tag = "th" if head else "td"
        if align:
            return f'<{tag} style="text-align:{align}">{text}</{tag}>\n'
        return f"<{tag}>{text}</{tag}>\n"

    def thematic_break(self) -> str:
        return "<hr>\n"


def _build_markdown() -> mistune.Markdown:
    """Build a mistune Markdown instance with our renderer and plugins."""
    renderer = XHSRenderer(escape=True)
    return mistune.create_markdown(
        renderer=renderer,
        plugins=["table", "strikethrough"],
    )


def md_to_html(text: str) -> str:
    """Convert Markdown text to XHS-card HTML, stripping the H1 (handled separately)."""
    text = text.strip()
    # Strip H1 — the builder inserts it on page 1
    if text.startswith("# "):
        idx = text.find("\n")
        if idx > 0:
            text = text[idx + 1:].strip()
        else:
            return ""

    markdown = _build_markdown()
    result = markdown(text)
    if not result:
        return ""
    return result.strip()
