from configparser import ConfigParser
import logging
from os.path import abspath, dirname, join, normpath

CONFIG_TAG_STORIES_ = 'stories'
CONFIG_TAG_VOICES__ = 'voices'
CONFIG_TAG_CALENDAR = 'calendar'
CONFIG_TAG_VOLUME__ = ' volume'

class Config:
    def __init__(self, filepath):
        self.config_filepath = abspath(filepath)
        self.config_dirpath = dirname(filepath)
        self.stories_dirpath = join(self.config_dirpath, 'stories')
        self.voices_dirpath = join(self.config_dirpath, 'voices')
        self.calendar_filepath = join(self.config_dirpath, 'calendar.json')
        self.volume = 0.8
        self.bookmark = None

    def load(self):
        logging.debug('loading config from: {}'.format(self.config_filepath))
        parser = ConfigParser()
        parser.read(self.config_filepath)
        if 'SETTINGS' in parser.sections():
            settings = parser['SETTINGS']
            self.stories_dirpath = settings.get(CONFIG_TAG_STORIES_, self.stories_dirpath)
            self.stories_dirpath = normpath(join(self.config_dirpath, self.stories_dirpath))
            self.voices_dirpath = settings.get(CONFIG_TAG_VOICES__, self.voices_dirpath)
            self.voices_dirpath = normpath(join(self.config_dirpath, self.voices_dirpath))
            self.calendar_filepath = settings.get(CONFIG_TAG_CALENDAR, self.calendar_filepath)
            self.calendar_filepath = normpath(join(self.config_dirpath, self.calendar_filepath))
            self.volume = settings.get(CONFIG_TAG_VOLUME__, self.volume)

        if 'BOOKMARK' in parser.sections():
            self.bookmark = parser['BOOKMARK']

    def save(self):
        logging.debug('saving config to: {}'.format(self.config_filepath))
        parser = ConfigParser()
        parser['SETTINGS'] = {
            CONFIG_TAG_STORIES_: abspath(self.stories_dirpath),
            CONFIG_TAG_VOICES__: abspath(self.voices_dirpath),
            CONFIG_TAG_CALENDAR: abspath(self.calendar_filepath),
            CONFIG_TAG_VOLUME__: abspath(self.volume),
        }
        if self.bookmark:
            parser['BOOKMARK'] = self.bookmark
        with open(self.config_filepath, 'w') as configfile:
            parser.write(configfile)

