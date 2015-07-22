# Copyright (C) 2015 James E. Blair <corvus@gnu.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import sys
import datetime
import time

import urwid

import palette
import client
import slide
import rst

PALETTE = [
    ('reversed', 'standout', ''),
    ('status', 'light red', ''),
]

class Row(urwid.Button):
    def __init__(self, index, title, console):
        super(Row, self).__init__('', on_press=console.jump, user_data=index)
        col = urwid.Columns([
                ('fixed', 3, urwid.Text('%-2i' % (index+1))),
                urwid.Text(title),
                ])
        self._w = urwid.AttrMap(col, None, focus_map='reversed')

    def selectable(self):
        return True

class Footer(urwid.WidgetWrap):
    def __init__(self):
        super(Footer, self).__init__(urwid.Columns([]))
        self.position = urwid.Text(u'')
        self.timer = urwid.Text(u'')
        self._w.contents.append((self.position, ('pack', None, False)))
        self._w.contents.append((urwid.Text(u''), ('weight', 1, False)))
        self._w.contents.append((self.timer, ('pack', None, False)))

class Screen(urwid.WidgetWrap):
    def __init__(self, console):
        super(Screen, self).__init__(urwid.Pile([]))
        self.console = console
        self.program = []
        self.current = -1
        self.progressive_state = 0
        self.blank_slide = slide.UrwidSlide(
            u'', None, urwid.Text(u''), None)
        self.timer = 45*60
        self.size = (80, 25)
        self.timer_end = None
        self.listbox = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self.footer = Footer()
        footer = urwid.AttrMap(self.footer, 'status')
        self.left = urwid.Pile([])
        self.left.contents.append((self.listbox, ('weight', 1)))
        self.left.set_focus(0)

        self.right = urwid.Pile([])
        self.setPreviews()

        self.main = urwid.Columns([])
        self.main.contents.append((self.left, ('weight', 1, False)))
        self.main.contents.append((self.right, ('given', self.size[0]+2, False)))
        self.main.set_focus(0)

        self._w.contents.append((self.main, ('weight', 1)))
        self._w.contents.append((footer, ('pack', 1)))
        self._w.set_focus(0)

    def setPreviews(self):
        current_slide = next_slide = self.blank_slide
        if 0 <= self.current < len(self.program):
            current_slide = self.program[self.current]
        if 0 <= self.current+1 < len(self.program):
            next_slide = self.program[self.current+1]
        current_slide.setProgressive(self.progressive_state)
        current_box = urwid.LineBox(current_slide, "Current")
        next_box = urwid.LineBox(next_slide, "Next")
        if current_slide.handout:
            notes_box = urwid.LineBox(current_slide.handout, "Notes")
        else:
            notes_box = None
        self.right.contents[:] = []
        self.left.contents[:] = self.left.contents[:1]
        cols, rows = self.size
        self.right.contents.append((current_box, ('given', rows+2)))
        self.right.contents.append((next_box, ('given', rows+2)))
        self.right.contents.append((urwid.Filler(urwid.Text(u'')), ('weight', 1)))
        if notes_box:
            self.left.contents.append((notes_box, ('pack', None)))

    def setProgram(self, program):
        self.program = program
        self.listbox.body[:] = []
        for i, s in enumerate(program):
            self.listbox.body.append(Row(i, s.title, self.console))

    def setSize(self, size):
        self.size = size
        cols, rows = size
        self.right.contents[0] = (self.right.contents[0][0], ('given', rows+2))
        self.right.contents[1] = (self.right.contents[1][0], ('given', rows+2))
        self.main.contents[1] = (self.main.contents[1][0], ('given', cols+2, False))

    # Implement this method from the urwid screen interface for the ScreenHinter
    def get_cols_rows(self):
        return self.size

    def setCurrent(self, state):
        index, progressive_state = state
        changed = False
        if index != self.current:
            self.current = index
            self.listbox.set_focus(index)
            self.listbox._invalidate()
            self.footer.position.set_text('%i / %i' % (index+1, len(self.program)))
            changed = True
        if progressive_state != self.progressive_state:
            self.progressive_state = progressive_state
            changed = True
        if changed:
            self.setPreviews()
        self.footer.timer.set_text(self.getTime())

    def getTime(self):
        now = time.time()
        if self.timer_end:
            return str(datetime.timedelta(seconds=(int(self.timer_end-now))))
        else:
            return str(datetime.timedelta(seconds=int(self.timer)))

    def setTimer(self, secs):
        self.timer = secs
        if self.timer_end:
            now = time.time()
            self.timer_end = now + self.timer

    def startStopTimer(self):
        now = time.time()
        if self.timer_end:
            remain = max(self.timer_end - int(now), 0)
            self.timer = remain
            self.timer_end = None
        else:
            self.timer_end = now + self.timer

    def keypress(self, size, key):
        if key in (' ', 'x'):
            self.startStopTimer()
        elif key == 'page up':
            self.console.prev()
        elif key == 'page down':
            self.console.next()
        elif key == 'right':
            self.console.next()
        elif key == 'left':
            self.console.prev()
        elif key == 't':
            self.console.timerDialog()
        elif key == 'q':
            raise urwid.ExitMainLoop()
        else:
            return super(Screen, self).keypress(size, key)
        return None

