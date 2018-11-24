import os
import click
import configparser
from infinite_pandora.api import *
from infinite_pandora.downloader import Downloader
import random
import sys


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

    # settings = {}
    # for line in config.readlines():
    #     line = line.strip()
    #     if line and line[0] != '#':
    #         k, v = line.split('=')
    #         settings[k.strip()] = v.strip()
    # ctx.obj = Pandora(user=settings['user'],
    #                       password=settings['password'])


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
            station = find_station(random.choice(station_list), stations)
            if not station:
                click.echo('Station not found')
                sys.exit(1)
            else:
                info('Downloading station "{}" to {}"', station.name, target)
            downloader = Downloader(target, station.name)

        playlist = pandora.playlist(station)
        # info('Got songs {}', ', '.join(
        #    map(attrgetter('name'), playlist.songs)))

        for song in playlist.songs:
            info('Downloading {} by {}', song.name, song.artist_name)
            song.station = station.name
            length = downloader.download(song) #station.name
            tick_count += 1
            if tick_limit <= tick_count:
                sys.exit(0)
            if sleep:
                sleep_length = sleep_factor * length
                # info('Sleeping {} seconds', sleep_length)
                time.sleep(sleep_length)
        song_count += 1


def find_station(criterion, stations):
    for i, station in enumerate(stations):
        if criterion in (station.id, station.name, str(i)):
            return station


if __name__ == '__main__':
    main()