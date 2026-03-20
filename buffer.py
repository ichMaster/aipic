class Buffer:
    """Text buffer: stores lines and handles insert/delete operations."""

    def __init__(self, lines=None):
        self.lines = lines if lines is not None else [""]
        self.modified = False

    @classmethod
    def from_file(cls, filepath):
        try:
            with open(filepath, "r") as f:
                text = f.read()
            lines = text.split("\n")
            if lines and lines[-1] == "":
                lines = lines[:-1]
            if not lines:
                lines = [""]
            buf = cls(lines)
            buf.modified = False
            return buf
        except FileNotFoundError:
            buf = cls([""])
            return buf

    def save(self, filepath):
        with open(filepath, "w") as f:
            f.write("\n".join(self.lines) + "\n")
        self.modified = False

    @property
    def line_count(self):
        return len(self.lines)

    def get_line(self, row):
        if 0 <= row < self.line_count:
            return self.lines[row]
        return ""

    def line_length(self, row):
        return len(self.get_line(row))

    def insert_char(self, row, col, ch):
        line = self.lines[row]
        self.lines[row] = line[:col] + ch + line[col:]
        self.modified = True

    def delete_char(self, row, col):
        """Delete character at (row, col). Returns True if deletion happened."""
        line = self.lines[row]
        if col < len(line):
            self.lines[row] = line[:col] + line[col + 1:]
            self.modified = True
            return True
        elif row + 1 < self.line_count:
            # Join with next line
            self.lines[row] = line + self.lines[row + 1]
            self.lines.pop(row + 1)
            self.modified = True
            return True
        return False

    def backspace(self, row, col):
        """Delete character before (row, col). Returns new (row, col)."""
        if col > 0:
            line = self.lines[row]
            self.lines[row] = line[:col - 1] + line[col:]
            self.modified = True
            return row, col - 1
        elif row > 0:
            # Join with previous line
            prev_len = len(self.lines[row - 1])
            self.lines[row - 1] += self.lines[row]
            self.lines.pop(row)
            self.modified = True
            return row - 1, prev_len
        return row, col

    def insert_newline(self, row, col):
        """Split line at (row, col). Returns new cursor position."""
        line = self.lines[row]
        self.lines[row] = line[:col]
        self.lines.insert(row + 1, line[col:])
        self.modified = True
        return row + 1, 0

    def cut_line(self, row):
        """Remove and return the line at row. Returns (removed_line, new_row)."""
        if self.line_count == 1:
            line = self.lines[0]
            self.lines[0] = ""
            self.modified = True
            return line, 0
        line = self.lines.pop(row)
        self.modified = True
        new_row = min(row, self.line_count - 1)
        return line, new_row

    def insert_lines(self, row, lines):
        """Insert lines at row."""
        for i, line in enumerate(lines):
            self.lines.insert(row + i, line)
        self.modified = True
