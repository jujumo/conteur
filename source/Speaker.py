#!/usr/bin/env python3
import pygame
import logging
import os
from os.path import abspath, join, isfile, dirname, isdir, exists
import re
# local includes
from tts import tts
from tempfile import gettempdir

__author__ = 'jumo'


class Speaker:
    def __init__(self, voices_dirpath):
        # make sure voices dir exists
        self._voices_dirpath = join(voices_dirpath)
        if not isdir(self._voices_dirpath):
            os.makedirs(self._voices_dirpath)

    def message_filepath(self, message, auto_cache=True):
        dirpath = self._voices_dirpath if auto_cache else gettempdir()
        hash = re.sub('[^A-Za-z0-9]+', '', message)
        return join(dirpath, hash + '.wav')

    def speak(self, message, auto_cache=True, wait_silence=False):
        if not message:
            return
        logging.debug('saying: ' + message)
        message_filepath = self.message_filepath(message, auto_cache)

        if not exists(message_filepath):
            logging.debug('no voice file ({}) for message: "{}"'.format(message_filepath, message))
            tts(message, message_filepath)

        if not exists(message_filepath):
            logging.error('unable to generate file ({}) for message: "{}".'.format(message_filepath, message))
            return

        voice = pygame.mixer.Sound(message_filepath)

        if wait_silence:
            while pygame.mixer.get_busy():
                # logging.debug('waiting the mixer is idle before speaking again.')
                pygame.time.wait(200)
        elif pygame.mixer.get_busy():
            pygame.mixer.stop()
        voice.play()


