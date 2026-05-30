from sys import exit
import os
import pygame as pg
from pygame._sdl2 import Window
import pygame.locals as loc

import ctypes
# 0 = unaware, 1 = system DPI aware, 2 = per-monitor DPI aware
ctypes.windll.shcore.SetProcessDpiAwareness(1)


class Game():
     
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((1920, 1080), pg.SCALED | pg.FULLSCREEN, vsync = 1)
        self.screen_rect = self.screen.get_rect()
        pg.display.set_caption("title")

        self.clk = pg.time.Clock()

        self.src_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.join(self.src_dir, os.pardir)

        self.set_init_game_state()

    def set_init_game_state(self):
        self.game_state = "playing"

    def run(self):
        while True:
            if self.game_state == "playing":
                self.playing()
    
    def playing(self):
        while self.game_state == "playing":
            self.handle_inputs()
            self.screen_update()
            self.screen_draw()
            self.dt = self.clk.tick(60) / 1000
    
    def handle_inputs(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
    
    def screen_update(self):
        pass

    def screen_draw(self):
        pg.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()
