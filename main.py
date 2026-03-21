#!/usr/bin/env python3
"""Aipic - A lightweight terminal text editor inspired by Pico/Nano."""

import sys
import curses
from editor import Editor  # from editor/__init__.py


def main(stdscr):
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    editor = Editor(stdscr, filepath)
    editor.run()


if __name__ == "__main__":
    curses.wrapper(main)
