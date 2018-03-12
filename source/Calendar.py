#!/usr/bin/env python3
import pygame
# from pygame.locals import *
import logging
import os
import datetime
import locale
import re
# local includes
import json

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


SPEAKABLE_DATE_FORMAT = 'Nous somme le {week:} {day:} {month:} {year:4d}.'
SPEAKABLE_TIME_FORMAT = 'Il est {hour:2d} heure {minute:2d}.'
SPEAKABLE_TIME_FORMAT_ROUND = 'pile'
SPEAKABLE_ANNI_FORMAT = 'Je souhaite un très bon anniversaire à {name:} pour ses {age:} ans.'


class Calendar:
    def __init__(self, filepath):
        self._events = {}
        if filepath:
            self.load(filepath)

    def load(self, filepath):
        # self._events = json.load(open(filepath))
        pass

    @staticmethod
    def get_speakable_date():
        now = datetime.datetime.now()
        date_message = SPEAKABLE_DATE_FORMAT.format(
            week=now.strftime('%A'),
            day=now.day if not now.day == 1 else 'premier',
            month=now.strftime('%B'),
            year=now.year
        )
        return date_message


    @staticmethod
    def get_speakable_time():
        now = datetime.datetime.now()
        time_message = SPEAKABLE_TIME_FORMAT.format(
            hour=now.hour,
            minute=now.minute if not now.minute == 0 else SPEAKABLE_TIME_FORMAT_ROUND
        )
        return time_message

    def get_speakable_anniversary(self):
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
            anniversary_message = SPEAKABLE_ANNI_FORMAT.format(**infos)
            return anniversary_message
        else:
            return None

    @staticmethod
    def get_speakable_christmas():
        today = datetime.datetime.now()
        if today.month == 12:
            if today.day < 25:
                remains = 25 - today.day
                christmas_message = 'Il reste {} jour avant noël ! '.format(remains)
            elif today.day == 25:
                christmas_message = "C'est noël aujourd'hui."
            return christmas_message

        return None

    def get_announcements(self):
        announce_msg_list = [
            self.get_speakable_date(),
            self.get_speakable_anniversary(),
            self.get_speakable_christmas(),
            self.get_speakable_time()
        ]
        announce_msg_list = [m for m in announce_msg_list if m]
        return announce_msg_list
