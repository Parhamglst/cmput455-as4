from board_util import (
    GoBoardUtil,
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    PASS,
    MAXSIZE,
    coord_to_point,
)
import numpy as np
import random
import os

def lookup(board, point, weights):
    neigh = _eight_neighbours(board, point)

    # convert base 4 address to base 10
    base_ten = 0
    for n in range(len(neigh)):
        base_ten += neigh[n] * (4 ** (len(neigh) - n -1))

    # lookup corresponding pattern to base 10 address
    weight_point = weights[base_ten]

    return weight_point


def generated_move(board, color, weights):
    """
    for every legal move p:

     1. Scan for matching patterns,

     2. sum up the weights for all matching patterns, and;

     3. choose a legal move according to the probability distribution
        of each move's weight.
    """

    legal_moves = GoBoardUtil.generate_legal_moves(board, color)
    if not legal_moves:
        return None

    weights_moves = []
    for m in legal_moves:
        weights_moves.append([m, lookup(board, m, weights)])

    weights_sum = 0
    for i in weights_moves:
        weights_sum += i[1]
    for w in range(len(weights_moves)):
        weights_moves[w][1] /= weights_sum

    move = choose_move(weights_moves)

    return move


def choose_move(weights_moves):
    """
    returns a randomly generated move based on probability distribution
    """
    value = random.random()

    i = 0

    while value > 0:
        value -= weights_moves[i][1]
        i += 1

    return weights_moves[i - 1][0]


def _eight_neighbours(board, point):
    """
    returns list of values for each of the eight neighbours in order:
    bottom right to left and up
    """
    return [
        board.board[point - board.NS + 1],  # bottom right
        board.board[point - board.NS],  # bottom center
        board.board[point - board.NS - 1],  # bottom left
        
        board.board[point + 1],  # right
        board.board[point - 1],  # left
        
        board.board[point + board.NS + 1],  # top right
        board.board[point + board.NS],  # top center
        board.board[point + board.NS - 1],  # top left
    ]

def get_weights():
    weight_file = open("SparkGo/weights.txt", "r")
    weights = weight_file.read().split('\n')

    for i in range(len(weights)):

        if weights[i]:
            weights[i] = float(weights[i].split(' ')[1])

    return weights