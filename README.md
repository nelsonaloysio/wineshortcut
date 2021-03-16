wineshortcut
---

A simple Python script aimed at creating shortcuts to Windows executable files to be opened in Wine.

```
usage: wineshortcut [-h] [-o OUTPUT_FOLDER] [-n NAME] [-i WITH_ICON]
                    [-c CATEGORIES] [-w WINE_PREFIX] [-d] [-a] [-s] [-r]
                    input_file

positional arguments:
  input_file            Windows executable file

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_FOLDER, --output OUTPUT_FOLDER
                        write shortcut to output directory
  -n NAME, --name NAME  use custom shortcut name
  -i WITH_ICON, --with-icon WITH_ICON
                        use a custom shortcut icon
  -c CATEGORIES, --categories CATEGORIES
                        use custom shortcut categories
  -w WINE_PREFIX, --wine-prefix WINE_PREFIX
                        use a custom Wine prefix
  -d, --to-desktop      write shortcut to desktop folder
  -a, --to-appmenu      write shortcut to application menu
  -s, --skip-icon       disable executable icon extraction
  -r, --dry-run         do not create shortcut, just print output
```

### Requirements

Optionally requires **wrestool** to try and extract the executable icon.

The program comes with the package **[icoutils](https://www.nongnu.org/icoutils/)** and can be installed with:

* On Ubuntu/Debian: `apt install icoutils`
* On Arch/Antergos/Manjaro: `pacman -S icoutils`
* On Fedora/CentOS: `yum install icoutils`
* On Mageia/Mandriva: `urpmi icoutils`
* On SUSE: `zypper install icoutils`
* On Gentoo: `emerge icoutils`

### Examples

Write shortcut to current working directory:
> `wineshortcut.py file.exe`

Write shortcut to desktop and application menu:
> `wineshortcut.py file.exe -d -a`

Write shortcut to a specific directory:
> `wineshortcut.py file.exe -o /path/to/folder`

Write shortcut with a system/user icon:
> `wineshortcut.py file.exe -i icon_name`

Write shortcuts with an existing icon file:
> `wineshortcut.py file.exe -da -i /path/to/icon_file.png`

Just print contents and do not extract icon:

> `wineshortcut.py file.exe -p -s`

Write shortcut with custom wine prefix:

> `wineshortcut.py -w $HOME/.wine `

or with the quotation marks if necessary:

> `wineshortcut.py -w "$HOME/.wine" `

### Configuration file

With a configuration file named `wineshortcut.json`, one can easily create shortcuts with predefined preferences, without typing or copying the full arguments again and again.
It includes all command line switches described above. They are renamed with the following rules:

- The prefix `--` is removed
- All `-` are replaced by `_`

For example, switch `to-desktop` is named `to_desktop` in the configuration file.

#### An example

With an example configuration file `wineshortcut.json`:

```json
{
        "wine_prefix": "$HOME/.wine",
        "to_desktop": true,
        "to_appmenu": true
}
```

The command `./wineshortcut.py ~/example.exe` is equivalent to `./wineshortcut.py ~/example.exe -d -w "$HOME/.wine"`.

