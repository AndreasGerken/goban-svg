#!/usr/bin/python2

import argparse
import svgwrite
import sys
import warnings

DefaultOptions = {
    # Draw a border (also used for default in arguments)
    'border': True,
    # Margin from the outer Lines to the board edge in mm
    'margin': 15,
    # Radius of the board corners when rounded corners is activated
    'rounded_corners': 10,
    # Spacing in width and height directions between lines
    'spacing_horizontal': 22,
    'spacing_vertical': 23.7,
    # linewidth in svg
    'linewidth': 0.15,
    # draw multiple lines which can be used for cleaner lasercuts
    'multiple_lines': 2,
    # spacing between the lines when multiple lines are drawn
    'multiple_lines_spacing': 0.25,
    # diameter of the star circles
    'star_diameter': 4,
    # Unit used everywhere
    'unit': 'mm',
    # Used colors
    'colors': {'cut_stroke': 'black',
               'mark_stroke': 'red',
               'background': 'white'},
    # Output file names
    'output': {'goban': 'goban.svg', 'test': 'test.svg'}
}

sizeOptions =\
    {'7': {'lines_horizontal': 7, 'lines_vertical': 7, 'star_points': ((2, 2), (4, 2), (2, 4), (4, 4))},
     '9': {'lines_horizontal': 9, 'lines_vertical': 9, 'star_points': ((2, 2), (6, 2), (4, 4), (2, 6), (6, 6))},
     '13': {'lines_horizontal': 13, 'lines_vertical': 13, 'star_points': ((3, 3), (9, 3), (6, 6), (3, 9), (9, 9))},
     '19': {'lines_horizontal': 19, 'lines_vertical': 19, 'star_points': ((3, 3), (9, 3), (15, 3), (3, 9), (9, 9), (15, 9), (3, 15), (9, 15), (15, 15))}}


