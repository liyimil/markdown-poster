"""HTML builder — assembles multi-page XHS card HTML from Markdown content."""

from __future__ import annotations

from pathlib import Path
from poster.config import PosterConfig
from poster.markdown import md_to_html
from poster.themes import get_theme


def build_html(
    pages_content: list[str],
    config: PosterConfig,
) -> str:
    """Build a complete multi-page HTML document from page contents."""
    theme = get_theme(config.theme)
    css = _load_css(theme)

    cards = []
    for i, content in enumerate(pages_content, 1):
        body_html = md_to_html(content)
        card_inner = _build_card_inner(body_html, i, config)
        cards.append(f'  <div class="card" data-page="{i}">\n{card_inner}\n  </div>')

    all_cards = "\n".join(cards)
    total = config.total_pages if config.total_pages else len(pages_content)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
{css}
</style>
</head>
<body>
{all_cards}
<div id="navControls">
  <button onclick="go(-1)">Prev</button>
  <button onclick="go(1)">Next</button>
</div>
<script>
let cur = parseInt(new URLSearchParams(location.search).get('page')) || 1;
function showPage(n) {{
  document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
  const el = document.querySelector('[data-page="'+n+'"]');
  if (el) el.classList.add('active');
  cur = n;
}}
function go(d) {{ cur = Math.max(1, Math.min({total}, cur+d)); showPage(cur); }}
function screenshotMode(pageNum) {{
  if (pageNum) showPage(pageNum);
  document.querySelectorAll('preact-border-shadow-host').forEach(e => e.remove());
  const activeCard = document.querySelector('.card.active');
  if (!activeCard) return {{ error: 'No active card found' }};
  const clone = activeCard.cloneNode(true);
  document.body.innerHTML = '';
  document.body.style.cssText = 'background:{theme.bg};margin:0;padding:0;outline:none!important;box-shadow:none!important';
  document.documentElement.style.cssText = 'background:{theme.bg};margin:0;padding:0;outline:none!important;box-shadow:none!important';
  document.body.appendChild(clone);
  clone.style.display = 'block';
  return {{ height: clone.scrollHeight, page: pageNum || cur, status: 'ready' }};
}}
showPage(cur);
document.addEventListener('keydown', e => {{
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') go(1);
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') go(-1);
  if (e.key === 'n' || e.key === 'N') {{
    const nav = document.getElementById('navControls');
    nav.style.display = nav.style.display === 'flex' ? 'none' : 'flex';
  }}
}});
</script>
</body>
</html>"""


def _build_card_inner(body_html: str, page_num: int, config: PosterConfig) -> str:
    """Build the inner HTML for a single card."""
    total = config.total_pages if config.total_pages else 1

    if page_num == 1:
        inner = f"""    <div class="content">
      <h1>{config.title}</h1>
      <div class="author-area">
        <img src="{config.avatar}" alt="avatar">
        <div class="author-info">
          <div class="author-name">{config.author}</div>
          <div class="author-date">{config.date}</div>
        </div>
      </div>
      {body_html}
      <div class="page-footer">
        <span class="footer-title">{config.footer_label}</span>
        <span class="footer-page">{page_num} / {total}</span>
      </div>
    </div>"""
    else:
        inner = f"""    <div class="content">
      {body_html}
      <div class="page-footer">
        <span class="footer-title">{config.footer_label}</span>
        <span class="footer-page">{page_num} / {total}</span>
      </div>
    </div>"""

    return inner


def _load_css(theme) -> str:
    """Load the shared CSS template and inject theme variables."""
    css_path = Path(__file__).parent.parent / "templates" / "xhs.css"
    css = css_path.read_text(encoding="utf-8")

    replacements = {
        "{bg}": theme.bg,
        "{text}": theme.text,
        "{heading}": theme.heading,
        "{muted}": theme.muted,
        "{accent}": theme.accent,
        "{border}": theme.border,
        "{table_header_bg}": theme.table_header_bg,
        "{table_border}": theme.table_border,
        "{code_bg}": theme.code_bg,
        "{pre_bg}": theme.pre_bg,
        "{blockquote_border}": theme.blockquote_border,
        "{blockquote_text}": theme.blockquote_text,
        "{author_name_color}": theme.author_name_color,
        "{author_date_color}": theme.author_date_color,
        "{footer_color}": theme.footer_color,
        "{card_shadow}": theme.card_shadow,
        "{card_outline}": theme.card_outline,
    }

    for placeholder, value in replacements.items():
        css = css.replace(placeholder, value)

    return css
