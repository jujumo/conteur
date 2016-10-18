#!/usr/bin/env python3
import pygame
# from pygame.locals import *
import argparse
import logging
import os
from glob import glob
from os.path import abspath, join, isfile, dirname, isdir
from configparser import ConfigParser
import re
from subprocess import call, Popen

__author__ = 'jumo'


class Config:
    def __init__(self, filepath):
        self._filepath = filepath
        self.data = ConfigParser()

    def load(self):
        logging.debug('loading config from: {}'.format(self._filepath))
        self.data.read(self._filepath)

    def save(self):
        logging.debug('saving config to: {}'.format(self._filepath))
        with open(self._config_filepath, 'w') as configfile:
            self.data.write(configfile)

    def set_bookmark(self, story=None, current=None):
        self.data['BOOKMARK'] = {'story': story, 'current': current}


class Speaker:
    def __init__(self, resource_dirpath):
        # make sure voices dir exists
        self._voices_dirpath = join(resource_dirpath, 'voices')
        if not isdir(self._voices_dirpath):
            os.makedirs(self._voices_dirpath)
        # populate voices
        voices_files = glob(join(self._voices_dirpath, '*.wav'))
        self._voices = {f: pygame.mixer.Sound(f) for f in voices_files}

    def message_filepath(self, message):
        hash = re.sub('[^A-Za-z0-9]+', '', message)
        return join(self._voices_dirpath, hash + '.wav')

    def speak(self, message):
        logging.debug('saying: ' + message)
        message_filepath = self.message_filepath(message)
        if message_filepath in self._voices:
            self._voices[message_filepath].play()
        else:
            logging.debug('no voice file ({}) for message: "{}"'.format(message_filepath, message))
            try:
                call(['pico2wave', '-l', '"fr-FR"', '-w', message_filepath, '"{}"'.format(message)])
            except OSError as e:
                logging.error('pico2wave error')


class Buttons:
    def __init__(self):
        pygame.joystick.init()
        joysticks = (pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count()))
        # filter the ones that qre called generic ... (thats how my buttons are called)
        joysticks = [b for b in joysticks if 'GENERIC' in b.get_name().upper().split()]
        if not joysticks:
            logging.error('buttons device not found')
            # raise EnvironmentError('buttons device not found')
            self._joystick = None
        else:
            self._joystick, = joysticks
            self._joystick.init()
            logging.debug('{} connected'.format(self._joystick.get_name()))


class Stories:
    def __init__(self, dirpath):
        self._direpath = None
        self._stories = {}
        self._current = {}
        self.populate(dirpath)

    def populate(self, dirpath):
        logging.info('populating stories in {}'.format(dirpath))
        self._dirpath = dirpath
        files = (abspath(f) for f in glob(join(self._dirpath, '*.*')))
        story_regexp = r'^(?P<filepath>.*[/\\](?P<num>\d+)[\s-]+(?P<name>.+)\.(?P<ext>\w+))$'
        # select audio files matching name format
        audio_file_props = (re.match(story_regexp, file).groupdict() for file in files if re.match(story_regexp, file))
        # build infos from files
        self._stories = {int(props['num']): props for props in audio_file_props}
        logging.info('{} stories loaded'.format(str(len(self._stories))))
        for i, story in self._stories.items():
            logging.debug(i, story)

    def tell(self, id, start_time=0):
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

    def get_bookmark(self):
        if self._current:
            current_time = self._current['start']
            current_time += round(pygame.mixer.music.get_pos() / 1000)
            return {'story': self._current_story, 'time': current_time}
        else:
            return None


class Conteur:
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

    def __init__(self, resource_dirpath):
        # pygame.mixer.pre_init(16000)
        pygame.init()
        # pygame.mixer.init(11025)
        pygame.mixer.music.set_volume(1.0)

        self._clock = pygame.time.Clock()
        self._buttons = Buttons()
        self._stories_filepath = abspath(resource_dirpath)
        self._config = Config(join(self._stories_filepath, 'config.ini'))
        self._stories = Stories(self._stories_filepath)
        self._select = None
        if os.name is 'nt':
            # windows needs a window to play music
            window = pygame.display.set_mode((640, 600))
        self._speaker = Speaker(resource_dirpath)
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

    def save(self):
        logging.debug('saving status')
        self._config.save()

    def load(self):
        logging.info('loading status')
        self._config.load()

    def main_loop(self):
        self.load()
        ask_exit = False
        while not ask_exit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == 2 and event.key ==pygame.K_ESCAPE):
                    ask_exit = True
                elif event.type == pygame.JOYBUTTONDOWN:
                    logging.info('button {}'.format(event.button))
                    self.button_pushed(event.button)
                elif event.type == 2 and 257 <= event.key <= 265:
                    # keyboard
                    num = event.key-256
                    logging.info('numpad {}'.format(num+1))
                    self.button_pushed(num)
                elif event.type == 2:
                    logging.debug('key pressed {}'.format(event.key))

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
        conteur = Conteur(resource_dirpath)
        conteur.main_loop()

    except Exception as e:
        logging.critical(e)
        if __debug__:
            raise

    finally:
        pygame.quit()

if __name__ == '__main__':
    main()

