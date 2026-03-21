"""Inventory file viewer — table and detail views for .inv files."""

import json
import os
import curses


class InvViewer:
    """Manages state for viewing .inv inventory files."""

    def __init__(self, filepath, records, columns):
        self.filepath = filepath
        self.records = records
        self.columns = columns  # list of {"field", "label", "width"}
        self.selected_index = 0
        self.scroll_offset = 0
        self.detail_mode = False
        self.detail_scroll = 0
        self.checked = set()  # set of record indices marked with space
        self.checked_view = False  # True when viewing only checked records
        self._checked_list = []  # ordered list for checked view navigation
        self._checked_scroll = 0
        self._checked_cursor = 0

    @classmethod
    def from_file(cls, filepath):
        """Load an .inv file and return an InvViewer, or None if not applicable."""
        if not filepath or not filepath.lower().endswith('.inv'):
            return None

        try:
            with open(filepath) as f:
                records = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        if not isinstance(records, list) or not records:
            return None

        config = _load_config()
        inv_type = _detect_type(filepath)
        if inv_type in config:
            columns = config[inv_type]["columns"]
        else:
            # Auto-generate columns from first record's keys
            columns = [{"field": k, "label": k, "width": max(len(k) + 2, 15)}
                       for k in records[0].keys()]
        return cls(filepath, records, columns)

    def move_up(self):
        if self.detail_mode:
            self.detail_scroll = max(0, self.detail_scroll - 1)
        elif self.selected_index > 0:
            self.selected_index -= 1

    def move_down(self, visible_height=None):
        if self.detail_mode:
            self.detail_scroll += 1
        elif self.selected_index < len(self.records) - 1:
            self.selected_index += 1

    def page_up(self, visible_height):
        if self.detail_mode:
            self.detail_scroll = max(0, self.detail_scroll - visible_height)
        else:
            self.selected_index = max(0, self.selected_index - visible_height)

    def page_down(self, visible_height):
        if self.detail_mode:
            self.detail_scroll += visible_height
        else:
            self.selected_index = min(len(self.records) - 1,
                                      self.selected_index + visible_height)

    def home(self):
        if self.detail_mode:
            self.detail_scroll = 0
        else:
            self.selected_index = 0

    def end(self):
        if self.detail_mode:
            pass  # will be clamped during rendering
        else:
            self.selected_index = len(self.records) - 1

    def toggle_check(self):
        """Toggle check mark on current record."""
        if self.checked_view:
            self._toggle_uncheck()
            return
        idx = self.selected_index
        if idx in self.checked:
            self.checked.discard(idx)
        else:
            self.checked.add(idx)
        # Auto-advance to next record
        if self.selected_index < len(self.records) - 1:
            self.selected_index += 1

    def _toggle_uncheck(self):
        """Toggle uncheck on current record — removes from main checked set."""
        if not self._checked_list:
            return
        idx = self._checked_list[self._checked_cursor]
        if idx in self.checked:
            self.checked.discard(idx)
        else:
            self.checked.add(idx)
        # Auto-advance
        if self._checked_cursor < len(self._checked_list) - 1:
            self._checked_cursor += 1

    def toggle_checked_view(self):
        """Toggle between full table and checked-only view."""
        if not self.checked_view:
            if not self.checked:
                return False  # nothing checked
            self._checked_list = sorted(self.checked)
            self._checked_cursor = 0
            self._checked_scroll = 0
            self.checked_view = True
            self.detail_mode = False
        else:
            self.checked_view = False
            self.detail_mode = False
        return True

    def get_checked_records(self):
        """All records in checked view (for display, includes unchecked ones)."""
        return [self.records[i] for i in self._checked_list]

    def get_selected_records(self):
        """Only records that are still checked."""
        return [self.records[i] for i in self._checked_list if i in self.checked]

    def get_checked_count(self):
        return len(self.checked)

    def get_selected_count(self):
        return sum(1 for i in self._checked_list if i in self.checked)

    def is_unchecked_in_view(self, checked_list_idx):
        """Check if a record at given index in _checked_list has been unchecked."""
        if 0 <= checked_list_idx < len(self._checked_list):
            return self._checked_list[checked_list_idx] not in self.checked
        return False

    def checked_move_up(self):
        if self.detail_mode:
            self.detail_scroll = max(0, self.detail_scroll - 1)
        elif self._checked_cursor > 0:
            self._checked_cursor -= 1

    def checked_move_down(self):
        if self.detail_mode:
            self.detail_scroll += 1
        elif self._checked_cursor < len(self._checked_list) - 1:
            self._checked_cursor += 1

    def checked_page_up(self, visible_height):
        if self.detail_mode:
            self.detail_scroll = max(0, self.detail_scroll - visible_height)
        else:
            self._checked_cursor = max(0, self._checked_cursor - visible_height)

    def checked_page_down(self, visible_height):
        if self.detail_mode:
            self.detail_scroll += visible_height
        else:
            self._checked_cursor = min(len(self._checked_list) - 1,
                                       self._checked_cursor + visible_height)

    def adjust_checked_scroll(self, visible_height):
        if self._checked_cursor < self._checked_scroll:
            self._checked_scroll = self._checked_cursor
        elif self._checked_cursor >= self._checked_scroll + visible_height:
            self._checked_scroll = self._checked_cursor - visible_height + 1

    def get_checked_selected_record(self):
        if 0 <= self._checked_cursor < len(self._checked_list):
            return self.records[self._checked_list[self._checked_cursor]]
        return None

    def toggle_detail(self):
        self.detail_mode = not self.detail_mode
        self.detail_scroll = 0

    def adjust_scroll(self, visible_height):
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible_height:
            self.scroll_offset = self.selected_index - visible_height + 1

    def get_selected_record(self):
        if 0 <= self.selected_index < len(self.records):
            return self.records[self.selected_index]
        return None

    def get_detail_lines(self):
        """Format the selected record as key-value lines for detail view."""
        record = self.get_selected_record()
        if not record:
            return []
        lines = []
        max_key_len = max(len(k) for k in record.keys()) if record else 0
        for key, value in record.items():
            val_str = _format_value(value)
            lines.append((key, val_str, max_key_len))
        return lines


def _load_config():
    config_path = os.path.join(os.path.dirname(__file__), "inv_config.json")
    try:
        with open(config_path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _detect_type(filepath):
    """Detect inventory type from filename prefix."""
    basename = os.path.basename(filepath).lower()
    for prefix, inv_type in (("db_", "db_inventory"), ("etl_", "etl_inventory"), ("bi_", "bi_inventory")):
        if basename.startswith(prefix):
            return inv_type
    return ""


def _format_value(value):
    """Format a value for display."""
    if value is None:
        return "—"
    if isinstance(value, dict):
        try:
            return json.dumps(value, indent=2)
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, str) and value.startswith("{"):
        try:
            parsed = json.loads(value)
            return json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, TypeError):
            pass
    return str(value)
