class Search:
    """Search logic with wrap-around."""

    def __init__(self):
        self.last_query = ""

    def find(self, buffer, query, start_row, start_col):
        """Find next occurrence of query starting after (start_row, start_col).
        Wraps around to the beginning. Returns (row, col) or None."""
        if not query:
            return None

        self.last_query = query
        total_lines = buffer.line_count

        # Search from current position to end
        for row in range(start_row, total_lines):
            line = buffer.get_line(row)
            search_from = start_col + 1 if row == start_row else 0
            idx = line.find(query, search_from)
            if idx != -1:
                return (row, idx)

        # Wrap around: search from beginning to current position
        for row in range(0, start_row + 1):
            line = buffer.get_line(row)
            end_at = start_col if row == start_row else len(line)
            idx = line.find(query, 0, end_at + len(query))
            if idx != -1 and (row != start_row or idx <= start_col):
                return (row, idx)

        return None
