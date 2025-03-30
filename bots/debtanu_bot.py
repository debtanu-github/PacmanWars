# --- START OF FILE debtanu_bot.py ---

import random
from collections import deque
import sys
import math # Needed for distance calculation

# --- Attempt to import Bot and constants ---
try:
    from bots.bot import Bot
    from constants import *
except ImportError as e:
     print(f"Import Warning/Error: {e}. Attempting relative import.", file=sys.stderr)
     try: from constants import *
     except ImportError:
          print("FATAL: Could not import constants.", file=sys.stderr)
          # Define fallback constants - THIS IS NOT IDEAL
          print("Defining fallback constants - PLEASE FIX IMPORTS", file=sys.stderr)
          MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, MOVE_HALT = 0, 1, 2, 3, 4
          MOVEMENTS = {MOVE_UP: (-1, 0), MOVE_DOWN: (1, 0), MOVE_LEFT: (0, -1), MOVE_RIGHT: (0, 1), MOVE_HALT: (0, 0)}
          WALKABLE_CELL, FOOD_CELL, MOUNTAIN_CELL, OUT_OF_BOUNDS_CELL, UNKNOWN_CELL = 'G', 'F', 'O', 'R', 'U'
     try: from bot import Bot
     except ImportError:
         print("FATAL: Could not import base Bot class.", file=sys.stderr)
         sys.exit(1)


# --- Constants for DebtanuBot ---
HISTORY_LENGTH = 8
STUCK_THRESHOLD = 4
DEFAULT_BFS_DEPTH = 15
ESCAPE_BFS_DEPTH = 5
HUNT_SCORE_DIFFERENCE = 5
LONG_TERM_STUCK_THRESHOLD = 10
TOTAL_GAME_MOVES = 1000 # NEW: Total moves allowed in the game
EARLY_GAME_PERCENTAGE = 0.10 # NEW: Percentage defining the early game
EARLY_GAME_TURN_LIMIT = int(TOTAL_GAME_MOVES * EARLY_GAME_PERCENTAGE) # NEW: Turn threshold

# --- DEBUGGING FLAG ---
DEBUG_MODE = False # <<<<<<< SET TO True FOR TESTING, False FOR COMPETITION >>>>>>>

# --- Opposite Move Mapping ---
OPPOSITE_MOVE = {
    MOVE_UP: MOVE_DOWN, MOVE_DOWN: MOVE_UP,
    MOVE_LEFT: MOVE_RIGHT, MOVE_RIGHT: MOVE_LEFT,
    MOVE_HALT: None
}

