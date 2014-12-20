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

import os
import threading
import SocketServer

class ConsoleHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        server = self.server.server
        while True:
            try:
                data = self.rfile.readline()
            except Exception:
                break
            if not data:
                break
            data = data.strip()
            if data == 'list':
                for i, slide in enumerate(server.list()):
                    self.wfile.write('slide %i %s\n' % (i, slide.title))
                self.wfile.write('end\n')
            elif data == 'current':
                i, slide = server.current()
                self.wfile.write('current %i %i %s\n' % (
                    i, slide.progressive_state, slide.title))
            elif data == 'next':
                i, slide = server.next()
                self.wfile.write('current %i %i %s\n' % (
                    i, slide.progressive_state, slide.title))
            elif data == 'prev':
                i, slide = server.prev()
                self.wfile.write('current %i %i %s\n' % (
                    i, slide.progressive_state, slide.title))
            elif data.startswith('jump'):
                parts = data.split()
                i, slide = server.jump(int(parts[1].strip()))
                self.wfile.write('current %i %i %s\n' % (
                    i, slide.progressive_state, slide.title))
            elif data == 'size':
                size = server.size()
                self.wfile.write('size %s %s\n' % size)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address=True

class ConsoleServer(object):
    def __init__(self, presenter, host='localhost', port=1292):
        self.presenter = presenter
        self.server = ThreadedTCPServer((host, port), ConsoleHandler)
        self.server.server = self
        self.lock = threading.Lock()

    def start(self):
        self.thread=threading.Thread(target=self._run, name="Console Server")
        self.thread.daemon=True
        self.thread.start()

    def _run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

    def list(self):
        return self.presenter.program

    def current(self):
        s = self.presenter.program[self.presenter.pos]
        return (self.presenter.pos, s)

    def size(self):
        return self.presenter.loop.screen.get_cols_rows()

    def next(self):
        self.lock.acquire()
        try:
            os.write(self.presenter.server_pipe_in, 'next')
            self.presenter.server_pipe_out_read.readline()
            return self.current()
        finally:
            self.lock.release()

    def prev(self):
        self.lock.acquire()
        try:
            os.write(self.presenter.server_pipe_in, 'prev')
            self.presenter.server_pipe_out_read.readline()
            return self.current()
        finally:
            self.lock.release()

    def jump(self, pos):
        self.lock.acquire()
        try:
            os.write(self.presenter.server_pipe_in, 'jump %s' % (pos,))
            self.presenter.server_pipe_out_read.readline()
            return self.current()
        finally:
            self.lock.release()
