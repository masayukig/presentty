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
import re
import docutils
import docutils.frontend
import docutils.parsers.rst
import docutils.nodes
import cStringIO as StringIO

import urwid

import slide
import transition as transition_mod
import image
import ansiparser
import text

try:
    import PIL
    import PIL.Image
except ImportError:
    PIL = None

DEFAULT_TRANSITION = 'dissolve'
DEFAULT_TRANSITION_DURATION = 0.4

class TextAccumulator(object):
    def __init__(self):
        self.text = []

    def append(self, text):
        self.text.append(text)

    def getFormattedText(self):
        return self.text

    wsre = re.compile('\s+')

    def getFlowedText(self):
        ret = []
        for part in self.text:
            if isinstance(part, tuple):
                ret.append((part[0], self.wsre.sub(u' ', part[1])))
            else:
                ret.append(self.wsre.sub(u' ', part))
        if not ret:
            return u''
        return ret

class UrwidTranslator(docutils.nodes.GenericNodeVisitor):
    transition_map = {'dissolve': transition_mod.DissolveTransition,
                      'cut': transition_mod.CutTransition,
                      'pan': transition_mod.PanTransition,
                      'tilt': transition_mod.TiltTransition,
                      }

    def __init__(self, document, palette, hinter=None, basedir='.'):
        docutils.nodes.GenericNodeVisitor.__init__(self, document)
        self.program = []
        self.stack = []
        self.default_transition = self._make_transition(
            DEFAULT_TRANSITION,
            DEFAULT_TRANSITION_DURATION)
        self.transition = self.default_transition
        self.attr = []
        self.table_columns = []
        self.table_column = []
        self.progressives = []
        self.palette = palette
        self.hinter = hinter
        self.basedir = basedir
        self.slide = None
        self.default_hide_title = False
        self.hide_title = self.default_hide_title

    def _make_transition(self, name, duration):
        tr = self.transition_map[name]
        return tr(duration)

    def default_visit(self, node):
        """Override for generic, uniform traversals."""
        pass

    def default_departure(self, node):
        """Override for generic, uniform traversals."""
        pass

    def _append(self, node, widget, *args, **kw):
        if self.stack:
            if 'handout' in node.get('classes'):
                if self.handout_pile not in self.stack:
                    container = self.handout_pile
                else:
                    # If the handout pile is in the stack, then ignore
                    # this class -- it has probably needlessly been
                    # applied to something deeper in the stack.  The
                    # thing further up will end up in the handout.
                    container = self.stack[-1]
            else:
                container = self.stack[-1]
            container.contents.append((widget, container.options(*args, **kw)))

    def styled(self, style, text):
        if style in self.palette:
            return (self.palette[style], text)
        return text

    def visit_transition(self, node):
        name = node['name']
        duration = node.get('duration', DEFAULT_TRANSITION_DURATION)
        self.transition = self._make_transition(name, duration)

    def depart_transition(self, node):
        pass

    def visit_hidetitle(self, node):
        if self.slide:
            self.hide_title = True
        else:
            self.default_hide_title = True

    def depart_hidetitle(self, node):
        pass

    def visit_system_message(self, node):
        #print node.astext()
        raise docutils.nodes.SkipNode()

    def visit_section(self, node):
        self.hide_title = self.default_hide_title
        self.transition = self.default_transition
        title_pile = slide.SlidePile([])
        title_pad = slide.SlidePadding(title_pile,
                                       align='center', width='pack')

        main_pile = slide.SlidePile([])
        main_pad = slide.SlidePadding(main_pile, align='center', width='pack')
        outer_pile = slide.SlidePile([
            ('pack', title_pad),
            ('pack', main_pad),
        ])
        s = slide.UrwidSlide(u'', self.transition, outer_pile,
                             self.palette['_default'])
        self.slide = s
        self.stack.append(main_pile)
        self.title_pile = title_pile

        pile = slide.SlidePile([])
        s = slide.Handout(pile, self.palette['_default'])
        self.handout = s
        self.handout_pile = pile
        self.slide.handout = s

    def depart_section(self, node):
        self.slide.transition = self.transition
        if self.hide_title:
            self.title_pile.contents[:] = []
        self.program.append(self.slide)
        self.stack.pop()

    def visit_block_quote(self, node):
        self.stack.append(slide.SlidePile([]))

    def depart_block_quote(self, node):
        pile = self.stack.pop()
        pad = slide.SlidePadding(pile, left=2)
        self._append(node, pad, 'pack')

    def visit_list_item(self, node):
        self.stack.append(slide.SlidePile([]))

    def depart_list_item(self, node):
        pile = self.stack.pop()
        bullet = urwid.Text(u'* ')
        cols = slide.SlideColumns([])
        cols.contents.append((bullet, cols.options('pack')))
        cols.contents.append((pile, cols.options('weight', 1)))
        if self.progressives:
            cols = urwid.AttrMap(cols, self.palette['progressive'])
            self.progressives[-1].append(cols)
        self._append(node, cols, 'pack')

    def visit_tgroup(self, node):
        self.table_columns.append([])
        self.stack.append(slide.SlidePile([]))

    def visit_colspec(self, node):
        self.table_columns[-1].append(node['colwidth'])

    def visit_row(self, node):
        self.stack.append(slide.SlideColumns([], dividechars=1))
        self.table_column.append(0)

    def depart_row(self, node):
        self.table_column.pop()
        cols = self.stack.pop()
        self._append(node, cols, 'pack')

    def visit_thead(self, node):
        pass

    def depart_thead(self, node):
        cols = slide.SlideColumns([], dividechars=1)
        for width in self.table_columns[-1]:
            cols.contents.append((urwid.Text(u'='*width),
                                  cols.options('given', width)))
        self._append(node, cols, 'pack')

    def visit_entry(self, node):
        self.stack.append(slide.SlidePile([]))

    def depart_entry(self, node):
        colindex = self.table_column[-1]
        self.table_column[-1] = colindex + 1
        pile = self.stack.pop()
        self._append(node, pile, 'given', self.table_columns[-1][colindex])

    def depart_tgroup(self, node):
        self.table_columns.pop()
        pile = self.stack.pop()
        self._append(node, pile, 'pack')

    def visit_textelement(self, node):
        self.stack.append(TextAccumulator())

    visit_paragraph = visit_textelement

    def depart_paragraph(self, node):
        text = self.stack.pop()
        self._append(node, urwid.Text(text.getFlowedText()), 'pack')

    visit_literal_block = visit_textelement

    def depart_literal_block(self, node):
        text = self.stack.pop()
        text = urwid.Text(text.getFormattedText(), wrap='clip')
        pad = slide.SlidePadding(text, width='pack')
        self._append(node, pad, 'pack')

    visit_line = visit_textelement

    def depart_line(self, node):
        text = self.stack.pop()
        self._append(node, urwid.Text(text.getFormattedText(), wrap='clip'),
                     'pack')

    visit_title = visit_textelement

    def depart_title(self, node):
        text = self.stack.pop()
        self.slide.title = node.astext()
        widget = urwid.Text(self.styled('title', text.getFlowedText()),
                            align='center')
        self.title_pile.contents.append(
            (widget, self.title_pile.options('pack')))

    def visit_Text(self, node):
        pass

    def depart_Text(self, node):
        if self.stack and isinstance(self.stack[-1], TextAccumulator):
            if self.attr:
                t = (self.attr[-1], node.astext())
            else:
                t =  node.astext()
            self.stack[-1].append(t)

    def visit_emphasis(self, node):
        self.attr.append(self.palette['emphasis'])

    def depart_emphasis(self, node):
        self.attr.pop()

    def visit_inline(self, node):
        cls = node.get('classes')
        if not cls:
            raise docutils.nodes.SkipDeparture()
        cls = [x for x in cls if x != 'literal']
        for length in range(len(cls), 0, -1):
            clsname = '-'.join(cls[:length])
            if clsname in self.palette:
                self.attr.append(self.palette[clsname])
                return
        raise docutils.nodes.SkipDeparture()

    def depart_inline(self, node):
        self.attr.pop()

    def visit_image(self, node):
        if not PIL:
            return
        uri = node['uri']
        fn = os.path.join(self.basedir, uri)
        w = image.ANSIImage(fn, self.hinter)
        self._append(node, w, 'pack')

    def visit_ansi(self, node):
        interval = node.get('interval', 0.5)
        oneshot = node.get('oneshot', False)
        animation = slide.AnimatedText(interval, oneshot)
        for name in node['names']:
            p = ansiparser.ANSIParser()
            fn = os.path.join(self.basedir, name)
            data = unicode(open(fn).read(), 'utf8')
            text = p.parse(data)
            animation.addFrame(text)
        self.slide.animations.append(animation)
        self._append(node, animation, 'pack')

    def depart_ansi(self, node):
        pass

    def visit_figlet(self, node):
        figlet = text.FigletText(node['text'])
        self._append(node, figlet, 'pack')

    def depart_figlet(self, node):
        pass

    def visit_cowsay(self, node):
        cowsay = text.CowsayText(node['text'])
        self._append(node, cowsay, 'pack')

    def depart_cowsay(self, node):
        pass

    def visit_container(self, node):
        self.stack.append(slide.SlidePile([]))
        if 'progressive' in node.get('classes'):
            self.progressives.append(self.slide.progressives)
            self.slide.progressive_attr = self.palette['progressive']

    def depart_container(self, node):
        pile = self.stack.pop()
        self._append(node, pile, 'pack')
        if 'progressive' in node.get('classes'):
            self.progressives.pop()

