# Goban #

`goban.py` generates an svg file for a [go board](https://en.wikipedia.org/wiki/Go_\(game\)#Boards) or goban.
The resulting file is suitable to print your own board.
I used it on wood with a [laser cutter](http://en.wikipedia.org/wiki/Laser_cutting) to create beautiful handmade boards.
The bed of my laser cutter was too small for full boards, so I made half boards and taped them together for handy flip boards (`--half_board`).

Since laser cutters create very thin lines, I made the program to draw multiple lines next to each other to make it appear thicker. In the default options, two lines with 0.25mm spacing are drawn everywhere. Use the `--test` argument to find out which spacing works for you and adjust it in the options at the top of the code.

## Usage ##

You will need svgwrite to use this program:

```bash
  pip install svgwrite
```

To use, simply run from the command line:

```bash
  python goban.py
```

To show the result you can use `eog goban.svg`.

### Arguments

There are a few command line arguments to modify the board.
Here's an example:

```bash
  python half_goban.py --size=19 --half_board
```

| Argument         | Description                                                                                            |
|-------------------|--------------------------------------------------------------------------------------------------------|
| --size, -s        | Size of the go board to generate [7, 9, 13, 19]                                                        |
| --margin, -m      | 'Margin from the board edge to the lines in mm                                                         |
| --rounded_corners | Radius of rounded corners in mm. 0 for no rounded corners.                                             |
| --no_border       | [Set] Don't draw the border around the board                                                           |
| --test            | [Set] Create a test file with different multi line spacings and amounts                               |
| --half_board      | [Set] Create only half of the board for flip boards, this can be useful for smaller laser cutter beds. |
| --output, -o      | Output file path        
