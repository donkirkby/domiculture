import random
import unittest
from textwrap import dedent

import pytest
from networkx.exception import NodeNotFound

from domino_puzzle import Domino, Cell, Board, BoardGraph, CaptureBoardGraph


class DummyRandom(object):
    def __init__(self, randints=None, samples=None):
        self.randints = randints or {}  # {(min, max): [i, j, k]}
        self.samples = samples or []  # [[choice]]

    def randint(self, a, b):
        results = self.randints.get((a, b), None)
        return results.pop(0) if results else 0

    def sample(self, population, k):
        result = self.samples.pop(0)
        assert len(result) == k
        for x in result:
            assert x in population
        return result


class CellTest(unittest.TestCase):
    def testRepr(self):
        cell = Cell(4)

        s = repr(cell)

        self.assertEqual("Cell(4)", s)

    def testPips(self):
        cell = Cell(5)

        pips = cell.pips

        self.assertEqual(5, pips)

    def testFindNeighbours(self):
        board = Board.create("""\
x 3|2

1|0 x
""")
        cell = board[1][0]
        expected_neighbours = {board[1][1]}

        neighbours = set(cell.find_neighbours())

        self.assertEqual(expected_neighbours, neighbours)


class DominoTest(unittest.TestCase):
    def testRepr(self):
        domino1 = Domino(5, 3)

        s = repr(domino1)

        self.assertEqual("Domino(5, 3)", s)

    def testInit(self):
        domino1 = Domino(5, 3)

        pips = domino1.head.pips

        self.assertEqual(5, pips)

    def testCreate(self):
        expected_dominoes = [Domino(0, 0),
                             Domino(0, 1),
                             Domino(0, 2),
                             Domino(1, 1),
                             Domino(1, 2),
                             Domino(2, 2)]
        dominoes = Domino.create(2)

        self.assertEqual(expected_dominoes, dominoes)

    def testEqual(self):
        domino1 = Domino(5, 3)
        domino2 = Domino(5, 3)

        eq_result = domino1 == domino2
        neq_result = domino1 != domino2
        self.assertTrue(eq_result)
        self.assertFalse(neq_result)

    def testDifferentPips(self):
        domino1 = Domino(5, 3)
        domino2 = Domino(5, 4)
        domino3 = Domino(6, 3)

        eq_result = domino1 == domino2
        neq_result = domino1 != domino2
        self.assertFalse(eq_result)
        self.assertTrue(neq_result)
        self.assertNotEqual(domino1, domino3)

    def testEqualFlipped(self):
        domino1 = Domino(5, 3)
        domino2 = Domino(3, 5)

        eq_result = domino1 == domino2
        neq_result = domino1 != domino2
        self.assertTrue(eq_result)
        self.assertFalse(neq_result)

    def testHashFlipped(self):
        domino1 = Domino(5, 3)
        domino2 = Domino(3, 5)

        hash1 = hash(domino1)
        hash2 = hash(domino2)

        self.assertEqual(hash1, hash2)

    def testRotateFullCircle(self):
        domino1 = Domino(1, 5)

        domino1.rotate(180)
        domino1.rotate(180)

        self.assertEqual(0, domino1.degrees)

    def testRotateNegative(self):
        domino1 = Domino(1, 5)

        domino1.rotate(-90)

        self.assertEqual(270, domino1.degrees)

    def testFindNeighbours(self):
        state = """\
1 0|2 x x
-
0 0|4 0|3
"""
        board = Board.create(state)
        domino1 = board[1][1].domino
        expected_neighbours = {board[0][1].domino, board[1][0].domino}

        neighbours = domino1.find_neighbours()

        self.assertEqual(expected_neighbours, neighbours)

    def testHasNoMatch(self):
        state = """\
1 0
- -
0 2
"""
        board = Board.create(state)
        domino = board[1][1].domino

        self.assertFalse(domino.hasMatch())

    def testHasMatch(self):
        state = """\
1 2
- -
0 0
"""
        board = Board.create(state)
        domino = board[1][1].domino

        self.assertTrue(domino.hasMatch())

    def testFindNoMatch(self):
        state = """\
1 0
- -
0 2
"""
        board = Board.create(state)
        domino = board[1][1].domino
        matches = domino.findMatches()
        expected_matches = []

        self.assertEqual(expected_matches, matches)

    def testFindMatch(self):
        state = """\
1 2
- -
0 0
"""
        board = Board.create(state)
        domino = board[1][1].domino
        matches = domino.findMatches()
        coordinates = [(cell.x, cell.y) for cell in matches]
        expected_coordinates = [(0, 0), (1, 0)]

        self.assertEqual(expected_coordinates, coordinates)

    def testIsMatch(self):
        domino1 = Domino(0, 1)

        self.assertFalse(domino1.isMatch(Domino(2, 2)))
        self.assertTrue(domino1.isMatch(Domino(0, 2)))
        self.assertTrue(domino1.isMatch(Domino(2, 1)))
        self.assertTrue(domino1.isMatch(Domino(2, 0)))
        self.assertTrue(domino1.isMatch(Domino(1, 2)))

    def testName(self):
        domino = Domino(1, 2)
        name = domino.get_name()

        self.assertEqual("12", name)

    def testDescribeMove(self):
        domino1 = Domino(1, 2)
        dx, dy = 1, 0
        expected_move = '12r'

        move = domino1.describe_move(dx, dy)

        self.assertEqual(expected_move, move)

    def testDescribeMoveReversed(self):
        domino1 = Domino(1, 2)
        domino1.rotate(180)
        dx, dy = 1, 0
        expected_move = '21r'

        move = domino1.describe_move(dx, dy)

        self.assertEqual(expected_move, move)

    def testDescribeMoveUpReversed(self):
        domino1 = Domino(1, 2)
        domino1.rotate(90)
        dx, dy = 0, 1
        expected_move = '21u'

        move = domino1.describe_move(dx, dy)

        self.assertEqual(expected_move, move)


