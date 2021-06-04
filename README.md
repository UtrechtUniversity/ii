# ii
ii - CLI-utilities for iRODS

## Summary

ii is a collection of commandline utilities for iRODS.
The current version is a functional prototype, in the sense
that the interface is still subject to change and that it
hasn't been tested extensively yet.

## Commands

### ii cd

Equivalent to the icd command in the iCommands. Changes the current
working directory. If no argument is given, it goes back to the
home directory.

```
usage: ii cd [-h] [--verbose] [directory]

positional arguments:
  directory      Directory to change to

optional arguments:
  -h, --help     show this help message and exit
  --verbose, -v  Print verbose information for troubleshooting
```

### ii pwd

Equivalent to the ipwd command in the iCommands. Prints the current
working directory.

```
usage: ii pwd [-h] [--verbose]

optional arguments:
  -h, --help     show this help message and exit
  --verbose, -v  Print verbose information for troubleshooting
```
