import unittest
import board
import random

class TestBoardMoves(unittest.TestCase):
    def test_move_validation(self):
        b = board.Board()

        # Fill up the second column of the board; all the other moves should be valid
        b.all_pieces = (-1) & board.COLUMN_MASKS[1]

        # Out-of-bounds checks
        with self.assertRaises(board.IllegalMoveException):
            b.apply_move(-1)

        with self.assertRaises(board.IllegalMoveException):
            b.apply_move(board.NUM_COLS)

        for c in range(board.NUM_COLS):
            if c == 1:
                with self.assertRaises(board.IllegalMoveException):
                    b.apply_move(c)
            else:
                b.apply_move(c)
    
    def test_get_legal_move_cols(self):
        b = board.Board()

        # Fill up the second column of the board; all the other moves should be valid
        b.all_pieces = (-1) & board.COLUMN_MASKS[1]

        self.assertEqual([c for c in range(board.NUM_COLS) if c != 1], b.get_legal_move_cols())

    def test_random_apply_unapply(self):
        rand = random.Random(0)
        b = board.Board()

        num_moves = 0
        while moves := b.get_legal_move_cols():
            b.apply_move(rand.choice(moves))
            num_moves += 1
        
        self.assertEqual(board.NUM_COLS * board.NUM_ROWS, num_moves)
        
        # Board is full now, try to backtrack
        for _ in range(num_moves):
            b.unapply_move()
        
        # Expect empty board
        self.assertEqual(0, b.all_pieces)
        self.assertEqual(0, b.player_board)

if __name__ == '__main__':
    unittest.main()