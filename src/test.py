import pygame as pg
import os

src_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(src_dir, os.pardir)
media_dir = os.path.join(base_dir, "media")

images = pg.image.load_animation(os.path.join(media_dir, "images/bird.gif"))

print(images)