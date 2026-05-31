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
        self.screen = pg.display.set_mode((800, 600))
        self.screen_rect = self.screen.get_rect()
        pg.display.set_caption("Laser_Cat")

        self.clk = pg.time.Clock()

        self.src_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.join(self.src_dir, os.pardir)
        self.media_dir = os.path.join(self.base_dir, "media")
        self.font_dir = os.path.join(self.base_dir, "fonts")
        self.settings_path = os.path.join(self.src_dir, "settings.json")

        with open(self.settings_path) as file:
            self.settings = json.load(file)
        
        # load media
        self.cat_normal_img = self.load_image("images/cat_normal.png", self.settings["sprite_scale"])
        self.cat_laser_img = self.load_image("images/cat_laser.png", self.settings["sprite_scale"])
        self.laser_beam_img = self.load_image("images/laser.png", self.settings["sprite_scale"])
        self.bird_left_img = self.load_image("images/bird_left.png", self.settings["sprite_scale"])
        self.bird_right_img = self.load_image("images/bird_right.png", self.settings["sprite_scale"])
        self.background_img = self.load_image("images/background.png", self.settings["sprite_scale"])

        # init fonts
        self.font_10 = pg.font.Font(os.path.join(self.font_dir, "Ldfcomicsansbold-zgma.ttf"), 30)
        self.font_20 = pg.font.Font(os.path.join(self.font_dir, "Ldfcomicsansbold-zgma.ttf"), 30)
        self.font_30 = pg.font.Font(os.path.join(self.font_dir, "Ldfcomicsansbold-zgma.ttf"), 30)
        self.font_40 = pg.font.Font(os.path.join(self.font_dir, "Ldfcomicsansbold-zgma.ttf"), 30)
        self.font_50 = pg.font.Font(os.path.join(self.font_dir, "Ldfcomicsansbold-zgma.ttf"), 30)

        # create sprite groups
        self.all_sprites = pg.sprite.Group()
        self.birds = pg.sprite.Group()
        self.lasers = pg.sprite.Group()
        self.backgrounds = pg.sprite.Group()

        # create cat
        self.cat = Cat(self.cat_normal_img, (300, 450), vel=200)
        #self.cat.add(self.all_sprites)
        self.all_sprites.add(self.cat)

        # create background
        self.background_vel = -20
        background = Background(self.background_img, (0, 0), self.background_vel)
        background.add(self.backgrounds)

        self.controls = {
            "left": self.bind_key(self.settings["controls"]["left"]),
            "right": self.bind_key(self.settings["controls"]["right"]),
            "shoot": self.bind_key(self.settings["controls"]["shoot"])
        }

        self.show_hitboxes = False

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
        self.laser_vel = (0, -300)
        self.bird_vel = 50
        self.score = 0
        self.background_vel = -20
        self.BIRD_SPAWN = pg.USEREVENT + self.event_counter
        self.event_counter += 1
        pg.time.set_timer(self.BIRD_SPAWN, 4000)

    def run(self):
        while True:
            if self.game_state == "playing":
                self.playing()
    
    def playing(self):
        while self.game_state == "playing":
            self.handle_inputs()
            self.screen_update()
            self.screen_draw()
            self.dt = self.clk.tick(self.settings["fps"]) / 1000
    
    def handle_inputs(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            if event.type == self.BIRD_SPAWN:
                spawn_side_left = random.randint(0, 1)
                if spawn_side_left:
                    pos = (0, 100)
                    vel = self.bird_vel
                    img = self.bird_right_img
                else:
                    pos = (self.screen.get_size()[0], 100)
                    vel = -self.bird_vel
                    img = self.bird_left_img
                bird = Bird(img, pos, vel, self.settings["sprite_scale"])
                bird.add(self.all_sprites, self.birds)
            if event.type == pg.KEYDOWN:
                key = event.key
                if key == self.controls["shoot"]:
                    cat_pos = self.cat.get_pos()
                    laser = Laser(self.laser_beam_img, cat_pos, self.laser_vel, self.settings["sprite_scale"])
                    laser.add(self.all_sprites, self.lasers)
                if key == loc.K_h:
                    self.show_hitboxes = True
        keys = pg.key.get_pressed()
        left = False
        right = False
        if keys[self.controls["left"]]:
            left = True
        if keys[self.controls["right"]]:
            right = True
        self.cat.move(left, right)

    def screen_update(self):
        # Collision Laser, Bird
        collisions = pg.sprite.groupcollide(self.lasers, self.birds, True, True, self.collision_hitbox)
        kills = 0
        for laser in collisions:
            kills += len(collisions[laser])
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

        # UI
        self.score_text = self.font_30.render(f"Score: {self.score}", True, pg.color.Color("black"))
        self.score_rect = self.score_text.get_rect()
        self.score_rect.topleft = (10, 10)

    def screen_draw(self):
        self.screen.fill(pg.Color("aqua"))
        self.backgrounds.draw(self.screen)
        self.all_sprites.draw(self.screen)
        if self.show_hitboxes:
            for bird in self.birds:
                bird.draw_hitbox(self.screen, pg.color.Color("red2"), pg.color.Color("green"))
            for laser in self.lasers:
                laser.draw_hitbox(self.screen, pg.color.Color("red2"), pg.color.Color("green"))
        
        # UI
        self.screen.blit(self.score_text, self.score_rect)

        pg.display.flip()
    
    def bind_key(self, name):
        return pg.key.key_code(name)

    def collision_hitbox(self, sprite1, sprite2):
        return sprite1.hitbox.colliderect(sprite2.hitbox)


class Cat(pg.sprite.Sprite):
    
    def __init__(self, image, pos, vel):
        super().__init__()
        self.image = image
        self.pos = pg.Vector2(pos)
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = self.pos
        self.left = False
        self.right = False
        self.vel = vel
    
    def update(self, dt, screen_rect):
        if self.left:
            self.pos.x -= self.vel * dt
        if self.right:
            self.pos.x += self.vel * dt
        self.rect.center = self.pos

    def move(self, left, right):
        self.left, self.right = left, right
    
    def get_pos(self):
        return self.pos


class Bird(pg.sprite.Sprite):
    
    def __init__(self, image, pos, vel, scale):
        super().__init__()
        self.image = image
        self.pos = pg.Vector2(pos)
        self.rect: pg.Rect = self.image.get_rect()
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
    
    def draw_hitbox(self, screen, color_hitbox, color_rect):
        pg.draw.rect(screen, color_hitbox, self.hitbox, 2)
        pg.draw.rect(screen, color_rect, self.rect, 2)


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



if __name__ == "__main__":
    game = Game()
    game.run()
