"""Embedded terminal panel using pty + pyte for full VT100 emulation."""

import os
import pty
import select
import signal
import struct
import fcntl
import termios

import pyte


class Terminal:
    """Manages a pseudo-terminal shell subprocess with full terminal emulation."""

    def __init__(self, rows=24, cols=40):
        self.master_fd = None
        self.pid = None
        self.visible = True
        self._rows = rows
        self._cols = cols
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.Stream(self.screen)

    def start(self):
        if self.pid is not None:
            return
        pid, fd = pty.fork()
        if pid == 0:
            # Child process — exec shell
            shell = os.environ.get("SHELL", "/bin/bash")
            os.environ["TERM"] = "xterm-256color"
            os.execvp(shell, [shell])
        # Parent
        self.pid = pid
        self.master_fd = fd
        flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self.resize(self._rows, self._cols)

    def stop(self):
        if self.pid is not None and self.pid > 0:
            try:
                os.kill(self.pid, signal.SIGTERM)
                os.waitpid(self.pid, os.WNOHANG)
            except (OSError, ChildProcessError):
                pass
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
        self.pid = None
        self.master_fd = None

    def resize(self, rows, cols):
        if rows <= 0 or cols <= 0:
            return
        self._rows = rows
        self._cols = cols
        self.screen.resize(rows, cols)
        if self.master_fd is not None:
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            except OSError:
                pass

    def send_key(self, ch):
        if self.master_fd is None:
            return
        if isinstance(ch, int):
            if ch < 256:
                data = bytes([ch])
            else:
                return
        elif isinstance(ch, str):
            data = ch.encode("utf-8")
        else:
            return
        try:
            os.write(self.master_fd, data)
        except OSError:
            pass

    def send_special_key(self, key_name):
        escape_sequences = {
            "up": b"\x1b[A",
            "down": b"\x1b[B",
            "right": b"\x1b[C",
            "left": b"\x1b[D",
            "home": b"\x1b[H",
            "end": b"\x1b[F",
            "delete": b"\x1b[3~",
            "page_up": b"\x1b[5~",
            "page_down": b"\x1b[6~",
        }
        seq = escape_sequences.get(key_name)
        if seq and self.master_fd is not None:
            try:
                os.write(self.master_fd, seq)
            except OSError:
                pass

    def read_output(self):
        if self.master_fd is None:
            return
        try:
            while True:
                ready, _, _ = select.select([self.master_fd], [], [], 0)
                if not ready:
                    break
                data = os.read(self.master_fd, 65536)
                if not data:
                    break
                self.stream.feed(data.decode("utf-8", errors="replace"))
        except (OSError, ValueError):
            pass

    def get_visible_lines(self, height):
        lines = []
        for row in range(self.screen.lines):
            line_chars = self.screen.buffer[row]
            line = ""
            for col in range(self.screen.columns):
                char = line_chars[col]
                line += char.data if char.data else " "
            lines.append(line.rstrip())
        return lines[:height]

    @property
    def cursor_pos(self):
        return self.screen.cursor.y, self.screen.cursor.x

    @property
    def is_alive(self):
        if self.pid is None or self.pid == 0:
            return False
        try:
            pid, _ = os.waitpid(self.pid, os.WNOHANG)
            return pid == 0
        except ChildProcessError:
            return False
