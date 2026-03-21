"""Markdown renderer for curses — converts markdown to styled lines."""

import re
import curses

# Color pair IDs (assigned in ui.py setup_colors)
CP_NORMAL = 4
CP_HEADER = 5
CP_BOLD = 6
CP_CODE = 7
CP_LINK = 8
CP_BULLET = 9
CP_HRULE = 10
CP_BLOCKQUOTE = 11

# Span types for inline formatting
SPAN_NORMAL = "normal"
SPAN_BOLD = "bold"
SPAN_ITALIC = "italic"
SPAN_CODE = "code"
SPAN_LINK_TEXT = "link_text"
SPAN_LINK_URL = "link_url"


def setup_colors():
    """Initialize color pairs for markdown rendering. Call after curses.start_color()."""
    curses.init_pair(CP_HEADER, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(CP_BOLD, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(CP_CODE, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(CP_LINK, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(CP_BULLET, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(CP_HRULE, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(CP_BLOCKQUOTE, curses.COLOR_MAGENTA, curses.COLOR_BLACK)


class RenderedLine:
    """A single rendered line with styled spans."""

    def __init__(self, spans=None, indent=0):
        self.spans = spans or []  # list of (text, color_pair, attrs)
        self.indent = indent

    def plain_length(self):
        return self.indent + sum(len(s[0]) for s in self.spans)


def render_markdown(lines):
    """Convert a list of raw markdown lines to a list of RenderedLine objects."""
    rendered = []
    in_code_block = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Code block toggle
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                lang = line.strip()[3:].strip()
                rl = RenderedLine(indent=2)
                rl.spans.append((f"  ┌─ {lang or 'code'} ", curses.color_pair(CP_CODE) | curses.A_DIM, 0))
                rendered.append(rl)
            else:
                rl = RenderedLine(indent=2)
                rl.spans.append(("  └─────", curses.color_pair(CP_CODE) | curses.A_DIM, 0))
                rendered.append(rl)
            i += 1
            continue

        if in_code_block:
            rl = RenderedLine(indent=4)
            rl.spans.append(("  │ " + line, curses.color_pair(CP_CODE), 0))
            rendered.append(rl)
            i += 1
            continue

        stripped = line.strip()

        # Empty line
        if not stripped:
            rendered.append(RenderedLine())
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            rl = RenderedLine()
            rl.spans.append(("  ────────────────────────────────────────", curses.color_pair(CP_HRULE) | curses.A_DIM, 0))
            rendered.append(rl)
            i += 1
            continue

        # Headers
        hdr_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if hdr_match:
            level = len(hdr_match.group(1))
            text = hdr_match.group(2)
            prefix = "  " + "█" * (4 - min(level, 3)) + " "
            rl = RenderedLine(indent=2)
            attrs = curses.color_pair(CP_HEADER) | curses.A_BOLD
            if level == 1:
                attrs |= curses.A_UNDERLINE
            rl.spans.append((prefix + text, attrs, 0))
            rendered.append(rl)
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            text = re.sub(r'^>\s?', '', line)
            rl = RenderedLine(indent=4)
            rl.spans.append(("  ▌ ", curses.color_pair(CP_BLOCKQUOTE) | curses.A_BOLD, 0))
            rl.spans.extend(_parse_inline(text))
            rendered.append(rl)
            i += 1
            continue

        # Unordered list
        ul_match = re.match(r'^(\s*)[*\-+]\s+(.*)', line)
        if ul_match:
            indent_level = len(ul_match.group(1)) // 2
            text = ul_match.group(2)
            prefix = "  " + "  " * indent_level + "• "
            rl = RenderedLine(indent=len(prefix))
            rl.spans.append((prefix, curses.color_pair(CP_BULLET) | curses.A_BOLD, 0))
            rl.spans.extend(_parse_inline(text))
            rendered.append(rl)
            i += 1
            continue

        # Ordered list
        ol_match = re.match(r'^(\s*)(\d+)[.)]\s+(.*)', line)
        if ol_match:
            indent_level = len(ol_match.group(1)) // 2
            num = ol_match.group(2)
            text = ol_match.group(3)
            prefix = "  " + "  " * indent_level + f"{num}. "
            rl = RenderedLine(indent=len(prefix))
            rl.spans.append((prefix, curses.color_pair(CP_BULLET) | curses.A_BOLD, 0))
            rl.spans.extend(_parse_inline(text))
            rendered.append(rl)
            i += 1
            continue

        # Table
        if "|" in line and i + 1 < len(lines) and re.match(r'^\s*\|?[\s\-:|]+\|', lines[i + 1]):
            rendered.extend(_render_table(lines, i))
            # Skip past table
            while i < len(lines) and "|" in lines[i]:
                i += 1
            continue

        # Normal paragraph
        rl = RenderedLine(indent=2)
        rl.spans.append(("  ", curses.color_pair(CP_NORMAL), 0))
        rl.spans.extend(_parse_inline(line))
        rendered.append(rl)
        i += 1

    return rendered


def _parse_inline(text):
    """Parse inline markdown (bold, italic, code, links) into spans."""
    spans = []
    pattern = re.compile(
        r'(`[^`]+`)'            # inline code
        r'|(\*\*\S.*?\S\*\*)'   # bold
        r'|(__\S.*?\S__)'       # bold alt
        r'|(\*\S.*?\S\*)'       # italic
        r'|(_\S.*?\S_)'         # italic alt
        r'|\[([^\]]+)\]\(([^)]+)\)'  # link
    )
    last_end = 0
    for m in pattern.finditer(text):
        # Text before match
        if m.start() > last_end:
            spans.append((text[last_end:m.start()], curses.color_pair(CP_NORMAL), 0))

        if m.group(1):  # inline code
            code_text = m.group(1)[1:-1]
            spans.append((f" {code_text} ", curses.color_pair(CP_CODE) | curses.A_REVERSE, 0))
        elif m.group(2):  # bold **
            spans.append((m.group(2)[2:-2], curses.color_pair(CP_BOLD) | curses.A_BOLD, 0))
        elif m.group(3):  # bold __
            spans.append((m.group(3)[2:-2], curses.color_pair(CP_BOLD) | curses.A_BOLD, 0))
        elif m.group(4):  # italic *
            spans.append((m.group(4)[1:-1], curses.color_pair(CP_NORMAL) | curses.A_ITALIC, 0))
        elif m.group(5):  # italic _
            spans.append((m.group(5)[1:-1], curses.color_pair(CP_NORMAL) | curses.A_ITALIC, 0))
        elif m.group(6):  # link
            spans.append((m.group(6), curses.color_pair(CP_LINK) | curses.A_UNDERLINE, 0))
            spans.append((f" ({m.group(7)})", curses.color_pair(CP_LINK) | curses.A_DIM, 0))

        last_end = m.end()

    # Remaining text
    if last_end < len(text):
        spans.append((text[last_end:], curses.color_pair(CP_NORMAL), 0))

    return spans


def _strip_inline_markers(text):
    """Return visible text length after removing markdown markers."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text


def _parse_inline_with_attr(text, base_attr):
    """Parse inline markdown, using base_attr for normal text instead of CP_NORMAL."""
    spans = _parse_inline(text)
    result = []
    for txt, attr, extra in spans:
        if attr == curses.color_pair(CP_NORMAL):
            result.append((txt, base_attr, extra))
        else:
            result.append((txt, attr, extra))
    return result


def _render_table(lines, start_idx):
    """Render a markdown table with box drawing."""
    rendered = []
    table_lines = []
    i = start_idx
    while i < len(lines) and "|" in lines[i]:
        table_lines.append(lines[i])
        i += 1

    if len(table_lines) < 2:
        return rendered

    # Parse cells
    rows = []
    for tl in table_lines:
        cells = [c.strip() for c in tl.strip().strip("|").split("|")]
        rows.append(cells)

    # Skip separator row
    header = rows[0]
    data_rows = rows[2:] if len(rows) > 2 else []

    # Calculate column widths based on visible text (strip markdown markers)
    all_rows = [header] + data_rows
    col_count = max(len(r) for r in all_rows)
    widths = [0] * col_count
    for row in all_rows:
        for j, cell in enumerate(row):
            if j < col_count:
                visible_len = len(_strip_inline_markers(cell))
                widths[j] = max(widths[j], visible_len)

    # Draw header
    rl = RenderedLine(indent=2)
    rl.spans.append(("  ", curses.color_pair(CP_NORMAL), 0))
    for j, cell in enumerate(header):
        w = widths[j] if j < len(widths) else len(cell)
        rl.spans.append((" ", curses.color_pair(CP_HEADER) | curses.A_BOLD, 0))
        rl.spans.extend(_parse_inline_with_attr(cell, curses.color_pair(CP_HEADER) | curses.A_BOLD))
        padding = w - len(_strip_inline_markers(cell))
        if padding > 0:
            rl.spans.append((" " * (padding + 1), curses.color_pair(CP_HEADER) | curses.A_BOLD, 0))
        else:
            rl.spans.append((" ", curses.color_pair(CP_HEADER) | curses.A_BOLD, 0))
        if j < len(header) - 1:
            rl.spans.append(("│", curses.color_pair(CP_HRULE) | curses.A_DIM, 0))
    rendered.append(rl)

    # Draw separator
    rl = RenderedLine(indent=2)
    rl.spans.append(("  ", curses.color_pair(CP_NORMAL), 0))
    sep_parts = []
    for j, w in enumerate(widths):
        sep_parts.append("─" * (w + 2))
    rl.spans.append(("┼".join(sep_parts), curses.color_pair(CP_HRULE) | curses.A_DIM, 0))
    rendered.append(rl)

    # Draw data rows
    for row in data_rows:
        rl = RenderedLine(indent=2)
        rl.spans.append(("  ", curses.color_pair(CP_NORMAL), 0))
        for j in range(col_count):
            cell = row[j] if j < len(row) else ""
            w = widths[j]
            rl.spans.append((" ", curses.color_pair(CP_NORMAL), 0))
            rl.spans.extend(_parse_inline(cell))
            padding = w - len(_strip_inline_markers(cell))
            if padding > 0:
                rl.spans.append((" " * (padding + 1), curses.color_pair(CP_NORMAL), 0))
            else:
                rl.spans.append((" ", curses.color_pair(CP_NORMAL), 0))
            if j < col_count - 1:
                rl.spans.append(("│", curses.color_pair(CP_HRULE) | curses.A_DIM, 0))
        rendered.append(rl)

    return rendered
