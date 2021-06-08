# ii
ii - CLI-utilities for iRODS

## Summary

ii is a collection of commandline utilities for iRODS.
The current version is a functional prototype, in the sense
that the interface is still subject to change and that it
hasn't been tested extensively yet.

## Requirements and installation

ii supports Python 3.6 and higher. It has currently been
tested with iRODS 4.2.7. The eventual goal is to support all
recent iRODS versions.

If you want to try it out, you can install it in a virtualenv:

```
virtualenv --no-site-packages --python /usr/bin/python3 venv
source venv/bin/activate
pip3 install --upgrade git+https://github.com/UtrechtUniversity/ii.git
```

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

### ii ls

Equivalent to the ils command in the iCommands. Lists data objects
or collections.

```
usage: ii ls [-h] [--verbose] [-m {plain,json,csv,yaml}]
             [-s {name,ext,size,date,unsorted}] [-H {default,yes,no}]
             [--recursive] [-l] [-L]
             [queries [queries ...]]

positional arguments:
  queries               Collection, data object or data object wildcard

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         Print verbose information for troubleshooting
  -m {plain,json,csv,yaml}, --format {plain,json,csv,yaml}
                        Output format
  -s {name,ext,size,date,unsorted}, --sort {name,ext,size,date,unsorted}
                        Propery to use for sorting
  -H {default,yes,no}, --hr-size {default,yes,no}
                        Whether to print human-readable sizes
                        [yes,no,default].By default, enable human-readable for
                        text output, disable for other formats.
  --recursive, -r       Include contents of subcollections
  -l                    Display replicas with size, resource, owner, date
  -L                    like -l, but also display checksum and physical path
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

## Known limitations

- ls command: sorting only has effect for the contents of collection
  arguments (e.g. `ii ls .`), but not for other arguments
  (e.g. `ii ls "*"` or `ii ls foo.dat bar.dat baz.dat`).
- ls command: human-readable output is not yet supported for JSON
  and YAML output.
- ls command: this command currently supports dataobject-only wildcards
  (e.g. `*.dat`), but not yet wildcards with collection names (e.g.
  `foo/*.dat` or `*/foo.dat`).
