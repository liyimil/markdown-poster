"""Theme definitions for Markdown Poster."""

from dataclasses import dataclass, field


@dataclass
class Theme:
    name: str
    # Colors
    bg: str
    text: str
    heading: str
    muted: str
    accent: str
    border: str
    table_header_bg: str
    table_border: str
    code_bg: str
    pre_bg: str
    blockquote_border: str
    blockquote_text: str
    # Author
    author_name_color: str
    author_date_color: str
    footer_color: str
    # Shadows / outlines
    card_shadow: str = "none"
    card_outline: str = "none"


class LightTheme(Theme):
    def __init__(self):
        super().__init__(
            name="light",
            bg="#F9F9F6",
            text="#1A1A1A",
            heading="#000000",
            muted="#888888",
            accent="#4a9eff",
            border="#E8E6D9",
            table_header_bg="#f0efe8",
            table_border="#d0cec5",
            code_bg="#f5f5f5",
            pre_bg="#f5f5f5",
            blockquote_border="#4a9eff",
            blockquote_text="#333333",
            author_name_color="#333333",
            author_date_color="#888888",
            footer_color="#aaaaaa",
        )


class DarkTheme(Theme):
    def __init__(self):
        super().__init__(
            name="dark",
            bg="#1A1A1E",
            text="#D4D4D4",
            heading="#FFFFFF",
            muted="#888888",
            accent="#6db3ff",
            border="#333333",
            table_header_bg="#252528",
            table_border="#444444",
            code_bg="#2a2a2e",
            pre_bg="#2a2a2e",
            blockquote_border="#6db3ff",
            blockquote_text="#c0c0c0",
            author_name_color="#CCCCCC",
            author_date_color="#888888",
            footer_color="#666666",
        )