class TransitionDirective(docutils.parsers.rst.Directive):
    required_arguments = 1
    option_spec = {'duration': float}
    has_content = False

    def run(self):
        args = {'name': self.arguments[0]}
        duration = self.options.get('duration')
        if duration:
            args['duration'] = duration
        node = transition(**args)
        return [node]

class ANSIDirective(docutils.parsers.rst.Directive):
    required_arguments = 1
    final_argument_whitespace = True
    option_spec = {'interval': float,
                   'oneshot': bool}
    has_content = False

    def run(self):
        args = {'names': self.arguments[0].split()}
        args.update(self.options)
        node = ansi(**args)
        return [node]

class FigletDirective(docutils.parsers.rst.Directive):
    required_arguments = 1
    has_content = False
    final_argument_whitespace = True

    def run(self):
        args = {'text': self.arguments[0]}
        node = figlet(**args)
        return [node]

class CowsayDirective(docutils.parsers.rst.Directive):
    required_arguments = 1
    has_content = False
    final_argument_whitespace = True

    def run(self):
        args = {'text': self.arguments[0]}
        node = cowsay(**args)
        return [node]

class HideTitleDirective(docutils.parsers.rst.Directive):
    has_content = False

    def run(self):
        node = hidetitle()
        return [node]

class transition(docutils.nodes.Special, docutils.nodes.Invisible,
                 docutils.nodes.Element):
    pass

