import sys

import pygame

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((800, 800))
base_font = pygame.font.SysFont("Arial", 20)
user_text = ""

input_rect = pygame.Rect(0, 0, 800, 30)
color = pygame.Color("lightblue")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                user_text = user_text[:-1]
            else:
                user_text += event.unicode

    screen.fill((0, 0, 0))
    pygame.draw.rect(screen, color, input_rect, 2)
    text_surface = base_font.render(user_text, True, (255, 255, 255), 2)
    screen.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))
    pygame.display.flip()
    clock.tick(60)
