Credit to @t-8ch . This project was heavily based on https://github.com/t-8ch/pandora-cli

Basic usage:
```bash
Usage: infinite-pandora [OPTIONS] COMMAND [ARGS]...

Options:
  --config FILENAME  configuration file to load
  --help             Show this message and exit.

Commands:
  download
  station
```


Sample CONFIG
```bash
[LOGIN]
user=username
password=password


[STATION]
shuffle=True
stations=Artist Radio, Artist 2 Radio
cycle=1

[SETTINGS]
download_directory=C:\Music
```
You can manually specific a config file location with --config. Alternatively, you can place your config your OS's default application/config location such as:
```bash
Unix:
~/.config/infinite-pandora\config
Win 7 (not roaming):
C:\Users\<user>\AppData\Local\infinite-pandora\config
```
