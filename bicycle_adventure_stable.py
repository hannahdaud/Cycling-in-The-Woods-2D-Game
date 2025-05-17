import pygame
import random
import sys
import os
import math
import logging
import platform
import asyncio

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting Bicycle Adventure with Win Condition")

# Initialize pygame
try:
    pygame.init()
    logging.info("Pygame initialized successfully")
except Exception as e:
    logging.error(f"Pygame initialization failed: {e}")
    sys.exit(1)

try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
    sound_enabled = True
    logging.info("Sound initialized successfully")
except Exception as e:
    logging.warning(f"Sound initialization failed: {e}")
    sound_enabled = False

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
try:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Behind His Eyes")
    logging.info("Display set up successfully")
except Exception as e:
    logging.error(f"Display setup failed: {e}")
    sys.exit(1)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)

# Game states
MAIN_MENU = 0
LEVEL_1 = 1
GAME_OVER = 4
GAME_WIN = 5

# Resource path for assets
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    full_path = os.path.join(base_path, relative_path)
    logging.debug(f"Resolving path: {relative_path} -> {full_path}")
    return full_path

# Load background image
try:
    background_image = pygame.image.load(resource_path("Dark Woods_2.jpg")).convert()
    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    logging.info("Background image loaded")
except Exception as e:
    logging.warning(f"Failed to load background image: {e}")
    background_image = None

# Clock for game speed
clock = pygame.time.Clock()
FPS = 60

# Font setup
try:
    font_small = pygame.font.SysFont("Arial", 24)
    font_medium = pygame.font.SysFont("Arial", 36)
    font_large = pygame.font.SysFont("Arial", 48)
    logging.info("Fonts loaded successfully")
except Exception as e:
    logging.warning(f"Font loading failed: {e}")
    font_small = pygame.font.Font(None, 24)
    font_medium = pygame.font.Font(None, 36)
    font_large = pygame.font.Font(None, 48)

# Load animation frames
def load_animation_frames(image_list, width, height):
    frames = []
    for image_path in image_list:
        if os.path.exists(image_path):
            try:
                frame = pygame.image.load(image_path).convert_alpha()
                frame = pygame.transform.scale(frame, (width, height))
                frames.append(frame)
                logging.info(f"Loaded image: {image_path}")
            except pygame.error as e:
                logging.error(f"Couldn't load image {image_path}: {e}")
        else:
            logging.warning(f"Image file not found: {image_path}")
    if not frames:
        placeholder = pygame.Surface((width, height))
        placeholder.fill(WHITE)
        frames = [placeholder]
        logging.info("Using placeholder for missing animation frames")
    return frames

# Load sounds
try:
    sound_files = ["race_music.wav", "collision.wav", "win.wav", "lose.wav", "coin.wav"]
    for sound_file in sound_files:
        path = resource_path(sound_file)
        if os.path.exists(path):
            globals()[sound_file.replace(".wav", "_sound")] = pygame.mixer.Sound(path)
            logging.info(f"Loaded sound: {sound_file}")
        else:
            logging.warning(f"Sound file not found: {path}")
            globals()[sound_file.replace(".wav", "_sound")] = None
except Exception as e:
    logging.error(f"Sound files failed to load: {e}")
    race_music_sound = collision_sound = win_sound = lose_sound = coin_sound = None

# Particle class
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, particle_group):
        super().__init__(particle_group)
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, WHITE, [
            (5, 0), (7, 3), (10, 5), (7, 7), (5, 10), (3, 7), (0, 5), (3, 3)
        ])  # Star shape
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]  # Random direction
        self.lifetime = 30  # Frames to live
        self.alpha = 255  # Initial opacity

    def update(self):
        # Move particle
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # Fade out
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
        else:
            self.alpha = max(0, self.alpha - 8)  # Fade out over time
            self.image.set_alpha(self.alpha)

