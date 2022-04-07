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
            s = S[t]
            if t < len(A):
                s.mcts_vals[A[t]][1] += 1
                if wl == 1 and s.board.current_player == S[0].board.current_player:
                    s.mcts_vals[A[t]][0] += 1
                elif wl == 0 and s.board.current_player != S[0].board.current_player:
                    s.mcts_vals[A[t]][0] -= 1
            for u in range(t, len(A), 2):
                s.amaf_vals[A[u]][1] += 1 # N++
                if wl == 1 and s.board.current_player == S[0].board.current_player:
                    s.amaf_vals[A[u]][0] += 1 # Q++
                elif wl == 0 and s.board.current_player != S[0].board.current_player:
                    s.amaf_vals[A[u]][0] -= 1