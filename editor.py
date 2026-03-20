import curses
import os

from buffer import Buffer
from clipboard import Clipboard
from search import Search
from keybindings import get_command, CMD_MOVE_UP, CMD_MOVE_DOWN, CMD_MOVE_LEFT, CMD_MOVE_RIGHT
from keybindings import CMD_HOME, CMD_END, CMD_PAGE_UP, CMD_PAGE_DOWN
from keybindings import CMD_BACKSPACE, CMD_DELETE, CMD_ENTER, CMD_TAB
from keybindings import CMD_SAVE, CMD_EXIT, CMD_SEARCH, CMD_CUT, CMD_PASTE
from keybindings import CMD_REFRESH, CMD_RESIZE, CMD_INSERT
from ui import UI


class Editor:
    """Core editor: state management, key dispatch, main loop."""

    def __init__(self, stdscr, filepath=None):
        self.stdscr = stdscr
        self.filepath = filepath
        self.ui = UI(stdscr)
        self.clipboard = Clipboard()
        self.search = Search()

        if filepath and os.path.exists(filepath):
            self.buffer = Buffer.from_file(filepath)
        else:
            self.buffer = Buffer()

        self.cursor_row = 0
        self.cursor_col = 0
        self.scroll_row = 0
        self.scroll_col = 0
        self.status_message = ""
        self.running = True

    def run(self):
        self.stdscr.keypad(True)
        curses.curs_set(1)
        curses.raw()
        self.stdscr.nodelay(False)

        while self.running:
            self._draw()
            key = self.stdscr.getch()
            self._handle_key(key)

    def _draw(self):
        self.stdscr.erase()
        self.ui.update_dimensions()
        self._adjust_scroll()
        self.ui.draw_title_bar(self.filepath, self.buffer.modified)
        self.ui.draw_content(self.buffer, self.scroll_row, self.scroll_col,
                             self.cursor_row, self.cursor_col)
        self.ui.draw_status_bar(self.status_message)
        self.ui.draw_shortcut_bar()
        self.ui.position_cursor(self.cursor_row, self.cursor_col,
                                self.scroll_row, self.scroll_col)
        self.ui.refresh()
        self.status_message = ""

    def _adjust_scroll(self):
        # Vertical scrolling
        if self.cursor_row < self.scroll_row:
            self.scroll_row = self.cursor_row
        elif self.cursor_row >= self.scroll_row + self.ui.content_height:
            self.scroll_row = self.cursor_row - self.ui.content_height + 1

        # Horizontal scrolling
        if self.cursor_col < self.scroll_col:
            self.scroll_col = self.cursor_col
        elif self.cursor_col >= self.scroll_col + self.ui.width:
            self.scroll_col = self.cursor_col - self.ui.width + 1

    def _handle_key(self, key):
        cmd, ch = get_command(key)
        if cmd is None:
            return

        handlers = {
            CMD_MOVE_UP: self._move_up,
            CMD_MOVE_DOWN: self._move_down,
            CMD_MOVE_LEFT: self._move_left,
            CMD_MOVE_RIGHT: self._move_right,
            CMD_HOME: self._home,
            CMD_END: self._end,
            CMD_PAGE_UP: self._page_up,
            CMD_PAGE_DOWN: self._page_down,
            CMD_BACKSPACE: self._backspace,
            CMD_DELETE: self._delete,
            CMD_ENTER: self._enter,
            CMD_TAB: self._tab,
            CMD_SAVE: self._save,
            CMD_EXIT: self._exit,
            CMD_SEARCH: self._search,
            CMD_CUT: self._cut,
            CMD_PASTE: self._paste,
            CMD_REFRESH: self._refresh,
            CMD_RESIZE: self._resize,
        }

        handler = handlers.get(cmd)
        if handler:
            handler()
        elif cmd == CMD_INSERT and ch:
            self._insert_char(ch)

    def _clamp_col(self):
        max_col = self.buffer.line_length(self.cursor_row)
        if self.cursor_col > max_col:
            self.cursor_col = max_col

    def _move_up(self):
        if self.cursor_row > 0:
            self.cursor_row -= 1
            self._clamp_col()

    def _move_down(self):
        if self.cursor_row < self.buffer.line_count - 1:
            self.cursor_row += 1
            self._clamp_col()

    def _move_left(self):
        if self.cursor_col > 0:
            self.cursor_col -= 1
        elif self.cursor_row > 0:
            self.cursor_row -= 1
            self.cursor_col = self.buffer.line_length(self.cursor_row)

    def _move_right(self):
        if self.cursor_col < self.buffer.line_length(self.cursor_row):
            self.cursor_col += 1
        elif self.cursor_row < self.buffer.line_count - 1:
            self.cursor_row += 1
            self.cursor_col = 0

    def _home(self):
        self.cursor_col = 0

    def _end(self):
        self.cursor_col = self.buffer.line_length(self.cursor_row)

    def _page_up(self):
        self.cursor_row = max(0, self.cursor_row - self.ui.content_height)
        self._clamp_col()

    def _page_down(self):
        self.cursor_row = min(self.buffer.line_count - 1,
                              self.cursor_row + self.ui.content_height)
        self._clamp_col()

    def _backspace(self):
        self.cursor_row, self.cursor_col = self.buffer.backspace(
            self.cursor_row, self.cursor_col)

    def _delete(self):
        self.buffer.delete_char(self.cursor_row, self.cursor_col)

    def _enter(self):
        self.cursor_row, self.cursor_col = self.buffer.insert_newline(
            self.cursor_row, self.cursor_col)

    def _tab(self):
        for _ in range(4):
            self.buffer.insert_char(self.cursor_row, self.cursor_col, " ")
            self.cursor_col += 1

    def _insert_char(self, ch):
        self.buffer.insert_char(self.cursor_row, self.cursor_col, ch)
        self.cursor_col += 1

    def _save(self):
        if not self.filepath:
            name = self.ui.get_input("File Name to Write: ")
            if name is None or name == "":
                self.status_message = "Cancelled"
                return
            self.filepath = name

        if os.path.exists(self.filepath) and not self.buffer.modified:
            pass  # No changes to save

        try:
            self.buffer.save(self.filepath)
            lines = self.buffer.line_count
            self.status_message = f"Wrote {lines} lines to {self.filepath}"
        except PermissionError:
            self.status_message = "Error: Permission denied"
        except OSError as e:
            self.status_message = f"Error: {e}"

    def _exit(self):
        if self.buffer.modified:
            answer = self.ui.get_yes_no_cancel(
                "Save modified buffer? (Y)es, (N)o, (C)ancel: ")
            if answer == 'y':
                self._save()
                if self.buffer.modified:
                    return  # Save failed
                self.running = False
            elif answer == 'n':
                self.running = False
            # 'c' = cancel, do nothing
        else:
            self.running = False

    def _search(self):
        prompt = "Search: "
        if self.search.last_query:
            prompt = f"Search [{self.search.last_query}]: "
        query = self.ui.get_input(prompt)

        if query is None:
            self.status_message = "Cancelled"
            return
        if query == "" and self.search.last_query:
            query = self.search.last_query
        if not query:
            return

        result = self.search.find(self.buffer, query,
                                  self.cursor_row, self.cursor_col)
        if result:
            self.cursor_row, self.cursor_col = result
            self.status_message = ""
        else:
            self.status_message = f'"{query}" not found'

    def _cut(self):
        line, self.cursor_row = self.buffer.cut_line(self.cursor_row)
        self.clipboard.cut(line, self.cursor_row)
        self._clamp_col()
        self.status_message = "Cut line"

    def _paste(self):
        lines = self.clipboard.paste()
        if not lines:
            self.status_message = "Nothing to paste"
            return
        self.buffer.insert_lines(self.cursor_row, lines)
        self.cursor_row += len(lines)
        self._clamp_col()
        self.status_message = f"Pasted {len(lines)} line(s)"

    def _refresh(self):
        self.stdscr.clear()

    def _resize(self):
        self.ui.update_dimensions()
