"""Theme system for Markdown Poster."""

from poster.themes.base import Theme, LightTheme, DarkTheme

THEMES = {
    "light": LightTheme,
    "dark": DarkTheme,
}

def get_theme(name: str) -> Theme:
    cls = THEMES.get(name)
    if cls is None:
        raise ValueError(f"Unknown theme: {name}. Available: {list(THEMES.keys())}")
    return cls()
