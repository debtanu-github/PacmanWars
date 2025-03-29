import random
from collections import deque
from bots.bot import Bot
from constants import * # Make sure MOVEMENTS is defined here (e.g., {MOVE_UP: (-1, 0), ...})
import sys # For printing map view neatly

# --- Constants for MyStrategicBot ---
HISTORY_LENGTH = 8       # How many past positions to remember for loop detection
STUCK_THRESHOLD = 4      # If unique positions in history <= this, consider stuck
DEFAULT_BFS_DEPTH = 10   # Default search depth for BFS
ESCAPE_BFS_DEPTH = 5     # Shorter search depth when escaping threats

# --- DEBUGGING FLAG ---
# Set to True to enable detailed print statements, False to disable them
DEBUG_MODE = False # <<<<<<< SET TO FALSE TO REDUCE OUTPUT >>>>>>>

def debug_print(*args, **kwargs):
    """Helper function to print only if DEBUG_MODE is True."""
    if DEBUG_MODE:
        # Flush ensures the output appears immediately, helpful for debugging crashes
        print(*args, **kwargs, flush=True)

class MyStrategicBot(Bot):
    # --- __init__ METHOD with fix ---
    def __init__(self, id: int, start_x: int, start_y: int, minimap: list, map_length: int, map_breadth: int):
        # Call the parent constructor, passing all arguments
        super().__init__(id, start_x, start_y, minimap, map_length, map_breadth)

        # Store map dimensions directly in this instance
        self.map_length = map_length
        self.map_breadth = map_breadth

        # Use a deque to automatically keep history size limited
        self.position_history = deque(maxlen=HISTORY_LENGTH)
        self.last_move_decision = "init" # For debugging/understanding bot state

        # Add a debug print to confirm they are set (will only print if DEBUG_MODE is True)
        debug_print(f"Bot {self.id} initialized at ({start_x}, {start_y}).")
        try:
             debug_print(f"  Map Size stored in bot: ({self.map_length}, {self.map_breadth})")
        except AttributeError:
             debug_print(f"  ERROR: Failed to store map_length/map_breadth in __init__!")
    # --- END __init__ METHOD ---

    # --- Core Move Logic ---
    def move(self, current_x: int, current_y: int, minimap: list, bot_food: dict) -> int:

        # --- Optional DEBUG: Check inputs ---
        # (Keep commented out unless needed again)
        # debug_print(f"\n>>> Bot {self.id} Received Inputs <<<")
        # debug_print(f"  current_x = {current_x} (type: {type(current_x)})")
        # debug_print(f"  current_y = {current_y} (type: {type(current_y)})")
        # debug_print(f"  minimap type = {type(minimap)}")
        # debug_print(f"  bot_food type = {type(bot_food)}")
        # debug_print("-" * 30)
        # --- End Optional DEBUG ---

        # --- ENSURE THIS IS CALLED FIRST ---
        try:
            self.update_state(current_x, current_y, minimap, bot_food)
            # debug_print(f"Bot {self.id}: update_state completed.") # Keep commented unless needed
        except Exception as e:
            debug_print(f"!!!!!!!! Bot {self.id}: ERROR during self.update_state !!!!!!!!")
            debug_print(f"  Error: {e}")
            return MOVE_HALT
        # --- END ENSURE ---

        # --- Add position history *after* update_state confirms basic state exists ---
        try:
            self.position_history.append((self.x, self.y))
        except AttributeError:
             debug_print(f"Bot {self.id}: ERROR - self.x or self.y not set after update_state. Cannot append history.")
             return MOVE_HALT

        # --- UNCOMMENTED Map Visualization Block ---
        # Print current state and surroundings if debugging is on
        if DEBUG_MODE:
            debug_print(f"\n--- Bot {self.id} Turn ---")
            try:
                debug_print(f"Bot {self.id} state: Pos=({self.x},{self.y}), Food={self.bot_food.get(self.id, 0)}, MapSize=({self.map_length},{self.map_breadth})")
                debug_print("Map around bot (self.map):")
                # Print a 5x5 view centered on the bot from self.map if possible
                view_radius = 2
                for i in range(max(0, self.x - view_radius), min(self.map_length, self.x + view_radius + 1)):
                     row_str = f"{i:2d}: " # Row index
                     for j in range(max(0, self.y - view_radius), min(self.map_breadth, self.y + view_radius + 1)):
                         # Check bounds before accessing map here too
                         if 0 <= i < self.map_length and 0 <= j < self.map_breadth:
                             cell_val = self.map[i][j]
                             # Highlight bot's current position
                             prefix = ">" if i == self.x and j == self.y else " "
                             suffix = "<" if i == self.x and j == self.y else " "
                             row_str += f"{prefix}{str(cell_val):<3}{suffix}" # Ensure cell_val is string for padding
                         else:
                             row_str += "  OOB " # Indicate Out Of Bounds
                     debug_print(row_str)
            except IndexError:
                 debug_print("  Error accessing map indices for printing view.")
            except AttributeError:
                 debug_print("  self.map, self.x, self.y, map_length/breadth might not be initialized correctly.")
            except TypeError:
                 debug_print("  Error formatting map view (maybe non-string cell values?).")
            debug_print("-" * 20)
        # --- End Map Visualization Block ---

        # --- Add a simple print here to see if we get past the map printing block ---
        # debug_print(f"Bot {self.id}: Passed the map printing block.") # Keep commented unless needed
        # ---

        # --- Start of actual decision logic ---
        # debug_print(f"--- Bot {self.id} Decision Logic ---") # Keep commented unless needed

        # 1. & 2. & 3. & 4. Avoid Threats
        # debug_print(f"Bot {self.id}: Checking for threats...") # Keep commented unless needed
        escape_move = self._find_escape_move()
        if escape_move is not None:
            self.last_move_decision = "escape"
            debug_print(f"Bot {self.id}: Escaping! Move: {escape_move}") # Keep this one maybe
            return escape_move
        # debug_print(f"Bot {self.id}: No immediate threats found or escape planned.") # Keep commented unless needed

        # 5. & 6. Hunt Weaker Bots
        # debug_print(f"Bot {self.id}: Checking for weaker bots...") # Keep commented unless needed
        hunt_move = self._find_hunt_move()
        if hunt_move is not None:
            self.last_move_decision = "hunt"
            debug_print(f"Bot {self.id}: Hunting! Move: {hunt_move}") # Keep this one maybe
            return hunt_move
        # debug_print(f"Bot {self.id}: No weaker bots found or hunt planned.") # Keep commented unless needed

        # 7. Collect Food Efficiently
        # debug_print(f"Bot {self.id}: Checking for food...") # Keep commented unless needed
        food_move = self._find_food_move()
        if food_move is not None:
            self.last_move_decision = "food"
            # debug_print(f"Bot {self.id}: Seeking food! Move: {food_move}") # Probably not needed now
            return food_move
        # debug_print(f"Bot {self.id}: No food found or food path planned.") # Keep commented unless needed

        # 8. Avoid Looping / Explore
        if self._is_stuck():
            debug_print(f"Bot {self.id}: Detected potential loop/stuck state. Exploring...") # Keep this one maybe
            explore_move = self._get_exploration_move()
            if explore_move is not None:
                 self.last_move_decision = "explore_stuck"
                 debug_print(f"Bot {self.id}: Exploring (stuck)! Move: {explore_move}") # Keep this one maybe
                 return explore_move
            debug_print(f"Bot {self.id}: Exploration move failed even when stuck.") # Keep this one maybe

        # Fallback: Random Safe Move
        self.last_move_decision = "random_fallback"
        # debug_print(f"Bot {self.id}: No specific action. Falling back to random safe move...") # Keep commented unless needed
        final_move = self._get_random_safe_move()
        # --- DEBUG: Print final decision ---
        # debug_print(f"Bot {self.id} at ({self.x}, {self.y}): Final decision='{self.last_move_decision}', Move={final_move}") # Keep commented unless needed
        # --- End DEBUG ---
        return final_move

    # --- Helper Methods ---
    # (Paste the same helper methods from the previous response here,
    #  they already include internal debug_print calls controlled by DEBUG_MODE)

    def _is_safe_cell(self, x: int, y: int) -> bool:
        """Checks if a cell is within bounds and is walkable or food."""
        if not self._in_bounds(x, y):
            # debug_print(f"  _is_safe_cell: ({x},{y}) is out of bounds.") # Optional: very verbose
            return False
        try:
            # Assuming self.map is correctly populated by update_state
            cell_type = self.map[x][y]
            is_safe = cell_type == WALKABLE_CELL or cell_type == FOOD_CELL
            # debug_print(f"  _is_safe_cell: ({x},{y}) type={cell_type}, safe={is_safe}") # Optional: very verbose
            return is_safe
        except IndexError:
            debug_print(f"  _is_safe_cell: IndexError accessing map at ({x},{y})")
            return False
        except AttributeError:
             debug_print("  _is_safe_cell: self.map might not be initialized correctly by update_state.")
             return False
        except TypeError:
             debug_print(f"  _is_safe_cell: self.map might not be a 2D list or similar at ({x},{y}). Type is {type(self.map)}")
             return False


    def _parse_bot_id(self, cell_value) -> int | None:
        """Safely tries to convert a cell value to a bot ID (integer)."""
        if cell_value in [WALKABLE_CELL, FOOD_CELL, MOUNTAIN_CELL, OUT_OF_BOUNDS_CELL, UNKNOWN_CELL]:
            return None
        try:
            # Check if it's already an int (less likely based on game description, but safe)
            if isinstance(cell_value, int):
                return cell_value
            # Try converting from string
            return int(cell_value)
        except (ValueError, TypeError):
            # debug_print(f"  _parse_bot_id: Could not parse '{cell_value}' as int.") # Optional: verbose
            return None

    def _find_escape_move(self) -> int | None:
        """
        Finds stronger bots nearby and determines the best escape move.
        Prioritizes moving directly away. If blocked, uses BFS to find nearest safe cell away from threats.
        """
        try:
            my_food = self.bot_food.get(self.id, 1)
        except AttributeError:
            debug_print("  _find_escape_move: ERROR - self.bot_food not set.")
            return None # Cannot determine threats without food info

        threat_directions = [] # Directions where threats are located
        stronger_bots_coords = []

        # Identify adjacent threats
        for direction, (dx, dy) in MOVEMENTS.items():
            try: # Add try block for safety when accessing self.x/y early
                nx, ny = self.x + dx, self.y + dy
            except AttributeError:
                debug_print("  _find_escape_move: ERROR - self.x or self.y not set.")
                return None # Cannot check neighbors if position unknown

            if not self._in_bounds(nx, ny):
                continue

            try:
                cell_val = self.map[nx][ny] # Check map access here too
            except (IndexError, AttributeError, TypeError):
                 debug_print(f"  _find_escape_move: Error accessing map at ({nx},{ny})")
                 continue # Skip if map is invalid

            other_bot_id = self._parse_bot_id(cell_val)
            if other_bot_id is not None and other_bot_id != self.id:
                other_food = self.bot_food.get(other_bot_id, 1)
                if other_food >= my_food:
                    debug_print(f"  Threat detected: Bot {other_bot_id} (Food: {other_food}) at ({nx},{ny}) in direction {direction}")
                    threat_directions.append(direction)
                    stronger_bots_coords.append((nx,ny))

        if not threat_directions:
            return None # No immediate threats

        # --- Determine Escape Strategy ---
        possible_moves = {} # move: is_safe
        for direction, (dx, dy) in MOVEMENTS.items():
             try: # Add try block for safety
                 nx, ny = self.x + dx, self.y + dy
             except AttributeError: return None # Cannot proceed if position unknown

             # Check bounds before checking safety
             if self._in_bounds(nx, ny):
                 possible_moves[direction] = self._is_safe_cell(nx, ny)
             else:
                 possible_moves[direction] = False # Out of bounds is not safe
             # debug_print(f"  Escape check: Move {direction} to ({nx},{ny}) safe={possible_moves[direction]}") # Optional: verbose

        # Prioritize moves directly away from threats that are safe
        safe_away_moves = []
        opposite = {MOVE_UP: MOVE_DOWN, MOVE_DOWN: MOVE_UP, MOVE_LEFT: MOVE_RIGHT, MOVE_RIGHT: MOVE_LEFT}

        potential_escape_dirs = list(MOVEMENTS.keys())
        for threat_dir in threat_directions:
            # Don't move towards a threat
            if threat_dir in potential_escape_dirs:
                potential_escape_dirs.remove(threat_dir)
            # Prefer moving opposite to a threat if safe
            escape_dir = opposite.get(threat_dir)
            if escape_dir and possible_moves.get(escape_dir, False):
                 # Prioritize moving to food while escaping
                 try: # Add try block for safety
                     ex, ey = self.x + MOVEMENTS[escape_dir][0], self.y + MOVEMENTS[escape_dir][1]
                 except AttributeError: return None # Cannot proceed if position unknown

                 # Need to check bounds again before accessing map for food check
                 if self._in_bounds(ex, ey):
                     try:
                         if self.map[ex][ey] == FOOD_CELL:
                             debug_print(f"  Best escape: Move {escape_dir} (away from {threat_dir}, safe, leads to food)")
                             return escape_dir # Best option: safe, away, and food!
                     except (IndexError, AttributeError, TypeError):
                          debug_print(f"  _find_escape_move: Error accessing map for food check at ({ex},{ey})")
                 safe_away_moves.append(escape_dir)

        # If a safe move directly away exists, take it (prefer unique ones first)
        if safe_away_moves:
            unique_safe_away_moves = list(set(safe_away_moves))
            chosen_move = random.choice(unique_safe_away_moves)
            debug_print(f"  Escape choice: Move {chosen_move} (safe, directly away from a threat)")
            return chosen_move

        # If direct escape isn't safe/possible, try other safe directions not towards threats
        other_safe_moves = [d for d in potential_escape_dirs if possible_moves.get(d, False)]
        if other_safe_moves:
             # Prioritize food among these safe moves
             for move in other_safe_moves:
                 try: # Add try block for safety
                     ex, ey = self.x + MOVEMENTS[move][0], self.y + MOVEMENTS[move][1]
                 except AttributeError: return None # Cannot proceed if position unknown

                 if self._in_bounds(ex, ey): # Check bounds
                     try:
                         if self.map[ex][ey] == FOOD_CELL:
                             debug_print(f"  Escape choice: Move {move} (safe, not towards threat, leads to food)")
                             return move
                     except (IndexError, AttributeError, TypeError):
                          debug_print(f"  _find_escape_move: Error accessing map for food check at ({ex},{ey})")
             chosen_move = random.choice(other_safe_moves) # Otherwise, pick a random safe direction
             debug_print(f"  Escape choice: Move {chosen_move} (safe, not towards threat)")
             return chosen_move

        # --- If no immediate safe adjacent cell, use BFS to find nearest safe spot ---
        debug_print(f"  No safe adjacent escape. Trying BFS for nearest safe cell...")
        def is_walkable_for_escape(x, y, cell_val):
             # Check bounds within the lambda/helper too
             if not self._in_bounds(x,y): return False
             # Check cell type safely
             try:
                 return cell_val == WALKABLE_CELL or cell_val == FOOD_CELL
             except: # Catch potential issues if cell_val is weird
                 return False

        def is_target_safe_cell(x, y, cell_val):
            # Check bounds within the lambda/helper too
            if not self._in_bounds(x,y): return False
            # Check cell type safely
            try:
                return cell_val == WALKABLE_CELL or cell_val == FOOD_CELL
            except:
                return False

        bfs_result_move = self._bfs(
            is_target_fn=is_target_safe_cell,
            is_walkable_fn=is_walkable_for_escape,
            max_depth=ESCAPE_BFS_DEPTH,
            bfs_purpose="escape_bfs" # Add purpose for debugging BFS
        )

        if bfs_result_move is not None:
            debug_print(f"  Escape choice: Move {bfs_result_move} (via BFS to nearest safe cell)")
            return bfs_result_move

        # If completely trapped (no adjacent safe moves and BFS found nothing)
        pos_str = f"at ({self.x}, {self.y})" if hasattr(self, 'x') and hasattr(self, 'y') else "at unknown position"
        debug_print(f"Bot {self.id} {pos_str}: Completely trapped by threats! Halting.") # ADDED DEBUG
        return MOVE_HALT # Last resort: stay still

    def _find_hunt_move(self) -> int | None:
        """Uses BFS to find the nearest weaker bot and returns the move towards it."""
        try:
            my_food = self.bot_food.get(self.id, 1)
        except AttributeError:
            debug_print("  _find_hunt_move: ERROR - self.bot_food not set.")
            return None

        def is_target_weaker_bot(x, y, cell_val):
            if not self._in_bounds(x,y): return False
            other_bot_id = self._parse_bot_id(cell_val)
            if other_bot_id is not None and other_bot_id != self.id:
                other_food = self.bot_food.get(other_bot_id, 1)
                return other_food < my_food
            return False

        def is_walkable_for_hunt(x, y, cell_val):
            if not self._in_bounds(x,y): return False
            # Can walk on empty cells, food cells, or cells occupied by weaker bots
            try:
                if cell_val == WALKABLE_CELL or cell_val == FOOD_CELL:
                    return True
            except: return False # Handle potential comparison errors

            other_bot_id = self._parse_bot_id(cell_val)
            if other_bot_id is not None and other_bot_id != self.id:
                 other_food = self.bot_food.get(other_bot_id, 1)
                 return other_food < my_food # Can step onto weaker bot cells
            return False

        return self._bfs(
            is_target_fn=is_target_weaker_bot,
            is_walkable_fn=is_walkable_for_hunt,
            max_depth=DEFAULT_BFS_DEPTH,
            bfs_purpose="hunt" # Add purpose for debugging BFS
        )

    def _find_food_move(self) -> int | None:
        """Uses BFS to find the nearest food cell and returns the move towards it."""
        def is_target_food(x, y, cell_val):
            if not self._in_bounds(x,y): return False
            try:
                return cell_val == FOOD_CELL
            except: return False

        def is_walkable_for_food(x, y, cell_val):
            if not self._in_bounds(x,y): return False
            # Can only walk on empty or food cells when seeking food
            try:
                return cell_val == WALKABLE_CELL or cell_val == FOOD_CELL
            except: return False

        return self._bfs(
            is_target_fn=is_target_food,
            is_walkable_fn=is_walkable_for_food,
            max_depth=DEFAULT_BFS_DEPTH,
            bfs_purpose="food" # Add purpose for debugging BFS
        )

    def _is_stuck(self) -> bool:
        """Checks if the bot has visited few unique positions recently."""
        if len(self.position_history) < HISTORY_LENGTH:
            return False # Not enough history yet
        try:
            unique_positions = set(self.position_history)
            is_stuck = len(unique_positions) <= STUCK_THRESHOLD
            if is_stuck:
                 debug_print(f"  _is_stuck: True. History={list(self.position_history)}, Unique={len(unique_positions)}")
            return is_stuck
        except TypeError:
             # This might happen if position_history contains non-hashable items, though unlikely with tuples
             debug_print("  _is_stuck: TypeError checking history uniqueness.")
             return False


    def _get_exploration_move(self) -> int | None:
        """Finds a safe move that doesn't lead to a recently visited position."""
        safe_moves_new = []
        safe_moves_old = []
        try:
            recent_pos_set = set(self.position_history)
        except TypeError:
             debug_print("  _get_exploration_move: TypeError creating set from history.")
             recent_pos_set = set() # Treat history as empty if error

        for direction, (dx, dy) in MOVEMENTS.items():
            try: # Add safety check for self.x/y
                nx, ny = self.x + dx, self.y + dy
            except AttributeError:
                debug_print("  _get_exploration_move: ERROR - self.x or self.y not set.")
                return None # Cannot explore without position

            # Check safety first (which includes bounds check)
            if self._is_safe_cell(nx, ny):
                if (nx, ny) not in recent_pos_set: # Prefer moves to new locations
                    safe_moves_new.append(direction)
                else:
                    safe_moves_old.append(direction) # Track safe moves to old locations too

        if safe_moves_new:
            chosen_move = random.choice(safe_moves_new)
            debug_print(f"  Exploration choice: Move {chosen_move} (safe, to new location)")
            return chosen_move
        elif safe_moves_old:
             # If only safe moves lead to recent positions, pick one of those
             chosen_move = random.choice(safe_moves_old)
             debug_print(f"  Exploration choice: Move {chosen_move} (safe, but to recent location)")
             return chosen_move

        # If no safe moves at all (should be rare if called after _is_stuck)
        debug_print(f"  Exploration failed: No safe moves found.")
        return None # Let fallback handle it (likely halt)


    def _get_random_safe_move(self) -> int:
        """Returns a random valid move (UP, DOWN, LEFT, RIGHT) into a safe cell."""
        safe_moves = []
        for direction, (dx, dy) in MOVEMENTS.items():
            try: # Add safety check for self.x/y
                nx, ny = self.x + dx, self.y + dy
            except AttributeError:
                debug_print("  _get_random_safe_move: ERROR - self.x or self.y not set.")
                continue # Skip this direction if position unknown

            # Check safety (includes bounds check)
            if self._is_safe_cell(nx, ny):
                safe_moves.append(direction)

        if safe_moves:
            chosen_move = random.choice(safe_moves)
            # debug_print(f"  Random safe move choice: {chosen_move}") # Commented out for cleaner output
            return chosen_move
        else:
            # Check if self.x, self.y exist before printing them
            pos_str = f"at ({self.x}, {self.y})" if hasattr(self, 'x') and hasattr(self, 'y') else "at unknown position"
            debug_print(f"Bot {self.id} {pos_str}: No safe adjacent moves found for random fallback. Halting.")
            return MOVE_HALT


    def _bfs(self, is_target_fn, is_walkable_fn, max_depth: int, bfs_purpose: str = "general") -> int | None:
        """
        Performs Breadth-First Search.
        Args:
            is_target_fn: Function(x, y, cell_value) -> bool, returns True if (x, y) is a target.
            is_walkable_fn: Function(x, y, cell_value) -> bool, returns True if bot can step on (x, y).
            max_depth: Maximum search depth.
            bfs_purpose: String label for debugging.
        Returns:
            The first move direction (int) towards the nearest target, or None if no target found.
        """
        try:
            start_x, start_y = self.x, self.y # Ensure bot position is known
        except AttributeError:
            debug_print(f"  BFS ({bfs_purpose}): ERROR - self.x or self.y not set. Cannot start BFS.")
            return None

        queue = deque([(start_x, start_y, None, 0)])  # (x, y, first_move_direction, depth)
        visited = set([(start_x, start_y)])
        # debug_print(f"  Starting BFS ({bfs_purpose}) from ({start_x},{start_y}), max_depth={max_depth}") # Commented out for cleaner output

        found_target_move = None # Store the first move of the first target found

        while queue:
            cx, cy, first_move, depth = queue.popleft()

            # Check if current cell is a target (and not the starting cell itself unless depth > 0)
            try:
                # Check bounds before accessing map
                if not self._in_bounds(cx, cy):
                    # debug_print(f"  BFS ({bfs_purpose}): Skipping out-of-bounds cell ({cx},{cy})") # Optional: verbose
                    continue # Skip if coords are somehow out of bounds

                current_cell_value = self.map[cx][cy]
                if depth > 0 and is_target_fn(cx, cy, current_cell_value):
                    debug_print(f"  BFS ({bfs_purpose}): Found target at ({cx},{cy}) via move {first_move} at depth {depth}")
                    found_target_move = first_move # Found the nearest target
                    break # Stop BFS once the *first* (nearest) target is found
            except IndexError:
                 debug_print(f"  BFS ({bfs_purpose}): IndexError accessing map at ({cx},{cy})")
                 continue # Skip this invalid cell
            except AttributeError:
                 debug_print(f"  BFS ({bfs_purpose}): self.map not initialized correctly.")
                 return None # Cannot proceed
            except TypeError:
                 debug_print(f"  BFS ({bfs_purpose}): self.map not 2D list? Error at ({cx},{cy}).")
                 return None # Cannot proceed

            if depth >= max_depth:
                continue # Stop searching deeper from this path

            # Explore neighbors
            shuffled_directions = list(MOVEMENTS.items())
            random.shuffle(shuffled_directions) # Avoid directional bias

            for direction, (dx, dy) in shuffled_directions:
                nx, ny = cx + dx, cy + dy

                # Check bounds before attempting to access map or check walkability
                if not self._in_bounds(nx, ny):
                    continue

                try:
                    # Check visited status *before* accessing map potentially
                    if (nx, ny) not in visited:
                        neighbor_cell_value = self.map[nx][ny]
                        # Check walkability *after* confirming it's in bounds and getting value
                        if is_walkable_fn(nx, ny, neighbor_cell_value):
                            visited.add((nx, ny))
                            # If this is the first step from the start, record the direction
                            next_first_move = first_move if first_move is not None else direction
                            queue.append((nx, ny, next_first_move, depth + 1))
                except IndexError:
                     debug_print(f"  BFS ({bfs_purpose}): IndexError accessing neighbor map at ({nx},{ny})")
                     continue # Skip this invalid cell
                except AttributeError:
                     debug_print(f"  BFS ({bfs_purpose}): self.map not initialized correctly.")
                     return None # Cannot proceed
                except TypeError:
                     debug_print(f"  BFS ({bfs_purpose}): self.map not 2D list? Error at neighbor ({nx},{ny}).")
                     return None # Cannot proceed


        # if found_target_move is None:
        #      debug_print(f"  BFS ({bfs_purpose}): No target found within depth {max_depth}") # Commented out for cleaner output

        return found_target_move # Return the move for the first target found, or None


    def _in_bounds(self, x: int, y: int) -> bool:
        """Checks if coordinates are within the map boundaries."""
        # Use the map dimensions stored during __init__
        try:
            # Ensure map_length and map_breadth are integers
            if not isinstance(self.map_length, int) or not isinstance(self.map_breadth, int):
                 debug_print(f"  _in_bounds check failed: map dimensions are not integers ({self.map_length}, {self.map_breadth})")
                 return False
            in_bounds = 0 <= x < self.map_length and 0 <= y < self.map_breadth
        except AttributeError:
             # This specific message should NOT appear anymore if __init__ fix worked
             debug_print("  _in_bounds check failed: self.map_length or self.map_breadth not set.")
             return False # Cannot determine bounds if attributes are missing
        # if not in_bounds:
        #     debug_print(f"    _in_bounds check: ({x},{y}) is OUTSIDE ({self.map_length},{self.map_breadth})") # Optional: verbose
        return in_bounds