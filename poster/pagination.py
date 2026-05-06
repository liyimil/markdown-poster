"""Auto-pagination — split Markdown into page-sized chunks."""

from __future__ import annotations


def _char_count(lines: list[str], start: int, end: int) -> int:
    """Count characters in line range (0-indexed, end exclusive)."""
    return sum(len(lines[i]) for i in range(start, min(end, len(lines))))


def _find_blank_lines(lines: list[str], start: int, end: int) -> list[int]:
    """Find indices of blank lines within [start, end)."""
    return [i for i in range(start, end) if not lines[i].strip()]


def auto_paginate(
    text: str,
    chars_per_page: int = 800,
    split_on_headings: bool = True,
    max_pages: int = 25,
) -> list[tuple[int, int]]:
    """Auto-split Markdown into page ranges.

    Returns a list of (start_line, end_line) — 1-indexed, inclusive.
    """
    lines = text.split("\n")

    if not lines or (len(lines) == 1 and not lines[0].strip()):
        return []

    if split_on_headings:
        h2_positions = [
            i for i, line in enumerate(lines) if line.strip().startswith("## ")
        ]
        if h2_positions:
            return _paginate_with_headings(lines, h2_positions, chars_per_page, max_pages)

    return _paginate_flat(lines, chars_per_page, max_pages)


def _build_segments(
    lines: list[str], h2_positions: list[int], chars_per_page: int
) -> list[tuple[int, int, str]]:
    """Build flat list of content segments from H2 sections.

    Pre-H2 content becomes its own segment. Each H2 section is a segment.
    Large segments are split at paragraph boundaries.

    Returns list of (start, end, label) — 0-indexed, end exclusive.
    """
    segments: list[tuple[int, int, str]] = []

    # Pre-H2 content
    if h2_positions[0] > 0:
        segments.append((0, h2_positions[0], "pre"))

    # H2 sections
    for idx, sec_start in enumerate(h2_positions):
        sec_end = h2_positions[idx + 1] if idx + 1 < len(h2_positions) else len(lines)
        heading = lines[sec_start].strip()[3:]
        segments.append((sec_start, sec_end, heading))

    # Split large segments
    split_segments = []
    for seg_start, seg_end, label in segments:
        seg_chars = _char_count(lines, seg_start, seg_end)
        if seg_chars > chars_per_page * 1.3 and (seg_end - seg_start) > 10:
            # Split at paragraph boundaries
            blanks = _find_blank_lines(lines, seg_start, seg_end)
            if blanks:
                chunk_start = seg_start
                chunk_chars = 0
                for i in range(seg_start, seg_end):
                    chunk_chars += len(lines[i])
                    if chunk_chars >= chars_per_page and i in blanks:
                        split_segments.append((chunk_start, i + 1, label))
                        chunk_start = i + 1
                        chunk_chars = 0
                if chunk_start < seg_end:
                    split_segments.append((chunk_start, seg_end, label))
            else:
                split_segments.append((seg_start, seg_end, label))
        else:
            split_segments.append((seg_start, seg_end, label))

    return split_segments


def _paginate_with_headings(
    lines: list[str],
    h2_positions: list[int],
    chars_per_page: int,
    max_pages: int,
) -> list[tuple[int, int]]:
    """Paginate using H2 headings as anchors, splitting large sections."""
    segments = _build_segments(lines, h2_positions, chars_per_page)
    return _pack_segments_to_pages(segments, lines, chars_per_page, max_pages)


def _pack_segments_to_pages(
    segments: list[tuple[int, int, str]],
    lines: list[str],
    chars_per_page: int,
    max_pages: int,
) -> list[tuple[int, int]]:
    """Greedily pack segments into pages."""
    pages: list[tuple[int, int]] = []
    page_start = segments[0][0]
    page_end = segments[0][1]
    page_chars = _char_count(lines, page_start, page_end)

    for idx in range(1, len(segments)):
        seg_start, seg_end, _label = segments[idx]
        seg_chars = _char_count(lines, seg_start, seg_end)

        if page_chars + seg_chars > chars_per_page * 1.2 and page_chars > 0:
            pages.append((page_start + 1, page_end))
            page_start = seg_start
            page_end = seg_end
            page_chars = seg_chars

            if len(pages) >= max_pages - 1:
                # Remaining segments go into the final page
                for j in range(idx + 1, len(segments)):
                    page_end = segments[j][1]
                break
        else:
            page_end = seg_end
            page_chars += seg_chars

    if page_end > page_start:
        pages.append((page_start + 1, page_end))

    pages = _merge_short_pages(pages, lines, chars_per_page)
    return pages[:max_pages]


def _merge_short_pages(
    pages: list[tuple[int, int]], lines: list[str], chars_per_page: int
) -> list[tuple[int, int]]:
    """Merge short pages (under 30% target) with their neighbors."""
    if len(pages) <= 1:
        return pages

    result = []
    i = 0
    while i < len(pages):
        curr_start, curr_end = pages[i]
        curr_chars = _char_count(lines, curr_start - 1, curr_end)

        # Try merging with next if very short and next exists
        if curr_chars < chars_per_page * 0.35 and i + 1 < len(pages):
            next_start, next_end = pages[i + 1]
            combined_chars = _char_count(lines, curr_start - 1, next_end)
            if combined_chars < chars_per_page * 2.5:
                result.append((curr_start, next_end))
                i += 2
                continue

        # Try merging with previous if short
        if curr_chars < chars_per_page * 0.3 and result:
            prev_start, prev_end = result[-1]
            combined_chars = _char_count(lines, prev_start - 1, curr_end)
            if combined_chars < chars_per_page * 2.5:
                result[-1] = (prev_start, curr_end)
                i += 1
                continue

        result.append((curr_start, curr_end))
        i += 1

    return result


def _paginate_flat(
    lines: list[str], chars_per_page: int, max_pages: int
) -> list[tuple[int, int]]:
    """Split by paragraph boundaries when no H2 headings exist."""
    blanks = _find_blank_lines(lines, 0, len(lines))

    if not blanks:
        per_page = max(1, len(lines) // max_pages)
        result = []
        for p in range(max_pages):
            start = p * per_page
            end = min(len(lines), (p + 1) * per_page)
            if start < len(lines):
                result.append((start + 1, end))
        return result

    pages = []
    current_start = 0
    current_chars = 0

    for i, line in enumerate(lines):
        current_chars += len(line)

        if current_chars >= chars_per_page and i in blanks:
            pages.append((current_start + 1, i))
            current_start = i + 1
            current_chars = 0
            if len(pages) >= max_pages - 1:
                break

    if current_start < len(lines):
        pages.append((current_start + 1, len(lines)))

    return pages[:max_pages]


def resolve_pages(
    lines: list[str],
    manual_pages: list[tuple[int, int]] | None = None,
    auto: bool = False,
    chars_per_page: int = 800,
    split_on_headings: bool = True,
    max_pages: int = 25,
) -> list[tuple[int, int]]:
    """Resolve page ranges from manual config or auto-detection."""
    if manual_pages and not auto:
        return manual_pages

    return auto_paginate("\n".join(lines), chars_per_page, split_on_headings, max_pages)