class FixedButton(urwid.Button):
    def sizing(self):
        return frozenset([urwid.FIXED])

    def pack(self, size, focus=False):
        return (len(self.get_label())+4, 1)

class TimerDialog(urwid.WidgetWrap):
    signals = ['set', 'cancel']
    def __init__(self):
        set_button = FixedButton('Set')
        cancel_button = FixedButton('Cancel')
        urwid.connect_signal(set_button, 'click',
                             lambda button:self._emit('set'))
        urwid.connect_signal(cancel_button, 'click',
                             lambda button:self._emit('cancel'))
        button_widgets = [('pack', set_button),
                          ('pack', cancel_button)]
        button_columns = urwid.Columns(button_widgets, dividechars=2)
        rows = []
        self.entry = urwid.Edit('Timer: ', edit_text='45:00')
        rows.append(self.entry)
        rows.append(urwid.Divider())
        rows.append(button_columns)
        pile = urwid.Pile(rows)
        fill = urwid.Filler(pile, valign='top')
        super(TimerDialog, self).__init__(urwid.LineBox(fill, 'Timer'))

    def keypress(self, size, key):
        r = super(TimerDialog, self).keypress(size, key)
        if r == 'enter':
            self._emit('set')
            return None
        elif r == 'esc':
            self._emit('cancel')
            return None
        return r

class Console(object):
    poll_interval = 0.5

    def __init__(self, program):
        self.screen = Screen(self)
        self.loop = urwid.MainLoop(self.screen, palette=PALETTE)
        self.client = client.Client()
        self.screen.setProgram(program)
        self.update()
        self.loop.set_alarm_in(self.poll_interval, self.updateCallback)

    def run(self):
        self.loop.run()

    def jump(self, widget, index):
        self.screen.setCurrent(self.client.jump(index))

    def next(self):
        self.screen.setCurrent(self.client.next())

    def prev(self):
        self.screen.setCurrent(self.client.prev())

    def updateCallback(self, loop=None, data=None):
        self.update()
        self.loop.set_alarm_in(self.poll_interval, self.updateCallback)

    def update(self):
        self.screen.setSize(self.client.size())
        self.screen.setCurrent(self.client.current())

    def timerDialog(self):
        dialog = TimerDialog()
        overlay = urwid.Overlay(dialog, self.loop.widget,
                                'center', 30,
                                'middle', 6)
        self.loop.widget = overlay
        urwid.connect_signal(dialog, 'cancel', self.cancelDialog)
        urwid.connect_signal(dialog, 'set', self.setTimer)

    def cancelDialog(self, widget):
        self.loop.widget = self.screen

    def setTimer(self, widget):
        parts = widget.entry.edit_text.split(':')
        secs = 0
        if len(parts):
            secs += int(parts.pop())
        if len(parts):
            secs += int(parts.pop())*60
        if len(parts):
            secs += int(parts.pop())*60*60
        self.screen.setTimer(secs)
        self.loop.widget = self.screen


def main():
    parser = argparse.ArgumentParser(
        description='Console-based presentation system')
    parser.add_argument('--light', dest='light',
                        default=False,
                        action='store_true',
                        help='use a black on white palette')
    parser.add_argument('file',
                        help='presentation file (RST)')
    args = parser.parse_args()
    if args.light:
        plt = palette.LIGHT_PALETTE
    else:
        plt = palette.DARK_PALETTE
    hinter = slide.ScreenHinter()
    parser = rst.PresentationParser(plt, hinter)
    program = parser.parse(open(args.file).read())
    c = Console(program)
    hinter.setScreen(c.screen)
    c.run()
