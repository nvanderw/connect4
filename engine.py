import board
from board import Board

WIN_EVAL = 10000
LOSS_EVAL = -WIN_EVAL
DRAW_EVAL = 0

def center_weight(player_board: int):
    # Controlling the center is important. Count the middle and adjacent columns.
    # int.bit_count uses GCC's __builtn_popcount which uses the POPCNT instruction
    # if it's available on this CPU.
    # https://github.com/python/cpython/blob/6784ef7da7cbf1a944fd0685630ced54e4a0066c/Include/internal/pycore_bitutils.h#L101
    score = 3 * (player_board & board.COLUMN_MASKS[3]).bit_count()
    score += 2 * (player_board & board.COLUMN_MASKS[2]).bit_count() + 2 * (player_board & board.COLUMN_MASKS[4]).bit_count()

    return score

def eval(b: Board) -> int:
    # There's a lot more we could add to the eval. 
    # Some possibilities:
    # * Track progress toward wins. Pre-generate masks for all winning lines (there are only 69 of them).
    #   Give a big bonus for 3-in-a-row (or column/diag) with an empty space.
    # * Track immediate threats (where the space can be filled on the next turn).
    # * Track double-threats/forks.
    return center_weight(b.player_board) - center_weight(b.opp_board())

class Engine:
    def __init__(self):
        self.nodes_visited = 0
        self.branches_pruned = 0

    # TODO: return PV as well
    def negamax(self, board: Board, depth: int) -> int:
        """
        Negamax search.
        """

        self.nodes_visited += 1
        if board.last_move_won():
            # The opponent's last move won, so we lost.
            return LOSS_EVAL + depth
        
        if board.is_full():
            return DRAW_EVAL

        if depth == 0:
            return eval(board)
        
        value = LOSS_EVAL
        for candidate in board.get_legal_move_cols():
            board.apply_move(candidate)

            if board.last_move_won():
                # We can't do better than winning at this depth, so bail out.
                board.unapply_move()
                return WIN_EVAL - (depth - 1) # depth - 1 because we've applied the next move

            value = max(value, -self.negamax(board, depth - 1))
            board.unapply_move()

        return value

    def negamax_alphabeta(self, board: Board, depth: int, alpha: int = LOSS_EVAL, beta: int = WIN_EVAL) -> int:
        """
        Negamax search with alpha-beta pruning.
        Adds to other parameters to the search:
            "alpha" - lower bound on this node's value; the best score side to move has found so far.
            "beta"  - upper bound on this node's value, from ancestors. The most the opponent would let us
                    get before abandoning this line and choosing something else.

        If alpha >= beta, our search window [alpha, beta) is empty. We've shown we can get at least alpha,
        and our opponent won't tolerate anything >= beta, so the rest of the nodes can't affect PV. Prune.
        """

        self.nodes_visited += 1
        if board.last_move_won():
            # The opponent's last move won, so we lost.
            return LOSS_EVAL + depth
        
        if board.is_full():
            return DRAW_EVAL

        if depth == 0:
            return eval(board)
        
        value = alpha 

        # TODO: better move ordering. Start with the center and move toward the sides.
        # If we use iterative deepening, start with the PV from the depth - 1 search.
        candidates = board.get_legal_move_cols()
        for i, candidate in enumerate(candidates):
            board.apply_move(candidate)

            if board.last_move_won():
                # We can't do better than winning at this depth, so bail out.
                board.unapply_move()
                
                # We don't need to consider further branches if we already found a win, so count that.
                self.branches_pruned += len(candidates) - i - 1
                return WIN_EVAL - (depth - 1)

            value = max(value, -self.negamax_alphabeta(board, depth - 1, -beta, -alpha))
            board.unapply_move()

            alpha = max(alpha, value)
            if alpha >= beta:
                # Keep track of how many moves we avoided considering, i.e.
                # all the ones after i. If we are to consider 7 moves, and i = 1, then
                # there are 5 moves left that we don't need to consider
                self.branches_pruned += len(candidates) - i - 1
                break

        return value

if __name__ == "__main__":
    e = Engine()
    print(f"Score: {e.negamax_alphabeta(Board(), 10)}")
    print(f"Nodes visited: {e.nodes_visited}")
    print(f"Branches pruned: {e.branches_pruned}")