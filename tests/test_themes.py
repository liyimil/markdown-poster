"""Tests for theme system."""

import pytest
from poster.themes import get_theme, THEMES
from poster.themes.base import Theme, LightTheme, DarkTheme


class TestThemes:
    def test_light_theme(self):
        theme = get_theme("light")
        assert theme.name == "light"
        assert theme.bg == "#F9F9F6"
        assert theme.text == "#1A1A1A"
        assert theme.heading == "#000000"

    def test_dark_theme(self):
        theme = get_theme("dark")
        assert theme.name == "dark"
        assert theme.bg == "#1A1A1E"
        assert theme.heading == "#FFFFFF"

    def test_unknown_theme(self):
        with pytest.raises(ValueError):
            get_theme("nonexistent")

    def test_theme_is_dataclass(self):
        theme = get_theme("light")
        d = {f.name: getattr(theme, f.name) for f in Theme.__dataclass_fields__.values()}
        assert "bg" in d
        assert "text" in d
        assert "heading" in d
        assert "accent" in d