# Collectible class
class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y, width=30, height=30, particle_group=None):
        super().__init__()
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.2
        self.particle_group = particle_group
        for i in range(7):
            try:
                frame = pygame.image.load(resource_path(f"Coin_Frame_{i}.jpg")).convert_alpha()
                frame = pygame.transform.scale(frame, (width, height))
                self.frames.append(frame)
            except Exception as e:
                logging.warning(f"Failed to load coin frame {i}: {e}")
        if not self.frames:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.circle(self.image, YELLOW, (width // 2, height // 2), width // 2)
        else:
            self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        if self.frames:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]

    def collect(self):
        if self.particle_group is not None:
            for _ in range(10):  # Create 10 particles
                Particle(self.rect.centerx, self.rect.centery, self.particle_group)
        self.kill()

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, game_ref=None):
        super().__init__()
        self.width = 80
        self.height = 120
        frame_paths = [resource_path(f"Frame{i}_Cycling.png") for i in range(1, 8)]
        self.frames = load_animation_frames(frame_paths, self.width, self.height)
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.15
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed_x = 0
        self.speed_y = 0
        self.on_ground = False
        self.crouch = False
        self.crouch_height = 80
        self.normal_height = self.height
        self.foot_offset = 25
        self.wheel_adjustment = 5
        self.dizzy_frames = []
        self.dizzy = False
        self.dizzy_frame_idx = 0
        self.dizzy_timer = 0
        self.dizzy_animation_speed = 0.2
        self.dizzy_loops = 0
        self.dizzy_hits = 0
        self.game_ref = game_ref
        for i in range(9):
            try:
                frame = pygame.image.load(resource_path(f"frame_{i}_delay-0.08s.gif")).convert_alpha()
                frame = pygame.transform.scale(frame, (self.width, self.height))
                self.dizzy_frames.append(frame)
            except Exception as e:
                logging.warning(f"Failed to load dizzy frame {i}: {e}")
        self.crouch_frames = [
            pygame.transform.scale(frame, (self.width, self.crouch_height))
            for frame in self.frames
        ]
        logging.info(f"Player initialized at ({x}, {y})")

    def update(self, platforms):
        if self.dizzy and self.dizzy_frames:
            self.dizzy_timer += self.dizzy_animation_speed
            if self.dizzy_timer >= 1:
                self.dizzy_timer = 0
                self.dizzy_frame_idx = (self.dizzy_frame_idx + 1) % len(self.dizzy_frames)
                if self.dizzy_frame_idx == 0:
                    self.dizzy_loops += 1
                    if self.dizzy_loops >= 2:
                        self.dizzy = False
            return
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.speed_y += 0.5
        self.rect.x += self.speed_x
        if self.rect.left < 0:
            self.rect.left = 0
        self.rect.y += self.speed_y
        self.on_ground = False
        for platform in platforms:
            if pygame.sprite.collide_rect(self, platform):
                if self.speed_y > 0:
                    self.rect.bottom = platform.rect.top + self.foot_offset + self.wheel_adjustment
                    self.on_ground = True
                    self.speed_y = 0
                elif self.speed_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.speed_y = 0
        if self.on_ground:
            platforms_beneath = [
                p for p in platforms
                if self.rect.right > p.rect.left and self.rect.left < p.rect.right
                and abs(self.rect.bottom - (self.foot_offset + self.wheel_adjustment) - p.rect.top) <= 15
            ]
            if platforms_beneath:
                platform_top = min(p.rect.top for p in platforms_beneath)
                self.rect.bottom = platform_top + self.foot_offset + self.wheel_adjustment
        if self.crouch and self.on_ground:
            self.image = self.crouch_frames[self.current_frame]
            self.height = self.crouch_height
            old_bottom = self.rect.bottom
            self.rect = self.image.get_rect(x=self.rect.x, bottom=old_bottom)
        else:
            self.image = self.frames[self.current_frame]
            self.height = self.normal_height
            if self.on_ground:
                old_bottom = self.rect.bottom
                self.rect = self.image.get_rect(x=self.rect.x, bottom=old_bottom)

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, width=50, height=70):
        super().__init__()
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.15
        frame_paths = [resource_path(f"Frame_{i}.png") for i in range(3)]
        self.frames = load_animation_frames(frame_paths, width, height)
        self.image = self.frames[0] if self.frames else pygame.Surface((width, height))
        if not self.frames:
            self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 3
        self.foot_offset = 5
        self.jump_timer = random.randint(60, 120)

    def update(self, player_x, player_y, platforms):
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        dx = player_x - self.rect.x
        if abs(dx) < 300:
            self.rect.x += self.speed if dx > 0 else -self.speed
        self.rect.y += 5
        on_ground = False
        for platform in platforms:
            if pygame.sprite.collide_rect(self, platform):
                if self.rect.bottom > platform.rect.top and self.rect.centery < platform.rect.centery:
                    self.rect.bottom = platform.rect.top + self.foot_offset
                    on_ground = True
        if not on_ground:
            self.rect.y += 5
        self.jump_timer -= 1
        if self.jump_timer <= 0 and on_ground:
            self.rect.y -= 10
            self.jump_timer = random.randint(60, 120)

