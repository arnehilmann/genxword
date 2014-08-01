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
    genxword --output=OUTPUT_PREFIX WORDFILE... [options]

Options:
    --number-words=INT      number of words to use [default: 50]
    --font-family=STRING    font family [default: DejaVuSerif]
    --text-fontsize=INT     normal font size [default: 10]
    --number-fontsize=INT   size of hint numbers [default: 6]
    --title-fontsize=INT    size of title [default: 16]
    --square-size=INT       size of one square [default: 15]
    --auto
    --mix-mode
"""

import os

from docopt import docopt

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A5, landscape
#from reportlab.lib.pagesizes import A4, portrait

from control import Genxword


class PdfRenderer(object):
    def __init__(self, output, *args, **kwargs):
        print kwargs
        self.name = output
        self.title = os.path.basename(self.name)
        #self.width, self.height = self.size = portrait(A4)
        self.width, self.height = self.size = landscape(A5)
        self.square = int(kwargs["square-size"])
        self.c = c = Canvas(self.name + ".pdf", pagesize=self.size)
        self.font_family = kwargs["font-family"]
        self.fontsize_title = int(kwargs["title-fontsize"])
        self.fontsize_hint_nr = int(kwargs["number-fontsize"])
        self.fontsize = int(kwargs["text-fontsize"])
        c.setFont(self.font_family, self.fontsize)

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
            c.drawString(2, (self.square - self.fontsize_hint_nr) / 2, str(nr))
        if dir == 1:
            c.drawCentredString(self.square / 2, self.square - self.fontsize_hint_nr, str(nr))

    def is_empty(self, grid, row_nr=None, col_nr=None):
        if row_nr is not None:
            for cell in grid["best_grid"][row_nr]:
                if cell not in grid["empty"]:
                    return False
        if col_nr is not None:
            for row in grid["best_grid"]:
                if row[col_nr] not in grid["empty"]:
                    return False
        return True



    def render(self, grid):
        c = self.c

        margin = lambda:_
        margin.top = self.height / 10
        margin.left = margin.right = self.width / 10

        c.setFont(self.font_family, self.fontsize_title)
        c.drawCentredString(self.width / 2, self.height - margin.top - self.fontsize, self.title)
        c.translate(0, -margin.top - self.fontsize)

        from pdfrw import PdfReader
        from pdfrw.buildxobj import pagexobj
        from pdfrw.toreportlab import makerl

        pages = PdfReader("examples/liftarn_Black_horse.pdf").pages
        pages = [pagexobj(x) for x in pages]

        c.saveState()
        c.translate(self.width - 2 * margin.right, self.height - 4 * margin.top)
        c.scale(0.2, 0.2)
        c.doForm(makerl(c, pages[0]))
        c.restoreState()

        c.translate(margin.left, self.height - margin.top)
        c.setFont(self.font_family, self.fontsize_hint_nr)
        c.saveState()

        hints = []
        real_row = 0
        for row, line in enumerate(grid["best_grid"]):
            if self.is_empty(grid, row_nr=row):
                continue
            c.restoreState()
            c.saveState()
            c.translate(-self.square, -real_row * self.square)
            for col, cell in enumerate(line):
                if self.is_empty(grid, col_nr=col):
                    continue
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
            real_row += 1
        c.restoreState()

        c.translate(0, -real_row * self.square - margin.top)

        from reportlab.graphics.widgets import signsandsymbols
        from reportlab.graphics.shapes import Drawing
        from reportlab.lib import colors
        arrow = signsandsymbols.ArrowOne()
        arrow.fillColor = colors.black
        arrow.size = 40
        arrow = arrow.draw()
        drawing = Drawing(0, 0)
        drawing.scale(0.8, 0.4)
        drawing.add(arrow)
        drawing.drawOn(c, 0, -10)

        c.setFont(self.font_family, self.fontsize)
        text = c.beginText(40, 0)
        for nr, hint in enumerate(hints):
            if hint[1] == 0:
                text.textLine("%2d  %s" % (nr + 1, hint[0]))
        c.drawText(text)

        c.translate(0, text._y - 10)
        c.saveState()
        c.rotate(-90)
        drawing.drawOn(c, -5, 10)
        c.restoreState()
        text = c.beginText(40, 0)
        for nr, hint in enumerate(hints):
            if hint[1] == 1:
                text.textLine("%2d  %s" % (nr + 1, hint[0]))
        c.drawText(text)

        c.showPage()
        c.save()
        print vars(c)


def init_ttf_fonts():
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    folder = os.path.dirname(reportlab.__file__) + os.sep + 'fonts'
    ttfFile = os.path.join(folder, 'Vera.ttf')

    folder = "/usr/share/fonts/truetype/dejavu/"
    dejavu_ttf = os.path.join(folder, "DejaVuSerif.ttf")

    pdfmetrics.registerFont(TTFont("Vera", ttfFile))
    pdfmetrics.registerFont(TTFont("DejaVuSerif", dejavu_ttf))


def de_dashdash_args(args):
    result = {}
    for key, value in args.iteritems():
        if key.startswith("--"):
            result[key[2:]] = value
        else:
            result[key] = value
    return result


def main():
    arguments = docopt(__doc__)

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

    init_ttf_fonts()

    arguments = de_dashdash_args(arguments)

    renderer = PdfRenderer(**arguments)
    renderer.render(grid)
