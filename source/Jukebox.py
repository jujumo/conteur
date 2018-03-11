#!/usr/bin/env python3
import pygame
# from pygame.locals import *
import argparse
import logging
import os
import datetime
import random
from os.path import abspath, join, basename, dirname, isdir, splitext
from glob import glob
import locale
import re
# local includes
from Config import Config
from Buttons import Buttons
from Speaker import Speaker


__author__ = 'jumo'

# force local to FR
locale_tag = 'fr-FR' if os.name is 'nt' else 'fr_FR.UTF-8'
try:
    locale.setlocale(locale.LC_TIME, locale_tag)
except locale.Error:
    logging.error('local {} is not installed on your system'.format(locale_tag))
    logging.error('to install FR on raspberry()')
    logging.error(' sudo nano /etc/locale.gen')
    logging.error('Remove the # from every line which you want to generate.')
    logging.error('sudo locale-gen')
    raise


def get_announce_date():
    now = datetime.datetime.now()
    date_message = 'Nous somme le {week:} {day:} {month:} {year:4d}.'.format(
        week=now.strftime('%A'),
        day=now.day if not now.day == 1 else 'premier',
        month=now.strftime('%B'),
        year=now.year
    )
    date_announce = {
        'message': date_message,
        'auto_cache': False
    }
    return date_announce


def get_announce_time():
    now = datetime.datetime.now()
    time_message = 'il est {hour:2d} heure {minute:2d}.'.format(
        hour=now.hour,
        minute=now.minute if not now.minute == 0 else 'pile'
    )
    time_announce = {
        'message': time_message,
        'auto_cache': False
    }
    return time_announce


def get_announce_anniversary():
    today = datetime.datetime.now()
    date_str = '{:02d}/{:02d}'.format(today.day, today.month)
    birthdate = {
        '15/02': {
            'name': 'Julien',
            'year': 1980
        },
        '25/02': {
            'name': 'Manon',
            'year': 2012
        },
        '12/03': {
            'name': 'Manon',
            'year': 1980
        },
        '23/08': {
            'name': 'Anaïs',
            'year': 2013
        }
    }

    if date_str in birthdate:
        infos = birthdate[date_str]
        infos['age'] = today.year - infos['year']
        anniversary_message = 'Je souhaite un très bon anniversaire à {name:} pour ses {age:} ans. '.format(**infos)
        anniversary_announce = {
            'message': anniversary_message,
            'auto_cache': True
        }
        return anniversary_announce
    else:
        return None


def get_announce_christmas():
    today = datetime.datetime.now()
    if today.month == 12:
        if today.day < 25:
            remains = 25 - today.day
            christmas_message = 'Il reste {} jour avant noël ! '.format(remains)
        elif today.day == 25:
            christmas_message = "C'est noël aujourd'hui."
        christmas_announce ={
            'message': christmas_message,
            'auto_cache': True
        }
        return christmas_announce

    return None


def get_announcements():
    announce_msg_list = [
        get_announce_date(),
        get_announce_anniversary(),
        get_announce_christmas(),
        get_announce_time()
    ]
    announce_msg_list = [m for m in announce_msg_list if m]
    for a in announce_msg_list:
        a.update({'wait_silence': True})
    return announce_msg_list


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

    def get_tracks(self):
        return self._tracks

    def change_track(self, increment):
        self._track_idx_current += increment
        self._track_idx_current %= len(self._tracks)

    def set_track(self, idx):
        self._track_idx_current = idx
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
            logging.info('esc to quit \n'
                         '1: previous disk\n'
                         '4: next disk\n'
                         '2: previous track\n'
                         '3: next track\n'
                         '6: stop\n'
                         '7: play\n'
                         '5: random\n'
                         '8: random\n')
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
        self._speaker.speak(self.get_current_disk().get_current_track().name(), wait_silence=True)

    def on_track_change(self, increment):
        self.get_current_disk().change_track(increment)
        self._speaker.speak(self.get_current_disk().get_current_track().name())

    def on_random(self):
        self._disk_idx_selected = random.choice(range(len(self._disks)))
        track = random.choice(range(len(self.get_current_disk().get_tracks())))
        self.get_current_disk().set_track(track)
        self._speaker.speak(self._disks[self._disk_idx_selected].name(), wait_silence=True)
        self._speaker.speak(self.get_current_disk().get_current_track().name(), wait_silence=True)

    def on_info(self):
        self._speaker.speak(self.get_current_disk().name(), wait_silence=True)
        self._speaker.speak(self.get_current_disk().get_current_track().name(), wait_silence=True)

    def on_play(self):
        track_filepath = self.get_current_disk().get_current_track().filepath()
        pygame.mixer.music.load(track_filepath)
        pygame.mixer.music.play()

    def on_date(self):
        self._speaker.speak(get_announce_date(), auto_cache=False, wait_silence=True)

    def on_time(self):
        for announce in get_announcements():
            self._speaker.speak(**announce)

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
        elif 6 == button_id:  # button stop
            self.on_stop()
        elif 7 == button_id:  # button play
            self.on_play()
        elif 5 == button_id:  # button random
            self.on_random()
        elif 8 == button_id:  # button random
            self.on_time()
        else:
            self.on_info()

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
        for announce in get_announcements():
            self._speaker.speak(**announce)
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

