# Aipic - Terminal Text Editor Specification

A lightweight terminal text editor inspired by GNU Pico/Nano, built in Python using the `curses` library.

## 1. Overview

Aipic is a simple, user-friendly terminal text editor. Like Pico, it prioritizes ease of use over advanced features, displaying available commands on-screen at all times.

## 2. Core Features

### 2.1 File Operations
- Open a file from the command line: `aipic [filename]`
- Open a new (unnamed) buffer if no filename is given
- Save file (Write Out) with `Ctrl+O`
  - Prompt for filename if the buffer has no name
  - Confirm overwrite if file already exists
- Exit with `Ctrl+X`
  - Prompt to save if buffer has unsaved changes ("Save modified buffer? Y/N/Cancel")

### 2.2 Text Editing
- Insert characters at cursor position
- Delete character before cursor (Backspace)
- Delete character at cursor (Delete)
- Enter key inserts a newline and moves cursor to the beginning of the new line
- Tab key inserts 4 spaces (soft tabs)
- Support for lines longer than the terminal width (horizontal scrolling)

### 2.3 Cursor Navigation
- Arrow keys: move cursor up, down, left, right
- `Home` / `Ctrl+A`: move cursor to beginning of line
- `End` / `Ctrl+E`: move cursor to end of line
- `Page Up` / `Ctrl+Y`: scroll up one screen
- `Page Down` / `Ctrl+V`: scroll down one screen
- `Ctrl+L`: refresh/redraw the screen

### 2.4 Search
- `Ctrl+W` (Where Is): search for text
  - Prompt for search string at the bottom of the screen
  - Move cursor to next occurrence
  - Wrap around to the beginning if not found after cursor
  - Display "Not Found" message if no match exists

### 2.5 Cut, Copy, and Paste
- `Ctrl+K`: cut current line (stores in cut buffer; consecutive cuts append)
- `Ctrl+U`: paste (uncut) the cut buffer at cursor position

## 3. User Interface Layout

```
+----------------------------------------------------------+
|  Aipic 1.0          filename.txt        Modified         |  <- Title bar
|                                                          |
|  (file content area)                                     |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|  [ status message ]                                      |  <- Status bar
|  ^O Write Out  ^X Exit  ^W Where Is  ^K Cut  ^U Paste   |  <- Shortcut bar row 1
|  ^Y Prev Page  ^V Next Page  ^L Refresh  ^A Home ^E End |  <- Shortcut bar row 2
+----------------------------------------------------------+
```

### 3.1 Title Bar
- Displayed as an inverted (reverse video) bar at the top
- Shows: editor name and version (left), filename (center), "Modified" flag (right)

### 3.2 Content Area
- Occupies the space between the title bar and the bottom bars
- Displays the file content with line wrapping disabled (horizontal scroll)
- Shows the cursor at its current position

### 3.3 Status Bar
- One line above the shortcut bars
- Displays transient messages: "File saved", "Not Found", prompts for input, etc.
- Messages disappear after a timeout or the next keypress

### 3.4 Shortcut Bar
- Two lines at the very bottom of the screen
- Shows available keyboard shortcuts
- `^` denotes the Ctrl key

## 4. Technical Design

### 4.1 Technology
- Language: Python 3.8+
- UI library: `curses` (standard library)
- No external dependencies

### 4.2 Architecture

| Module          | Responsibility                                      |
|-----------------|-----------------------------------------------------|
| `main.py`       | Entry point, argument parsing, curses initialization |
| `editor.py`     | Core editor class: state, key dispatch, main loop    |
| `buffer.py`     | Text buffer: list of lines, insert/delete operations |
| `ui.py`         | Screen rendering: title bar, content, status, shortcuts |
| `keybindings.py`| Key mapping and command dispatch table               |
| `search.py`     | Search logic (find next, wrap around)                |
| `clipboard.py`  | Cut buffer management (cut/paste lines)              |

### 4.3 Buffer Model
- Text is stored as a list of strings (one per line)
- Cursor is tracked as `(row, col)` in buffer coordinates
- Viewport is tracked as `(scroll_row, scroll_col)` for scrolling

### 4.4 Rendering Loop
1. Read a keypress (`curses.getch()`)
2. Dispatch keypress to the appropriate handler
3. Update buffer and cursor state
4. Redraw the screen (title bar, content, status bar, shortcut bar)
5. Position the terminal cursor

### 4.5 Error Handling
- Gracefully handle terminal resize (`curses.KEY_RESIZE`)
- Handle file permission errors on save
- Ensure curses cleanup on crash (`curses.wrapper`)

## 5. Command-Line Interface

```
usage: aipic [filename]

positional arguments:
  filename    File to open (optional; opens empty buffer if omitted)
```

## 6. Limitations (Out of Scope for v1.0)
- No syntax highlighting
- No multiple buffers / split view
- No undo/redo
- No mouse support
- No configuration file
- No spell checking
