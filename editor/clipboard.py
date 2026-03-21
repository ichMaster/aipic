class Clipboard:
    """Cut buffer management for cut/paste operations."""

    def __init__(self):
        self.lines = []
        self._last_cut_row = -1
        self._last_cut_seq = 0
        self._seq = 0

    def cut(self, line, row):
        """Add a cut line. Consecutive cuts on adjacent rows append to the buffer."""
        self._seq += 1
        if self._last_cut_seq == self._seq - 1 and self._last_cut_row == row:
            # Consecutive cut — append
            self.lines.append(line)
        else:
            # New cut — replace buffer
            self.lines = [line]
        self._last_cut_row = row
        self._last_cut_seq = self._seq

    def paste(self):
        """Return a copy of the cut buffer lines."""
        return list(self.lines)

    @property
    def is_empty(self):
        return len(self.lines) == 0
