from board import Board

WIN_EVAL = 10000
LOSS_EVAL = -WIN_EVAL

def eval(b: Board) -> int:
    if Board.has_four(b.player_board):
        return WIN_EVAL
    
    if Board.has_four(b.opp_board()):
        return LOSS_EVAL

    # TODO improve eval
    return 0

def negamax(board: Board, depth: int) -> int:
    """
    Negamax search.
    """

    if depth == 0:
        return eval(board)

    if board.last_move_won():
        # The opponent's last move won, so we lost
        return LOSS_EVAL
    
    value = LOSS_EVAL
    for candidate in board.get_legal_move_cols():
        board.apply_move(candidate)
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

    if depth == 0:
        return eval(board)

    if board.last_move_won():
        # The opponent's last move won, so we lost
        return LOSS_EVAL
    
    value = LOSS_EVAL
    for candidate in board.get_legal_move_cols():
        board.apply_move(candidate)
        value = max(value, -negamax_alphabeta(board, depth - 1, -beta, -alpha))
        board.unapply_move()

        alpha = max(alpha, value)
        if alpha >= beta:
            break

    return value