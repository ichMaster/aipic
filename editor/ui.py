import curses
import json

from . import markdown_renderer

VERSION = "1.0"
EXPLORER_WIDTH = 30
TERMINAL_WIDTH = 80

SHORTCUTS_ROW1 = [
    ("^O", "Write Out"),
    ("^X", "Exit"),
    ("^W", "Where Is"),
    ("^K", "Cut"),
    ("^U", "Paste"),
]

SHORTCUTS_ROW2 = [
    ("^Y", "Prev Page"),
    ("^V", "Next Page"),
    ("^T", "Explorer"),
    ("^B", "Terminal"),
    ("^A", "Home"),
]


class UI:
    """Screen rendering: title bar, content, status bar, shortcut bar, explorer."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.setup_colors()
        self.update_dimensions()

    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Title/status bar
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Shortcut bar
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Shortcut keys
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Content area
        markdown_renderer.setup_colors()
        curses.init_pair(12, curses.COLOR_CYAN, curses.COLOR_BLACK)    # inv header
        curses.init_pair(13, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # inv key
        curses.init_pair(14, curses.COLOR_WHITE, curses.COLOR_BLACK)   # inv value
        curses.init_pair(15, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # inv checked header
        self.stdscr.bkgd(' ', curses.color_pair(4))

    def update_dimensions(self, terminal_visible=True):
        self.height, self.width = self.stdscr.getmaxyx()
        self.explorer_width = min(EXPLORER_WIDTH, self.width // 4)
        self.content_start_col = self.explorer_width + 1  # +1 for separator
        self.terminal_visible = terminal_visible
        if terminal_visible:
            self.terminal_width = min(TERMINAL_WIDTH, self.width // 3)
            self.terminal_start_col = self.width - self.terminal_width
            self.content_width = self.terminal_start_col - 1 - self.content_start_col
        else:
            self.terminal_width = 0
            self.terminal_start_col = self.width
            self.content_width = self.width - self.content_start_col
        self.content_height = self.height - 4  # 1 title + 1 status + 2 shortcuts
        self.content_start_row = 1

    def draw_title_bar(self, filename, modified):
        title_left = f" Aipic {VERSION}"
        title_center = filename or "[New Buffer]"
        title_right = " Modified " if modified else ""

        bar = title_left
        padding = self.width - len(title_left) - len(title_center) - len(title_right)
        if padding > 0:
            left_pad = padding // 2
            right_pad = padding - left_pad
            bar = title_left + " " * left_pad + title_center + " " * right_pad + title_right
        else:
            bar = (title_left + " " + title_center + " " + title_right)

        bar = bar[:self.width]
        bar = bar.ljust(self.width)

        try:
            self.stdscr.addnstr(0, 0, bar, self.width, curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass

    def draw_explorer(self, explorer, focus):
        is_focused = (focus == "explorer")
        ew = self.explorer_width

        # Draw directory header
        dir_display = explorer.current_dir
        if len(dir_display) > ew - 1:
            dir_display = "..." + dir_display[-(ew - 4):]
        dir_display = " " + dir_display
        dir_display = dir_display[:ew].ljust(ew)
        header_attr = curses.color_pair(1) | curses.A_BOLD if is_focused else curses.color_pair(1)
        try:
            self.stdscr.addnstr(self.content_start_row, 0, dir_display, ew, header_attr)
        except curses.error:
            pass

        # Draw entries
        list_height = self.content_height - 1  # -1 for header
        explorer.adjust_scroll(list_height)

        for i in range(list_height):
            screen_row = self.content_start_row + 1 + i
            entry_idx = explorer.scroll_offset + i

            if entry_idx < len(explorer.entries):
                name, is_dir, _ = explorer.entries[entry_idx]
                if is_dir and name != "..":
                    display = " " + name + "/"
                else:
                    display = " " + name
                display = display[:ew].ljust(ew)

                if entry_idx == explorer.selected_index:
                    attr = curses.color_pair(4) | curses.A_REVERSE
                else:
                    attr = curses.color_pair(4)
                try:
                    self.stdscr.addnstr(screen_row, 0, display, ew, attr)
                except curses.error:
                    pass
            else:
                try:
                    self.stdscr.addnstr(screen_row, 0, " " * ew, ew, curses.color_pair(4))
                except curses.error:
                    pass

        # Draw vertical separator
        for i in range(self.content_height):
            screen_row = self.content_start_row + i
            try:
                self.stdscr.addch(screen_row, ew, curses.ACS_VLINE, curses.color_pair(4))
            except curses.error:
                pass

    def draw_content(self, buffer, scroll_row, scroll_col, cursor_row, cursor_col):
        for i in range(self.content_height):
            screen_row = self.content_start_row + i
            buf_row = scroll_row + i

            try:
                # Clear content area (from content_start_col to content end)
                clear_text = " " * max(0, self.content_width)
                self.stdscr.addnstr(screen_row, self.content_start_col,
                                    clear_text, self.content_width)
            except curses.error:
                pass

            if buf_row < buffer.line_count:
                line = buffer.get_line(buf_row)
                visible = line[scroll_col:scroll_col + self.content_width]
                try:
                    self.stdscr.addnstr(screen_row, self.content_start_col,
                                        visible, self.content_width)
                except curses.error:
                    pass

    def draw_markdown_content(self, rendered_lines, scroll_row):
        for i in range(self.content_height):
            screen_row = self.content_start_row + i
            line_idx = scroll_row + i

            try:
                clear_text = " " * max(0, self.content_width)
                self.stdscr.addnstr(screen_row, self.content_start_col,
                                    clear_text, self.content_width)
            except curses.error:
                pass

            if line_idx < len(rendered_lines):
                rl = rendered_lines[line_idx]
                col = self.content_start_col
                for text, attr, _ in rl.spans:
                    remaining = self.content_width - (col - self.content_start_col)
                    if remaining <= 0:
                        break
                    display = text[:remaining]
                    try:
                        self.stdscr.addnstr(screen_row, col, display, remaining, attr)
                    except curses.error:
                        pass
                    col += len(display)

    def _draw_inv_header(self, columns, mark_col=True, header_cp=12):
        """Draw table header row with optional check-mark column."""
        cw = self.content_width
        sc = self.content_start_col
        header_row = self.content_start_row

        try:
            self.stdscr.addnstr(header_row, sc, " " * cw, cw, curses.color_pair(header_cp))
        except curses.error:
            pass

        col = sc
        if mark_col:
            try:
                self.stdscr.addnstr(header_row, col, "   ", 3,
                                    curses.color_pair(header_cp) | curses.A_BOLD)
            except curses.error:
                pass
            col += 3

        for c in columns:
            w = min(c["width"], cw - (col - sc))
            if w <= 0:
                break
            text = f" {c['label']:<{w - 1}}"[:w]
            try:
                self.stdscr.addnstr(header_row, col, text, w,
                                    curses.color_pair(header_cp) | curses.A_BOLD)
            except curses.error:
                pass
            col += w

        # Separator
        sep_row = self.content_start_row + 1
        try:
            self.stdscr.addnstr(sep_row, sc, "─" * cw, cw,
                                curses.color_pair(header_cp) | curses.A_DIM)
        except curses.error:
            pass

    def draw_inv_table(self, inv_viewer):
        columns = inv_viewer.columns
        cw = self.content_width
        sc = self.content_start_col

        self._draw_inv_header(columns, mark_col=True)

        list_height = self.content_height - 2
        inv_viewer.adjust_scroll(list_height)

        for i in range(list_height):
            screen_row = self.content_start_row + 2 + i
            rec_idx = inv_viewer.scroll_offset + i

            try:
                self.stdscr.addnstr(screen_row, sc, " " * cw, cw, curses.color_pair(4))
            except curses.error:
                pass

            if rec_idx < len(inv_viewer.records):
                record = inv_viewer.records[rec_idx]
                is_cursor = (rec_idx == inv_viewer.selected_index)
                is_checked = (rec_idx in inv_viewer.checked)
                attr = curses.color_pair(4) | curses.A_REVERSE if is_cursor else curses.color_pair(4)

                # Check mark column
                mark = " ✓ " if is_checked else "   "
                mark_attr = curses.color_pair(12) | curses.A_BOLD if is_checked else attr
                if is_cursor:
                    mark_attr = curses.color_pair(4) | curses.A_REVERSE
                try:
                    self.stdscr.addnstr(screen_row, sc, mark, 3, mark_attr)
                except curses.error:
                    pass

                col = sc + 3
                for c in columns:
                    w = min(c["width"], cw - (col - sc))
                    if w <= 0:
                        break
                    val = str(record.get(c["field"], ""))
                    text = f" {val:<{w - 1}}"[:w]
                    try:
                        self.stdscr.addnstr(screen_row, col, text, w, attr)
                    except curses.error:
                        pass
                    col += w

    def draw_inv_checked_table(self, inv_viewer):
        """Draw table showing only checked records."""
        columns = inv_viewer.columns
        cw = self.content_width
        sc = self.content_start_col
        checked_records = inv_viewer.get_checked_records()

        self._draw_inv_header(columns, mark_col=True, header_cp=15)

        list_height = self.content_height - 2
        inv_viewer.adjust_checked_scroll(list_height)

        for i in range(list_height):
            screen_row = self.content_start_row + 2 + i
            rec_idx = inv_viewer._checked_scroll + i

            try:
                self.stdscr.addnstr(screen_row, sc, " " * cw, cw, curses.color_pair(4))
            except curses.error:
                pass

            if rec_idx < len(checked_records):
                record = checked_records[rec_idx]
                is_cursor = (rec_idx == inv_viewer._checked_cursor)
                is_unchecked = inv_viewer.is_unchecked_in_view(rec_idx)
                if is_cursor:
                    attr = curses.color_pair(4) | curses.A_REVERSE
                elif is_unchecked:
                    attr = curses.color_pair(4) | curses.A_DIM
                else:
                    attr = curses.color_pair(4)

                # Show check/uncheck marker
                marker = "   " if is_unchecked else " ✓ "
                try:
                    self.stdscr.addnstr(screen_row, sc, marker, 3, attr)
                except curses.error:
                    pass

                col = sc + 3
                for c in columns:
                    w = min(c["width"], cw - (col - sc))
                    if w <= 0:
                        break
                    val = str(record.get(c["field"], ""))
                    text = f" {val:<{w - 1}}"[:w]
                    try:
                        self.stdscr.addnstr(screen_row, col, text, w, attr)
                    except curses.error:
                        pass
                    col += w

    def draw_inv_detail(self, inv_viewer):
        cw = self.content_width
        sc = self.content_start_col
        if inv_viewer.checked_view:
            record = inv_viewer.get_checked_selected_record()
        else:
            record = inv_viewer.get_selected_record()
        if not record:
            return

        # Header: record identifier
        header_row = self.content_start_row
        name = str(record.get("object_name", record.get("pipeline_item_name", "Record")))
        header_text = f" Record: {name}"
        try:
            self.stdscr.addnstr(header_row, sc, header_text.ljust(cw)[:cw], cw,
                                curses.color_pair(12) | curses.A_BOLD)
        except curses.error:
            pass

        # Build detail lines (key-value pairs, multi-line values expanded)
        detail_lines = []
        max_key_len = max(len(k) for k in record.keys()) if record else 0
        for key, value in record.items():
            val_str = self._format_inv_value(value)
            val_lines = val_str.split("\n")
            detail_lines.append(("key", key, val_lines[0], max_key_len))
            for extra in val_lines[1:]:
                detail_lines.append(("cont", "", extra, max_key_len))

        # Clamp scroll
        visible = self.content_height - 1  # -1 for header
        max_scroll = max(0, len(detail_lines) - visible)
        if inv_viewer.detail_scroll > max_scroll:
            inv_viewer.detail_scroll = max_scroll

        for i in range(visible):
            screen_row = self.content_start_row + 1 + i
            line_idx = inv_viewer.detail_scroll + i

            # Clear
            try:
                self.stdscr.addnstr(screen_row, sc, " " * cw, cw, curses.color_pair(4))
            except curses.error:
                pass

            if line_idx < len(detail_lines):
                kind, key, val, mkl = detail_lines[line_idx]
                if kind == "key":
                    key_text = f"  {key:>{mkl}} : "
                    try:
                        self.stdscr.addnstr(screen_row, sc, key_text,
                                            min(len(key_text), cw),
                                            curses.color_pair(13) | curses.A_BOLD)
                    except curses.error:
                        pass
                    val_col = sc + len(key_text)
                    val_w = cw - len(key_text)
                    if val_w > 0:
                        try:
                            self.stdscr.addnstr(screen_row, val_col,
                                                val[:val_w], val_w,
                                                curses.color_pair(14))
                        except curses.error:
                            pass
                else:
                    indent = mkl + 5  # align with value column
                    val_col = sc + indent
                    val_w = cw - indent
                    if val_w > 0:
                        try:
                            self.stdscr.addnstr(screen_row, val_col,
                                                val[:val_w], val_w,
                                                curses.color_pair(14))
                        except curses.error:
                            pass

    def _format_inv_value(self, value):
        if value is None:
            return "—"
        if isinstance(value, str) and value.startswith("{"):
            try:
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, TypeError):
                pass
        return str(value)

    def draw_terminal(self, terminal, focus):
        if not self.terminal_visible:
            return

        is_focused = (focus == "terminal")
        tw = self.terminal_width
        sep_col = self.terminal_start_col - 1

        # Draw vertical separator
        for i in range(self.content_height):
            screen_row = self.content_start_row + i
            try:
                self.stdscr.addch(screen_row, sep_col, curses.ACS_VLINE,
                                  curses.color_pair(4))
            except curses.error:
                pass

        # Draw terminal header
        header = " Terminal"
        header = header[:tw].ljust(tw)
        header_attr = curses.color_pair(1) | curses.A_BOLD if is_focused else curses.color_pair(1)
        try:
            self.stdscr.addnstr(self.content_start_row, self.terminal_start_col,
                                header, tw, header_attr)
        except curses.error:
            pass

        # Draw terminal output
        output_height = self.content_height - 1  # -1 for header
        visible_lines = terminal.get_visible_lines(output_height)

        for i in range(output_height):
            screen_row = self.content_start_row + 1 + i
            if i < len(visible_lines):
                line = visible_lines[i][:tw]
                display = line.ljust(tw)
            else:
                display = " " * tw
            try:
                self.stdscr.addnstr(screen_row, self.terminal_start_col,
                                    display, tw, curses.color_pair(4))
            except curses.error:
                pass

    def draw_status_bar(self, message=""):
        row = self.height - 3
        text = message[:self.width].ljust(self.width)
        try:
            self.stdscr.addnstr(row, 0, text, self.width, curses.color_pair(1))
        except curses.error:
            pass

    def draw_shortcut_bar(self):
        self._draw_shortcut_row(self.height - 2, SHORTCUTS_ROW1)
        self._draw_shortcut_row(self.height - 1, SHORTCUTS_ROW2)

    def _draw_shortcut_row(self, row, shortcuts):
        col = 0
        item_width = self.width // len(shortcuts)

        for key, label in shortcuts:
            if col >= self.width:
                break
            try:
                self.stdscr.addnstr(row, col, key, self.width - col,
                                    curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass
            col += len(key)

            display_label = " " + label
            remaining = item_width - len(key)
            display_label = display_label.ljust(remaining)
            try:
                self.stdscr.addnstr(row, col, display_label, self.width - col,
                                    curses.color_pair(2))
            except curses.error:
                pass
            col += remaining

    def position_cursor(self, focus, cursor_row, cursor_col, scroll_row, scroll_col,
                        explorer_selected=0, explorer_scroll=0, terminal=None):
        if focus == "editor":
            screen_row = self.content_start_row + (cursor_row - scroll_row)
            screen_col = self.content_start_col + (cursor_col - scroll_col)
        elif focus == "terminal" and terminal is not None:
            term_cursor_row, term_cursor_col = terminal.cursor_pos
            screen_row = self.content_start_row + 1 + term_cursor_row
            screen_col = self.terminal_start_col + term_cursor_col
        else:
            # Position cursor on selected explorer entry
            screen_row = self.content_start_row + 1 + (explorer_selected - explorer_scroll)
            screen_col = 1
        try:
            self.stdscr.move(screen_row, screen_col)
        except curses.error:
            pass

    def get_input(self, prompt):
        """Show a prompt on the status bar and read a string."""
        row = self.height - 3
        try:
            self.stdscr.addnstr(row, 0, prompt.ljust(self.width), self.width,
                                curses.color_pair(1))
        except curses.error:
            pass
        self.stdscr.refresh()

        curses.echo()
        curses.curs_set(1)
        result = ""
        try:
            self.stdscr.move(row, len(prompt))
            buf = []
            while True:
                ch = self.stdscr.getch()
                if ch in (10, 13, curses.KEY_ENTER):
                    break
                elif ch == 27:  # Escape
                    curses.noecho()
                    return None
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    if buf:
                        buf.pop()
                        self.stdscr.addnstr(row, 0, (prompt + "".join(buf)).ljust(self.width),
                                            self.width, curses.color_pair(1))
                        self.stdscr.move(row, len(prompt) + len(buf))
                elif 32 <= ch <= 126:
                    buf.append(chr(ch))
                    try:
                        self.stdscr.addch(row, len(prompt) + len(buf) - 1, ch,
                                          curses.color_pair(1))
                    except curses.error:
                        pass
            result = "".join(buf)
        finally:
            curses.noecho()
        return result

    def get_yes_no_cancel(self, prompt):
        """Show prompt, return 'y', 'n', or 'c' (cancel)."""
        row = self.height - 3
        try:
            self.stdscr.addnstr(row, 0, prompt.ljust(self.width), self.width,
                                curses.color_pair(1))
        except curses.error:
            pass
        self.stdscr.refresh()

        while True:
            ch = self.stdscr.getch()
            if ch in (ord('y'), ord('Y')):
                return 'y'
            elif ch in (ord('n'), ord('N')):
                return 'n'
            elif ch == 27 or ch in (ord('c'), ord('C')):
                return 'c'

    def refresh(self):
        self.stdscr.noutrefresh()
        curses.doupdate()
