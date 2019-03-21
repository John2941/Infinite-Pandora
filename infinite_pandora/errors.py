import logging
import click_log


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
formatter = logging.Formatter('1%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)
click_log.basic_config(log)



class PandoraException(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        log.error(msg)

    def __str__(self):
        return self.msg


class StationException(PandoraException):
    pass


class SongDownloadException(PandoraException):
    pass

