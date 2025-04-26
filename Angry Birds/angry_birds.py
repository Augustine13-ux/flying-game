import pygame
import pymunk
import math
import sys
import random
import os

# Initialize Pygame and its sound mixer
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)

# Set up the display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Angry Birds")
clock = pygame.time.Clock()

# Load sounds
try:
    launch_sound = pygame.mixer.Sound("launch.wav")
    hit_sound = pygame.mixer.Sound("hit.wav")
    destroy_sound = pygame.mixer.Sound("destroy.wav")
except:
    print("Sound files not found. Game will run without sound.")
    launch_sound = hit_sound = destroy_sound = None

# Set up the physics space
space = pymunk.Space()
space.gravity = (0, 900)

# Bird types
BIRD_TYPES = {
    'red': {'color': RED, 'radius': 20, 'mass': 1, 'special': None},
    'yellow': {'color': YELLOW, 'radius': 20, 'mass': 1, 'special': 'boost'},
    'blue': {'color': BLUE, 'radius': 15, 'mass': 0.8, 'special': 'split'},
    'black': {'color': BLACK, 'radius': 25, 'mass': 1.5, 'special': 'bomb'}
}

class Bird:
    def __init__(self, x, y, bird_type='red'):
        self.type = bird_type
        self.properties = BIRD_TYPES[bird_type]
        self.body = pymunk.Body(self.properties['mass'], 100)
        self.body.position = x, y
        self.shape = pymunk.Circle(self.body, self.properties['radius'])
        self.shape.elasticity = 0.8
        self.shape.friction = 0.7
        self.shape.collision_type = 1
        space.add(self.body, self.shape)
        self.launched = False
        self.original_pos = (x, y)
        self.special_used = False
        self.split_birds = []

    def draw(self):
        pos = self.body.position
        pygame.draw.circle(screen, self.properties['color'], (int(pos.x), int(pos.y)), self.properties['radius'])
        # Draw eyes
        eye_pos = (int(pos.x + 5), int(pos.y - 5))
        pygame.draw.circle(screen, WHITE, eye_pos, 5)
        pygame.draw.circle(screen, BLACK, eye_pos, 2)

    def launch(self, power, angle):
        if not self.launched:
            self.launched = True
            force = power * 1000
            self.body.apply_impulse_at_local_point(
                (force * math.cos(angle), -force * math.sin(angle))
            )
            if launch_sound:
                launch_sound.play()

    def use_special(self):
        if not self.special_used and self.launched:
            if self.properties['special'] == 'boost':
                self.body.velocity = (self.body.velocity.x * 1.5, self.body.velocity.y * 1.5)
            elif self.properties['special'] == 'split':
                self.split()
            elif self.properties['special'] == 'bomb':
                self.explode()
            self.special_used = True

    def split(self):
        if len(self.split_birds) == 0:
            for i in [-1, 1]:
                new_bird = Bird(self.body.position.x, self.body.position.y, 'blue')
                new_bird.body.velocity = (self.body.velocity.x + i*200, self.body.velocity.y)
                self.split_birds.append(new_bird)

    def explode(self):
        for block in blocks:
            distance = math.sqrt((block.body.position.x - self.body.position.x)**2 + 
                               (block.body.position.y - self.body.position.y)**2)
            if distance < 100:
                force = 5000 / (distance + 1)
                angle = math.atan2(block.body.position.y - self.body.position.y,
                                 block.body.position.x - self.body.position.x)
                block.body.apply_impulse_at_local_point(
                    (force * math.cos(angle), force * math.sin(angle))
                )

    def reset(self):
        self.body.position = self.original_pos
        self.body.velocity = (0, 0)
        self.launched = False
        self.special_used = False
        self.split_birds = []

class Block:
    def __init__(self, x, y, width, height, block_type='wood'):
        self.type = block_type
        self.body = pymunk.Body(1, 100)
        self.body.position = x, y
        self.shape = pymunk.Poly.create_box(self.body, (width, height))
        self.shape.elasticity = 0.5
        self.shape.friction = 0.7
        self.shape.collision_type = 2
        space.add(self.body, self.shape)
        self.width = width
        self.height = height
        self.health = 100 if block_type == 'wood' else 200 if block_type == 'stone' else 50
        self.destroyed = False

    def draw(self):
        if not self.destroyed:
            pos = self.body.position
            color = BROWN if self.type == 'wood' else (100, 100, 100) if self.type == 'stone' else GREEN
            points = [
                (pos.x - self.width/2, pos.y - self.height/2),
                (pos.x + self.width/2, pos.y - self.height/2),
                (pos.x + self.width/2, pos.y + self.height/2),
                (pos.x - self.width/2, pos.y + self.height/2)
            ]
            pygame.draw.polygon(screen, color, points)
            # Draw health bar
            health_width = (self.health / 100) * self.width
            pygame.draw.rect(screen, RED, (pos.x - self.width/2, pos.y - self.height/2 - 5, self.width, 3))
            pygame.draw.rect(screen, GREEN, (pos.x - self.width/2, pos.y - self.height/2 - 5, health_width, 3))

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0 and not self.destroyed:
            self.destroyed = True
            if destroy_sound:
                destroy_sound.play()
            return True
        return False

