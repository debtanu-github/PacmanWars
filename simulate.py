# --- START OF FILE simulate.py ---

import sys
import os
import time
import random
from collections import defaultdict

# --- Add project root to Python path if necessary ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ---

# --- Imports from your project ---
try:
    from constants import *
    from modules.map_generator import generate_map
    from modules.food_generator import generate_food
    from modules.bot_operations import get_number_of_bots, generate_bot_positions, load_bots, calculate_bot_directions, move_bots
    # Import your bot classes (add others if you have more)
    from bots.debtanu_bot import DebtanuBot # Assuming you renamed it
    # from bots.basic_bot1 import BasicBot1
    # from bots.basic_bot2 import BasicBot2

except ImportError as e:
    print(f"Error importing game modules: {e}")
    print("Please ensure simulate.py is in the main project directory and all modules are accessible.")
    sys.exit(1)

# --- Simulation Parameters ---
NUM_SIMULATIONS = 300
MAX_GAME_MOVES = 1000
MAP_GENERATION_PARAMS = (0.6, 0.6, 200)

# --- Food Generation Config (Match main.py's chosen logic) ---
MAX_FOOD_PERCENTAGE = 0.15
FOOD_GENERATION_QUANTITY_PER_BOT = 1
# ---

def run_single_simulation():
    """Runs one full game simulation without graphics and returns the result including final bot statuses."""
    try:
        # --- Initialize Game State ---
        game_map = generate_map(*MAP_GENERATION_PARAMS)
        number_of_bots = get_number_of_bots()
        if number_of_bots == 0: return None
        bot_positions = generate_bot_positions(game_map, number_of_bots)
        bots, bot_names = load_bots(bot_positions, game_map)
        bot_food = {id: 1 for id in bot_positions.keys()}
        bot_ids = {id: BOT_ALIVE for id in range(1, number_of_bots + 1)} # Stores ALIVE/DEAD status
        game_counter = MAX_GAME_MOVES
        num_alive_bots = number_of_bots
        rows = len(game_map); cols = len(game_map[0]) if rows > 0 else 0
        if rows <= 0 or cols <= 0: return None

        # --- Simulation Loop ---
        while game_counter > 0 and num_alive_bots > 1:
            bot_directions = calculate_bot_directions(game_map, bots, bot_positions, bot_ids, bot_food)
            move_bots(game_map, bot_ids, bot_positions, bot_directions, bot_food) # This updates bot_ids
            num_alive_bots = sum(1 for i in bot_ids.values() if i == BOT_ALIVE)
            if num_alive_bots <= 1: break

            # Food Generation
            total_cells = rows * cols
            food_count = sum(row.count(FOOD_CELL) for row in game_map)
            current_food_percentage = food_count / total_cells if total_cells > 0 else 0
            if current_food_percentage < MAX_FOOD_PERCENTAGE:
                quantity_to_generate = num_alive_bots * FOOD_GENERATION_QUANTITY_PER_BOT
                generate_food(game_map, quantity_to_generate)

            game_counter -= 1

        # --- Determine Winner ---
        winner_id = -1
        # Check timeout condition first
        timed_out = (game_counter <= 0)

        if timed_out:
            alive_bots_food = {id: food for id, food in bot_food.items() if bot_ids.get(id, BOT_DEAD) == BOT_ALIVE}
            if alive_bots_food: winner_id = max(alive_bots_food, key=alive_bots_food.get)
            elif bot_food: winner_id = max(bot_food, key=bot_food.get) # Fallback if all died somehow
        elif num_alive_bots == 1: # Last bot standing
            for id, status in bot_ids.items():
                if status == BOT_ALIVE: winner_id = id; break
        else: # num_alive_bots == 0 (Simultaneous death?)
             if bot_food: winner_id = max(bot_food, key=bot_food.get)

        winner_name = "DRAW" # Should be rare
        if winner_id != -1:
             winner_name = bot_names.get(winner_id, f"Bot {winner_id}")

        # --- Return results including final statuses ---
        return {
            "winner_id": winner_id,
            "winner_name": winner_name,
            "final_food": bot_food,
            "bot_names": bot_names,
            "turns_lasted": MAX_GAME_MOVES - game_counter,
            "timed_out": timed_out,
            "final_status": bot_ids # <-- ADDED: Dictionary of {bot_id: BOT_ALIVE/BOT_DEAD}
        }

    except Exception as e:
        print(f"\n!!! ERROR during simulation run: {e} !!!")
        import traceback
        traceback.print_exc()
        return None

