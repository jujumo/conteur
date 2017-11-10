#!/usr/bin/env python3
import pygame
# from pygame.locals import *
import argparse
import logging
import os
from glob import glob
from os.path import abspath, join, isfile, dirname, isdir
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
        # populate voices
        self._voices = {}
        self.populate_voices()

    def populate_voices(self):
        voices_files = glob(join(self._voices_dirpath, '*.wav'))
        self._voices = {}
        for filepath in voices_files:
            try:
                sound = pygame.mixer.Sound(filepath)
                self._voices[filepath] = sound
            except pygame.error as e:
                # this might be a corrupted file, just remove it
                os.remove(filepath)
                pass

    def message_filepath(self, message, auto_cache=True):
        dirpath = self._voices_dirpath if auto_cache else gettempdir()
        hash = re.sub('[^A-Za-z0-9]+', '', message)
        return join(dirpath, hash + '.wav')

    def speak(self, message, auto_cache=True):
        logging.debug('saying: ' + message)
        message_filepath = self.message_filepath(message, auto_cache)

        if message_filepath not in self._voices:
            logging.debug('no voice file ({}) for message: "{}"'.format(message_filepath, message))
            tts(message_filepath, message)
            self._voices[message_filepath] = pygame.mixer.Sound(message_filepath)

        if message_filepath in self._voices:
            self._voices[message_filepath].play()