class BoardGraphTest(unittest.TestCase):
    def testWalkRight(self):
        board = Board.create("""\
0|2 x

0|1 x
""")
        graph = BoardGraph()
        expected_states = set("""\
0|2

0|1
---
0|2 x

x 0|1
---
x 0|2

0|1 x
""".split('---\n'))

        states = graph.walk(board)

        self.assertEqual(expected_states, states)

    def testWalkLeft(self):
        board = Board.create("""\
x 0|2

0|1 x
""")
        graph = BoardGraph()
        expected_states = set("""\
0|2

0|1
---
0|2 x

x 0|1
---
x 0|2

0|1 x
""".split('---\n'))

        states = graph.walk(board)

        self.assertEqual(expected_states, states)

    def testWalkDown(self):
        board = Board.create("""\
x 3 x x x
  -
x 2 0|2 x

x 0|1 x x
""")
        graph = BoardGraph()
        expected_states = set("""\
3 x x
-
2 0|2

0|1 x
---
3 x x
-
2 0|2

x 0|1
---
3 x x x
-
2 0|2 x

x x 0|1
---
3 0|2
-
2 0|1
---
3 0|2 x
-
2 x 0|1
""".split('---\n'))

        states = graph.walk(board)

        self.assertEqual(expected_states, states)

    def ignoreWalkLast(self):
        """ Switching to NetworkX broke this. Not really used, so ignore for now.
        """
        board = Board.create("""\
3 x x
-
2 0|2

0|1 x
""")
        graph = BoardGraph()
        expected_last = """\
3 0|2 x
-
2 x 0|1
"""

        graph.walk(board)

        self.assertMultiLineEqual(expected_last, graph.last)

    def testWalkNoSplit(self):
        board = Board.create("""\
x 3|2 3|1 x
""")
        graph = BoardGraph()
        expected_states = set("""\
3|2 3|1
""".split('---\n'))

        states = graph.walk(board)

        self.assertEqual(expected_states, states)

    def testWalkNoLoner(self):
        board = Board.create("""\
x 3 5 x
  - -
x 2 4 x

x 3|5 x
""")
        graph = BoardGraph()
        expected_states = set("""\
3 5
- -
2 4

3|5
""".split('---\n'))

        states = graph.walk(board)

        self.assertEqual(expected_states, states)


