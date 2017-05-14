"""ota-server package installation module."""

import os
from os.path import join as pjoin
from setuptools import setup, find_packages


PACKAGE = 'otaserver'


def readme(fname):
    """Utility function to read the README. Used for long description."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def get_version(package):
    """Extract package version without importing file.

    Inspired from pep8 setup.py.
    """
    with open(os.path.join(package, '__init__.py')) as init_fd:
        for line in init_fd:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])  # pylint:disable=eval-used

if __name__ == '__main__':

    setup(name=PACKAGE,
          version=get_version(PACKAGE),
          description='RIOT Other The Air update management server.',
          long_description=readme('README.md'),
          author='Alexandre Abadie',
          author_email='alexandre.abadie@inria.fr',
          url='http://www.iot-lab.info',
          license='BSD',
          keywords="iot demonstration web coap",
          platforms='any',
          packages=find_packages(),
          scripts=[pjoin('bin', 'ota-server')],
          install_requires=[
            'tornado>=4.4.2',
            'aiocoap>=0.2'
          ],
          classifiers=[
            'Development Status :: 4 - Beta',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Intended Audience :: Developers',
            'Environment :: Console',
            'Topic :: Communications',
            'License :: OSI Approved :: ',
            'License :: OSI Approved :: BSD License'],
          zip_safe=False,
          )
