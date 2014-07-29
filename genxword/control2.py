# Authors: David Whitlock <alovedalongthe@gmail.com>, Bryan Helmig, Arne Hilmann <arne@hilmann.de>
# Crossword generator that outputs the grid and clues as a pdf file and/or
# the grid in png/svg format with a text file containing the words and clues.
# Copyright (C) 2010-2011 Bryan Helmig
# Copyright (C) 2011-2014 David Whitlock
#
# Genxword is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Genxword is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with genxword.  If not, see <http://www.gnu.org/licenses/gpl.html>.
"""
Usage:
    genxword --output=OUTPUT_PREFIX [--auto] [--mix-mode] [--number-words=INT] WORDFILE...

Options:
    --number-words=INT  number of words to use [default: 50]
"""

from docopt import docopt

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, portrait

from control import Genxword


class PdfRenderer(object):
    def __init__(self, name):
        self.name = name
        self.width, self.height = self.size = portrait(A4)
        self.square = 25
        self.c = c = Canvas(name + ".pdf", pagesize=self.size)
        c.setTitle(name)
        self.fontsize = 8
        c.setFont("Helvetica", self.fontsize)

    def render_square(self, content, nr=None, dir=None):
        c = self.c
        p = c.beginPath()
        p.moveTo(0, 0)
        p.lineTo(self.square, 0)
        p.lineTo(self.square, self.square)
        p.lineTo(0, self.square)
        p.lineTo(0, 0)
        c.drawPath(p)
        #c.drawCentredString(self.square / 2, self.square / 2, content)

    def render_hint_nr(self, nr, dir):
        c = self.c
        if dir == 0:
            c.drawString(2, (self.square - self.fontsize) / 2, str(nr))
        if dir == 1:
            c.drawCentredString(self.square / 2, self.square - self.fontsize, str(nr))



    def render(self, grid):
        c = self.c

        c.translate(100, self.height - 100)
        c.saveState()
        hints = []
        for row, line in enumerate(grid["best_grid"]):
            c.restoreState()
            c.saveState()
            c.translate(0, - row * self.square)
            for col, cell in enumerate(line):
                c.translate(self.square, 0)
                if cell in grid["empty"]:
                    continue

                for word in grid["best_word_list"]:
                    if word[2] == row and word[3] == col:
                        nr = len(hints)
                        print "%d (%d/%d) %s" % (nr + 1, col, row, word[1])
                        hints.append((word[1].strip(), word[4]))
                        self.render_hint_nr(nr + 1, word[4])
                self.render_square(cell)
        c.restoreState()

        text = c.beginText(0, -row * self.square)
        text.textLine("quer")
        for nr, hint in enumerate(hints):
            if hint[1] == 0:
                text.textLine("%2d  %s" % (nr + 1, hint[0]))
        text.textLine("hoch")
        for nr, hint in enumerate(hints):
            if hint[1] == 1:
                text.textLine("%2d  %s" % (nr + 1, hint[0]))
        c.drawText(text)

        c.showPage()
        c.save()


def main():
    arguments = docopt(__doc__)
    print arguments

    #parser.add_argument('infile', type=argparse.FileType('r'), help=_('Name of word list file.'))
    #parser.add_argument('saveformat', help=_('Save files as A4 pdf (p), letter size pdf (l), png (n) and/or svg (s).'))
    #parser.add_argument('-a', '--auto', dest='auto', action='store_true', help=_('Automated (non-interactive) option.'))
    #parser.add_argument('-m', '--mix', dest='mixmode', action='store_true', help=_('Create anagrams for the clues'))
    #parser.add_argument('-n', '--number', dest='nwords', type=int, default=50, help=_('Number of words to be used.'))
    #parser.add_argument('-o', '--output', dest='output', default='Gumby', help=_('Name of crossword.'))

    wordlist = []
    for wordfilename in arguments["WORDFILE"]:
        with open(wordfilename) as wordfile:
            for line in wordfile:
                wordlist.append(line)

    gen = Genxword(auto=arguments["--auto"], mixmode=arguments["--mix-mode"])
    gen.wlist(wordlist, int(arguments["--number-words"]))
    gen.grid_size()
    grid = gen.gengrid()
    print grid

    renderer = PdfRenderer(arguments["--output"])
    renderer.render(grid)
