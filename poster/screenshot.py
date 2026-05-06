"""Shared screenshot module — captures XHS card pages as PNG/WebP images."""

from __future__ import annotations

import asyncio
from pathlib import Path


async def take_screenshots(
    html_path: Path,
    total_pages: int,
    output_dir: Path,
    *,
    width: int = 1080,
    fixed_height: int = 1440,
    auto_height: bool = True,
    format: str = "png",
    headless: bool = True,
    wait_ms_page1: int = 3000,
    wait_ms_other: int = 500,
) -> list[Path]:
    """Take screenshots of each card page using Playwright."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    html_path = html_path.resolve()
    base_url = html_path.as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)

        for i in range(1, total_pages + 1):
            url = base_url + f"?page={i}"
            wait_ms = wait_ms_page1 if i == 1 else wait_ms_other

            if auto_height:
                page = await browser.new_page(viewport={"width": width, "height": 4000})
                await page.goto(url, wait_until="commit", timeout=15000)
                await page.wait_for_timeout(wait_ms)

                # Isolate the active card and get its height
                height = await page.evaluate("""() => {
                    document.querySelectorAll('preact-border-shadow-host').forEach(e => e.remove());
                    document.getElementById('navControls').style.display = 'none';
                    document.querySelectorAll('*').forEach(el => {
                        el.style.outline = 'none';
                        el.style.boxShadow = 'none';
                    });
                    const card = document.querySelector('.card.active');
                    if (!card) return 1440;
                    return card.scrollHeight;
                }""")

                actual_height = min(height + 60, 10000)
                await page.set_viewport_size({"width": width, "height": actual_height})
                await page.wait_for_timeout(300)
            else:
                page = await browser.new_page(
                    viewport={"width": width, "height": fixed_height}
                )
                await page.goto(url, wait_until="commit", timeout=15000)
                await page.wait_for_timeout(wait_ms)
                await page.evaluate("""() => {
                    document.getElementById('navControls').style.display = 'none';
                    document.querySelectorAll('*').forEach(el => {
                        el.style.outline = 'none'; el.style.boxShadow = 'none';
                    });
                }""")
                await page.wait_for_timeout(300)

            suffix = format if format in ("png", "webp", "jpeg") else "png"
            ext = "jpg" if suffix == "jpeg" else suffix
            out_path = output_dir / f"{str(i).zfill(2)}.{ext}"

            if auto_height:
                card = await page.query_selector(".card.active")
                if card:
                    await card.screenshot(path=str(out_path))
                else:
                    await page.screenshot(path=str(out_path), full_page=False)
            else:
                await page.screenshot(path=str(out_path), full_page=True)

            saved.append(out_path)
            await page.close()

        await browser.close()

    return saved


def take_screenshots_sync(
    html_path: Path,
    total_pages: int,
    output_dir: Path,
    **kwargs,
) -> list[Path]:
    """Synchronous wrapper for take_screenshots."""
    return asyncio.run(
        take_screenshots(html_path, total_pages, output_dir, **kwargs)
    )