def debug_print(*args, **kwargs):
    """Helper function to print only if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(*args, **kwargs, file=sys.stderr, flush=True)

# ===============================================
class DebtanuBot(Bot):
# ===============================================

    # --- __init__ METHOD ---
    def __init__(self, id: int, start_x: int, start_y: int, minimap: list, map_length: int, map_breadth: int):
        super().__init__(id, start_x, start_y, minimap, map_length, map_breadth)
        self.map_length = map_length
        self.map_breadth = map_breadth
        self.position_history = deque(maxlen=HISTORY_LENGTH)
        self.last_move_decision = "init"
        self.stuck_turns = 0
        self.last_move_action = None
        self.turn_counter = 0 # NEW: Initialize turn counter
        debug_print(f"Bot {self.id} initialized at ({start_x}, {start_y}). Early game limit: {EARLY_GAME_TURN_LIMIT} turns.")
        try:
             debug_print(f"  Map Size stored in bot: ({self.map_length}, {self.map_breadth})")
        except AttributeError:
             debug_print(f"  ERROR: Failed to store map_length/map_breadth in __init__!")
    # --- END __init__ METHOD ---

    # --- Core Move Logic ---
    def move(self, current_x: int, current_y: int, minimap: list, bot_food: dict) -> int:
        # --- Increment Turn Counter ---
        self.turn_counter += 1

        # --- Update State ---
        try: self.update_state(current_x, current_y, minimap, bot_food)
        except Exception as e:
            debug_print(f"!!!!!!!! Bot {self.id} Turn {self.turn_counter}: ERROR during self.update_state !!!!!!!! {e}")
            return MOVE_HALT

        # --- Add position history ---
        try: self.position_history.append((self.x, self.y))
        except AttributeError:
             debug_print(f"Bot {self.id} Turn {self.turn_counter}: ERROR - Bot state missing after update. Cannot append history.")
             return MOVE_HALT

        # --- (Optional Debug Map Printing) ---
        if DEBUG_MODE: self._print_debug_map_view() # Now includes turn counter

        # --- Check if stuck and update counter ---
        is_currently_stuck = self._is_stuck()
        if is_currently_stuck: self.stuck_turns += 1
        else: self.stuck_turns = 0

        # --- Determine Game Phase ---
        is_early_game = self.turn_counter <= EARLY_GAME_TURN_LIMIT
        if DEBUG_MODE:
            phase = "EARLY GAME" if is_early_game else "MID/LATE GAME"
            debug_print(f"Bot {self.id} Turn {self.turn_counter}: Phase = {phase}")

        # --- Decision Logic ---
        final_move = MOVE_HALT # Default action

        # 1. Escape Threats (Always highest priority)
        escape_move = self._find_escape_move()
        if escape_move is not None:
            self.last_move_decision = "escape"; self.stuck_turns = 0
            final_move = escape_move
        else:
            # --- Phase-Dependent Logic ---
            if is_early_game:
                # Early Game: Prioritize Food, Skip Hunt
                debug_print("  (Early Game Logic: Food > Skip Hunt > Patrol > Explore > Random)")
                # 2. Collect Food (Priority 2 in Early Game)
                food_move = self._find_food_move()
                if food_move is not None:
                    self.last_move_decision = "food_early"; self.stuck_turns = 0
                    final_move = food_move
                else:
                    # 3. Hunt Weaker Bots (SKIPPED in Early Game)
                    debug_print("  (Skipping hunt check in early game)")
                    # 4. Perimeter Patrol
                    perimeter_move = self._get_perimeter_patrol_move()
                    if perimeter_move is not None:
                        self.last_move_decision = "perimeter_early"
                        final_move = perimeter_move
                    else:
                        # 5. Avoid Looping / Explore
                        if is_currently_stuck:
                            explore_move = self._get_exploration_move(self.stuck_turns >= LONG_TERM_STUCK_THRESHOLD)
                            if explore_move is not None:
                                self.last_move_decision = "explore_early"
                                final_move = explore_move
                            else: # Fallback if explore fails
                                self.last_move_decision = "random_fallback_early_stuck"
                                final_move = self._get_random_safe_move()
                        else:
                            # 6. Fallback: Random Safe Move
                            self.last_move_decision = "random_fallback_early"
                            final_move = self._get_random_safe_move()
            else:
                # Mid/Late Game: Normal Priority (Hunt > Food)
                debug_print("  (Mid/Late Game Logic: Hunt > Food > Patrol > Explore > Random)")
                # 2. Hunt Weaker Bots (Priority 2 in Mid/Late Game)
                hunt_move = self._find_hunt_move()
                if hunt_move is not None:
                    self.last_move_decision = "hunt"; self.stuck_turns = 0
                    final_move = hunt_move
                else:
                    # 3. Collect Food (Priority 3 in Mid/Late Game)
                    food_move = self._find_food_move()
                    if food_move is not None:
                        self.last_move_decision = "food"; self.stuck_turns = 0
                        final_move = food_move
                    else:
                        # 4. Perimeter Patrol
                        perimeter_move = self._get_perimeter_patrol_move()
                        if perimeter_move is not None:
                            self.last_move_decision = "perimeter"
                            final_move = perimeter_move
                        else:
                            # 5. Avoid Looping / Explore
                            if is_currently_stuck:
                                explore_move = self._get_exploration_move(self.stuck_turns >= LONG_TERM_STUCK_THRESHOLD)
                                if explore_move is not None:
                                    self.last_move_decision = "explore_stuck" # Decision name reflects mid/late game context
                                    final_move = explore_move
                                else: # Fallback if explore fails
                                    self.last_move_decision = "random_fallback_stuck"
                                    final_move = self._get_random_safe_move()
                            else:
                                # 6. Fallback: Random Safe Move
                                self.last_move_decision = "random_fallback"
                                final_move = self._get_random_safe_move()

        # --- Log final decision ---
        pos_str = f"({getattr(self, 'x', '?')},{getattr(self, 'y', '?')})"
        debug_print(f"Bot {self.id} Turn {self.turn_counter} at {pos_str}: डिसीजन='{self.last_move_decision}', चाल={final_move}")

        # --- Store the action taken for the next turn ---
        self.last_move_action = final_move
        return final_move

    # --- Helper Methods ---

    def _print_debug_map_view(self):
        """Prints the map view around the bot if DEBUG_MODE is True."""
        debug_print(f"\n--- Bot {self.id} Turn {self.turn_counter} ---") # Added turn counter here
        try:
            pos_str=f"({self.x},{self.y})" if hasattr(self,'x') and hasattr(self,'y') else "(?,?)"
            food_str=self.bot_food.get(self.id,0) if hasattr(self,'bot_food') else "?"
            map_size_str=f"({self.map_length},{self.map_breadth})" if hasattr(self,'map_length') and hasattr(self,'map_breadth') else "(?,?)"
            stuck_info = f"StuckTurns:{self.stuck_turns}" if hasattr(self, 'stuck_turns') else ""
            last_act = f"LastAct:{self.last_move_action}" if hasattr(self, 'last_move_action') and self.last_move_action is not None else "LastAct:None"
            debug_print(f"Bot {self.id} state: Pos={pos_str}, Food={food_str}, Map={map_size_str} {stuck_info} {last_act}")
            if hasattr(self,'map') and hasattr(self,'x') and hasattr(self,'y'):
                debug_print("Map around bot (self.map):")
                view_radius=2
                for i in range(max(0,self.x-view_radius),min(self.map_length,self.x+view_radius+1)):
                     row_str=f"{i:2d}: "
                     for j in range(max(0,self.y-view_radius),min(self.map_breadth,self.y+view_radius+1)):
                         if 0<=i<self.map_length and 0<=j<self.map_breadth:
                             cell_val=self.map[i][j];prefix=">" if i==self.x and j==self.y else " ";suffix="<" if i==self.x and j==self.y else " "
                             row_str+=f"{prefix}{str(cell_val):<3}{suffix}"
                         else: row_str+="  OOB "
                     debug_print(row_str)
            else: debug_print("  (Cannot print map view - state missing)")
        except Exception as e: debug_print(f"  Error printing debug map view: {e}")
        debug_print("-" * 20)

    # --- (Keep all other helper methods unchanged: _get_distance_sq, _get_centroid, _get_exploration_move, _get_random_safe_move, _is_safe_cell, _parse_bot_id, _find_escape_move, _find_hunt_move, _find_food_move, _get_perimeter_patrol_move, _is_stuck, _bfs, _in_bounds) ---
    # Make sure the _find_hunt_move uses the HUNT_SCORE_DIFFERENCE constant correctly.
    # Make sure _get_exploration_move and _get_random_safe_move use self.last_move_action correctly.

    def _get_distance_sq(self, x1, y1, x2, y2):
        return (x1 - x2)**2 + (y1 - y2)**2

    def _get_centroid(self, positions):
        if not positions: return None
        sum_x, sum_y, count = 0, 0, 0
        for pos in positions:
            try:
                x, y = pos
                if isinstance(x, (int, float)) and isinstance(y, (int, float)): sum_x += x; sum_y += y; count += 1
                else: debug_print(f"  Centroid Warning: Skipping invalid pos data {pos}")
            except (TypeError, ValueError): debug_print(f"  Centroid Warning: Skipping invalid pos data {pos}")
        if count == 0: return None
        return sum_x / count, sum_y / count

    def _get_exploration_move(self, is_long_term_stuck: bool) -> int | None:
        safe_moves_data = []
        try:
            current_x, current_y = self.x, self.y
            for direction, (dx, dy) in MOVEMENTS.items():
                if direction == MOVE_HALT: continue
                nx, ny = current_x + dx, current_y + dy
                if self._is_safe_cell(nx, ny): safe_moves_data.append((direction, nx, ny))
        except AttributeError: debug_print("  _get_exploration_move: ERROR - state missing."); return None
        if not safe_moves_data: debug_print(f"  Exploration failed: No safe moves from ({current_x},{current_y})."); return None

        if is_long_term_stuck and len(self.position_history) > 0:
            debug_print("  Attempting enhanced exploration (away from centroid)...")
            centroid = self._get_centroid(self.position_history)
            if centroid:
                centroid_x, centroid_y = centroid; debug_print(f"  Centroid: ({centroid_x:.2f}, {centroid_y:.2f})")
                opposite_last = OPPOSITE_MOVE.get(self.last_move_action); preferred = []; opposite_option = None
                max_dist_sq = -1; best_preferred = -1; max_dist_sq_opp = -1
                random.shuffle(safe_moves_data)
                for direction, nx, ny in safe_moves_data:
                    dist_sq = self._get_distance_sq(nx, ny, centroid_x, centroid_y)
                    if direction == opposite_last:
                        opposite_option = direction
                        if dist_sq > max_dist_sq_opp: max_dist_sq_opp = dist_sq
                    else:
                        preferred.append(direction)
                        if dist_sq > max_dist_sq: max_dist_sq = dist_sq; best_preferred = direction
                if best_preferred != -1: debug_print(f"  Enhanced choice: Move {best_preferred} (preferred, max dist)"); return best_preferred
                elif opposite_option is not None: debug_print(f"  Enhanced choice: Move {opposite_option} (only option is opposite)"); return opposite_option
                else: debug_print("  Enhanced exploration failed selection.")
            else: debug_print("  Enhanced exploration failed: No centroid.")

        debug_print("  Attempting normal exploration (prefer new cells, avoid reversal)...")
        preferred_new = []; preferred_old = []; opposite_new = None; opposite_old = None
        opposite_last = OPPOSITE_MOVE.get(self.last_move_action)
        try: recent = set(self.position_history)
        except TypeError: debug_print("  Normal explore: TypeError history set."); recent = set()
        for direction, nx, ny in safe_moves_data:
            is_new = (nx, ny) not in recent; is_opposite = (direction == opposite_last)
            if is_new:
                if not is_opposite: preferred_new.append(direction)
                else: opposite_new = direction
            else:
                if not is_opposite: preferred_old.append(direction)
                else: opposite_old = direction
        if preferred_new: chosen = random.choice(preferred_new); debug_print(f"  Normal choice: Move {chosen} (preferred, new)"); return chosen
        elif preferred_old: chosen = random.choice(preferred_old); debug_print(f"  Normal choice: Move {chosen} (preferred, old)"); return chosen
        elif opposite_new is not None: debug_print(f"  Normal choice: Move {opposite_new} (opposite, new)"); return opposite_new
        elif opposite_old is not None: debug_print(f"  Normal choice: Move {opposite_old} (opposite, old)"); return opposite_old
        debug_print("  Exploration fallback: No suitable move found."); return None

    def _get_random_safe_move(self) -> int:
        safe_moves = []
        try: current_x, current_y = self.x, self.y
        except AttributeError: debug_print("  _get_random_safe_move: ERROR - state missing."); return MOVE_HALT
        for direction, (dx, dy) in MOVEMENTS.items():
            if direction == MOVE_HALT: continue
            nx, ny = current_x + dx, current_y + dy
            if self._is_safe_cell(nx, ny): safe_moves.append(direction)
        if not safe_moves: debug_print(f"Bot {self.id} at ({current_x}, {current_y}): No safe fallback moves. Halting."); return MOVE_HALT
        opposite_last = OPPOSITE_MOVE.get(self.last_move_action)
        preferred = [m for m in safe_moves if m != opposite_last]
        if preferred: return random.choice(preferred)
        elif safe_moves: return random.choice(safe_moves)
        else: debug_print(f"Bot {self.id} at ({current_x}, {current_y}): Logic error random move. Halting."); return MOVE_HALT

    def _is_safe_cell(self, x: int, y: int) -> bool:
        if not self._in_bounds(x, y): return False
        try: return self.map[x][y] in [WALKABLE_CELL, FOOD_CELL]
        except (IndexError, AttributeError, TypeError) as e: debug_print(f"  _is_safe_cell: Error ({x},{y}): {e}"); return False

    def _parse_bot_id(self, cell_value) -> int | None:
        if cell_value in [WALKABLE_CELL, FOOD_CELL, MOUNTAIN_CELL, OUT_OF_BOUNDS_CELL, UNKNOWN_CELL]: return None
        try: return int(cell_value)
        except (ValueError, TypeError): return None

    def _find_escape_move(self) -> int | None:
        try: my_food = self.bot_food.get(self.id, 1); cx, cy = self.x, self.y
        except AttributeError: debug_print("  _find_escape_move: ERROR - state missing."); return None
        threat_dirs = []; threats = []
        for d, (dx, dy) in MOVEMENTS.items():
            if d == MOVE_HALT: continue
            nx, ny = cx + dx, cy + dy
            if not self._in_bounds(nx, ny): continue
            try: cell = self.map[nx][ny]
            except (IndexError, AttributeError, TypeError) as e: debug_print(f"  _find_escape_move: Error map access ({nx},{ny}): {e}"); continue
            o_id = self._parse_bot_id(cell)
            if o_id is not None and o_id != self.id:
                o_food = self.bot_food.get(o_id, 1)
                if o_food >= my_food: threat_dirs.append(d); threats.append((nx,ny))
        if not threat_dirs: return None
        moves = {}; safe_away = []; opposite = {MOVE_UP: MOVE_DOWN, MOVE_DOWN: MOVE_UP, MOVE_LEFT: MOVE_RIGHT, MOVE_RIGHT: MOVE_LEFT}
        potential = list(MOVEMENTS.keys()); potential.remove(MOVE_HALT)
        for d, (dx, dy) in MOVEMENTS.items():
             if d == MOVE_HALT: continue; nx, ny = cx + dx, cy + dy; moves[d] = self._is_safe_cell(nx, ny)
        for t_dir in threat_dirs:
            if t_dir in potential: potential.remove(t_dir)
            esc_dir = opposite.get(t_dir)
            if esc_dir and moves.get(esc_dir, False):
                 ex, ey = cx + MOVEMENTS[esc_dir][0], cy + MOVEMENTS[esc_dir][1]
                 try:
                     if self._in_bounds(ex, ey) and self.map[ex][ey] == FOOD_CELL: return esc_dir # Best
                 except (IndexError, AttributeError, TypeError) as e: debug_print(f"  _find_escape_move: Error food check ({ex},{ey}): {e}")
                 safe_away.append(esc_dir)
        if safe_away: return random.choice(list(set(safe_away)))
        other_safe = [d for d in potential if moves.get(d, False)]
        if other_safe:
             for m in other_safe:
                 ex, ey = cx + MOVEMENTS[m][0], cy + MOVEMENTS[m][1]
                 try:
                     if self._in_bounds(ex, ey) and self.map[ex][ey] == FOOD_CELL: return m # Prefer food
                 except (IndexError, AttributeError, TypeError) as e: debug_print(f"  _find_escape_move: Error food check ({ex},{ey}): {e}")
             return random.choice(other_safe)
        debug_print(f"  No safe adjacent escape. Trying BFS...");
        def iwf(x,y,c): return self._in_bounds(x,y) and c in [WALKABLE_CELL, FOOD_CELL]
        def ist(x,y,c): return self._in_bounds(x,y) and c in [WALKABLE_CELL, FOOD_CELL]
        bfs_move = self._bfs(is_target_fn=ist, is_walkable_fn=iwf, max_depth=ESCAPE_BFS_DEPTH, bfs_purpose="escape_bfs")
        if bfs_move is not None: return bfs_move
        debug_print(f"Bot {self.id} at ({cx}, {cy}): Trapped! Halting."); return MOVE_HALT

    def _find_hunt_move(self) -> int | None:
        try: my_food = self.bot_food.get(self.id, 1)
        except AttributeError: debug_print("  _find_hunt_move: ERROR - state missing."); return None
        def is_target(x, y, c):
            if not self._in_bounds(x,y): return False
            o_id = self._parse_bot_id(c)
            if o_id is not None and o_id != self.id: return my_food > self.bot_food.get(o_id, 1) + HUNT_SCORE_DIFFERENCE
            return False
        def is_walkable(x, y, c):
            if not self._in_bounds(x,y): return False
            if c in [WALKABLE_CELL, FOOD_CELL]: return True
            o_id = self._parse_bot_id(c)
            if o_id is not None and o_id != self.id: return my_food > self.bot_food.get(o_id, 1) + HUNT_SCORE_DIFFERENCE
            return False
        return self._bfs(is_target_fn=is_target, is_walkable_fn=is_walkable, max_depth=DEFAULT_BFS_DEPTH, bfs_purpose="hunt")

    def _find_food_move(self) -> int | None:
        def is_target(x,y,c): return self._in_bounds(x,y) and c == FOOD_CELL
        def is_walkable(x,y,c): return self._in_bounds(x,y) and c in [WALKABLE_CELL, FOOD_CELL]
        return self._bfs(is_target_fn=is_target, is_walkable_fn=is_walkable, max_depth=DEFAULT_BFS_DEPTH, bfs_purpose="food")

    def _get_perimeter_patrol_move(self) -> int | None:
        try:
            x, y = self.x, self.y
            if not isinstance(getattr(self, 'map_length', None), int) or not isinstance(getattr(self, 'map_breadth', None), int) or self.map_length <= 0 or self.map_breadth <= 0: return None
            max_x, max_y = self.map_length - 1, self.map_breadth - 1
        except AttributeError: debug_print("  Perimeter Patrol: ERROR - state missing."); return None
        primary_move = None; on_top = (x == 0); on_bottom = (x == max_x); on_left = (y == 0); on_right = (y == max_y)
        if on_top and on_left: primary_move = MOVE_RIGHT
        elif on_top and on_right: primary_move = MOVE_DOWN
        elif on_bottom and on_right: primary_move = MOVE_LEFT
        elif on_bottom and on_left: primary_move = MOVE_UP
        elif on_top: primary_move = MOVE_RIGHT
        elif on_right: primary_move = MOVE_DOWN
        elif on_bottom: primary_move = MOVE_LEFT
        elif on_left: primary_move = MOVE_UP
        else: return None
        if primary_move is not None:
            move_delta = MOVEMENTS.get(primary_move)
            if move_delta:
                nx, ny = x + move_delta[0], y + move_delta[1]
                # --- Penalize Reversal during Patrol ---
                opposite_last = OPPOSITE_MOVE.get(self.last_move_action)
                if primary_move == opposite_last:
                     debug_print(f"  Perimeter Patrol: Primary move {primary_move} is opposite of last move {self.last_move_action}. Skipping.")
                     return None # Avoid immediate reversal even if safe
                # --- End Reversal Penalty ---
                if self._is_safe_cell(nx, ny): return primary_move
                else: debug_print(f"  Perimeter Patrol: Primary move {primary_move} blocked."); return None
            else: return None
        else: return None

    def _is_stuck(self) -> bool:
        if len(self.position_history) < HISTORY_LENGTH: return False
        try: return len(set(self.position_history)) <= STUCK_THRESHOLD
        except TypeError: debug_print("  _is_stuck: TypeError."); return False

    def _bfs(self, is_target_fn, is_walkable_fn, max_depth: int, bfs_purpose: str = "general") -> int | None:
        try: start_x, start_y = self.x, self.y
        except AttributeError: debug_print(f"  BFS ({bfs_purpose}): ERROR - state missing."); return None
        queue = deque([(start_x, start_y, None, 0)]); visited = set([(start_x, start_y)]); found_target_move = None
        while queue:
            cx, cy, first_move, depth = queue.popleft()
            try:
                if not self._in_bounds(cx, cy): continue
                current_cell_value = self.map[cx][cy]
                if depth > 0 and is_target_fn(cx, cy, current_cell_value):
                    debug_print(f"  BFS ({bfs_purpose}): Found target at ({cx},{cy}) via move {first_move} at depth {depth}")
                    found_target_move = first_move; break
            except (IndexError, AttributeError, TypeError) as e: debug_print(f"  BFS ({bfs_purpose}): Error map access ({cx},{cy}): {e}"); continue
            if depth >= max_depth: continue
            shuffled_directions = list(MOVEMENTS.items()); random.shuffle(shuffled_directions)
            for direction, (dx, dy) in shuffled_directions:
                if direction == MOVE_HALT: continue
                nx, ny = cx + dx, cy + dy
                if not self._in_bounds(nx, ny): continue
                try:
                    if (nx, ny) not in visited:
                        neighbor_cell_value = self.map[nx][ny]
                        if is_walkable_fn(nx, ny, neighbor_cell_value):
                            visited.add((nx, ny)); next_first_move = first_move if first_move is not None else direction
                            queue.append((nx, ny, next_first_move, depth + 1))
                except (IndexError, AttributeError, TypeError) as e: debug_print(f"  BFS ({bfs_purpose}): Error neighbor access ({nx},{ny}): {e}"); continue
        return found_target_move

    def _in_bounds(self, x: int, y: int) -> bool:
        try:
            if not isinstance(self.map_length, int) or not isinstance(self.map_breadth, int) or self.map_length <= 0 or self.map_breadth <= 0: return False
            return 0 <= x < self.map_length and 0 <= y < self.map_breadth
        except AttributeError: debug_print("  _in_bounds check failed: map dimensions missing."); return False

# --- END OF FILE debtanu_bot.py ---