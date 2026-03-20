import curses

VERSION = "1.0"

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
    ("^L", "Refresh"),
    ("^A", "Home"),
    ("^E", "End"),
]


class UI:
    """Screen rendering: title bar, content, status bar, shortcut bar."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.setup_colors()
        self.update_dimensions()

    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Title/status bar
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)   # Shortcut bar
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Shortcut keys

    def update_dimensions(self):
        self.height, self.width = self.stdscr.getmaxyx()
        # Content area: between title bar (row 0) and bottom bars
        # Bottom: status bar (1 line) + shortcut bars (2 lines) = 3 lines
        self.content_height = self.height - 4  # 1 title + 1 status + 2 shortcuts
        self.content_start_row = 1

    def draw_title_bar(self, filename, modified):
        title_left = f" MyPico {VERSION}"
        title_center = filename or "[New Buffer]"
        title_right = " Modified " if modified else ""

        bar = title_left
        # Center the filename
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

    def draw_content(self, buffer, scroll_row, scroll_col, cursor_row, cursor_col):
        for i in range(self.content_height):
            screen_row = self.content_start_row + i
            buf_row = scroll_row + i

            try:
                self.stdscr.move(screen_row, 0)
                self.stdscr.clrtoeol()
            except curses.error:
                continue

            if buf_row < buffer.line_count:
                line = buffer.get_line(buf_row)
                visible = line[scroll_col:scroll_col + self.width]
                try:
                    self.stdscr.addnstr(screen_row, 0, visible, self.width)
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
            # Draw key (inverted)
            try:
                self.stdscr.addnstr(row, col, key, self.width - col,
                                    curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass
            col += len(key)

            # Draw label
            display_label = " " + label
            remaining = item_width - len(key)
            display_label = display_label.ljust(remaining)
            try:
                self.stdscr.addnstr(row, col, display_label, self.width - col,
                                    curses.color_pair(2))
            except curses.error:
                pass
            col += remaining

    def position_cursor(self, cursor_row, cursor_col, scroll_row, scroll_col):
        screen_row = self.content_start_row + (cursor_row - scroll_row)
        screen_col = cursor_col - scroll_col
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
