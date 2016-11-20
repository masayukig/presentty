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

import urwid

class FigletText(urwid.WidgetWrap):
    def __init__(self, text, attr=None):
        self.text = text
        self.attr = attr
        output = self._run()
        if attr:
            widget = urwid.Text((attr, output), wrap='clip')
        else:
            widget = urwid.Text(output, wrap='clip')
        super(FigletText, self).__init__(widget)

    def _run(self):
        try:
            p = subprocess.Popen(['figlet'],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except OSError, e:
            if e.errno == 2:
                print("ERROR: figlet is used but is not installed.")
            else:
                print("ERROR: unable to run figlet: %s" % e)
            raw_input("Press ENTER to continue.")
            data = "[Unable to run figlet]"
        else:
            p.stdin.write(self.text)
            p.stdin.close()
            data = p.stdout.read()
            p.stderr.read()
            p.wait()
        return data

class CowsayText(urwid.WidgetWrap):
    def __init__(self, text, attr=None):
        self.text = text
        self.attr = attr
        output = self._run()
        if attr:
            widget = urwid.Text((attr, output), wrap='clip')
        else:
            widget = urwid.Text(output, wrap='clip')
        super(CowsayText, self).__init__(widget)

    def _run(self):
        try:
            p = subprocess.Popen(['cowsay'],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except OSError, e:
            if e.errno == 2:
                print("ERROR: cowsay is used but is not installed.")
            else:
                print("ERROR: unable to run cowsay: %s" % e)
            raw_input("Press ENTER to continue.")
            data = "[Unable to run cowsay]"
        else:
            p.stdin.write(self.text)
            p.stdin.close()
            data = p.stdout.read()
            p.stderr.read()
            p.wait()
        return data

def main():
    import slide
    w = FigletText("Testing")
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
if __name__=='__main__':
    main()
