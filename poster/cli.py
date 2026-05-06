"""Unified CLI for Markdown Poster — Markdown to XHS card images."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from poster.config import PosterConfig, load_config, merge_cli_args
from poster.pagination import resolve_pages
from poster.builder import build_html


@click.command()
@click.argument("src", type=click.Path(exists=True), required=False)
@click.option("-c", "--config", "config_path", type=click.Path(exists=True),
              help="Path to YAML config file")
@click.option("-t", "--title", help="Article title")
@click.option("-a", "--author", help="Author name")
@click.option("-d", "--date", help="Publication date")
@click.option("--avatar", help="Avatar image path")
@click.option("--footer", "footer_label", help="Footer label text")
@click.option("-p", "--pages", type=int, help="Total pages (overrides auto)")
@click.option("--auto-paginate", is_flag=True, help="Auto-split content into pages")
@click.option("--chars-per-page", type=int, default=500,
              help="Target characters per page (default: 500)")
@click.option("--max-pages", type=int, default=25,
              help="Maximum pages for auto-pagination (default: 25)")
@click.option("--theme", type=click.Choice(["light", "dark"]), default="light",
              help="Color theme")
@click.option("-o", "--output", "output_dir", type=click.Path(),
              help="Output directory for images")
@click.option("--format", "img_format", type=click.Choice(["png", "webp", "jpeg"]),
              default="png", help="Output image format")
@click.option("--fixed-height", is_flag=True, help="Use fixed 1080x1440 instead of auto-height")
@click.option("--no-screenshot", is_flag=True, help="Generate HTML only, skip screenshots")
@click.option("--open", "open_html", is_flag=True, help="Open HTML in browser after generation")
@click.version_option(version="2.0.0", prog_name="markdown-poster")
def main(
    src,
    config_path,
    title,
    author,
    date,
    avatar,
    footer_label,
    pages,
    auto_paginate,
    chars_per_page,
    max_pages,
    theme,
    output_dir,
    img_format,
    fixed_height,
    no_screenshot,
    open_html,
):
    """Turn Markdown articles into beautifully formatted XHS (小红书) image cards.

    \b
    Examples:
      markdown-poster article.md
      markdown-poster article.md --auto-paginate --theme dark
      markdown-poster article.md -t "My Title" -a "Jane" --format webp
      markdown-poster -c poster.yaml
    """
    # Load config
    if config_path:
        cfg = load_config(Path(config_path))
    else:
        cfg = load_config()

    # Merge CLI overrides
    overrides = {
        "title": title, "author": author, "date": date,
        "avatar": avatar, "footer_label": footer_label,
        "theme": theme, "format": img_format,
        "auto_height": not fixed_height,
        "screenshot": not no_screenshot,
        "auto_paginate": auto_paginate,
        "chars_per_page": chars_per_page,
    }
    if pages:
        overrides["total_pages"] = pages
    author_changed = bool(author)
    footer_changed = bool(footer_label)
    if src:
        overrides["src"] = Path(src)
        out_html_changed = True
    else:
        out_html_changed = False
    if output_dir:
        overrides["output_dir"] = Path(output_dir)

    cfg = merge_cli_args(cfg, **overrides)
    if out_html_changed:
        cfg.out_html = None  # force recalculation with new stem
    if author_changed and not footer_changed:
        cfg.footer_label = ""  # force recalculation from new author
    cfg.__post_init__()  # re-normalize paths

    # Resolve source
    src_path = cfg.src
    if isinstance(src_path, str):
        src_path = Path(src_path)
    if not src_path.exists():
        click.echo(f"Error: source file not found: {src_path}", err=True)
        sys.exit(1)

    click.echo(f"Source:  {src_path.name}")
    click.echo(f"Theme:   {cfg.theme}")
    click.echo(f"Format:  {cfg.format}")

    # Read source lines
    src_lines = src_path.read_text(encoding="utf-8").split("\n")

    # Resolve pages
    page_ranges = resolve_pages(
        src_lines,
        manual_pages=cfg.pages if cfg.pages else None,
        auto=cfg.auto_paginate or not cfg.pages,
        chars_per_page=cfg.chars_per_page,
        max_pages=max_pages,
    )

    if not page_ranges:
        # Single page with all content
        page_ranges = [(1, len(src_lines))]

    cfg.total_pages = len(page_ranges)
    cfg.pages = page_ranges

    click.echo(f"Pages:   {len(page_ranges)}")
    for idx, (s, e) in enumerate(page_ranges, 1):
        char_count = sum(len(src_lines[i - 1]) for i in range(s, e + 1))
        click.echo(f"  Page {idx}: lines {s}-{e} (~{char_count} chars)")

    # Extract page content
    pages_content = []
    for start, end in page_ranges:
        chunk = src_lines[start - 1 : end]
        pages_content.append("\n".join(chunk))

    # Build HTML
    html = build_html(pages_content, cfg)
    out_html = cfg.out_html
    if isinstance(out_html, str):
        out_html = Path(out_html)
    out_html.write_text(html, encoding="utf-8")
    click.echo(f"\nHTML:    {out_html}")

    # Screenshot
    if cfg.screenshot:
        from poster.screenshot import take_screenshots_sync

        output = cfg.output_dir
        if isinstance(output, str):
            output = Path(output)

        click.echo(f"Shooting {cfg.total_pages} page(s)...")
        saved = take_screenshots_sync(
            out_html,
            cfg.total_pages,
            output,
            width=cfg.width,
            fixed_height=cfg.fixed_height,
            auto_height=cfg.auto_height,
            format=cfg.format,
            headless=cfg.headless,
        )
        for p in saved:
            click.echo(f"  -> {p.name}")
        click.echo(f"\nDone! {len(saved)} cards saved to {output}/")

    # Open in browser
    if open_html:
        import webbrowser
        webbrowser.open(out_html.as_uri())


if __name__ == "__main__":
    main()
