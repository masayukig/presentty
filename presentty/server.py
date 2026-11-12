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
import socketserver

class ConsoleHandler(socketserver.StreamRequestHandler):
    def handle(self):
        server = self.server.server
        while True:
            try:
                data = self.rfile.readline()
            except Exception:
                break
            if not data:
                break
            data = data.decode('utf8').strip()
            if data == 'list':
                for i, slide in enumerate(server.list()):
                    self._write('slide %i %s\n' % (i, slide.title))
                self._write('end\n')
            elif data == 'current':
                i, slide = server.current()
                self._write('current %i %i %s\n' % (
                    i, slide.progressive_state, slide.title))
            elif data == 'next':
                i, slide = server.next()
                self._write('current %i %i %s\n' % (
                    i, slide.progressive_state, slide.title))
            elif data == 'prev':
                i, slide = server.prev()
                self._write('current %i %i %s\n' % (
                    i, slide.progressive_state, slide.title))
            elif data.startswith('jump'):
                parts = data.split()
                i, slide = server.jump(int(parts[1].strip()))
                self._write('current %i %i %s\n' % (
                    i, slide.progressive_state, slide.title))
            elif data == 'size':
                size = server.size()
                self._write('size %s %s\n' % size)

    def _write(self, data):
        self.wfile.write(data.encode('utf8'))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address=True
    daemon_threads=True

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
            os.write(self.presenter.server_pipe_in, b'next')
            self.presenter.server_pipe_out_read.readline()
            return self.current()
        finally:
            self.lock.release()

    def prev(self):
        self.lock.acquire()
        try:
            os.write(self.presenter.server_pipe_in, b'prev')
            self.presenter.server_pipe_out_read.readline()
            return self.current()
        finally:
            self.lock.release()

    def jump(self, pos):
        self.lock.acquire()
        try:
            os.write(self.presenter.server_pipe_in, ('jump %s' % (pos,)).encode('utf8'))
            self.presenter.server_pipe_out_read.readline()
            return self.current()
        finally:
            self.lock.release()
