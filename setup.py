
#-----------------------------------------------------------------------------
# setup.py
#
#------------------------------------------------------------------------
#
# Written/Update by  SparkFun Electronics, Fall 2022
#
# This python package implements a GUI Qt application that supports
# firmware and boot loader uploading to the SparkFun Artemis module
#
# This file defines the python install package to be build for the
# 'artemis_upload' package
#
# More information on qwiic is at https://www.sparkfun.com/artemis
#
# Do you like this library? Help support SparkFun. Buy a board!
#
#==================================================================================
# Copyright (c) 2022 SparkFun Electronics
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#==================================================================================
import setuptools
from codecs import open  # To use a consistent encoding
from os import path
from platform import system, machine
import subprocess
import sys

# sub folder for our resource files
_RESOURCE_DIRECTORY = "artemis_uploader/resource"

#https://stackoverflow.com/a/50914550
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, _RESOURCE_DIRECTORY, relative_path)

def get_version(rel_path: str) -> str:
    try: 
        with open(resource_path(rel_path), encoding='utf-8') as fp:
            for line in fp.read().splitlines():
                if line.startswith("__version__"):
                    delim = '"' if '"' in line else "'"
                    return line.split(delim)[1]
            raise RuntimeError("Unable to find version string.")
    except:
        raise RuntimeError("Unable to find _version.py.")

_APP_VERSION = get_version("_version.py")

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.md'), encoding='utf-8') as f:
    long_description = f.read()

install_deps = ['darkdetect', 'pyserial', 'pycryptodome']

# Raspberry Pi needs python3-pyqt5 and python3-pyqt5.qtserialport
# which can only be installed with apt-get
if (system() == "Linux") and ((machine() == "armv7l") or (machine() == "aarch64")):
    cmd = ['sudo','apt-get','install','python3-pyqt5','python3-pyqt5.qtserialport']
    subprocess.run(cmd)
else:
    install_deps.append('pyqt5')

setuptools.setup(
    name='artemis_uploader',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version=_APP_VERSION,

    description='Application to upload firmware to SparkFun Artemis based products',
    long_description=long_description,

    # The project's main homepage.
    url='https://www.sparkfun.com/artemis',

    # Author details
    author='SparkFun Electronics',
    author_email='sales@sparkfun.com',

    project_urls = {
        "Bug Tracker" : "https://github.com/sparkfun/Artemis-Firmware-Upload-GUI/issues",
        "Repository"   : "https://github.com/sparkfun/Artemis-Firmware-Upload-GUI"
    },
    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Production Stable :: 5',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Hardware Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',

    ],

    download_url="https://github.com/sparkfun/Artemis-Firmware-Upload-GUI/releases",

    # What does your project relate to?
    keywords='Firmware SparkFun Artemis Arduino',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=["artemis_uploader", "artemis_uploader/asb", "artemis_uploader/resource"],

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
    install_requires=install_deps,

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'artemis_uploader/resource': ['*.png', '*.jpg', '*.ico', '*.bin', '*.icns'],
    },



    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': ['artemis_upload=artemis_uploader:startArtemisUploader',
        ],
    },
)
