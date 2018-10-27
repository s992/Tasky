#!/usr/bin/python
# -*- coding: latin-1 -*-

import urwid
import subprocess

from lib.taskwarrior import TaskWarrior, Utility
from lib.taskwidget import TaskWidget
from lib.lineeditor import LineEditor
from lib.scrollinglistbox import ScrollingListBox
from lib.config import Config


class Tasky(object):
    palette = [
        ('proj', '', '', '', 'dark green', ''),
        ('proj_focus', '', '', '', 'black', 'dark green'),
        ('body', '', '', '', 'dark blue', ''),
        ('body_focus', '', '', '', 'black', 'dark cyan'),
        ('body_emph', '', '', '', 'light red', ''),
        ('body_emph_focus', '', '', '', 'black', 'dark magenta'),
        ('head', '', '', '', 'light red', 'black'),
        ('dim', '', '', '', 'g54', 'black')
    ]

    def __init__(self):

        self.warrior = TaskWarrior()
        self.config = Config()

        self.default_limit = self.config.get_default_filter()
        self.limit = self.default_limit
        self.show_annotations = []

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
        self.loop = loop
        urwid.connect_signal(self.walker, 'modified', update_header)
        loop.screen.set_terminal_properties(colors=256)
        loop.run()

    def refresh(self):
        limit = self.limit or ''
        self.walker[:] = [TaskWidget(task, task.uuid() in self.show_annotations) for task in self.warrior.pending_tasks(limit)]

    def sync(self):
        self.warrior.sync()
        self.refresh()

    def keystroke(self, input):
        def exit():
            raise urwid.ExitMainLoop()

        def undo():
            self.warrior.undo()
            self.refresh()

        view_action_map = {
            'q': exit,
            'Q': exit,
            'r': self.sync,
            'u': undo,
            'i': self.new_inbox,
            't': self.new_task,
            ':': self.command_mode,
            '!': self.shell_mode,
            '/': self.change_limit,
            '-': self.all,
            'b': self.clear_limit,
        }

        task_action_map = {
            'enter': (self.edit_task, False),
            'e': (self.edit_task_detail, True),
            'n': (self.task_annotate, True),
            'N': (self.task_note, True),
            'c': (self.warrior.complete, True),
            'd': (self.warrior.delete, True),
            ' ': (self.warrior.toggle_active, True),
            'y': (self.copy_description, False),
            'Y': (self.copy_notes, False),
            'o': (self.open_browser, False),
            'a': (self.toggle_annotations, True),
            'A': (self.toggle_all_annotations, True),
            'T': (self.new_task_with_defaults, True),
            's': (self.sleep_task, True),
        }

        config_bind = self.config.get_bind(input)

        if config_bind and len(config_bind):
            self.limit = config_bind
            self.refresh()
            return

        if input in view_action_map:
            view_action_map[input]()
            return

        if input in task_action_map:
            (action, should_refresh) = task_action_map[input]
            action(self.selected_task())
            if should_refresh:
                self.refresh()

    def selected_task(self):
        return self.list_box.get_focus()[0].task

    def task_annotate(self, task):
        self.edited_task = task
        self.present_editor(' >> ', '', self.annotate_done)

    def task_note(self, task):
        self.loop.stop()
        subprocess.check_call(['tasknote %s' % str(task.id())], shell=True)
        self.loop.start()

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

    def all(self):
        self.limit = ''
        self.refresh()

    def clear_limit(self):
        self.limit = self.default_limit
        self.refresh()

    def copy_description(self, task):
        Utility.write_to_clipboard(task.description())

    def copy_notes(self, task):
        notes = [note[u'description'] for note in task.annotations()]
        Utility.write_to_clipboard("\n".join(notes))

    def open_browser(self, task):
        urls = []

        if Utility.is_url(task.description()):
            urls.append(task.description())

        possibles = [v[u'description'] for v in task.annotations() if Utility.is_url(v[u'description'])]
        urls.extend(possibles)

        for url in urls:
            Utility.run_command('open -a "Google Chrome" %s' % url)

    def toggle_annotations(self, task):
        if not len(task.annotations()):
            return

        if task.uuid() in self.show_annotations:
            self.show_annotations.remove(task.uuid())
        else:
            self.show_annotations.append(task.uuid())

    def toggle_all_annotations(self, task):
        if len(self.show_annotations):
            self.show_annotations = []
        else:
            limit = self.limit or ''
            self.show_annotations = [t.uuid() for t in self.warrior.pending_tasks(limit)]

    def edit_task(self, task):
        self.edited_task = task
        self.present_editor(' >> ', task.description(), self.edit_done)

    def sleep_task(self, task):
        self.edited_task = task
        self.present_editor(' >> ', 'wait:', self.edit_done)

    def edit_task_detail(self, task):
        self.loop.stop()
        subprocess.check_call(['task %s edit' % str(task.id())], shell=True)
        self.loop.start()

    def new_task(self, prefilled=''):
        self.present_editor(' >> ', prefilled, self.new_done)

    def new_inbox(self):
        self.new_task('+in ')

    def new_task_with_defaults(self, task):
        project = task.project()
        tags = task.tags_string()
        prefilled = ''

        if project:
            prefilled += 'pro:{} '.format(project)

        prefilled += '{} '.format(tags)

        self.new_task(prefilled)

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
        self.loop.stop()
        subprocess.check_call(['/bin/zsh', '-i', '-c', content])
        self.loop.start()

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
