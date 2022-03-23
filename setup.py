#!/usr/bin/env python
import setuptools


def get_version(rel_path):
    delim = ' = '
    for line in read(rel_path).splitlines():
        if line.startswith('__ver_major__'):
            major_version = line.split(delim)[1]
        elif line.startswith('__ver_minor__'):
            minor_version = line.split(delim)[1]
        elif line.startswith('__ver_patch__'):
            patch_version = line.split(delim)[1].replace("'", '')
            break
    else:
        raise RuntimeError("Unable to find version string.")
    return "{}.{}.{}".format(major_version, minor_version, patch_version)


if __name__ ==  "__main__":
    setuptools.setup(version=get_version("polyglotdb/__init__.py"))

