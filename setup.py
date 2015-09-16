import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

import annograph

def readme():
    with open('README.md') as f:
        return f.read()

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--strict', '--verbose', '--tb=long', 'tests']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(name='annograph',
      version=annograph.__version__,
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
      url='https://github.com/PhonologicalCorpusTools/PyAnnotationGraph',
      author='Phonological CorpusTools',
      author_email='michael.e.mcauliffe@gmail.com',
      packages=['annograph',
                'annograph.io',
                'annograph.graph',
                'annograph.sql'],
      install_requires=[
          'sqlalchemy',
          'textgrid',
          'py2neo'
      ],
    cmdclass={'test': PyTest},
    extras_require={
        'testing': ['pytest'],
    }
      )
