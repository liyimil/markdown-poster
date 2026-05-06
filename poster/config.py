"""Configuration system — YAML file + CLI overrides."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PosterConfig:
    """Full configuration for generating XHS card images from Markdown."""

    # Source
    src: Path = Path("article.md")
    out_html: Optional[Path] = None

    # Metadata
    title: str = "Untitled"
    author: str = "Author"
    date: str = ""
    avatar: str = "avatar.jpg"
    footer_label: str = ""

    # Pagination
    total_pages: int = 0  # 0 = auto-detect from pages list
    pages: list[tuple[int, int]] = field(default_factory=list)

    # Rendering
    theme: str = "light"
    format: str = "png"  # png or webp
    auto_height: bool = True
    width: int = 1080
    fixed_height: int = 1440

    # Auto-pagination settings
    auto_paginate: bool = False
    chars_per_page: int = 800
    split_on_headings: bool = True

    # Output
    output_dir: Path = Path("output")

    # Screenshot
    screenshot: bool = True
    headless: bool = True

    def __post_init__(self):
        if not self.footer_label:
            self.footer_label = self.author
        if isinstance(self.src, str):
            self.src = Path(self.src)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if self.out_html is None:
            stem = self.src.stem
            self.out_html = self.src.parent / f"{stem}_xhs_pages.html"
        if isinstance(self.out_html, str):
            self.out_html = Path(self.out_html)


def load_config(yaml_path: Optional[Path] = None) -> PosterConfig:
    """Load configuration from a YAML file, falling back to defaults."""
    if yaml_path is None:
        # Search for poster.yaml / poster.yml in cwd
        for name in ("poster.yaml", "poster.yml"):
            candidate = Path(name)
            if candidate.exists():
                yaml_path = candidate
                break

    if yaml_path and yaml_path.exists():
        import yaml
        with open(yaml_path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        return PosterConfig(**raw)

    return PosterConfig()


def merge_cli_args(config: PosterConfig, **overrides) -> PosterConfig:
    """Override config fields with CLI-supplied values (only non-None)."""
    for k, v in overrides.items():
        if v is not None and hasattr(config, k):
            setattr(config, k, v)
    return config
