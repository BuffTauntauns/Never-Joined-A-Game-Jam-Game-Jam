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

        # create sprite groups
        self.all_sprites = pg.sprite.Group()
        self.birds = pg.sprite.Group()

        # create cat
        self.cat = Cat(self.cat_normal_img, (300, 450), vel=200)
        #self.cat.add(self.all_sprites)
        self.all_sprites.add(self.cat)

        self.controls = {
            "left": self.bind_key(self.settings["controls"]["left"]),
            "right": self.bind_key(self.settings["controls"]["right"]),
            "shoot": self.bind_key(self.settings["controls"]["shoot"])
        }

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
        self.BIRD_SPAWN = pg.USEREVENT + self.event_counter
        self.event_counter += 1
        pg.time.set_timer(self.BIRD_SPAWN, 3000)

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
                bird = Bird(img, pos, vel)
                bird.add(self.all_sprites, self.birds)
            if event.type == pg.KEYDOWN:
                key = event.key
                if key == self.controls["shoot"]:
                    cat_pos = self.cat.get_pos()
                    laser = Laser(self.laser_beam_img, cat_pos, self.laser_vel)
                    laser.add(self.all_sprites)
        keys = pg.key.get_pressed()
        left = False
        right = False
        if keys[self.controls["left"]]:
            left = True
        if keys[self.controls["right"]]:
            right = True
        self.cat.move(left, right)

    
    def screen_update(self):
        self.all_sprites.update(self.dt)

    def screen_draw(self):
        self.screen.fill(pg.Color("aqua"))
        self.all_sprites.draw(self.screen)
        pg.display.flip()
    
    def bind_key(self, name):
        return pg.key.key_code(name)


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
    
    def update(self, dt):
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
    
    def __init__(self, image, pos, vel):
        super().__init__()
        self.image = image
        self.pos = pg.Vector2(pos)
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = self.pos
        self.vel = vel
    
    def update(self, dt):
        self.pos.x += self.vel *dt
        self.rect.center = self.pos


class Laser(pg.sprite.Sprite):
    
    def __init__(self, image, pos, vel):
        super().__init__()
        self.image = image
        self.pos = pg.Vector2(pos)
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = self.pos
        self.vel = pg.Vector2(vel)
    
    def update(self, dt):
        self.pos.y += self.vel.y * dt
        self.pos.x += self.vel.x * dt
        self.rect.center = self.pos


if __name__ == "__main__":
    game = Game()
    game.run()
