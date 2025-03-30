# --- START OF FILE main.py ---

import pygame
import sys
from constants import * # Make sure FOOD_CELL is defined here
from modules.map_generator import generate_map
from modules.food_generator import generate_food
from modules.bot_operations import *
from modules.speed_buttons import get_speed_buttons

try:
    # Initialize the game using pygame UI
    pygame.init()
    screen = pygame.display.set_mode((WIDTH + 200, HEIGHT + 100))
    pygame.display.set_caption("PACMAN WARS")
except pygame.error as e:
    print(f"Error initializing pygame: {e}")
    sys.exit(1)

# Draws the entire game screen snapshot on the application
# (DO NOT CHANGE THIS, YOUR CHANGES WILL BE IGNORED IN THE COMPETITION)
def draw_game_screen(screen: pygame.Surface, speed_buttons: list, map: list, moves_left: int, bot_food: dict, bot_names: dict):
    """
    Draws game screen on the application
    :param screen: UI screen
    :param speed_buttons: List of speed buttons to alter game speed
    :param map: 2D list representing the game map
    :param moves_left: number of moves left to play in the game
    :param bot_food: Dictionary containing the food count of the bots
    :param bot_names: Dictionary containing the names of the bots
    """
    try:
        # Draw game title
        font = pygame.font.SysFont('Arial', 45, bold=True)  # Use Arial font with size 30 and bold
        text = font.render("PACMAN WARS", True, TEXT_COLOR)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))

        # Draw speed buttons
        font = pygame.font.SysFont('Arial', 15, bold=False)
        text = font.render(f"Change game speed", True, TEXT_COLOR)
        screen.blit(text, (WIDTH + 10, HEIGHT - 80))
        for button in speed_buttons:
            button.draw(screen, font)

        # Draw grid map
        font = pygame.font.SysFont(None, 18)
        for i, row in enumerate(map):
            for j, cell in enumerate(row):
                # Basic check for non-uniform rows
                if j < len(row):
                    cell_value = row[j]
                    if cell_value in COLOR_MAP.keys():    # If its not a player cell
                        color = COLOR_MAP[cell_value]
                    else:   # Player cell will be marked by a number rather than 'P'
                        color = COLOR_MAP.get(PLAYER_CELL, (255, 255, 255)) # Use default white if PLAYER_CELL missing
                    
                    # Draw the cell with desired color
                    pygame.draw.rect(screen, color, (j * CELL_SIZE, i * CELL_SIZE + 100, CELL_SIZE, CELL_SIZE))
                    pygame.draw.rect(screen, BORDER_COLOR, (j * CELL_SIZE, i * CELL_SIZE + 100, CELL_SIZE, CELL_SIZE), 1)

                    # If its a player cell, draw the player number
                    if cell_value not in COLOR_MAP.keys():
                        text = font.render(str(cell_value), True, (0, 0, 0))  # Black text for player numbers
                        screen.blit(text, (j * CELL_SIZE + CELL_SIZE // 3, i * CELL_SIZE + 100 + CELL_SIZE // 4))
                # else: # Handle potentially jagged map rows if necessary
                    # pygame.draw.rect(screen, OUT_OF_BOUNDS_COLOR, (j * CELL_SIZE, i * CELL_SIZE + 100, CELL_SIZE, CELL_SIZE))
                    # pygame.draw.rect(screen, BORDER_COLOR, (j * CELL_SIZE, i * CELL_SIZE + 100, CELL_SIZE, CELL_SIZE), 1)


        # Draw moves left
        font = pygame.font.SysFont('Arial', 25, bold=True)  # Use Arial font with size 30 and bold
        text = font.render(f"Moves left : {moves_left}", True, TEXT_COLOR)
        screen.blit(text, (WIDTH + 20, 20))

        # Draw score board
        font = pygame.font.SysFont('Arial', 20, bold=False)  # Use Arial font with size 20 and not bold
        sorted_bots = sorted(bot_food.items(), key=lambda item: item[1], reverse=True)

        x_offset = WIDTH + 20
        y_offset = 120
        scoreboard_width = 180
        # Adjust height dynamically based on number of bots
        scoreboard_height = 40 + len(sorted_bots) * 30

        # Draw the box around the scoreboard
        pygame.draw.rect(screen, BORDER_COLOR, (x_offset - 10, y_offset - 10, scoreboard_width, scoreboard_height), 2)

        screen.blit(font.render("Scoreboard", True, TEXT_COLOR), (x_offset, y_offset))
        y_offset += 30

        for bot_id, food in sorted_bots:
            # Ensure bot_id exists in bot_names before accessing
            bot_name = bot_names.get(bot_id, f"Bot {bot_id}") # Provide default name if missing
            text = f"{bot_id}. {bot_name}: {food}"
            screen.blit(font.render(text, True, TEXT_COLOR), (x_offset, y_offset))
            y_offset += 30
    except Exception as e:
        print(f"Error in draw_game_screen: {e}")
        # Optionally re-raise or handle differently
        # raise

# Draws game over screen with the winner name
# (DO NOT CHANGE THIS, YOUR CHANGES WILL BE IGNORED IN THE COMPETITION)
def draw_game_over_screen(screen: pygame.Surface, winner_bot_name: str):
    """
    Draw the game over on the screen
    :param screen: UI screen
    :param winner_bot_name: Name of the winner bot
    """
    try:
        font = pygame.font.SysFont('Arial', 50, bold=True)  # Use Arial font with size 30 and bold
        text = font.render("GAME OVER", True, TEXT_COLOR)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2 + 100, HEIGHT // 2))
        text = font.render(f"WINNER IS {winner_bot_name}", True, TEXT_COLOR)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2 + 100, HEIGHT // 2 + 100))
    except Exception as e:
        print(f"Error in draw_game_over_screen: {e}")
        # Optionally re-raise or handle differently
        # raise

# Main loop of the game
# (DO NOT CHANGE THIS, YOUR CHANGES WILL BE IGNORED IN THE COMPETITION)
def main():
    try:
        clock = pygame.time.Clock()     # Game clock
        map = generate_map(0.6, 0.6, 200)   # Generate the game map
        number_of_bots = get_number_of_bots()   # Get the number of bots
        bot_positions = generate_bot_positions(map, number_of_bots)  # Generate the bot positions
        bots, bot_names = load_bots(bot_positions, map) # Generate bot objects with names
        bot_food = {id: 1 for id in bot_positions.keys()}  # Initialize the food count for each bot
        bot_ids = {id: BOT_ALIVE for id in range(1, number_of_bots + 1)} # Initialize the bot ids with BOT_ALIVE status
        speed_buttons = get_speed_buttons()     # Generate speed buttons to alter game speed
        num_of_alive_bots = number_of_bots      # Number of bots still alive
        game_tick = 1   # Game speed

        is_game_running = True  # Game loop
        game_counter = 1000 # Maximum game moves

        # --- Configuration for Food Generation (Option D) ---
        MAX_FOOD_PERCENTAGE = 0.15 # Adjust this: Max 15% of map cells should be food
        FOOD_GENERATION_QUANTITY_PER_BOT = 1 # How much food to potentially add per alive bot
        # --- End Configuration ---

        while is_game_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_game_running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for button in speed_buttons:
                        if button.is_clicked(event.pos):
                            game_tick = button.action()

            # --- Game Logic Execution ---
            if game_counter > 0 and num_of_alive_bots > 1: # Check if game is still running normally
                # 1. Calculate Bot Moves
                bot_directions = calculate_bot_directions(map, bots, bot_positions, bot_ids, bot_food)

                # 2. Move Bots (This should handle eating food and updating map)
                move_bots(map, bot_ids, bot_positions, bot_directions, bot_food)

                # 3. Update Alive Bot Count (Crucial after moves/battles)
                num_of_alive_bots = sum(1 for i in bot_ids.values() if i == BOT_ALIVE)

                # 4. Conditional Food Generation (Option D)
                rows = len(map)
                cols = len(map[0]) if rows > 0 else 0
                if rows > 0 and cols > 0: # Ensure map is valid
                    total_cells = rows * cols
                    # Count only FOOD_CELL, not walkable or others
                    food_count = sum(row.count(FOOD_CELL) for row in map)
                    current_food_percentage = food_count / total_cells

                    # Check threshold before generating food
                    if current_food_percentage < MAX_FOOD_PERCENTAGE:
                        # Calculate quantity based on alive bots
                        quantity_to_generate = num_of_alive_bots * FOOD_GENERATION_QUANTITY_PER_BOT
                        # print(f"Debug: Food % ({current_food_percentage:.2f}) < Threshold ({MAX_FOOD_PERCENTAGE}). Generating up to {quantity_to_generate} food.") # Optional Debug
                        generate_food(map, quantity_to_generate)
                    # else:
                        # print(f"Debug: Food % ({current_food_percentage:.2f}) >= Threshold ({MAX_FOOD_PERCENTAGE}). Skipping food generation.") # Optional Debug
                else:
                    print("Warning: Map dimensions invalid, skipping food generation.")


                # 5. Draw Screen
                screen.fill(BACKGROUND_COLOR)
                draw_game_screen(screen, speed_buttons, map, game_counter, bot_food, bot_names)

                # --- REMOVED OLD generate_food CALL ---
                # generate_food(map, number_of_bots) # <<< THIS IS THE OLD CALL, NOW REMOVED/HANDLED ABOVE

            # --- Game Over Logic ---
            elif game_counter <= 0 or num_of_alive_bots <= 1:
                # Find winner of the game (Bot with maximum food among survivors, or last one standing)
                winner = -1 # Default to no winner
                max_food = -1

                # If timeout, winner is highest score among alive
                if game_counter <= 0:
                    alive_bots_food = {id: food for id, food in bot_food.items() if bot_ids.get(id, BOT_DEAD) == BOT_ALIVE}
                    if alive_bots_food:
                         winner = max(alive_bots_food, key=alive_bots_food.get)
                    # If no bots alive at timeout (unlikely but possible), winner remains -1
                # If last man standing
                elif num_of_alive_bots == 1:
                    for id, status in bot_ids.items():
                        if status == BOT_ALIVE:
                            winner = id
                            break
                # If somehow num_of_alive_bots is 0 (e.g., simultaneous death on last move)
                else: # num_of_alive_bots == 0
                     # Could declare draw or pick highest score among all ever existed
                     if bot_food: # Check if bot_food has any entries
                         winner = max(bot_food, key=bot_food.get)


                winner_name = "DRAW" # Default if no winner found
                if winner != -1 and winner in bot_names:
                    winner_name = bot_names[winner]
                elif winner != -1:
                    winner_name = f"Bot {winner}" # Fallback name

                screen.fill(BACKGROUND_COLOR)
                draw_game_over_screen(screen, winner_name)

                # Optional: Add a small delay or wait for click before quitting on game over
                # pygame.time.wait(3000)
                # is_game_running = False # Or wait for QUIT event

            # --- Update Display and Tick Clock ---
            game_counter -= 1
            pygame.display.flip()
            clock.tick(game_tick)

    except Exception as e:
        print(f"Error in main game loop: {e}")
        # Optionally re-raise to see traceback
        raise
    finally:
        pygame.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Print fatal errors that might occur outside the main loop's try-except
        print(f"Fatal error during execution: {e}")
        import traceback
        traceback.print_exc() # Print the full traceback for debugging
        pygame.quit()
        sys.exit(1)

# --- END OF FILE main.py ---