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

import urwid

class SlidePile(urwid.Pile):
    def pack(self, size, focus=False):
        cols = 0
        rows = 0
        for x in self.contents:
            c,r = x[0].pack((size[0],))
            if c>cols:
                cols = c
            rows += r
        return (cols, rows)

class SlidePadding(urwid.Padding):
    def pack(self, size, focus=False):
        r = self._original_widget.pack(size, focus)
        width = max(r[0] + self.left + self.right, self.min_width)
        width = min(size[0], width)
        return (width, r[1])

class SlideColumns(urwid.Columns):
    def pack(self, size, focus=False):
        cols = self.dividechars * (len(self.contents)-1)
        rows = 0
        for widget, packing in self.contents:
            if packing[0] == 'given':
                allocated_cols = packing[1]
            else:
                allocated_cols = size[0]
            c,r = widget.pack((allocated_cols,))
            if packing[0] == 'given':
                c = allocated_cols
            if r>rows:
                rows = r
            cols += c
        return (cols, rows)

class SlideFiller(urwid.Filler):
    pass

class ScreenHinter(object):
    # A terrible hack to try to provide some needed context to the
    # image widget.
    def __init__(self, screen=None):
        self.screen = screen

    def setScreen(self, screen):
        self.screen = screen

    def getSize(self):
        cols, rows = self.screen.get_cols_rows()
        return (cols, rows-1)

class Handout(urwid.WidgetWrap):
    def __init__(self, widget, background):
        self.background = background
        self.pad = SlidePadding(widget, align='center', width='pack')
        self.map = urwid.AttrMap(self.pad, self.background)
        super(Handout, self).__init__(self.map)

class UrwidSlide(urwid.WidgetWrap):
    def __init__(self, title, transition, widget, background):
        self.title = title
        self.transition = transition
        self.fill = SlideFiller(widget)
        self.background = background
        self.map = urwid.AttrMap(self.fill, self.background)
        self.handout = None
        self.animations = []
        self.progressives = []
        self.progressive_attr = None
        self.progressive_state = 0
        super(UrwidSlide, self).__init__(self.map)

    def startAnimation(self, loop):
        for x in self.animations:
            x.startAnimation(loop)

    def stopAnimation(self):
        for x in self.animations:
            x.stopAnimation()

    def resetAnimation(self):
        for x in self.animations:
            x.resetAnimation()

    def resetProgressive(self, on=False):
        if on:
            self.progressive_state = len(self.progressives)
            for x in self.progressives:
                x.set_attr_map({None: None})
        else:
            self.progressive_state = 0
            for x in self.progressives:
                x.set_attr_map({None: self.progressive_attr})

    def nextProgressive(self):
        if self.progressive_state >= len(self.progressives):
            return False
        self.progressives[self.progressive_state].set_attr_map(
            {None: None})
        self.progressive_state += 1
        return True

    def prevProgressive(self):
        if self.progressive_state <= 0:
            return False
        self.progressive_state -= 1
        self.progressives[self.progressive_state].set_attr_map(
            {None: self.progressive_attr})
        return True

    def setProgressive(self, state):
        self.progressive_state = state
        for i, x in enumerate(self.progressives):
            if i < self.progressive_state:
                x.set_attr_map({None: None})
            else:
                x.set_attr_map({None: self.progressive_attr})

class AnimatedText(urwid.Text):
    def __init__(self, interval=0.5, oneshot=False):
        super(AnimatedText, self).__init__(u'')
        self.frames = []
        self.current = 0
        self.running = False
        self.interval = interval
        self.oneshot = oneshot

    def addFrame(self, text):
        self.frames.append(text)
        if len(self.frames) == self.current+1:
            self.set_text(text)

    def startAnimation(self, loop):
        if self.running:
            return
        if len(self.frames) == 1:
            return
        self.running = True
        loop.set_alarm_in(self.interval, self.updateCallback)

    def updateCallback(self, loop=None, data=None):
        if not self.running:
            return
        if self.current+1 >= len(self.frames):
            if self.oneshot:
                self.running = False
                return
            self.current = 0
        else:
            self.current += 1
        self.set_text(self.frames[self.current])
        loop.set_alarm_in(self.interval, self.updateCallback)

    def stopAnimation(self):
        if not self.running:
            return
        self.running = False

    def resetAnimation(self):
        self.current = 0
        self.set_text(self.frames[self.current])
