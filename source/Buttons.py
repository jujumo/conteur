import logging
import pygame


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

