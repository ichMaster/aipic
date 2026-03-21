import curses

# Ctrl key combinations produce ASCII 1-26 (Ctrl+A=1, Ctrl+B=2, ...)
CTRL_A = 1    # Home
CTRL_E = 5    # End
CTRL_K = 11   # Cut line
CTRL_L = 12   # Refresh
CTRL_O = 15   # Write Out (save)
CTRL_U = 21   # Paste (uncut)
CTRL_V = 22   # Page Down
CTRL_W = 23   # Where Is (search)
CTRL_X = 24   # Exit
CTRL_T = 20   # Toggle explorer
CTRL_B = 2    # Toggle terminal
CTRL_Y = 25   # Page Up

# Command names
CMD_MOVE_UP = "move_up"
CMD_MOVE_DOWN = "move_down"
CMD_MOVE_LEFT = "move_left"
CMD_MOVE_RIGHT = "move_right"
CMD_HOME = "home"
CMD_END = "end"
CMD_PAGE_UP = "page_up"
CMD_PAGE_DOWN = "page_down"
CMD_BACKSPACE = "backspace"
CMD_DELETE = "delete"
CMD_ENTER = "enter"
CMD_TAB = "tab"
CMD_SAVE = "save"
CMD_EXIT = "exit"
CMD_SEARCH = "search"
CMD_CUT = "cut"
CMD_PASTE = "paste"
CMD_REFRESH = "refresh"
CMD_RESIZE = "resize"
CMD_INSERT = "insert"
CMD_TOGGLE_EXPLORER = "toggle_explorer"
CMD_TOGGLE_TERMINAL = "toggle_terminal"


def get_command(key):
    """Map a key code to a command name. Returns (command, char) tuple."""
    key_map = {
        curses.KEY_UP: CMD_MOVE_UP,
        curses.KEY_DOWN: CMD_MOVE_DOWN,
        curses.KEY_LEFT: CMD_MOVE_LEFT,
        curses.KEY_RIGHT: CMD_MOVE_RIGHT,
        curses.KEY_HOME: CMD_HOME,
        curses.KEY_END: CMD_END,
        curses.KEY_PPAGE: CMD_PAGE_UP,
        curses.KEY_NPAGE: CMD_PAGE_DOWN,
        curses.KEY_BACKSPACE: CMD_BACKSPACE,
        127: CMD_BACKSPACE,  # Alternative backspace
        curses.KEY_DC: CMD_DELETE,
        10: CMD_ENTER,
        13: CMD_ENTER,
        curses.KEY_ENTER: CMD_ENTER,
        9: CMD_TAB,
        CTRL_A: CMD_HOME,
        CTRL_E: CMD_END,
        CTRL_Y: CMD_PAGE_UP,
        CTRL_V: CMD_PAGE_DOWN,
        CTRL_O: CMD_SAVE,
        CTRL_X: CMD_EXIT,
        CTRL_W: CMD_SEARCH,
        CTRL_K: CMD_CUT,
        CTRL_U: CMD_PASTE,
        CTRL_L: CMD_REFRESH,
        CTRL_T: CMD_TOGGLE_EXPLORER,
        CTRL_B: CMD_TOGGLE_TERMINAL,
        curses.KEY_RESIZE: CMD_RESIZE,
    }

    cmd = key_map.get(key)
    if cmd:
        return cmd, None

    # Printable character
    if 32 <= key <= 126 or key >= 128:
        try:
            return CMD_INSERT, chr(key)
        except (ValueError, OverflowError):
            return None, None

    return None, None
