from sys import exit
import os
import pygame as pg
from pygame._sdl2 import Window
import pygame.locals as loc
import random
import json

import ctypes
# 0 = unaware, 1 = system DPI aware, 2 = per-monitor DPI aware
ctypes.windll.shcore.SetProcessDpiAwareness(1)


class Game():
     
    def __init__(self):
        pg.init()
        pg.mixer.init()
        self.screen = pg.display.set_mode((800, 600))
        self.screen_rect = self.screen.get_rect()
        pg.display.set_caption("Laser_Cat")

        self.clk = pg.time.Clock()

        self.src_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.join(self.src_dir, os.pardir)
        self.media_dir = os.path.join(self.base_dir, "media")
        self.font_dir = os.path.join(self.base_dir, "fonts")
        self.settings_path = os.path.join(self.src_dir, "settings.json")

        self.read_settings()
        
        # load media
        self.bird_scream = pg.mixer.Sound(os.path.join(self.media_dir, "sfx/bird_scream_2.wav"))

        self.cat_normal_img = self.load_image("images/cat_normal.png", self.settings["sprite_scale"])
        self.cat_laser_img = self.load_image("images/cat_laser.png", self.settings["sprite_scale"])
        self.laser_beam_img = self.load_image("images/laser.png", self.settings["sprite_scale"])
        self.background_img = self.load_image("images/background.png", self.settings["sprite_scale"])

        self.sheet_bird_left = self.load_image("images/bird_sprite_sheet.png", self.settings["sprite_scale"])
        self.sheet_bird_right = self.load_image("images/bird_mirrored_sprite_sheet.png", self.settings["sprite_scale"])
        self.sheet_bird_left_death = self.load_image("images/bird_left_death_animation_sprite_sheet.png", self.settings["sprite_scale"])
        self.sheet_bird_right_death = self.load_image("images/bird_right_death_animation_sprite_sheet.png", self.settings["sprite_scale"])

        self.tile_size = 16 * self.settings["sprite_scale"]
        self.default_delay = 150

        self.bird_left_img = []
        for y in range(0, self.sheet_bird_left.get_height(), self.tile_size):
            for x in range(0, self.sheet_bird_left.get_width(), self.tile_size):
                image = pg.Surface((self.tile_size, self.tile_size), pg.SRCALPHA)
                image.blit(self.sheet_bird_left, (0, 0), (x, y, self.tile_size, self.tile_size))
                self.bird_left_img.append((image, self.default_delay))
        
        self.bird_right_img = []
        for y in range(0, self.sheet_bird_right.get_height(), self.tile_size):
            for x in range(0, self.sheet_bird_right.get_width(), self.tile_size):
                image = pg.Surface((self.tile_size, self.tile_size), pg.SRCALPHA)
                image.blit(self.sheet_bird_right, (0, 0), (x, y, self.tile_size, self.tile_size))
                self.bird_right_img.append((image, self.default_delay))
        
        self.bird_left_death_img = []
        for y in range(0, self.sheet_bird_left_death.get_height(), self.tile_size):
            for x in range(0, self.sheet_bird_left_death.get_width(), self.tile_size):
                image = pg.Surface((self.tile_size, self.tile_size), pg.SRCALPHA)
                image.blit(self.sheet_bird_left_death, (0, 0), (x, y, self.tile_size, self.tile_size))
                self.bird_left_death_img.append((image, 50))

        self.bird_right_death_img = []
        for y in range(0, self.sheet_bird_right_death.get_height(), self.tile_size):
            for x in range(0, self.sheet_bird_right_death.get_width(), self.tile_size):
                image = pg.Surface((self.tile_size, self.tile_size), pg.SRCALPHA)
                image.blit(self.sheet_bird_right_death, (0, 0), (x, y, self.tile_size, self.tile_size))
                self.bird_right_death_img.append((image, 50))

        # init fonts
        self.font_10 = pg.font.Font(os.path.join(self.font_dir, "born2bsporty-fs.otf"), 15)
        self.font_20 = pg.font.Font(os.path.join(self.font_dir, "born2bsporty-fs.otf"), 25)
        self.font_25 = pg.font.Font(os.path.join(self.font_dir, "born2bsporty-fs.otf"), 30)
        self.font_30 = pg.font.Font(os.path.join(self.font_dir, "born2bsporty-fs.otf"), 35)
        self.font_40 = pg.font.Font(os.path.join(self.font_dir, "born2bsporty-fs.otf"), 45)
        self.font_50 = pg.font.Font(os.path.join(self.font_dir, "born2bsporty-fs.otf"), 55)

        self.menu_setup()

        # create sprite groups
        self.all_sprites = pg.sprite.Group()
        self.birds = pg.sprite.Group()
        self.lasers = pg.sprite.Group()
        self.backgrounds = pg.sprite.Group()

        # create cat
        self.cat = Cat(self.cat_normal_img, self.cat_laser_img, (300, 455), vel=200)
        #self.cat.add(self.all_sprites)
        self.all_sprites.add(self.cat)

        # create background
        self.background_vel = -20
        background = Background(self.background_img, (0, 0), self.background_vel)
        background.add(self.backgrounds)

        self.controls = {
            "left": self.bind_key(self.settings["controls"]["left"]),
            "right": self.bind_key(self.settings["controls"]["right"]),
            "attack": self.bind_key(self.settings["controls"]["attack"])
        }

        self.show_hitboxes = False

        self.bird_base_vel = 100

        self.dt = 1/60
        self.event_counter = 1

        self.set_init_game_state()
    
    def load_image(self, img_path_from_media, scale):
        surf = pg.image.load(os.path.join(self.media_dir, img_path_from_media))
        surf = pg.transform.scale_by(surf, scale)
        surf = surf.convert_alpha()
        return surf

    def set_init_game_state(self):
        self.game_state = "playing"
        self.running = True
        self.laser_vel = (0, -350)
        self.bird_vel = self.bird_base_vel
        self.score = 0
        self.background_vel = -20
        self.BIRD_SPAWN = pg.USEREVENT + self.event_counter
        self.event_counter += 1
        self.timer_bird_spawn = Timer(2000, self.clk)
        self.timer_attack = Timer(1500, self.clk)
        self.attack_allowed = True
        self.lives = 3
        self.start_time = pg.time.get_ticks()
        for bird in self.birds:
            bird.kill()
        for laser in self.lasers:
            laser.kill()
        self.lasers.empty()

    def run(self):
        while self.running:
            if self.game_state == "reset":
                self.set_init_game_state()
                self.game_state = "playing"
            elif self.game_state == "playing":
                self.change_game_state("playing")
                if self.last_game_state != "playing":
                    # resume timers
                    self.timer_attack.resume(pg.time.get_ticks())
                    self.timer_bird_spawn.resume(pg.time.get_ticks())
                self.playing()
            elif self.game_state == "menu":
                self.change_game_state("menu")
                if self.last_game_state != "menu":
                    self.menu_setup
                    self.timer_attack.pause(pg.time.get_ticks())
                    self.timer_bird_spawn.pause(pg.time.get_ticks())
                self.menu()
            elif self.game_state == "game_over":
                if self.last_game_state != "game_over":
                    self.game_over_setup()
                    self.timer_attack.pause(pg.time.get_ticks())
                    self.timer_bird_spawn.pause(pg.time.get_ticks())
                    if self.settings["highscore"] < self.score:
                        self.settings["highscore"] = self.score
                        self.save_settings()
                self.change_game_state("game_over")
                self.game_over()
            pg.display.flip()
            self.dt = self.clk.tick(self.settings["fps"]) / 1000
        pg.quit()
        exit()

    def menu_setup(self):
        self.menu_text = []
        self.menu_size = (400, 400)
        self.menu_surf = pg.Surface(self.menu_size)
        self.menu_surf_rect = self.menu_surf.get_rect()
        self.menu_surf_rect.center = self.screen_rect.center

        self.text_menu_title = self.get_text(self.font_40, "MENU", pg.color.Color("black"), (0, 20))
        self.text_menu_title[1].centerx = self.menu_size[0] / 2
        self.menu_text.append(self.text_menu_title)

        self.text_controls = self.get_text(self.font_25, "Controls", pg.color.Color("black"), (0, 85))
        self.text_controls[1].right = self.menu_size[0] - 60
        self.menu_text.append(self.text_controls)

        self.text_control_left = self.get_text(self.font_20, "Left", pg.color.Color("black"), (0, 120))
        self.text_control_left[1].left = self.menu_size[0] - 160
        self.menu_text.append(self.text_control_left)

        self.text_control_right = self.get_text(self.font_20, "Right", pg.color.Color("black"), (0, 150))
        self.text_control_right[1].left = self.menu_size[0] - 160
        self.menu_text.append(self.text_control_right)

        self.text_control_attack = self.get_text(self.font_20, "Attack", pg.color.Color("black"), (0, 180))
        self.text_control_attack[1].left = self.menu_size[0] - 160
        self.menu_text.append(self.text_control_attack)

        self.text_restart = self.get_text(self.font_25, "Restart", pg.color.Color("black"), (0, 0))
        self.text_restart[1].bottom = self.menu_size[1] - 20
        self.text_restart[1].left = 30
        self.menu_text.append(self.text_restart)

        self.text_resume = self.get_text(self.font_25, "Resume", pg.color.Color("black"), (0, 0))
        self.text_resume[1].bottom = self.menu_size[1] - 20
        self.text_resume[1].centerx = self.menu_size[0] / 2 - 14
        self.menu_text.append(self.text_resume)

        self.text_exit_game = self.get_text(self.font_25, "Exit Game", pg.color.Color("red4"), (0, 0))
        self.text_exit_game[1].bottom = self.menu_size[1] - 20
        self.text_exit_game[1].right = (self.menu_size[0]) - 30
        self.menu_text.append(self.text_exit_game)
    
    def menu(self):
        self.text_control_left_button = self.get_text(self.font_20, self.settings["controls"]["left"], pg.color.Color("black"), (0, 120))
        self.text_control_left_button[1].right = self.menu_size[0] - 50

        self.text_control_right_button = self.get_text(self.font_20, self.settings["controls"]["right"], pg.color.Color("black"), (0, 150))
        self.text_control_right_button[1].right = self.menu_size[0] - 50

        self.text_control_attack_button = self.get_text(self.font_20, self.settings["controls"]["attack"], pg.color.Color("black"), (0, 180))
        self.text_control_attack_button[1].right = self.menu_size[0] - 50

        # events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                pos = pg.Vector2(pg.mouse.get_pos()) - pg.Vector2(self.menu_surf_rect.topleft)
                if self.text_resume[1].collidepoint(pos):
                    self.game_state = "playing"
                if self.text_restart[1].collidepoint(pos):
                    self.game_state = "reset"
                if self.text_exit_game[1].collidepoint(pos):
                    pg.quit()
                    exit()
                if self.text_resume[1].collidepoint(pos):
                    self.game_state = "playing"
            if event.type == pg.KEYDOWN:
                key = event.key
                if key == loc.K_ESCAPE:
                    self.game_state = "playing"
        
        # draw
        self.menu_surf.fill(pg.color.Color("chocolate3"))
        pg.draw.rect(self.menu_surf, pg.color.Color("chocolate4"), (0, 0, self.menu_surf_rect.width, self.menu_surf_rect.height), 15)
        for text in self.menu_text:
            self.menu_surf.blit(text[0], text[1])
        self.menu_surf.blit(self.text_control_left_button[0], self.text_control_left_button[1])
        self.menu_surf.blit(self.text_control_right_button[0], self.text_control_right_button[1])
        self.menu_surf.blit(self.text_control_attack_button[0], self.text_control_attack_button[1])
        self.screen.blit(self.menu_surf, self.menu_surf_rect)
    
    def playing(self):
        self.handle_inputs()
        self.screen_update()
        self.screen_draw()
    
    def handle_inputs(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.KEYDOWN:
                key = event.key
                if key == self.controls["attack"] and self.attack_allowed:
                    cat_pos = self.cat.get_pos()
                    laser = Laser(self.laser_beam_img, cat_pos, self.laser_vel, self.settings["sprite_scale"])
                    laser.add(self.all_sprites, self.lasers)
                    self.attack_allowed = False
                    self.cat.attack_animation()
                if key == loc.K_h:
                    self.show_hitboxes = True
                if key == loc.K_ESCAPE:
                        self.game_state = "menu"

        keys = pg.key.get_pressed()
        left = False
        right = False
        if keys[self.controls["left"]]:
            left = True
        if keys[self.controls["right"]]:
            right = True
        self.cat.move(left, right)

    def screen_update(self):
        # Timer
        if self.timer_attack.update(pg.time.get_ticks()):
            self.attack_allowed = True
        if self.timer_bird_spawn.update(pg.time.get_ticks()):
            spawn_side_left = random.randint(0, 1)
            height_delta = random.randint(0, 180)
            vel_base = -self.bird_vel - random.randint(0, int(self.bird_vel * 1.5))
            if spawn_side_left:
                pos = (0, 70 + height_delta)
                vel = -vel_base
                img_flying = self.bird_right_img
                img_dying = self.bird_right_death_img
            else:
                pos = (self.screen.get_size()[0], 70 + height_delta)
                vel = vel_base
                img_flying = self.bird_left_img
                img_dying = self.bird_left_death_img
            bird = Bird(img_flying, img_dying, pos, vel, "flying", self.settings["sprite_scale"])
            bird.add(self.birds)

        # Collision Laser, Bird
        collisions = pg.sprite.groupcollide(self.lasers, self.birds, True, False, self.collision_hitbox)
        kills = 0
        for laser in collisions:
            kills += len(collisions[laser])
            for bird in collisions[laser]:
                bird.update_state("dying")
        self.score += kills

        # background
        self.backgrounds.update(self.dt, self.screen_rect)
        most_right = 0
        for bg in self.backgrounds:
            right = bg.get_right_x()
            if right > most_right:
                most_right = right
        if most_right <= 850:
            background = Background(self.background_img, (right, 0), self.background_vel)
            background.add(self.backgrounds)

        # sprites
        self.all_sprites.update(self.dt, self.screen_rect)
        for bird in self.birds:
            if bird.update(self.dt, self.screen_rect) == "killed":
                self.lives -= 1
                if self.lives == 0:
                    self.game_state = "game_over"
                    continue

        # UI
        self.stats_text = self.font_30.render(f"Score: {self.score}  |  Lives: {self.lives}", True, pg.color.Color("black"))
        self.stats_rect = self.stats_text.get_rect()
        self.stats_rect.topleft = (10, 0)

        self.highscore_text = self.font_30.render(f"Highscore: {self.settings["highscore"]}", True, pg.color.Color("black"))
        self.highscore_rect = self.highscore_text.get_rect()
        self.highscore_rect.topright = (self.screen_rect.width - 10, 0)

        # balancing
        time_diff = pg.time.get_ticks() - self.start_time
        self.bird_vel = self.bird_base_vel + (time_diff / 1000)

        # sound
        if kills:
            self.bird_scream.play()

    def screen_draw(self):
        self.screen.fill(pg.Color("aqua"))
        self.backgrounds.draw(self.screen)
        self.all_sprites.draw(self.screen)
        for bird in self.birds:
            bird.draw(self.screen)
        if self.show_hitboxes:
            for bird in self.birds:
                bird.draw_hitbox(self.screen, pg.color.Color("red2"), pg.color.Color("green"))
            for laser in self.lasers:
                laser.draw_hitbox(self.screen, pg.color.Color("red2"), pg.color.Color("green"))
        
        # UI
        self.screen.blit(self.stats_text, self.stats_rect)
        self.screen.blit(self.highscore_text, self.highscore_rect)
    
    def bind_key(self, name):
        return pg.key.key_code(name)

    def collision_hitbox(self, sprite1, sprite2):
        return sprite1.hitbox.colliderect(sprite2.hitbox)

    def get_text(self, font, content, color, pos):
        text = font.render(content, True, color)
        text_rect = text.get_rect()
        text_rect.topleft = pos
        return (text, text_rect)

    def change_game_state(self, new_game_state):
        self.last_game_state = self.game_state
        self.game_state = new_game_state

    def save_settings(self):
        with open(self.settings_path, "w") as file:
            json.dump(self.settings, file, indent=4)

    def read_settings(self):
        with open(self.settings_path, "r") as file:
            self.settings = json.load(file)

    def game_over_setup(self):
        self.game_over_size = (400, 400)
        self.game_over_surf = pg.Surface(self.game_over_size)
        self.game_over_rect = self.game_over_surf.get_rect()
        self.game_over_rect.center = self.screen_rect.center

        self.game_over_texts = []

        self.text_game_over = self.get_text(self.font_40, "Game Over!", pg.color.Color("red4"), (0, 0))
        self.text_game_over[1].top = 20
        self.text_game_over[1].centerx = self.game_over_size[0] / 2
        self.game_over_texts.append(self.text_game_over)

        self.text_score = self.get_text(self.font_25, f"Your score was: {self.score}", pg.color.Color("black"), (0, 0))
        self.text_score[1].top = 100
        self.text_score[1].centerx = self.game_over_size[0] / 2
        self.game_over_texts.append(self.text_score)

        self.text_score = self.get_text(self.font_25, f"Highscore: {self.settings["highscore"]}", pg.color.Color("black"), (0, 0))
        self.text_score[1].top = 150
        self.text_score[1].centerx = self.game_over_size[0] / 2
        self.game_over_texts.append(self.text_score)

        self.text_exit_game = self.get_text(self.font_25, "Exit Game", pg.color.Color("red4"), (0, 0))
        self.text_exit_game[1].bottom = self.game_over_size[1] - 20
        self.text_exit_game[1].right = self.game_over_size[0] - 30
        self.game_over_texts.append(self.text_exit_game)

        self.text_new_game = self.get_text(self.font_25, "New Game", pg.color.Color("green4"), (0, 0))
        self.text_new_game[1].bottom = self.game_over_size[1] - 20
        self.text_new_game[1].left = 30
        self.game_over_texts.append(self.text_new_game)

    def game_over(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                pos = pg.Vector2(pg.mouse.get_pos()) - pg.Vector2(self.game_over_rect.topleft)
                if self.text_new_game[1].collidepoint(pos):
                    self.game_state = "reset"
                if self.text_exit_game[1].collidepoint(pos):
                    self.running = False
        
        # draw
        self.game_over_surf.fill(pg.color.Color("chocolate3"))
        pg.draw.rect(self.game_over_surf, pg.color.Color("chocolate4"), (0, 0, self.game_over_rect.width, self.game_over_rect.height), 15)
        for text in self.game_over_texts:
            self.game_over_surf.blit(text[0], text[1])
        self.screen.blit(self.game_over_surf, self.game_over_rect)


class Cat(pg.sprite.Sprite):
    
    def __init__(self, image_normal, image_laser, pos, vel):
        super().__init__()
        self.images = {"normal": image_normal,
                       "attacking": image_laser}
        self.image = self.images["normal"]
        self.pos = pg.Vector2(pos)
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = self.pos
        self.left = False
        self.right = False
        self.vel = vel
        self.state = "normal"
    
    def update(self, dt, screen_rect):
        if self.left:
            self.pos.x -= self.vel * dt
        if self.right:
            self.pos.x += self.vel * dt
        self.rect.center = self.pos
        if self.state == "attacking":
            if pg.time.get_ticks() - self.last_attack >= 300:
                self.state = "normal"
        self.image = self.images[self.state]

    def move(self, left, right):
        self.left, self.right = left, right
    
    def get_pos(self):
        return self.pos

    def attack_animation(self):
        self.state = "attacking"
        self.last_attack = pg.time.get_ticks()

class Bird(pg.sprite.Sprite):
    
    def __init__(self, images_flying, images_dying, pos, vel, initial_state, scale):
        super().__init__()
        self.images = {
            "flying": images_flying,
            "dying": images_dying
        }
        self.state = initial_state
        self.last_state = "no_state"
        self.animation_update()
        self.pos = pg.Vector2(pos)
        self.rect: pg.Rect = self.images["flying"][0][0].get_rect()
        self.rect.center = self.pos
        self.vel = vel
        self.hitbox_offset = pg.Vector2(1 * scale, 6 * scale)
        self.hitbox = pg.Rect(self.rect.topleft, (14 * scale, 5 * scale))

    def update(self, dt, screen_rect):
        self.pos.x += self.vel *dt
        self.rect.center = self.pos
        self.hitbox.topleft = self.rect.topleft + self.hitbox_offset
        if not self.rect.colliderect(screen_rect):
            self.kill()
            return "killed"
        self.animation_update()
        return None
    
    def animation_update(self):
        if self.state == "flying":
            if self.last_state != "flying":
                self.last_animation = pg.time.get_ticks()
                self.animation_counter = 0
                self.image = self.images["flying"][self.animation_counter]
                self.last_state = "flying"
        elif self.state == "dying":
            if self.last_state != "dying":
                self.last_animation = pg.time.get_ticks()
                self.animation_counter = 0
                self.image = self.images["dying"][self.animation_counter]
                self.last_state = "dying"
        if pg.time.get_ticks() - self.last_animation >= self.image[1]:  # type: ignore
            if self.animation_counter < len(self.images[self.state]) - 1:
                self.animation_counter += 1
            else:
                self.animation_counter = 0
                if self.state == "dying":
                    self.kill()
            self.image = self.images[self.state][self.animation_counter]
            self.last_animation = pg.time.get_ticks()
    
    def update_state(self, new_state):
        self.state = new_state
        self.last_state = self.state
    
    def draw(self, surf):
        surf.blit(self.image[0], self.rect)  # type: ignore

    def draw_hitbox(self, screen, color_hitbox, color_rect):
        pg.draw.rect(screen, color_hitbox, self.hitbox, 2)
        pg.draw.rect(screen, color_rect, self.rect, 2)
    
    def collision(self, type, obj):
        if type == "rect":
            return self.rect.colliderect(obj)


class Laser(pg.sprite.Sprite):
    
    def __init__(self, image, pos, vel, scale):
        super().__init__()
        self.image = image
        self.pos = pg.Vector2(pos)
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = self.pos
        self.vel = pg.Vector2(vel)
        self.hitbox_offset = pg.Vector2(7 * scale, 4 * scale)
        self.hitbox = pg.Rect(self.rect.topleft, (5 * scale, 3 * scale))
    
    def update(self, dt, screen_rect):
        self.pos.y += self.vel.y * dt
        self.pos.x += self.vel.x * dt
        self.rect.center = self.pos
        self.hitbox.topleft = self.rect.topleft + self.hitbox_offset
        if not self.rect.colliderect(screen_rect):
            self.kill()
    
    def draw_hitbox(self, screen, color_hitbox, color_rect):
        pg.draw.rect(screen, color_hitbox, self.hitbox, 2)
        pg.draw.rect(screen, color_rect, self.rect, 2)


class Background(pg.sprite.Sprite):

    def __init__(self, image, pos, vel):
        super().__init__()
        self.image = image
        self.pos = pg.Vector2(pos)
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.topleft = self.pos
        self.vel = vel

    def update(self, dt, screen_rect):
        self.pos.x += self.vel * dt
        self.rect.topleft = self.pos
        if not self.rect.colliderect(screen_rect):
            self.kill()
        
    def get_right_x(self):
        return self.rect.right


class Timer():
    instances = []

    def __init__(self, duration, clock):
        self.duration = duration
        self.clk = clock
        self.last_time = pg.time.get_ticks()
        self.paused = False
        Timer.instances.append(self)

    def pause(self, time):
        self.paused = True
        self.pause_amount = time - self.last_time

    def resume(self, time):
        self.paused = False
        self.last_time = time - self.pause_amount

    def update(self, time):
        if self.paused:
            return False
        else:
            if time >= (self.last_time + self.duration):
                self.last_time = time
                return True
            else:
                return False


if __name__ == "__main__":
    game = Game()
    game.run()
