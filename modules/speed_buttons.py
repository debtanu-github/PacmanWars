import pygame
from constants import *

# Pygame button creator
class Button:
    def __init__(self, x, y, width, height, color, text, action):
        """
        Creates a button with given specifications
        :param x: x coordinate of the button
        :param y: y coordinate of the button
        :param width: width of the button
        :param height: height of the button
        :param color: color of the button
        :param text: Text to be written inside the button
        :param action: Function to be executed on the button click
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text = text
        self.action = action

    def draw(self, screen, font):
        # Draw button background
        pygame.draw.rect(screen, self.color, self.rect)
        # Draw button border
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 1)
        # Draw button text
        text_surface = font.render(self.text, True, (0, 0, 0))
        screen.blit(text_surface, (self.rect.x + (self.rect.width - text_surface.get_width()) // 2,
                                   self.rect.y + (self.rect.height - text_surface.get_height()) // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Generate buttons to modify game speed
# (DO NOT CHANGE THIS, YOUR CHANGES WILL BE IGNORED IN THE COMPETITION)
def get_speed_buttons():
    """
    Generates 5 buttons with x1, x2, x4, x8 and x16 game speed modes
    """
    button1 = Button(WIDTH + 20, HEIGHT - 40, 20, 20, WALKABLE_CELL_COLOR, "x1", lambda : 1)
    button2 = Button(WIDTH + 50, HEIGHT - 40, 20, 20, WALKABLE_CELL_COLOR, "x2", lambda : 2)
    button3 = Button(WIDTH + 80, HEIGHT - 40, 20, 20, WALKABLE_CELL_COLOR, "x4", lambda : 4)
    button4 = Button(WIDTH + 110, HEIGHT - 40, 20, 20, WALKABLE_CELL_COLOR, "x8", lambda : 8)
    button5 = Button(WIDTH + 140, HEIGHT - 40, 20, 20, WALKABLE_CELL_COLOR, "x16", lambda : 16)
    buttons = [button1, button2, button3, button4, button5]
    return buttons
