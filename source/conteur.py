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


class Speaker:
    def __init__(self, resource_dirpath):
        # make sure voices dir exists
        self._voices_dirpath = join(resource_dirpath, 'voices')
        if not isdir(self._voices_dirpath):
            os.makedirs(self._voices_dirpath)
        # populate voices
        voices_files = glob(join(self._voices_dirpath, '*.wav'))
        self._voices = {f: pygame.mixer.Sound(f) for f in voices_files}
        # make sur pico2wav is accessible
        # if os.name is not 'nt':
        try:
            ret = call(['which', 'pico2wave'])
        except OSError as e:
            logging.error('which not found')

    def message_filepath(self, message):
        hash = re.sub('[^A-Za-z0-9]+', '', message)
        return join(self._voices_dirpath, hash + '.wav')

    def speak(self, message):
        logging.debug('saying: ' + message)
        message_filepath = self.message_filepath(message)
        if message_filepath in self._voices:
            self._voices[message_filepath].play()
        else:
            logging.warning('no voice file for: ' + message)
            # todo: try to create the sound and file


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
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.set_volume(1.0)
        pygame.joystick.init()
        self._clock = pygame.time.Clock()
        Conteur.init_buttons()
        self._stories_filepath = abspath(resource_dirpath)
        self._config_filepath = join(self._stories_filepath, 'config.ini')
        self._stories = None
        self._config = ConfigParser()
        self._selected_id = None
        self._playing_id = None
        self._playing_start = 0
        if os.name is 'nt':
            # windows needs a window to play music
            window = pygame.display.set_mode((640, 600))
        self.populate_stories()
        self._speaker = Speaker(resource_dirpath)
        logging.info('init successful')

    def populate_stories(self):
        files = (abspath(f) for f in glob(join(self._stories_filepath, '*.*')))
        # audio_files = (file for file in files if splitext(file)[1] in audio_extionsion_list)
        story_regexp = r'^(?P<filepath>.*/(?P<num>\d+)[\s-]+(?P<name>.+)\.(?P<ext>\w+))$'
        # select audio files matching name format
        audio_file_props = (re.match(story_regexp, file).groupdict() for file in files if re.match(story_regexp, file))
        # build infos from files
        self._stories = {int(g['num']): g for g in audio_file_props}

    def play(self, id, start=0):
        if self._playing_id:
            self.stop()

        if id in self._stories:
            logging.info('start playing {}'.format(id))
            story_filepath = self._stories[id]['filepath']
            pygame.mixer.music.load(story_filepath)
            pygame.mixer.music.play(start=start)
            self._playing_id = id
            self._playing_start = start

    def stop(self):
        pygame.mixer.music.stop()
        self._playing_id = None

    def button_pushed(self, button_id):
        logging.info('button {} pushed.'.format(button_id))
        self._speaker.speak('{:02d}'.format(button_id))

    def get_current_time_s(self):
        pos = self._playing_start
        pos += round(pygame.mixer.music.get_pos() / 1000)
        return pos

    def save(self):
        logging.info('saving {}'.format(self._config_filepath))
        with open(self._config_filepath, 'w') as configfile:
            self._config['playing'] = {
                'id': self._playing_id,
                'time': self.get_current_time_s()
            }
            self._config.write(configfile)

    def load(self):
        logging.info('loading {}'.format(self._config_filepath))
        self._config.read(self._config_filepath)
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
                    self.button_pushed(event.button)
                elif event.type == 2 and 257 <= event.key <= 265:
                    # keyboard
                    num = event.key-257
                    logging.info('numpad {}'.format(num+1))
                    self.button_pushed(num)
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