class GoBoard(object):
    def __init__(self, opt):
        """Initializes the object and prepares all dimensions of the board according to the options.
        opt: Dictionary with {
            border: bool,
            margin: float,
            rounded_corners: float,
            spacing_horizontal: float,
            spacing_vertical: float,
            linewidth: float,
            multiple_lines: int,
            multiple_lines_spacing: float,
            star_diameter: float,
            unit: str,
            colors: dict{cut_stroke: str, mark_stroke: str, background:str},
            output: dict{goban:str, test:str}
        }
        """

        # Load the option dictionary to the object variables.
        # All options are directly useable from self, to reduce
        # self.opt['margin'] with self.margin
        self.__dict__.update(opt)

        # If the margin is smaller than the rounded corners we add more to not mess up
        if self.margin < self.rounded_corners:
            warnings.warn("The margin is smaller than the rounded corners radius, which might result in strange boards. Increase the margin with --margin.")

        # Board width with margin at both sides
        self.width = (self.lines_horizontal - 1) * self.spacing_horizontal + \
            self.linewidth + self.margin * 2

        # Specials for half boards
        if self.half_board:

            if self.lines_vertical % 2 == 0:
                raise Exception(
                    'The half board option only works with an odd number of vertical lines.')

            # reduce number of lines to half
            self.lines_vertical = (int)((self.lines_vertical + 1) / 2)

            # Board height only has a margin at the bottom when there is a half board
            self.height = (self.lines_vertical - 1) * \
                self.spacing_vertical + self.linewidth + self.margin
        else:
            # Board height with margin at the top and bottom
            self.height = (self.lines_vertical - 1) * \
                self.spacing_vertical + self.linewidth + self.margin * 2

        self.drawing = None

    def draw(self):
        """Draws the goban using current dimentions"""

        # Initialize drawing
        drawing = svgwrite.Drawing(size=(
            "%f%s" % (self.width, self.unit),
            "%f%s" % (self.height, self.unit)),
            viewBox=('0 0 %d %d' % (self.width, self.height)))
        self.drawing = drawing

        if self.border:
            # Create the edges of the board.
            # Since it is very easy to create full rectangles with rounded corner,
            # the half board is created as full rounded rectangle and then the top is cut of
            # later. This gives a little waste strip but makes the program simpler.

            borderwidth = self.width - self.linewidth

            # Position and height of the border
            if self.half_board:
                borderpos = (0, -self.rounded_corners)
                borderheight = self.height - self.linewidth + \
                    self.rounded_corners
            else:
                borderpos = (0, 0)
                borderheight = self.height - self.linewidth

            border = drawing.rect(borderpos,
                                  size=(borderwidth, borderheight),
                                  stroke=self.colors['cut_stroke'],
                                  stroke_width=self.linewidth,
                                  fill=self.colors['background'],
                                  rx=self.rounded_corners,
                                  ry=self.rounded_corners)
            drawing.add(border)

            # If the board is just half, cut of the top part with the rounded corners
            if self.half_board:
                top_cut = self.drawing.line(
                    (0, 0), (self.width, 0), stroke=self.colors['cut_stroke'],
                    stroke_width=self.linewidth)
                self.drawing.add(top_cut)

        # Find the top left point where to start the lines
        if self.half_board:
            start = (self.margin, 0)
        else:
            start = (self.margin, self.margin)

        # Draw all lines & stars
        self.draw_lines(start, 'vertical')
        self.draw_lines(start, 'horizontal')
        self.draw_starpoints(start)

    def draw_lines(self, start, direction):
        """Draws a bunch of lines, this function is used for vertical and horizontal lines

        start is a tuple of two values
        direction should be 'vertical' or 'horizontal'
        """

        # Sanity
        start = list(start)
        if len(start) != 2:
            raise ValueError("start must be a tuple of 2 values")

        # Find all spacings and indices according to the chosen direction
        if direction == 'vertical':
            line_count = self.lines_vertical
            spacing = self.spacing_vertical
            line_length = self.spacing_horizontal * (self.lines_horizontal - 1)
            dir_line = 0
            dir_count = 1
        elif direction == 'horizontal':
            line_count = self.lines_horizontal
            spacing = self.spacing_horizontal
            line_length = self.spacing_vertical * (self.lines_vertical - 1)
            dir_line = 1
            dir_count = 0
        else:
            raise Exception('Directions can only be horizontal or vertical')

        # Draw all lines
        for i in range(line_count):

            # Find the end of the line
            end = list(start)
            end[dir_line] += line_length

            # Draw multiple lines next to each other for lasercutting
            self.draw_multiple_lines(
                start, end, dir_count)

            # Move the start to the next line
            start[dir_count] += spacing

    def draw_multiple_lines(self, start, end, dir_count):
        """ Draw multiple lines next to each other for better lasercutting.
        The amount of lines and their spacing comes from the options.

        start is tuple(2) of the start coordinates
        end is tuple(2) of the end coordinates
        dir_count is the tupel index direction in which to spread the lines.
        """

        for l in range(self.multiple_lines):
            start_o = list(start)
            end_o = list(end)

            # Offset the lines from the center line
            offset = (l - self.multiple_lines / 2.) * \
                self.multiple_lines_spacing
            start_o[dir_count] += offset
            end_o[dir_count] += offset

            line = self.drawing.line(
                start=start_o, end=end_o, stroke=self.colors['mark_stroke'], stroke_width=self.linewidth)
            self.drawing.add(line)

    def draw_starpoint(self, pos):
        """ Draw one starpoint consisting of multiple lines next to each other.
        The amount of lines and their spacing comes from the options.

        pos is tuple(2) of the center coordinates
        """
        for l in range(self.multiple_lines):
            diameter = self.star_diameter + \
                (l - self.multiple_lines) * \
                self.multiple_lines_spacing
            star = self.drawing.circle(
                pos, r=diameter / 2, fill='none', stroke=self.colors['mark_stroke'], stroke_width=self.linewidth)
            self.drawing.add(star)

    def draw_starpoints(self, start):
        """Draws all star points

        start is tuple(2) of start coordinates
        """

        # Vertical position offset for the stars. If there is only a half board,
        # All stars are moved up by the half board which is the vertical line count of the board at this point.
        vert_pos_offset = self.lines_vertical - 1 if self.half_board else 0

        # Draw all stars
        for point in self.star_points:

            # Move the points with the vertical offset
            point = (point[0], point[1] - vert_pos_offset)

            # If it is still on the board after moving, draw it.
            if(point[1] >= 0):
                center = (start[0] + point[0] * self.spacing_horizontal - self.multiple_lines_spacing / 2,
                          start[1] + point[1] * self.spacing_vertical - self.multiple_lines_spacing / 2)
                self.draw_starpoint(center)

    def write(self, filename):
        """writes the svg rendering into a file"""
        if not self.drawing:
            self.draw()

        self.drawing.saveas(filename)

    def tostring(self):
        if self.drawing:
            return self.drawing.tostring()
        else:
            return ""

    def draw_test(self):
        """ This test function creates a test piece to see how the multiple line ammunt and spacing shoult be chosen.
        It can be activated with the --test argument. """

        # Tuples of linecount and spacing between them to test
        lines = [(2, 0.1), (2, 0.2), (2, 0.3), (2, 0.4), (2, 0.5),
                 (3, 0.1), (3, 0.2), (3, 0.3), (3, 0.4), (3, 0.5)]

        margin = 10
        line_length = 10
        spacing = 10
        width = line_length + 2 * margin
        height = len(lines) * spacing + margin * 2

        drawing = svgwrite.Drawing(size=(
            "%f%s" % (width, self.unit),
            "%f%s" % (height, self.unit)),
            viewBox=('0 0 %d %d' % (width, height)))

        self.drawing = drawing

        # create an initial rectangle around the drawing
        border = drawing.rect(size=(width, height),
                              stroke=self.colors['cut_stroke'],
                              stroke_width=self.linewidth,
                              fill=self.colors['background'],
                              rx=self.rounded_corners, ry=self.rounded_corners)
        drawing.add(border)

        start = (margin, margin)

        dir_line = 0
        dir_count = 1

        for i in range(len(lines)):
            end = list(start)
            end[dir_line] += line_length

            multiple_lines = lines[i][0]
            multiple_lines_spacing = lines[i][1]

            self.draw_multiple_lines(
                start, end, multiple_lines, multiple_lines_spacing, dir_count)

            start[dir_count] += spacing


