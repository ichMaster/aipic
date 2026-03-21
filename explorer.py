import os


class FileExplorer:
    """File explorer panel: directory listing and navigation."""

    def __init__(self, root_dir=None):
        self.current_dir = root_dir or os.getcwd()
        self.entries = []  # List of (name, is_dir, full_path)
        self.selected_index = 0
        self.scroll_offset = 0
        self.refresh_entries()

    def refresh_entries(self):
        self.entries = []
        # Parent directory entry (unless at filesystem root)
        if self.current_dir != os.path.dirname(self.current_dir):
            self.entries.append(("..", True, os.path.dirname(self.current_dir)))

        try:
            items = os.listdir(self.current_dir)
        except PermissionError:
            return

        dirs = []
        files = []
        for item in items:
            if item.startswith("."):
                continue
            full_path = os.path.join(self.current_dir, item)
            if os.path.isdir(full_path):
                dirs.append((item, True, full_path))
            else:
                files.append((item, False, full_path))

        dirs.sort(key=lambda e: e[0].lower())
        files.sort(key=lambda e: e[0].lower())
        self.entries.extend(dirs)
        self.entries.extend(files)

    def move_up(self):
        if self.selected_index > 0:
            self.selected_index -= 1

    def move_down(self):
        if self.selected_index < len(self.entries) - 1:
            self.selected_index += 1

    def enter(self):
        """Enter directory or select file. Returns ("open_file", path) or ("cd", None)."""
        if not self.entries:
            return (None, None)
        name, is_dir, full_path = self.entries[self.selected_index]
        if is_dir:
            self.current_dir = full_path
            self.selected_index = 0
            self.scroll_offset = 0
            self.refresh_entries()
            return ("cd", None)
        else:
            return ("open_file", full_path)

    def go_parent(self):
        parent = os.path.dirname(self.current_dir)
        if parent != self.current_dir:
            self.current_dir = parent
            self.selected_index = 0
            self.scroll_offset = 0
            self.refresh_entries()

    def adjust_scroll(self, visible_height):
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible_height:
            self.scroll_offset = self.selected_index - visible_height + 1
