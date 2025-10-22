# enemies.py
import pygame
import math
import random

class Spike:
    def __init__(self, pos, size=60):
        self.pos = pygame.Vector2(pos)
        self.size = size
        self.color = (255, 0, 150)
        self.points = self.generate_spike_points()

    def generate_spike_points(self):
        half_base = self.size / 2
        height = self.size
        return [
            (self.pos.x, self.pos.y - height),
            (self.pos.x - half_base, self.pos.y),
            (self.pos.x + half_base, self.pos.y)
        ]

    def draw(self, surface):
        pygame.draw.polygon(surface, self.color, self.points)

    def collides_with(self, player_pos, player_radius):
        distance = self.pos.distance_to(player_pos)
        return distance < self.size / 1.5 + player_radius

class MovingObject:
    def __init__(self, sprite, size, color, start_pos, direction, speed, lifetime, spin_speed=0):
        self.original_sprite = pygame.transform.scale(sprite.copy(), size)
        self.sprite = self.original_sprite.copy()
        self.color = color
        self.pos = pygame.Vector2(start_pos)
        self.direction = pygame.Vector2(direction).normalize() if direction.length_squared() > 0 else pygame.Vector2(0, 0)
        self.speed = speed
        self.lifetime = lifetime
        self.remaining_life = lifetime
        self.spin_speed = spin_speed
        self.angle = 0
        self.size = size

        if color:
            tint_surface = pygame.Surface(self.sprite.get_size(), pygame.SRCALPHA)
            tint_surface.fill(color)
            self.original_sprite.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def update(self, dt):
        self.remaining_life -= dt
        self.pos += self.direction * self.speed * dt
        self.angle += self.spin_speed * dt

    def draw(self, surface):
        rotated = pygame.transform.rotate(self.original_sprite, -self.angle)
        rect = rotated.get_rect(center=self.pos)
        surface.blit(rotated, rect)

    def is_dead(self):
        return self.remaining_life <= 0

    def collides_with(self, player_pos, player_radius):
        distance = self.pos.distance_to(player_pos)
        return distance < max(self.size) / 2 + player_radius
    
class Piston:
    def __init__(self, start_pos, direction, color, length, width=40, speed=300, delay=1.0, lifetime=None):
        self.base_pos = pygame.Vector2(start_pos)
        self.direction = pygame.Vector2(direction).normalize()
        self.color = color
        self.length = length
        self.width = width
        self.speed = speed
        self.extending = True
        self.progress = 0  # 0 to 1
        self.delay = delay
        self.delay_timer = 0

        # Lifetime management
        self.lifetime = lifetime if lifetime is not None else float('inf')
        self.remaining_life = self.lifetime

        self.done = False

    def update(self, dt):
    
        if self.done:
            return
        # Decrease lifetime
        self.remaining_life -= dt
        if self.remaining_life <= 0:
            self.done = True
            return
        if self.delay_timer > 0:
            self.delay_timer -= dt
            return
        movement = self.speed * dt / self.length
        if self.extending:
            self.progress += movement
            if self.progress >= 1:
                self.progress = 1
                if self.delay == 0:
                    # One-shot piston: stay extended, do nothing more
                    return
                else:
                    self.extending = False
                    self.delay_timer = self.delay
        else:
            self.progress -= movement
            if self.progress <= 0:
                self.progress = 0
                self.extending = True
                self.delay_timer = self.delay

    def get_end_pos(self):
        return self.base_pos + self.direction * self.length * self.progress

    def draw(self, surface):
        if self.done and self.progress == 0:
            return  # Nothing to draw when fully retracted and done

        rect_length = self.length * self.progress
        if rect_length <= 0:
            return
        rect_center = self.base_pos + self.direction * rect_length / 2

        angle = math.atan2(self.direction.y, self.direction.x)
        size = (rect_length, self.width)

        piston_surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(piston_surface, self.color, pygame.Rect(0, 0, *size))

        rotated = pygame.transform.rotate(piston_surface, -math.degrees(angle))
        rect = rotated.get_rect(center=rect_center)
        surface.blit(rotated, rect)

    def collides_with(self, player_pos, player_radius):
        if self.done and self.progress == 0:
            return False

        end = self.get_end_pos()
        start = self.base_pos

        seg_v = end - start
        pt_v = player_pos - start
        seg_len = seg_v.length()
        if seg_len == 0:
            return False
        seg_dir = seg_v / seg_len
        proj = max(0, min(seg_len, pt_v.dot(seg_dir)))
        closest = start + seg_dir * proj
        distance = player_pos.distance_to(closest)

        return distance <= player_radius + self.width / 2
