# MyPico

A lightweight terminal text editor inspired by GNU Pico/Nano, built in Python using the `curses` library. No external dependencies.

## Usage

```bash
# Open a new empty buffer
python3 main.py

# Open a file
python3 main.py filename.txt
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Save file |
| `Ctrl+X` | Exit (prompts to save if modified) |
| `Ctrl+W` | Search text |
| `Ctrl+K` | Cut current line |
| `Ctrl+U` | Paste cut line(s) |
| `Ctrl+Y` | Page Up |
| `Ctrl+V` | Page Down |
| `Ctrl+A` | Move to beginning of line |
| `Ctrl+E` | Move to end of line |
| `Ctrl+L` | Refresh screen |

Arrow keys, Home, End, Page Up, Page Down, Backspace, and Delete all work as expected.

## Project Structure

```
main.py         Entry point and curses initialization
editor.py       Core editor: state, key dispatch, main loop
buffer.py       Text buffer: line storage, insert/delete operations
ui.py           Screen rendering: title bar, content, status, shortcuts
keybindings.py  Key mapping and command dispatch
search.py       Search with wrap-around
clipboard.py    Cut/paste buffer management
```

## Requirements

- Python 3.8+
- `curses` (included in Python standard library on macOS/Linux)