class CaptureBoardGraphTest(unittest.TestCase):
    def testCaptureRight(self):
        board = Board.create("""\
0|2 x

1|0 x
""")
        graph = CaptureBoardGraph()
        expected_states = set("""\
0|2

1|0
---
""".split('---\n'))

        states = graph.walk(board)

        self.assertEqual(expected_states, states)

    def testSomeUncaptured(self):
        board = Board.create("""\
4|4 3
    -
1|5 4
""")
        graph = CaptureBoardGraph()
        expected_states = set("""\
4|4 3
    -
1|5 4
---
1|5
""".split('---\n'))

        states = graph.walk(board)

        self.assertEqual(expected_states, states)

    def testMoveWithoutCapture(self):
        board = Board.create("""\
4|3

1|2
""")
        graph = CaptureBoardGraph()
        expected_states = set("""\
4|3

1|2
---
x 4|3

1|2 x
""".split('---\n'))

        states = graph.walk(board)

        self.assertEqual(expected_states, states)

    @staticmethod
    def testMoveLeftUpdatesOffset():
        start_state = """\
4|3

1|2
"""
        board = Board.create(start_state, border=1)
        graph = CaptureBoardGraph()
        expected_state = """\
x 4|3

1|2 x
"""
        graph.walk(board)
        offset = [1, 1]  # position of bottom left corner (within border)
        expected_offset = [1, 0]  # equivalent position after move and cropping

        state, remaining = graph.move(board[1][1].domino, -1, 0, offset)

        assert state == expected_state
        assert offset == expected_offset

    def testSolution(self):
        graph = CaptureBoardGraph()
        expected_solution = ['34u', '24r']
        expected_closest = ''
        board = Board.create("""\
6|2 3
    -
2|4 4
""")
        graph.walk(board)
        solution = graph.get_solution()

        self.assertEqual(expected_solution, solution)
        self.assertEqual(expected_closest, graph.closest)

    @staticmethod
    def testNoSolution():
        graph = CaptureBoardGraph()
        board = Board.create("""\
6|2 3
    -
2|4 5
""")
        expected_closest = """\
3
-
5
"""
        graph.walk(board)

        assert graph.closest == expected_closest
        with pytest.raises(NodeNotFound):
            graph.get_solution()

    @staticmethod
    def testNoMoves():
        graph = CaptureBoardGraph()
        board = Board.create("""\
6|2 3
    -
1|4 5
""")
        expected_closest = """\
6|2 3
    -
1|4 5
"""
        graph.walk(board)

        assert graph.closest == expected_closest
        with pytest.raises(NodeNotFound):
            graph.get_solution()

    def testPartialSolution(self):
        graph = CaptureBoardGraph()
        expected_solution = ['62l']
        board = Board.create("""\
6|2 3
    -
2|4 5
""")
        graph.walk(board)

        solution = graph.get_solution(return_partial=True)

        self.assertEqual(expected_solution, solution)

    def testDisconnectedBeforeCapture(self):
        """ Board must be connected after move and after capture.

        Here, move 62L is disconnected after the move, but connected after
        the capture removes most of the dominoes. Test that the move is still
        not allowed.
        """
        board = Board.create("""\
x x x x 5
        -
x x 6|2 3

6|6 2|4 x
""")
        graph = CaptureBoardGraph()
        expected_states = set("""\
x x x x 5
        -
x x 6|2 3

6|6 2|4 x
""".split('---\n'))

        states = graph.walk(board)

        self.assertEqual(expected_states, states)


def test_dice_set():
    board = Board.create("""\
1|2 3
    -
4|5 6
---
dice:(2,1)3,(0,0)4
""")
    dice_set = board.dice_set

    assert repr(dice_set) == "DiceSet('(2,1)3,(0,0)4')"
    assert dice_set[2, 1] == 3
    assert dice_set[1, 1] is None


def test_dice_set_move_with_border():
    board = Board.create("""\
1|2 3
    -
4|5 6
---
dice:(2,1)3,(0,0)4
""", border=1)
    expected_display = """\
1|2 3
    -
4|5 6
---
dice:(1,1)3,(0,0)4
"""
    board.dice_set.move((3, 2), (2, 2))

    assert board.display(cropped=True) == expected_display


def test_arrow_set():
    board = Board.create("""\
1|2 3
    -
4|5 6
---
arrows:(2,1)L2D1,(1,0)R1
""")
    arrows = board.arrows

    assert repr(arrows) == "ArrowSet('(2,1)L2D1,(1,0)R1')"
    assert arrows.positions == [[(2, 1), (0, 1), (0, 0)],
                                [(1, 0), (2, 0)]]


def test_mutate_after_removal():
    """ Removing an extra domino means it can't be used in a mutation. """
    board = Board.create(dedent("""\
        0|0 0
            -
        1|1 1"""), max_pips=2)
    board.extra_dominoes.clear()

    for _ in range(10):
        mutated = board.mutate(random)

        assert Domino(2, 2) not in mutated.dominoes
