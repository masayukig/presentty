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

DARK_PALETTE = {
    '_default': urwid.AttrSpec('light gray', 'black'),

    'emphasis': urwid.AttrSpec('bold, light gray', 'black'),
    'title': urwid.AttrSpec('bold, white', 'black'),

    'progressive': urwid.AttrSpec('dark gray', 'black'),

    # Based on pygments default colors

    'whitespace': urwid.AttrSpec('light gray', '#aaa'),
    'comment': urwid.AttrSpec('#688', 'black'),
    'comment-preproc': urwid.AttrSpec('#a80', 'black'),
    'keyword': urwid.AttrSpec('bold, #0f0', 'black'),
    'keyword-pseudo': urwid.AttrSpec('#080', 'black'),
    'keyword-type': urwid.AttrSpec('#a06', 'black'),
    'operator': urwid.AttrSpec('#666', 'black'),
    'operator-word': urwid.AttrSpec('bold, #a0f', 'black'),
    'name-builtin': urwid.AttrSpec('#0d0', 'black'),
    'name-function': urwid.AttrSpec('#00f', 'black'),
    'name-class': urwid.AttrSpec('bold, #00f', 'black'),
    'name-namespace': urwid.AttrSpec('bold, #00f', 'black'),
    'name-exception': urwid.AttrSpec('bold, #d66', 'black'),
    'name-variable': urwid.AttrSpec('#008', 'black'),
    'name-constant': urwid.AttrSpec('#800', 'black'),
    'name-label': urwid.AttrSpec('#aa0', 'black'),
    'name-entity': urwid.AttrSpec('bold, #888', 'black'),
    'name-attribute': urwid.AttrSpec('#880', 'black'),
    'name-tag': urwid.AttrSpec('bold, #080', 'black'),
    'name-decorator': urwid.AttrSpec('#a0f', 'black'),
    'string': urwid.AttrSpec('#a00', 'black'),
    'string-doc': urwid.AttrSpec('light gray', 'black'),
    'string-interpol': urwid.AttrSpec('bold, #a68', 'black'),
    'string-escape': urwid.AttrSpec('bold, #a60', 'black'),
    'string-regex': urwid.AttrSpec('#a68', 'black'),
    'string-symbol': urwid.AttrSpec('#008', 'black'),
    'string-other': urwid.AttrSpec('#080', 'black'),
    'number': urwid.AttrSpec('#666', 'black'),
    'generic-heading': urwid.AttrSpec('bold, #008', 'black'),
    'generic-subheading': urwid.AttrSpec('bold, #808', 'black'),
    'generic-deleted': urwid.AttrSpec('#a00', 'black'),
    'generic-inserted': urwid.AttrSpec('#0a0', 'black'),
    'generic-error': urwid.AttrSpec('#f00', 'black'),
    'generic-emph': urwid.AttrSpec('bold, #fff', 'black'),
    'generic-strong': urwid.AttrSpec('bold, #ddd', 'black'),
    'generic-prompt': urwid.AttrSpec('bold, #008', 'black'),
    'generic-output': urwid.AttrSpec('#888', 'black'),
    'generic-traceback': urwid.AttrSpec('#06d', 'black'),
    'error': urwid.AttrSpec('underline, #f00', 'black'),
}

LIGHT_PALETTE = {}
for k, v in DARK_PALETTE.items():
    LIGHT_PALETTE[k] = urwid.AttrSpec(v.foreground, 'h15')

LIGHT_PALETTE.update({
    '_default': urwid.AttrSpec('black', 'h15'),
    'emphasis': urwid.AttrSpec('bold, black', 'h15'),
    'title': urwid.AttrSpec('bold, #000', 'h15'),
    'progressive': urwid.AttrSpec('light gray', 'h15'),
})
