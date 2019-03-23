import os
import click
import configparser
from infinite_pandora.api import *
from infinite_pandora.downloader import Downloader
from infinite_pandora.errors import *
import random
import sys
import logging
import click_log

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('1%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)
click_log.basic_config(log)


def info(message, *args, **kwargs):
    click.echo(click.style(message.format(*args, **kwargs), 'blue'))


@click.group()
@click.option('--config', 'config_file', help='configuration file to load',

              default=os.path.join(click.get_app_dir('infinite-pandora'), 'config'),
              type=click.File('r'))
@click.pass_context
def main(ctx, config_file):
    config = configparser.ConfigParser()
    config.read(config_file.name)

    ctx.obj = dict()
    ctx.obj['PANDORA'] = Pandora(user=config['LOGIN']['user'],
                          password=config['LOGIN']['password'])
    ctx.obj['CONFIG'] = config


@main.group()
def station():
    pass


@station.command('list')
@click.pass_context
def station_list(ctx):
    pandora = ctx.obj['PANDORA']
    pandora.auth()

    for i, station in enumerate(pandora.stations()):
        click.echo('{:2}: {} ({})'.format(i, station.name, station.id))


@main.command()
@click.argument('station', required=False, default=None)
@click.option('--target', help='where to store files',
              default='.',
              type=click.Path(exists=True, file_okay=False, writable=True))
@click.option('--sleep/--no-sleep', default=True)
@click.option('--count', 'tick_limit', default=-1, type=int,
              help='amount of songs to download')
@click.option('--sleep-factor', default=1.0, type=float,
              help='which fraction of a job to sleep')
@click.pass_context
def download(ctx, station, target, sleep, tick_limit, sleep_factor):
    pandora = ctx.obj['PANDORA']
    config = ctx.obj['CONFIG']
    station_list = config['STATION']['stations'].split(',') if not station else list(station)
    station_cycle = int(config['STATION']['cycle'] if 'cycle' in config['STATION'] else 0) or 15
    tick_count = 0
    song_count = station_cycle + 1  # make sure we trigger the station lookup on first iteration

    if not station_list:
            raise Exception('stations argument needs a value')

    if 'download_directory' in config['SETTINGS']:
        target = config['SETTINGS']['download_directory']
    if 'sleep_factor' in config['SETTINGS']:
        sleep_factor = float(config['SETTINGS']['sleep_factor'])
    if 'tick_limit' in config['SETTINGS']:
        tick_limit = int(config['SETTINGS']['tick_limit'])

    pandora.auth()
    stations = pandora.stations()

    while True:
        if song_count > station_cycle:
            song_count = 0
            random_station = random.choice(station_list)
            station = find_station(random_station, stations)
            if not station:
                raise StationException('{} station not found.'.format(random_station))
                click.echo('Station not found')
                sys.exit(1)
            else:
                info('Downloading station "{}" to {}"', station.name, target)
            try:
                downloader = Downloader(target, station.name)
            except PandoraException as e:
                log.error(e)
                raise SongDownloadException('Downloading {} from {} station'.format(target, station.name))
                time.sleep(30)
                pandora = Pandora(user=config['LOGIN']['user'],
                                  password=config['LOGIN']['password'])
                pandora.auth()
                continue
        try:
            playlist = pandora.playlist(station)
        except (PlaylistException, PandoraException):
            # log.error(e)
            # raise PlaylistException('Playlist error. -- {}'.format(e))
            time.sleep(30)
            pandora = Pandora(user=config['LOGIN']['user'],
                          password=config['LOGIN']['password'])
            pandora.auth()
            continue
        # info('Got songs {}', ', '.join(
        #    map(attrgetter('name'), playlist.songs)))

        for song in playlist.songs:
            log.debug('song_count: {}, station_cycle: {}, tick_count: {}, tick_limit: {}'.format(song_count,
                                                                                                 station_cycle,
                                                                                                 tick_count,
                                                                                                 tick_limit))
            info('Downloading {} by {}', song.name, song.artist_name)
            song.station = station.name

            try:
                downloader.download(song) #station.name
                tick_count += 1
            except PandoraException as e:
                log.error(e)
                raise SongDownloadException('Downloading {} from {} station'.format(song.name, station.name))
                time.sleep(30)
                pandora = Pandora(user=config['LOGIN']['user'],
                                  password=config['LOGIN']['password'])
                pandora.auth()
                continue

            if tick_limit > 0 and tick_limit <= tick_count:
                sys.exit(0)

            if sleep:
                sleep_length = sleep_factor * (song.length if song.length > 0 else 180)
                log.debug('Sleeping {} seconds'.format(sleep_length))
                time.sleep(sleep_length)
        song_count += 1


def find_station(criterion, stations):
    for i, station in enumerate(stations):
        if criterion in (station.id, station.name, str(i)):
            return station


if __name__ == '__main__':
    main()