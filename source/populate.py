#!/usr/bin/env python3
import pygame
# from pygame.locals import *
import argparse
import logging
import os
from glob import glob
from os.path import abspath, join, isfile, dirname, isdir
import re

__author__ = 'jumo'


class Album:
    def __init__(self, dir_path):
        self._dir_path = dir_path
        self._tracks = []
        self.populate(dir_path)

    def populate(self, dir_path):

        pass


class MediaNavigation:
    def __init__(self, config):
        self._config = config
        self._subfolders = {}
        self._files = {}
        self.populate(config.stories_dirpath)

    def populate(self, dirpath):
        logging.info('populating media in {}'.format(dirpath))
        files = (abspath(f) for f in glob(join(dirpath, '*.*')))
        story_regexp = r'^(?P<filepath>.*[/\\](?P<num>\d+)[\s-]+(?P<name>.+)\.(?P<ext>\w+))$'
        # select audio files matching name format
        audio_file_props = (re.match(story_regexp, file).groupdict() for file in files if re.match(story_regexp, file))
        # build infos from files
        self._stories = {int(props['num']): props for props in audio_file_props}
        logging.info('{} stories loaded'.format(str(len(self._stories))))

    def say_my_name(self, id, start_time=0):
        logging.debug('ask the story {}'.format(id))
        if id in self._stories:
            self._current = self._stories[id]
            self._current['start'] = start_time
            logging.debug('the story is {}'.format(self._current['name']))
            story_filepath = self._current['filepath']
            pygame.mixer.music.load(story_filepath)
            pygame.mixer.music.play(start=start_time)
        else:
            logging.error('no story {} found.'.format(id))

    def halt(self):
        self._current = None
        pygame.mixer.music.stop()

    def get_story(self, id):
        if id in self._stories:
            return self._stories[id]
        else:
            return None



class Conteur:
    def __init__(self, config):
        # pygame.mixer.pre_init(16000)
        pygame.init()
        # pygame.mixer.init(11025)
        pygame.mixer.music.set_volume(1.0)
        self._buttons = Buttons()
        self._config = config
        self._clock = pygame.time.Clock()
        self._stories = Stories(config)
        self._select = None
        if os.name is 'nt':
            # windows needs a window to play music
            window = pygame.display.set_mode((640, 600))
        self._speaker = Speaker(config.voices_dirpath)
        pygame.mixer.music.set_volume(1.0)
        logging.info('init successful')

    def button_pushed(self, button_id):
        logging.info('button {} pushed.'.format(button_id))
        self._stories.halt()
        if self._select == button_id:
            logging.info('play selection')
            self._select = None
            self._stories.tell(button_id)
        else:
            story = self._stories.get_story(button_id)
            if story:
                self._speaker.speak(story['name'])
                self._select = button_id
            else:
                logging.error('story {} not found.'.format(button_id))

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


def main():
    try:
        parser = argparse.ArgumentParser(description='Conteur is a story teller program triggered by gamepad buttons.')
        parser.add_argument('-v', '--verbose', action='store_true', help='verbose message')
        parser.add_argument('-c', '--config', required=True, help='config file')
        parser.add_argument('-l', '--log', help='specify log file')

        args = parser.parse_args()

        if args.log:
            logging.basicConfig(filename=abspath(args.log))
        if args.verbose:
            logging.getLogger().setLevel(logging.INFO)
        if __debug__:
            logging.getLogger().setLevel(logging.DEBUG)

        config = Config(abspath(args.config))
        config.load()
        config.save()
        conteur = Conteur(config)
        conteur.main_loop()

    except Exception as e:
        logging.critical(e)
        if __debug__:
            raise

    finally:
        pygame.quit()

if __name__ == '__main__':
    main()

