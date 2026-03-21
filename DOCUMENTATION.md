# Aipic - Technical Documentation

## Table of Contents

1. [Overview](#1-overview)
2. [Getting Started](#2-getting-started)
3. [Architecture](#3-architecture)
4. [Module Reference](#4-module-reference)
5. [User Interface Layout](#5-user-interface-layout)
6. [Keyboard Shortcuts](#6-keyboard-shortcuts)
7. [Focus Model](#7-focus-model)
8. [Data Flow](#8-data-flow)
9. [Dependencies](#9-dependencies)
10. [Limitations](#10-limitations)

---

## 1. Overview

Aipic is a lightweight terminal text editor inspired by GNU Pico/Nano, built in Python using the `curses` library. It provides a three-panel layout with a file explorer, text editor, and embedded terminal — all within a single terminal window.

### Design Philosophy

- **Simplicity first**: Prioritizes ease of use over advanced features, with on-screen shortcut hints at all times.
- **Zero external UI dependencies**: Uses only the Python standard library `curses` module for rendering.
- **Single-file editing**: One file open at a time, keeping the mental model simple.
- **Integrated workflow**: File browsing, editing, and shell access without leaving the editor.

---

## 2. Getting Started

### Requirements

- Python 3.8+
- `curses` (included in Python standard library on macOS/Linux)
- `pyte` (Python terminal emulator library, required for the embedded terminal panel)

### Installation

```bash
pip install pyte
```

### Usage

```bash
# Open a new empty buffer
python3 main.py

# Open an existing file
python3 main.py filename.txt
```

---

## 3. Architecture

### High-Level Design

Aipic follows a modular architecture with clear separation of concerns. The application is structured around an event loop that reads keypresses, dispatches them to handlers, updates state, and redraws the screen.

```
main.py
  |
  v
Editor (editor.py)  <-- Central orchestrator
  |
  +-- Buffer (buffer.py)         Text storage & manipulation
  +-- UI (ui.py)                 Screen rendering
  +-- Keybindings (keybindings.py)  Key-to-command mapping
  +-- Search (search.py)         Find text with wrap-around
  +-- Clipboard (clipboard.py)   Cut/paste buffer
  +-- FileExplorer (explorer.py) Directory browsing
  +-- Terminal (terminal.py)     Embedded PTY shell
```

### Module Dependency Graph

```
main.py
  --> editor.py
        --> buffer.py
        --> ui.py
        --> keybindings.py
        --> search.py
        --> clipboard.py
        --> explorer.py
        --> terminal.py (depends on pyte)
```

All modules are leaf dependencies of `editor.py` — none of them depend on each other, enabling clean isolation and testability.

---

## 4. Module Reference

### 4.1 `main.py` — Entry Point

**Purpose**: Application entry point, argument parsing, and curses initialization.

**Flow**:
1. Reads an optional filename from `sys.argv`.
2. Uses `curses.wrapper()` to safely initialize and tear down the curses environment.
3. Creates an `Editor` instance and starts the main loop.

`curses.wrapper()` ensures that the terminal state is always restored on exit, even if an exception occurs.

---

### 4.2 `editor.py` — Core Editor Class

**Purpose**: Central orchestrator that owns all state and coordinates input handling, buffer operations, and rendering.

#### Class: `Editor`

**Constructor** (`__init__`):

| Attribute | Type | Description |
|-----------|------|-------------|
| `stdscr` | curses window | The main curses screen |
| `filepath` | str or None | Path to the currently open file |
| `ui` | UI | Screen rendering engine |
| `clipboard` | Clipboard | Cut/paste buffer |
| `search` | Search | Search state and logic |
| `explorer` | FileExplorer | File explorer panel |
| `terminal` | Terminal | Embedded shell terminal |
| `focus` | str | Current focus: `"editor"`, `"explorer"`, or `"terminal"` |
| `buffer` | Buffer | Text buffer for the open file |
| `cursor_row` | int | Cursor row in buffer coordinates |
| `cursor_col` | int | Cursor column in buffer coordinates |
| `scroll_row` | int | Vertical scroll offset |
| `scroll_col` | int | Horizontal scroll offset |
| `status_message` | str | Transient message shown in the status bar |
| `running` | bool | Main loop control flag |

**Key Methods**:

| Method | Description |
|--------|-------------|
| `run()` | Main event loop. Sets up curses, polls for keys at 50ms intervals, dispatches input, and redraws. |
| `_draw()` | Full screen redraw cycle: erase, update dimensions, draw all panels, position cursor, refresh. |
| `_adjust_scroll()` | Ensures the cursor remains visible by adjusting `scroll_row` and `scroll_col`. |
| `_handle_key(key)` | Top-level key dispatcher. Routes keys based on current focus (terminal, explorer, or editor). |
| `_handle_explorer_key(cmd)` | Handles navigation within the file explorer panel. |
| `_handle_editor_key(cmd, ch)` | Handles editor commands: movement, editing, search, cut/paste. |
| `_save()` | Saves the buffer to disk. Prompts for filename if unnamed. Handles permission errors. |
| `_exit()` | Exits the editor. Prompts to save if the buffer is modified. |
| `_open_file(path)` | Opens a file from the explorer. Prompts to save current buffer if modified. |
| `_check_save_before_close()` | Displays Y/N/Cancel prompt when closing a modified buffer. Returns `True` if safe to proceed. |
| `_search()` | Interactive search: prompts for query, supports repeating last search, wrap-around. |
| `_cut()` | Cuts the current line into the clipboard. Consecutive cuts append. |
| `_paste()` | Pastes clipboard contents at the current cursor row. |
| `_toggle_focus()` | Cycles focus: editor -> explorer -> terminal -> editor. |
| `_toggle_terminal()` | Toggles focus between terminal and editor (direct toggle via `Ctrl+B`). |

**Cursor Movement Methods**:

| Method | Behavior |
|--------|----------|
| `_move_up()` | Move cursor up one line; clamp column to line length. |
| `_move_down()` | Move cursor down one line; clamp column to line length. |
| `_move_left()` | Move left; wraps to end of previous line if at column 0. |
| `_move_right()` | Move right; wraps to start of next line if at end of line. |
| `_home()` | Move to column 0. |
| `_end()` | Move to end of current line. |
| `_page_up()` | Move cursor up by one screen height. |
| `_page_down()` | Move cursor down by one screen height. |

---

### 4.3 `buffer.py` — Text Buffer

**Purpose**: Stores the document as a list of strings (one per line) and provides all text manipulation operations.

#### Class: `Buffer`

**Data Model**:
- `lines`: `list[str]` — each element is one line of text (without newline characters).
- `modified`: `bool` — dirty flag, set to `True` on any edit, reset on save.

**Class Methods**:

| Method | Description |
|--------|-------------|
| `from_file(filepath)` | Reads a file from disk and returns a `Buffer`. Splits on `\n`, strips trailing empty line. Returns empty buffer on `FileNotFoundError`. |

**Instance Methods**:

| Method | Signature | Description |
|--------|-----------|-------------|
| `save` | `(filepath)` | Writes lines joined by `\n` with trailing newline. Resets `modified`. |
| `line_count` | property | Number of lines in the buffer. |
| `get_line` | `(row) -> str` | Returns the line at `row`, or `""` if out of bounds. |
| `line_length` | `(row) -> int` | Length of the line at `row`. |
| `insert_char` | `(row, col, ch)` | Inserts a character at the given position. |
| `delete_char` | `(row, col) -> bool` | Deletes character at position. If at end of line, joins with next line. |
| `backspace` | `(row, col) -> (row, col)` | Deletes character before cursor. If at column 0, joins with previous line. Returns new cursor position. |
| `insert_newline` | `(row, col) -> (row, col)` | Splits line at cursor position. Returns new cursor position (next line, column 0). |
| `cut_line` | `(row) -> (line, new_row)` | Removes and returns the line. If only one line exists, clears it instead of removing. |
| `insert_lines` | `(row, lines)` | Inserts multiple lines at the given row position. |

---

### 4.4 `ui.py` — Screen Rendering

**Purpose**: Handles all screen drawing — title bar, file explorer, content area, terminal panel, status bar, and shortcut hints.

#### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `VERSION` | `"1.0"` | Editor version displayed in the title bar. |
| `EXPLORER_WIDTH` | `30` | Default width of the file explorer panel in columns. |
| `TERMINAL_WIDTH` | `80` | Default width of the terminal panel in columns. |
| `SHORTCUTS_ROW1` | list | First row of shortcut hints: Write Out, Exit, Where Is, Cut, Paste. |
| `SHORTCUTS_ROW2` | list | Second row: Prev Page, Next Page, Explorer, Terminal, Home. |

#### Class: `UI`

**Color Scheme**: All green-on-black (`curses.COLOR_GREEN` on `curses.COLOR_BLACK`) — four color pairs are defined but all use the same colors, creating a retro terminal aesthetic.

**Layout Dimensions** (computed in `update_dimensions()`):

| Attribute | Description |
|-----------|-------------|
| `height`, `width` | Terminal dimensions. |
| `explorer_width` | Actual explorer width (capped at `width // 4`). |
| `content_start_col` | First column of the editor content area (after explorer + separator). |
| `terminal_width` | Actual terminal width (capped at `width // 3`). |
| `terminal_start_col` | First column of the terminal panel. |
| `content_width` | Width available for editor content (between explorer and terminal). |
| `content_height` | Height available for content (`height - 4` for title, status, 2 shortcut rows). |
| `content_start_row` | First row of content (row 1, after title bar). |

**Drawing Methods**:

| Method | Description |
|--------|-------------|
| `draw_title_bar(filename, modified)` | Renders the inverted title bar with editor name, filename (centered), and "Modified" flag. |
| `draw_explorer(explorer, focus)` | Renders the file explorer: directory header, entry list with selection highlight, vertical separator. Focused panel gets bold header. |
| `draw_content(buffer, scroll_row, scroll_col, ...)` | Renders the visible portion of the text buffer in the content area with horizontal scrolling support. |
| `draw_terminal(terminal, focus)` | Renders the terminal panel: header, vertical separator, and terminal output lines from pyte screen. |
| `draw_status_bar(message)` | Renders a transient message on the status line (3rd from bottom). |
| `draw_shortcut_bar()` | Renders two rows of shortcut hints at the bottom of the screen. |
| `position_cursor(focus, ...)` | Positions the hardware cursor based on which panel is focused. |

**Input Methods**:

| Method | Returns | Description |
|--------|---------|-------------|
| `get_input(prompt)` | `str` or `None` | Shows a prompt on the status bar and reads a string. Returns `None` on Escape (cancel). Supports backspace editing. |
| `get_yes_no_cancel(prompt)` | `'y'`, `'n'`, or `'c'` | Shows a prompt and waits for Y, N, C, or Escape. |

---

### 4.5 `keybindings.py` — Key Mapping

**Purpose**: Maps raw curses key codes to semantic command names, decoupling input handling from editor logic.

#### Control Key Constants

| Constant | Value | Key | Command |
|----------|-------|-----|---------|
| `CTRL_A` | 1 | Ctrl+A | Home |
| `CTRL_B` | 2 | Ctrl+B | Toggle terminal |
| `CTRL_E` | 5 | Ctrl+E | End |
| `CTRL_K` | 11 | Ctrl+K | Cut line |
| `CTRL_L` | 12 | Ctrl+L | Refresh |
| `CTRL_O` | 15 | Ctrl+O | Save (Write Out) |
| `CTRL_T` | 20 | Ctrl+T | Toggle explorer focus |
| `CTRL_U` | 21 | Ctrl+U | Paste (Uncut) |
| `CTRL_V` | 22 | Ctrl+V | Page Down |
| `CTRL_W` | 23 | Ctrl+W | Search (Where Is) |
| `CTRL_X` | 24 | Ctrl+X | Exit |
| `CTRL_Y` | 25 | Ctrl+Y | Page Up |

#### Command Constants

20 command constants are defined (e.g., `CMD_MOVE_UP`, `CMD_SAVE`, `CMD_INSERT`, etc.) used throughout the editor for dispatch.

#### Function: `get_command(key) -> (command, char)`

- Looks up the key in a static mapping dictionary.
- For printable characters (ASCII 32-126 or >= 128), returns `(CMD_INSERT, chr(key))`.
- Returns `(None, None)` for unrecognized keys.

---

### 4.6 `search.py` — Search Logic

**Purpose**: Implements text search with wrap-around behavior.

#### Class: `Search`

**State**:
- `last_query`: Stores the most recent search string for repeat-search functionality.

**Method**: `find(buffer, query, start_row, start_col) -> (row, col) | None`

**Algorithm**:
1. Search forward from `(start_row, start_col + 1)` to the end of the buffer.
2. If not found, wrap around and search from the beginning to the starting position.
3. Returns the `(row, col)` of the first match, or `None` if not found.

---

### 4.7 `clipboard.py` — Cut/Paste Buffer

**Purpose**: Manages the cut buffer with support for consecutive cut accumulation.

#### Class: `Clipboard`

**State**:
- `lines`: `list[str]` — the cut buffer contents.
- `_last_cut_row`: Row of the last cut operation.
- `_last_cut_seq`: Sequence number of the last cut.
- `_seq`: Global sequence counter.

**Consecutive Cut Logic**:
When `Ctrl+K` is pressed multiple times in a row on adjacent lines, the cut lines accumulate in the buffer (append behavior). If a non-cut operation occurs between cuts, the buffer is replaced with just the new cut line.

| Method | Description |
|--------|-------------|
| `cut(line, row)` | Adds a line to the buffer. Appends if consecutive, replaces otherwise. |
| `paste()` | Returns a copy of all buffered lines. |
| `is_empty` | Property: `True` if the buffer is empty. |

---

### 4.8 `explorer.py` — File Explorer

**Purpose**: Provides a directory browser panel for navigating the filesystem and opening files.

#### Class: `FileExplorer`

**State**:
- `current_dir`: Absolute path of the currently displayed directory.
- `entries`: `list[tuple(name, is_dir, full_path)]` — directory contents.
- `selected_index`: Index of the highlighted entry.
- `scroll_offset`: Scroll position for long directory listings.

**Directory Listing Rules**:
- `..` entry is always first (unless at filesystem root).
- Directories listed before files.
- Both groups sorted alphabetically (case-insensitive).
- Hidden files (names starting with `.`) are excluded.

**Methods**:

| Method | Description |
|--------|-------------|
| `refresh_entries()` | Rescans the current directory and rebuilds the entry list. |
| `move_up()` / `move_down()` | Moves the selection cursor within the entry list. |
| `enter()` | Opens the selected entry. Returns `("cd", None)` for directories or `("open_file", path)` for files. |
| `go_parent()` | Navigates to the parent directory. |
| `adjust_scroll(visible_height)` | Adjusts scroll offset to keep the selected entry visible. |

---

### 4.9 `terminal.py` — Embedded Terminal

**Purpose**: Provides a fully functional terminal emulator embedded in the editor using PTY (pseudo-terminal) and the `pyte` library for VT100 terminal emulation.

#### Class: `Terminal`

**Architecture**:
- Forks a child process via `pty.fork()` that runs the user's shell (`$SHELL` or `/bin/bash`).
- The parent process communicates with the child through a master file descriptor.
- Terminal output is fed into a `pyte.Screen` + `pyte.Stream` pipeline for proper VT100 rendering.
- The master FD is set to non-blocking mode for asynchronous reads.

**State**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `master_fd` | int or None | File descriptor for the PTY master side. |
| `pid` | int or None | PID of the child shell process. |
| `visible` | bool | Whether the terminal panel is visible. |
| `screen` | pyte.Screen | Virtual terminal screen buffer. |
| `stream` | pyte.Stream | VT100 escape sequence parser. |

**Methods**:

| Method | Description |
|--------|-------------|
| `start()` | Forks a shell subprocess and sets up the PTY. Sets `TERM=xterm-256color`. |
| `stop()` | Sends `SIGTERM` to the shell process and closes the master FD. |
| `resize(rows, cols)` | Resizes the pyte screen and sends `TIOCSWINSZ` ioctl to the PTY. |
| `send_key(ch)` | Sends a single byte (keypress) to the shell. |
| `send_special_key(key_name)` | Sends VT100 escape sequences for special keys (arrows, Home, End, Delete, Page Up/Down). |
| `read_output()` | Non-blocking read from the PTY. Feeds output into the pyte stream for rendering. |
| `get_visible_lines(height)` | Returns rendered terminal lines from the pyte screen buffer. |
| `cursor_pos` | Property: returns `(row, col)` of the terminal cursor from pyte. |
| `is_alive` | Property: checks if the shell process is still running. |

**Special Key Escape Sequences**:

| Key | Sequence |
|-----|----------|
| Up | `\x1b[A` |
| Down | `\x1b[B` |
| Right | `\x1b[C` |
| Left | `\x1b[D` |
| Home | `\x1b[H` |
| End | `\x1b[F` |
| Delete | `\x1b[3~` |
| Page Up | `\x1b[5~` |
| Page Down | `\x1b[6~` |

---

## 5. User Interface Layout

```
+-----------------------------------------------------------------------+
|  Aipic 1.0              filename.txt                    Modified       |  <- Title bar (row 0)
| /path/to/dir        |                          | Terminal              |
| ..                   | (file content area)      | $ ls                 |
| [dir1/]              |                          | file1.py             |
| [dir2/]              |                          | file2.txt            |
|  file1.py            |                          | $                    |
|  file2.txt           |                          |                      |
|                      |                          |                      |
|  [ status message ]                                                    |  <- Status bar (row H-3)
|  ^O Write Out  ^X Exit  ^W Where Is  ^K Cut  ^U Paste                 |  <- Shortcut row 1 (row H-2)
|  ^Y Prev Page  ^V Next Page  ^T Explorer  ^B Terminal  ^A Home        |  <- Shortcut row 2 (row H-1)
+-----------------------------------------------------------------------+
```

### Panel Widths

| Panel | Default Width | Maximum |
|-------|---------------|---------|
| File Explorer | 30 columns | `terminal_width // 4` |
| Editor Content | Remaining space | Fills between explorer and terminal |
| Terminal | 80 columns | `terminal_width // 3` |

### Vertical Separators

Vertical line characters (`ACS_VLINE`) are drawn between:
- The file explorer and the content area.
- The content area and the terminal panel.

### Bottom Bars

The bottom 3 rows of the screen are reserved:
- **Row H-3**: Status bar — transient messages (saved, not found, prompts).
- **Row H-2**: Shortcut row 1 — Write Out, Exit, Where Is, Cut, Paste.
- **Row H-1**: Shortcut row 2 — Prev Page, Next Page, Explorer, Terminal, Home.

---

## 6. Keyboard Shortcuts

### Global Shortcuts (work in any focus mode)

| Shortcut | Command | Description |
|----------|---------|-------------|
| `Ctrl+O` | Save | Save file (prompts for name if unnamed) |
| `Ctrl+X` | Exit | Exit editor (prompts to save if modified) |
| `Ctrl+T` | Toggle Focus | Cycle focus: Editor -> Explorer -> Terminal |
| `Ctrl+B` | Toggle Terminal | Switch focus directly to/from terminal |
| `Ctrl+L` | Refresh | Force screen redraw |

### Editor Mode Shortcuts

| Shortcut | Command | Description |
|----------|---------|-------------|
| `Ctrl+W` | Search | Find text with wrap-around |
| `Ctrl+K` | Cut | Cut current line (consecutive cuts append) |
| `Ctrl+U` | Paste | Paste cut buffer at cursor |
| `Ctrl+A` | Home | Move cursor to beginning of line |
| `Ctrl+E` | End | Move cursor to end of line |
| `Ctrl+Y` | Page Up | Scroll up one screen |
| `Ctrl+V` | Page Down | Scroll down one screen |
| Arrow keys | Navigation | Move cursor directionally |
| `Home` / `End` | Navigation | Beginning / end of line |
| `Page Up` / `Page Down` | Navigation | Scroll by screen height |
| `Backspace` | Delete | Delete character before cursor |
| `Delete` | Delete | Delete character at cursor |
| `Enter` | Newline | Insert newline at cursor |
| `Tab` | Insert spaces | Insert 4 spaces (soft tab) |

### Explorer Mode Shortcuts

| Shortcut | Command | Description |
|----------|---------|-------------|
| `Up` / `Down` | Navigate | Move selection in file list |
| `Enter` / `Right` | Open | Open file or enter directory |
| `Left` / `Backspace` | Parent | Navigate to parent directory |

### Terminal Mode Shortcuts

When the terminal is focused, all keypresses are forwarded to the shell **except**:

| Shortcut | Action |
|----------|--------|
| `Ctrl+B` | Return focus to editor |
| `Ctrl+T` | Cycle focus to next panel |
| `Ctrl+X` | Exit the editor |

---

## 7. Focus Model

The editor has three focus states, managed by the `Editor.focus` attribute:

```
         Ctrl+T              Ctrl+T              Ctrl+T
"editor" -------> "explorer" -------> "terminal" -------> "editor"

         Ctrl+B                                  Ctrl+B
"editor" <------------------------------> "terminal"
```

### Focus Behavior

| Focus | Input Handling | Cursor Position |
|-------|----------------|-----------------|
| `"editor"` | Keys dispatched to editor commands (movement, editing, search, etc.) | Positioned in the content area at `(cursor_row, cursor_col)` |
| `"explorer"` | Keys dispatched to explorer navigation (up/down/enter/back) | Positioned on the selected entry in the explorer panel |
| `"terminal"` | Keys forwarded to the PTY shell subprocess (except Ctrl+B/T/X) | Positioned at the terminal cursor from pyte screen |

### Visual Indicator

The focused panel's header is rendered with **bold** text; unfocused panels use normal weight.

---

## 8. Data Flow

### Main Event Loop

```
while running:
    1. terminal.read_output()      -- Poll PTY for new shell output
    2. _draw()                     -- Full screen redraw
       a. stdscr.erase()
       b. ui.update_dimensions()
       c. terminal.resize()
       d. _adjust_scroll()
       e. Draw: title -> explorer -> content -> terminal -> status -> shortcuts
       f. Position cursor
       g. Refresh screen
       h. Clear status_message
    3. key = stdscr.getch()        -- Read keypress (50ms timeout)
    4. if key == -1: continue      -- No key pressed, loop back
    5. _handle_key(key)            -- Dispatch to appropriate handler
```

### File Open Flow

```
User selects file in explorer
  --> explorer.enter() returns ("open_file", path)
  --> _open_file(path)
      --> _check_save_before_close()
          --> If modified: prompt Y/N/C
              Y: save, then proceed
              N: discard, proceed
              C: cancel, abort open
      --> Buffer.from_file(path)
      --> Reset cursor and scroll to (0, 0)
      --> Set focus to "editor"
```

### Save Flow

```
Ctrl+O pressed
  --> _save()
      --> If no filepath: prompt for filename
          --> If cancelled: return
      --> buffer.save(filepath)
      --> On success: "Wrote N lines to filepath"
      --> On PermissionError: "Error: Permission denied"
      --> On OSError: "Error: {message}"
```

### Search Flow

```
Ctrl+W pressed
  --> _search()
      --> Show prompt (with last query hint)
      --> Read query string
      --> If empty and last_query exists: reuse last query
      --> search.find(buffer, query, cursor_row, cursor_col)
          --> Search forward from cursor to end
          --> Wrap around to beginning if needed
      --> If found: move cursor to match
      --> If not found: show "not found" message
```

---

## 9. Dependencies

### Standard Library

| Module | Used By | Purpose |
|--------|---------|---------|
| `curses` | main.py, editor.py, ui.py, keybindings.py | Terminal UI rendering and input |
| `os` | editor.py, explorer.py, terminal.py | File operations, process management |
| `sys` | main.py | Command-line argument parsing |
| `pty` | terminal.py | Pseudo-terminal fork |
| `select` | terminal.py | Non-blocking I/O polling |
| `signal` | terminal.py | Process signal handling (SIGTERM) |
| `struct` | terminal.py | Binary data packing (ioctl) |
| `fcntl` | terminal.py | File descriptor flags, ioctl |
| `termios` | terminal.py | Terminal I/O control (TIOCSWINSZ) |

### External

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `pyte` | any | terminal.py | VT100 terminal emulation (Screen, Stream) |

---

## 10. Limitations

The following features are explicitly out of scope for version 1.0:

| Feature | Status |
|---------|--------|
| Syntax highlighting | Not supported |
| Multiple open files | Single file only |
| Undo/Redo | Not supported |
| Mouse support | Not supported |
| Configuration file | Not supported |
| Spell checking | Not supported |
| Unicode input | Partial (printable ASCII + high bytes via chr()) |
| Line wrapping | Disabled (horizontal scrolling instead) |
| Terminal toggle visibility | Terminal panel is always visible; `Ctrl+B` only changes focus |

### Known Design Notes

- The terminal subprocess is started immediately on editor launch, even if the user never interacts with it.
- The terminal panel is always rendered (`terminal_visible=True` is hardcoded in `_draw()`), though the `UI` class supports hiding it.
- The `Clipboard` consecutive-cut detection relies on sequence numbers and row tracking — the row must match because after cutting a line, the next line slides into the same row position.
- Status messages are cleared after every draw cycle, making them visible for exactly one frame (~50ms) unless no key is pressed (in which case they persist until the next keypress).
