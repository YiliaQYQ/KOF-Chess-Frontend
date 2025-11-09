# animations.py
import pygame
from settings import SCREEN, CELL_SIZE, CHIP_COLORS, FONT, HEIGHT, WIDTH

def animate_move(sr, sc, tr, tc, chip, steps=10):
    """平滑移动动画"""
    start_x, start_y = sc * CELL_SIZE, sr * CELL_SIZE
    end_x, end_y = tc * CELL_SIZE, tr * CELL_SIZE
    for i in range(1, steps + 1):
        x = start_x + (end_x - start_x) * i / steps
        y = start_y + (end_y - start_y) * i / steps
        color = CHIP_COLORS.get(chip.name, (0, 0, 0))
        pygame.draw.rect(SCREEN, color, (x + 6, y + 6, CELL_SIZE - 12, CELL_SIZE - 12))
        pygame.display.flip()
        pygame.time.delay(25)

def animate_athena_fusion(r1, c1, r2, c2, draw_board, flashes=6):
    """雅典娜融合 / 同归于尽特效"""
    for i in range(flashes):
        draw_board()
        color = (255, 255, 255) if i % 2 == 0 else (255, 255, 0)
        pygame.draw.rect(SCREEN, color, (c1 * CELL_SIZE, r1 * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        pygame.draw.rect(SCREEN, color, (c2 * CELL_SIZE, r2 * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        pygame.display.flip()
        pygame.time.delay(100)
