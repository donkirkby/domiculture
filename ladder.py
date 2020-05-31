import random

from domino_puzzle import Board, BadPositionError, Domino, BoardGraph, GraphLimitExceeded
from evo import Evolution, Individual


class LadderBoard(Board):
    @classmethod
    def create(cls, state, border=0, max_pips: int = 6):
        """ Create a ladder board.

        :param state: Standard board state, plus '---' and an extra status line
            that holds the move type and the target number. Move type is 'M' for
            marker and 'D' for domino, so 'D2' means a domino move with a target
            of 2.
        :param border: number of blank rows and columns to add around the edge
        :param max_pips: maximum number of pips in the full set of dominoes
        """
        divider = '\n---\n'
        sections = state.split(divider)
        if len(sections) > 1:
            move_state = sections.pop()
        else:
            move_state = '1'
        board_state = divider.join(sections)
        board = super().create(board_state, border, max_pips)
        board.target = int(move_state)
        if not board.markers and len(board.dominoes) > 1:
            board.markers[(0, 0)] = 'P'
            board.markers[(board.width-1, 0)] = 'R'
            board.markers[(0, board.height-1)] = 'N'
            board.markers[(board.width-1, board.height-1)] = 'B'
        return board

    def __init__(self, width, height, max_pips=None):
        super().__init__(width, height, max_pips)
        self.target = 1

    def display(self, cropped=False, cropping_bounds=None):
        domino_display = super().display(cropped, cropping_bounds)
        return f'{domino_display}---\n{self.target}\n'

    def advance_target(self):
        self.target = self.target % self.max_pips + 1

    def revert_target(self):
        self.target = (self.target + self.max_pips - 2) % self.max_pips + 1


class LadderGraph(BoardGraph):
    def __init__(self, board_class=LadderBoard):
        super().__init__(board_class)
        self.min_marker_area = None

    def generate_moves(self, board: LadderBoard):
        if board.are_markers_connected:
            if self.last is None:
                self.last = '0|0\n---\n1'
            yield 'SOLVED', self.last
            return
        marker_area = board.marker_area
        if self.min_marker_area is None or marker_area < self.min_marker_area:
            self.min_marker_area = marker_area
        for domino in board.dominoes[:]:
            dx, dy = domino.direction
            yield from self.try_move_domino(domino, dx, dy)
            yield from self.try_move_domino(domino, -dx, -dy)
        for x, y in list(board.markers.keys()):
            for dx, dy in Domino.directions:
                yield from self.try_move_marker(board, x, y, dx, dy)

    def try_move_marker(self, board: LadderBoard, x: int, y: int, dx: int, dy: int):
        try:
            move, new_state, heuristic = self.move_marker(board, x, y, dx, dy)
            yield move, new_state, None, heuristic
        except BadPositionError:
            pass

    def move_marker(self, board: LadderBoard, x: int, y: int, dx: int, dy: int):
        x2 = x+dx
        y2 = y+dy
        new_cell = board[x2][y2]
        if new_cell is None:
            raise BadPositionError('Marker cannot move off the board.')
        if new_cell.pips != board.target:
            raise BadPositionError(f'Marker must move onto a {board.target}.')
        if (x2, y2) in board.markers:
            raise BadPositionError(f'A marker is already on {x2}, {y2}.')
        direction_name = Domino.describe_direction(dx, dy).upper()
        marker = board.markers.pop((x, y))
        board.markers[(x2, y2)] = marker
        move = f'{marker}{direction_name}{board.target}'
        board.advance_target()

        new_state = board.display(cropped=True)
        heuristic = self.calculate_heuristic(board)

        board.revert_target()
        del board.markers[(x2, y2)]
        board.markers[(x, y)] = marker
        return move, new_state, heuristic

    def try_move_domino(self, domino: Domino, dx: int, dy: int):
        try:
            move, new_state, heuristic = self.move_domino(domino, dx, dy)
            yield move, new_state, None, heuristic
        except BadPositionError:
            pass

    def move_domino(self, domino, dx, dy):
        domino_markers = [
            domino.head.board.markers.get((cell.x, cell.y))
            for cell in (domino.head, domino.tail)]
        marker = domino_markers[0]
        if marker is None:
            marker = domino_markers[1]
            marker_cell = domino.tail
            domino_pips = domino.head.pips
        else:
            marker_cell = domino.head
            if domino_markers[1] is not None:
                raise BadPositionError('Cannot move a domino with two markers.')
            domino_pips = domino.tail.pips
        if marker is None:
            raise BadPositionError('Cannot move a domino without a marker.')
        board = domino.head.board
        if domino_pips != board.target:
            raise BadPositionError(f'Cannot move a domino showing {domino_pips}'
                                   f' when the target is {board.target}')
        direction_name = domino.describe_direction(dx, dy).upper()
        move = f'{marker}D{direction_name}{board.target}'
        original_markers = board.markers.copy()
        try:
            del board.markers[(marker_cell.x, marker_cell.y)]
            domino.move(dx, dy)
            board.markers[(marker_cell.x, marker_cell.y)] = marker
        except Exception:
            board.markers = original_markers
            raise
        try:
            board.advance_target()
            if not board.is_connected():
                raise BadPositionError('Board is not connected.')
            heuristic = self.calculate_heuristic(board)
            return move, board.display(cropped=True), heuristic
        finally:
            board.revert_target()
            domino.move(-dx, -dy)
            board.markers = original_markers

    def calculate_heuristic(self, board):
        # Calculate centre of mass for markers.
        x_sum = y_sum = 0
        for x, y in board.markers:
            x_sum += x
            y_sum += y
        marker_count = len(board.markers)
        cx = x_sum // marker_count
        cy = y_sum // marker_count

        # Count moves to centre.
        total_moves = 0
        for x, y in board.markers:
            total_moves += abs(x - cx) + abs(y-cy)

        # Not all pieces have to get all the way to the centre.
        total_moves -= min(total_moves, marker_count)
        return total_moves


