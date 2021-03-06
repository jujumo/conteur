#!/usr/bin/env python3
import pygame
import argparse
import logging
import os
from os.path import abspath, join, isfile, dirname, isdir
# local includes
from tts import tts
from Config import Config
from Buttons import Buttons
from Jukebox import Jukebox


# set SDL to use the dummy NULL video driver, 
#   so it doesn't need a windowing system.
os.environ["SDL_VIDEODRIVER"] = "dummy"


__author__ = 'jumo'


def main():
    try:
        parser = argparse.ArgumentParser(description='Jukebox is a simple disk player triggered by gamepad buttons.')
        parser.add_argument('-v', '--verbose', action='count', default=0, help='verbose message')
        parser.add_argument('-c', '--config', default='jukebox.ini', help='config file')
        parser.add_argument('-l', '--log', help='specify log file')

        args = parser.parse_args()

        if args.log:
            logging.basicConfig(filename=abspath(args.log))
        if args.verbose:
            logging.getLogger().setLevel(logging.INFO)
        if args.verbose > 1:
            logging.getLogger().setLevel(logging.DEBUG)

        config = Config(abspath(args.config))
        config.load()
        # config.save()
        jukebox = Jukebox(config)
        jukebox.main_loop()

    except Exception as e:
        logging.critical(e)
        if args.verbose > 1:
            raise

    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

