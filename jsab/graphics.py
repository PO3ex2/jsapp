
# graphics.py
import pygame
import math
import random

BLUE = (0, 200, 255)

class Particle:
    def __init__(self, pos, vel, lifetime, color, radius):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.radius = radius

    def update(self, dt):
        self.pos += self.vel * dt
        self.lifetime -= dt

    def draw(self, surface):
        alpha = max(0, int(255 * (self.lifetime / self.max_lifetime)))
        faded_color = (*self.color, alpha)
        surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, faded_color, (self.radius, self.radius), self.radius)
        surface.blit(surf, (self.pos.x - self.radius, self.pos.y - self.radius))

    def is_dead(self):
        return self.lifetime <= 0

def draw_player(screen, pos, is_dashing, dash_dir, invincible, radius):
    base_size = radius * 2
    squish_factor = 1.5

    if is_dashing and dash_dir.length_squared() > 0:
        stretch_dir = dash_dir.normalize()
        angle = math.atan2(stretch_dir.y, stretch_dir.x)
        scale_x = base_size * squish_factor
        scale_y = base_size / squish_factor
    else:
        scale_x = base_size
        scale_y = base_size
        angle = 0

    current_time = pygame.time.get_ticks()
    blink_on = (current_time // 100) % 2 == 0
    color = (255, 60, 60) if invincible and blink_on else BLUE

    player_surface = pygame.Surface((base_size, base_size), pygame.SRCALPHA)
    pygame.draw.circle(player_surface, color, (radius, radius), radius)
    scaled_surface = pygame.transform.smoothscale(player_surface, (int(scale_x), int(scale_y)))
    rotated_surface = pygame.transform.rotate(scaled_surface, -math.degrees(angle))
    rect = rotated_surface.get_rect(center=(int(pos.x), int(pos.y)))
    screen.blit(rotated_surface, rect)
