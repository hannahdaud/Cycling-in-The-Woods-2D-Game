import pygame
import random
import sys
import os
import math
import logging  # Added for better debugging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting Bicycle Adventure")

# Initialize pygame
try:
    pygame.init()
    logging.info("Pygame initialized successfully")
except Exception as e:
    logging.error(f"Pygame initialization failed: {e}")
    print(f"Error: Pygame initialization failed: {e}")
    sys.exit(1)

try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
    sound_enabled = True
    logging.info("Sound initialized successfully")
except Exception as e:
    logging.warning(f"Sound initialization failed: {e}")
    print("Sound initialization failed. Running without sound.")
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
    print(f"Error: Display setup failed: {e}")
    sys.exit(1)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
LIGHT_BLUE = (135, 206, 235)

# Game states
MAIN_MENU = 0
LEVEL_1 = 1
GAME_OVER = 4
GAME_WIN = 5

# Define the base path for assets
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    full_path = os.path.join(base_path, relative_path)
    logging.debug(f"Resolving path: {relative_path} -> {full_path}")
    return full_path

# Load background image if available, otherwise set to None
try:
    background_image = pygame.image.load(resource_path("Dark Woods_2.jpg")).convert()
    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    logging.info("Background image loaded: Dark Woods_2.jpg")
except Exception as e:
    logging.warning(f"Failed to load background image: {e}")
    background_image = None

# Clock for controlling game speed
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

def load_animation_frames(image_list, width, height):
    """Load animation frames from a list of file paths."""
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
                print(f"Couldn't load image {image_path}")
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
    sound_files = ["race_music.wav", "collision.wav", "win.wav", "lose.wav"]
    for sound_file in sound_files:
        path = resource_path(sound_file)
        logging.debug(f"Checking sound file: {path}")
        if os.path.exists(path):
            globals()[sound_file.replace(".wav", "_sound")] = pygame.mixer.Sound(path)
            logging.info(f"Loaded sound: {sound_file}")
        else:
            logging.warning(f"Sound file not found: {path}")
            globals()[sound_file.replace(".wav", "_sound")] = None
except Exception as e:
    logging.error(f"Sound files failed to load: {e}")
    print("Sound files not found or failed to load. Running with no sound.")
    level2_music = collision_sound = win_sound = lose_sound = None

