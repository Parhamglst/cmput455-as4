#!/usr/bin/python3
# /usr/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil, PASS
from board import GoBoard
import numpy as np
from simulation import select_best_move
from ucb import runUcb
import pattern
#################################################
'''
This is a uniform random NoGo player served as the starter code
for your (possibly) stronger player. Good luck!
'''
class NoGo:
    def __init__(self):
        """
        NoGo player that selects moves randomly from the set of legal moves.

        Parameters
        ----------
        name : str
            name of the player (used by the GTP interface).
        version : float
            version number (used by the GTP interface).
        """

        self.name = "NoGo4"
        self.version = 1.0
        self.sim = 10
        self.limit = 100
        self.random_simulation = False
        self.weights = get_weights()

    # def get_move(self, board:GoBoard, color:int):
    #     """
    #     Select a random move.
    #     """
    #     move = GoBoardUtil.generate_random_move(board, color)
    #     return move
    
    def simulate(self, board, move, toplay):
        """
        Run a simulated game for a given move.
        """
        cboard = board.copy()
        cboard.play_move(move, toplay)
        opp = GoBoardUtil.opponent(toplay)
        return self.playGame(cboard, opp)

    def simulateMove(self, board, move, toplay):
        """
        Run simulations for a given move.
        """
        wins = 0
        for _ in range(self.sim):
            result = self.simulate(board, move, toplay)
            if result == toplay:
                wins += 1
        return wins

    def get_move(self, board, color):
        """
          Run one-ply MC simulations to get a move to play.
          """
        cboard = board.copy()
        emptyPoints = board.get_empty_points()
        moves = []
        for p in emptyPoints:
            if board.is_legal(p, color):
                moves.append(p)
        if not moves:
            return None
       
        # use_ucb    
        C = 0.4  # sqrt(2) is safe, this is more aggressive
        best, stats = runUcb(self, cboard, C, moves, color)
        for i in range(len(stats)):
            stats[i] = stats[i][0] / (stats[i][0]+stats[i][1])
        return best
        
        
    def get_winrates(self, board, color):
        """
          Run one-ply MC simulations to get the winrate of the legal moves
          """
        cboard = board.copy()
        emptyPoints = board.get_empty_points()
        moves = []
        for p in emptyPoints:
            if board.is_legal(p, color):
                moves.append(p)
        if not moves:
            return None

        # use_ucb 
        weights = np.array([])
        for m in moves:
            weights = np.append(weights, pattern.lookup(cboard, m, self.weights))

        weights = np.array(weights) / sum(weights)
        return moves, weights


    def playGame(self, board, color):
        """
        Run a simulation game.
        """

        for _ in range(self.limit):

            color = board.current_player

            move = pattern.generated_move(board, color, self.weights)

            board.play_move(move, color)

        return GoBoardUtil.opponent(color)


def get_weights():
    weight_file = open("weights.txt", "r")
    weights = weight_file.read().split('\n')

    for i in range(len(weights)):

        if weights[i]:
            weights[i] = float(weights[i].split(' ')[1])

    return weights

        
def run():
    """
    start the gtp connection and wait for commands.
    """
    board = GoBoard(7)
    con = GtpConnection(NoGo(), board)
    con.start_connection()

if __name__ == "__main__":
    run()
