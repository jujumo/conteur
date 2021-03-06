#!/usr/bin/env python3
import logging
import os
import datetime
import locale
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
SPEAKABLE_TIME_FORMAT = 'Il est {hour} heure {minute}.'
SPEAKABLE_TIME_FORMAT_ROUND = 'pile'
SPEAKABLE_ANNI_FORMAT = 'Je souhaite un très bon anniversaire à {birth_name:} pour ses {age:} ans.'


class Calendar:
    def __init__(self, filepath):
        self._events = {}
        if filepath:
            self.load(filepath)

    def load(self, filepath):
        try:
            self._events = json.load(open(filepath))
        except:
            self._events = {}

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
        event = self._events[date_str] if date_str in self._events else None
        if event and event['type'] == 'anniversary':
            event['age'] = today.year - event['birth_year']
            anniversary_message = SPEAKABLE_ANNI_FORMAT.format(**event)
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
