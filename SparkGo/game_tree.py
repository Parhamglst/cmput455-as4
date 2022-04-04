import numpy as np
import board_util
import pattern

K = 20


class GameTree:
    def __init__(self, board) -> None:
        self.root = GoNode(board)
        self.weights = pattern.get_weights()

    def _simulate(self, node):
        """performs a simulation on the given node

        Args:
            node (GoNode): node that the simulation is being performed on

        Returns:
            int: 1 if the trajectory won for the node's current player
            np.Array: trajectory that the default policy traversed
        """
        wl = 0
        move_trajectory = []
        board_copy = node.board.copy()
        legal_moves = board_util.GoBoardUtil.generate_legal_moves(
            board_copy, board_copy.color)

        while (len(legal_moves) > 0):
            move = pattern.generated_move(
                board_copy, board_copy.color, self.weights)
            board_copy.play_move(move, board_copy.color)

            move_trajectory.append(move)

            legal_moves = board_util.GoBoardUtil.generate_legal_moves(
                board_copy, board_copy.color)

        return wl, move_trajectory

    def _uct(self):
        """Run UCT to find the best leaf node to simulate on

        Returns:
            np.Array: trajectory of (action, state) pairs leading to the leaf node with the final state having None as action
        """
        tree_trajectory = []

        current = self.root
        sim_child = current.max_child()  # type(sim_child) = Edge
        tree_trajectory.append(sim_child)
        while board_util.GoBoardUtil.generate_legal_moves(sim_child.node.board, sim_child.node.color):
            current = sim_child.node
            sim_child = current.max_child()  # might have issue
            tree_trajectory.append(sim_child)

        # The tree trajectory is an array of (action, state) tuples
        # The first tuple which is the root node has None as action
        return tree_trajectory

    def mc_rave(self):
        tree_trajectory = self._uct()
        leaf = tree_trajectory[-1][1]  # Last state
        wl, policy_trajectory = self._simulate(leaf)

        # Update the ENTIRE tree (q values, AMAF scores and MCTS values)
        self._update_values(wl, tree_trajectory, policy_trajectory)
        # TODO:update best move

    def _update_values(self, wl, tree_trajectory, move_trajectory):
        # Back propogation
        for edge in tree_trajectory:
            edge.update_wl_sim(wl)

        # RAVE
        bfs = [self.root]
        while bfs:
            cur = bfs.pop(0)
            for edge in cur.children:
                if edge.move in move_trajectory:
                    edge.update_wl_amaf(wl)
                bfs.append(edge.node)
            cur.update_best_move()

    def update_root(self, move):
        for edge in self.root.children:
            if edge.move == move:
                self.root = edge.node
                return
        board = self.root.board.copy()
        self.root = GoNode(board)


class GoNode:
    def __init__(self, board) -> None:
        self.board = board
        self.children = []  # Expanded children nodes of class Edge
        self.legal_moves = board_util.GoBoardUtil.generate_legal_moves(
            board, board.current_player)  # All possible children nodes, unexpanded
        self.best_move = None

    def getChildren(self):
        return self.children

    def max_child(self):
        """returns the child to be traversed through
        If all children expanded: selects the biggest q value
        If there exists a child that hasn't been expanded: expands the child by adding it to self.children and returns the child node

        Returns:
            GoNode: node to be simulated on
            bool: True if we expanded a child, False if we just returned an already exxpanded child
        """
        if len(self.children) == len(self.legal_moves):
            # self.update_best_move()
            return self.best_child
        else:
            moves = set(self.legal_moves)
            for child in self.children:
                moves.remove(child.move)
            self._expand(moves[0])
            return self.children[-1]

    def _expand(self, move):
        """adds an unexpanded child node to self.children according to move

        Args:
            move (str): move that leads to the child state
        """
        board = self.board.copy()
        opp_color = board_util.GoBoardUtil.opponent(self.board.current_player)
        board.play_move(move, opp_color)
        self.children.append((Edge(move), GoNode(board, opp_color)))

    def has_move(self, move):
        for child in self.children:
            if child[0].move == move:
                return True
        return False

    def update_best_move(self):
        if self.children:
            self.best_child = max(self.children, lambda k: self.children[k].q)

    def get_best(self):
        return self.best_move


class Edge:
    def __init__(self, move, node) -> None:
        self.move = move
        self.node = node

        self.mcts_wins = 0
        self.number_of_simulations = 0
        self.mcts_val = np.Infinity

        self.amaf_wins = 0
        self.amaf_encounters = 0
        self.amaf_score = 0

        self.q = self.mcts_val

    def update_wl_sim(self, wl):
        self.number_of_simulations += 1
        if wl == 1:
            self.mcts_wins += 1
        self._update_params()

    def update_wl_amaf(self, wl):
        self.amaf_encounters += 1
        if wl == 1:
            self.amaf_wins += 1
        self._update_params()

    def _update_params(self):
        self.mcts_val = self.mcts_wins/self.number_of_simulations
        self.amaf_score = self.amaf_wins/self.amaf_encounters

        alpha = max(0, (K - self.number_of_simulations) /
                    self.number_of_simulations)
        self.q = alpha * self.amaf_score + (1 - alpha) * self.mcts_val
