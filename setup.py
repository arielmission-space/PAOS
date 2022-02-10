import codecs
import os

from setuptools import setup, find_packages


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_info(rel_path, info):
    for line in read(rel_path).splitlines():
        if line.startswith('__%s__' % info):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find %s string." % info)


packages = find_packages(exclude=('tests', 'docs'))

with open("README.md", "r") as fh:
    long_description = fh.read()

provides = [get_info("paos/__init__.py", 'pkg_name'), ]
console_scripts = [
    'paos=paos.paos:main',
    'paosgui=paos.paosGui:main'
]

# TODO: separate requirements from setup.py
with open('requirements.txt') as f:
    required = f.read().splitlines()
install_requires = required
entry_points = {'console_scripts': console_scripts, }

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Operating System :: POSIX',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development :: Libraries',
]

setup(name=get_info("paos/__init__.py", 'pkg_name'),
      provides=provides,
      version=get_info("paos/__version__.py", 'version'),
      description=get_info("paos/__init__.py", 'description'),
      url=get_info("paos/__init__.py", 'url'),
      author=get_info("paos/__init__.py", 'author'),
      author_email=get_info("paos/__init__.py", 'email'),
      license=get_info("paos/__init__.py", 'license'),
      long_description=long_description,
      long_description_content_type="text/markdown",
      packages=packages,
      classifiers=classifiers,
      install_requires=install_requires,
      include_package_data=True,
      entry_points=entry_points,
      python_requires='>=3.8',
      zip_safe=False)
