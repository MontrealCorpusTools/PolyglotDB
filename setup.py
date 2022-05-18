#!/usr/bin/env python
import setuptools
import os
import codecs


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


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