# --- Main Simulation Runner ---
if __name__ == "__main__":
    # --- Run Simulations ---
    print(f"Starting {NUM_SIMULATIONS} simulations...")
    start_time = time.time()
    simulation_results = []
    for i in range(NUM_SIMULATIONS):
        # Simple progress indicator
        print(f"\r  Running simulation {i + 1}/{NUM_SIMULATIONS}...", end="")
        result = run_single_simulation()
        if result:
            simulation_results.append(result)
        # else: # Optional: Log skipped/failed runs
            # print(f"\n  Simulation {i+1} failed or was skipped.")
    print("\nFinished.") # Newline after progress indicator
    end_time = time.time()
    print(f"Completed {len(simulation_results)} successful simulations in {end_time - start_time:.2f} seconds.")

    # --- Aggregate Statistics ---
    if not simulation_results:
        print("No successful simulations to analyze.")
        sys.exit(0)

    # Use nested defaultdict for easier stat tracking per bot
    # bot_stats[bot_id]['stat_name'] = value
    bot_stats = defaultdict(lambda: defaultdict(int))
    bot_names_master = {}
    total_turns = 0

    for result in simulation_results:
        total_turns += result["turns_lasted"]
        bot_names_master.update(result["bot_names"])
        winner_id = result["winner_id"]
        timed_out = result["timed_out"]
        final_status = result["final_status"]

        # Iterate through all bots that participated in this run (based on final_food keys)
        for bot_id in result["final_food"].keys():
            bot_stats[bot_id]['games_played'] += 1
            bot_stats[bot_id]['total_food'] += result["final_food"].get(bot_id, 0)

            # Check win/loss
            if bot_id == winner_id:
                bot_stats[bot_id]['wins'] += 1
            else:
                # It's a loss, determine type
                status = final_status.get(bot_id, BOT_DEAD) # Assume dead if missing (shouldn't happen)
                if status == BOT_DEAD:
                    bot_stats[bot_id]['losses_killed'] += 1
                elif status == BOT_ALIVE:
                    # Must have lost on score at timeout
                    bot_stats[bot_id]['losses_score'] += 1
                else: # Should not happen
                     bot_stats[bot_id]['losses_unknown'] += 1


    # --- Print Statistics ---
    print("\n--- Simulation Statistics ---")
    print(f"Total Successful Runs: {len(simulation_results)}")
    avg_turns = total_turns / len(simulation_results) if len(simulation_results) > 0 else 0
    print(f"Average Game Length: {avg_turns:.2f} turns")

    print("\n--- Bot Performance ---")
    all_bot_ids = sorted(bot_names_master.keys())
    for bot_id in all_bot_ids:
        name = bot_names_master.get(bot_id, f"Bot {bot_id}")
        stats = bot_stats[bot_id]
        wins = stats['wins']
        losses_k = stats['losses_killed']
        losses_s = stats['losses_score']
        losses_u = stats['losses_unknown'] # Should be 0
        total_losses = losses_k + losses_s + losses_u
        games_played = stats['games_played']
        total_food = stats['total_food']

        win_perc = (wins / games_played) * 100 if games_played > 0 else 0
        loss_k_perc = (losses_k / total_losses) * 100 if total_losses > 0 else 0
        loss_s_perc = (losses_s / total_losses) * 100 if total_losses > 0 else 0
        avg_food = total_food / games_played if games_played > 0 else 0

        print(f"\n  Bot: {name} (ID {bot_id})")
        print(f"    - Games Played: {games_played}")
        print(f"    - Wins:         {wins} ({win_perc:.2f}%)")
        print(f"    - Total Losses: {total_losses}")
        if total_losses > 0:
            print(f"      - Killed:     {losses_k} ({loss_k_perc:.2f}% of losses)")
            print(f"      - Score:      {losses_s} ({loss_s_perc:.2f}% of losses)")
            if losses_u > 0: print(f"      - Unknown:    {losses_u}") # Report if any unknown losses occurred
        print(f"    - Avg Food:     {avg_food:.2f}")


    print("\n--- End of Report ---")

# --- END OF FILE simulate.py ---