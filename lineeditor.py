import urwid


class LineEditor(urwid.Edit):
    __metaclass__ = urwid.signals.MetaSignals
    signals = ['done']

    def keypress(self, size, key):
        if key == 'enter':
            urwid.emit_signal(self, 'done', self.get_edit_text())
            return

        if key == 'esc':
            urwid.emit_signal(self, 'done', None)
            return

        if key == 'ctrl l':
            self.set_edit_text("")

        if key == 'ctrl a':
            self.set_edit_pos(0)

        if key == 'ctrl e':
            self.set_edit_pos(len(self.get_edit_text()))

        return urwid.Edit.keypress(self, size, key)
