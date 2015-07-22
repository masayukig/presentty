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
import os
import sys
import time

import urwid

import slide
import server
import rst
import palette


class Presenter(object):
    def __init__(self, palette):
        blank = urwid.Text(u'')
        self.blank = slide.UrwidSlide('Blank', None, blank,
                                      palette['_default'])
        self.current = self.blank
        self.program = []
        self.palette = palette
        self.pos = -1
        self.loop = urwid.MainLoop(self.blank,
                                   unhandled_input=self.unhandledInput)
        self.loop.screen.set_terminal_properties(colors=256)

        self.server_pipe_in = self.loop.watch_pipe(self.serverData)
        r,w = os.pipe()
        self.server_pipe_out_read = os.fdopen(r)
        self.server_pipe_out_write = w
        self.server = server.ConsoleServer(self)
        self.server.start()

    def serverData(self, data):
        parts = data.split()
        if parts[0] == 'jump':
            try:
                index = int(parts[1])
            except Exception:
                os.write(self.server_pipe_out_write, 'err\n')
                return
            if index < 0 or index > len(self.program)-1:
                os.write(self.server_pipe_out_write, 'err\n')
                return
            self.transitionTo(index)
            os.write(self.server_pipe_out_write, 'ok\n')
        elif parts[0] == 'next':
            self.nextSlide()
            os.write(self.server_pipe_out_write, 'ok\n')
        elif parts[0] == 'prev':
            self.prevSlide()
            os.write(self.server_pipe_out_write, 'ok\n')

    def setProgram(self, program):
        self.program = program

    def run(self):
        self.loop.set_alarm_in(0, self.nextSlide)
        self.loop.run()

    def unhandledInput(self, key):
        if key in ('right', 'page down'):
            self.nextSlide()
        elif key in ('left', 'page up'):
            self.prevSlide()
        elif key == 'q':
            raise urwid.ExitMainLoop()

    def transitionTo(self, index, forward=True):
        self.pos = index
        current_slide = self.current
        new_slide = self.program[index]
        if forward:
            transition = new_slide.transition
            new_slide.resetProgressive()
        else:
            transition = current_slide.transition
            new_slide.resetProgressive(True)
        current_slide.stopAnimation()
        if forward:
            transition.setTargets(current_slide, new_slide)
        else:
            transition.setTargets(new_slide, current_slide)
        self.loop.widget = transition
        duration = transition.getDuration()
        start = time.time()
        now = start
        end = start + duration
        while duration:
            if forward:
                progress = min(1-((end-now)/duration), 1.0)
            else:
                progress = max(((end-now)/duration), 0.0)
            transition.setProgress(progress)
            self.loop.draw_screen()
            now = time.time()
            if now >= end:
                break
        end = time.time()
        self.loop.widget = new_slide
        self.current = new_slide
        self.loop.draw_screen()
        current_slide.resetAnimation()
        new_slide.startAnimation(self.loop)

    def nextSlide(self, loop=None, data=None):
        if self.current.nextProgressive():
            return
        if self.pos+1 == len(self.program):
            return
        self.transitionTo(self.pos+1)

    def prevSlide(self, loop=None, data=None):
        if self.current.prevProgressive():
            return
        if self.pos == 0:
            return
        self.transitionTo(self.pos-1, forward=False)

def main():
    parser = argparse.ArgumentParser(
        description='Console-based presentation system')
    parser.add_argument('--light', dest='light',
                        default=False,
                        action='store_true',
                        help='use a black on white palette')
    parser.add_argument('--warnings', dest='warnings',
                        default=False,
                        action='store_true',
                        help='print RST parser warnings and exit if any')
    parser.add_argument('file',
                        help='presentation file (RST)')
    args = parser.parse_args()
    if args.light:
        plt = palette.LIGHT_PALETTE
    else:
        plt = palette.DARK_PALETTE
    hinter = slide.ScreenHinter()
    parser = rst.PresentationParser(plt, hinter)
    program = parser.parse(open(args.file).read(), args.file)
    if args.warnings:
        w = parser.warnings.getvalue()
        if w:
            print w
            sys.exit(1)
    p = Presenter(plt)
    p.setProgram(program)
    hinter.setScreen(p.loop.screen)
    p.run()