def main():
    parser = argparse.ArgumentParser(
        description="Generate an SVG file defining a go board",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-s", "--size", default="13", choices=sizeOptions.keys(),
                        help="Size of go board to generate")

    parser.add_argument("--half_board", default=False, action="store_true")

    parser.add_argument("-o", "--output", default=DefaultOptions['output']['goban'],
                        help="Output filename")

    parser.add_argument("--test", default=False, action="store_true",
                        help="With this option set, instead of a go board a test file will be created to find the line spacing for the laser cutter")
    parser.add_argument("--no_border", action="store_true",
                        help="Don't draw the border around the board")
    parser.add_argument(
        "--rounded_corners", default=DefaultOptions['rounded_corners'], help="Radius of rounded corners in mm. 0 for no rounded corners.")

    parser.add_argument("-m", "--margin", default=DefaultOptions['margin'], help='Margin from the board edge to the lines in mm.')

    parse_opt = parser.parse_args()

    # Get the options for the chosen size
    options = sizeOptions[parse_opt.size]

    # Enrich options with defaults
    options.update(DefaultOptions)

    # Add options from arguments
    options['half_board'] = parse_opt.half_board
    options['border'] = not parse_opt.no_border
    options['rounded_corners'] = (int)(parse_opt.rounded_corners)

    b = GoBoard(options)

    if parse_opt.test:
        b.draw_test()
    else:
        b.draw()

    if parse_opt.test and parse_opt.output == DefaultOptions['output']['goban']:
        parse_opt.output = DefaultOptions['output']['test']

    b.write(parse_opt.output)


if __name__ == "__main__":
    sys.exit(main())
