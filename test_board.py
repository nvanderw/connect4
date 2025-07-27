import unittest
import board
import random

from dataclasses import dataclass

# Helper function to parse a human-readable bitboard into an int.
def parse_board(input: list[str]) -> int:
    result = 0

    for col in input:
        for bit in col:
            if bit != "0" and bit != "1":
                raise Exception(f"Unexpected input: {bit}")
            
            result <<= 1
            result |= int(bit)
    
    return result

class TestBoard(unittest.TestCase):
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
        print()
        for _ in range(num_moves):
            b.unapply_move()
        
        # Expect empty board
        self.assertEqual(0, b.all_pieces)
        self.assertEqual(0, b.player_board)

        # Expect empty hash; this checks consistency of our Zobrist hashes across apply/unapply
        self.assertEqual(0, b.hash)
    
    def test_last_move_won(self):
        @dataclass
        class TestCase:
            name: str
            expect_win: bool
            bits: list[str]

        test_cases = [
            # Vertical test cases
            TestCase(
                name = "Vertical win",
                expect_win = True,
                bits = [
                    "0000000",
                    "0000000",
                    "0011110",
                    "0000000",
                    "0000000",
                    "0000000",
                    "0000000",
                ]
            ),
            TestCase(
                name = "Vertical not-win #1",
                expect_win = False,
                bits = [
                    "0000000",
                    "0000000",
                    "0011010",
                    "0000000",
                    "0000000",
                    "0000000",
                    "0000000",
                ]
            ),
            TestCase(
                name = "Vertical not-win #2",
                expect_win = False,
                bits = [
                    "0000000",
                    "0000000",
                    "0011100",
                    "0000000",
                    "0000000",
                    "0000000",
                    "0000000",
                ]
            ),

            # Horizontal test cases
            TestCase(
                name = "Horizontal win",
                expect_win = True,
                bits = [
                    "0000000",
                    "0001000",
                    "0001000",
                    "0001000",
                    "0001000",
                    "0000000",
                    "0000000",
                ]
            ),
            TestCase(
                name = "Horizontal not-win #1",
                expect_win = False,
                bits = [
                    "0000000",
                    "0001000",
                    "0001000",
                    "0001000",
                    "0000000",
                    "0000000",
                    "0000000",
                ]
            ),
            TestCase(
                name = "Horizontal not-win #2",
                expect_win = False,
                bits = [
                    "0000000",
                    "0001000",
                    "0001000",
                    "0000000",
                    "0001000",
                    "0000000",
                    "0000000",
                ]
            ),

            # Diagonal test cases /
            TestCase(
                name = "Diagonal win /",
                expect_win = True,
                bits = [
                    "0000000",
                    "0000010",
                    "0000100",
                    "0001000",
                    "0010000",
                    "0000000",
                    "0000000",
                ]
            ),
            TestCase(
                name = "Diagonal not-win /1",
                expect_win = False,
                bits = [
                    "0000000",
                    "0000010",
                    "0000100",
                    "0000000",
                    "0010000",
                    "0000000",
                    "0000000",
                ]
            ),
            TestCase(
                name = "Diagonal not-win /2",
                expect_win = False,
                bits = [
                    "0000000",
                    "0000010",
                    "0000100",
                    "0001000",
                    "0000000",
                    "0000000",
                    "0000000",
                ]
            ),

            # Diagonal test cases \
            TestCase(
                name = "Diagonal win \\",
                expect_win = True,
                bits = [
                    "0000000",
                    "0000000",
                    "0010000",
                    "0001000",
                    "0000100",
                    "0000010",
                    "0000000",
                ]
            ),
            TestCase(
                name = "Diagonal not-win \\1",
                expect_win = False,
                bits = [
                    "0000000",
                    "0000000",
                    "0010000",
                    "0000000",
                    "0000100",
                    "0000010",
                    "0000000",
                ]
            ),
            TestCase(
                name = "Diagonal not-win \\2",
                expect_win = False,
                bits = [
                    "0000000",
                    "0000000",
                    "0000000",
                    "0001000",
                    "0000100",
                    "0000010",
                    "0000000",
                ]
            ),
        ]

        for test_case in test_cases:
            player_board = parse_board(test_case.bits)
            self.assertEqual(test_case.expect_win, board.Board.has_four(player_board), f"Failed test case \"{test_case.name}\"")

if __name__ == '__main__':
    unittest.main()