# Obstacle classes
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class FlyingObstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width=80, height=40, speed=3):
        super().__init__()
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.5
        for i in range(4):
            try:
                frame = pygame.image.load(resource_path(f"frame_{i}_delay-0.2s.png")).convert_alpha()
                frame = pygame.transform.scale(frame, (width, height))
                self.frames.append(frame)
            except Exception as e:
                logging.warning(f"Failed to load flying obstacle frame {i}: {e}")
        if self.frames:
            self.image = self.frames[0]
        else:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed

    def update(self):
        if self.frames:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

class HighFlyingObstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width=80, height=40, speed=3, left_limit=0, right_limit=800, fall_speed=4):
        super().__init__()
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.3
        self.width = width
        self.height = height
        self.speed = speed
        self.left_limit = left_limit
        self.right_limit = right_limit
        self.fall_speed = fall_speed
        self.drop_timer = 0
        self.drop_interval = random.randint(90, 180)
        self.hover_offset_x = 150
        self.hover_height = 80
        self.is_oscillating = False
        self.oscillation_amplitude = 20
        self.oscillation_speed = 0.15
        self.oscillation_phase = 0
        self.oscillation_duration = 60
        self.oscillation_timer = 0
        for i in range(24):
            try:
                frame = pygame.image.load(resource_path(f"frame_{i:02d}_delay-0.05s.gif")).convert_alpha()
                frame = pygame.transform.scale(frame, (width, height))
                self.frames.append(frame)
            except Exception as e:
                logging.warning(f"Failed to load frame {i}: {e}")
        self.image = self.frames[0] if self.frames else pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.base_x = self.rect.x
        self.game_ref = None

    def hover_near_player(self, player_x):
        target_x = player_x + self.hover_offset_x
        self.base_x = target_x
        if not self.is_oscillating:
            self.rect.x = target_x
        self.rect.y = self.hover_height
        if random.random() < 0.01:
            self.is_oscillating = True
            self.oscillation_timer = 0
            self.oscillation_phase = 0
        if self.is_oscillating:
            self.oscillation_timer += 1
            self.oscillation_phase += self.oscillation_speed
            self.rect.x = self.base_x + self.oscillation_amplitude * math.sin(self.oscillation_phase)
            if self.oscillation_timer >= self.oscillation_duration:
                self.is_oscillating = False

    def update(self):
        if self.game_ref and self.game_ref.player:
            self.hover_near_player(self.game_ref.player.rect.x)
        if self.frames:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]
        self.drop_timer += 1
        if self.drop_timer >= self.drop_interval:
            if self.game_ref:
                num_drops = random.randint(1, 3)
                for _ in range(num_drops):
                    offset_x = random.randint(-self.width // 2, self.width // 2)
                    drop_x = self.rect.centerx + offset_x
                    drop_y = self.rect.bottom
                    dropped = DroppedObstacle(drop_x, drop_y)
                    self.game_ref.obstacles.add(dropped)
            self.drop_timer = 0
            self.drop_interval = random.randint(90, 180)

class DroppedObstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width=30, height=30, fall_speed=6):
        super().__init__()
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.25
        for i in range(8):
            try:
                frame = pygame.image.load(resource_path(f"frame_{i}_delay-0.04s.gif")).convert_alpha()
                frame = pygame.transform.scale(frame, (width, height))
                self.frames.append(frame)
            except Exception as e:
                logging.warning(f"Failed to load dropped obstacle frame {i}: {e}")
        if self.frames:
            self.image = self.frames[0]
        else:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (128, 64, 0), [0, 0, width, height])
        self.rect = self.image.get_rect(center=(x, y))
        self.fall_speed = fall_speed
        self.speed_x = random.uniform(-3, 3)

    def update(self):
        if self.frames:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]
        self.rect.x += self.speed_x
        self.rect.y += self.fall_speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.width = width
        self.height = height
        try:
            self.image = pygame.image.load(resource_path("Tile_2.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (width, height))
            logging.info("Loaded platform tile: Tile_2.png")
        except Exception as e:
            logging.error(f"Tile_2.png: {e}")
            self.image = pygame.Surface([width, height])
            self.image.fill(GRAY)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class FinishLine(pygame.sprite.Sprite):
    def __init__(self, x, y, width=20, height=500):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class FireEffect(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.2
        for i in range(16):
            try:
                frame = pygame.image.load(resource_path(f"frame_{i:02d}_delay-0.09s.gif")).convert_alpha()
                frame = pygame.transform.scale(frame, (30, 30))
                self.frames.append(frame)
            except Exception as e:
                logging.warning(f"Failed to load fire frame {i}: {e}")
        if not self.frames:
            placeholder = pygame.Surface((30, 30))
            placeholder.fill(RED)
            self.frames = [placeholder]
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.lifetime = 20

    def update(self):
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

class Game:
    def __init__(self):
        self.state = MAIN_MENU
        self.level_time = 0
        self.current_music = None
        self.fade_start_time = 0
        self.is_fading_in = False
        self.is_fading_out = False
        self.fade_duration = 3000
        self.fade_callback = None
        self.player = Player(100, 300, game_ref=self)
        self.platforms = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        self.particle_group = pygame.sprite.Group()  # New: Particle group for collectible effects
        self.finish_line = None
        self.rightmost_platform_x = 0
        self.fire_effects = pygame.sprite.Group()
        self.last_flying_obstacle_time = pygame.time.get_ticks()
        self.score = 0
        self.high_score = 0
        self.shake_timer = 0
        self.shake_intensity = 10
        self.level_time = None
        logging.info("Game object initialized")

    def fade_in_music(self):
        logging.info("Fade-in started")
        self.is_fading_in = True
        self.is_fading_out = False
        self.fade_start_time = pygame.time.get_ticks()
        pygame.mixer.music.set_volume(0.0)
        pygame.mixer.music.play(-1)

    def fade_out_music(self, callback=None):
        logging.info("Fade-out started")
        self.is_fading_out = True
        self.is_fading_in = False
        self.fade_start_time = pygame.time.get_ticks()
        self.fade_callback = callback

    def update_fade(self):
        current_time = pygame.time.get_ticks()
        if self.is_fading_in:
            elapsed = current_time - self.fade_start_time
            if elapsed < self.fade_duration:
                volume = elapsed / self.fade_duration
                pygame.mixer.music.set_volume(volume)
            else:
                pygame.mixer.music.set_volume(1.0)
                self.is_fading_in = False
                logging.info("Fade-in complete")
        elif self.is_fading_out:
            elapsed = current_time - self.fade_start_time
            if elapsed < self.fade_duration:
                volume = 1.0 - (elapsed / self.fade_duration)
                pygame.mixer.music.set_volume(max(volume, 0))
            else:
                pygame.mixer.music.stop()
                pygame.mixer.music.set_volume(1.0)
                self.is_fading_out = False
                logging.info("Fade-out complete")
                if self.fade_callback is not None:
                    self.fade_callback()
                    self.fade_callback = None

    def fade_in(self, width, height):
        fade_surface = pygame.Surface((width, height))
        fade_surface.fill((0, 0, 0))
        for alpha in reversed(range(0, 256)):
            fade_surface.set_alpha(alpha)
            self.draw_current_state()
            screen.blit(fade_surface, (0, 0))
            pygame.display.update()
            pygame.time.delay(5)

    def draw_current_state(self):
        if self.state == MAIN_MENU:
            self.draw_main_menu()
        elif self.state == LEVEL_1:
            self.draw_level1()
        elif self.state == GAME_OVER:
            self.draw_game_over()
        elif self.state == GAME_WIN:
            self.draw_win_screen()
        else:
            screen.fill(BLACK)
            pygame.display.flip()

    def start_level1(self):
        def after_fade_out():
            logging.info("Starting Level 1")
            self.state = LEVEL_1
            self.level_time = pygame.time.get_ticks()
            self.win_time = None
            self.score = 0
            self.player = Player(100, 300, game_ref=self)
            self.platforms = pygame.sprite.Group()
            self.particle_group = pygame.sprite.Group()  # New: Reset particle group
            self.high_flying_obstacle = HighFlyingObstacle(
                x=0, y=80, width=80, height=40, speed=3, left_limit=0, right_limit=SCREEN_WIDTH
            )
            self.high_flying_obstacle.game_ref = self
            self.obstacles.add(self.high_flying_obstacle)
            terrain_y = 500
            platform_width = 120
            level_length = 5000
            for x in range(0, level_length, platform_width):
                platform = Platform(x, terrain_y, platform_width, 50)
                self.platforms.add(platform)
                if random.random() < 0.2:
                    collectible = Collectible(x + platform_width // 2, terrain_y - 40, particle_group=self.particle_group)
                    self.collectibles.add(collectible)
            self.rightmost_platform_x = level_length - platform_width
            self.finish_line = FinishLine(level_length, 100)
            for platform in self.platforms:
                if platform.rect.x == 0:
                    self.player.rect.bottom = platform.rect.top + self.player.foot_offset + self.player.wheel_adjustment
                    break
            self.enemies = pygame.sprite.Group()
            enemy = Enemy(-50, 300)
            self.enemies.add(enemy)
            try:
                music_path = resource_path("dark-ambient-51418.wav")
                pygame.mixer.music.load(music_path)
                self.fade_in_music()
                self.current_music = pygame.mixer.music
            except pygame.error as e:
                logging.error(f"Failed to load or play music: {e}")
                self.current_music = None
                self.is_fading_in = False
            self.fade_in(SCREEN_WIDTH, SCREEN_HEIGHT)
        if self.current_music:
            self.fade_out_music(after_fade_out)
        else:
            after_fade_out()

    async def run(self):
        running = True
        logging.info("Entering main game loop")
        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        if self.state == MAIN_MENU:
                            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                                self.start_level1()
                        elif self.state == GAME_OVER or self.state == GAME_WIN:
                            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                                self.__init__()
                        elif self.state == LEVEL_1:
                            if event.key == pygame.K_DOWN:
                                if hasattr(self, 'player'):
                                    self.player.crouch = True
                            if event.key == pygame.K_SPACE and hasattr(self, 'player'):
                                if self.player.on_ground:
                                    self.player.speed_y = -10
                                    self.player.on_ground = False
                    if event.type == pygame.KEYUP:
                        if self.state == LEVEL_1:
                            if event.key == pygame.K_DOWN:
                                if hasattr(self, 'player'):
                                    self.player.crouch = False
                self.update_fade()
                if self.state == MAIN_MENU:
                    self.draw_main_menu()
                elif self.state == LEVEL_1:
                    self.process_level1()
                elif self.state == GAME_OVER:
                    self.draw_game_over()
                elif self.state == GAME_WIN:
                    self.draw_win_screen()
                clock.tick(FPS)
                await asyncio.sleep(1.0 / FPS)
        except Exception as e:
            logging.error(f"Game loop crashed: {e}")
            raise
        finally:
            pygame.quit()
            logging.info("Pygame quit")

    def process_level1(self):
        keys = pygame.key.get_pressed()
        self.player.speed_x = 0
        if keys[pygame.K_LEFT]:
            self.player.speed_x = -5
        if keys[pygame.K_RIGHT]:
            self.player.speed_x = 5
        self.player.update(self.platforms)
        self.fire_effects.update()
        self.collectibles.update()
        self.particle_group.update()  # New: Update particle group
        for enemy in self.enemies:
            enemy.update(self.player.rect.x, self.player.rect.y, self.platforms)
        camera_offset_x = self.player.rect.x - SCREEN_WIDTH // 2
        camera_offset_x = max(0, camera_offset_x)
        now = pygame.time.get_ticks()
        if now - self.last_flying_obstacle_time > 3000 and self.player.rect.x < 4000:
            fly_y = 400
            flying_obstacle = FlyingObstacle(self.player.rect.x + 900, fly_y, width=80, height=40)
            self.obstacles.add(flying_obstacle)
            self.last_flying_obstacle_time = now
        for obstacle in self.obstacles:
            if hasattr(obstacle, "update"):
                obstacle.update()
        for obstacle in self.obstacles:
            if pygame.sprite.collide_rect(self.player, obstacle):
                if isinstance(obstacle, (FlyingObstacle, DroppedObstacle)):
                    if not self.player.crouch:
                        if self.player.dizzy_hits == 0:
                            self.player.dizzy = True
                            self.player.dizzy_frame_idx = 0
                            self.player.dizzy_timer = 0
                            self.player.dizzy_loops = 0
                            self.player.dizzy_hits += 1
                            if collision_sound:
                                collision_sound.play()
                            self.shake_timer = 20
                            obstacle.kill()
                        else:
                            if collision_sound:
                                collision_sound.play()
                            self.state = GAME_OVER
                            if self.current_music:
                                self.fade_out_music()
                            if lose_sound:
                                lose_sound.play()
                            obstacle.kill()
                else:
                    if collision_sound:
                        collision_sound.play()
                    self.state = GAME_OVER
                    if self.current_music:
                        self.fade_out_music()
                    if lose_sound:
                        lose_sound.play()
        if pygame.sprite.spritecollide(self.player, self.enemies, False):
            if collision_sound:
                collision_sound.play()
            self.state = GAME_OVER
            if self.current_music:
                self.fade_out_music()
            if lose_sound:
                lose_sound.play()
        collected = pygame.sprite.spritecollide(self.player, self.collectibles, False)
        for collectible in collected:
            collectible.collect()  # New: Trigger collect method
            self.score += 100
            if coin_sound:
                coin_sound.play()
        self.score += int(self.player.speed_x * 0.1)
        self.high_score = max(self.high_score, self.score)
        if self.shake_timer > 0:
            self.shake_timer -= 1
        if self.finish_line and pygame.sprite.collide_rect(self.player, self.finish_line):
            self.win_time = (pygame.time.get_ticks() - self.level_time) // 1000
            self.state = GAME_WIN
            if self.current_music:
                self.fade_out_music()
            if win_sound:
                win_sound.play()
        self.draw_level1()

    def draw_main_menu(self):
        screen.fill(BLACK)
        title_text = font_large.render("Bicycle Adventure", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH / 2 - title_text.get_width() / 2, 150))
        instr_text = font_medium.render("Press SPACE or ENTER to start", True, WHITE)
        screen.blit(instr_text, (SCREEN_WIDTH / 2 - instr_text.get_width() / 2, 300))
        desc1 = font_small.render("Escape the Forest! Reach the Finish Line!", True, WHITE)
        screen.blit(desc1, (SCREEN_WIDTH / 2 - desc1.get_width() / 2, 400))
        pygame.display.flip()

    def draw_level1(self):
        camera_offset_x = self.player.rect.x - SCREEN_WIDTH // 2
        camera_offset_x = max(0, camera_offset_x)
        shake_offset_x = 0
        shake_offset_y = 0
        if self.shake_timer > 0:
            shake_offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_offset_y = random.randint(-self.shake_intensity, self.shake_intensity)
        if background_image:
            screen.blit(background_image, (shake_offset_x, shake_offset_y))
        else:
            screen.fill(BLACK)
        for platform in self.platforms:
            screen.blit(platform.image, (platform.rect.x - camera_offset_x + shake_offset_x, platform.rect.y + shake_offset_y))
        for collectible in self.collectibles:
            screen.blit(collectible.image, (collectible.rect.x - camera_offset_x + shake_offset_x, collectible.rect.y + shake_offset_y))
        for particle in self.particle_group:  # New: Draw particles
            screen.blit(particle.image, (particle.rect.x - camera_offset_x + shake_offset_x, particle.rect.y + shake_offset_y))
        for obstacle in self.obstacles:
            screen.blit(obstacle.image, (obstacle.rect.x - camera_offset_x + shake_offset_x, obstacle.rect.y + shake_offset_y))
        for enemy in self.enemies:
            screen.blit(enemy.image, (enemy.rect.x - camera_offset_x + shake_offset_x, enemy.rect.y + shake_offset_y))
        for fire_effect in self.fire_effects:
            screen.blit(fire_effect.image, (fire_effect.rect.x - camera_offset_x + shake_offset_x, fire_effect.rect.y + shake_offset_y))
        screen.blit(self.player.image, (self.player.rect.x - camera_offset_x + shake_offset_x, self.player.rect.y + shake_offset_y))
        if self.finish_line:
            screen.blit(self.finish_line.image, (self.finish_line.rect.x - camera_offset_x + shake_offset_x, self.finish_line.rect.y + shake_offset_y))
        if self.player.dizzy and self.player.dizzy_frames:
            dizzy_img = self.player.dizzy_frames[self.player.dizzy_frame_idx]
            dizzy_x = self.player.rect.x - camera_offset_x + (self.player.rect.width - dizzy_img.get_width()) // 2 + shake_offset_x
            dizzy_y = self.player.rect.y - 10 + shake_offset_y
            screen.blit(dizzy_img, (dizzy_x, dizzy_y))
        time_elapsed = (pygame.time.get_ticks() - self.level_time) // 1000
        time_text = font_small.render(f"Time: {time_elapsed}s", True, WHITE)
        screen.blit(time_text, (20 + shake_offset_x, 20 + shake_offset_y))
        score_text = font_small.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (20 + shake_offset_x, 50 + shake_offset_y))
        high_score_text = font_small.render(f"High Score: {self.high_score}", True, WHITE)
        screen.blit(high_score_text, (20 + shake_offset_x, 80 + shake_offset_y))
        instr_text = font_small.render("← → to move, SPACE to jump, ↓ to crouch", True, WHITE)
        screen.blit(instr_text, (SCREEN_WIDTH - instr_text.get_width() - 20 + shake_offset_x, 20 + shake_offset_y))
        pygame.display.flip()

    def draw_game_over(self):
        screen.fill(BLACK)
        over_text = font_large.render("Game Over!", True, RED)
        screen.blit(over_text, (SCREEN_WIDTH / 2 - over_text.get_width() / 2, 200))
        score_text = font_medium.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH / 2 - score_text.get_width() / 2, 280))
        high_score_text = font_medium.render(f"High Score: {self.high_score}", True, WHITE)
        screen.blit(high_score_text, (SCREEN_WIDTH / 2 - high_score_text.get_width() / 2, 320))
        restart_text = font_medium.render("Press SPACE or ENTER to play again", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH / 2 - restart_text.get_width() / 2, 360))
        pygame.display.flip()

    def draw_win_screen(self):
        screen.fill(BLACK)
        win_text = font_large.render("You Win!", True, GREEN)
        screen.blit(win_text, (SCREEN_WIDTH / 2 - win_text.get_width() / 2, 200))
        minutes = self.win_time // 60
        seconds = self.win_time % 60
        time_text = font_medium.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
        screen.blit(time_text, (SCREEN_WIDTH / 2 - time_text.get_width() / 2, 240))
        score_text = font_medium.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH / 2 - score_text.get_width() / 2, 280))
        high_score_text = font_medium.render(f"High Score: {self.high_score}", True, WHITE)
        screen.blit(high_score_text, (SCREEN_WIDTH / 2 - high_score_text.get_width() / 2, 320))
        restart_text = font_medium.render("Press SPACE or ENTER to try again", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH / 2 - restart_text.get_width() / 2, 360))
        pygame.display.flip()

async def main():
    game = Game()
    await game.run()

if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.ensure_future(main())
    else:
        asyncio.run(main())