import os
from os.path import abspath, join, isfile, dirname, isdir
from subprocess import check_call, Popen
import tempfile
import logging
import urllib.request
import urllib.parse


VOXYGEN_URL_FMT = 'https://www.voxygen.fr/sites/all/modules/voxygen_voices/assets/proxy/index.php?method=redirect&text={message}&voice=Marion'
VOICERSS_URL_FMT = 'http://api.voicerss.org/?key=125f646630aa40649a5ef922dea3e76c&hl=fr-fr&src={message}'
MYBLUEMIX_URL_FMT = 'https://text-to-speech-demo.ng.bluemix.net/api/synthesize?voice=fr-FR_ReneeVoice&download=true&accept=audio%2Fmp3&text={message}'

def get_temp_filepath():
    f = tempfile.NamedTemporaryFile()
    temp_filepath = f.name
    f.close()
    return temp_filepath


def tts_normalize(filepath_in, filepath_out, rate=22050):
    # sox -V0 %(export_name)s.mp3 %(filename)s.wav rate 22050 norm
    if os.name is 'nt':
        # relies on ffmpeg on windows
        cmd = ['ffmpeg', '-i', filepath_in, '-ar', str(rate), '-y', filepath_out]
    else:
        cmd = ['sox', '-t', 'mp3', filepath_in, filepath_out, 'rate', str(rate)]

    try:
        success = check_call(cmd)
        if success is not 0:
            return False
    except:
        return False


def tts_pico(message, filepath):
    tmp_filepath = get_temp_filepath() + '.wav'
    cmd = ['pico2wave', '-l', 'fr-FR', '-w', tmp_filepath, message]
    check_call(cmd)
    tts_normalize(tmp_filepath, filepath)
    os.remove(tmp_filepath)


def tts_online(message, filepath):
    message = urllib.parse.quote(message)
    url = MYBLUEMIX_URL_FMT.format(message=message)
    logging.debug('requesting: {}'.format(url))
    tmp_filepath, headers = urllib.request.urlretrieve(url)
    tts_normalize(tmp_filepath, filepath)
    os.remove(tmp_filepath)


def tts(message, filepath):
    # first try online, and fallback on pico if needed
    try:
        logging.debug('try to get voice online')
        tts_online(message, filepath)
        return True
    except IOError as e:
        logging.debug(e)
        logging.debug('online failed')

    try:
        logging.debug('fallback on pico')
        tts_pico(message, filepath)
        return True
    except IOError as e:
        logging.debug(e)
        logging.debug('pico failed')

    return False
