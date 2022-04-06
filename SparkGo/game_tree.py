import numpy as np
import board_util
import pattern

K = 15


class GameTree:
    def __init__(self, board) -> None:
        self.root = GoNode(board)
        self.weights = pattern.get_weights()
        self.color = 0
        

    def simDefault(self, node):
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

        while not self.gameOver(board_copy):
            move = self.defaultPolicy(board_copy)
            board_copy.play_move(move, board_copy.current_player)

            move_trajectory.append(move)
        
        if board_copy.current_player != self.root.board.current_player:
            wl = 1
        return wl, move_trajectory
    
    def defaultPolicy(self, board_copy):
        move = pattern.generated_move(
                board_copy, board_copy.current_player, self.weights)
        return move

    def _uct(self):
        """Run UCT to find the best leaf node to simulate on

        Returns:
            np.Array: trajectory of (action, state) pairs leading to the leaf node with the final state having None as action
        """
        tree_trajectory = [(None, self.root)]
        
        cur = self.root
        board_copy = cur.board.copy()
        while not self.gameOver(board_copy):
            move, node, expanded = cur.selectMove(self.root)
            tree_trajectory = tree_trajectory + [(move, node)]
            if expanded:
                return tree_trajectory
            board_copy.play_move(move, board_copy.current_player)
            cur = node
        return tree_trajectory
        
        # tree_trajectory = [Edge(None, self.root)]

        # current = self.root
        # sim_child, expanded = current.max_child()  # type(sim_child) = Edge
        # tree_trajectory.append(sim_child)
        # if expanded:
        #     return tree_trajectory
        # while board_util.GoBoardUtil.generate_legal_moves(sim_child.node.board, sim_child.node.board.current_player):
        #     current = sim_child.node
        #     sim_child, expanded = current.max_child()  # might have issue
        #     tree_trajectory.append(sim_child)
        #     if expanded:
        #         break
        # The tree trajectory is an array of (action, state) tuples
        # The first tuple which is the root node has None as action
        # return tree_trajectory

    def mc_rave(self, color):
        if self.color == 0:
            self.root.board.current_player = color
            self.color = color
        if self.root.board.current_player != color:
            raise(Exception)
        tree_trajectory = self._uct()
        leaf = tree_trajectory[-1][1]  # Last state
        wl, policy_trajectory = self.simDefault(leaf)

        # Update the ENTIRE tree (q values, AMAF scores and MCTS values)
        self._update_values(wl, tree_trajectory, policy_trajectory)
        return self.root.bestMove(self.root)

    def _update_values(self, wl, tree_trajectory, move_trajectory):
        # Back propogation
        S = []
        A = []
        for edge in tree_trajectory:
            S.append(edge[1])
            if edge[0]:
                A.append(edge[0])
        A = A + move_trajectory
        for t in range(len(S)):
            S[t].mcts_vals[A[t]][1] += 1
            if wl == 1:
                S[t].mcts_vals[A[t]][0] += 1
            s = S[t]
            for u in range(t, len(A), 2):
                s.amaf_vals[A[u]][1] += 1 # N++
                if wl == 1:
                    s.amaf_vals[A[u]][0] += 1 # Q++

                

    def update_root(self, move):
        for m in self.root.children.keys():
            if m == move:
                self.root = self.root.children[move]
                return
        board = self.root.board.copy()
        board.play_move(move, self.root.board.current_player)
        # board.current_player = board_util.GoBoardUtil.opponent(self.root.board.current_player)
        self.root = GoNode(board)
    
    def gameOver(self, board):
        legal_moves = board_util.GoBoardUtil.generate_legal_moves(board, board.current_player)
        if legal_moves:
            return False
        else:
            return True


class GoNode:
    def __init__(self, board) -> None:
        self.board = board
        self.children = {}  # {a: node}
        self.legal_moves = board_util.GoBoardUtil.generate_legal_moves(
            board, board.current_player)  # All possible children nodes, unexpanded
        
        self.amaf_vals = {} # dictionary
        for move in self.legal_moves:
            self.amaf_vals[move] = [0.5,0.5]    # (wins, encounters) 
        
        self.mcts_vals = {} # dictionary
        for move in self.legal_moves:
            self.mcts_vals[move] = [0.5,0.5]    # (wins, encounters) 

    def getChildren(self):
        return self.children

    def selectMove(self, root):
        """returns the child to be traversed through
        If all children expanded: selects the biggest q value
        If there exists a child that hasn't been expanded: expands the child by adding it to self.children and returns the child node

        Returns:
            GoNode: node to be simulated on
            bool: True if we expanded a child, False if we just returned an already expanded child
        """
        
        eval_actions = []
        for a in self.legal_moves:
            eval_actions.append(self.evaluate(a))
        eval_actions = enumerate(eval_actions)
        expanded = False

        if self.board.current_player == root.board.current_player:
            maxI = max(eval_actions, key=lambda k: k[1])[0]
            if self.legal_moves[maxI] not in self.children.keys():
                self._expand(self.legal_moves[maxI])
                expanded = True
            return self.legal_moves[maxI], self.children[self.legal_moves[maxI]], expanded
        else:
            minI = min(eval_actions, key=lambda k: k[1])[0]
            if self.legal_moves[minI] not in self.children.keys():
                self._expand(self.legal_moves[minI])
                expanded = True
            return self.legal_moves[minI], self.children[self.legal_moves[minI]], expanded
    
    def bestMove(self, root):
        eval_actions = []
        for a in self.legal_moves:
            eval_actions.append(self.evaluate(a))
        eval_actions = enumerate(eval_actions)

        if self.board.current_player == root.board.current_player:
            maxI = max(eval_actions, key=lambda k: k[1])[0]
            return self.legal_moves[maxI]
        else:
            minI = min(eval_actions, key=lambda k: k[1])[0]
            return self.legal_moves[minI]
                

    def _expand(self, move):
        """adds an unexpanded child node to self.children according to move

        Args:
            move (str): move that leads to the child state
        """
        board = self.board.copy()
        board.play_move(move, board.current_player)
        # opp_color = board_util.GoBoardUtil.opponent(board.current_player) # ???????????
        self.children[move] = GoNode(board)
    
    def evaluate(self, a):
        amaf_score = self.amaf_vals[a][0]/self.amaf_vals[a][1]
        mcts_score = self.mcts_vals[a][0]/self.mcts_vals[a][1]
        
        alpha = max(0, (K - self.mcts_vals[a][1]) / K)
        return alpha * amaf_score + (1 - alpha) * mcts_score
    
