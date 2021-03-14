#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A simple script aimed at creating shortcuts to
Windows executable files to be opened in Wine.

If the program wrestool is installed, it will also
try and extract the executable icon beforehand.

usage: wineshortcut [-h] [-o OUTPUT_FOLDER] [-n NAME] [-i ICON]
                    [-c CATEGORIES] [-w WINE_PREFIX] [-d] [-a] [-s] [-p]
                    input_file

positional arguments:
  input_file            Windows executable file

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_FOLDER, --output OUTPUT_FOLDER
                        write shortcut to output directory
  -n NAME, --name NAME  set custom shortcut name
  -i ICON, --icon ICON  set custom shortcut icon
  -c CATEGORIES, --categories CATEGORIES
                        set custom shortcut categories
  -w WINE_PREFIX, --wine-prefix WINE_PREFIX
                        set custom Wine prefix
  -d, --to-desktop      write shortcut to desktop folder
  -a, --to-appmenu      write shortcut to application menu
  -s, --skip-icon       disable executable icon extraction
  -p, --dry-run    do not create shortcut, just print output
'''

from argparse import ArgumentParser
from collections import defaultdict
from os import chdir, devnull, getcwd, environ
from os.path import abspath, basename, dirname, expanduser
from os.path import exists, isdir, isfile, relpath, splitext
from re import findall
from subprocess import call, check_output
from sys import argv, stderr
from warnings import warn
import json

OUTPUT = """[Desktop Entry]
Version=1.0
Encoding=UTF-8
Name=$NAME
Exec=$WINE_PREFIX wine "$FILE"
Type=Application
StartupNotify=true
Path=$PATH
Icon=$ICON
StartupWMClass=$EXE
Comment=Wine application
Categories=Wine;$CATEGORIES"""

CONFIG_FILE = 'wineshortcut.json'

class Argument:
    """
    Program argument with command switch name, description text
    and other options that ArgumentParser wants.
    """
    def __init__(self, short_switch, long_switch, description, action=None, const=None, default=None, dest=None):
        self.short_switch = short_switch
        self.long_switch = long_switch
        self.description = description
        self.action = action
        self.const = const
        self.default = default
        self.dest = dest

    def get_parsed_name(self):
        """
        Get the corresponding key name in parsed argument dict.
        """
        if self.dest:
            return self.dest  # use dest if present
        # otherwise generate the key name from switch name
        # this should behave identically with python ArgumentParser
        return self.long_switch.replace('--', '').replace('-', '_')

    def get_config_key_name(self):
        """
        Get the corresponding key name in configuration file.
        """
        return self.long_switch.replace('--', '').replace('-', '_')


def wineshortcut(input_file, output_folder=None,
    name=None, custom_icon=None, do_not_extract_icon=False, categories=None, wine_prefix=None,
    to_desktop=False, to_appmenu=False, dry_run=False):
    '''
    Call main function to create shortcut.
    '''
    cwd = getcwd()

    input_file = abspath(input_file)
    input_exe = basename(input_file)
    input_name = splitext(input_exe)[0]
    input_path = dirname(input_file)

    output_name = input_name + '.desktop'
    extracted_icon = abspath(input_path + '/' + input_name + '.png')

    if wine_prefix:
        # read $HOME from environment variable, fallback to expanduser call
        wine_prefix = wine_prefix.replace('$HOME', environ.get('HOME', expanduser('~')))
        # read `~`
        wine_prefix = expanduser(wine_prefix)
        if isdir(abspath(wine_prefix)):
            wine_prefix = abspath(wine_prefix)
        if not isdir(wine_prefix):
            print("Warning: Wine prefix folder '%s' not found." % wine_prefix, file=stderr)
        wine_prefix = 'env WINEPREFIX="%s" ' % wine_prefix

    if not isfile(input_file):
        raise FileNotFoundError("file '%s' not found" % input_file)

    if isinstance(custom_icon, str):
        if isfile(custom_icon):
            custom_icon = abspath(custom_icon)
        else:
            raise FileNotFoundError("specified icon file '%s' does not exist" % custom_icon)

    elif exists(extracted_icon) and not do_not_extract_icon:
        print("Warning: image file '%s' already exists." % abspath(extracted_icon), file=stderr)

    elif not do_not_extract_icon:  # extract icon from the given .exe file
        best_size = 0
        best_type = None
        best_types = ['group_icon', 'PNG']

        with open(devnull, 'w') as dev_null:
            try: # ignore if unsuccesful
                resources = check_output(['wrestool', '-l', input_file], stderr=dev_null)

                for r in resources.decode().splitlines():
                    icon_name = findall(r'(?<=--name=)[a-zA-Z0-9\'_"]+', r)[0]
                    icon_name = icon_name.replace('\'','').strip('"')
                    icon_size = int(findall(r'(?<=size=)[0-9]+', r)[0])
                    icon_type = findall(r'(?<=type=)[a-zA-Z0-9\'_"]+', r)
                    icon_type = max(icon_type).strip("'")
                    icon_lang = findall(r'(?<=language=)[0-9]+', r)[0]

                    # check every resource for optimal size and type
                    cond1 = (best_size == 0)
                    cond2 = (icon_size >= best_size)
                    cond3 = (icon_type in best_types)

                    if (cond1 or cond2) and cond3:
                        best_name = icon_name
                        best_size = icon_size
                        best_type = icon_type
                        best_lang = icon_lang

                if best_size != 0:
                    cmd = ['wrestool', '-x', input_file,
                        '--output=' + extracted_icon,
                        '--name=' + best_name,
                        '--type=' + best_type,
                        '--language=' + best_lang]

                    call(cmd, stderr=dev_null)

                    if not isfile(extracted_icon):
                        # extract raw resource
                        call(cmd + ['--raw'])

                    chdir(cwd)

            except FileNotFoundError as e:
                warn(e)

    output = OUTPUT.replace('$NAME', name if name else input_name)\
                   .replace('$CATEGORIES', categories if categories else '')\
                   .replace('$WINE_PREFIX ', wine_prefix if wine_prefix else '')\
                   .replace('$FILE', input_file)\
                   .replace('$PATH', input_path)\
                   .replace('$EXE', input_exe)

    if isinstance(custom_icon, str):
        # use the custom icon that the user specified
        output = output.replace('$ICON', custom_icon)
    elif not do_not_extract_icon and isfile(extracted_icon):
        # no custom icon was specified, and we are allowed to extract icon
        # and we successfully extracted the icon
        # so we use the icon we extracted
        output = output.replace('$ICON', extracted_icon)
    else:
        # no available icons
        # remove line
        output = output.replace('Icon=$ICON\n', '')

    if dry_run:
        print(output)
        raise SystemExit

    if not any(x for x in [output_folder, to_desktop, to_appmenu]):
        output_folder = '.'

    if output_folder:
        if isdir(output_folder):
            shortcut = abspath(output_folder + '/' + output_name)
            write_shortcut(shortcut, output)
        else: print("Warning: output '%s' is not a folder or does not exist." % output_folder, file=stderr)

    if to_desktop:
        shortcut = expanduser('~/Desktop/' + output_name)
        write_shortcut(shortcut, output)

    if to_appmenu:
        appmenu = expanduser('~/.local/share/applications/')
        shortcut = abspath(appmenu + '/' + output_name)
        write_shortcut(shortcut, output)

def write_shortcut(shortcut, output):
    '''
    Write output to file and make it executable.
    '''
    with open(shortcut, 'w', newline='', encoding='utf8', errors='ignore') as f:
        f.write(output)
    call(['chmod', '755', shortcut])

if __name__ == '__main__':

    arguments = [
        Argument('-o', '--output', 'write shortcut to output directory', dest='output_folder'),
        Argument('-n', '--name', 'use custom shortcut name'),
        Argument('-i', '--with-icon', 'use a custom shortcut icon', default=None),
        Argument('-c', '--categories', 'use custom shortcut categories'),
        Argument('-w', '--wine-prefix', 'use a custom Wine prefix'),
        Argument('-d', '--to-desktop', 'write shortcut to desktop folder', action='store_true'),
        Argument('-a', '--to-appmenu', 'write shortcut to application menu', action='store_true'),
        Argument('-s', '--skip-icon', 'disable executable icon extraction', action='store_true'),
        Argument('-p', '--dry-run', 'do not create shortcut, just print output', action='store_true')
    ]

    parser = ArgumentParser(description='wineshortcut - create shortcut to Windows executable file')
    parser.add_argument('input_file', help='Windows executable file')
    for arg in arguments:
        parser.add_argument(arg.short_switch, arg.long_switch, 
            help=arg.description, action=arg.action, default=arg.default, dest=arg.dest)
    args = parser.parse_args()

    config_json = {}
    if isfile(CONFIG_FILE):
        # config file exists
        # if some options are not provided by command line arguments, try to load them from the file
        with open(CONFIG_FILE, 'r', encoding='utf8') as f:
            config_json = json.load(f)
    
    # try to read configuration from file, filling out missing options
    for arg in arguments:
        config_key = arg.get_config_key_name()
        parsed_name = arg.get_parsed_name()
        if (not hasattr(args, parsed_name) or getattr(args, parsed_name) is None) and config_key in config_json:
            setattr(args, parsed_name, config_json[config_key])

    wineshortcut(args.input_file,
                 args.output_folder,
                 args.name,
                 args.with_icon,
                 args.skip_icon,
                 args.categories,
                 args.wine_prefix,
                 args.to_desktop,
                 args.to_appmenu,
                 args.dry_run)
