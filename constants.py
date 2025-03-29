# (DO NOT CHANGE THIS, YOUR CHANGES WILL BE IGNORED IN THE COMPETITION)
# Cell Types
WALKABLE_CELL = 'G'         # bot can walk on this cell
OUT_OF_BOUNDS_CELL = 'R'    # this region is not a part of the map
MOUNTAIN_CELL = 'O'         # bot cannot walk on this cell
FOOD_CELL = 'F'             # bot can walk on this cell, but it is a food source
PLAYER_CELL = 'W'           # bot can walk on this cell, but it is another player so they will battle
UNKNOWN_CELL = 'U'          # bot does not know what is in this cell

# Bot movements
MOVE_UP = 0                 # bot moves up
MOVE_DOWN = 1               # bot moves down
MOVE_LEFT = 2               # bot moves left
MOVE_RIGHT = 3              # bot moves right
MOVE_HALT = 4               # bot does not move
MOVEMENTS = {MOVE_UP: (-1, 0), MOVE_DOWN: (1, 0), MOVE_LEFT: (0, -1), MOVE_RIGHT: (0, 1), MOVE_HALT: (0, 0)}

# Bot states
BOT_ALIVE = 1
BOT_DEAD = 0

# =======================================================================================================
# (DO NOT CHANGE THIS, YOUR CHANGES WILL BE IGNORED IN THE COMPETITION)
# Generation of the map
MAX_OUT_OF_BOUND_PROBABILITY = 0.8

# =======================================================================================================
# (YOU CAN CHANGE THESE VALUES)
# Screen dimensions
import pygame
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
# Calculate window size as 80% of the smaller screen dimension
WINDOW_SIZE = min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.8
WIDTH = int(WINDOW_SIZE)
HEIGHT = int(WINDOW_SIZE)
ROWS, COLS = 40, 40
CELL_SIZE = WIDTH // COLS

# Define colors - Updated for better visual appeal and reduced eye strain
# Soft, muted colors for better contrast and reduced eye strain
WALKABLE_CELL_COLOR = (200, 230, 200)  # Soft mint green for walkable areas
OUT_OF_BOUNDS_COLOR = (40, 40, 40)      # Dark gray for out of bounds
MOUNTAIN_CELL_COLOR = (180, 120, 100)   # Warm brown for mountains
FOOD_CELL_COLOR = (255, 215, 0)         # Soft gold for food
PLAYER_CELL_COLOR = (255, 255, 255)     # White for player cells
UNKNOWN_CELL_COLOR = (180, 180, 180)    # Light gray for unknown cells
BACKGROUND_COLOR = (25, 25, 35)         # Dark blue-gray for background
TEXT_COLOR = (230, 230, 230)            # Soft white for text
BORDER_COLOR = (60, 60, 70)             # Dark gray for borders

COLOR_MAP = {
    WALKABLE_CELL: WALKABLE_CELL_COLOR,
    OUT_OF_BOUNDS_CELL: OUT_OF_BOUNDS_COLOR,
    MOUNTAIN_CELL: MOUNTAIN_CELL_COLOR,
    FOOD_CELL: FOOD_CELL_COLOR,
    PLAYER_CELL: PLAYER_CELL_COLOR,
    UNKNOWN_CELL: UNKNOWN_CELL_COLOR
}