def create_level(level_num):
    blocks = []
    if level_num == 1:
        blocks = [
            Block(600, WINDOW_HEIGHT - 100, 40, 200, 'wood'),
            Block(700, WINDOW_HEIGHT - 100, 40, 200, 'wood'),
            Block(650, WINDOW_HEIGHT - 200, 100, 40, 'wood')
        ]
    elif level_num == 2:
        blocks = [
            Block(600, WINDOW_HEIGHT - 100, 40, 200, 'stone'),
            Block(700, WINDOW_HEIGHT - 100, 40, 200, 'wood'),
            Block(650, WINDOW_HEIGHT - 200, 100, 40, 'wood'),
            Block(600, WINDOW_HEIGHT - 300, 40, 200, 'wood')
        ]
    return blocks

# Game state
current_level = 1
score = 0
birds = [Bird(100, WINDOW_HEIGHT - 100, 'red')]
blocks = create_level(current_level)
current_bird_index = 0

# Game loop
running = True
dragging = False
start_pos = None
power = 0
max_power = 1000

def draw_ui():
    # Draw score
    font = pygame.font.Font(None, 36)
    score_text = font.render(f'Score: {score}', True, BLACK)
    screen.blit(score_text, (10, 50))
    
    # Draw level
    level_text = font.render(f'Level: {current_level}', True, BLACK)
    screen.blit(level_text, (10, 90))
    
    # Draw birds remaining
    birds_text = font.render(f'Birds: {len(birds) - current_bird_index}', True, BLACK)
    screen.blit(birds_text, (10, 130))

def check_level_complete():
    return all(block.destroyed for block in blocks)

def next_level():
    global current_level, blocks, birds, current_bird_index, score
    current_level += 1
    blocks = create_level(current_level)
    birds = [Bird(100, WINDOW_HEIGHT - 100, random.choice(list(BIRD_TYPES.keys())))]
    current_bird_index = 0
    score += 1000

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and not birds[current_bird_index].launched:
            dragging = True
            start_pos = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP and dragging:
            dragging = False
            end_pos = pygame.mouse.get_pos()
            dx = start_pos[0] - end_pos[0]
            dy = start_pos[1] - end_pos[1]
            angle = math.atan2(dy, dx)
            power = min(math.sqrt(dx*dx + dy*dy), max_power)
            birds[current_bird_index].launch(power, angle)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                birds[current_bird_index].reset()
            elif event.key == pygame.K_SPACE:
                birds[current_bird_index].use_special()

    # Update physics
    space.step(1/FPS)

    # Check for collisions and damage
    for bird in birds:
        if bird.launched:
            for block in blocks:
                if not block.destroyed:
                    distance = math.sqrt((block.body.position.x - bird.body.position.x)**2 + 
                                       (block.body.position.y - bird.body.position.y)**2)
                    if distance < 50:
                        if block.take_damage(50):
                            score += 100

    # Check if current bird is out of bounds or stopped
    if birds[current_bird_index].launched:
        pos = birds[current_bird_index].body.position
        vel = birds[current_bird_index].body.velocity
        if (pos.x > WINDOW_WIDTH or pos.y > WINDOW_HEIGHT or 
            (abs(vel.x) < 1 and abs(vel.y) < 1 and pos.y > WINDOW_HEIGHT - 100)):
            current_bird_index += 1
            if current_bird_index >= len(birds):
                if check_level_complete():
                    next_level()
                else:
                    birds = [Bird(100, WINDOW_HEIGHT - 100, random.choice(list(BIRD_TYPES.keys())))]
                    current_bird_index = 0

    # Draw everything
    screen.fill(WHITE)
    
    # Draw background
    pygame.draw.rect(screen, (135, 206, 235), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.draw.rect(screen, (34, 139, 34), (0, WINDOW_HEIGHT - 50, WINDOW_WIDTH, 50))
    
    # Draw slingshot
    pygame.draw.line(screen, BROWN, (50, WINDOW_HEIGHT - 100), (150, WINDOW_HEIGHT - 100), 5)
    
    # Draw power meter if dragging
    if dragging:
        end_pos = pygame.mouse.get_pos()
        pygame.draw.line(screen, BLUE, start_pos, end_pos, 2)
        power = min(math.sqrt((end_pos[0]-start_pos[0])**2 + (end_pos[1]-start_pos[1])**2), max_power)
        power_width = (power / max_power) * 100
        pygame.draw.rect(screen, RED, (10, 10, power_width, 20))

    # Draw game objects
    for bird in birds:
        bird.draw()
    for block in blocks:
        block.draw()

    # Draw UI
    draw_ui()

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit() 