import logging
import click_log
import time

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
formatter = logging.Formatter('1%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)
click_log.basic_config(log)



class PandoraException(Exception):
    def __init__(self, *args):
        self.msg = args
        log.error(self.msg)

    def __str__(self):
        return str(self.msg)


class StationException(PandoraException):
    pass


class SongDownloadException(PandoraException):
    pass


class PlaylistException(PandoraException):
    pass


class PandoraLoginException(PandoraException):
    def __init__(self):
        super(PandoraException, self).__init__()
        time.sleep(60)
