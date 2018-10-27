import urwid


class ScrollingListBox(urwid.ListBox):

    def scroll_down(self):
        self.down_by(1)

    def scroll_up(self):
        self.up_by(1)

    def page_down(self):
        self.down_by(5)

    def page_up(self):
        self.up_by(5)

    def top(self):
        self.set_focus(0)

    def bottom(self):
        self.set_focus(len(self.body.positions()) - 1)

    def down_by(self, n):
        focus = self.focus_position or 0
        new_focus = min(focus + n, len(self.body.positions()) - 1)

        self.set_focus(new_focus)

    def up_by(self, n):
        focus = self.focus_position or 0
        new_focus = max(focus - n, 0)

        self.set_focus(new_focus)

    def mouse_event(self, size, event, button, col, row, focus):
        button_map = {
            4: self.scroll_down,
            5: self.scroll_up
        }

        if button in button_map:
            button_map[button]()

        return urwid.ListBox.mouse_event(self, size, event, button, col, row, focus)

    def keypress(self, size, key):
        key_map = {
            'j': self.scroll_down,
            'k': self.scroll_up,
            'ctrl d': self.page_down,
            'ctrl u': self.page_up,
            'g': self.top,
            'G': self.bottom,
        }

        if key in key_map:
            key_map[key]()

        return urwid.ListBox.keypress(self, size, key)
