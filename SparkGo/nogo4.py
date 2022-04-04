#!/usr/bin/python3
# /usr/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil, BLACK
from board import GoBoard
import numpy as np
from ucb import runUcb
import pattern
import signal
import os, psutil
import game_tree

#################################################
'''
This is a uniform random NoGo player served as the starter code
for your (possibly) stronger player. Good luck!
'''
class NoGo:
    def __init__(self, board):
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
        self.board = board
        self.game_tree = game_tree.GameTree(self.board)
            
        
    def get_move(self, board, color):
        """
        Run simulations for a given move.
        """
        # memory limit 1GB
        process = psutil.Process(os.getpid())
        while process.memory_info().rss < 1e9:
            try:
                signal.alarm(self.timelimit)
                self.game_tree.mc_rave()
                signal.alarm(0)
                break
                
            except Exception as e:
                # exceed 30 sec, it will be killed
                break
        return self.game_tree.get_best()
        
        

        
def run():
    """
    start the gtp connection and wait for commands.
    """
    board = GoBoard(7)
    con = GtpConnection(NoGo(board), board)
    con.start_connection()

if __name__ == "__main__":
    run()