class LadderProblem(Individual):
    def __repr__(self):
        return f'LadderProblem({self.value!r}'

    def pair(self, other, pair_params):
        return LadderProblem(self.value)

    def mutate(self, mutate_params):
        max_pips = self.value['max_pips']
        board = LadderBoard.create(self.value['start'], max_pips=max_pips)
        new_board = board.mutate(random, LadderBoard)
        self.value = dict(start=new_board.display(), max_pips=max_pips)

    def _random_init(self, init_params):
        max_pips = init_params['max_pips']
        board = LadderBoard(**init_params)
        while True:
            if board.fill(random):
                break

        return dict(start=board.display(), max_pips=max_pips)


class FitnessCalculator:
    def __init__(self, target_length=None):
        self.target_length = target_length

    def calculate(self, problem):
        """ Calculate fitness score based on the solution length.

        -100,000 if there's no solution.
        -1000 * abs(solution_length-target_length)
        -10*max_choices
        -avg_choices
        """
        value = problem.value
        fitness = value.get('fitness')
        if fitness is not None:
            return fitness
        board = LadderBoard.create(value['start'], max_pips=value['max_pips'])
        graph = LadderGraph()
        fitness = 0
        try:
            graph.walk(board, size_limit=10_000)
        except GraphLimitExceeded:
            pass
        if graph.last is None:
            fitness -= 100_000
            fitness -= graph.min_marker_area
        else:
            solution_nodes = graph.get_solution_nodes()
            solution_moves = graph.get_solution(solution_nodes=solution_nodes)
            domino_move_count = sum(len(move) == 4 for move in solution_moves)
            fitness += 1000*domino_move_count
            if self.target_length is None:
                fitness += len(solution_nodes)*1000
            else:
                fitness -= 1000*abs(len(solution_nodes) - self.target_length)

            max_choices = graph.get_max_choices(solution_nodes)
            average_choices = graph.get_average_choices(solution_nodes)
            fitness -= max_choices*10
            fitness -= average_choices

        value['fitness'] = fitness
        return fitness


def main():
    max_pips = 5
    fitness_calculator = FitnessCalculator(target_length=20)
    init_params = dict(max_pips=max_pips, width=max_pips+1, height=max_pips)
    evo = Evolution(
        pool_size=100,
        fitness=fitness_calculator.calculate,
        individual_class=LadderProblem,
        n_offsprings=30,
        pair_params=None,
        mutate_params=None,
        init_params=init_params)
    n_epochs = 1000

    hist = []
    for i in range(n_epochs):
        top_individual = evo.pool.individuals[-1]
        top_fitness = evo.pool.fitness(top_individual)
        mid_fitness = evo.pool.fitness(evo.pool.individuals[-len(evo.pool.individuals)//5])
        print(i, top_fitness, mid_fitness, repr(top_individual.value['start']))
        hist.append(top_fitness)
        evo.step()

    best = evo.pool.individuals[-1]
    for problem in evo.pool.individuals:
        print(evo.pool.fitness(problem))
    # plt.plot(hist)
    # plt.show()
    start = best.value['start']
    print(start)


if __name__ == '__main__':
    main()
