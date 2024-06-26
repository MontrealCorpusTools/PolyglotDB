import os
from setuptools import setup, find_packages
import codecs


def readme():
    with open('README.md') as f:
        return f.read()


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


if __name__ == '__main__':
    setup(name='polyglotdb',
          version=get_version("polyglotdb/__init__.py"),
          description='',
          long_description=readme(),
          long_description_content_type='text/markdown',
          classifiers=[
              'Development Status :: 3 - Alpha',
              'Programming Language :: Python',
              'Programming Language :: Python :: 3',
              'Intended Audience :: Science/Research',
              'License :: OSI Approved :: MIT License',
              'Operating System :: OS Independent',
              'Topic :: Scientific/Engineering',
              'Topic :: Text Processing :: Linguistic',
          ],
          keywords='phonology corpus phonetics',
          url='https://github.com/MontrealCorpusTools/PolyglotDB',
          author='Montreal Corpus Tools',
          author_email='michael.e.mcauliffe@gmail.com',
          packages=find_packages(include=['polyglotdb', 'polyglotdb.*']),
          include_package_data=True,
          package_data={
              'polyglotdb.databases': ['*.conf'],
              'polyglotdb.acoustics.formants': ['*.praat']},
          install_requires=[
              'neo4j-driver~=4.3',
              'praatio~=5.0',
              'textgrid',
              'conch_sounds',
              'librosa',
              'influxdb',
              'tqdm',
              'requests'
          ],
          entry_points={
              'console_scripts': [
                  'pgdb=polyglotdb.pgdb:main'
              ]
          },
          tests_require=[
              'pytest'
          ]
          )
    
