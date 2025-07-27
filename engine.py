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
    return center_weight(b.player_board) - center_weight(b.opp_board())

# TODO: return PV as well
def negamax(board: Board, depth: int) -> int:
    """
    Negamax search.
    """

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

        value = max(value, -negamax(board, depth - 1))
        board.unapply_move()

    return value

def negamax_alphabeta(board: Board, depth: int, alpha: int = LOSS_EVAL, beta: int = WIN_EVAL) -> int:
    """
    Negamax search with alpha-beta pruning.
    Adds to other parameters to the search:
        "alpha" - lower bound on this node's value; the best score side to move has found so far.
        "beta"  - upper bound on this node's value, from ancestors. The most the opponent would let us
                  get before abandoning this line and choosing something else.

    If alpha >= beta, our search window [alpha, beta) is empty. We've shown we can get at least alpha,
    and our opponent won't tolerate anything >= beta, so the rest of the nodes can't affect PV. Prune.
    """

    if board.last_move_won():
        # The opponent's last move won, so we lost.
        return LOSS_EVAL + depth
    
    if board.is_full():
        return DRAW_EVAL

    if depth == 0:
        return eval(board)
    
    value = LOSS_EVAL

    # TODO: better move ordering
    for candidate in board.get_legal_move_cols():
        board.apply_move(candidate)

        if board.last_move_won():
            # We can't do better than winning at this depth, so bail out.
            board.unapply_move()
            return WIN_EVAL - (depth - 1)

        value = max(value, -negamax_alphabeta(board, depth - 1, -beta, -alpha))
        board.unapply_move()

        alpha = max(alpha, value)
        if alpha >= beta:
            break

    return value