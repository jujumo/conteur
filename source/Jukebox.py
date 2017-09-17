#!/usr/bin/env python3
import pygame
# from pygame.locals import *
import argparse
import logging
import os
from glob import glob
from os.path import abspath, join, basename, dirname, isdir, splitext
import re
# local includes
from Config import Config
from Buttons import Buttons
from Speaker import Speaker


__author__ = 'jumo'


class Track:
    def __init__(self, track_filepath):
        self._filepath = track_filepath
        self._name = ''
        self.set_name(track_filepath)
        logging.debug('adding track {}'.format(self._name))

    def set_name(self, track_filepath):
        # keep only filename
        self._name = basename(track_filepath)
        # remove extension
        self._name = splitext(self._name)[0]
        # remove track number if any
        self._name = re.sub(r'\d{1,3}\s*-\s*', '', self._name)

    def filepath(self):
        return self._filepath

    def name(self):
        return self._name


class Disk:
    def __init__(self, disk_dirpath):
        self._dirpath = disk_dirpath
        self._name = basename(disk_dirpath)
        logging.debug('populating disk {name}'.format(name=self._name))
        self._tracks = [Track(join(p, n)) for p, sd, fs in os.walk(self._dirpath) for n in fs if n.lower().endswith(".mp3")]
        self._track_idx_current = 0

    def get_current_track(self):
        return self._tracks[self._track_idx_current]

    def on_change_track(self, increment):
        self._track_idx_current += increment
        self._track_idx_current %= len(self._tracks)

    def name(self):
        return self._name


class Jukebox:
    def __init__(self, config):
        # pygame.mixer.pre_init(16000)
        pygame.init()
        # pygame.mixer.init(11025)
        pygame.mixer.music.set_volume(1.0)
        self._buttons = Buttons()
        self._config = config
        self._clock = pygame.time.Clock()
        self._disk_idx_selected = 0
        self.populate_disks(config.stories_dirpath)
        if os.name is 'nt':
            # windows needs a window to play music
            window = pygame.display.set_mode((640, 600))
        self._speaker = Speaker(config.voices_dirpath)
        pygame.mixer.music.set_volume(1.0)
        logging.info('init successful')

    def populate_disks(self, disks_rootpath):
        self._disks = []
        # list every folder that contains at least one mp3
        file_list = (join(p, n) for p, sd, fs in os.walk(disks_rootpath) for n in fs if n.lower().endswith(".mp3"))
        disk_set = set(dirname(f) for f in file_list)
        for disk_path in disk_set:
            self._disks += [Disk(disk_path)]

    def get_current_disk(self):
        return self._disks[self._disk_idx_selected]

    def on_change_disk(self, increment):
        self._disk_idx_selected += increment
        self._disk_idx_selected %= len(self._disks)
        self._speaker.speak(self.get_current_disk().name())

    def on_track_change(self, increment):
        self.get_current_disk().on_change_track(increment)
        self._speaker.speak(self.get_current_disk().get_current_track().name())

    def on_play(self):
        # self._speaker.speak('jouer' )
        # self._speaker.speak(self.get_current_disk().name())
        self._speaker.speak(self.get_current_disk().get_current_track().name())
        track_filepath = self.get_current_disk().get_current_track().filepath()
        pygame.mixer.music.load(track_filepath)
        pygame.mixer.music.play()

    def on_stop(self):
        pygame.mixer.music.stop()

    def button_pushed(self, button_id):
        logging.info('button {} pushed.'.format(button_id))
        logging.info('play selection')
        if 1 == button_id:  # button previous disk
            self.on_change_disk(-1)
        elif 4 == button_id:  # button next disk
            self.on_change_disk(+1)
        elif 2 == button_id:  # button previous track
            self.on_track_change(-1)
        elif 3 == button_id:  # button next track
            self.on_track_change(+1)
        elif 5 == button_id:  # button stop
            self.on_stop()
        elif 6 == button_id:  # button play
            self.on_play()
        else:
            self._speaker.speak('ce bouton ne fait rien.')

    def volume_increment(self, increment):
        volume = pygame.mixer.music.get_volume()
        logging.debug('old volume {}'.format(volume))
        # apply increment
        volume += increment/10.0
        # clamp between 0..1
        volume = min(max(0, volume), 1)
        # set
        pygame.mixer.music.set_volume(volume)
        logging.info('set volume {}'.format(pygame.mixer.music.get_volume()))

    def save(self):
        logging.debug('saving status')
        self._config.save()

    def load(self):
        logging.info('loading status')
        self._config.load()

    def main_loop(self):
        self.load()
        self._speaker.speak('bonjour')
        ask_exit = False
        while not ask_exit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == 2 and event.key ==pygame.K_ESCAPE):
                    ask_exit = True
                elif event.type == pygame.JOYAXISMOTION:
                    if event.axis == 0 and not event.value == 0:
                        logging.debug('joystick {}'.format(event.value))
                        self.volume_increment(event.value)
                    elif event.axis == 1 and not event.value == 0:
                        logging.debug('joystick 2{}'.format(event.value))
                elif event.type == pygame.JOYBUTTONDOWN:
                    logging.debug('button {}'.format(event.button))
                    self.button_pushed(event.button+1)
                elif event.type == 2 and 257 <= event.key <= 265:
                    # keyboard
                    num = event.key-256
                    logging.debug('numpad {}'.format(num+1))
                    self.button_pushed(num)
                elif event.type == 2 and 269 <= event.key <= 270:
                    increment = -1 if event.key == 269 else 1
                    logging.debug('key {}'.format(increment))
                    self.volume_increment(increment)
                elif event.type == 2:
                    logging.debug('key pressed {}'.format(event.key))

            self._clock.tick(5)  # 5 fps

