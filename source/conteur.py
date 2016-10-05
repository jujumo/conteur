#!/usr/bin/env python3
import pygame
# from pygame.locals import *
import argparse
import logging
import os
from glob import glob
from os.path import abspath, join, isfile, dirname
from configparser import ConfigParser

__author__ = 'jumo'

config_filpath = 'config.ini'


class Setup:
    @staticmethod
    def init_buttons():
        # list possible interfaces
        joysticks = (pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count()))
        # filter the ones that qre called generic ... (thats how my buttons are called)
        joysticks = [b for b in joysticks if 'GENERIC' in b.get_name().upper().split()]
        if not joysticks:
            logging.error('buttons device not found')
            # raise EnvironmentError('buttons device not found')
        else:
            buttons, = joysticks
            buttons.init()
            logging.debug('{} connected'.format(buttons.get_name()))

    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.set_volume(1.0)
        pygame.joystick.init()
        self._clock = pygame.time.Clock()
        Setup.init_buttons()
        self._stories = None
        self._config = ConfigParser()
        self._playing_id = None
        self._playing_start = 0
        if os.name is 'nt':
            # windows needs a window to play music
            window = pygame.display.set_mode((640, 600))
        logging.info('init successful')

    def populate_stories(self, stories_dirpath, selection_number=8):
        stories = (abspath(f) for f in glob(join(stories_dirpath, '*.mp3')))
        soties_selected = sorted(stories)
        del soties_selected[selection_number:]
        self._stories = soties_selected

    def play(self, id, start=0):
        if self._playing_id:
            self.stop()

        if id < len(self._stories):
            logging.info('start playing {}'.format(id))
            story_filepath = self._stories[id]
            pygame.mixer.music.load(story_filepath)
            pygame.mixer.music.play(start=start)
            self._playing_id = id
            self._playing_start = start

    def stop(self):
        pygame.mixer.music.stop()
        self._playing_id = None

    def get_current_time_s(self):
        pos = self._playing_start
        pos += round(pygame.mixer.music.get_pos() / 1000)
        return pos

    def save(self):
        logging.info('saving {}'.format(config_filpath))
        with open(config_filpath, 'w') as configfile:
            self._config['playing'] = {
                'id': self._playing_id,
                'time': self.get_current_time_s()
            }
            self._config.write(configfile)

    def load(self):
        logging.info('loading {}'.format(config_filpath))
        self._config.read(config_filpath)
        if 'playing' in self._config:
            self.stop()
            playing = self._config['playing']
            id = playing.getint('id')
            start = playing.getint('time')
            self.play(id, start)
        else:
            self.play(0)

    def main_loop(self):
        self.load()
        ask_exit = False
        count = 0
        while not ask_exit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    ask_exit = True
                elif event.type == pygame.JOYBUTTONDOWN:
                    logging.info('button {}'.format(event.button))
                    self.play(event.button)
                elif event.type == 2 and 257 <= event.key <= 265:
                    # keyboard
                    num = event.key-257
                    logging.info('numpad {}'.format(num+1))
                    self.play(num)
            if self._playing_id is not None:
                if count == 10:
                    count = 0
                    self.save()
                else:
                    count += 1
            self._clock.tick(5)  # 5 fps


def main():
    try:
        parser = argparse.ArgumentParser(description='Conteur is a story teller program triggered by gamepad buttons.')
        parser.add_argument('-v', '--verbose', action='store_true', help='verbose message')
        parser.add_argument('-i', '--input', help='stories directory')
        parser.add_argument('-l', '--log', help='specify log file')

        args = parser.parse_args()

        if args.log:
            logging.basicConfig(filename=abspath(args.log))
        if args.verbose:
            logging.getLogger().setLevel(logging.INFO)
        if __debug__:
            logging.getLogger().setLevel(logging.DEBUG)

        resource_dirpath = abspath(args.input or dirname(__file__))
        setup = Setup()
        setup.populate_stories(resource_dirpath)
        setup.main_loop()

    except Exception as e:
        logging.critical(e)
        if __debug__:
            raise

    finally:
        pygame.quit()

if __name__ == '__main__':
    main()

