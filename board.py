# Connect 4 board with 6 rows and 7 columns.

# We'll use a bitboard. Since dropping pieces happens on *columns* in Connect 4,
# we'll put columns contiguously in the boardboard. Picture a normal Connect 4
# board rotated 90 degrees to the right.

# To keep columns from "overflowing" into each other we'll keep 1 sentinel bit between them.
# (This makes it easy to implement win detection via shifts without accidentally shifting bits from one
# column into the next).
# So the board looks like the following, from least-significant bit to most-significant bit:

# a0 a1 a2 a3 a4 a5 0
# b0 b1 b2 b3 b4 b5 0
# c0 c1 c2 c3 c4 c5 0
# d0 d1 d2 d3 d4 d5 0
# e0 e1 e2 e3 e4 e5 0
# f0 f1 f2 f3 f4 f5 0
# g0 g1 g2 g3 g4 g5 0

# With a..g as columns and 0..6 as rows in the Connect 4 board. Total board size with sentinels is 7*7=49.

# In the board state, we'll keep track of two bitmasks: the player board, which just has a 1 everywhere the
# current player has a piece, and the all_pieces board, which has a 1 everywhere *either* player has a piece.
# We can XOR these together to get the board with just the opponent's pieces.

# The neat thing about having the columns represented as contiguous bits is that it's easy to figure out
# where a "dropped" piece goes. Say we have a column from all_pieces:
# 111100

# By just adding 1 at the "bottom" of the column, we get: 000010. The 1 carries all the way over to the
# "lowest" available spot to give us a mask 000010, which is the bitmask of the "move".

import functools
import random

NUM_ROWS = 6
NUM_COLS = 7
STRIDE = NUM_ROWS + 1 # Include the extra sentinel bit.

# Masks for each column, not including the sentinel bit.
COLUMN_MASKS = [((1 << (STRIDE - 1)) - 1) << (STRIDE * c) for c in range(NUM_COLS)]

# Mask for all the playable positions on the board
BOARD_MASK = functools.reduce(lambda x, y: x | y, COLUMN_MASKS, 0)

# Masks for just the bottom bit of each column - to play a piece, we'll add this to the column and
# let the bit "carry" into the first available 0 (empty spot).
BOTTOM_MASKS = [1 << (STRIDE * c) for c in range(NUM_COLS)]

# Masks for the top bit of each column; used to check which columns are full so we can compute
# the list of legal moves
TOP_MASKS = [1 << (STRIDE * c + STRIDE - 2) for c in range(NUM_COLS)]

# Zobrist hashes. We need a random hash for each position + piece combo, plus a side-to-move hash.
# So this is essentially a map of color -> square -> hash.
SQUARE_HASHES = [
    [
        random.randrange(0, 1<<64) for _ in range(NUM_COLS * NUM_ROWS)
    ] for _ in range(2)
]

SIDE_TO_MOVE_HASH = random.randrange(0, 1<<64)

# In order to look up the SQUARE_HASHES for a given move, we need to know what the bit index of the
# move is. There are some bitwise ways we could do this but it's easiest to just generate
# a lookup table from move mask -> square index (0..48).
MOVE_MASK_TO_SQUARE_IX = {}

for c in range(NUM_COLS):
    for r in range(NUM_ROWS):
        MOVE_MASK_TO_SQUARE_IX[1 << (c * STRIDE + r)] = c * NUM_ROWS + r

class Debug:
    @staticmethod
    def print_mask(mask: int):
        for c in range(NUM_COLS):
            # Col mask that includes sentinels
            col_mask = ((1 << STRIDE) - 1) << (c * STRIDE)
            col = (mask & col_mask) >> (c * STRIDE)

            # Print each bit in the column from LSB -> MSB
            for b in range(STRIDE):
                print(col & 1, end = "")
                col >>= 1

            print()

class IllegalMoveException(Exception):
    pass

