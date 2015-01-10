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

import re

import urwid

class ANSIParser(object):
    colors = [
        urwid.BLACK,
        urwid.DARK_RED,
        urwid.DARK_GREEN,
        urwid.BROWN,
        urwid.DARK_BLUE,
        urwid.DARK_MAGENTA,
        urwid.DARK_CYAN,
        urwid.LIGHT_GRAY,
        urwid.DARK_GRAY,
        urwid.LIGHT_RED,
        urwid.LIGHT_GREEN,
        urwid.YELLOW,
        urwid.LIGHT_BLUE,
        urwid.LIGHT_MAGENTA,
        urwid.LIGHT_CYAN,
        urwid.WHITE,
        ]

    colors256 = ['0', '6', '8', 'a', 'd', 'f']
    colorsgray = ['3', '7', '11', '13', '15', '19', '23', '27', '31',
                  '35', '38', '42', '46', '50', '52', '58', '62', '66',
                  '70', '74', '78', '82', '85', '89', '93']

    def __init__(self):
        self.x = 0
        self.y = 0
        self.text_lines = []
        self.attr_lines = []
        self.background = urwid.AttrSpec('light gray', 'black')
        self.attr = self.background
        self.resetColor()
        self.moveTo(0,0)

    def resetColor(self):
        self.bold = False
        self.blink = False
        self.fg = 7
        self.bg = 0
        self.bg256 = None
        self.fg256 = None

    def moveTo(self, x, y):
        while x>80:
            x-=80
            y+=1
        while y+1 > len(self.text_lines):
            self.text_lines.append([u' ' for i in range(80)])
            self.attr_lines.append([self.attr for i in range(80)])
        self.x = x
        self.y = y

    def parseSequence(self, seq):
        values = []
        buf = ''
        for c in seq:
            if c in ['\x1b', '[']:
                continue
            if c == ';':
                values.append(int(buf))
                buf = ''
                continue
            if ord(c) < 64:
                buf += c
        if buf:
            values.append(int(buf))
        if c == 'm':
            if not values:
                values = [0]
            for v in values:
                if self.fg256 is True:
                    if v <= 0x08:
                        self.fg = v
                    elif v <= 0x0f:
                        self.fg = v - 0x08
                        self.bold = True
                    elif v <= 0xe7:
                        r, x = divmod(v-16, 36)
                        g, x = divmod(x, 6)
                        b = x % 6
                        self.fg256 = ('#' +
                                      self.colors256[r] +
                                      self.colors256[g] +
                                      self.colors256[b])
                    else:
                        self.fg256 = 'g' + str(self.colorsgray[v-232])
                elif self.bg256 is True:
                    if v <= 0x08:
                        self.bg = v
                    #elif v <= 0x0f:
                    #    self.bg = v - 0x08
                    #    self.bold = True
                    elif v <= 0xe7:
                        r, x = divmod(v-16, 36)
                        g, x = divmod(x, 6)
                        b = x % 6
                        self.bg256 = ('#' +
                                      self.colors256[r] +
                                      self.colors256[g] +
                                      self.colors256[b])
                    else:
                        self.bg256 = 'g' + str(self.colorsgray[v-232])
                elif v == 0:
                    self.resetColor()
                elif v == 1:
                    self.bold = True
                elif v == 5:
                    self.blink = True
                elif v>29 and v<38:
                    self.fg = v-30
                    self.fg256 = None
                elif v>39 and v<48:
                    self.bg = v-40
                    self.bg256 = None
                elif v==38:
                    self.fg256=True
                elif v==48:
                    self.bg256=True
            fg = self.fg
            if self.bold:
                fg += 8
            fgattrs = []
            if self.blink:
                fgattrs.append('blink')
            if self.fg256:
                fgattrs.append(self.fg256)
            else:
                fgattrs.append(self.colors[fg])
            if self.bg256:
                bg = self.bg256
            else:
                bg = self.colors[self.bg]
            self.attr = urwid.AttrSpec(', '.join(fgattrs), bg)
        if c == 'A':
            if not values:
                values = [1]
            y = max(self.y-values[0], 0)
            self.moveTo(self.x, y)
        if c == 'C':
            if not values:
                values = [1]
            x = self.x + values[0]
            self.moveTo(x, self.y)
        if c == 'H':
            self.moveTo(values[1]-1, values[0]-1)

    def parse(self, data):
        seq = ''
        for char in data:
            if seq:
                seq += char
                if ord(char) >= 64 and char != '[':
                    self.parseSequence(seq)
                    seq = ''
                continue
            if char == '\x1a':
                continue
            if char == '\x1b':
                seq = char
                continue
            if char == '\r':
                self.moveTo(0, self.y)
                continue
            if char == '\n':
                self.moveTo(self.x, self.y+1)
                continue
            if not seq:
                self.text_lines[self.y][self.x] = char
                self.attr_lines[self.y][self.x] = self.attr
                x = self.x + 1
                self.moveTo(x, self.y)
        text = []
        current_attr = self.attr_lines[0][0]
        current_text = u''
        for y in range(len(self.text_lines)):
            for x in range(80):
                char = self.text_lines[y][x]
                attr = self.attr_lines[y][x]
                if (attr.foreground_number != current_attr.foreground_number or
                    attr.background_number != current_attr.background_number):
                    text.append((current_attr, current_text))
                    current_attr = attr
                    current_text = u''
                current_text += char
            if (current_attr.background_number==0):
                current_text = current_text.rstrip(' ')
            current_text += u'\n'
        current_text = re.sub('\n+$', '\n', current_text)
        text.append((current_attr, current_text))
        return text
