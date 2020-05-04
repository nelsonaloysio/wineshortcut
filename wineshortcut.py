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
  -p, --print-output    disable shortcut creation, just print output
'''

from argparse import ArgumentParser
from collections import defaultdict
from os import chdir, devnull, getcwd
from os.path import abspath, basename, dirname, expanduser
from os.path import exists, isdir, isfile, relpath, splitext
from re import findall
from subprocess import call, check_output
from sys import argv, stderr
from warnings import warn

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

def wineshortcut(input_file, output_folder=None,
    name=None, icon=None, categories=None, wine_prefix=None,
    to_desktop=False, to_appmenu=False, print_output=False):
    '''
    Call main function to create shortcut.
    '''
    cwd = getcwd()

    input_file = abspath(input_file)
    input_exe = basename(input_file)
    input_name = splitext(input_exe)[0]
    input_path = dirname(input_file)

    output_name = input_name + '.desktop'
    output_icon = abspath(input_path + '/' + input_name + '.png')

    if wine_prefix:
        wine_prefix = abspath(wine_prefix)
        if not isdir(wine_prefix):
            print("Warning: Wine prefix folder '%s' not found." % wine_prefix, file=stderr)
        wine_prefix = 'env WINEPREFIX="%s" ' % wine_prefix

    if not isfile(input_file):
        raise FileNotFoundError("file '%s' not found" % input_file)

    if isinstance(icon, str):
        icon = abspath(icon) if isfile(icon) else icon

    elif exists(output_icon) and icon:
        print("Warning: image file '%s' already exists." % relpath(output_icon), file=stderr)

    elif icon: # extract
        best_size = 0
        best_type = None
        best_types = ['group_icon', 'PNG']

        try: # ignore if unsuccesful
            dev_null = open(devnull, 'w')
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
                      '--output=' + output_icon,
                      '--name=' + best_name,
                      '--type=' + best_type,
                      '--language=' + best_lang]

                call(cmd, stderr=dev_null)

                if not isfile(output_icon):
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

    if isinstance(icon, str):
        output = output.replace('$ICON', icon)
    elif icon and isfile(output_icon):
        output = output.replace('$ICON', output_icon)
    else: # remove line
        output = output.replace('Icon=$ICON\n', '')

    if print_output:
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
    call(['chmod', '700', shortcut])
    call(['chmod', '+x', shortcut])

if __name__ == '__main__':
    parser = ArgumentParser(description='wineshortcut - create shortcut to Windows executable file')
    parser.add_argument('input_file', help='Windows executable file')
    parser.add_argument('-o', '--output', help='write shortcut to output directory', dest='output_folder')
    parser.add_argument('-n', '--name', help='set custom shortcut name')
    parser.add_argument('-i', '--icon', help='set custom shortcut icon', default=True)
    parser.add_argument('-c', '--categories', help='set custom shortcut categories')
    parser.add_argument('-w', '--wine-prefix', help='set custom Wine prefix')
    parser.add_argument('-d', '--to-desktop', help='write shortcut to desktop folder', action='store_true')
    parser.add_argument('-a', '--to-appmenu', help='write shortcut to application menu', action='store_true')
    parser.add_argument('-s', '--skip-icon', help='disable executable icon extraction', action='store_const', const=False, dest='icon')
    parser.add_argument('-p', '--print-output', help='disable shortcut creation, just print output', action='store_true')

    args = parser.parse_args()

    wineshortcut(args.input_file,
                 args.output_folder,
                 args.name,
                 args.icon,
                 args.categories,
                 args.wine_prefix,
                 args.to_desktop,
                 args.to_appmenu,
                 args.print_output)