class Board:
    """
    Represents a 7x6 Connect-4 board.
    """
    def __init__(self):
        # player_board is the bits of the side to move.
        # all_pieces is the bits of every piece on the board.
        # player_board ^ all_pieces gives the bits of the other player.
        self.player_board = 0
        self.all_pieces = 0

        # Stack of move masks so we can easily unapply moves.
        self.move_stack = []

        # Zobrist hash
        self.hash = 0
    
    def get_legal_move_cols(self) -> list[int]:
        """
        Gets the column indices which are legal moves i.e. aren't already full.
        """
        return [c for c in range(NUM_COLS) if (TOP_MASKS[c] & self.all_pieces) == 0]
    
    def apply_move(self, c: int):
        """
        Drops a piece into the column index c.
        """
        if c < 0 or c >= NUM_COLS:
            raise IllegalMoveException(f"Column is out-of-bounds: {c}")

        # Get the move mask: a 1 in the position where the new piece is going to be.
        # This uses the addition trick mentioned above.
        move_mask = (self.all_pieces + BOTTOM_MASKS[c]) & COLUMN_MASKS[c]
        if move_mask == 0:
            raise IllegalMoveException(f"Tried to drop piece in full column {c}")

        # Switch player board mask first; safe because the new piece is on this player's board, not opponent's
        self.player_board ^= self.all_pieces
        self.all_pieces ^= move_mask

        self.hash ^= SIDE_TO_MOVE_HASH
        self.hash ^= SQUARE_HASHES[len(self.move_stack) & 1][MOVE_MASK_TO_SQUARE_IX[move_mask]]

        self.move_stack.append(move_mask)
    
    def unapply_move(self):
        """
        Reverts the most recent move.
        """
        move_mask = self.move_stack.pop()

        # The last move was made by the opponent; we don't need to undo it from this player's board.
        # Just clear it from all_pieces and then swap the player.
        self.all_pieces ^= move_mask
        self.player_board ^= self.all_pieces

        self.hash ^= SIDE_TO_MOVE_HASH
        self.hash ^= SQUARE_HASHES[len(self.move_stack) & 1][MOVE_MASK_TO_SQUARE_IX[move_mask]]
    
    @staticmethod
    def has_four(player_board) -> bool:
        """
        Checks if a given player board has 4 in a row, column, or diagonal.
        Use last_move_won to determine if the last applied move was a win for the previous player.
        """

        # Vertical win detection: how would we test for 2 consecutive bits? Shift and AND
        m = player_board & (player_board >> 1) # Each 1 here represents the lowest bit in a 2-in-a-row.

        # 4 consecutive bits is just 2 pairs of 2 consecutive bits.
        if m & (m >> 2):
            return True

        # Horizontal win detection: basically the same as vertical, but shifting by STRIDE instead of 1.
        m = player_board & (player_board >> STRIDE)
        if m & (m >> (2 * STRIDE)):
            return True
        
        # Diagonals: same as above, but we'll use STRIDE - 1 or STRIDE + 1 to "offset" the check up or down.
        m = player_board & (player_board >> (STRIDE - 1))
        if m & (m >> (2 * (STRIDE - 1))):
            return True

        m = player_board & (player_board >> (STRIDE + 1))
        if m & (m >> (2 * (STRIDE + 1))):
            return True
        
        return False
    
    def opp_board(self):
        """
        Returns the player board from the opponent's perspective. Use player_board for the
        current player's perspective.
        """
        return self.all_pieces ^ self.player_board

    def last_move_won(self) -> bool:
        """
        Checks if the *opponent's* board has 4 in a row, column, or diagonal.
        This is needed to check for wins after a move was played.
        """

        # Since we've already swapped to the next player after applying the last move,
        # we need to evaluate the opponent's board here.
        return Board.has_four(self.all_pieces ^ self.player_board)
    
    def is_full(self) -> bool:
        """
        Checks if the board is full; if so, this is a draw.
        """
        return (self.all_pieces & BOARD_MASK) == BOARD_MASK