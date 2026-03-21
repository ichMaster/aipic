import curses
import json
import os

from .buffer import Buffer
from .clipboard import Clipboard
from .search import Search
from .keybindings import get_command, CMD_MOVE_UP, CMD_MOVE_DOWN, CMD_MOVE_LEFT, CMD_MOVE_RIGHT
from .keybindings import CMD_HOME, CMD_END, CMD_PAGE_UP, CMD_PAGE_DOWN
from .keybindings import CMD_BACKSPACE, CMD_DELETE, CMD_ENTER, CMD_TAB
from .keybindings import CMD_SAVE, CMD_EXIT, CMD_SEARCH, CMD_CUT, CMD_PASTE
from .keybindings import CMD_REFRESH, CMD_RESIZE, CMD_INSERT, CMD_TOGGLE_EXPLORER
from .keybindings import CMD_TOGGLE_TERMINAL, CMD_TOGGLE_MD_VIEW, CMD_TOGGLE_CHECKED_VIEW
from .explorer import FileExplorer
from .inv_viewer import InvViewer
from .markdown_renderer import render_markdown
from .terminal import Terminal
from .ui import UI


class Editor:
    """Core editor: state management, key dispatch, main loop."""

    def __init__(self, stdscr, filepath=None):
        self.stdscr = stdscr
        self.filepath = filepath
        self.ui = UI(stdscr)
        self.clipboard = Clipboard()
        self.search = Search()
        self.explorer = FileExplorer(
            os.path.dirname(os.path.abspath(filepath)) if filepath else None
        )
        self.terminal = Terminal()
        self.terminal.start()
        self.focus = "editor"

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
        self.md_view_mode = self._is_markdown()
        self.md_rendered = None
        self.md_scroll_row = 0
        if self.md_view_mode:
            self._render_markdown()
        self.inv_viewer = InvViewer.from_file(self.filepath)

    def run(self):
        self.stdscr.keypad(True)
        curses.curs_set(1)
        curses.raw()
        self.stdscr.timeout(50)

        try:
            while self.running:
                self.terminal.read_output()
                self._draw()
                key = self.stdscr.getch()
                if key == -1:
                    continue
                self._handle_key(key)
        finally:
            self.terminal.stop()

    def _is_markdown(self):
        return bool(self.filepath and self.filepath.lower().endswith(('.md', '.markdown')))

    def _render_markdown(self):
        self.md_rendered = render_markdown(self.buffer.lines)

    def _draw(self):
        self.stdscr.erase()
        self.ui.update_dimensions(terminal_visible=True)
        self.terminal.resize(self.ui.content_height - 1, self.ui.terminal_width)
        self._adjust_scroll()
        self.ui.draw_title_bar(self.filepath, self.buffer.modified)
        self.ui.draw_explorer(self.explorer, self.focus)

        if self.focus == "terminal":
            curses.curs_set(1)

        if self.inv_viewer is not None:
            iv = self.inv_viewer
            if self.focus != "terminal":
                curses.curs_set(0)
            chk = iv.get_checked_count()
            if iv.detail_mode:
                self.ui.draw_inv_detail(iv)
                mode_indicator = " [DETAIL] Enter=Back F5=All"
            elif iv.checked_view:
                self.ui.draw_inv_checked_table(iv)
                sel = iv._checked_cursor + 1
                n = len(iv._checked_list)
                kept = iv.get_selected_count()
                mode_indicator = f" [FILTERED {sel}/{n} kept:{kept}] Space=Unselect Enter=Detail F5=All"
            else:
                self.ui.draw_inv_table(iv)
                n = len(iv.records)
                sel = iv.selected_index + 1
                chk_text = f" ✓{chk}" if chk else ""
                mode_indicator = f" [TABLE {sel}/{n}{chk_text}] Space=Select Enter=Detail F6=Filter"
        elif self.md_view_mode and self.md_rendered is not None:
            self.ui.draw_markdown_content(self.md_rendered, self.md_scroll_row)
            if self.focus == "editor":
                curses.curs_set(0)
            mode_indicator = " [VIEW] F5=Edit"
        else:
            if self.focus == "editor":
                curses.curs_set(1)
            self.ui.draw_content(self.buffer, self.scroll_row, self.scroll_col,
                                 self.cursor_row, self.cursor_col)
            mode_indicator = ""

        self.ui.draw_terminal(self.terminal, self.focus)
        status = self.status_message if self.status_message else mode_indicator
        self.ui.draw_status_bar(status)
        self.ui.draw_shortcut_bar()

        if self.inv_viewer is None and not self.md_view_mode:
            self.ui.position_cursor(self.focus, self.cursor_row, self.cursor_col,
                                    self.scroll_row, self.scroll_col,
                                    self.explorer.selected_index,
                                    self.explorer.scroll_offset,
                                    self.terminal)
        else:
            self.ui.position_cursor(self.focus, 0, 0, 0, 0,
                                    self.explorer.selected_index,
                                    self.explorer.scroll_offset,
                                    self.terminal)
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
        elif self.cursor_col >= self.scroll_col + self.ui.content_width:
            self.scroll_col = self.cursor_col - self.ui.content_width + 1

    def _handle_key(self, key):
        # When terminal is focused, forward most keys directly to the pty
        if self.focus == "terminal":
            cmd, ch = get_command(key)
            if cmd == CMD_TOGGLE_TERMINAL:
                self._toggle_terminal()
                return
            if cmd == CMD_TOGGLE_EXPLORER:
                self._toggle_focus()
                return
            if cmd == CMD_EXIT:
                self._exit()
                return
            if cmd == CMD_RESIZE:
                self._resize()
                return
            # Forward special keys as escape sequences
            special_map = {
                CMD_MOVE_UP: "up", CMD_MOVE_DOWN: "down",
                CMD_MOVE_LEFT: "left", CMD_MOVE_RIGHT: "right",
                CMD_HOME: "home", CMD_END: "end",
                CMD_DELETE: "delete",
                CMD_PAGE_UP: "page_up", CMD_PAGE_DOWN: "page_down",
            }
            if cmd in special_map:
                self.terminal.send_special_key(special_map[cmd])
            elif cmd == CMD_ENTER:
                self.terminal.send_key(13)
            elif cmd == CMD_TAB:
                self.terminal.send_key(9)
            elif cmd == CMD_BACKSPACE:
                self.terminal.send_key(127)
            elif key < 256:
                self.terminal.send_key(key)
            return

        cmd, ch = get_command(key)
        if cmd is None:
            return

        # Toggle focus works in both modes
        if cmd == CMD_TOGGLE_EXPLORER:
            self._toggle_focus()
            return

        if cmd == CMD_TOGGLE_TERMINAL:
            self._toggle_terminal()
            return

        # In inv viewer mode, handle navigation (must be before md view toggle)
        if self.inv_viewer is not None and self.focus == "editor":
            iv = self.inv_viewer
            vh = self.ui.content_height - 2
            if cmd == CMD_TOGGLE_MD_VIEW:  # F5 = back to all records
                iv.detail_mode = False
                if iv.checked_view:
                    iv.checked_view = False
            elif cmd == CMD_TOGGLE_CHECKED_VIEW:  # F6 = filter to selected
                if not iv.detail_mode and not iv.checked_view:
                    if not iv.toggle_checked_view():
                        self.status_message = "No records selected (use Space to select)"
            elif cmd == CMD_INSERT and ch == " ":
                iv.toggle_check()
            elif cmd == CMD_ENTER:
                if iv.detail_mode:
                    iv.detail_mode = False  # back to table/filtered
                else:
                    iv.toggle_detail()  # enter detail
            elif cmd == CMD_MOVE_DOWN:
                if iv.checked_view:
                    iv.checked_move_down()
                else:
                    iv.move_down(vh)
            elif cmd == CMD_MOVE_UP:
                if iv.checked_view:
                    iv.checked_move_up()
                else:
                    iv.move_up()
            elif cmd == CMD_PAGE_DOWN:
                if iv.checked_view:
                    iv.checked_page_down(vh)
                else:
                    iv.page_down(vh)
            elif cmd == CMD_PAGE_UP:
                if iv.checked_view:
                    iv.checked_page_up(vh)
                else:
                    iv.page_up(vh)
            elif cmd == CMD_HOME:
                iv.home()
            elif cmd == CMD_END:
                iv.end()
            elif cmd == CMD_SAVE:
                self._save_checked_records()
            elif cmd in (CMD_EXIT, CMD_REFRESH, CMD_RESIZE):
                global_handlers = {
                    CMD_EXIT: self._exit,
                    CMD_REFRESH: self._refresh,
                    CMD_RESIZE: self._resize,
                }
                global_handlers[cmd]()
            return

        if cmd == CMD_TOGGLE_MD_VIEW:
            self._toggle_md_view()
            return

        # In markdown view mode, only allow scrolling and mode toggle
        if self.md_view_mode and self.focus == "editor":
            if cmd == CMD_MOVE_DOWN:
                max_scroll = max(0, len(self.md_rendered) - self.ui.content_height)
                self.md_scroll_row = min(self.md_scroll_row + 1, max_scroll)
            elif cmd == CMD_MOVE_UP:
                self.md_scroll_row = max(0, self.md_scroll_row - 1)
            elif cmd == CMD_PAGE_DOWN:
                max_scroll = max(0, len(self.md_rendered) - self.ui.content_height)
                self.md_scroll_row = min(self.md_scroll_row + self.ui.content_height, max_scroll)
            elif cmd == CMD_PAGE_UP:
                self.md_scroll_row = max(0, self.md_scroll_row - self.ui.content_height)
            elif cmd == CMD_HOME:
                self.md_scroll_row = 0
            elif cmd == CMD_END:
                self.md_scroll_row = max(0, len(self.md_rendered) - self.ui.content_height)
            elif cmd in (CMD_SAVE, CMD_EXIT, CMD_REFRESH, CMD_RESIZE):
                pass  # fall through to global handlers below
            else:
                return
            if cmd not in (CMD_SAVE, CMD_EXIT, CMD_REFRESH, CMD_RESIZE):
                return

        # Global commands work regardless of focus
        if cmd in (CMD_SAVE, CMD_EXIT, CMD_REFRESH, CMD_RESIZE):
            global_handlers = {
                CMD_SAVE: self._save,
                CMD_EXIT: self._exit,
                CMD_REFRESH: self._refresh,
                CMD_RESIZE: self._resize,
            }
            global_handlers[cmd]()
            return

        if self.focus == "explorer":
            self._handle_explorer_key(cmd)
        else:
            self._handle_editor_key(cmd, ch)

    def _handle_explorer_key(self, cmd):
        if cmd == CMD_MOVE_UP:
            self.explorer.move_up()
        elif cmd == CMD_MOVE_DOWN:
            self.explorer.move_down()
        elif cmd in (CMD_ENTER, CMD_MOVE_RIGHT):
            action, path = self.explorer.enter()
            if action == "open_file":
                self._open_file(path)
        elif cmd in (CMD_MOVE_LEFT, CMD_BACKSPACE):
            self.explorer.go_parent()
        elif cmd == CMD_TOGGLE_MD_VIEW:
            self.explorer.refresh_entries()
            self.status_message = "Explorer refreshed"

    def _handle_editor_key(self, cmd, ch):
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
            CMD_SEARCH: self._search,
            CMD_CUT: self._cut,
            CMD_PASTE: self._paste,
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

    def _save_checked_records(self):
        iv = self.inv_viewer
        if iv.checked_view:
            records = iv.get_selected_records()
            count = len(records)
        else:
            if not iv.checked:
                self.status_message = "No records selected"
                return
            records = [iv.records[i] for i in sorted(iv.checked)]
            count = len(records)
        if count == 0:
            self.status_message = "No records selected"
            return
        name = self.ui.get_input(f"Save {count} record(s) to: ")
        if name is None or name == "":
            self.status_message = "Cancelled"
            return
        try:
            with open(name, "w") as f:
                json.dump(records, f, indent=2)
            self.status_message = f"Saved {count} record(s) to {name}"
        except PermissionError:
            self.status_message = "Error: Permission denied"
        except OSError as e:
            self.status_message = f"Error: {e}"

    def _toggle_focus(self):
        if self.focus == "editor":
            self.focus = "explorer"
        elif self.focus == "explorer":
            self.focus = "terminal"
        else:
            self.focus = "editor"

    def _toggle_md_view(self):
        if not self._is_markdown():
            self.status_message = "Not a markdown file"
            return
        self.md_view_mode = not self.md_view_mode
        if self.md_view_mode:
            self._render_markdown()
            self.md_scroll_row = 0
            self.status_message = "View mode (F5 to edit)"
        else:
            curses.curs_set(1)
            self.status_message = "Edit mode (F5 to preview)"

    def _toggle_terminal(self):
        if self.focus == "terminal":
            self.focus = "editor"
        else:
            self.focus = "terminal"

    def _open_file(self, path):
        if not self._check_save_before_close():
            return
        self.filepath = path
        self.buffer = Buffer.from_file(path)
        self.cursor_row = 0
        self.cursor_col = 0
        self.scroll_row = 0
        self.scroll_col = 0
        self.focus = "editor"
        self.inv_viewer = InvViewer.from_file(path)
        self.md_view_mode = self._is_markdown()
        self.md_scroll_row = 0
        if self.md_view_mode:
            self._render_markdown()
        self.status_message = f"Opened {os.path.basename(path)}"

    def _check_save_before_close(self):
        """Returns True if safe to close current buffer, False if cancelled."""
        if not self.buffer.modified:
            return True
        answer = self.ui.get_yes_no_cancel(
            "Save modified buffer? (Y)es, (N)o, (C)ancel: ")
        if answer == 'y':
            self._save()
            return not self.buffer.modified  # False if save failed
        elif answer == 'n':
            return True
        return False  # cancel

    def _exit(self):
        if self._check_save_before_close():
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
        self.explorer.refresh_entries()
        self.stdscr.clear()

    def _resize(self):
        self.ui.update_dimensions(terminal_visible=self.terminal.visible)
