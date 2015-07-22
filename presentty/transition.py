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

class Transition(urwid.Widget):
    def __init__(self, duration=0.4):
        super(Transition, self).__init__()
        self.duration = duration
        self.old = None
        self.new = None
        self.progress = 0.0

    def getDuration(self):
        return self.duration

    def setTargets(self, old, new):
        self.old = old
        self.new = new
        self.setProgress(0.0)

    def setProgress(self, progress):
        self.progress = progress
        self._invalidate()

class PanTransition(Transition):
    def render(self, size, focus=False):
        old = self.old.render((size[0], size[1]))
        new = self.new.render((size[0], size[1]))
        c = urwid.CanvasJoin([(old, None, False, size[0]),
                              (new, None, False, size[0])])
        #c = urwid.CanvasOverlay(new, old, 6, 0)
        offset = int(size[0] * self.progress)
        c.pad_trim_left_right(0-offset, 0-(size[0]-offset))
        return c

class TiltTransition(Transition):
    def render(self, size, focus=False):
        old = self.old.render((size[0], size[1]))
        new = self.new.render((size[0], size[1]))
        c = urwid.CanvasCombine([(old, None, False),
                              (new, None, False)])
        offset = int(size[1] * self.progress)
        c.pad_trim_top_bottom(0-offset, 0-(size[1]-offset))
        return c

class DissolveTransition(Transition):
    def __init__(self, *args, **kw):
        super(DissolveTransition, self).__init__(*args, **kw)
        self._oldbuf = None
        self._newbuf = None
        self._cache_size = None

    def setTargets(self, old, new):
        if old != self.old:
            self._oldbuf = None
            self._cache_size = None
        if new != self.new:
            self._newbuf = None
            self._cache_size = None
        super(DissolveTransition, self).setTargets(old, new)

    def _to_buf(self, canvas):
        buf = []
        for line in canvas.content():
            for (attr, cs, text) in line:
                for char in unicode(text, 'utf8'):
                    buf.append((attr, cs, char))
        return buf

    def render(self, size, focus=False):
        if self._cache_size != size:
            old = self.old.render((size[0], size[1]))
            new = self.new.render((size[0], size[1]))
            self._oldbuf = self._to_buf(old)
            self._newbuf = self._to_buf(new)
            self._cache_size = size
        line_list = []
        attr_list = []
        line_text = ''
        line_attrs = []
        current_attr = [None, 0]
        current_rgb = None
        current_props = None
        background = urwid.AttrSpec('light gray', 'black')
        for i in range(len(self._oldbuf)):
            oldattr, oldcs, oldchar = self._oldbuf[i]
            newattr, newcs, newchar = self._newbuf[i]
            oldrgb = oldattr.get_rgb_values()
            newrgb = newattr.get_rgb_values()
            if None in oldrgb:
                oldrgb = background.get_rgb_values()
            if None in newrgb:
                newrgb = background.get_rgb_values()
            if newchar == ' ':
                char = oldchar
                charattr = oldattr
                newrgb = newrgb[3:]*2
            elif oldchar == ' ':
                char = newchar
                charattr = newattr
                oldrgb = oldrgb[3:]*2
            elif self.progress >= 0.5:
                char = newchar
                charattr = newattr
            else:
                char = oldchar
                charattr = oldattr
            char = char.encode('utf8')
            line_text += char
            rgb = []
            props = []
            if charattr.bold:
                props.append('bold')
            if charattr.underline:
                props.append('underline')
            if charattr.standout:
                props.append('standout')
            if charattr.blink:
                props.append('blink')
            for x in range(len(oldrgb)):
                rgb.append(int(((newrgb[x]-oldrgb[x])*self.progress)+oldrgb[x])>>4)
            if current_rgb == rgb and current_props == props:
                current_attr[1] += len(char)
            else:
                if current_attr[0]:
                    line_attrs.append(tuple(current_attr))
                fg = ', '.join(props + ['#%x%x%x' % tuple(rgb[:3])])
                bg = '#%x%x%x' % tuple(rgb[3:])
                attr = urwid.AttrSpec(fg, bg)
                current_attr = [attr, len(char)]
                current_rgb = rgb
                current_props = props
            if (i+1) % size[0] == 0:
                line_attrs.append(tuple(current_attr))
                current_attr = [None, 0]
                current_rgb = None
                line_list.append(line_text)
                line_text = ''
                attr_list.append(line_attrs)
                line_attrs = []
        canvas = urwid.TextCanvas(line_list, attr_list)
        return canvas

class CutTransition(Transition):
    def __init__(self, *args, **kw):
        super(CutTransition, self).__init__(*args, **kw)
        self.duration = 0.0

    def render(self, size, focus=False):
        return self.new.render(size, focus)
