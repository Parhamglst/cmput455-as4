import numpy as np
import board_util
import pattern

K = 20

class GameTree:
    def __init__(self, board) -> None:
        self.root = GoNode(board)
        self.best_move = None
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
        legal_moves = board_util.GoBoardUtil.generate_legal_moves(board_copy, board_copy.color)
        
        while (len(legal_moves) > 0):
            move = pattern.generated_move(board_copy, board_copy.color, self.weights)
            board_copy.play_move(move, board_copy.color)
            
            move_trajectory.append(move)
            
            legal_moves = board_util.GoBoardUtil.generate_legal_moves(board_copy, board_copy.color)
            
        return wl, move_trajectory
    
    def _uct(self):
        """Run UCT to find the best leaf node to simulate on

        Returns:
            np.Array: trajectory of (action, state) pairs leading to the leaf node with the final state having None as action
        """
        tree_trajectory = [(None, self.root)]
        
        current = self.root
        sim_child, expanded = current.max_child() # sim_child = (move leading to child node, child node)
        tree_trajectory.append(sim_child)
        while not expanded: # TODO:Change to nonterminal
            current = sim_child[1]
            sim_child, expanded = current.max_child() # might have issue
            tree_trajectory.append(sim_child)
        
        # The tree trajectory is an array of (action, state) tuples
        # The first tuple which is the root node has None as action
        return tree_trajectory
    
    def mc_rave(self):
        tree_trajectory = self._uct()
        leaf = tree_trajectory[-1][1] # Last state
        wl, policy_trajectory = self._simulate(leaf)
        
        self._update_values(wl, tree_trajectory, policy_trajectory) # Update the ENTIRE tree (q values, AMAF scores and MCTS values)
        # TODO:update best move
    
    def _update_values(self, wl, tree_trajectory, policy_trajectory):
        for node in tree_trajectory:
            pass
            #TODO: Finish this
    
    def update_root(self, move):
        pass   
    
    def get_best(self):
        return self.best_move
        
    
class GoNode:
    def __init__(self, board) -> None:
        self.board = board
        self.children = [] # Expanded children nodes (action, node) tuples
        self.legal_moves = board_util.GoBoardUtil.generate_legal_moves(board, board.current_player) # All possible children nodes, unexpanded
        
        #############################################
        self.mcts_wins = 0
        self.number_of_simulations = 0
        self.mcts_val = np.Infinity
        
        self.amaf_wins = 0
        self.amaf_encounters = 0
        self.amaf_score = 0 
        
        self.q = self.mcts_val # change to dict
    
    def getChildren(self):
        return self.children
    
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
        
        alpha = max(0, (K - self.number_of_simulations)/self.number_of_simulations)
        self.q = alpha * self.amaf_score + (1 - alpha) * self.mcts_val
            
    def max_child(self):
        """returns the child to be traversed through
        If all children expanded: selects the biggest q value
        If there exists a child that hasn't been expanded: expands the child by adding it to self.children and returns the child node

        Returns:
            GoNode: node to be simulated on
            bool: True if we expanded a child, False if we just returned an already exxpanded child
        """
        if len(self.children) == len(self.legal_moves):
            return max(self.children, lambda k: self.children[k][1].q), False
        else:
            moves = set(self.legal_moves)
            for child in self.children:
                moves.remove(child[0])
            self._expand(moves[0])
            return self.children[-1], True
        
    def _expand(self, move):
        """adds an unexpanded child node to self.children according to move

        Args:
            move (str): move that leads to the child state
        """
        board = self.board.copy()
        opp_color = board_util.GoBoardUtil.opponent(self.board.current_player)
        board.play_move(move, opp_color)
        self.children.append((move, GoNode(board, opp_color)))
        