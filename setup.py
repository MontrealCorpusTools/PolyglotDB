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
        self.test_args = ['-x', '--strict', '--verbose', '--tb=long', 'tests']
        if os.environ.get('TRAVIS', False):
            self.test_args.insert(0, '--skipacoustics')
        self.test_suite = True

    def run_tests(self):
        if __name__ == '__main__': #Fix for multiprocessing infinite recursion on Windows
            import pytest
            errcode = pytest.main(self.test_args)
            sys.exit(errcode)

if __name__ == '__main__':
    setup(name='polyglotdb',
      version='0.0.1',
      description='',
      long_description='',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
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
                'polyglotdb.corpus',
                'polyglotdb.io',
                'polyglotdb.io.types',
                'polyglotdb.io.parsers',
                'polyglotdb.io.inspect',
                'polyglotdb.io.exporters',
                'polyglotdb.io.importer',
                'polyglotdb.io.enrichment',
                'polyglotdb.graph',
                'polyglotdb.graph.attributes',
                'polyglotdb.graph.cypher',
                'polyglotdb.sql',
                'polyglotdb.syllabification'],
      install_requires=[
          'sqlalchemy',
          'textgrid',
          'acousticsim',
          'py2neo',
          'librosa',
          'influxdb'
      ],
    cmdclass={'test': PyTest},
    extras_require={
        'testing': ['pytest'],
    }
      )