class ansi(docutils.nodes.General, docutils.nodes.Inline,
           docutils.nodes.Element):
    pass

class figlet(docutils.nodes.General, docutils.nodes.Inline,
             docutils.nodes.Element):
    pass

class cowsay(docutils.nodes.General, docutils.nodes.Inline,
             docutils.nodes.Element):
    pass

class hidetitle(docutils.nodes.Special, docutils.nodes.Invisible,
                docutils.nodes.Element):
    pass

class PresentationParser(object):
    def __init__(self, palette, hinter=None):
        docutils.parsers.rst.directives.register_directive(
            'transition', TransitionDirective)
        docutils.parsers.rst.directives.register_directive(
            'ansi', ANSIDirective)
        docutils.parsers.rst.directives.register_directive(
            'figlet', FigletDirective)
        docutils.parsers.rst.directives.register_directive(
            'cowsay', CowsayDirective)
        docutils.parsers.rst.directives.register_directive(
            'hidetitle', HideTitleDirective)
        self.warnings = StringIO.StringIO()
        self.settings = docutils.frontend.OptionParser(
            components=(docutils.parsers.rst.Parser,),
            defaults=dict(warning_stream=self.warnings)).get_default_values()
        self.parser = docutils.parsers.rst.Parser()
        self.palette = palette
        self.hinter = hinter

    def _parse(self, input, filename):
        document = docutils.utils.new_document(filename, self.settings)
        self.parser.parse(input, document)
        visitor = UrwidTranslator(document, self.palette, self.hinter,
                                  os.path.dirname(filename))
        document.walkabout(visitor)
        return document, visitor

    def parse(self, input, filename='program'):
        document, visitor = self._parse(input, filename)
        return visitor.program

def main():
    import argparse
    import palette

    argp = argparse.ArgumentParser(description='Test RST parser')
    argp.add_argument('file', help='presentation file (RST)')
    argp.add_argument('slides', nargs='*', default=[],
                      help='slides to render')
    argp.add_argument('--render', action='store_true',
                      help='Fully render a slide')
    args = argp.parse_args()

    parser = PresentationParser(palette.DARK_PALETTE)
    document, visitor = parser._parse(open(args.file).read(), args.file)

    slides = args.slides
    if not slides:
        slides = range(len(visitor.program))
    slides = [int(x) for x in slides]

    if not args.render:
        print document.pformat()
        for i in slides:
            print '-'*80
            s = visitor.program[i]
            for line in s.render((80,25)).text:
                print line
    else:
        screen = urwid.raw_display.Screen()
        with screen.start():
            for i in slides:
                s = visitor.program[i]
                screen.draw_screen((80,25), s.render((80,25)))
                raw_input()

if __name__ == '__main__':
    main()
