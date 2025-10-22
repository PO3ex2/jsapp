# main.py
import pygame
import sys
import random
import re
import math
import json
from enemies import MovingObject, Piston
from graphics import Particle, draw_player

# Setup
pygame.init()
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("JSAB Player Controller")
clock = pygame.time.Clock()

# Assets
try:
    spike_img = pygame.image.load("jsab/assets/spike_ball_full.png").convert_alpha()
except:
    spike_img = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.polygon(spike_img, (255, 0, 150), [(20, 0), (0, 40), (40, 40)])

# Colors and fonts
WHITE = (255, 255, 255)
BLUE = (0, 200, 255)
font = pygame.font.SysFont("Arial", 36)

# Game state
player_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
player_vel = pygame.Vector2(0, 0)
player_speed = 125
friction = 0.75
radius = 20
player_health = 3
invincible = False
invincible_time = 1500
last_hit_time = 0
knockback_strength = 50
dashing = False
dash_cooldown = 500
last_dash_time = 0
dash_duration = 150
dash_speed = 20
dash_direction = pygame.Vector2(0, 0)


level_start_time = pygame.time.get_ticks()
event_index = 0

particles = []
moving_objects = []
pistons = []

#Level Loader
def parse_random_value(value):
    if isinstance(value, str):
        match = re.match(r'random\(([^,]+),\s*([^)]+)\)', value)
        if match:
            low = float(match.group(1))
            high = float(match.group(2))
            return random.uniform(low, high)
    return value

def parse_random_in_data(data):
    if isinstance(data, list):
        return [parse_random_in_data(x) for x in data]
    elif isinstance(data, dict):
        return {k: parse_random_in_data(v) for k, v in data.items()}
    else:
        return parse_random_value(data)

def load_level(path):
    with open(path, "r") as f:
        data = json.load(f)
    return sorted(data, key=lambda e: e["time"])

# Input & Dash
def get_input():
    keys = pygame.key.get_pressed()
    direction = pygame.Vector2(0, 0)
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        direction.y = -1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        direction.y += 1
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        direction.x = -1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        direction.x += 1
    if direction.length() > 0:
        direction = direction.normalize()
    return direction

def dash(direction):
    global dashing, last_dash_time, dash_direction
    if direction.length_squared() == 0:
        direction = pygame.Vector2(1, 0)
    dashing = True
    dash_direction = direction
    last_dash_time = pygame.time.get_ticks()

def spawn_trail_particles():
    move_dir = player_vel.normalize() if player_vel.length_squared() > 0 else pygame.Vector2(0, 0)
    for _ in range(2):
        base_speed = -move_dir * random.uniform(30, 60)
        perpendicular = pygame.Vector2(-move_dir.y, move_dir.x)
        spread = perpendicular * random.uniform(-40, 40)
        vel = base_speed + spread
        lifetime = random.uniform(0.1, 0.4)
        size = random.randint(3, 6)
        p = Particle(player_pos, vel, lifetime, BLUE, size)
        particles.append(p)

# Game loop
while True:
    level_events = load_level("jsab/levels/level1.json")
    level_events = parse_random_in_data(level_events)
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k:
                obj = MovingObject(
                    sprite=spike_img,
                    size=(60, 60),
                    color=(255, 0, 150),
                    start_pos=(WIDTH // 2, HEIGHT // 2),
                    direction=pygame.Vector2(1, 0).rotate(random.randint(0, 360)),
                    speed=random.randint(100, 360),
                    lifetime=5.0,
                    spin_speed=180
                )
                moving_objects.append(obj)
            elif event.key == pygame.K_l:
                pistons.append(Piston(
                    start_pos=(0, random.randint(0, HEIGHT)),
                    direction=pygame.Vector2(1, 0).rotate(0),
                    color=(255, 0, 150),
                    length=WIDTH,
                    width=50,
                    speed=15000,
                    lifetime=1,
                    delay=0
                ))

    direction = get_input()
    current_time = pygame.time.get_ticks()

    elapsed = (current_time - level_start_time) / 1000  # convert to seconds

    while event_index < len(level_events) and level_events[event_index]["time"] <= elapsed:
        event = level_events[event_index]
        etype = event["type"]
        if etype == "moving_object":
            angle = event.get("direction_angle", 0)
            obj_dir = pygame.Vector2(1, 0).rotate(angle)
            mo = MovingObject(
                sprite=spike_img,
                size=(60, 60),
                color=event.get("color", (255,0,150)),
                start_pos=tuple(event["pos"]),
                direction=obj_dir,
                speed=event.get("speed", 100),
                lifetime=event.get("lifetime", 5.0),
                spin_speed=event.get("spin_speed", 0)
            )
            moving_objects.append(mo)
        elif etype == "piston":
            pistons.append(Piston(
                start_pos=tuple(event["pos"]),
                direction=pygame.Vector2(event["direction"]),
                color=event.get("color", (255,0,150)),
                length=event["length"],
                width=event.get("width", 40),
                speed=event.get("speed", 300),
                lifetime=event.get("lifetime", None),
                delay=event.get("delay", 1.0)
            ))

        event_index += 1

    if not dashing and current_time - last_dash_time > dash_cooldown:
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            dash(direction)

    if dashing:
        if current_time - last_dash_time < dash_duration:
            player_vel = dash_direction * dash_speed
            invincible = True
        else:
            dashing = False
            invincible = False
    else:
        player_vel += direction * player_speed * dt
        player_vel *= friction

    player_pos += player_vel
    player_pos.x = max(radius, min(WIDTH - radius, player_pos.x))
    player_pos.y = max(radius, min(HEIGHT - radius, player_pos.y))

    for obj in moving_objects:
        obj.update(dt)
    moving_objects = [obj for obj in moving_objects if not obj.is_dead()]

    for piston in pistons:
        piston.update(dt)
    
    pistons = [p for p in pistons if not p.done]

    if player_vel.length_squared() > 10 or dashing:
        spawn_trail_particles()

    if not invincible:
        for obj in moving_objects:
            if obj.collides_with(player_pos, radius):
                player_health -= 1
                invincible = True
                last_hit_time = pygame.time.get_ticks()
                knockback_dir = (player_pos - obj.pos).normalize()
                player_vel = knockback_dir * knockback_strength
                break
        for piston in pistons:
            if piston.collides_with(player_pos, radius):
                player_health -= 1
                invincible = True
                last_hit_time = pygame.time.get_ticks()
                knockback_dir = (player_pos - piston.base_pos).normalize()
                player_vel = knockback_dir * knockback_strength
                break


    if invincible and current_time - last_hit_time > invincible_time:
        invincible = False

    for p in particles:
        p.update(dt)
    particles = [p for p in particles if not p.is_dead()]

    screen.fill((20, 20, 30))
    for p in particles:
        p.draw(screen)
    for obj in moving_objects:
        obj.draw(screen)
    for piston in pistons:
        piston.draw(screen)
    draw_player(screen, player_pos, dashing, dash_direction, invincible, radius)

    health_text = font.render(f"Health: {player_health}", True, (255, 100, 100))
    time_text = font.render(f"Time: {elapsed}", True, (255, 200, 200))
    screen.blit(health_text, (30, 30))
    screen.blit(time_text, (30, 60))

    pygame.display.flip()

