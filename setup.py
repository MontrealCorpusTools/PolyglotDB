import sys
import os
from setuptools import setup
from setuptools.command.test import test as TestCommand


def readme():
    with open('README.md') as f:
        return f.read()


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--strict', '--verbose', '--tb=long', 'tests', '-x']
        # if os.environ.get('TRAVIS', False):
        #    self.test_args.insert(0, '--skipacoustics')
        self.test_suite = True

    def run_tests(self):
        if __name__ == '__main__':  # Fix for multiprocessing infinite recursion on Windows
            import pytest
            errcode = pytest.main(self.test_args)
            sys.exit(errcode)


if __name__ == '__main__':
    setup(name='polyglotdb',
          version='0.1.13',
          description='',
          long_description=readme(),
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
          packages=['polyglotdb',
                    'polyglotdb.acoustics',
                    'polyglotdb.acoustics.formants',
                    'polyglotdb.acoustics.pitch',
                    'polyglotdb.client',
                    'polyglotdb.corpus',
                    'polyglotdb.databases',
                    'polyglotdb.io',
                    'polyglotdb.io.types',
                    'polyglotdb.io.parsers',
                    'polyglotdb.io.inspect',
                    'polyglotdb.io.exporters',
                    'polyglotdb.io.importer',
                    'polyglotdb.io.enrichment',
                    'polyglotdb.query',
                    'polyglotdb.query.base',
                    'polyglotdb.query.annotations',
                    'polyglotdb.query.annotations.attributes',
                    'polyglotdb.query.annotations.profiles',
                    'polyglotdb.query.discourse',
                    'polyglotdb.query.speaker',
                    'polyglotdb.query.lexicon',
                    'polyglotdb.syllabification'],
          package_data={'polyglotdb.databases': ['*.conf'],
                        'polyglotdb.acoustics.formants': ['*.praat']},
          install_requires=[
              'neo4j-driver',
              'textgrid',
              'conch_sounds',
              'librosa',
              'influxdb',
              'tqdm'
          ],
          scripts=['bin/pgdb'],
          cmdclass={'test': PyTest},
          extras_require={
              'testing': ['pytest'],
          }
          )
