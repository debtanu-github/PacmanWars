import pygame
import sys
from constants import *
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
                if cell in COLOR_MAP.keys():    # If its not a player cell
                    color = COLOR_MAP[cell]
                else:   # Player cell will be marked by a number rather than 'P'
                    color = COLOR_MAP[PLAYER_CELL]
                
                # Draw the cell with desired color
                pygame.draw.rect(screen, color, (j * CELL_SIZE, i * CELL_SIZE + 100, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, BORDER_COLOR, (j * CELL_SIZE, i * CELL_SIZE + 100, CELL_SIZE, CELL_SIZE), 1)

                # If its a player cell, draw the player number
                if cell not in COLOR_MAP.keys():
                    text = font.render(cell, True, (0, 0, 0))  # Black text for player numbers
                    screen.blit(text, (j * CELL_SIZE + CELL_SIZE // 3, i * CELL_SIZE + 100 + CELL_SIZE // 4))

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
        scoreboard_height = 40 + len(sorted_bots) * 30

        # Draw the box around the scoreboard
        pygame.draw.rect(screen, BORDER_COLOR, (x_offset - 10, y_offset - 10, scoreboard_width, scoreboard_height), 2)

        screen.blit(font.render("Scoreboard", True, TEXT_COLOR), (x_offset, y_offset))
        y_offset += 30
        
        for bot_id, food in sorted_bots:
            bot_name = bot_names[bot_id]
            text = f"{bot_id}. {bot_name}: {food}"
            screen.blit(font.render(text, True, TEXT_COLOR), (x_offset, y_offset))
            y_offset += 30
    except Exception as e:
        print(f"Error in draw_game_screen: {e}")
        raise

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
        raise

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
        while is_game_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_game_running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for button in speed_buttons:
                        if button.is_clicked(event.pos):
                            game_tick = button.action()

            if game_counter > 0 or num_of_alive_bots == 1:
                bot_directions = calculate_bot_directions(map, bots, bot_positions, bot_ids, bot_food)
                move_bots(map, bot_ids, bot_positions, bot_directions, bot_food)
                num_of_alive_bots = sum(1 for i in bot_ids.values() if i == BOT_ALIVE)

                screen.fill(BACKGROUND_COLOR)
                draw_game_screen(screen, speed_buttons, map, game_counter, bot_food, bot_names)
                generate_food(map, number_of_bots)
            
            else:
                # Find winner of the game (Bot with maximum food)
                winner = 1
                for id in bot_food.keys():
                    if bot_food[id] > bot_food[winner]:
                        winner = id
                screen.fill(BACKGROUND_COLOR)
                draw_game_over_screen(screen, bot_names[winner])
            
            game_counter -= 1
            pygame.display.flip()
            clock.tick(game_tick)
    except Exception as e:
        print(f"Error in main game loop: {e}")
        raise
    finally:
        pygame.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        pygame.quit()
        sys.exit(1)