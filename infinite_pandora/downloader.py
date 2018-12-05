import os
from unidecode import unidecode
import logging
import click_log
import requests
import re
from mutagen.id3 import APIC, error, TIT2, TPE1, TALB, COMM, ID3, ID3NoHeaderError
from mutagen.mp4 import MP4, MP4Cover

from infinite_pandora.api import AudioQuality


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
formatter = logging.Formatter('1%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)
click_log.basic_config(log)


class Downloader(object):
    def __init__(self, target, station, quality=AudioQuality.highQuality):
        self.target = target
        self.quality = quality
        self.station = station
        self._tmp_subdir = '.tmp'
        self._http_session = requests.Session()
        self._station_tag = 'pandora:station'

    def download(self, song):
        target = self._format_target(song)
        log.debug('Saving {}\\{}\\{} as {}'.format(song.album_name, song.artist_name, song.name, target))
        url = song.audios['low'].url

        try:
            self._ensure_dirname(target)
        except FileNotFoundError:
            return False

        if not os.path.exists(target):
            with open(target, 'wb') as fd:
                res = self._http_session.get(url, stream=True)

                for chunk in res.iter_content(2048):
                    fd.write(chunk)

            self._tag_file_get_length(target, song)
            self._ensure_dirname(target)
            return song.length if song.length > 0 else 180

        else:
            return False

    def _format_tail(self, song):
        _station = self._format_string_for_fs(self.station, directory=True)
        _artist_name = self._format_string_for_fs(song.artist_name, directory=True)
        _album_name = self._format_string_for_fs(song.album_name, directory=True)
        _song_name = self._format_string_for_fs(song.name + '.m4a')
        return os.path.join(_station,
                            _artist_name,
                            _album_name,
                            _song_name)

    def _format_target(self, song):
        return os.path.join(self.target, self._format_tail(song))

    def _format_tmp(self, song):
        return os.path.join(self.target, self._tmp_subdir,
                            self._format_tail(song))

    @staticmethod
    def _format_string_for_fs(_str, directory=False):
        '''Gets rid of unicode and characters that can't be saved in file name'''
        new_word = unidecode(_str)
        bad_chars = "/?@*\\=|[]:\""
        for letter in bad_chars:
            new_word = new_word.replace(letter, '_')
        if directory and new_word[-1] == '.':
            new_word = new_word[:-1] + '_'
        return new_word

    @staticmethod
    def _ensure_dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    @staticmethod
    def _tag_file_get_length(path, song):
        mp4tags = {
            'title': '\xa9nam',
            'artist': '\xa9ART',
            'album': '\xa9alb',
            'comment': '\xa9cmt',
            'album artist': 'aART',
            'coverart': 'covr'
        }
        audio = MP4(path)
        song.album_art_tmp = os.getcwd()
        song.album_art_tmp = os.path.join(os.path.split(path)[0], 'covertart_temp')
        try:
            r = requests.get(song.album_art)
            with open(song.album_art_tmp, 'wb') as f:
                f.write(r.content)
        except requests.exceptions.MissingSchema as e:
            song.album_art = None
        if song.album_art is not None:
            with open(song.album_art_tmp, 'rb') as f:
                audio[mp4tags['coverart']] = [
                    MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_PNG)
                ]
            os.remove(song.album_art_tmp)
        audio[mp4tags['title']] = song.name
        audio[mp4tags['artist']] = song.artist_name
        audio[mp4tags['album']] = song.album_name
        audio[mp4tags['comment']] = song.station
        audio.save()
