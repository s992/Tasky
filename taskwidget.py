import urwid


class TaskWidget(urwid.WidgetWrap):

    def __init__(self, task, showing_annotations):
        self.task = task

        desc = urwid.Text(task.description())
        proj = urwid.Text(task.project())

        due = urwid.Text(task.due_date_string() + ' ', align='right')
        tags = urwid.Text(task.tags_string() + ' ', align='right')
        notes = urwid.Text(str(len(task.annotations())), align='right')

        (style, style_focus) = ('body', 'body_focus')
        if task.start_date() is not None:
            (style, style_focus) = ('body_emph', 'body_emph_focus')

        item = urwid.AttrMap(urwid.Columns([
            ('fixed', 30, urwid.AttrWrap(proj, 'proj', 'proj_focus')),
            desc,
            tags,
            ('fixed', 2, notes),
            ('fixed', 11, due)
        ]), style, style_focus)

        if showing_annotations:
            annotations = [urwid.Columns([('fixed', 33, urwid.Text('')), urwid.Text('-> ' + n[u'description'])]) for n
                           in task.annotations()]
            row = urwid.Pile([item] + annotations)
            urwid.WidgetWrap.__init__(self, row)
        else:
            urwid.WidgetWrap.__init__(self, item)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key
