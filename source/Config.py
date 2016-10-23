from configparser import ConfigParser
import logging
from os.path import abspath, dirname, join


class Config:
    def __init__(self, filepath):
        self.config_filepath = abspath(filepath)
        self.config_dirpath = dirname(filepath)
        self.stories_dirpath = join(self.config_dirpath, 'stories')
        self.voices_dirpath = join(self.config_dirpath, 'voices')
        self.bookmark = None

    def load(self):
        logging.debug('loading config from: {}'.format(self.config_filepath))
        parser = ConfigParser()
        parser.read(self.config_filepath)
        if 'SETTINGS' in parser.sections():
            settings = parser['SETTINGS']
            self.stories_dirpath = abspath(settings.get('stories', self.stories_dirpath))
            self.voices_dirpath = abspath(settings.get('voices', self.voices_dirpath))
        if 'BOOKMARK' in parser.sections():
            self.bookmark = parser['BOOKMARK']

    def save(self):
        logging.debug('saving config to: {}'.format(self.config_filepath))
        parser = ConfigParser()
        parser['SETTINGS'] = {
            'stories': abspath(self.stories_dirpath),
            'voices': abspath(self.voices_dirpath)
        }
        if self.bookmark:
            parser['BOOKMARK'] = self.bookmark
        with open(self.config_filepath, 'w') as configfile:
            parser.write(configfile)

