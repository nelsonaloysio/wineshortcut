#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A simple script aimed at creating shortcuts to
Windows executable files to be opened in Wine.

If the program wrestool is installed, it will also
try and extract the executable icon beforehand.

Available for install on Debian/Ubuntu Linux with:
$ sudo apt install icoutils

Tested with Ubuntu 16.04 LTS and Python 3.5.2
and last edited 14/12/2017.
'''

from collections import defaultdict
from os import chdir, getcwd
from os.path import abspath, basename, dirname, isfile, splitext
from re import findall
from subprocess import call, check_output
from sys import argv

def main(input_file, icon_file=None, install=False):

    output = """[Desktop Entry]
Name=$NAME
Exec=env WINEPREFIX="/home/neo/.wine" /usr/bin/wine C:\\\\windows\\\\command\\\\start.exe /Unix "$FILE"
Type=Application
StartupNotify=true
Path=$PATH
Icon=$ICON
StartupWMClass=$EXE"""

    current = getcwd()
    exe = basename(input_file)
    name = splitext(exe)[0]
    file = abspath(input_file)
    path = dirname(file)
    shortcut = name+'.desktop'

    if not isfile(input_file):
        quit('Error: file', input_file, 'not found.')

    if icon_file:
        if isfile(icon_file):
            icon = abspath(input_icon)
        else: # show warning
            print('Warning: icon', icon_file, 'not found.')
            icon_file = None

    else: # extract icon from file

        try: # ignore if unsuccesful

            best_icon = 0
            best_size = 0
            icon_file = name+'.ico'
            icons = check_output(['wrestool', '-l', file]).decode().splitlines()

            for line in icons:
                if 'group_icon' in line:
                    icon_name = findall(r'(?<=--name=)[a-zA-Z0-9\'_"]+', line)[0]
                    icon_name = icon_name.replace('\'','').replace('"','')
                    icon_type = findall(r'(?<=--type=)[0-9]+', line)[0]
                    icon_size = findall(r'(?<=size=)[0-9]+', line)[0]
                    icon_language = findall(r'(?<=language=)[0-9]+', line)[0]
                    if int(icon_size) > int(best_size):
                        best_icon = {'icon_name': icon_name,
                                     'icon_type': icon_type,
                                     'icon_language': icon_language}
                        best_size = icon_size

            chdir(path)
            call(['wrestool', '-x',
                  '--output=' + icon_file,
                  '--language=' + best_icon['icon_language'],
                  '--type=' + best_icon['icon_type'],
                  '--name=' + best_icon['icon_name'],
                  exe])
            chdir(current)

            icon_file = abspath(path+'/'+icon_file)

        except Exception as e:
            print(str(e))

    output = output.replace('$NAME', name)\
                   .replace('$FILE', file)\
                   .replace('$PATH', path)\
                   .replace('$EXE', exe)

    if icon_file and isfile(icon_file):
        output = output.replace('$ICON', icon_file)
    else: output = output.replace('Icon=$ICON\n', '')

    if install:
        shortcut = '/home/neo/.local/share/applications/wine/Programs/' + shortcut

    with open(shortcut, 'w', newline='', encoding='utf8', errors='ignore') as output_file:
        output_file.write(output)

    call(['chmod', '700', shortcut])
    call(['chmod', '+x', shortcut])

    print(output)

if __name__ == '__main__':
    INSTALL=(True if '-i' in argv else False)
    for input_file in argv[1:]:
        if input_file != '-i':
            main(argv[1], install=INSTALL)
