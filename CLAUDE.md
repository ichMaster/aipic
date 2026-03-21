# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running

```bash
# Open editor with a file
python3 main.py filename.txt

# Open empty buffer
python3 main.py
```

No build step. No test suite. External dependency: `pyte` (VT100 terminal emulation).

## Architecture

Aipic is a terminal text editor (Pico/Nano-inspired) built with Python curses. The UI has three panels: file explorer (left), editor/viewer (center), and embedded terminal (right, always visible).

### Layout

```
main.py                  Entry point — curses.wrapper → Editor.run()
editor/
  editor.py              Core state, main loop, key dispatch — the hub
  ui.py                  All rendering (title bar, content, status, explorer, terminal, inv tables)
  keybindings.py         Key code → command name mapping
  buffer.py              Line-based text storage with insert/delete/cut ops
  explorer.py            File explorer panel — directory listing, navigation
  terminal.py            Embedded bash shell via pty.fork() + pyte Screen
  clipboard.py           Cut/paste line buffer
  search.py              Text search with wrap-around
  markdown_renderer.py   Markdown → styled curses lines (headers, bold, code, tables, links)
  inv_viewer.py          State for .inv inventory file viewer (table, detail, filter modes)
  inv_config.json        Column definitions per inventory type (db_, etl_, bi_)
extractor/
  extract_inventory.py   Pulls DB/ETL/BI inventory from migVisor REST API, saves as .inv
  config.json            REST API base URL
```

### Key dispatch flow

`Editor._handle_key()` in editor.py routes input based on focus and mode:
1. Focus-independent: Ctrl+T (cycle focus), Ctrl+B (terminal focus)
2. Terminal focus: keys forwarded to pty via `Terminal.send_key()`
3. Explorer focus: navigation and file open
4. Editor focus with inv_viewer: inv-specific keys (Space, Enter, F5, F6, Ctrl+O)
5. Editor focus with md_view_mode: F5 toggles rendered/edit markdown
6. Normal editor focus: text editing commands

### Viewer modes

**Markdown** (`.md` files): F5 toggles between rendered view and edit mode. Rendering done by `markdown_renderer.render_markdown()` returning styled line spans.

**Inventory** (`.inv` files): Read-only table viewer. Type detected by filename prefix (`db_`, `etl_`, `bi_`); unknown prefixes get auto-generated columns from first record's keys. Modes:
- Table view: browse all records, Space=select, Enter=detail, F6=filter selected
- Filtered view: only checked records shown, Space=unselect (modifies main checked set), F5=back to all
- Detail view: key-value display of one record, Enter=back, F5=back to all

### UI color pairs

Pairs 1-4: base editor (green on black). Pairs 5-11: markdown styles. Pair 12: inv table header (cyan). Pair 13-14: inv detail keys/values. Pair 15: inv filtered view header (black on yellow).

### Terminal panel

Uses `pty.fork()` to spawn a real shell, `pyte.Screen`/`pyte.Stream` for VT100 emulation. Always visible (80 cols wide). Ctrl+B toggles keyboard focus to/from terminal.

## Extractor

`extractor/extract_inventory.py` fetches paginated inventory data from migVisor REST API (`POST` to `/api/tools/{tool_name}`) and saves as `.inv` (JSON) files in `data/`. Config in `extractor/config.json`.
