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

import subprocess
import HTMLParser
import re

import PIL
import PIL.ExifTags
import urwid

import slide

def nearest_color(x):
    if x < 0x30: return '0'
    if x < 0x70: return '6'
    if x < 0x98: return '8'
    if x < 0xc0: return 'a'
    if x < 0xe8: return 'd'
    return 'f'

class ANSIImage(urwid.Widget):
    def __init__(self, uri, hinter=None, scale=1, background=None):
        super(ANSIImage, self).__init__()
        self.uri = uri
        image = self._loadImage()
        self.htmlparser = HTMLParser.HTMLParser()
        self.ratio = float(image.size[0])/float(image.size[1])
        self.hinter = hinter
        if scale > 1:
            scale = 1
        self.scale = scale
        self.background = background or 'black'
        self._prime = True
        self.render((3,1))
        self._prime = False

    def _loadImage(self):
        image = PIL.Image.open(self.uri)
        image.load()
        try:
            exif = image._getexif()
        except AttributeError:
            # No info on whether we should rotate image
            exif = None
        if exif:
            orientation = exif.get(274, 1)
            if orientation == 1:
                pass
            elif orientation == 3:
                image = image.rotate(180)
            elif orientation == 6:
                image = image.rotate(-90)
            elif orientation == 8:
                image = image.rotate(90)
        return image

    def pack(self, size, focus=False):
        cols = size[0]
        if len(size) > 1:
            rows = size[1]
        elif self.hinter:
            rows = self.hinter.getSize()[1]
        else:
            rows = None
        width = cols
        height = int(cols*(1.0/self.ratio)/2.0)
        if rows is not None and height > rows:
            height = rows
            width = int(rows*self.ratio*2.0)
        return (width, height)

    def rows(self, size, focus=False):
        r = self.pack(size)
        return r[1]

    def _blank(self, width, height):
        ret = []
        for y in range(height):
            ret.append("<span style='color:#000000; background-color:#000000;'>%s</span>" % ('.'*width))
        return '<br/>'.join(ret)

    SPAN_RE = re.compile(r"<span style='color:#(......); background-color:#(......);'>(.*)")
    def render(self, size, focus=False):
        spanre = self.SPAN_RE
        htmlparser = self.htmlparser

        # Calculate image size and any bounding box
        total_width, total_height = self.pack(size, focus)
        width, height = self.pack([s * self.scale for s in size], focus)
        width = int(width)
        height = int(height)
        top_pad = (total_height - height) // 2
        bottom_pad = total_height - height - top_pad
        left_pad = (total_width - width) // 2
        right_pad = total_width - width - left_pad
        padding_attr = urwid.AttrSpec(self.background, self.background)

        try:
            jp2a = subprocess.Popen(['jp2a', '--colors', '--fill',
                                     '--width=%s' % width,
                                     '--height=%s' % height,
                                     '--html-raw', '-'],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        except OSError, e:
            if self._prime:
                if e.errno == 2:
                    print("ERROR: jp2a is used but is not installed.")
                else:
                    print("ERROR: unable to run jp2a: %s" % e)
                raw_input("Press ENTER to continue.")
            data = self._blank(width, height)
        else:
            image = self._loadImage()
            image = image.convert('RGBA')
            image.save(jp2a.stdin, 'JPEG')
            jp2a.stdin.close()
            data = jp2a.stdout.read()
            jp2a.stderr.read()
            jp2a.wait()

        line_list = []
        attr_list = []
        line_text = ''
        line_attrs = []
        current_attr = [None, 0]
        current_fg = None
        current_bg = None
        current_props = None

        # Top pad
        for padding in range(0, top_pad):
            line_list.append(' ' * total_width)
            attr_list.append([(padding_attr, 1)] * total_width)

        for line in data.split('<br/>'):
            if not line:
                continue

            # Left pad
            line_text += ' ' * left_pad
            for fake_attr in range(0, left_pad):
                line_attrs.append((padding_attr, 1))

            for span in line.split('</span>'):

                if not span:
                    continue
                m = spanre.match(span)
                fg, bg, char = m.groups()
                if '&' in char:
                    char = htmlparser.unescape(char)
                char = char.encode('utf8')
                line_text += char
                props = []
                # TODO: if bold is set, append bold to props
                fg = ('#'+
                      nearest_color(int(fg[0:2], 16)) +
                      nearest_color(int(fg[2:4], 16)) +
                      nearest_color(int(fg[4:6], 16)))
                bg = ('#'+
                      nearest_color(int(bg[0:2], 16)) +
                      nearest_color(int(bg[2:4], 16)) +
                      nearest_color(int(bg[4:6], 16)))
                if current_fg == fg and current_bg == bg and current_props == props:
                    current_attr[1] += len(char)
                else:
                    if current_attr[0]:
                        line_attrs.append(tuple(current_attr))
                    fg = ', '.join(props + [fg])
                    attr = urwid.AttrSpec(fg, bg)
                    current_attr = [attr, len(char)]
                    current_fg = fg
                    current_bg = bg
                    current_props = props
            line_attrs.append(tuple(current_attr))
            current_attr = [None, 0]
            current_fg = None
            current_bg = None

            # Right pad
            line_text += ' ' * right_pad
            for fake_attr in range(0, right_pad):
                line_attrs.append((padding_attr, 1))

            line_list.append(line_text)
            line_text = ''
            attr_list.append(line_attrs)
            line_attrs = []

        # Bottom pad
        for padding in range(0, bottom_pad):
            line_list.append(' ' * total_width)
            attr_list.append([(padding_attr, 1)] * total_width)

        canvas = urwid.TextCanvas(line_list, attr_list)
        return canvas

def main():
    import PIL.Image
    img = PIL.Image.open('/tmp/p/8.jpg')
    img.load()
    hinter = slide.ScreenHinter()
    hinter.set_cols_rows((80, 25))
    w = ANSIImage(img, hinter)
    slpile = slide.SlidePile([])
    slpile.contents.append((w, slpile.options()))
    pad = slide.SlidePadding(slpile, align='center', width='pack')
    fill = slide.SlideFiller(pad)
    #w.render((80,25))
    fill.render((80,25))
    screen = urwid.raw_display.Screen()
    if True:
        with screen.start():
            screen.draw_screen((80,25), fill.render((80,25)))
            raw_input()
