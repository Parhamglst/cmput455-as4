import numpy as np
import board_util
import pattern

K = 15


class GameTree:
    def __init__(self, board) -> None:
        self.root = GoNode(board)
        self.weights = pattern.get_weights()
        self.color = 0

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
            board_copy, board_copy.current_player)

        while (len(legal_moves) > 0):
            move = pattern.generated_move(
                board_copy, board_copy.current_player, self.weights)
            board_copy.play_move(move, board_copy.current_player)

            move_trajectory.append(move)

            legal_moves = board_util.GoBoardUtil.generate_legal_moves(
                board_copy, board_copy.current_player)
        
        if board_copy.current_player != self.root.board.current_player:
            wl = 1
        return wl, move_trajectory

    def _uct(self):
        """Run UCT to find the best leaf node to simulate on

        Returns:
            np.Array: trajectory of (action, state) pairs leading to the leaf node with the final state having None as action
        """
        tree_trajectory = []

        current = self.root
        sim_child, expanded = current.max_child()  # type(sim_child) = Edge
        tree_trajectory.append(sim_child)
        if expanded:
            return tree_trajectory
        while board_util.GoBoardUtil.generate_legal_moves(sim_child.node.board, sim_child.node.board.current_player):
            current = sim_child.node
            sim_child, expanded = current.max_child()  # might have issue
            tree_trajectory.append(sim_child)
            if expanded:
                break
        # The tree trajectory is an array of (action, state) tuples
        # The first tuple which is the root node has None as action
        return tree_trajectory

    def mc_rave(self, color):
        if self.color == 0:
            self.root.board.current_player = color
            self.color = color
        if self.root.board.current_player != color:
            raise(Exception)
        tree_trajectory = self._uct()
        leaf = tree_trajectory[-1].node  # Last state
        wl, policy_trajectory = self._simulate(leaf)

        # Update the ENTIRE tree (q values, AMAF scores and MCTS values)
        self._update_values(wl, tree_trajectory, policy_trajectory)
        return

    def _update_values(self, wl, tree_trajectory, move_trajectory):
        # Back propogation
        for edge in tree_trajectory:
                edge.update_wl_sim(wl)

        # RAVE
        bfs = [self.root]
        while bfs:
            cur = bfs.pop(0)
            for edge in cur.children:
                if edge.move in move_trajectory and edge.node.board.current_player != self.root.board.current_player:
                    edge.update_wl_amaf(wl)
                bfs.append(edge.node)
            cur.update_best_move()

    def update_root(self, move):
        for edge in self.root.children:
            if edge.move == move:
                self.root = edge.node
                return
        board = self.root.board.copy()
        board.play_move(move, self.root.board.current_player)
        # board.current_player = board_util.GoBoardUtil.opponent(self.root.board.current_player)
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
            bool: True if we expanded a child, False if we just returned an already expanded child
        """
        if len(self.children) == len(self.legal_moves):
            # self.update_best_move()
            return self.best_move, False
        else:
            moves = list(self.legal_moves)
            for child in self.children:
                moves.remove(child.move)
            self._expand(np.random.choice(moves))
            return self.children[-1], True

    def _expand(self, move):
        """adds an unexpanded child node to self.children according to move

        Args:
            move (str): move that leads to the child state
        """
        board = self.board.copy()
        board.play_move(move, board.current_player)
        # opp_color = board_util.GoBoardUtil.opponent(board.current_player) # ???????????
        self.children.append(Edge(move, GoNode(board)))

    def has_move(self, move):
        for child in self.children:
            if child[0].move == move:
                return True
        return False

    def update_best_move(self):
        if self.children:
            self.best_move = max(self.children, key=lambda k: k.q)

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
        self.mcts_val = self.mcts_wins/self.number_of_simulations
        
        alpha = max(0, (K - self.number_of_simulations) / K)
        self.q = alpha * self.amaf_score + (1 - alpha) * self.mcts_val

    def update_wl_amaf(self, wl):
        self.amaf_encounters += 1
        if wl == 1:
            self.amaf_wins += 1
        self._update_params()

    def _update_params(self):
        self.amaf_score = self.amaf_wins/self.amaf_encounters

        alpha = max(0, (K - self.number_of_simulations) / K)
        self.q = alpha * self.amaf_score + (1 - alpha) * self.mcts_val