# Simple sprite classes for the game entities
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, player_num=1):
        super().__init__()
        self.width = 80
        self.height = 120

        if player_num == 1:
            frame_paths = [
                resource_path(f"Frame{i}_Cycling.png") for i in range(1, 8)
            ]
            self.frames = load_animation_frames(frame_paths, self.width, self.height)
        else:
            surface = pygame.Surface((self.width, self.height))
            surface.fill(RED)
            self.frames = [surface]
            logging.info("Using red rectangle for Player 2")

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
        self.player_num = player_num
        self.crouch = False
        self.crouch_height = 80
        self.normal_height = self.height
        self.foot_offset = 25
        self.wheel_adjustment = 5

        if player_num == 1:
            self.crouch_frames = [
                pygame.transform.scale(frame, (self.width, self.crouch_height))
                for frame in self.frames
            ]
        else:
            crouch_surface = pygame.Surface((self.width, self.crouch_height))
            crouch_surface.fill(RED)
            self.crouch_frames = [crouch_surface]
        logging.info(f"Player {player_num} initialized at ({x}, {y})")

    def update(self, platforms):
        # Animate only when right arrow key is pressed (player 1 only)
        if self.player_num == 1:
            try:
                if pygame.key.get_pressed()[pygame.K_RIGHT]:  # Check right arrow key
                    self.animation_timer += self.animation_speed
                    if self.animation_timer >= 1:
                        self.animation_timer = 0
                        self.current_frame = (self.current_frame + 1) % len(self.frames)
                        logging.debug(f"Player animation frame: {self.current_frame}")
                # Else, keep current frame (no reset to avoid jarring stop)
            except Exception as e:
                logging.error(f"Error checking key press: {e}")
                print(f"Error in key press handling: {e}")

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
            if self.player_num == 1:
                self.image = self.crouch_frames[self.current_frame]
            else:
                self.image = self.crouch_frames[0]
            self.height = self.crouch_height
            old_bottom = self.rect.bottom
            self.rect = self.image.get_rect(x=self.rect.x, bottom=old_bottom)
        else:
            if self.player_num == 1:
                self.image = self.frames[self.current_frame]
            else:
                self.image = self.frames[0]
            self.height = self.normal_height
            if self.on_ground:
                old_bottom = self.rect.bottom
                self.rect = self.image.get_rect(x=self.rect.x, bottom=old_bottom)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, width=50, height=70):
        super().__init__()
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 5
        self.animation_speed = 0.15
        
        placeholder = pygame.Surface((width, height))
        placeholder.fill(WHITE)
        self.frames = [placeholder]
        
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        self.foot_offset = 5

    def update(self, player_x, player_y, platforms):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]

        if self.rect.x < player_x:
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed

        self.rect.y += 5

        on_ground = False
        for platform in platforms:
            if pygame.sprite.collide_rect(self, platform):
                if self.rect.bottom > platform.rect.top and self.rect.centery < platform.rect.centery:
                    self.rect.bottom = platform.rect.top + self.foot_offset
                    on_ground = True

        if not on_ground:
            self.rect.y += 5

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

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
        self.player = None
        self.platforms = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.rightmost_platform_x = 0
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
            
            self.player = Player(100, 300)
            self.platforms = pygame.sprite.Group()
            
            terrain_y = 500  # Fixed height for flat terrain
            platform_width = 120
            initial_terrain_length = 2000
            for x in range(0, initial_terrain_length, platform_width):
                platform = Platform(x, terrain_y, platform_width, 50)
                self.platforms.add(platform)
            
            self.rightmost_platform_x = initial_terrain_length - platform_width
            
            for platform in self.platforms:
                if platform.rect.x == 0:
                    self.player.rect.bottom = platform.rect.top + self.player.foot_offset + self.player.wheel_adjustment
                    break
            
            self.obstacles = pygame.sprite.Group()
            
            self.enemies = pygame.sprite.Group()
            enemy = Enemy(-50, 300)
            frame_paths = [
                resource_path("Frame_0.png"),
                resource_path("Frame_1.png"),
                resource_path("Frame_2.png"),
            ]
            enemy.frames = load_animation_frames(frame_paths, 50, 60)
            self.enemies.add(enemy)
            
            try:
                music_path = resource_path("dark-ambient-51418.wav")
                logging.debug(f"Checking if music file exists: {os.path.exists(music_path)}")
                logging.debug(f"Attempting to load music from: {music_path}")
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

    def start_level2(self):
        def after_fade_out():
            self.state = LEVEL_1
            self.player1 = Player(100, 300, 1)
            self.player2 = Player(100, 300, 2)
            self.finish_line = FinishLine(2800, 100)
            self.platforms = pygame.sprite.Group()
            
            terrain_y = 500
            platform_width = 120
            for x in range(0, 3000, platform_width):
                if x > 0:
                    terrain_y += random.randint(-30, 30)
                    terrain_y = max(300, min(550, terrain_y))
                if random.random() < 0.3:
                    platform = Platform(x, terrain_y, platform_width, 50)
                    self.platforms.add(platform)
                    if random.random() < 0.3:
                        ramp = Platform(x + 50, terrain_y - 20, 30, 20)
                        self.platforms.add(ramp)
                else:
                    platform = Platform(x, terrain_y, platform_width, 50)
                    self.platforms.add(platform)
            
            self.obstacles = pygame.sprite.Group()
            
            if level2_music:
                if self.current_music:
                    self.current_music.stop()
                level2_music.play(-1)
                self.current_music = level2_music

            self.fade_in(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        if self.current_music:
            self.fade_out_music(after_fade_out)
        else:
            after_fade_out()

    def run(self):
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
                                    self.player.speed_y = -10  # Jump when spacebar is pressed
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
        except Exception as e:
            logging.error(f"Game loop crashed: {e}")
            print(f"Error in game loop: {e}")
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
        
        for enemy in self.enemies:
            enemy.update(self.player.rect.x, self.player.rect.y, self.platforms)
        
        platform_width = 120
        generation_threshold = 500
        if self.player.rect.x > self.rightmost_platform_x - generation_threshold:
            last_platform = max(self.platforms, key=lambda p: p.rect.x)
            terrain_y = 500  # Fixed height for flat terrain
            for x in range(self.rightmost_platform_x + platform_width, self.rightmost_platform_x + 1000 + platform_width, platform_width):
                platform = Platform(x, terrain_y, platform_width, 50)
                self.platforms.add(platform)
            self.rightmost_platform_x += 1000
        
        camera_offset_x = self.player.rect.x - SCREEN_WIDTH // 2
        for platform in self.platforms.copy():
            if platform.rect.right < camera_offset_x - 1000:
                self.platforms.remove(platform)
        
        if pygame.sprite.spritecollide(self.player, self.obstacles, False):
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
        
        self.draw_level1()

    def process_level2(self):
        keys = pygame.key.get_pressed()
        self.player1.speed_x = 0
        if keys[pygame.K_LEFT]:
            self.player1.speed_x = -5
        if keys[pygame.K_RIGHT]:
            self.player1.speed_x = 5
        
        self.player2.speed_x = random.uniform(2, 6)
        
        self.player1.update(self.platforms)
        self.player2.update(self.platforms)
        
        if pygame.sprite.spritecollide(self.player1, self.obstacles, False):
            self.player1.speed_x = -2
            if collision_sound:
                collision_sound.play()
        
        if pygame.sprite.spritecollide(self.player2, self.obstacles, False):
            self.player2.speed_x = -2
        
        if pygame.sprite.collide_rect(self.player1, self.finish_line):
            self.state = GAME_WIN
            if self.current_music:
                self.fade_out_music()
            if win_sound:
                win_sound.play()
        
        if pygame.sprite.collide_rect(self.player2, self.finish_line):
            self.state = GAME_OVER
            if self.current_music:
                self.fade_out_music()
            if lose_sound:
                lose_sound.play()
        
        self.draw_level2()

    def draw_main_menu(self):
        screen.fill(BLACK)
        title_text = font_large.render("Bicycle Adventure", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH/2 - title_text.get_width()/2, 150))
        instr_text = font_medium.render("Press SPACE or ENTER to start", True, WHITE)
        screen.blit(instr_text, (SCREEN_WIDTH/2 - instr_text.get_width()/2, 300))
        desc1 = font_small.render("Escape the Forest! Run endlessly!", True, WHITE)
        screen.blit(desc1, (SCREEN_WIDTH/2 - desc1.get_width()/2, 400))
        pygame.display.flip()

    def draw_level1(self):
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill(BLACK)
    
        camera_offset_x = self.player.rect.x - SCREEN_WIDTH // 2
        camera_offset_x = max(0, camera_offset_x)
        
        for platform in self.platforms:
            screen.blit(platform.image, (platform.rect.x - camera_offset_x, platform.rect.y))
        
        for obstacle in self.obstacles:
            screen.blit(obstacle.image, (obstacle.rect.x - camera_offset_x, obstacle.rect.y))
        
        for enemy in self.enemies:
            screen.blit(enemy.image, (enemy.rect.x - camera_offset_x, enemy.rect.y))
        
        screen.blit(self.player.image, (self.player.rect.x - camera_offset_x, self.player.rect.y))
        
        time_elapsed = (pygame.time.get_ticks() - self.level_time) // 1000
        time_text = font_small.render(f"Time: {time_elapsed}s", True, WHITE)
        screen.blit(time_text, (20, 20))
        
        instr_text = font_small.render("← → to move, SPACE to jump, ↓ to crouch", True, WHITE)
        screen.blit(instr_text, (SCREEN_WIDTH - instr_text.get_width() - 20, 20))
        
        pygame.display.flip()

    def draw_level2(self):
        screen.fill(LIGHT_BLUE)
        camera_offset_x = (self.player1.rect.x + self.player2.rect.x) // 2 - SCREEN_WIDTH // 2
        camera_offset_x = max(0, camera_offset_x)
        
        for platform in self.platforms:
            screen.blit(platform.image, (platform.rect.x - camera_offset_x, platform.rect.y))
        
        for obstacle in self.obstacles:
            screen.blit(obstacle.image, (obstacle.rect.x - camera_offset_x, obstacle.rect.y))
        
        screen.blit(self.finish_line.image, (self.finish_line.rect.x - camera_offset_x, self.finish_line.rect.y))
        
        screen.blit(self.player1.image, (self.player1.rect.x - camera_offset_x, self.player1.rect.y))
        screen.blit(self.player2.image, (self.player2.rect.x - camera_offset_x, self.player2.rect.y))
        
        p1_text = font_small.render("P1", True, WHITE)
        screen.blit(p1_text, (self.player1.rect.x - camera_offset_x, self.player1.rect.y - 25))
        
        p2_text = font_small.render("P2", True, WHITE)
        screen.blit(p2_text, (self.player2.rect.x - camera_offset_x, self.player2.rect.y - 25))
        
        instr_text = font_small.render("← → to move, ↑ to jump, ↓ to crouch", True, WHITE)
        screen.blit(instr_text, (SCREEN_WIDTH - instr_text.get_width() - 20, 20))
        
        pygame.display.flip()

    def draw_game_over(self):
        screen.fill(BLACK)
        over_text = font_large.render("Game Over!", True, RED)
        screen.blit(over_text, (SCREEN_WIDTH/2 - over_text.get_width()/2, 200))
        restart_text = font_medium.render("Press SPACE or ENTER to try again", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH/2 - restart_text.get_width()/2, 300))
        pygame.display.flip()

    def draw_win_screen(self):
        screen.fill(BLACK)
        win_text = font_large.render("You Win!", True, GREEN)
        screen.blit(win_text, (SCREEN_WIDTH/2 - win_text.get_width()/2, 200))
        restart_text = font_medium.render("Press SPACE or ENTER to play again", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH/2 - restart_text.get_width()/2, 300))
        pygame.display.flip()

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        logging.error(f"Main program crashed: {e}")
        print(f"Error: Main program crashed: {e}")
        pygame.quit()
        sys.exit(1)