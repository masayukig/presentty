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

import socket

class Client(object):
    def __init__(self, host='127.0.0.1', port=1292):
        self.host = host
        self.port = port
        self.sock = None
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.file = self.sock.makefile('rw', 0)

    def list(self):
        self.file.write('list\n')
        program = []
        while True:
            ln = self.file.readline().strip()
            if ln == 'end':
                break
            x, index, title = ln.split(' ', 2)
            program.append(title)
        return program

    def size(self):
        self.file.write('size\n')
        ln = self.file.readline().strip()
        x, cols, rows = ln.split(' ', 2)
        return (int(cols), int(rows))

    def parseCurrent(self):
        ln = self.file.readline().strip()
        x, index, progressive_state, title = ln.split(' ', 3)
        return (int(index), int(progressive_state))

    def current(self):
        self.file.write('current\n')
        return self.parseCurrent()

    def jump(self, index):
        self.file.write('jump %i\n' % index)
        return self.parseCurrent()

    def next(self):
        self.file.write('next\n')
        return self.parseCurrent()

    def prev(self):
        self.file.write('prev\n')
        return self.parseCurrent()
