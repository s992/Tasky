#!/usr/bin/python
# -*- coding: latin-1 -*-

import urwid
import sys

from taskwarrior import TaskWarrior, Utility
from taskwidget import TaskWidget
from lineeditor import LineEditor
from scrollinglistbox import ScrollingListBox


class Tasky(object):

    palette = [
        ('proj', '', '', '', 'dark green', ''),
        ('proj_focus', '', '', '', 'black', 'dark green'),
        ('body','', '', '', 'dark blue', ''),
        ('body_focus', '', '', '', 'black', 'dark cyan'),
        ('body_emph','', '', '', 'light red', ''),
        ('body_emph_focus', '', '', '', 'black', 'dark magenta'),
        ('head', '', '', '',  'light red', 'black'),
        ('dim', '', '', '', 'g54', 'black')
    ]

    def __init__(self):

        self.warrior = TaskWarrior()

        self.default_limit = '-in -future -rnr'
        self.limit = self.default_limit

        header = urwid.AttrMap(urwid.Text('tasky.α'), 'head')
        self.walker = urwid.SimpleListWalker([])
        self.list_box = ScrollingListBox(self.walker)
        self.view = urwid.Frame(urwid.AttrWrap(self.list_box, 'body'))
        self.refresh()

        def update_header():
            limit = ' | ' + self.limit if self.limit else ''
            header_text = ['tasky.α', ('dim', limit)]
            self.view.set_header(urwid.AttrMap(urwid.Text(header_text), 'head'))

        update_header()

        loop = urwid.MainLoop(self.view, Tasky.palette, unhandled_input=self.keystroke)
        urwid.connect_signal(self.walker, 'modified', update_header)
        loop.screen.set_terminal_properties(colors=256)
        loop.run()

    def refresh(self):
        limit = self.limit or ''
        self.walker[:] = map(TaskWidget, self.warrior.pending_tasks(limit))

    def keystroke(self, input):
        def exit():
            raise urwid.ExitMainLoop()

        def undo():
            self.warrior.undo()
            self.refresh()

        view_action_map = {
            'q': exit,
            'Q': exit,
            'r': self.refresh,
            'u': undo,
            'i': self.new_task,
            ':': self.command_mode,
            '!': self.shell_mode,
            '/': self.change_limit,
            'I': self.inbox,
            'R': self.rnr,
            'F': self.future,
            'W': self.work,
            'P': self.personal,
            'A': self.all,
            'b': self.clear_limit
        }

        task_action_map = {
            'enter': (self.edit_task, False),
            'e': (self.edit_task, False),
            'n': (self.task_note, True),
            'c': (self.warrior.complete, True),
            'd': (self.warrior.delete, True),
            ' ': (self.warrior.toggle_active, True)
        }

        if input in view_action_map:
            view_action_map[input]()

        if input in task_action_map:
            (action, should_refresh) = task_action_map[input]
            action(self.selected_task())
            if should_refresh:
                self.refresh()

    def selected_task(self):
        return self.list_box.get_focus()[0].task


    def task_note(self, task):
        self.edited_task = task
        self.present_editor(' >> ', '', self.annotate_done)

    def present_editor(self, prompt, text, handler):
        self.foot = LineEditor(prompt, text)
        self.view.set_footer(self.foot)
        self.view.set_focus('footer')
        urwid.connect_signal(self.foot, 'done', handler)

    def command_mode(self):
        self.present_editor(': ', '', self.command_done)

    def shell_mode(self):
        self.present_editor('! ', '', self.shell_done)

    def change_limit(self):
        self.present_editor('Filter: ', '', self.limit_done)

    def inbox(self):
        self.limit = '+in'
        self.refresh()

    def rnr(self):
        self.limit = '+rnr'
        self.refresh()

    def future(self):
        self.limit = '+future'
        self.refresh()

    def work(self):
        self.set_limit('+work or +review')

    def personal(self):
        self.set_limit('+personal')

    def all(self):
        self.limit = ''
        self.refresh()

    def set_limit(self, limit):
        self.limit = self.default_limit + ' ' + limit
        self.refresh()

    def clear_limit(self):
        self.limit = self.default_limit
        self.refresh()

    def edit_task(self, task):
        self.edited_task = task
        self.present_editor(' >> ', task.description(), self.edit_done)

    def new_task(self):
        self.present_editor(' >> ', '', self.new_done)


    def dismiss_editor(action):
        def wrapped(self, content):
            self.view.set_focus('body')
            urwid.disconnect_signal(self, self.foot, 'done', action)
            if content is not None:
                action(self, content)
            self.view.set_footer(None)
        return wrapped

    @dismiss_editor
    def edit_done(self, content):
        self.warrior.mod(self.edited_task, content)
        self.edited_task = None
        self.refresh()

    @dismiss_editor
    def new_done(self, content):
        self.warrior.add(content)
        self.refresh()

    @dismiss_editor
    def command_done(self, content):
        Utility.run_command('task ' + content)
        self.refresh()

    @dismiss_editor
    def shell_done(self, content):
        Utility.run_command("tmux split-window '%s'" % content)

    @dismiss_editor
    def limit_done(self, content):
        self.limit = content
        self.refresh()

    @dismiss_editor
    def annotate_done(self, content):
        self.warrior.annotate(self.edited_task, content)
        self.edited_task = None
        self.refresh()


Tasky()
